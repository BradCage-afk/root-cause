# Setup on Windows (RTX 3050 laptop)

About 20 minutes, most of it downloading. Internet is needed **once**. After that, Root Cause runs
with Wi-Fi switched off.

## 1. Install two things

| | Where | Notes |
|---|---|---|
| **Python 3.11 or newer** | [python.org/downloads](https://www.python.org/downloads/) | Tick **"Add python.exe to PATH"** on the first screen |
| **Ollama** | [ollama.com/download/windows](https://ollama.com/download/windows) | Runs in the system tray and uses the RTX 3050 automatically |

Check both in a new terminal:

```bat
py --version
ollama --version
nvidia-smi
```

## 2. Get the code

```bat
git clone https://github.com/BradCage-afk/root-cause.git
cd root-cause
```

No git? Download the ZIP from the GitHub page and extract it.

## 3. Set up

```bat
setup.bat
```

This creates `.venv`, installs the Python packages and pulls two models:

| Model | Size | Job |
|---|---|---|
| `llama3.2:3b` | ~2.0 GB | answers, adjudication, pre-flight wording — fits fully in 4 GB VRAM |
| `nomic-embed-text` | ~0.3 GB | embeddings |

## 4. Run

```bat
run.bat
```

Your browser opens at **http://127.0.0.1:8000**. The header should read
**Local model: llama3.2:3b · nomic-embed-text**. If it says *Fallback mode*, Ollama isn't running —
open it from the Start menu.

The first start embeds the whole vault. Give it a minute.

## 5. Check before you record

```bat
.venv\Scripts\python -m rootcause.check
```

Every line should say **PASS** and it should end with **Ready to record.**

If anything says FAIL, the local model is judging a pair differently from the tested rules. Use the
deterministic judge (the model still writes answers and warnings):

```bat
set RC_JUDGE=rules
run.bat
```

## 6. Prove it's offline

Turn Wi-Fi off, refresh the page, ask a question. It still answers. The header still reads
**Egress: 0 external connections**.

---

## Fully offline install (for the venue — no Wi-Fi there)

Do this at home, with internet, **before** 30 Sept:

1. `bundle-offline.bat` — saves every Python package into `wheels\`
2. Copy the whole `root-cause` folder **and** `%USERPROFILE%\.ollama\models` onto a USB stick
3. Make a second copy on a second stick, carried by a different person

At the venue, on any Windows laptop with Python and Ollama installed:

1. Copy the `root-cause` folder off the stick
2. Copy `models` back into `%USERPROFILE%\.ollama\`
3. `setup.bat` — it sees `wheels\` and installs with no network; the `ollama pull` lines find the
   models already present

## Troubleshooting

| Symptom | Fix |
|---|---|
| `py` not found | Reinstall Python with "Add to PATH" ticked, open a **new** terminal |
| Header says *Fallback mode* | Start Ollama from the Start menu; wait 10 s; refresh |
| Answers slow (> 10 s) | Check `nvidia-smi` shows the model on the GPU; close other GPU apps; use a cooling pad |
| Port 8000 in use | Close the other app, or edit the port at the bottom of `rootcause\app.py` |
| Demo state is messy | **Guided demo → Start clean → Go** |
| Want a clean start | Stop the app, delete the `data\` folder, run again |

## Settings (environment variables)

| Variable | Default | |
|---|---|---|
| `RC_CHAT_MODEL` | `llama3.2:3b` | e.g. `qwen2.5:3b` for the model-swap demo |
| `RC_EMBED_MODEL` | `nomic-embed-text` | changing it triggers a full re-embed on next start |
| `RC_JUDGE` | `hybrid` | `hybrid`, `llm` or `rules` |
| `RC_MODE` | `auto` | `fallback` never calls a model |
| `RC_CONF_MIN` | `0.60` | adjudication confidence needed to join a cluster |
