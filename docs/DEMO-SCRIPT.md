# Demo video script — 3 minutes

**Record on the RTX 3050 laptop, with Ollama running.** Before you press record:

- [ ] `.venv\Scripts\python -m rootcause.check` ends with **Ready to record**
- [ ] App open at http://127.0.0.1:8000, browser full-screen (F11), zoom 90%
- [ ] **Live demo controls → Reset demo**
- [ ] Notifications off (Focus assist), other windows closed
- [ ] Explorer open on `root-cause\demo\` in a second window, in case you drag files

**Recorder:** Windows **Win + Alt + R** (Xbox Game Bar) records the active window. Or OBS.
Trim in Clipchamp (built into Windows). Record each scene separately if that's easier — cut them together.

Read the lines naturally. They're a guide, not a script to recite.

---

### 0:00 — Hook (on the app's Ask page)

> "Every organisation fixes the same failure again and again — in different teams, with different
> symptoms — because nobody connects them. This is Root Cause. It runs entirely on this laptop."

### 0:12 — Beat 1: sovereign (point at the header)

**Turn Wi-Fi off on camera** (click the Wi-Fi icon in the taskbar).

> "Wi-Fi is off. The model is Llama 3.2, 3 billion parameters, running on this RTX 3050. The egress
> monitor reads zero external connections, and it stays at zero for the whole demo."

### 0:25 — Beat 2: ask

Ask: **What caused the checkout timeouts in January?** Click a citation chip.

> "Every claim cites the chunk it came from. Ask something outside the record and it says so instead
> of guessing."

(Optional: ask *What is the capital of France?* → "Nothing in the record covers that.")

### 0:45 — Beat 3: a new incident arrives

**Live demo controls → ① Drop new incident INC-301.** Pause on the BLOCK / RANK / JUDGE trace.

> "A new incident from the notifications team. Root Cause didn't compare it with every past incident —
> it checked the clusters sharing its dependencies, ranked them against their centroids, and had the
> model judge it against a real past incident. It just linked it to three older ones."

### 1:05 — Beat 4: why

**Recurrence clusters → WHY THIS?** Scroll slowly.

> "Four incidents, four teams — payments, search, platform, notifications — all tracing back to one
> exhausted connection pool. Here's the shared dependency, the evidence, and the confidence for every
> link. Nothing here is asserted — you can inspect every step."

### 1:30 — Beat 5: the fix that didn't work

Point at **REM-31 ✗ ineffective**. Then **Failure debt**.

> "In January, the team recorded this as a permanent fix. The timeline says otherwise — three
> recurrences since. That's not the model's opinion, it's a timestamp comparison. Failure debt ranks
> what's still unpaid: recurrence times persistence times impact times spread. And every fix is a
> prediction — here's which ones held."

### 1:55 — Beat 6: before the next change

**Pre-flight check → Load CHG-88 → Run pre-flight.**

> "Now someone plans to double the reindex workers. Before it ships, Root Cause warns them: this touches
> the component behind that cluster, and the last two fixes didn't hold."

### 2:15 — Beat 7: a poisoned document

**Live demo controls → ② Drop poisoned postmortem PM-199.** The red banner appears.

> "This postmortem contains hidden instructions telling the AI to email the whole vault outside. It's
> quarantined — retrieved content is evidence, not authority."

**Actions & policy → Propose: email vault to external address** → BLOCKED.

> "And even if an agent tried, the policy gate blocks any external send."

### 2:35 — Beat 8: governed action + audit

**Recurrence clusters → Write note to Obsidian vault → Actions → Approve.**

> "Safe actions wait for a human. Approved — the cluster note is now in the team's own Obsidian vault,
> as plain markdown."

**Audit ledger** → chain intact → **Tamper with an entry** → broken.

> "Every step is in a hash-chained ledger. Edit one entry, and the chain breaks."

### 2:55 — Close

> "Root Cause. Sovereign causal memory — it finds what your organisation keeps fixing, and why it keeps
> happening. Team Track and Field."

---

**If something goes wrong mid-take:** Live demo controls → Reset demo, and redo that scene.
