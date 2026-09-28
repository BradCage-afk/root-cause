"""Runtime configuration. Everything is local; there is no setting that points off-box."""
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
VAULT = Path(os.environ.get("RC_VAULT", ROOT / "vault"))
DB_PATH = Path(os.environ.get("RC_DB", ROOT / "data" / "rootcause.db"))
WEB_DIR = ROOT / "web"

OLLAMA_URL = os.environ.get("RC_OLLAMA_URL", "http://127.0.0.1:11434")
CHAT_MODEL = os.environ.get("RC_CHAT_MODEL", "llama3.2:3b")
JUDGE_MODEL = os.environ.get("RC_JUDGE_MODEL", "llama3.2:3b")
EMBED_MODEL = os.environ.get("RC_EMBED_MODEL", "nomic-embed-text")
NUM_CTX = int(os.environ.get("RC_NUM_CTX", "4096"))
# "auto" uses Ollama when reachable, "fallback" never calls a model (tests, CPU-only boxes)
MODE = os.environ.get("RC_MODE", "auto")

# Recurrence linking thresholds (see docs/ARCHITECTURE.md, "Recurrence linking")
# RANK floor depends on the vector space: semantic embeddings (Ollama) and the hashed
# fallback live on different similarity scales. Precision comes from ADJUDICATE, not RANK.
SIM_MIN = float(os.environ.get("RC_SIM_MIN", "0.30"))
SIM_MIN_HASH = float(os.environ.get("RC_SIM_MIN_HASH", "0.12"))
TOP_K = int(os.environ.get("RC_TOP_K", "5"))
CONF_MIN = float(os.environ.get("RC_CONF_MIN", "0.60"))
# ADJUDICATE judge: "hybrid" averages the local model's verdict with the deterministic
# factor-overlap score (default); "llm" trusts the model alone; "rules" never calls it.
JUDGE = os.environ.get("RC_JUDGE", "hybrid")
# Hybrid veto: the model may promote a link only when the cause language already partly
# supports it. Below this deterministic score, no model verdict can create a link.
RULES_FLOOR = float(os.environ.get("RC_RULES_FLOOR", "0.45"))

# Folders inside the vault the system may write to. Everything else is human-authored.
WRITABLE_DIRS = ("clusters",)
SKIP_DIRS = ("clusters", ".obsidian", ".trash")

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def assert_local(url: str) -> str:
    """Sovereignty guard: refuse any model endpoint that is not on this machine or LAN."""
    host = urlparse(url).hostname or ""
    if host in _LOCAL_HOSTS or host.startswith(("10.", "192.168.", "172.")) or host.endswith(".local"):
        return url
    raise ValueError(f"Refusing non-local model endpoint {url!r}: Root Cause never calls out.")


assert_local(OLLAMA_URL)

# An LLM "Nothing in the record" is overridden with quoted evidence when the best passage is at
# least this similar to the question (semantic space only; on the demo vault off-topic
# questions score <= 0.49 and real ones >= 0.62 with nomic-embed-text).
ANSWER_SIM = float(os.environ.get("RC_ANSWER_SIM", "0.58"))
