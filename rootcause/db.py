"""SQLite store. The schema mirrors the Postgres + pgvector design one-to-one;
vectors are float32 blobs here and `vector(n)` columns there."""
import json
import sqlite3
import numpy as np

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, path TEXT, kind TEXT, team TEXT, title TEXT,
  occurred_at TEXT, ingested_at TEXT, meta TEXT, quarantined INTEGER DEFAULT 0,
  quarantine_reason TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT, document_id TEXT, ord INTEGER,
  section TEXT, text TEXT, embedding BLOB, quarantined INTEGER DEFAULT 0
);
-- standalone FTS table (rowid = chunks.id): deletes are always safe, even for rows never indexed
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text);

CREATE TABLE IF NOT EXISTS incidents (
  id TEXT PRIMARY KEY, document_id TEXT, title TEXT, team TEXT, component TEXT,
  depends_on TEXT, symptom TEXT, factors TEXT, severity TEXT,
  opened_at TEXT, restored_at TEXT, fingerprint BLOB
);
CREATE TABLE IF NOT EXISTS remediations (
  id TEXT PRIMARY KEY, document_id TEXT, incident_id TEXT, kind TEXT,
  applied_at TEXT, description TEXT
);
CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY, document_id TEXT, title TEXT, made_at TEXT,
  superseded_by TEXT, valid_until TEXT, recorded_at TEXT
);
CREATE TABLE IF NOT EXISTS clusters (
  id TEXT PRIMARY KEY, created_at TEXT, hypothesis TEXT, centroid BLOB,
  member_count INTEGER, representative_incident_id TEXT
);
CREATE TABLE IF NOT EXISTS cluster_members (
  cluster_id TEXT, incident_id TEXT, similarity REAL, verdict TEXT,
  confidence REAL, reason TEXT, added_at TEXT, PRIMARY KEY (cluster_id, incident_id)
);
-- blocking index: which clusters own which component/dependency nodes
CREATE TABLE IF NOT EXISTS cluster_nodes (
  cluster_id TEXT, node TEXT, PRIMARY KEY (cluster_id, node)
);
CREATE INDEX IF NOT EXISTS cluster_nodes_node ON cluster_nodes(node);
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, remediation_id TEXT, cluster_id TEXT,
  predicted_at TEXT, verified_at TEXT, outcome TEXT, evidence TEXT
);
CREATE TABLE IF NOT EXISTS actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, tool TEXT, args TEXT, permission TEXT,
  risk TEXT, decision TEXT, status TEXT, reason TEXT, proposed_by TEXT,
  created_at TEXT, resolved_at TEXT, result TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, actor TEXT, action TEXT,
  payload TEXT, prev_hash TEXT, hash TEXT
);
"""


def connect(path=None) -> sqlite3.Connection:
    p = path or config.DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def to_blob(v) -> bytes:
    return np.asarray(v, dtype=np.float32).tobytes()


def from_blob(b) -> np.ndarray:
    return np.frombuffer(b, dtype=np.float32) if b else np.zeros(0, dtype=np.float32)


def dumps(o) -> str:
    return json.dumps(o, sort_keys=True, ensure_ascii=False)


def rows(con, sql, args=()):
    return [dict(r) for r in con.execute(sql, args).fetchall()]
