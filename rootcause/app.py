"""Root Cause — FastAPI backend and live vault watcher.

Run:  python -m rootcause.app      then open http://127.0.0.1:8000
"""
import json
import os
import shutil
import subprocess
import sys
from contextlib import asynccontextmanager
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import audit, cluster, config, debt, egress, ingest, models, policy, preflight, search
from .db import connect, rows

LOCK = threading.RLock()
con = connect()
con.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
DEMO_DIR = config.ROOT / "demo"
EVENTS = []  # recent live events for the UI ticker
RECENT = {}  # path -> time ingested via the API, so the watcher does not double-ingest


def event(kind, text):
    EVENTS.append({"ts": time.time(), "kind": kind, "text": text})
    del EVENTS[:-30]


def _meta(k, v=None):
    if v is None:
        r = con.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
        return r[0] if r else None
    con.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, v))
    con.commit()


def rebuild(reason="bootstrap"):
    with LOCK:
        for t in ("documents", "chunks", "incidents", "remediations", "decisions", "clusters",
                  "cluster_members", "cluster_nodes", "predictions", "actions", "audit_log"):
            con.execute(f"DELETE FROM {t}")
        con.execute("DELETE FROM chunks_fts")
        con.commit()
        t0 = time.time()
        docs = ingest.ingest_vault(con)
        traces = cluster.recluster(con)
        debt.predictions(con)
        _meta("space", models.embed_space())
        audit.record(con, "system", "BOOTSTRAP", {
            "reason": reason, "documents": len(docs), "incidents": len(traces),
            "clusters": len(cluster.recurrence_clusters(con)), "mode": models.status()["mode"],
            "seconds": round(time.time() - t0, 1)})
        event("system", f"Loaded {len(docs)} documents, {len(traces)} incidents replayed chronologically")
        return {"documents": len(docs), "seconds": round(time.time() - t0, 1)}


def ingest_path(path: Path, actor="watcher"):
    RECENT[str(path.resolve())] = time.time()
    with LOCK:
        res = ingest.ingest_file(con, path, actor=actor)
        trace = None
        if res["kind"] == "incident":
            already = con.execute("SELECT 1 FROM cluster_members WHERE incident_id=?", (res["id"],)).fetchone()
            if not already:
                trace = cluster.link_incident(con, res["id"])
        debt.predictions(con)
        audit.record(con, actor, "INGESTED", {"document": res["id"], "kind": res["kind"],
                                               "quarantined": res["quarantined"],
                                               "cluster": (trace or {}).get("result")})
        if res["quarantined"]:
            event("danger", f"{res['id']} quarantined: {res['reason']}")
        elif trace and "joined" in trace["result"]:
            event("link", f"{res['id']} joined {trace['result']['joined']}")
        else:
            event("info", f"Ingested {res['id']}")
        return {**res, "trace": trace}


# ---------------------------------------------------------------- watcher
def start_watcher():
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        return
    seen = {}

    class H(FileSystemEventHandler):
        def on_any_event(self, e):
            if e.is_directory or not str(e.src_path).endswith(".md") or e.event_type not in ("created", "modified", "moved"):
                return
            p = Path(getattr(e, "dest_path", "") or e.src_path)
            rel = p.relative_to(config.VAULT).parts if p.is_relative_to(config.VAULT) else ("",)
            if rel[0] in config.SKIP_DIRS or not p.exists():
                return
            if time.time() - seen.get(p, 0) < 2 or time.time() - RECENT.get(str(p.resolve()), 0) < 5:
                return
            seen[p] = time.time()
            time.sleep(0.4)  # let the writer finish
            if time.time() - RECENT.get(str(p.resolve()), 0) < 5:
                return
            try:
                ingest_path(p)
            except Exception as ex:  # never kill the watcher
                event("danger", f"ingest failed for {p.name}: {ex}")

    obs = Observer()
    obs.schedule(H(), str(config.VAULT), recursive=True)
    obs.daemon = True
    obs.start()


# ---------------------------------------------------------------- API
@asynccontextmanager
async def lifespan(_app):
    empty = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 0
    if empty or _meta("space") != models.embed_space():
        m = models.status()
        print(f"Building memory from the vault ({m['mode']} mode) - first start takes about a minute...",
              flush=True)
        res = rebuild("startup" if empty else "embedding model changed")
        print(f"Loaded {res['documents']} documents in {res['seconds']} s.", flush=True)
    if cluster.backfill_nodes(con):
        print("Upgraded the clustering index for an existing database.", flush=True)
    start_watcher()
    print("Root Cause is ready: http://127.0.0.1:8000   (keep this window open; Ctrl+C to stop)", flush=True)
    if os.environ.get("RC_OPEN_BROWSER", "1") == "1":
        import webbrowser
        webbrowser.open("http://127.0.0.1:8000")
    yield


app = FastAPI(title="Root Cause", version="0.1", lifespan=lifespan)


class Q(BaseModel):
    q: str


class ModelChoice(BaseModel):
    chat_model: str


class Change(BaseModel):
    text: str


class Proposal(BaseModel):
    tool: str
    args: dict = {}


@app.get("/")
def index():
    # no-cache: the browser must pick up a new UI after an update
    return FileResponse(config.WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/api/status")
def status():
    with LOCK:
        q = rows(con, "SELECT id, title, quarantine_reason FROM documents WHERE quarantined=1")
        return {"model": models.status(), "egress": egress.check(), "audit": audit.verify(con),
                "counts": {k: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for k, t in
                           (("documents", "documents"), ("chunks", "chunks"), ("incidents", "incidents"))},
                "recurrence_clusters": len(cluster.recurrence_clusters(con)),
                "quarantined": q, "events": EVENTS[-8:]}


@app.get("/api/models")
def list_models():
    return {"current": config.CHAT_MODEL, "available": models.available_chat_models(),
            "mode": models.status()["mode"], "embed_model": config.EMBED_MODEL}


@app.post("/api/model")
def swap_model(body: ModelChoice):
    before = config.CHAT_MODEL
    try:
        now = models.set_chat_model(body.chat_model)
    except ValueError as e:
        raise HTTPException(400, str(e))
    with LOCK:
        audit.record(con, "operator", "MODEL_SWAPPED", {"from": before, "to": now,
                                                        "memory": "unchanged", "embed_model": config.EMBED_MODEL})
    event("link", f"Now answering with {now}. Same memory, clusters and ledger - different brain.")
    return {"from": before, "to": now}


@app.post("/api/ask")
def ask(body: Q):
    with LOCK:
        out = search.answer(con, body.q)
        out["model"] = config.CHAT_MODEL if out["mode"] == "llm" else None
        audit.record(con, "operator", "QUERY", {"q": body.q, "mode": out["mode"],
                                                "citations": out.get("citations", [])})
        return out


@app.get("/api/clusters")
def clusters():
    with LOCK:
        return cluster.recurrence_clusters(con)


@app.get("/api/clusters/{cid}/why")
def why(cid: str):
    with LOCK:
        c = next((x for x in cluster.recurrence_clusters(con) if x["id"] == cid), None)
        if not c:
            raise HTTPException(404, "no such cluster")
        ids = [m["incident_id"] for m in c["members"]]
        docs = set(ids)
        for r in rows(con, "SELECT id FROM documents"):
            txt = " ".join(x["text"] for x in rows(con, "SELECT text FROM chunks WHERE document_id=?", (r["id"],)))
            if any(i in txt for i in ids) or any(i in (r["id"]) for i in ids):
                docs.add(r["id"])
        ev = [e for e in search.hybrid(con, f"{c['hypothesis']} contributing factors", k=40)
              if e["document_id"] in docs][:7]
        shared = sorted({w for m in c["members"] for w in (m["reason"].get("shared_factor") or "").split(" · ") if w})
        fixes = [f for f in debt.fix_effectiveness(con) if f["cluster_id"] == cid]
        return {"cluster": cid, "hypothesis": c["hypothesis"],
                "incidents": [{"id": m["incident_id"], "team": m["team"], "component": m["component"],
                               "symptom": m["symptom"], "opened_at": m["opened_at"][:10],
                               "similarity": m["similarity"], "confidence": m["confidence"],
                               "judge": m["reason"].get("judge", "seed")} for m in c["members"]],
                "shared_dependencies": c["shared_dependencies"], "teams": c["teams"],
                "shared_factor_terms": shared, "evidence": ev,
                "remediations": [{"id": f["id"], "status": f["status"], "applied_at": f["applied_at"],
                                  "description": f["description"],
                                  "recurred": [x["id"] for x in f["recurrences_after"]]} for f in fixes]}


@app.get("/api/debt")
def get_debt():
    with LOCK:
        return debt.failure_debt(con)


@app.get("/api/fixes")
def get_fixes():
    with LOCK:
        return debt.fix_effectiveness(con)


@app.get("/api/predictions")
def get_predictions():
    with LOCK:
        return debt.predictions(con)


@app.get("/api/decisions")
def get_decisions():
    with LOCK:
        return debt.decisions(con)


@app.post("/api/preflight")
def pre(body: Change):
    with LOCK:
        out = preflight.check(con, body.text)
        audit.record(con, "operator", "PREFLIGHT", {"level": out["level"],
                                                    "clusters": [h["cluster"] for h in out["hits"]]})
        return out


@app.post("/api/ingest")
async def upload(file: UploadFile):
    name = Path(file.filename).name
    if not name.endswith(".md"):
        raise HTTPException(400, "markdown only")
    dest = config.VAULT / "inbox" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    RECENT[str(dest.resolve())] = time.time()
    dest.write_bytes(await file.read())
    return ingest_path(dest, actor="operator")


@app.get("/api/demo")
def demo_files():
    return sorted(p.name for p in DEMO_DIR.glob("*.md"))


@app.get("/api/demo/text/{name}")
def demo_text(name: str):
    src = DEMO_DIR / Path(name).name
    if not src.exists():
        raise HTTPException(404, "no such demo file")
    import frontmatter
    return {"name": src.name, "text": frontmatter.load(src).content.strip()}


@app.post("/api/demo/drop/{name}")
def demo_drop(name: str):
    src = DEMO_DIR / Path(name).name
    if not src.exists():
        raise HTTPException(404, "no such demo file")
    sub = {"INC": "incidents", "PM": "postmortems", "CHG": "changes"}.get(src.stem.split("-")[0], "inbox")
    dest = config.VAULT / sub / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    RECENT[str(dest.resolve())] = time.time()
    shutil.copy(src, dest)
    return ingest_path(dest, actor="operator")


@app.get("/api/actions")
def actions():
    with LOCK:
        out = rows(con, "SELECT * FROM actions ORDER BY id DESC")
        for a in out:
            a["args"] = json.loads(a["args"])
        return {"actions": out, "tools": {t: {"permission": p, "risk": r, "policy": policy.decide(t)[0]}
                                          for t, (p, r) in policy.TOOLS.items()}}


@app.post("/api/actions")
def propose(body: Proposal):
    with LOCK:
        return policy.propose(con, body.tool, body.args, proposed_by="operator")


@app.post("/api/actions/{aid}/{verb}")
def resolve(aid: int, verb: str):
    if verb not in ("approve", "reject"):
        raise HTTPException(400, "approve or reject")
    with LOCK:
        return policy.resolve(con, aid, verb == "approve")


@app.get("/api/audit")
def get_audit():
    with LOCK:
        return {"verify": audit.verify(con),
                "entries": rows(con, "SELECT * FROM audit_log ORDER BY id DESC LIMIT 60")}


@app.post("/api/audit/tamper")
def tamper():
    with LOCK:
        return {**audit.tamper(con), "verify": audit.verify(con)}


BENCH = {"proc": None}
BENCH_LOG = config.ROOT / "data" / "benchmark.log"


@app.get("/api/benchmark")
def get_benchmark():
    p = BENCH["proc"]
    running = p is not None and p.poll() is None
    failed = p is not None and not running and p.returncode != 0
    out = config.ROOT / "data" / "benchmark.json"
    result = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    return {"running": running, "result": result,
            "error": f"The scale test stopped with an error; details in {BENCH_LOG}" if failed else None}


@app.post("/api/benchmark/run")
def run_benchmark(incidents: int = 500, chains: int = 40, judge: str = "rules", vectors: str = "fast"):
    """Runs in a separate process against its own vault and database; the live memory is untouched.

    vectors=fast (default) uses the deterministic offline vectors, so the button finishes in seconds on
    any machine: the test measures linking, not embedding. vectors=model embeds all 500 incidents with
    the local model first (about a minute on the RTX 3050, much longer on CPU)."""
    p = BENCH["proc"]
    if p is not None and p.poll() is None:
        return {"running": True}
    env = {**os.environ, "RC_JUDGE": judge if judge in ("rules", "hybrid", "llm") else "rules"}
    if vectors != "model":
        env["RC_MODE"] = "fallback"
    log = open(BENCH_LOG, "w", encoding="utf-8")
    BENCH["proc"] = subprocess.Popen(
        [sys.executable, "-m", "rootcause.benchmark", "--incidents", str(incidents), "--chains", str(chains)],
        cwd=str(config.ROOT), env=env, stdout=log, stderr=subprocess.STDOUT)
    with LOCK:
        audit.record(con, "operator", "BENCHMARK_STARTED", {"incidents": incidents, "chains": chains, "judge": judge, "vectors": vectors})
    return {"running": True}


@app.get("/api/egress")
def get_egress():
    return egress.check()


@app.post("/api/reset")
def reset():
    """Restore the pre-demo state: remove demo drops and generated notes, rebuild."""
    for p in DEMO_DIR.glob("*.md"):
        for sub in ("incidents", "postmortems", "changes", "inbox"):
            (config.VAULT / sub / p.name).unlink(missing_ok=True)
    shutil.rmtree(config.VAULT / "clusters", ignore_errors=True)
    shutil.rmtree(config.VAULT / "inbox", ignore_errors=True)
    EVENTS.clear()
    return rebuild("reset")


def main():
    import uvicorn
    print(f"Starting Root Cause. Model server: {config.OLLAMA_URL} ({models.status()['mode']})", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
