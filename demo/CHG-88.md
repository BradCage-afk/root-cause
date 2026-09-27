---
id: CHG-88
type: change
team: search
date: 2026-07-06
---
Raise search-indexer batch reindex concurrency from 8 to 16 workers and move the nightly reindex
window to 02:00. Each worker holds its own database connection for the duration of its batch.
