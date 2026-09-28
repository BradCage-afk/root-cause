# Root Cause — project summary

**Team:** Track and Field · **Event:** ASYNC'26, Ramaiah Institute of Technology · **Track 1:** Sovereign AI
**Repo:** https://github.com/BradCage-afk/root-cause · **Stage:** working prototype, 16 automated tests passing

> Root Cause is an offline AI memory for incidents: it links the failures different teams keep fixing
> separately, proves from timestamps which "permanent fixes" never held, and warns before the same mistake
> ships again — all on one laptop, with nothing sent to the internet.

---

## 1. What it is

Root Cause is **sovereign causal memory** for an engineering organisation. It reads the documents a company
already writes — incident reports, postmortems, runbooks, architecture decisions, change plans — stored as a
plain markdown (Obsidian) vault, and turns them into a memory of **failure patterns**, not just documents.

It answers four questions that search and chatbots don't:

1. **Which incidents are really the same problem?** Different teams, different symptoms, one underlying cause.
2. **Did the fix actually work?** Every recorded fix is checked against what happened afterwards.
3. **What is still unpaid?** Recurring problems ranked by *failure debt*.
4. **Is this next change about to repeat history?** A planned change is checked before it ships.

Everything — the database, the search index, the AI model, the audit trail — runs on a single laptop
(RTX 3050, 16 GB RAM). The demo runs with Wi-Fi switched off.

## 2. Why we built it

- **Organisations forget.** In the demo corpus, a checkout outage (payments), a search indexing lag
  (search), a gateway health-check storm (platform) and a notification failure (notifications) are all
  the same exhausted database connection pool. Each team wrote a good postmortem. Nobody connected them.
- **"Permanent fixes" are rarely checked.** A fix is recorded, the ticket closes, and nobody verifies
  whether the failure came back. In the demo, the January fix *raise the pool size from 100 to 200*
  didn't hold — the problem came back three more times.
- **The documents that hold these lessons are the ones you can't upload.** Postmortems name internal
  systems, customers, vulnerabilities and people. Banks, defence, healthcare, government and consulting
  firms (Deloitte, EY and their clients) can't send them to a cloud AI. Sovereign AI means the model comes
  to the data, not the other way round.
- **AI assistants answer when asked; they don't warn.** The most valuable moment is *before* a risky change
  ships, when nobody thinks to ask.

## 3. How it works — technical approach

**Pipeline:** OBSERVE → MODEL → REMEMBER → DIAGNOSE → ACT
(Data → Knowledge → Memory → Reasoning → Action).

| Layer | What happens | Technology |
|---|---|---|
| **Observe** | A file watcher ingests markdown from the vault. Frontmatter (team, component, dependencies, dates, severity) is parsed; text is split into section chunks. Every chunk is scanned for prompt injection before it can reach a model. | Python, watchdog, regex injection patterns |
| **Model** | Chunks are embedded and indexed for hybrid search: keyword (BM25 via SQLite FTS5) + vector similarity, merged with reciprocal-rank fusion. | Ollama `nomic-embed-text`, SQLite + FTS5 |
| **Remember** | **Centroid-first recurrence linking.** A new incident is compared with *cluster centroids*, not every past incident: **block** on shared dependency nodes (indexed lookup) → **rank** by cosine similarity to each candidate centroid → **adjudicate** against a real representative incident → **join** (O(1) centroid update) or **seed** a new cluster. Incidents are replayed chronologically, so batch and live ingestion use one code path. | numpy, SQLite |
| **Diagnose** | **Fix effectiveness** is a timestamp comparison: a fix is *ineffective* if its cluster recurs after it shipped. **Failure debt** = recurrence × persistence × impact × cross-team spread, normalised to 0–100. **Pre-flight** matches a change plan's components against cluster dependencies. None of these is decided by the model. | Deterministic Python |
| **Act** | The model may *propose* actions; a fixed policy table (permission × risk) decides AUTO / APPROVAL / BLOCK. Approved notes are written back into the Obsidian vault (only the `clusters/` folder is writable). Every event goes into a hash-chained audit ledger. The same gate applies to external agents over MCP. | FastAPI, MCP server, SHA-256 chain |

**The judge (is this the same cause?)** is a hybrid of a local LLM and a rules score. The rules score is an
IDF-weighted overlap of contributing-factor words, excluding entity names already shared by blocking, with
a penalty when the incidents name different subject dependencies. The LLM's vote is averaged in, but a
**veto floor** means the model can promote a borderline link, never invent one from nothing.

**Answers** come only from retrieved records, with numbered citations. If nothing relevant is found, it says
*"That isn't in your records"* instead of guessing.

**Sovereignty is enforced in code, not promised:** `assert_local()` refuses any non-local model endpoint; a
live egress monitor counts connections to non-local addresses (it reads 0); with no model available the app
falls back to deterministic embeddings and a rules judge, and every feature still works.

**Stack:** Python 3.11 · FastAPI · SQLite + FTS5 · Ollama (Llama 3.2 3B / Qwen 2.5 3B, nomic-embed-text) ·
one-file HTML UI (no Node) · Obsidian vault · MCP. Windows one-click setup (`setup.bat`, `run.bat`).

## 4. Unique selling point — **Proof of Fix**

> **Root Cause is the only incident memory that proves which fixes didn't work — from timestamps, not AI
> opinion — and warns you before the same change ships again. Fully offline, on one laptop.**

What makes that different:

- **Every fix is a falsifiable prediction.** Recording "raise pool size to 200" is a claim that the problem
  won't come back. The timeline grades it: *held* or *didn't hold*. The AI cannot hallucinate this result,
  because the AI doesn't compute it.
- **It warns before, not after.** Pre-flight checks a change plan against every recurring problem and the
  fixes that already failed, before anyone asks.
- **Cross-team by design.** The unit of intelligence is the failure pattern, not the document. It links
  incidents that four teams treated as four separate problems.
- **The brain is replaceable, the memory is yours.** Swap Llama for Qwen live: same citations, same
  clusters, same audit trail.
- **Measured, not claimed.** A 500-incident benchmark with known answers is built in.

## 5. Results so far

| Metric | Value |
|---|---|
| Demo corpus | 37 documents → 21 incidents → 2 recurring problems, 3 fixes that didn't hold |
| Near-miss rejected | An incident sharing `pg-primary` but with a different cause is correctly *not* linked |
| Time to link a new incident (500-incident benchmark) | **~1 ms** median (p95 1.5 ms) |
| Comparisons vs. checking every pair | **861 vs 124,750 — 145× fewer** |
| Links that are correct (pair precision) | **90%** |
| True links found (pair recall) | **65%** with the rules judge — the local model is there to raise this |
| Data sent outside during the demo | **0 connections** |
| Tests | 16 passing |

We report the misses too: the rules judge prefers missing a link over inventing one.

## 6. Additional details

- **Security:** prompt-injection quarantine (a poisoned postmortem that tells the AI to email the vault
  outside is caught before it reaches a prompt); policy gate blocks any external send; writes are scoped to
  one folder; the tamper test shows an edited audit event is detected immediately.
- **Obsidian:** the corpus is plain markdown with wikilinks. Approved problem notes are written back, so the
  knowledge is readable in Obsidian's graph view even with Root Cause uninstalled.
- **Hardware:** runs on an RTX 3050 laptop (4–6 GB VRAM) with a 3B model; also runs with no GPU in fallback
  mode.
- **UI:** light and dark themes, plain-language labels with technical details one click away, and a
  Guided demo checklist.
- **Path to enterprise scale:** the SQLite schema mirrors PostgreSQL + pgvector one-to-one for multi-user
  deployments; importers for Jira / ServiceNow exports; one GPU server per organisation (or per client, for
  consulting firms) keeps data inside their boundary; MCP lets existing agents query the memory under the
  same policy gate.
- **Limitations we state openly:** a root cause is an evidence-backed *hypothesis*, not a certainty; recall
  at scale depends on the judge; the demo corpus is synthetic, written to mirror real postmortem structure.

## 7. What we're building in the 24 hours

Measured answer latency on the 3050 (replacing the "target" in the deck), a Jira / ServiceNow CSV importer,
the hybrid-judge benchmark run on the GPU, and an Obsidian graph-view demo beat.
