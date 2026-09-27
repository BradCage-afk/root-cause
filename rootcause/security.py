"""Untrusted-content boundary.

Retrieved content is evidence, not authority. Every ingested chunk is scanned for
text that tries to address the agent; flagged chunks are quarantined before they
can reach a prompt. This is defence in depth, not a solved problem: the policy
gate still decides every action regardless of what any document says.
"""
import re

PATTERNS = [
    (r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|prompts?)", "instruction override"),
    (r"disregard (all |the )?(previous|prior|above|your) ", "instruction override"),
    (r"\byou are now\b", "role reassignment"),
    (r"\b(system prompt|developer message|maintenance mode)\b", "prompt manipulation"),
    (r"\breply only with\b|\brespond only with\b", "output control"),
    (r"\b(e-?mail|send|forward|upload|post)\b[^.\n]{0,60}\b(to|at)\b[^.\n]{0,40}(@|https?://)", "exfiltration request"),
    (r"<\s*/?\s*(tool|function_call|tool_call)\b|\"tool\"\s*:", "tool-call syntax"),
]
_COMPILED = [(re.compile(p, re.I), why) for p, why in PATTERNS]


def scan(text: str):
    """Returns a list of (reason, matched_text). Empty list means clean."""
    hits = []
    for rx, why in _COMPILED:
        m = rx.search(text)
        if m:
            hits.append((why, m.group(0)[:80]))
    return hits
