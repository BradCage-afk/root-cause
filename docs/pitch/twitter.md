# X (Twitter) post — Root Cause

Post **after** submission, or right after the hackathon with the demo video. Images come from
`root-cause/docs/screenshots/` (regenerate any time with `python scripts/screenshots.py`; add `--dark` for dark ones).
X allows 4 images per post, 280 characters per post (unless the account has Premium).

---

## Option A — single post (fits 280 characters)

> Every company fixes the same outage again and again, in different teams, under different names.
>
> We built Root Cause for #ASYNC26: an offline AI that links them, proves which "permanent fixes" never
> held, and warns before you repeat them.
>
> Wi-Fi off. One laptop. 0 bytes sent out.

**Images (4):**
1. `00-overview.png` — the dashboard: top recurring problem, the timeline with "didn't hold" markers
2. `03-why-linked.png` — four teams, one cause, with how sure it is for each link
3. `06-check-a-change.png` — the warning before a risky change ships
4. `07-hidden-instructions-blocked.png` — the poisoned document caught

Or attach the **demo video** (best reach) instead of images — trim a 30–45 s cut: Wi-Fi off → new incident
links → "didn't hold" → change warning.

---

## Option B — thread (6 posts)

**1/**
> Every org fixes the same failure again and again — different teams, different symptoms, one root cause.
> Nobody connects them.
>
> For #ASYNC26 (Sovereign AI track) we built Root Cause: causal memory that runs entirely offline, on one
> laptop. 🧵

📎 demo video, or `00-overview.png`

**2/**
> A checkout outage. A search indexing lag. A gateway health-check storm. A notification failure.
>
> Four teams, four postmortems. Root Cause links all four to one exhausted DB connection pool — and shows
> the evidence for every link.

📎 `03-why-linked.png`

**3/**
> Our USP: Proof of Fix.
>
> Every recorded fix is a prediction. The timeline grades it. "Raise pool size to 200" was logged as
> permanent — it came back 3 more times.
>
> Not the AI's opinion. A timestamp comparison.

📎 `05-failure-debt.png`

**4/**
> It warns *before*, not after.
>
> Paste a change plan → Root Cause checks it against every recurring problem and the fixes that already
> failed, before it ships.

📎 `06-check-a-change.png`

**5/**
> Sovereign by design:
> • Llama 3.2 3B on an RTX 3050 via Ollama
> • 0 external connections (live egress monitor)
> • prompt injection quarantined, policy blocks external sends
> • hash-chained audit trail
> • swap the model live — the memory stays yours

📎 `07-hidden-instructions-blocked.png` + `10-audit-tamper-detected.png`

**6/**
> Measured, not claimed: 500 incidents, ~1 ms to link a new one, 145× fewer comparisons, 90% of links
> correct.
>
> Built by Team Track and Field. Code: github.com/BradCage-afk/root-cause
> #SovereignAI #LocalAI #SRE

📎 `11-scale-test.png`

---

## Hashtags and tags

- Hashtags (use 2–4, not all): **#ASYNC26** · #SovereignAI · #LocalAI · #Ollama · #SRE · #DevOps · #BuildInPublic
- Tag: the official ASYNC'26 / Ramaiah Institute of Technology (MSRIT) accounts and the track sponsors —
  **check their exact handles on the event page first**; don't guess handles.
- Tag teammates by their X handles.
- Optional: @ollama (they often repost local-AI projects).

## Tips

- Best images: **light theme** reads better in the X feed on phones; use `--dark` screenshots only if the
  post is about the dark UI.
- Crop to the interesting part — X shows images at 16:9 in the feed. The `deck-*.jpg` crops
  (`deck-why.jpg`, `deck-preflight.jpg`, `deck-policy.jpg`) work well.
- Alt text for every image (X → "+Alt"), e.g. *"Root Cause dashboard showing one recurring problem across
  three teams and two fixes marked 'didn't hold'."*
- Pin the thread to the team profile for judges who look you up.
- Don't post the repo link until you're happy for it to be public (it already is public on GitHub).

## LinkedIn version (reuse)

Take thread posts 1–3 and 5–6 as paragraphs, add one line per teammate with their role, attach the video.
