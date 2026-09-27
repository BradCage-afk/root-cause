"""Generates the seeded demo vault (Obsidian-style markdown + YAML frontmatter).

Three fictional teams (Payments, Search, Platform), January-June 2026.
Planted on purpose, and documented as planted:
  chain A  INC-102 -> INC-217 -> INC-288   shared cause via pgbouncer-main
           REM-31 (recorded as a "fix") and REM-37 both fail to stop it
  chain B  INC-156 -> INC-241              manual internal certificate renewal
  held     INC-133 + REM-52                a fix that actually worked
  near-miss INC-244                        shares pg-primary with chain A, different cause
  decision ADR-011 superseded by ADR-019
Everything else is filler with genuinely distinct causes.
Run:  python scripts/make_corpus.py
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "vault"


def fm(d):
    out = ["---"]
    for k, v in d.items():
        if isinstance(v, list):
            out.append(f"{k}: [{', '.join(v)}]")
        else:
            out.append(f"{k}: {v}")
    return "\n".join(out + ["---", ""])


def write(folder, name, meta, body):
    p = VAULT / folder / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(fm(meta) + body.strip() + "\n", encoding="utf-8")


def incident(iid, title, team, comp, deps, opened, restored, sev, symptom, summary, timeline, factors, action,
             follow=""):
    body = f"""# {iid} — {title}

{summary}

## Timeline
{timeline}

## Contributing factors
{factors}

## Action taken
{action}
"""
    if follow:
        body += f"\n## Follow-up\n{follow}\n"
    write("incidents", iid, {"id": iid, "type": "incident", "title": f'"{title}"', "team": team,
                             "component": comp, "depends_on": deps, "severity": sev,
                             "opened": opened, "restored": restored, "symptom": f'"{symptom}"'}, body)


def build():
    shutil.rmtree(VAULT, ignore_errors=True)
    PG = ["pgbouncer-main", "pg-primary"]

    # ------------------------------------------------------------------ chain A
    incident("INC-102", "Checkout timeouts during month-end promotion", "payments", "checkout-api", PG,
             "2026-01-14T09:14:00+05:30", "2026-01-14T11:02:00+05:30", "SEV-2",
             "checkout requests timing out",
             "Checkout requests timed out for roughly 1h50m. About 18% of checkout attempts failed.",
             "- 09:14 alert: checkout p99 latency above 8s\n- 09:31 on-call sees workers blocked waiting for a database connection\n"
             "- 10:20 promotion traffic throttled at the edge\n- 11:02 latency nominal, incident closed",
             "A month-end promotion tripled checkout traffic. checkout-api workers could not acquire database "
             "connections from pgbouncer-main: the connection pool was exhausted and requests queued until they "
             "timed out. Synchronous retries in the payment client multiplied the load on the pool.",
             "Throttled promotion traffic. Restarted checkout-api workers.",
             "Pool sizing raised in [[REM-31]]. See [[PM-102]].")
    write("postmortems", "PM-102", {"id": "PM-102", "type": "postmortem", "incident": "INC-102",
                                    "date": "2026-01-16", "team": "payments"}, """
# PM-102 — Postmortem for INC-102 (checkout timeouts)

## Summary
Checkout degraded for 1h50m during the month-end promotion.

## Root cause
The pgbouncer-main connection pool was exhausted. Checkout workers blocked waiting for a
connection, and synchronous retries in the payment client kept adding load.

## Resolution
Raise the pgbouncer-main pool size from 100 to 200 ([[REM-31]]). Recorded as a permanent fix.

## Open questions
Pool sizing for pgbouncer-main is shared by several services and has no owner. Raised as [[PLT-449]].
""")
    write("remediations", "REM-31", {"id": "REM-31", "type": "remediation", "incident": "INC-102",
                                     "kind": "fix", "applied": "2026-01-22T15:00:00+05:30",
                                     "summary": '"Raise pgbouncer-main pool size from 100 to 200"'}, """
# REM-31 — Raise pgbouncer-main pool size to 200

Changed `default_pool_size` from 100 to 200 on pgbouncer-main. Load-tested checkout at 2x
normal traffic. Postmortem [[PM-102]] records this as the permanent fix for [[INC-102]].
""")
    write("tickets", "PLT-449", {"id": "PLT-449", "type": "ticket", "team": "platform", "status": "open",
                                 "date": "2026-01-17"}, """
# PLT-449 — Nobody owns connection pool sizing across services

pgbouncer-main fronts pg-primary for checkout-api, search-indexer, gateway health checks and
reporting. Each team sizes its own client pools; nobody sizes the shared pool against the sum.

Status: open. Not scheduled.
""")
    incident("INC-217", "Search indexing lag after batch reindex", "search", "search-indexer", PG,
             "2026-03-03T09:14:00+05:30", "2026-03-03T11:42:00+05:30", "SEV-2",
             "indexing lag; stale search results",
             "Indexing fell about 40 minutes behind. Queries served stale results for roughly 2.5 hours.",
             "- 09:02 scheduled batch reindex starts\n- 09:14 alert: indexer lag above 15m\n"
             "- 09:31 on-call notes indexer workers cannot acquire database connections\n"
             "- 10:05 batch reindex paused; lag begins clearing\n- 11:42 lag nominal, incident closed",
             "A batch reindex started at 09:02 opened hundreds of database connections through pgbouncer-main. "
             "The connection pool was exhausted, so indexer workers could not acquire connections and indexing "
             "fell 40 minutes behind.",
             "Paused the batch reindex. Restarted indexer workers.",
             "Reindex schedule staggered in [[REM-37]]. [[PLT-449]] still unscheduled.")
    write("postmortems", "PM-217", {"id": "PM-217", "type": "postmortem", "incident": "INC-217",
                                    "date": "2026-03-05", "team": "search"}, """
# PM-217 — Postmortem for INC-217 (indexing lag)

## Root cause
The 09:02 batch reindex opened too many connections at once through pgbouncer-main and
exhausted the shared pool.

## Resolution
Stagger the batch reindex into four windows ([[REM-37]]).

## Notes
Payments saw pool exhaustion in January ([[INC-102]]). Their fix raised the pool size; we
consumed the extra headroom.
""")
    write("remediations", "REM-37", {"id": "REM-37", "type": "remediation", "incident": "INC-217",
                                     "kind": "workaround", "applied": "2026-03-06T12:00:00+05:30",
                                     "summary": '"Stagger the batch reindex into four windows"'}, """
# REM-37 — Stagger the batch reindex

Split the nightly batch reindex into four windows so fewer connections open at once.
""")
    incident("INC-288", "Gateway health checks flapping under load", "platform", "gateway-healthcheck", PG,
             "2026-06-21T22:40:00+05:30", "2026-06-21T23:55:00+05:30", "SEV-1",
             "health checks flapping; gateway ejecting healthy nodes",
             "The API gateway ejected healthy nodes for 75 minutes. Partial outage for all services behind it.",
             "- 22:40 alert: gateway healthy-node count below 50%\n- 22:52 probes time out on their database check\n"
             "- 23:20 database probe disabled on the gateway\n- 23:55 node count nominal, incident closed",
             "During a traffic spike, health-check probes that query the database could not acquire connections "
             "from pgbouncer-main because the connection pool was exhausted. Probes failed, the gateway ejected "
             "healthy nodes, and load shifted onto the remaining nodes.",
             "Disabled the database check in the gateway health probe.",
             "Third team affected by pgbouncer-main this year. [[PLT-449]] still open.")

    # ------------------------------------------------------------------ chain B
    incident("INC-156", "Search API TLS handshake failures", "search", "search-api", ["internal-ca"],
             "2026-02-09T06:30:00+05:30", "2026-02-09T09:10:00+05:30", "SEV-2",
             "TLS handshake errors from internal clients",
             "Internal clients could not reach search-api over TLS for 2h40m.",
             "- 06:30 alert: search-api 5xx from internal callers\n- 07:15 expired certificate identified\n"
             "- 09:10 certificate reissued from internal-ca, incident closed",
             "The internal TLS certificate for search-api expired. Certificate renewal is manual and tracked in a "
             "spreadsheet; the renewal reminder went to an engineer who had left the team.",
             "Manually reissued the certificate from internal-ca.",
             "Calendar reminder added in [[REM-44]].")
    write("remediations", "REM-44", {"id": "REM-44", "type": "remediation", "incident": "INC-156",
                                     "kind": "workaround", "applied": "2026-02-09T10:00:00+05:30",
                                     "summary": '"Renew certificate manually and add a calendar reminder"'}, """
# REM-44 — Manual renewal plus a calendar reminder

Reissued the search-api certificate and added a team calendar reminder 14 days before expiry.
""")
    write("tickets", "SRCH-88", {"id": "SRCH-88", "type": "ticket", "team": "search", "status": "open",
                                 "date": "2026-02-11"}, """
# SRCH-88 — Automate internal certificate renewal

Proposal: inventory every internal certificate issued by internal-ca and renew automatically.
Status: open. Not scheduled.
""")
    incident("INC-241", "Search admin console unreachable over HTTPS", "search", "search-admin", ["internal-ca"],
             "2026-05-11T07:05:00+05:30", "2026-05-11T08:40:00+05:30", "SEV-3",
             "admin console unreachable over HTTPS",
             "The search admin console was unreachable for 1h35m.",
             "- 07:05 support reports admin console certificate errors\n- 07:40 expired certificate identified\n"
             "- 08:40 certificate reissued, incident closed",
             "The internal TLS certificate for search-admin expired. Certificate renewal is still manual; the "
             "calendar reminder added after INC-156 covered only search-api.",
             "Manually reissued the certificate from internal-ca.")

    # ------------------------------------------------------------------ a fix that held
    incident("INC-133", "log-shipper OOM-killed every few hours", "platform", "log-shipper", ["node-agents"],
             "2026-01-28T14:00:00+05:30", "2026-01-28T18:30:00+05:30", "SEV-3",
             "log-shipper restarted repeatedly by the OOM killer",
             "Log delivery had gaps of up to 20 minutes across the fleet for four hours.",
             "- 14:00 alert: log-shipper restarts\n- 16:10 heap profile shows failed batches retained\n"
             "- 18:30 hotfix rolled out, incident closed",
             "A memory leak in the log-shipper batching code retained failed batches indefinitely, growing the heap "
             "until the process was killed.",
             "Rolled back to the previous log-shipper release.", "Permanent fix in [[REM-52]].")
    write("remediations", "REM-52", {"id": "REM-52", "type": "remediation", "incident": "INC-133",
                                     "kind": "fix", "applied": "2026-02-02T11:00:00+05:30",
                                     "summary": '"Patch batch retention leak and add memory ceiling test"'}, """
# REM-52 — Patch the batch retention leak

Failed batches are now dropped after three attempts. Added a soak test that fails CI if heap
grows past 400 MB.
""")

    # ------------------------------------------------------------------ the near-miss
    incident("INC-244", "Order writes blocked by schema migration", "payments", "orders-migration", ["pg-primary"],
             "2026-04-08T13:10:00+05:30", "2026-04-08T13:40:00+05:30", "SEV-2",
             "order writes blocked",
             "Order writes stalled for 30 minutes during a daytime schema migration.",
             "- 13:10 migration starts\n- 13:12 order write latency climbs\n- 13:40 migration completes",
             "A schema migration took an exclusive lock on the orders table for 18 minutes. Writes queued behind "
             "the lock. The migration had never been tested against production-sized tables.",
             "Waited for the migration to finish. Migrations now require a size-matched rehearsal.")

    # ------------------------------------------------------------------ decisions (bi-temporal)
    write("decisions", "ADR-011", {"id": "ADR-011", "type": "decision", "made": "2026-02-10",
                                   "superseded_by": "ADR-019", "team": "platform"}, """
# ADR-011 — Standardise on synchronous retries for database writes

## Decision
All services retry failed database writes synchronously, up to 5 times, with no backoff.

## Rationale
Simplest behaviour to reason about; no retry queue to operate.
""")
    write("decisions", "ADR-019", {"id": "ADR-019", "type": "decision", "made": "2026-05-20",
                                   "team": "platform"}, """
# ADR-019 — Retry budgets with jittered exponential backoff

## Decision
Replace synchronous retries (supersedes [[ADR-011]]) with per-service retry budgets and jittered
exponential backoff.

## Context
[[PM-102]] and [[PM-217]] show synchronous retries amplifying load while the pgbouncer-main pool
was exhausted. Retrying immediately against an exhausted pool deepens the outage.
""")

    # ------------------------------------------------------------------ runbooks
    write("runbooks", "RB-pgbouncer", {"id": "RB-pgbouncer", "type": "runbook", "team": "platform",
                                       "date": "2026-01-05"}, """
# Runbook — pgbouncer-main

pgbouncer-main is the shared connection pooler in front of pg-primary. Clients: checkout-api,
search-indexer, gateway-healthcheck, reporting.

## When clients cannot get connections
1. Check `SHOW POOLS;` for `cl_waiting` above 0.
2. Identify the client with the most active server connections.
3. Throttle that client before touching pool size.
""")
    write("runbooks", "RB-cert-renewal", {"id": "RB-cert-renewal", "type": "runbook", "team": "search",
                                          "date": "2026-01-10"}, """
# Runbook — Internal certificate renewal

Internal certificates are issued by internal-ca and renewed by hand. Expiry dates live in the
"certs" spreadsheet. Renew at least 14 days before expiry.
""")
    write("runbooks", "RB-deploy", {"id": "RB-deploy", "type": "runbook", "team": "platform",
                                    "date": "2026-01-08"}, """
# Runbook — Production deploys

Deploys go out behind feature flags. Roll to 10% first, watch error budgets for 30 minutes,
then 50%, then 100%. Config changes are reviewed like code.
""")

    # ------------------------------------------------------------------ filler: distinct causes
    F = [
        ("INC-108", "Log volume full on worker nodes", "platform", "log-volume", ["node-disks"],
         "2026-01-19T03:20:00+05:30", "2026-01-19T04:10:00+05:30", "SEV-3", "worker nodes out of disk",
         "logrotate was configured for weekly rotation after a config refactor, so application logs filled the "
         "log volume on eleven worker nodes.", "Rotated logs by hand and restored the daily logrotate schedule."),
        ("INC-121", "SMS OTP delivery failing", "payments", "sms-gateway", ["sms-vendor-api"],
         "2026-01-25T19:05:00+05:30", "2026-01-25T20:30:00+05:30", "SEV-2", "one-time passwords not delivered",
         "The SMS vendor rotated our API key during scheduled maintenance and the notice went to an unmonitored "
         "inbox, so every send was rejected as unauthorised.", "Installed the new vendor key; vendor notices now route to on-call."),
        ("INC-139", "Query cache stampede after deploy", "search", "query-cache", ["redis-cache"],
         "2026-02-03T12:00:00+05:30", "2026-02-03T12:35:00+05:30", "SEV-3", "search latency spike after deploy",
         "The deploy flushed every cached query key at once; thousands of identical cold queries hit the backend "
         "simultaneously because there was no request coalescing.", "Added request coalescing and staggered key expiry."),
        ("INC-147", "DNS query storm after resolver change", "platform", "dns-resolver", ["coredns"],
         "2026-02-06T10:15:00+05:30", "2026-02-06T11:00:00+05:30", "SEV-2", "intermittent name resolution failures",
         "A resolver config change set the cache TTL to zero, so every lookup went upstream and coredns ran out of "
         "CPU.", "Restored a 30-second TTL."),
        ("INC-163", "Fraud scorer rejecting valid payments", "payments", "fraud-scorer", ["feature-flags"],
         "2026-02-17T16:40:00+05:30", "2026-02-17T17:25:00+05:30", "SEV-1", "valid card payments rejected",
         "A new fraud model flag was rolled to 100% of traffic instead of 10%; the model had an inverted threshold.",
         "Rolled the flag back. Flag service now caps first rollout at 10%."),
        ("INC-172", "Kafka consumer rebalance storm", "platform", "kafka-consumers", ["kafka-cluster"],
         "2026-02-24T08:50:00+05:30", "2026-02-24T10:05:00+05:30", "SEV-2", "event processing stalled",
         "A consumer session timeout was lowered to 3 seconds; GC pauses exceeded it, triggering continuous group "
         "rebalances that stalled consumption.", "Raised the session timeout to 30 seconds."),
        ("INC-188", "Image resizer OOM on large uploads", "search", "image-resizer", ["worker-nodes"],
         "2026-03-12T15:30:00+05:30", "2026-03-12T16:05:00+05:30", "SEV-3", "thumbnails missing for new listings",
         "A seller uploaded 200-megapixel images; the resizer decoded them fully into memory and was OOM-killed.",
         "Added an input size limit and streaming decode."),
        ("INC-195", "CDN purge-all misfire", "platform", "cdn-edge", ["cdn-provider"],
         "2026-03-19T21:00:00+05:30", "2026-03-19T21:40:00+05:30", "SEV-2", "origin overloaded by cache misses",
         "A script meant to purge one path issued a purge-all because of an empty variable, sending all traffic "
         "to origin.", "Purge script now refuses empty paths."),
        ("INC-203", "Edge proxy silently kept stale config", "payments", "nginx-edge", ["edge-config"],
         "2026-03-26T11:10:00+05:30", "2026-03-26T12:00:00+05:30", "SEV-3", "new payment route returning 404",
         "A typo in the edge config made the reload fail, and the reload script reported success, so the proxy "
         "kept serving the old routes.", "Reload script now checks the config test exit code."),
        ("INC-226", "Autoscaler flapping", "platform", "autoscaler", ["k8s-control-plane"],
         "2026-04-02T14:20:00+05:30", "2026-04-02T15:10:00+05:30", "SEV-3", "pods scaling up and down every minute",
         "Scale-up and scale-down thresholds were set 2% apart with no stabilisation window, so the autoscaler "
         "oscillated.", "Added a five-minute stabilisation window."),
        ("INC-252", "Nightly report job ran twice", "search", "cron-reports", ["scheduler"],
         "2026-04-22T02:05:00+05:30", "2026-04-22T03:00:00+05:30", "SEV-3", "duplicate reports sent to partners",
         "Clock skew on one scheduler node made it claim a job that another node had already started, because "
         "the job lock used local timestamps.", "Job locks now use the database clock."),
        ("INC-263", "Refund exports failing", "payments", "refund-service", ["s3-exports"],
         "2026-05-04T09:40:00+05:30", "2026-05-04T11:15:00+05:30", "SEV-2", "refund files not delivered to the bank",
         "A bucket policy tightened by the security team removed write access for the export role.",
         "Restored the export role's write permission with a scoped policy."),
        ("INC-276", "Stale endpoints after mesh upgrade", "platform", "service-mesh", ["mesh-control"],
         "2026-05-28T17:00:00+05:30", "2026-05-28T18:20:00+05:30", "SEV-2", "requests routed to terminated pods",
         "The mesh control plane upgrade changed endpoint sync defaults; sidecars kept endpoints for terminated "
         "pods for up to ten minutes.", "Pinned the endpoint sync interval to 5 seconds."),
        ("INC-281", "Suggestions API serving garbage", "search", "suggest-api", ["ml-model-store"],
         "2026-06-06T13:30:00+05:30", "2026-06-06T14:10:00+05:30", "SEV-3", "nonsense autocomplete suggestions",
         "The suggestion model file was truncated during upload and loaded without a checksum check.",
         "Model loads now verify checksums."),
    ]
    for (iid, title, team, comp, deps, o, r, sev, sym, factors, action) in F:
        incident(iid, title, team, comp, deps, o, r, sev, sym, f"{sym.capitalize()}.",
                 f"- {o[11:16]} alert fired\n- {r[11:16]} restored, incident closed", factors, action)

    for tid, team, date, title, body in [
        ("PAY-310", "payments", "2026-02-18", "Cap first rollout of risk-model flags",
         "Enforce a 10% ceiling on the first rollout step for any flag touching payment decisions."),
        ("PLT-512", "platform", "2026-04-03", "Autoscaler defaults review",
         "Audit stabilisation windows on every autoscaler after INC-226."),
        ("SRCH-102", "search", "2026-06-07", "Checksum every model artifact",
         "Model store should reject artifacts without a matching checksum."),
    ]:
        write("tickets", tid, {"id": tid, "type": "ticket", "team": team, "status": "open", "date": date},
              f"# {tid} — {title}\n\n{body}\n")

    (VAULT / ".obsidian").mkdir(exist_ok=True)
    (VAULT / ".obsidian" / "app.json").write_text('{"showFrontmatter": true}\n', encoding="utf-8")
    n = len(list(VAULT.rglob("*.md")))
    print(f"wrote {n} documents to {VAULT}")


if __name__ == "__main__":
    build()
