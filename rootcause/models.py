"""Local model layer: Ollama when reachable, a deterministic fallback when not.

The fallback exists so the pipeline runs on any machine (tests, CPU-only laptops)
and so a model hiccup on stage degrades the demo instead of crashing it. The UI
always shows which mode is active.
"""
import hashlib
import json
import re
import time

import httpx
import numpy as np

from . import config

_state = {"checked": 0.0, "ok": False, "models": []}
FALLBACK_DIM = 512
_WORD = re.compile(r"[a-z0-9][a-z0-9\-]+")
_STOP = set("""a an the and or of to in on for with by at from is are was were be been it its this
that as not no into over under after before during than then so but if we our they their
there these those which who what when where while about all any can could should would""".split())


def _stem(w: str) -> str:
    for suf in ("ations", "ation", "ings", "ing", "ed", "es", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def tokens(text: str):
    return [_stem(w) for w in _WORD.findall(text.lower()) if w not in _STOP]


def ollama_up() -> bool:
    if config.MODE == "fallback":
        return False
    now = time.time()
    if now - _state["checked"] < 15:
        return _state["ok"]
    _state["checked"] = now
    try:
        r = httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=2.0)
        _state["models"] = [m["name"] for m in r.json().get("models", [])]
        _state["ok"] = r.status_code == 200
    except Exception:
        _state["ok"] = False
    return _state["ok"]


def status() -> dict:
    up = ollama_up()
    have = _state["models"]
    def present(m):
        return any(x == m or x.startswith(m + ":") or x.split(":")[0] == m for x in have)
    return {
        "mode": "ollama" if up else "fallback",
        "endpoint": config.OLLAMA_URL,
        "chat_model": config.CHAT_MODEL, "embed_model": config.EMBED_MODEL,
        "chat_ready": up and present(config.CHAT_MODEL),
        "embed_ready": up and present(config.EMBED_MODEL),
    }


def embed_space() -> str:
    """Identifies the vector space so stored vectors are never mixed across models."""
    s = status()
    return f"ollama:{config.EMBED_MODEL}" if s["embed_ready"] else f"hash:{FALLBACK_DIM}"


# ---------------------------------------------------------------- embeddings
def _hash_embed(text: str) -> np.ndarray:
    v = np.zeros(FALLBACK_DIM, dtype=np.float32)
    toks = tokens(text)
    grams = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
    for g in grams:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        v[h % FALLBACK_DIM] += 1.0 if (h >> 64) & 1 else -1.0
    n = np.linalg.norm(v)
    return v / n if n else v


def embed(texts):
    if status()["embed_ready"]:
        try:
            r = httpx.post(f"{config.OLLAMA_URL}/api/embed",
                           json={"model": config.EMBED_MODEL, "input": list(texts)}, timeout=120)
            r.raise_for_status()
            out = []
            for e in r.json()["embeddings"]:
                a = np.asarray(e, dtype=np.float32)
                out.append(a / (np.linalg.norm(a) or 1.0))
            return out
        except Exception:
            pass
    return [_hash_embed(t) for t in texts]


def cosine(a, b) -> float:
    if a is None or b is None or len(a) == 0 or len(b) == 0 or len(a) != len(b):
        return 0.0
    return float(np.dot(a, b) / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1.0))


# ---------------------------------------------------------------- chat
def chat(system: str, user: str, as_json: bool = False, model: str = None):
    """Returns text (or a parsed dict when as_json). None when no model is available."""
    if not status()["chat_ready"]:
        return None
    body = {
        "model": model or config.CHAT_MODEL, "stream": False,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": 0.1, "num_ctx": config.NUM_CTX},
    }
    if as_json:
        body["format"] = "json"
    try:
        r = httpx.post(f"{config.OLLAMA_URL}/api/chat", json=body, timeout=180)
        r.raise_for_status()
        txt = r.json()["message"]["content"]
        return json.loads(txt) if as_json else txt.strip()
    except Exception:
        return None


# ---------------------------------------------------------------- model swap
_EMBED_HINTS = ("embed", "minilm", "bge-", "e5-")


def available_chat_models():
    """Chat-capable models the local Ollama server has on disk (embedding models excluded)."""
    if not ollama_up():
        return []
    return sorted(m for m in _state["models"] if not any(h in m.lower() for h in _EMBED_HINTS))


def set_chat_model(name: str) -> str:
    """Switch the answering model at runtime. Embeddings, clusters and the ledger are untouched:
    the memory stays exactly the same, only the model that writes prose changes."""
    have = available_chat_models()
    match = next((m for m in have if m == name or m.split(":")[0] == name or m == name + ":latest"), None)
    if not match:
        raise ValueError(f"{name!r} is not installed. Available: {', '.join(have) or 'none'}")
    config.CHAT_MODEL = match
    _state["checked"] = 0.0
    return match
