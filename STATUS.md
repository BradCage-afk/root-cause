# Project status

**Root Cause** · ASYNC'26 Track 1 · Team Track and Field · updated 28 Sept 2026

**Stage: working prototype.** Every capability in the idea deck runs end to end on one laptop, is
covered by an automated test, and is shown in the demo video.

## Done

| Capability | Where | Test |
|---|---|---|
| Vault ingestion (Obsidian markdown + frontmatter), live watch-folder | `ingest.py`, `app.py` | ✅ |
| Hybrid retrieval — vector + FTS5 keyword, reciprocal rank fusion | `search.py` | ✅ |
| Cited answers, honest refusal outside the record | `search.py` | ✅ |
| Centroid-based recurrence clustering (block → rank → adjudicate → join/seed) | `cluster.py` | ✅ |
| "Why this?" evidence view for every cluster | `app.py` | ✅ |
| Fix effectiveness by timeline | `debt.py` | ✅ |
| Every fix as a falsifiable prediction, graded; calibration figure | `debt.py` | ✅ |
| Deterministic failure-debt score | `debt.py` | ✅ |
| Bi-temporal decisions (ADR superseded, with validity window) | `debt.py` | — |
| Pre-flight change check | `preflight.py` | ✅ |
| Prompt-injection quarantine | `security.py` | ✅ |
| Policy gate (permission × risk → AUTO / APPROVAL / BLOCK), scoped writes | `policy.py` | ✅ |
| Obsidian write-back of cluster notes, through the gate | `vault.py` | ✅ |
| MCP server (4 tools, same policy gate) | `mcp_server.py` | manual |
| Hash-chained audit ledger + tamper detection | `audit.py` | ✅ |
| Egress monitor; refuses any non-local model endpoint | `egress.py`, `config.py` | ✅ |
| Deterministic fallback when no model is running | `models.py` | ✅ |
| Windows one-click setup, offline wheel bundle | `setup.bat`, `bundle-offline.bat` | manual |
| Runtime model swap (memory untouched) | `models.py`, `app.py` | ✅ + verified against real Ollama |
| Indexed blocking (`cluster_nodes`) — true O(candidates) lookup | `cluster.py` | ✅ |
| Scale benchmark with ground truth (500 incidents) | `benchmark.py` | ✅ |
| Hybrid judge with veto floor (model can promote, never invent, a link) | `cluster.py` | ✅ |

16 automated tests pass (`python -m pytest -q`).

## Verified numbers (seeded corpus)

| | |
|---|---|
| Documents / incidents | 37 / 21 |
| Recurrence clusters | 2 — no false clusters (a near-miss sharing `pg-primary` is correctly rejected) |
| Chain A | INC-102 → INC-217 → INC-288, three teams; INC-301 joins live |
| REM-31, recorded as a permanent fix | **ineffective** — 2 recurrences, 3 after the live drop |
| REM-52 | **held** |
| Failure debt, chain A | 79 → 87 when INC-301 lands |
| Egress | 0 external connections |

## Scale proof (500 incidents, known ground truth, deterministic judge)

| | |
|---|---|
| New incident linked in | **0.9 ms** (median 0.8, p95 1.3) |
| Comparisons | **861** centroid comparisons vs **124,750** all-pairs (145× fewer) |
| Pair precision · recall | **0.90 · 0.65** |
| False links | 12 |
| Chains recovered exactly | 19 of 40 |

The benchmark found a real weakness first: counting shared dependency names as evidence gave precision 0.30.
The judge now weights shared words by rarity (IDF), ignores entity names blocking already counted, and treats
two causes that name *different* failing dependencies as different. Recall misses are paraphrases the
deterministic judge cannot see; the local-model judge addresses those on the GPU laptop.

## Changed from the idea deck, and why

| Deck said | Prototype does | Reason |
|---|---|---|
| PostgreSQL + pgvector | SQLite + FTS5, same schema | Zero install on Windows; pgvector on Windows needs Docker + WSL2. Postgres remains the scale path. |
| Next.js console | One HTML page served by FastAPI | No Node toolchain to carry offline; nothing to build. |
| bge-small via sentence-transformers | `nomic-embed-text` via Ollama | Drops a 2 GB PyTorch dependency and the HuggingFace offline-cache trap. |
| Cross-encoder reranker | Not included | First item on the cut list; reciprocal rank fusion alone ranks this corpus well. |

## Next (hackathon, 30 Sept – 1 Oct)

1. Measure the median answer time on the RTX 3050 (target < 5 s)
2. Run the scale benchmark with the hybrid (local-model) judge on the 3050 and compare recall
3. Jira / ServiceNow importer
4. PostgreSQL + pgvector backend behind the same interface

## Known limitations

- Corpus is seeded, with recurrence chains planted on purpose (documented in `scripts/make_corpus.py`)
- Causes are evidence-backed hypotheses, not proofs
- Injection detection is pattern-based; the policy gate is the real boundary
- Single-user; no authentication (local-only by design for the prototype)
