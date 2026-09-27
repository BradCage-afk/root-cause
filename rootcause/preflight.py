"""Memory that arrives before the change.

A change plan is matched against the causal graph: which components and
dependencies it touches, which recurrence clusters own them, what happened last
time, and whether the previous fix held. Same retrieval path as a question,
pointed at a diff instead."""
import json
import re

from . import models
from .cluster import recurrence_clusters
from .db import from_blob, rows
from .debt import failure_debt, fix_effectiveness


def known_nodes(con):
    nodes = set()
    for r in rows(con, "SELECT component, depends_on FROM incidents"):
        nodes |= {r["component"], *json.loads(r["depends_on"] or "[]")}
    return sorted(nodes - {""})


def check(con, change_text: str) -> dict:
    low = change_text.lower()
    touched = [n for n in known_nodes(con) if re.search(r"(?<![\w-])" + re.escape(n.lower()) + r"(?![\w-])", low)]
    # a component implies its dependencies
    implied = set(touched)
    for r in rows(con, "SELECT component, depends_on FROM incidents"):
        if r["component"] in touched:
            implied |= set(json.loads(r["depends_on"] or "[]"))
    cv = models.embed([change_text])[0]
    debt = {d["cluster"]: d for d in failure_debt(con)}
    fixes = fix_effectiveness(con)
    centroids = {c["id"]: from_blob(c["centroid"]) for c in rows(con, "SELECT id, centroid FROM clusters")}

    hits = []
    for c in recurrence_clusters(con):
        nodes = {m["component"] for m in c["members"]} | set(c["shared_dependencies"])
        overlap = sorted(nodes & implied)
        sim = models.cosine(cv, centroids.get(c["id"]))
        if not overlap and sim < 0.35:
            continue
        failed = [f for f in fixes if f["cluster_id"] == c["id"] and f["status"] == "ineffective"]
        hits.append({
            "cluster": c["id"], "hypothesis": c["hypothesis"], "overlap": overlap,
            "similarity": round(sim, 3), "debt": debt.get(c["id"], {}).get("score"),
            "incidents": [{"id": m["incident_id"], "team": m["team"], "opened_at": m["opened_at"][:10],
                           "title": m["title"]} for m in c["members"]],
            "failed_fixes": [{"id": f["id"], "description": f["description"],
                              "recurred": [x["id"] for x in f["recurrences_after"]]} for f in failed],
        })
    hits.sort(key=lambda h: (-(len(h["overlap"]) > 0), -(h["debt"] or 0)))
    level = "warn" if hits else "clear"
    return {"level": level, "touched": sorted(implied), "hits": hits,
            "message": _message(change_text, hits)}


def _message(change_text, hits):
    if not hits:
        return "No recurrence cluster owns anything this change touches."
    h = hits[0]
    facts = (f"cluster {h['cluster']} ({h['hypothesis']}); incidents "
             + ", ".join(f"{i['id']} ({i['team']}, {i['opened_at']})" for i in h["incidents"])
             + (f"; previous fix {h['failed_fixes'][0]['id']} did not hold" if h["failed_fixes"] else ""))
    text = models.chat(
        "Write a two-sentence pre-flight warning for an engineer about to ship a change. "
        "Use only the facts given. Name incident ids. No speculation.",
        f"Change: {change_text}\nFacts: {facts}")
    return text or (f"This change touches {', '.join(h['overlap']) or 'a component'} owned by {h['cluster']} "
                    f"— {len(h['incidents'])} past incidents share the hypothesis \"{h['hypothesis']}\""
                    + (f", and {h['failed_fixes'][0]['id']} did not stop it recurring." if h["failed_fixes"] else "."))
