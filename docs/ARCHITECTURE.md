# Architecture

Root Cause maps onto the five stages of the Track 1 brief — Data → Knowledge → Memory → Reasoning →
Action — named for what they do: **Observe → Model → Remember → Diagnose → Act**.

```
                ┌──────────────────── one laptop, no egress ────────────────────┐
 Obsidian vault │  OBSERVE    watchdog + ingest.py                               │
 (markdown +    │     │       parse frontmatter, split by section, scan for      │
  frontmatter)──┼─────┘       injection, embed                                  │
                │  MODEL      typed rows: incidents, remediations, decisions     │
                │             missing fields → constrained JSON extraction       │
                │  REMEMBER   SQLite: chunks + embeddings, FTS5 keyword index,   │
                │             clusters with centroids, bi-temporal decisions     │
                │  DIAGNOSE   search.py   hybrid retrieval, RRF, cited answers   │
                │             cluster.py  block → rank → adjudicate → join/seed  │
                │             debt.py     failure debt, fix effect, predictions  │
                │             preflight.py change plan vs clusters               │
                │  ACT        policy.py   permission × risk → AUTO/APPROVAL/BLOCK│
                │             vault.py    write-back, scoped to clusters/        │
                │             audit.py    hash chain     mcp_server.py  MCP      │
                │                                                                 │
                │  Ollama @ 127.0.0.1:11434  llama3.2:3b · nomic-embed-text      │
                └─────────────────────────────────────────────────────────────────┘
```

## Where the model is — and isn't — used

| Step | Model? |
|---|---|
| Parse, chunk, load | No |
| Embeddings | `nomic-embed-text` (local) |
| Hybrid retrieval + reciprocal rank fusion | No — SQL + vector maths |
| Recurrence test 1: shared component/dependency | No — set intersection |
| Recurrence test 2: similarity to centroid | No — cosine |
| Recurrence test 3: adjudication | **Yes** — averaged with a deterministic score (`RC_JUDGE=hybrid`) |
| Failure debt | No — arithmetic |
| Fix effectiveness, prediction grading | No — timestamps |
| Writing an answer / a pre-flight warning | **Yes** — from supplied evidence only |

The model is never asked to *know* anything. That is why a 3B model is sufficient, why the
time-based findings cannot hallucinate, and why swapping the model barely changes the results.

## Recurrence linking

```python
for incident in chronological order:
    candidates = clusters sharing a component or dependency      # BLOCK
    ranked = top_k(cosine(incident, cluster.centroid))           # RANK, floor per vector space
    for cluster in ranked:
        verdict = judge(incident, cluster.representative)        # ADJUDICATE vs a real document
        if verdict.confidence >= CONF_MIN:
            join(cluster); centroid = normalise((c*n + v)/(n+1)) # O(1)
            break
    else:
        seed a new cluster
```

- **Cost** grows with the number of clusters, not incidents squared. At 50,000 incidents naive
  pairwise linking is 1.25 billion comparisons; this is a few thousand centroid comparisons.
- **One code path**: the initial load replays history through the same function the live watcher uses.
- **Order-dependent by design**: the system knows what it knew when it knew it.
- **Precision comes from adjudication, recall from ranking.** The RANK floor is set per vector space
  (`RC_SIM_MIN` for semantic embeddings, `RC_SIM_MIN_HASH` for the fallback) because the two live on
  different similarity scales.

## Failure debt

```
debt = recurrence × persistence × impact × spread × (0.25 if a later fix held)
       recurrence  = incidents in the cluster
       persistence = 1 + span in days / 30
       impact      = mean severity weight × (1 + mean hours to restore / 4)
       spread      = distinct teams
score = 100 × debt / (debt + 50)
```

## Trust boundary

- **Retrieved content is evidence, not authority.** `security.py` scans every chunk for text addressed to
  the agent (instruction overrides, role changes, exfiltration requests, tool-call syntax); matches are
  quarantined — stored for audit, excluded from every prompt and every search result.
- **Policy is the only authority.** `policy.py` maps each tool's permission and risk to AUTO, APPROVAL or
  BLOCK. No document, prompt or MCP client can change the table.
- **Writes are scoped.** The only writable place is `vault/clusters/`; path traversal is refused.
- **Nothing leaves.** `config.py` refuses any model endpoint that isn't local; `egress.py` watches the app
  and the model server for connections to non-local addresses.
- **Everything is recorded.** `audit.py` chains each entry to the previous hash.

## Scaling path

| Prototype | At scale |
|---|---|
| SQLite + FTS5 | PostgreSQL + pgvector (HNSW) + tsvector, same schema, row-level security per tenant |
| Ollama on one GPU | vLLM with continuous batching |
| Watch-folder | ServiceNow / Jira / PagerDuty / Confluence connectors |
| Single user | SSO, RBAC, per-engagement keys |
