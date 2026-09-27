"""Hash-chained, append-only audit log. Each entry seals the one before it."""
import hashlib
from datetime import datetime, timezone

from .db import dumps, rows

GENESIS = "0" * 64


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _digest(prev, ts, actor, action, payload) -> str:
    return hashlib.sha256(f"{prev}|{ts}|{actor}|{action}|{payload}".encode()).hexdigest()


def record(con, actor: str, action: str, payload: dict) -> dict:
    last = con.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    prev = last["hash"] if last else GENESIS
    ts, body = now(), dumps(payload)
    h = _digest(prev, ts, actor, action, body)
    con.execute("INSERT INTO audit_log(ts,actor,action,payload,prev_hash,hash) VALUES(?,?,?,?,?,?)",
                (ts, actor, action, body, prev, h))
    con.commit()
    return {"ts": ts, "action": action, "hash": h}


def verify(con) -> dict:
    prev = GENESIS
    entries = rows(con, "SELECT * FROM audit_log ORDER BY id")
    for e in entries:
        expect = _digest(prev, e["ts"], e["actor"], e["action"], e["payload"])
        if e["prev_hash"] != prev or e["hash"] != expect:
            return {"ok": False, "entries": len(entries), "broken_at": e["id"],
                    "message": f"Chain broken at entry #{e['id']} ({e['action']})"}
        prev = e["hash"]
    return {"ok": True, "entries": len(entries), "head": prev,
            "message": f"{len(entries)} entries, chain intact"}


def tamper(con) -> dict:
    """Demo only: edit a past entry in place without re-sealing it."""
    e = con.execute("SELECT id, payload FROM audit_log ORDER BY id LIMIT 1 OFFSET 2").fetchone()
    if not e:
        return {"ok": False, "message": "not enough entries to tamper with"}
    con.execute("UPDATE audit_log SET payload=? WHERE id=?",
                (e["payload"].replace("}", ', "edited": true}', 1), e["id"]))
    con.commit()
    return {"ok": True, "tampered_id": e["id"]}
