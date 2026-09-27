---
id: REM-31
type: remediation
incident: INC-102
kind: fix
applied: 2026-01-22T15:00:00+05:30
summary: "Raise pgbouncer-main pool size from 100 to 200"
---
# REM-31 — Raise pgbouncer-main pool size to 200

Changed `default_pool_size` from 100 to 200 on pgbouncer-main. Load-tested checkout at 2x
normal traffic. Postmortem [[PM-102]] records this as the permanent fix for [[INC-102]].
