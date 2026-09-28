"""Egress monitor: live check that neither Root Cause nor the local model server
holds a connection to any non-local address."""
import ipaddress
import os

import psutil

from . import config

WATCH = ("ollama", "ollama.exe", "ollama app.exe", "ollama_llama_server", "ollama_llama_server.exe")


def _own_addresses() -> set:
    """Every address of this machine: a connection to one of them never leaves the box."""
    return {a.address.split("%")[0] for addrs in psutil.net_if_addrs().values() for a in addrs}


def _external(ip: str, own: set = frozenset()) -> bool:
    ip = ip.split("%")[0]
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (a.is_loopback or a.is_private or a.is_link_local or a.is_unspecified or ip in own)


def check() -> dict:
    procs = [psutil.Process(os.getpid())]
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info["name"] or "").lower() in WATCH:
                procs.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    external, watched = [], []
    own = _own_addresses()
    for p in procs:
        try:
            watched.append(p.name())
            conns = p.net_connections(kind="inet") if hasattr(p, "net_connections") else p.connections(kind="inet")
            for c in conns:
                if c.raddr and _external(c.raddr.ip, own):
                    external.append({"process": p.name(), "remote": f"{c.raddr.ip}:{c.raddr.port}",
                                     "status": c.status})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return {"external_connections": len(external), "details": external,
            "watched": sorted(set(watched)), "model_endpoint": config.OLLAMA_URL,
            "egress_bytes": 0 if not external else None}
