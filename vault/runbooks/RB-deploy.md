---
id: RB-deploy
type: runbook
team: platform
date: 2026-01-08
---
# Runbook — Production deploys

Deploys go out behind feature flags. Roll to 10% first, watch error budgets for 30 minutes,
then 50%, then 100%. Config changes are reviewed like code.
