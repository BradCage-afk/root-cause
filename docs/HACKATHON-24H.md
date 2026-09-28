# The 24 hours — 30 Sept to 1 Oct

**Root Cause** · Team Track and Field · on campus · **no Wi-Fi**

The prototype already works end to end. The 24 hours are for three things:

1. **Turn claims into measurements.** The deck says "target < 5 s". Walk out with a measured number.
2. **Add the features that win.** Model swap, a scale proof, and a real-world importer.
3. **Nail the demo.** Rehearse, record a backup, prepare for judges' questions.

Do **not** rebuild what works. Every new feature goes in behind the 14 tests that already pass.

---

## Before you leave home (needs internet — do it by 29 Sept)

**On the RTX 3050 laptop (the demo machine):**
- [ ] `ollama pull qwen2.5:3b` — needed for the model-swap feature
- [ ] Install **Obsidian** (obsidian.md) — for the graph-view demo beat
- [ ] Copy `%USERPROFILE%\.ollama\models` to a USB stick (backup of every model)

**On every teammate's laptop:**
- [ ] Download the repo and run `setup.bat` **at home**, so Python packages are already installed
- [ ] Run `.venv\Scripts\python -m pytest -q` and see 14 passed
- [ ] Without a GPU, set `RC_MODE=fallback` for development; the demo laptop runs the real model

**Sharing code at the venue without internet:**
- If phone hotspots with mobile data are allowed, GitHub works as usual.
- If not: one person is the integrator. Others copy their changed files over on a USB stick, or use a
  local network share. Merge on the demo laptop, run the tests, commit there, push once you're back online.

**Pack:** power strip, laptop chargers, cooling pad for the 3050, USB sticks ×2, ethernet cable.

---

## Who does what

| Person | Feature | Why it matters to judges |
|---|---|---|
| **Anshuman** (3050 laptop) | Real-model tuning + **latency measurement** + **model swap** | Replaces "target" with a measured number; proves "the brain is replaceable, the memory is yours" |
| **Vatsal** | **Scale proof**: 500-incident generated corpus + benchmark | Backs the centroid O(clusters) claim with numbers: link time, false-cluster rate |
| **Tharun** | **Jira / ServiceNow importer** (CSV/JSON export → vault markdown) | Shows it works on real exports, not only hand-written files |
| **Tobie** | UI for the three features + **Obsidian graph-view** beat + deck updates | Makes the new work visible in the demo |

---

## The features, concretely

### 1. Latency measurement — Anshuman
- Time every `/api/ask` call (retrieval ms, model ms, total ms); store in the audit payload.
- Add a small "median answer time" tile on the Overview, computed from real queries.
- Run 20 questions on the 3050, write the median into the deck (slide 6) in place of "target".

### 2. Model swap — Anshuman + Tobie
- `POST /api/model {"chat_model": "qwen2.5:3b"}` switches the chat model at runtime (embeddings stay the same,
  so the memory is untouched).
- A dropdown in the header: Llama 3.2 3B ↔ Qwen 2.5 3B.
- Demo beat: ask the same question, switch model, ask again. Same citations, same clusters, different wording.

### 3. Scale proof — Vatsal
- Extend `scripts/make_corpus.py` with `--scale 500`: generate filler incidents with distinct causes across
  more teams and components (keep the planted chains).
- Benchmark script: time to link one new incident, and how many recurrence clusters are found.
- Pass criteria: **still exactly the 2 planted clusters, no false links, new incident links in under 1 s.**
- Show the result on a "Scale" card: *500 incidents · 2 clusters · 0 false links · 0.3 s per new incident*.

### 4. Jira / ServiceNow importer — Tharun
- `scripts/import_tickets.py export.csv` → one markdown file per ticket in `vault/incidents/` with frontmatter
  (id, team, component, opened, restored, severity, symptom).
- Column mapping in a small config so it works for both Jira and ServiceNow exports.
- Include a 10-row sample export in `demo/` so the beat works offline.

### 5. Obsidian graph view — Tobie
- Approve "Write note to Obsidian vault" for CLU-001, open the `vault` folder in Obsidian, open **Graph view**.
- INC-102/217/288/301 all link to CLU-001, which links to REM-31. Ten seconds of demo, zero build cost.

### Stretch (only if everything above is done by hour 13)
- **PostgreSQL + pgvector backend** behind the same interface. Needs Docker Desktop installed beforehand — skip
  it if Docker isn't already on the laptop.
- **Cluster graph view** inside the web UI (nodes and edges, not just the timeline).

---

## Schedule

| Hours | What | Checkpoint |
|---|---|---|
| 0–1 | Everyone runs the app and the tests offline. Anshuman runs `rootcause.check` on the 3050 | All green |
| 1–5 | Build features 1–4 in parallel | — |
| 5–6 | **Merge #1** on the demo laptop, run tests | 14+ tests pass |
| 6–12 | Finish features, add their UI, Obsidian beat | — |
| 12–13 | **Merge #2** | Every feature visible in the UI |
| 13–16 | Stretch goals **or** bug fixing — not both | — |
| 16–18 | Update the deck with measured numbers and new screenshots (`scripts/deck_shots.py`) | Deck final |
| **18** | **FEATURE FREEZE.** No new code after this | — |
| 18–21 | Rehearse the demo 5 times. **Record a backup video** on the 3050 | Backup video saved |
| 21–24 | Buffer, sleep in shifts, practise judge questions | — |

**Cut in this order if you're behind:** stretch goals → importer UI (keep the script) → scale card
(keep the numbers) → Obsidian beat. **Never cut:** the core demo that already works.

---

## Demo (4 minutes) — the current 8 beats plus 3 new ones

1. Wi-Fi off → **0 external connections**
2. Overview → the timeline and the fix that didn't hold
3. Ask a suggested question → cited answer
4. **NEW** Switch to Qwen, ask again → same memory, different brain
5. Drop INC-301 → it links to three older incidents
6. WHY THIS? → the evidence
7. Pre-flight on CHG-88 → warning
8. Drop the poisoned postmortem → quarantined; external email → blocked
9. Approve the vault note → **NEW** open Obsidian graph view
10. **NEW** Scale card: 500 incidents, still 2 clusters, sub-second linking
11. Audit ledger → tamper → chain broken

---

## Judge questions — have these answers ready

**"Is this just ChatGPT on your documents?"** No. The unit of intelligence is the failure pattern, not the
document. It links incidents that different teams treated as separate, proves which fixes didn't hold, and
warns before the next change. ChatGPT answers when asked; this checks changes before they ship.

**"How does it work with no internet?"** The model is a 2 GB file running on this laptop's GPU through Ollama.
Internet was needed once, to download it. Most of the analysis uses no model at all — it's SQL, vector maths
and timestamp comparisons.

**"How do you know it found the real root cause?"** We don't claim certainty. It's an evidence-backed
hypothesis, and every fix becomes a prediction the timeline grades.

**"Does it scale?"** A new incident is compared with cluster centroids, not every past incident — cost grows
with the number of clusters, not incidents squared. [Show the scale card.]

**"What if a document tells the AI to do something?"** Retrieved content is evidence, not authority. Injected
instructions are quarantined, and only the policy table can authorise an action.

**"Why SQLite and not Postgres?"** Zero install on Windows for the prototype. The schema mirrors the
Postgres + pgvector design one-to-one; Postgres is the path for multi-user deployments.

**"Did you build this before the hackathon?"** The organisers ran a mentored build phase from 22–28 Sept, and
we used it. During the 24 hours we added [model swap, scale proof, importer] and measured the latency.
