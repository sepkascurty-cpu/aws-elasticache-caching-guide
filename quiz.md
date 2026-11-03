# Quiz — AWS ElastiCache Caching Done Right ⚡

Test yourself before peeking. Click to reveal.

---

### 1. In the cache-aside pattern, what happens on a cache miss?

<details>
<summary>Answer</summary>

The application queries the database directly, then writes the result back into the cache (with a TTL) so the next identical request is a hit.
</details>

---

### 2. Every key in your cache is given the exact same 1-hour TTL. At the top of each hour, what breaks — and what's the fix?

<details>
<summary>Answer</summary>

**Cache stampede (thundering herd):** thousands of keys expire at the same second, so a flood of requests all miss at once and slam the database. Fix: add random jitter to TTLs (e.g. 1h ± 10 min) so expiry spreads out.
</details>

---

### 3. What's the difference between write-through and write-behind, and which one risks data loss?

<details>
<summary>Answer</summary>

**Write-through** writes to cache *and* database synchronously — slower writes, but no data loss. **Write-behind** writes only to cache and flushes to the DB asynchronously — much faster writes, but data not yet flushed is lost if the cache node crashes.
</details>

---

### 4. You have a primary + replica ElastiCache cluster. The primary node fails. What happens to in-flight reads?

<details>
<summary>Answer</summary>

ElastiCache **automatic failover** promotes a replica to primary and updates the DNS endpoint. Reads briefly pause during promotion (seconds, not minutes); the application should retry with backoff instead of crashing.
</details>

---

### 5. When is ElastiCache Serverless a better choice than a provisioned cluster?

<details>
<summary>Answer</summary>

When traffic is **spiky or unpredictable** — Serverless scales capacity automatically and you pay per request/GB-hr instead of paying for idle node hours. Provisioned clusters win when traffic is steady and predictable (lower unit cost, more control over node types).
</details>

---

*Scored 5/5? You're production-ready. 3–4? Re-read the TTL section. Below 3? Start again at [README.md](README.md).*
