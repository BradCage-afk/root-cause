"""MCP server: exposes Root Cause's memory to any MCP client (Claude Desktop, IDEs, agents).

Every state-changing tool goes through the same policy gate as the UI; an agent
connected over MCP cannot do anything the policy table does not allow.

Run:  python -m rootcause.mcp_server        (stdio transport)
"""
from mcp.server.mcpserver import MCPServer

from . import cluster, debt, policy, preflight, search
from .db import connect

con = connect()
mcp = MCPServer("root-cause")


@mcp.tool()
def search_memory(query: str) -> dict:
    """Answer a question from the organisation's incident memory, with citations."""
    return search.answer(con, query)


@mcp.tool()
def list_recurrence_clusters() -> list:
    """Incidents that share an evidence-backed causal hypothesis, with failure-debt scores."""
    scores = {d["cluster"]: d["score"] for d in debt.failure_debt(con)}
    return [{"id": c["id"], "hypothesis": c["hypothesis"], "debt": scores.get(c["id"]),
             "incidents": [m["incident_id"] for m in c["members"]], "teams": c["teams"]}
            for c in cluster.recurrence_clusters(con)]


@mcp.tool()
def preflight_check(change_description: str) -> dict:
    """Check a planned change against every recurrence cluster before it ships."""
    return preflight.check(con, change_description)


@mcp.tool()
def propose_action(tool: str, args: dict) -> dict:
    """Propose an action. The policy gate decides: AUTO, APPROVAL (human in the UI) or BLOCK."""
    return policy.propose(con, tool, args, proposed_by="mcp-agent")


if __name__ == "__main__":
    mcp.run()
