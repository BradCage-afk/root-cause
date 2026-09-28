"""Scale proof: a synthetic incident corpus with known ground truth, and a benchmark
that measures recurrence linking against it.

    python -m rootcause.benchmark --incidents 500 --chains 40

Every generated incident belongs to an *archetype* = (cause family, shared dependency).
Archetypes with 2-5 incidents are true recurrence chains, written with different wording,
on different components, by different teams, months apart. The rest are singletons, many of
which share a dependency with a chain but have a different cause (near-misses).

The benchmark replays the corpus chronologically through the same link_incident() the app
uses, then reports precision/recall against ground truth, link time per incident, and
centroid comparisons against the naive all-pairs count. Results: data/benchmark.json
"""
import argparse
import json
import random
import shutil
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from . import cluster, config, ingest, models
from .db import connect, rows

SCALE_VAULT = config.ROOT / "vault-scale"
OUT = config.ROOT / "data" / "benchmark.json"

DEPS = """kafka-main kafka-events redis-sessions redis-cache-eu pg-orders pg-ledger pg-users mysql-catalog
es-search s3-archive s3-exports dns-internal vault-secrets ldap-auth smtp-relay sms-vendor payment-gateway
cdn-edge-2 k8s-control istio-mesh consul-kv zookeeper-3 rabbitmq-main nats-bus clickhouse-metrics
prometheus-main loki-logs ntp-pool nfs-shared minio-backups keycloak-sso flags-svc cron-scheduler
gpu-pool memcached-a etcd-main mongo-profiles cassandra-events grafana-alerts jenkins-ci""".split()
TEAMS = "payments search platform notifications identity data mobile growth checkout logistics risk support".split()
PRE = """billing ledger cart order invoice refund profile auth session feed catalog pricing inventory shipping
tracking suggest ranking image video email push report export import fraud kyc loyalty coupon wallet payout
settlement analytics metrics gateway notifier""".split()
SUF = "api worker service consumer writer reader sync cron proxy indexer".split()

# cause family -> (symptom, [contributing-factor paraphrases]); {c}=component, {d}=dependency
FAMILIES = {
    "pool": ("requests timing out waiting for connections", [
        "{c} could not acquire connections from {d}; the connection pool was exhausted under a burst.",
        "The {d} connection pool hit its limit and {c} requests queued until they timed out.",
        "{c} workers blocked waiting for a {d} connection because every pool slot was held.",
        "Connection pool saturation on {d}: all connections in use, new {c} requests timed out."]),
    "cert": ("TLS handshake failures", [
        "The TLS certificate {c} uses for {d} expired; certificate renewal is manual.",
        "{c} failed TLS handshakes to {d} after its certificate expired unnoticed.",
        "An expired certificate on the {d} endpoint broke {c}; nobody owned certificate renewal."]),
    "disk": ("writes failing with no space left", [
        "The {d} volume filled up after log rotation stopped, so {c} could not write.",
        "Disk space on {d} ran out; {c} writes failed with no space left on device.",
        "{c} filled the {d} disk with unrotated logs until writes failed."]),
    "leak": ("process restarted by the OOM killer", [
        "A memory leak in {c} retained {d} response buffers until the OOM killer restarted it.",
        "{c} heap grew without bound holding {d} results; out-of-memory kills every few hours.",
        "Leaked {d} client objects in {c} exhausted memory and triggered OOM restarts."]),
    "typo": ("stale configuration served after reload", [
        "A typo in the {c} config for {d} made the reload fail silently; the old config kept serving.",
        "The {d} settings for {c} had a syntax error; the reload script ignored the failed config test.",
        "{c} reported a successful reload although its {d} config failed validation."]),
    "dns": ("intermittent name resolution failures", [
        "The DNS TTL for {d} was set to zero, overloading resolvers and breaking {c} lookups.",
        "{c} could not resolve {d} after a resolver change disabled DNS caching.",
        "Zero-TTL DNS records for {d} sent every {c} lookup upstream until resolvers failed."]),
    "stampede": ("latency spike after cache flush", [
        "A deploy flushed the {d} cache and cold {c} requests stampeded the backend.",
        "{c} had no request coalescing, so an emptied {d} cache caused a thundering herd.",
        "Every {d} cache key expired at once; {c} sent thousands of identical cold queries."]),
    "ratelimit": ("requests rejected with 429", [
        "The vendor lowered the {d} rate limit and {c} requests were rejected with 429.",
        "{c} exceeded the {d} rate limit after a traffic increase; calls throttled with 429.",
        "{d} started throttling {c} at a new, lower rate limit announced to an unread inbox."]),
    "rebalance": ("event processing stalled", [
        "{c} consumers on {d} rebalanced continuously after the session timeout was lowered.",
        "A too-short session timeout made the {d} consumer group behind {c} rebalance in a loop.",
        "Consumer group rebalance storms on {d} stalled {c}; heartbeats missed the timeout."]),
    "skew": ("signed requests rejected as expired", [
        "Clock skew on {c} hosts made {d} reject signed requests as expired.",
        "{c} host clocks drifted from NTP and {d} refused its request signatures.",
        "Drifting clocks on {c} servers caused {d} signature timestamp validation to fail."]),
    "flag": ("behaviour change reached all users", [
        "A feature flag in {d} rolled the {c} change to 100% of traffic instead of 10%.",
        "{c} changes shipped to every user because the {d} flag rollout skipped staged percentages.",
        "The {d} flag for {c} was enabled globally at once instead of a gradual rollout."]),
    "lock": ("writes blocked", [
        "A schema migration on {d} held an exclusive table lock and {c} writes queued.",
        "{c} writes stalled behind a long-running {d} migration holding a table lock.",
        "An untested {d} migration locked a large table for minutes, blocking {c}."]),
    "starve": ("service unresponsive under load", [
        "{c} thread pool starved because slow {d} calls had no timeout.",
        "Every {c} worker thread blocked on {d} calls without deadlines; the pool starved.",
        "Missing timeouts on {d} calls tied up all {c} threads until it stopped responding."]),
    "retry": ("degradation amplified into an outage", [
        "Synchronous retries from {c} amplified load on a degraded {d} into a retry storm.",
        "{c} retried failed {d} calls immediately with no backoff, deepening the outage.",
        "A retry storm from {c} kept {d} overloaded; retries had no budget or jitter."]),
    "gc": ("heartbeats missed and sessions expired", [
        "Long garbage-collection pauses in {c} stalled {d} heartbeats and sessions expired.",
        "{c} stop-the-world GC pauses exceeded the {d} session timeout.",
        "GC pauses in {c} made {d} consider it dead and drop its session."]),
    "key": ("calls returning unauthorised", [
        "The {d} API key was rotated without notice and {c} calls returned unauthorised.",
        "{c} kept using a revoked {d} credential after a vendor key rotation.",
        "A {d} credential rotation was not propagated to {c}; every call failed authentication."]),
    "quota": ("writes rejected over quota", [
        "{c} exhausted its {d} storage quota and writes were rejected.",
        "The {d} quota for {c} was reached; new objects were refused.",
        "{c} hit the {d} usage quota nobody was monitoring."]),
    "noisy": ("CPU starvation on shared nodes", [
        "A batch job on shared {d} nodes starved {c} of CPU.",
        "{c} shared {d} hosts with an unthrottled batch workload that consumed the CPU.",
        "Noisy-neighbour batch work on {d} took the CPU {c} needed."]),
    "partition": ("stale reads after network split", [
        "A network partition between {c} and {d} split the cluster and served stale reads.",
        "{c} lost connectivity to part of {d}; the split cluster diverged.",
        "Split-brain after a network partition in {d} gave {c} inconsistent data."]),
    "upgrade": ("unexpected behaviour after library upgrade", [
        "An unpinned {d} client library upgrade changed defaults in {c}.",
        "{c} picked up a new {d} client version whose default timeouts changed.",
        "A floating {d} dependency version in {c} upgraded silently and changed behaviour."]),
    "timeout": ("requests piling up", [
        "The {c} timeout to {d} was longer than the upstream deadline, so requests piled up.",
        "{c} waited 30 seconds for {d} while callers had already given up; work accumulated.",
        "Misaligned timeouts between {c} and {d} left abandoned requests consuming capacity."]),
    "cron": ("scheduled job ran twice", [
        "Two {d} scheduler nodes both ran the {c} job after a failover.",
        "{c} ran twice because the {d} job lock expired during a slow run.",
        "A {d} failover lost the job lease and a second {c} run started."]),
}
ACTIONS = ["Restarted the affected pods.", "Rolled back the last deploy.", "Failed over to the standby.",
           "Throttled traffic at the edge.", "Applied a manual hotfix.", "Scaled the service up temporarily."]


def generate(n=500, chains=40, seed=7, root: Path = SCALE_VAULT):
    rng = random.Random(seed)
    shutil.rmtree(root, ignore_errors=True)
    (root / "incidents").mkdir(parents=True)
    comps = {}
    for p in PRE:
        for s in rng.sample(SUF, 3):
            name = f"{p}-{s}"
            comps[name] = {"team": rng.choice(TEAMS), "deps": rng.sample(DEPS, rng.choice((1, 2)))}
    by_dep = defaultdict(list)
    for c, v in comps.items():
        for d in v["deps"]:
            by_dep[d].append(c)
    pairs = [(f, d) for f in FAMILIES for d in DEPS if len(by_dep[d]) >= 2]
    rng.shuffle(pairs)
    chain_sizes = [rng.randint(2, 5) for _ in range(chains)]
    singles = max(0, n - sum(chain_sizes))
    archetypes = [(pairs[i], k) for i, k in enumerate(chain_sizes)]
    archetypes += [(pairs[chains + i], 1) for i in range(singles)]
    start = datetime(2025, 1, 1, 9, 0)
    truth, idn = {}, 1000
    for ai, ((fam, dep), k) in enumerate(archetypes):
        symptom, templates = FAMILIES[fam]
        comps_here = rng.sample(by_dep[dep], min(k, len(by_dep[dep])))
        days = sorted(rng.sample(range(0, 540), k))
        tpl = rng.sample(templates, min(k, len(templates)))
        for j in range(k):
            idn += 1
            iid = f"INC-{idn}"
            comp = comps_here[j % len(comps_here)]
            opened = start + timedelta(days=days[j], minutes=rng.randint(0, 600))
            restored = opened + timedelta(minutes=rng.randint(20, 240))
            factors = tpl[j % len(tpl)].format(c=comp, d=dep)
            sev = rng.choice(("SEV-1", "SEV-2", "SEV-2", "SEV-3", "SEV-3"))
            arch = f"ARCH-{ai:03d}"
            truth[iid] = arch
            (root / "incidents" / f"{iid}.md").write_text(
                f"---\nid: {iid}\ntype: incident\ntitle: \"{comp} {symptom}\"\nteam: {comps[comp]['team']}\n"
                f"component: {comp}\ndepends_on: [{', '.join(comps[comp]['deps'])}]\nseverity: {sev}\n"
                f"opened: {opened.isoformat()}+05:30\nrestored: {restored.isoformat()}+05:30\n"
                f"symptom: \"{symptom}\"\ntruth: {arch}\n---\n"
                f"# {iid} — {comp}: {symptom}\n\n{symptom.capitalize()} on {comp}.\n\n"
                f"## Contributing factors\n{factors}\n\n## Action taken\n{rng.choice(ACTIONS)}\n",
                encoding="utf-8")
    return truth


def _pairs(groups):
    return {tuple(sorted((a, b))) for g in groups for i, a in enumerate(g) for b in g[i + 1:]}


def run(n=500, chains=40, seed=7, root: Path = SCALE_VAULT, db: Path = None, out: Path = OUT):
    t_all = time.perf_counter()
    truth = generate(n, chains, seed, root)
    db = db or config.ROOT / "data" / "bench.db"
    for suffix in ("", "-wal", "-shm"):
        Path(str(db) + suffix).unlink(missing_ok=True)
    con = connect(db)

    t0 = time.perf_counter()
    files = sorted((root / "incidents").glob("*.md"))
    for p in files:
        ingest.ingest_file(con, p, actor="benchmark")
    t_ingest = time.perf_counter() - t0

    order = [r["id"] for r in rows(con, "SELECT id FROM incidents ORDER BY opened_at, id")]
    held_out = order[-1]  # the last incident is linked separately, as "a new one arriving"
    link_ms, blocked, ranked, judged = [], 0, 0, 0
    for iid in order[:-1]:
        t = time.perf_counter()
        tr = cluster.link_incident(con, iid)
        link_ms.append((time.perf_counter() - t) * 1000)
        blocked += len(tr["blocked"]); ranked += len(tr["ranked"]); judged += len(tr["adjudicated"])
    t = time.perf_counter()
    tr = cluster.link_incident(con, held_out)
    new_ms = (time.perf_counter() - t) * 1000
    blocked += len(tr["blocked"]); judged += len(tr["adjudicated"])

    pred = defaultdict(list)
    for r in rows(con, "SELECT cluster_id, incident_id FROM cluster_members"):
        pred[r["cluster_id"]].append(r["incident_id"])
    true_groups = defaultdict(list)
    for iid, a in truth.items():
        true_groups[a].append(iid)
    pred_pairs = _pairs(pred.values())
    true_pairs = _pairs(true_groups.values())
    tp = len(pred_pairs & true_pairs)
    precision = tp / len(pred_pairs) if pred_pairs else 1.0
    recall = tp / len(true_pairs) if true_pairs else 1.0
    found = [sorted(g) for g in pred.values() if len(g) >= 2]
    real = [sorted(g) for g in true_groups.values() if len(g) >= 2]
    exact = sum(1 for g in found if g in real)
    false_links = 0
    for g in found:
        majority = Counter(truth[i] for i in g).most_common(1)[0][1]
        false_links += len(g) - majority

    link_ms.sort()
    res = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "incidents": len(order), "true_chains": len(real),
        "chain_incidents": sum(len(g) for g in real), "singletons": len(order) - sum(len(g) for g in real),
        "clusters_found": len(found), "chains_recovered_exactly": exact,
        "pair_precision": round(precision, 3), "pair_recall": round(recall, 3), "false_links": false_links,
        "link_ms_median": round(statistics.median(link_ms), 1),
        "link_ms_p95": round(link_ms[int(0.95 * (len(link_ms) - 1))], 1),
        "new_incident_ms": round(new_ms, 1),
        "centroid_comparisons": ranked, "blocked_candidates": blocked, "adjudications": judged,
        "naive_pair_comparisons": len(order) * (len(order) - 1) // 2,
        "ingest_seconds": round(t_ingest, 1), "total_seconds": round(time.perf_counter() - t_all, 1),
        "embed_space": models.embed_space(), "judge": config.JUDGE,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2), encoding="utf-8")
    con.close()
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--incidents", type=int, default=500)
    ap.add_argument("--chains", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--judge", choices=("rules", "hybrid", "llm"), default=None,
                    help="adjudication judge; defaults to RC_JUDGE. 'hybrid'/'llm' need Ollama and take longer")
    a = ap.parse_args()
    if a.judge:
        config.JUDGE = a.judge
    r = run(a.incidents, a.chains, a.seed)
    w = max(len(k) for k in r)
    for k, v in r.items():
        print(f"{k:<{w}}  {v}")


if __name__ == "__main__":
    main()
