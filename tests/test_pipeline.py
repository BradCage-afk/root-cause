"""End-to-end checks for every demo beat, in fallback mode (no model needed).

Run:  RC_MODE=fallback python -m pytest -q
"""
import os
import shutil
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_tmp = Path(tempfile.mkdtemp())
shutil.copytree(ROOT / "vault", _tmp / "vault")
os.environ.update(RC_MODE="fallback", RC_DB=str(_tmp / "t.db"), RC_VAULT=str(_tmp / "vault"))

from fastapi.testclient import TestClient  # noqa: E402
from rootcause import app as A  # noqa: E402


@pytest.fixture(scope="module")
def c():
    with TestClient(A.app) as client:
        yield client


def members(c, cid):
    return {m["incident_id"] for x in c.get("/api/clusters").json() if x["id"] == cid for m in x["members"]}


def test_zero_egress(c):
    assert c.get("/api/egress").json()["external_connections"] == 0


def test_chain_a_clusters_across_three_teams(c):
    cs = c.get("/api/clusters").json()
    a = next(x for x in cs if "INC-102" in {m["incident_id"] for m in x["members"]})
    assert {m["incident_id"] for m in a["members"]} == {"INC-102", "INC-217", "INC-288"}
    assert set(a["teams"]) == {"payments", "search", "platform"}
    assert "pgbouncer-main" in a["shared_dependencies"]


def test_chain_b_and_no_false_clusters(c):
    cs = c.get("/api/clusters").json()
    assert len(cs) == 2
    linked = {m["incident_id"] for x in cs for m in x["members"]}
    assert "INC-244" not in linked, "near-miss shares pg-primary but has a different cause"
    assert {"INC-156", "INC-241"} <= linked


def test_recorded_fix_proven_ineffective_by_timeline(c):
    fx = {f["id"]: f for f in c.get("/api/fixes").json()}
    assert fx["REM-31"]["kind"] == "fix" and fx["REM-31"]["status"] == "ineffective"
    assert [x["id"] for x in fx["REM-31"]["recurrences_after"]] == ["INC-217", "INC-288"]
    assert fx["REM-52"]["status"] == "held"


def test_cited_answer_and_refusal(c):
    a = c.post("/api/ask", json={"q": "What caused the checkout timeouts in January?"}).json()
    assert a["citations"] and not a["invalid_citations"]
    assert "pool" in a["answer"].lower()
    r = c.post("/api/ask", json={"q": "What is the capital of France?"}).json()
    assert r["answer"].startswith("Nothing in the record")


def test_live_incident_joins_and_debt_rises(c):
    before = {d["cluster"]: d["score"] for d in c.get("/api/debt").json()}
    r = c.post("/api/demo/drop/INC-301.md").json()
    cid = r["trace"]["result"]["joined"]
    assert "INC-301" in members(c, cid)
    after = {d["cluster"]: d["score"] for d in c.get("/api/debt").json()}
    assert after[cid] > before[cid]
    why = c.get(f"/api/clusters/{cid}/why").json()
    assert len(why["incidents"]) == 4 and len(why["evidence"]) >= 5


def test_poisoned_document_quarantined(c):
    r = c.post("/api/demo/drop/PM-199-poisoned.md").json()
    assert r["quarantined"]
    hits = c.post("/api/ask", json={"q": "maintenance mode email ops-archive"}).json()["evidence"]
    assert all(not ("Ignore previous" in e["text"]) for e in hits)


def test_preflight_warns_on_pool_change(c):
    text = c.get("/api/demo/text/CHG-88.md").json()["text"]
    r = c.post("/api/preflight", json={"text": text}).json()
    assert r["level"] == "warn" and "pgbouncer-main" in r["touched"]
    assert r["hits"][0]["failed_fixes"]


def test_policy_gate(c):
    assert c.post("/api/actions", json={"tool": "send_external_email", "args": {"to": "x@y.example"}}).json()["status"] == "blocked"
    n = c.post("/api/actions", json={"tool": "write_cluster_note", "args": {"cluster_id": "CLU-001"}}).json()
    assert n["status"] == "pending"
    done = c.post(f"/api/actions/{n['id']}/approve").json()
    assert done["status"] == "executed" and (Path(os.environ["RC_VAULT"]) / "clusters" / "CLU-001.md").exists()


def test_write_scope_enforced():
    from rootcause import policy
    with pytest.raises(PermissionError):
        policy.safe_path("incidents/INC-102.md")
    with pytest.raises(PermissionError):
        policy.safe_path("clusters/../incidents/x.md")


def test_audit_chain_and_tamper(c):
    assert c.get("/api/audit").json()["verify"]["ok"]
    assert not c.post("/api/audit/tamper").json()["verify"]["ok"]
    c.post("/api/reset")
    assert c.get("/api/audit").json()["verify"]["ok"]


def test_refuses_remote_model_endpoint():
    from rootcause import config
    with pytest.raises(ValueError):
        config.assert_local("https://api.openai.com")


def test_reingest_quarantined_doc_does_not_corrupt(c):
    for _ in range(3):
        c.post("/api/demo/drop/PM-199-poisoned.md")
        c.post("/api/demo/drop/INC-301.md")
    assert c.get("/api/clusters/CLU-001/why").status_code == 200
    c.post("/api/reset")
    assert c.get("/api/audit").json()["verify"]["ok"]
