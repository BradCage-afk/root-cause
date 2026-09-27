"""ACT: the policy gate. The model may propose; only policy decides.

Every tool has a permission level and a risk level. The pair maps to AUTO,
APPROVAL or BLOCK. Nothing a document says can change this table.
"""
import json
from pathlib import Path

from . import audit, config
from .db import rows

# tool -> (permission, risk)
TOOLS = {
    "read_document":        ("READ",    "LOW"),
    "write_cluster_note":   ("WRITE",   "MEDIUM"),
    "create_remediation_task": ("WRITE", "MEDIUM"),
    "delete_document":      ("DELETE",  "HIGH"),
    "send_external_email":  ("SEND",    "HIGH"),
}

MATRIX = {
    ("READ", "LOW"): "AUTO",
    ("WRITE", "LOW"): "AUTO",
    ("WRITE", "MEDIUM"): "APPROVAL",
    ("DELETE", "HIGH"): "BLOCK",
    ("SEND", "HIGH"): "BLOCK",
}


def decide(tool: str):
    if tool not in TOOLS:
        return "BLOCK", "unknown tool", ("?", "?")
    perm, risk = TOOLS[tool]
    d = MATRIX.get((perm, risk), "APPROVAL")
    why = {"AUTO": "low-risk read", "APPROVAL": "changes state; a human must approve",
           "BLOCK": f"{perm} at {risk} risk is never allowed"}[d]
    return d, why, (perm, risk)


def propose(con, tool: str, args: dict, proposed_by="agent") -> dict:
    decision, why, (perm, risk) = decide(tool)
    status = {"AUTO": "approved", "APPROVAL": "pending", "BLOCK": "blocked"}[decision]
    cur = con.execute("INSERT INTO actions(tool,args,permission,risk,decision,status,reason,proposed_by,created_at) "
                      "VALUES(?,?,?,?,?,?,?,?,?)",
                      (tool, json.dumps(args), perm, risk, decision, status, why, proposed_by, audit.now()))
    con.commit()
    aid = cur.lastrowid
    audit.record(con, proposed_by, f"ACTION_{status.upper()}", {"action": aid, "tool": tool, "args": args,
                                                                  "policy": decision})
    if decision == "AUTO":
        return execute(con, aid, approver="policy:auto")
    return get(con, aid)


def get(con, aid):
    a = rows(con, "SELECT * FROM actions WHERE id=?", (aid,))
    if not a:
        return None
    a = a[0]
    a["args"] = json.loads(a["args"])
    return a


def resolve(con, aid: int, approve: bool, approver="operator"):
    a = get(con, aid)
    if not a or a["status"] != "pending":
        return a
    if not approve:
        con.execute("UPDATE actions SET status='rejected', resolved_at=? WHERE id=?", (audit.now(), aid))
        con.commit()
        audit.record(con, approver, "ACTION_REJECTED", {"action": aid, "tool": a["tool"]})
        return get(con, aid)
    return execute(con, aid, approver)


def execute(con, aid: int, approver: str):
    from . import vault
    a = get(con, aid)
    tool, args = a["tool"], a["args"]
    if tool == "write_cluster_note":
        result = vault.write_cluster_note(con, args["cluster_id"])
    elif tool == "create_remediation_task":
        result = vault.write_task(args)
    elif tool == "read_document":
        r = rows(con, "SELECT id, title, kind FROM documents WHERE id=?", (args.get("id"),))
        result = r[0] if r else {"error": "not found"}
    else:
        result = {"error": "not executable"}
    con.execute("UPDATE actions SET status='executed', resolved_at=?, result=? WHERE id=?",
                (audit.now(), json.dumps(result), aid))
    con.commit()
    audit.record(con, approver, "ACTION_EXECUTED", {"action": aid, "tool": tool, "result": result})
    return get(con, aid)


def safe_path(rel: str) -> Path:
    """Writes are scoped to WRITABLE_DIRS inside the vault. No traversal, no exceptions."""
    p = (config.VAULT / rel).resolve()
    allowed = [(config.VAULT / d).resolve() for d in config.WRITABLE_DIRS]
    if not any(p.is_relative_to(a) for a in allowed):
        raise PermissionError(f"write outside {config.WRITABLE_DIRS} refused: {rel}")
    return p
