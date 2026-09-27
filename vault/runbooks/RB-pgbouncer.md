---
id: RB-pgbouncer
type: runbook
team: platform
date: 2026-01-05
---
# Runbook — pgbouncer-main

pgbouncer-main is the shared connection pooler in front of pg-primary. Clients: checkout-api,
search-indexer, gateway-healthcheck, reporting.

## When clients cannot get connections
1. Check `SHOW POOLS;` for `cl_waiting` above 0.
2. Identify the client with the most active server connections.
3. Throttle that client before touching pool size.
