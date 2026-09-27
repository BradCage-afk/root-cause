"""Deterministic analysis. No model decides any number on this page.

  failure debt   = recurrence x persistence x impact x cross-team spread
  fix effect     = incidents in the same cluster opened after the fix was applied
  prediction     = every remediation predicts its cluster closes; the timeline grades it
"""
import json
from datetime import datetime

from .cluster import recurrence_clusters
from .db import rows

SEV = {"SEV-1": 3.0, "SEV-2": 2.0, "SEV-3": 1.0}


def _t(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _hours(a, b):
    ta, tb = _t(a), _t(b)
    return max(0.0, (tb - ta).total_seconds() / 3600) if ta and tb else 0.0


def cluster_of(con):
    return {r["incident_id"]: r["cluster_id"] for r in rows(con, "SELECT * FROM cluster_members")}


def fix_effectiveness(con):
    """For each remediation: which incidents of the same cluster happened after it."""
    membership = cluster_of(con)
    incidents = {r["id"]: r for r in rows(con, "SELECT * FROM incidents")}
    out = []
    for rem in rows(con, "SELECT * FROM remediations ORDER BY applied_at"):
        cid = membership.get(rem["incident_id"])
        applied = _t(rem["applied_at"])
        after = []
        if cid and applied:
            for iid, c in membership.items():
                inc = incidents.get(iid)
                if c == cid and inc and _t(inc["opened_at"]) and _t(inc["opened_at"]) > applied:
                    after.append({"id": iid, "opened_at": inc["opened_at"], "team": inc["team"]})
        after.sort(key=lambda x: x["opened_at"])
        out.append({**rem, "cluster_id": cid, "recurrences_after": after,
                    "status": "ineffective" if after else "held"})
    return out


def predictions(con):
    """Every remediation is a falsifiable prediction that its cluster stops recurring."""
    fx = fix_effectiveness(con)
    latest = con.execute("SELECT MAX(opened_at) FROM incidents").fetchone()[0]
    con.execute("DELETE FROM predictions")
    preds = []
    for f in fx:
        outcome = "broken" if f["recurrences_after"] else "kept"
        evidence = [r["id"] for r in f["recurrences_after"]]
        con.execute("INSERT INTO predictions(remediation_id,cluster_id,predicted_at,verified_at,outcome,evidence) "
                    "VALUES(?,?,?,?,?,?)", (f["id"], f["cluster_id"], f["applied_at"], latest, outcome,
                                            json.dumps(evidence)))
        preds.append({"remediation": f["id"], "kind": f["kind"], "cluster": f["cluster_id"],
                      "predicted": f"{f['cluster_id'] or 'its incident'} stops recurring",
                      "predicted_at": f["applied_at"], "verified_at": latest,
                      "outcome": outcome, "evidence": evidence})
    con.commit()
    kept = sum(p["outcome"] == "kept" for p in preds)
    return {"predictions": preds, "kept": kept, "total": len(preds),
            "calibration": round(kept / len(preds), 2) if preds else None}


def failure_debt(con):
    fx = fix_effectiveness(con)
    out = []
    for c in recurrence_clusters(con):
        m = c["members"]
        times = [_t(x["opened_at"]) for x in m if _t(x["opened_at"])]
        span_days = (max(times) - min(times)).days if times else 0
        recurrence = len(m)
        persistence = round(1 + span_days / 30, 2)
        mean_sev = sum(SEV.get(x["severity"], 1.0) for x in m) / recurrence
        mean_ttr = sum(_hours(x["opened_at"], x["restored_at"]) for x in m) / recurrence
        impact = round(mean_sev * (1 + mean_ttr / 4), 2)
        spread = len(c["teams"])
        rems = [f for f in fx if f["cluster_id"] == c["id"]]
        last = max(times) if times else None
        paid = any(f["status"] == "held" and _t(f["applied_at"]) and last and _t(f["applied_at"]) > last
                   for f in rems)
        raw = recurrence * persistence * impact * spread * (0.25 if paid else 1.0)
        score = round(100 * raw / (raw + 50))
        out.append({"cluster": c["id"], "hypothesis": c["hypothesis"], "score": score,
                    "inputs": {"recurrence": recurrence, "persistence": persistence,
                               "impact": impact, "spread": spread, "paid_off": paid,
                               "span_days": span_days, "mean_ttr_hours": round(mean_ttr, 1)},
                    "teams": c["teams"], "members": [x["incident_id"] for x in m],
                    "remediations": [{"id": f["id"], "kind": f["kind"], "status": f["status"]}
                                     for f in rems]})
    return sorted(out, key=lambda d: -d["score"])


def decisions(con):
    """Bi-temporal view: when a decision was true, and when we learned it stopped being."""
    ds = rows(con, "SELECT * FROM decisions ORDER BY made_at")
    made = {d["id"]: d["made_at"] for d in ds}
    for d in ds:
        d["valid_from"] = d["made_at"]
        d["valid_until"] = made.get(d["superseded_by"]) if d["superseded_by"] else None
        d["status"] = "superseded" if d["superseded_by"] else "active"
    return ds
