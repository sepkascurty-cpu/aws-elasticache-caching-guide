"""
cache.py — Cache-aside demo against ElastiCache (Redis/Valkey-compatible).

Simulates the pattern from the architecture diagram:
    EC2 app  ->  ElastiCache (hit? serve)  ->  RDS (miss? query + populate)

Run:  pip install redis   then   python cache.py
Works against any Redis-compatible endpoint (local redis, ElastiCache,
Valkey). Falls back to an in-process dict so the demo still runs offline.
"""

import time
import random

try:
    import redis
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    client.ping()
    BACKEND = "redis"
except Exception:
    BACKEND = "memory-dict"

# ---------------- fake slow database ----------------
FAKE_DB = {
    "product:101": {"name": "Kopi Tubruk", "price": 15000, "stock": 240},
    "product:202": {"name": "Indomie Goreng", "price": 3500, "stock": 1800},
    "product:303": {"name": "Teh Botol", "price": 4000, "stock": 950},
}

def slow_db_query(key: str):
    """Pretend this is a 60ms round-trip to RDS."""
    time.sleep(0.06)
    return FAKE_DB.get(key)


# ---------------- cache-aside wrapper ----------------
class CacheAside:
    def __init__(self, default_ttl: int = 10):
        self.default_ttl = default_ttl
        self.hits = self.misses = 0
        self._mem = {}

    # --- backend-agnostic get/set ---
    def _get(self, key):
        if BACKEND == "redis":
            return client.get(key)
        entry = self._mem.get(key)
        if entry and entry["exp"] > time.time():
            return entry["val"]
        return None

    def _set(self, key, value, ttl):
        if BACKEND == "redis":
            client.setex(key, ttl, value)
        else:
            self._mem[key] = {"val": value, "exp": time.time() + ttl}

    # --- the pattern ---
    def get_product(self, key: str, ttl: int | None = None) -> dict | None:
        cached = self._get(key)
        if cached is not None:
            self.hits += 1
            return {"source": "cache", "data": cached}
        self.misses += 1
        row = slow_db_query(key)          # miss -> query RDS
        if row is None:
            return None
        self._set(key, str(row), ttl or self.default_ttl)  # populate cache
        return {"source": "db", "data": row}

    def invalidate(self, key: str):
        """Call this on every write so reads never go stale."""
        if BACKEND == "redis":
            client.delete(key)
        else:
            self._mem.pop(key, None)


# ---------------- demo ----------------
if __name__ == "__main__":
    print(f"[backend: {BACKEND}]")
    c = CacheAside(default_ttl=3)   # short TTL so you can watch expiry live

    keys = list(FAKE_DB)
    for i in range(8):
        key = random.choice(keys)
        t0 = time.perf_counter()
        res = c.get_product(key)
        dt = (time.perf_counter() - t0) * 1000
        print(f"req {i+1}: {key:12} <- {res['source']:5} ({dt:5.1f} ms)")

    print(f"\nhits={c.hits}  misses={c.misses}")
    print("sleeping 4s so the TTL expires...")
    time.sleep(4)
    res = c.get_product(keys[0])
    print(f"after expiry: {keys[0]} <- {res['source']}  (cold miss, back to DB)")

    # write invalidation: price changes must not stay stale
    c.get_product("product:101")          # warm the cache
    FAKE_DB["product:101"]["price"] = 16000
    c.invalidate("product:101")           # invalidate on write
    res = c.get_product("product:101")
    print(f"after write+invalidate: {res['data']}  <- {res['source']}")
