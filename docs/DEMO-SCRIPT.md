# Demo video script — 3 minutes

> **Newer, combined version:** [UPDATED-DECK-SCRIPT.md](UPDATED-DECK-SCRIPT.md) — slide-by-slide pitch, this
> demo (updated), and judge answers in one file.

**Record on the RTX 3050 laptop, with Ollama running.** Before you press record:

- [ ] `.venv\Scripts\python -m rootcause.check` ends with **Ready to record**
- [ ] App open at http://127.0.0.1:8000, browser full-screen (F11), zoom 90%
- [ ] **Theme:** the moon/sun button top-right. Use **light** for a projector in a bright room; dark looks
      better in a screen recording. Pick one and keep it for the whole video.
- [ ] Sidebar → **Guided demo** → **1 · Start clean → Go**
- [ ] Notifications off (Focus assist), other windows closed

**Recorder:** Windows **Win + Alt + R** (Xbox Game Bar) records the active window. Or OBS.
Trim in Clipchamp (built into Windows). Record each scene separately if that's easier — cut them together.

**The easy way:** every beat below is a numbered step on the **Guided demo** page. Press its **Go** button
and the app jumps to the right screen. You can run the whole demo from that one checklist.

Read the lines naturally. They're a guide, not a script to recite.

---

### 0:00 — Hook (on the Overview)

> "Every organisation fixes the same failure again and again — in different teams, with different
> symptoms — because nobody connects them. This is Root Cause. It runs entirely on this laptop."

### 0:12 — Beat 1: sovereign (point at the header chips)

**Turn Wi-Fi off on camera** (click the Wi-Fi icon in the taskbar).

> "Wi-Fi is off. The model is Llama 3.2, 3 billion parameters, running on this RTX 3050. The header says
> 'Offline · nothing sent out', and the 'Data sent outside' counter stays at zero for the whole demo."

### 0:25 — Beat 2: ask (step 2)

Click the suggested question **What caused the checkout timeouts in January?** Click a numbered source.

> "Every claim cites the record it came from. Ask something outside the record and it says so instead
> of guessing."

(Optional: ask *How many gears does a tractor have?* → "That isn't in your records.")

### 0:38 — Swap the brain (needs `ollama pull qwen2.5:3b` beforehand)

Header → **AI model** dropdown → pick **qwen2.5:3b**. Ask the same question again.

> "Same question, a different model. Same sources, same problems, same audit trail. The brain is
> replaceable — the memory is yours."

### 0:45 — Beat 3: a new incident arrives (step 3)

**Add a new incident → Go.** Pause on the four steps.

> "A new incident from the notifications team. Root Cause didn't compare it with every past incident —
> it looked only at problems sharing its dependencies, picked the closest, and checked it against a real
> past incident. It just linked it to three older ones."

### 1:05 — Beat 4: why (step 4)

**Show why they are linked → Go.** Scroll slowly. Open **Technical details** if you want the numbers.

> "Four incidents, four teams — payments, search, platform, notifications — all tracing back to one
> exhausted connection pool. Same dependency, same kind of failure, and how sure it is for every link.
> Nothing here is asserted — you can inspect every step."

### 1:30 — Beat 5: the fix that didn't work (step 5)

Point at the red **Didn't hold** tags on the timeline. Then **Failure debt**.

> "In January, the team recorded this as a permanent fix. The timeline says otherwise — three
> recurrences since. That's not the model's opinion, it's a timestamp comparison. Failure debt ranks
> what's still unpaid: recurrence times persistence times impact times spread. And every fix is a
> prediction — here's which ones held."

### 1:55 — Beat 6: before the next change (step 6)

**Check a planned change → Go.** The amber warning appears.

> "Now someone plans to double the reindex workers. Before it ships, Root Cause warns them: this touches
> the dependency behind that recurring problem, and the last two fixes didn't hold."

### 2:15 — Beat 7: a poisoned document (steps 7 and 8)

**Add a poisoned document → Go.** The red banner appears.

> "This postmortem contains hidden instructions telling the AI to email the whole vault outside. It's
> quarantined — retrieved content is evidence, not authority."

**Try a forbidden action → Go** → Blocked.

> "And even if an agent tried, the policy blocks any external send. Nothing was sent."

### 2:35 — Beat 8: governed action + audit (steps 9 and 10)

**Approve a safe action → Go**, then press **Approve**.

> "Safe actions wait for a human. Approved — the problem note is now in the team's own Obsidian vault,
> as plain markdown."

**Tamper test → Go** → "Tampering detected".

> "Every step is sealed into a hash-chained audit trail. Edit one past event, and it's caught."

### 2:50 — Scale (optional)

Sidebar → **Scale test**.

> "At 500 incidents, a new one is matched in about a millisecond — 145 times fewer comparisons than
> checking every pair — measured against known answers, including where it still misses."

### 2:55 — Close

> "Root Cause. Sovereign causal memory — it finds what your organisation keeps fixing, and why it keeps
> happening. Team Track and Field."

---

**If something goes wrong mid-take:** Guided demo → **Start clean → Go**, and redo that scene.
