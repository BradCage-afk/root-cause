"""Obsidian write-back. Analysis lands in the team's own vault as plain markdown,
readable without Root Cause installed. Only reached through the policy gate."""
from . import audit
from .debt import failure_debt, fix_effectiveness
from .cluster import recurrence_clusters
from .policy import safe_path


def write_cluster_note(con, cid: str) -> dict:
    c = next((x for x in recurrence_clusters(con) if x["id"] == cid), None)
    if not c:
        return {"error": f"{cid} is not a recurrence cluster"}
    debt = next((d for d in failure_debt(con) if d["cluster"] == cid), {})
    rems = [f for f in fix_effectiveness(con) if f["cluster_id"] == cid]
    lines = [
        "---", f"id: {cid}", "type: cluster", f"hypothesis: \"{c['hypothesis']}\"",
        f"debt_score: {debt.get('score', '')}", f"members: {c['member_count']}",
        f"teams: [{', '.join(c['teams'])}]", "generated_by: root-cause",
        f"generated_at: {audit.now()}", "---", "",
        f"# {cid} — {c['hypothesis']}", "",
        "> Evidence-backed causal hypothesis, not a proven root cause.", "",
        "## Members",
    ]
    for m in c["members"]:
        r = m["reason"]
        extra = "" if r.get("seed") else f" — similarity {m['similarity']}, confidence {m['confidence']}"
        lines.append(f"- [[{m['incident_id']}]] — {m['team']}, {m['opened_at'][:10]}{extra}")
    lines += ["", "## Shared dependencies"] + [f"- `{d}`" for d in c["shared_dependencies"]]
    lines += ["", "## Remediation history"]
    for f in rems:
        after = ", ".join(f"[[{x['id']}]]" for x in f["recurrences_after"])
        verdict = f"**ineffective** — recurred: {after}" if f["recurrences_after"] else "held"
        lines.append(f"- [[{f['id']}]] — {f['applied_at'][:10]} — {f['description']} — {verdict}")
    if debt:
        i = debt["inputs"]
        lines += ["", "## Failure debt",
                  f"recurrence {i['recurrence']} × persistence {i['persistence']} × impact {i['impact']} "
                  f"× spread {i['spread']} → **{debt['score']}**"]
    path = safe_path(f"clusters/{cid}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"written": f"clusters/{cid}.md", "bytes": path.stat().st_size}


def write_task(args: dict) -> dict:
    tid = args.get("id") or f"TASK-{abs(hash(args.get('title', ''))) % 10000:04d}"
    path = safe_path(f"clusters/tasks/{tid}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nid: {tid}\ntype: task\ncluster: {args.get('cluster_id', '')}\n---\n\n"
                    f"# {args.get('title', 'Remediation task')}\n\n{args.get('body', '')}\n", encoding="utf-8")
    return {"written": f"clusters/tasks/{tid}.md"}
