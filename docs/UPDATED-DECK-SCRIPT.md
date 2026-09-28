# Root Cause — updated deck + demo script

**Team Track and Field · ASYNC'26 · Track 1 Sovereign AI** · updated 28 Sept 2026

Three parts:

- **A.** What to say on each of the 9 slides (about 4 minutes)
- **B.** The live demo (about 3 minutes, run from **Guided demo** in the app)
- **C.** Quick answers for judges

Read naturally. These are guides, not lines to memorise.

**Timing at a glance**

| Part | Time |
|---|---|
| Slides 1–6 | ~3 min |
| Live demo | ~3 min |
| Slides 7–9 (or skip, since the demo showed it) | ~1 min |
| Questions | whatever is left |

If you only have 5 minutes: slides 1–3, the demo, then slide 9.

---

## A. Slide-by-slide pitch

### Slide 1 — Title (15 s)
> "We're Track and Field, and this is **Root Cause** — sovereign causal memory for operations. It runs
> entirely on this laptop: open-weight models, no internet, no API keys. It finds the failures a team keeps
> re-fixing, explains why they keep happening, and warns before the same change ships again."

Point at the three numbers: **0 bytes** out, **100% local**, **one RTX 3050**.

### Slide 2 — The problem (40 s)
> "Every organisation runs this loop: failure, workaround, service restored, ticket closed. Teams are
> measured on restoring service, so the symptom goes away — but the cause survives and comes back in another
> team, wearing a different symptom.
>
> The lessons *are* written down, in postmortems and tickets, but nobody assembles them. And this is the
> worst data to hand to a cloud AI: it maps credentials, internal systems and where the company is weakest."

### Slide 3 — The solution (40 s)
> "Not AI that knows what happened — AI that understands *why it keeps happening*.
>
> Here, three incidents from three different teams trace back to one exhausted connection pool. The January
> fix was recorded as permanent — and the timeline shows three recurrences since. That verdict comes from
> timestamps, not from the model.
>
> The pipeline is the Sovereign AI track exactly: Observe, Model, Remember, Diagnose, Act — Data to Knowledge
> to Memory to Reasoning to Action."

### Slide 4 — What's different (45 s)
> "The unit of intelligence isn't the document. It's the failure pattern.
>
> One: **recurrence linking, not search** — incidents only join when they share a dependency, are similar to
> the cluster, *and* a judge confirms it against a real past incident.
> Two: **it warns before the change**, not after.
> Three: **failure debt is a number** — recurrence times persistence times impact times spread. The model
> doesn't decide it.
> Four — our USP, **Proof of Fix**: every fix is a falsifiable prediction, and the timeline grades it.
>
> A normal AI goes question, retrieve, answer — and stops. Root Cause keeps going to verify the outcome."

### Slide 5 — Can you build it? (30 s)
> "It's built. One RTX 3050 laptop, Llama 3.2 3B through Ollama, SQLite with full-text and vector search,
> FastAPI, an MCP server, and a policy gate. Seventeen automated tests pass. On our seeded corpus of 37
> documents it finds exactly the two real recurring problems, and it correctly rejects a near-miss that
> shares a database but has a different cause."

### Slide 6 — What will you achieve? (20 s)
> "Zero bytes of egress, measured live. Every claim traceable to its source. And these seven moments are
> what you're about to see — so let me show you instead of telling you."

→ **Switch to the app now and run Part B.**

### Slide 7 — The dashboard (20 s, after the demo or skip)
> "One screen: live counters, the highest failure debt, the timeline that proves which fixes didn't hold,
> and questions answered only from your own records."

### Slide 8 — Inside the prototype (20 s, or skip)
> "The four moments you just saw: evidence for every link, the warning before a change, a poisoned
> document stopped, and a tamper-evident audit trail."

### Slide 9 — Project status (30 s)
> "Everything in our idea deck runs — plus a live model swap and a 500-incident scale test. We changed a few
> things for an offline laptop: SQLite instead of Postgres with the same schema, one page instead of
> Next.js. In the 24 hours we'll measure answer latency on the GPU, run the scale test with the model judge,
> and add a Jira and ServiceNow importer. The code is public on GitHub.
>
> Root Cause — it finds what your organisation keeps fixing, and why it keeps happening. Thank you."

---

## B. Live demo — about 3 minutes

**Before you start:**

- `.venv\Scripts\python -m rootcause.check` says **Ready to record**.
- The browser is full-screen (F11) at 90% zoom.
- Theme is **light** if you're on a projector in a bright room, **dark** for a screen recording.
- **Guided demo → 1 · Start clean → Go**.
- Notifications are off.
- To let judges follow on their phones, start **`share.bat`** instead of `run.bat` and show them the printed
  link. They must be on the same hotspot.

Every step below is a numbered **Go** button on the **Guided demo** page.

**0:00 — Offline.** Turn Wi-Fi off on camera. Point at the header: **Offline · nothing sent out**.
> "Wi-Fi is off. The model is Llama 3.2, 3 billion parameters, on this RTX 3050. 'Data sent outside' stays
> at zero for the whole demo."

**0:15 — Ask (step 2).** Click **What caused the checkout timeouts in January?** Click a numbered source.
> "Every claim cites the record it came from."

Optional: type *How many gears does a tractor have?* → "That isn't in your records."
> "It won't guess outside your data."

If the answer says **"The AI model held back, so these lines are quoted directly from your records"**, that's
fine and on purpose:
> "When the small model is unsure, it shows the source lines instead of making something up."

These questions reliably work:

- What caused the checkout timeouts in January?
- What is pgbouncer-main and who uses it?
- Why do internal certificates keep expiring?
- Why did search indexing fall behind?

**0:35 — Swap the brain.** Header → **AI model** → **qwen2.5:3b**. Ask again.
> "A different model, the same sources and the same memory. The brain is replaceable — the memory is yours."

**0:45 — New incident (step 3).** Pause on the four steps.
> "A new incident from the notifications team. Root Cause only looked at problems sharing its dependencies,
> picked the closest, and checked it against a real past incident. It just linked it to three older ones."

**1:05 — Why (step 4).** Scroll slowly.
> "Four teams — payments, search, platform, notifications — one exhausted connection pool. Same dependency,
> same kind of failure, and how sure it is for every link."

**1:25 — Proof of Fix (step 5).** Point at the red **Didn't hold** tags, then **Failure debt**.
> "January's 'permanent fix' — the problem came back three times. That's a timestamp comparison, not the
> model's opinion. Failure debt ranks what's still unpaid."

**1:50 — Before the next change (step 6).**
> "Someone plans to double the reindex workers. Before it ships: this touches the dependency behind that
> problem, and the last two fixes didn't hold."

**2:10 — Poisoned document (steps 7 and 8).**
> "This postmortem hides instructions telling the AI to email the vault outside. Quarantined — documents
> are evidence, not authority." … "And if an agent tries anyway, the policy blocks it. Nothing was sent."

**2:30 — Approve + audit (steps 9 and 10).** Press **Approve**, then **Tamper test**.
> "Safe actions wait for a human — the note is now in the team's Obsidian vault. Every step is sealed in a
> hash-chained audit trail. Edit one past event, and it's caught."

**2:45 — Scale test (optional).** Sidebar → **Scale test** → **Run the scale test**. It takes about
**2–3 seconds**.
> "500 incidents with known answers: a new one is matched in about a millisecond, with 145 times fewer
> comparisons than checking every pair, and 90% of the links it makes are correct. It also shows where it
> still misses."

**2:55 — Close.**
> "Root Cause — sovereign causal memory. Team Track and Field."

**If something goes wrong:** **Guided demo → Start clean → Go**, and redo that step.

---

## C. Judge questions — short answers

**"Is this just ChatGPT on documents?"**
No. The unit is the failure pattern. It links incidents different teams treated as separate, proves which
fixes didn't hold, and warns before the next change.

**"No internet — how does the AI work?"**
The model is a 2 GB file running on this GPU through Ollama. Most of the analysis — linking, debt, fix
grading — is SQL, vector maths and timestamps, with no model at all.

**"How do you know it's the real root cause?"**
We don't claim certainty. It's an evidence-backed hypothesis, and every fix becomes a prediction the
timeline grades.

**"Does it scale?"**
A new incident is compared with cluster centroids, not every past incident. On the scale test: 500
incidents, about 1 ms per new incident, 145× fewer comparisons. We report the misses too — 65% of true
links found with the rules judge; the model judge is there to raise it.

**"What if a document tells the AI to do something?"**
It's quarantined before it reaches a prompt, and only the fixed policy table can authorise an action.

**"Why did the answer quote the records instead of writing one?"**
Small local models sometimes decline even when the evidence is clear. When the match is strong, we show
the cited source lines rather than hide them — never an invented answer.

**"Why SQLite, not Postgres?"**
Zero install on Windows. The schema mirrors Postgres + pgvector one-to-one for multi-user deployments.

**"Can big firms use this?"**
Yes — one GPU server per organisation, or per client for consulting firms. Data never leaves their
boundary, and existing agents connect over MCP under the same policy gate.

**"Did you build it before the hackathon?"**
During the mentored build phase, 22–28 Sept. In the 24 hours we're adding measured latency, the GPU scale
run and the importer.
