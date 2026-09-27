"""OBSERVE + MODEL: read the vault, chunk, embed, and write typed rows.

The vault is an Obsidian-style folder of markdown files with YAML frontmatter.
Frontmatter fields are parsed directly; the model is only asked for fields
that are missing (constrained JSON extraction).
"""
import re
from pathlib import Path

import frontmatter

from . import audit, config, models, security
from .db import dumps, to_blob

SECTION = re.compile(r"^##\s+(.+)$", re.M)
FACTOR_HEADS = ("contributing factors", "root cause", "cause", "what happened")


def _str(v):
    if v is None:
        return ""
    return v.isoformat() if hasattr(v, "isoformat") else str(v)


def split_sections(body: str):
    """[(section_title, text)] split on '## ' headings; preamble is 'Summary'."""
    parts, last, title = [], 0, "Summary"
    for m in SECTION.finditer(body):
        chunk = body[last:m.start()].strip()
        if chunk:
            parts.append((title, chunk))
        title, last = m.group(1).strip(), m.end()
    tail = body[last:].strip()
    if tail:
        parts.append((title, tail))
    return parts


def _section(sections, heads):
    for t, txt in sections:
        if t.lower() in heads:
            return txt
    return ""


def _extract_missing(meta, body):
    """Ask the local model for component/symptom only when frontmatter lacks them."""
    need = [k for k in ("component", "symptom") if not meta.get(k)]
    if not need:
        return {}
    out = models.chat(
        "Extract fields from an incident report. Reply with JSON only: "
        '{"component": string, "symptom": string}. Use short phrases. No prose.',
        body[:3000], as_json=True)
    if not isinstance(out, dict):
        return {}
    return {k: str(out.get(k, ""))[:120] for k in need if out.get(k)}


def ingest_file(con, path: Path, actor="ingest") -> dict:
    post = frontmatter.load(path)
    meta, body = dict(post.metadata), post.content
    doc_id = str(meta.get("id") or path.stem)
    kind = str(meta.get("type", "note"))
    title = meta.get("title") or (re.search(r"^#\s+(.+)$", body, re.M) or [None, path.stem])[1]
    occurred = _str(meta.get("opened") or meta.get("date") or meta.get("applied") or meta.get("made"))

    # idempotent re-ingest
    for t, col in (("chunks", "document_id"), ("incidents", "document_id"),
                   ("remediations", "document_id"), ("decisions", "document_id")):
        if t == "chunks":
            con.execute("DELETE FROM chunks_fts WHERE rowid IN (SELECT id FROM chunks WHERE document_id=?)",
                        (doc_id,))
        con.execute(f"DELETE FROM {t} WHERE {col}=?", (doc_id,))
    con.execute("DELETE FROM documents WHERE id=?", (doc_id,))

    sections = split_sections(body)
    flagged = []
    texts = []
    for title_s, txt in sections:
        hits = security.scan(txt)
        flagged.append(hits)
        texts.append(f"{title}\n{title_s}\n{txt}")
    vecs = models.embed(texts) if texts else []
    quarantined = any(flagged)
    reason = "; ".join(sorted({h[0] for hs in flagged for h in hs}))

    con.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?,?)",
                (doc_id, str(path.relative_to(config.VAULT) if path.is_relative_to(config.VAULT) else path),
                 kind, str(meta.get("team", "")), title, occurred, audit.now(),
                 dumps({k: _str(v) if not isinstance(v, list) else v for k, v in meta.items()}),
                 int(quarantined), reason))
    for i, ((sec, txt), v, hits) in enumerate(zip(sections, vecs, flagged)):
        cur = con.execute("INSERT INTO chunks(document_id,ord,section,text,embedding,quarantined) "
                          "VALUES(?,?,?,?,?,?)", (doc_id, i, sec, txt, to_blob(v), int(bool(hits))))
        if not hits:
            con.execute("INSERT INTO chunks_fts(rowid, text) VALUES(?,?)", (cur.lastrowid, f"{title} {sec} {txt}"))

    if kind == "incident":
        meta.update(_extract_missing(meta, body))
        factors = _section(sections, FACTOR_HEADS)
        symptom = str(meta.get("symptom", ""))
        fp = models.embed([f"{symptom}. {factors}"])[0]
        deps = meta.get("depends_on") or []
        con.execute("INSERT INTO incidents VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (doc_id, doc_id, title, str(meta.get("team", "")), str(meta.get("component", "")),
                     dumps(deps if isinstance(deps, list) else [deps]), symptom, factors,
                     str(meta.get("severity", "SEV-3")), _str(meta.get("opened")),
                     _str(meta.get("restored")), to_blob(fp)))
    elif kind == "remediation":
        con.execute("INSERT INTO remediations VALUES(?,?,?,?,?,?)",
                    (doc_id, doc_id, str(meta.get("incident", "")), str(meta.get("kind", "fix")),
                     _str(meta.get("applied")), str(meta.get("summary", title))))
    elif kind == "decision":
        con.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?)",
                    (doc_id, doc_id, title, _str(meta.get("made")), str(meta.get("superseded_by") or ""),
                     "", audit.now()))
    con.commit()

    if quarantined:
        audit.record(con, actor, "INJECTION_QUARANTINED",
                     {"document": doc_id, "reason": reason,
                      "matched": [h[1] for hs in flagged for h in hs][:3]})
    return {"id": doc_id, "kind": kind, "chunks": len(sections), "quarantined": quarantined, "reason": reason}


def vault_files():
    for p in sorted(config.VAULT.rglob("*.md")):
        rel = p.relative_to(config.VAULT).parts
        if rel and rel[0] in config.SKIP_DIRS:
            continue
        yield p


def ingest_vault(con) -> list:
    return [ingest_file(con, p) for p in vault_files()]
