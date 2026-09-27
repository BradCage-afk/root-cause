---
id: REM-37
type: remediation
incident: INC-217
kind: workaround
applied: 2026-03-06T12:00:00+05:30
summary: "Stagger the batch reindex into four windows"
---
# REM-37 — Stagger the batch reindex

Split the nightly batch reindex into four windows so fewer connections open at once.
