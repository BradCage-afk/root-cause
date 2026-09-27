---
id: REM-52
type: remediation
incident: INC-133
kind: fix
applied: 2026-02-02T11:00:00+05:30
summary: "Patch batch retention leak and add memory ceiling test"
---
# REM-52 — Patch the batch retention leak

Failed batches are now dropped after three attempts. Added a soak test that fails CI if heap
grows past 400 MB.
