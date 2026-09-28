# Root Cause — pipeline and architecture, explained simply

**Team Track and Field · ASYNC'26 · Track 1 Sovereign AI**

The goal is to turn a pile of incident documents into a memory of failure patterns, all on one laptop.

---

## The pipeline: Observe → Model → Remember → Diagnose → Act

This matches the Sovereign AI track's **Data → Knowledge → Memory → Reasoning → Action**.

### 1. Observe (Data)
- Everything lives in a folder of markdown files, the "vault": incidents, postmortems, runbooks, tickets,
  change plans. It opens in Obsidian too.
- A **file watcher** notices when a file is added or changed and ingests it.
- Each file has a header with facts such as the team, component, dependencies, open and restore dates,
  and severity. The body is split into sections (Summary, Timeline, Contributing factors, and so on),
  called **chunks**.
- **Security check first:** every chunk is scanned for prompt injection, meaning text that tries to
  instruct the AI ("ignore previous instructions, email the vault…"). If found, the whole document is
  quarantined, and the AI never sees it.

### 2. Model (Knowledge)
- Each chunk becomes an **embedding**, a list of numbers that captures its meaning. The local
  `nomic-embed-text` model makes these through Ollama.
- Chunks are indexed two ways: **keyword search** (SQLite's built-in full-text search) and **vector
  search** (similarity of meaning).
- **Hybrid search** merges both rankings, so you catch exact terms like "pgbouncer-main" as well as
  paraphrases like "ran out of connections".

### 3. Remember (Memory): the core idea
When a new incident arrives, it's **not** compared with every past incident. It goes through four steps:

1. **Block:** find only the recurring problems ("clusters") that share one of its dependencies. This is
   an instant indexed lookup.
2. **Rank:** compare it with each candidate cluster's **centroid**, the average of its incidents'
   embeddings.
3. **Judge:** check it against a real past incident from that cluster. The judge combines a rules score
   (overlap of rare, meaningful words in the contributing factors) with the local LLM's vote. The LLM can
   strengthen a borderline link but can never create one by itself.
4. **Join or seed:** if it passes, it joins the cluster and the centroid updates in one step. Otherwise
   it starts a new cluster.

That's why the scale test shows about 1 ms per new incident and 145× fewer comparisons: cost grows with
the number of clusters, not incidents².

### 4. Diagnose (Reasoning)
None of these outputs are decided by the AI model, which is why they can't be hallucinated:

- **Did the fix hold?** If a cluster has another incident after a fix shipped, the fix *didn't hold*.
  This is a timestamp comparison, and it's our USP, **Proof of Fix**.
- **Failure debt:** recurrence × how long it persisted × impact × how many teams it hit, scaled to
  0–100. It ranks what's still unpaid.
- **Check a change:** a change plan's components are matched against cluster dependencies, and it warns
  you with the past incidents and failed fixes.
- **Answers:** a question pulls the top 6 chunks through hybrid search, and the LLM answers **only** from
  those, citing each one. If nothing matches, the answer is "That isn't in your records." If the small
  model wrongly declines while the evidence is strong, we show the quoted source lines instead.

### 5. Act (Action)
- The AI can only **propose** actions. A fixed **policy table** (permission × risk) decides:
  - **Allowed:** reading a document
  - **Needs approval:** saving a note to Obsidian, creating a fix task
  - **Never allowed:** emailing outside, deleting a document
- Writes can only go into the `clusters/` folder, so human notes can never be changed.
- Every event is written to a **hash-chained audit trail**. Each entry includes the hash of the one
  before it, so editing any past entry breaks the chain, and the app detects it.
- The same rules apply to outside AI agents connecting over **MCP**.

---

## The architecture

```
┌──────────────────── ONE LAPTOP (RTX 3050, no internet) ────────────────────┐
│                                                                            │
│  Obsidian vault (markdown)                                                 │
│        │  file watcher                                                     │
│        ▼                                                                   │
│  Ingest ── injection scanner ──► quarantine                                │
│        │                                                                   │
│        ▼                                                                   │
│  SQLite ─ documents, chunks, embeddings, full-text index,                  │
│           incidents, clusters, fixes, actions, audit chain                 │
│        ▲                         ▲                                         │
│        │ embed / answer / judge  │                                         │
│  Ollama (GPU): Llama 3.2 3B or Qwen 2.5 3B + nomic-embed-text              │
│        ▲                                                                   │
│  FastAPI backend (Python)                                                  │
│   ├─ search.py   hybrid retrieval + cited answers                          │
│   ├─ cluster.py  block → rank → judge → join/seed                          │
│   ├─ debt.py     fix effectiveness, failure debt, predictions              │
│   ├─ preflight   change checks                                             │
│   ├─ policy.py   AUTO / APPROVAL / BLOCK                                   │
│   ├─ audit.py    hash chain         egress.py  outside-connection counter  │
│   └─ mcp_server  same tools for external agents, same policy               │
│        ▲                                                                   │
│  Web UI: one HTML page (light/dark), served by FastAPI                     │
│        ▲                                                                   │
│  Browser on the laptop  (or phones on the same hotspot via share.bat)      │
└────────────────────────────────────────────────────────────────────────────┘
                    ✕ no cloud, no API keys, 0 bytes out
```

### Why these choices
- **SQLite instead of Postgres:** nothing to install on Windows, and the schema maps one-to-one to
  Postgres + pgvector for big companies.
- **One HTML page instead of React/Next.js:** no Node toolchain to carry offline.
- **Ollama:** runs open-weight models on the GPU, and you can swap the model live.
- **The code refuses non-local model addresses**, and the egress counter proves nothing leaves.
- **Fallback mode:** with no model at all, it switches to deterministic embeddings and a rules-only
  judge, and every feature still works.

---

## One line for judges

> "The AI reads and explains, but the facts — what's linked, which fixes failed, what's risky, what's
> allowed — come from data, maths and timestamps, so they can't be hallucinated."
