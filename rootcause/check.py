"""Pre-recording sanity check. Rebuilds from the vault and prints what the demo depends on.

    .venv\\Scripts\\python -m rootcause.check
"""
from . import app, cluster, debt, models


def main():
    s = models.status()
    print(f"mode: {s['mode']}  chat: {s['chat_model']} ready={s['chat_ready']}  "
          f"embed: {s['embed_model']} ready={s['embed_ready']}")
    app.rebuild("check")
    cs = cluster.recurrence_clusters(app.con)
    for c in cs:
        print(f"  {c['id']}  {[m['incident_id'] for m in c['members']]}  teams={c['teams']}  hypothesis={c['hypothesis']!r}")
    fx = {f["id"]: f["status"] for f in debt.fix_effectiveness(app.con)}
    linked = {m["incident_id"] for c in cs for m in c["members"]}
    checks = [
        ("chain A clustered (INC-102, INC-217, INC-288)", any({"INC-102", "INC-217", "INC-288"} <= {m["incident_id"] for m in c["members"]} for c in cs)),
        ("chain B clustered (INC-156, INC-241)", any({"INC-156", "INC-241"} <= {m["incident_id"] for m in c["members"]} for c in cs)),
        ("near-miss INC-244 NOT clustered", "INC-244" not in linked),
        ("exactly 2 recurrence clusters", len(cs) == 2),
        ("REM-31 ineffective", fx.get("REM-31") == "ineffective"),
        ("REM-52 held", fx.get("REM-52") == "held"),
    ]
    for name, ok in checks:
        print(("  PASS  " if ok else "  FAIL  ") + name)
    if all(ok for _, ok in checks):
        print("\nReady to record.")
    else:
        print("\nSomething differs with the local model. Restart with:  set RC_JUDGE=rules  then run.bat")


if __name__ == "__main__":
    main()
