# -*- coding: utf-8 -*-
"""The line of each subagent in the swarm panel: the name, the status and the fill of its window.
It also puts a snapshot of the swarm into the session's ctx file, so that the monitor sees not only
the main sessions but what is going on inside them."""
import json, os, sys, time

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

R, DIM, RED, YEL, GRN = "\033[0m", "\033[2m", "\033[31m", "\033[33m", "\033[32m"


def bar(pct, width=8):
    n = max(0, min(width, int(round(pct * width / 100.0))))
    return "█" * n + "░" * (width - n)


def main():
    ctxlib.utf8_io()
    d = ctxlib.stdin_json()
    c = ctxlib.cfg()
    tasks = d.get("tasks") or []
    snap = []
    for t in tasks:
        tok, win = t.get("tokenCount"), t.get("contextWindowSize")
        name = t.get("name") or t.get("type") or "agent"
        status = t.get("status") or ""
        line = [name, DIM + status + R]
        if tok and win:
            pct = tok * 100.0 / win
            col = RED if pct >= c["hard_pct"] else (YEL if pct >= c["soft_pct"] else GRN)
            line.append("%s%s %d%%%s" % (col, bar(pct), round(pct), R))
            snap.append({"name": name, "pct": round(pct, 1), "status": status})
        desc = t.get("label") or t.get("description")
        if desc:
            line.append(DIM + desc[:40] + R)
        sys.stdout.write(json.dumps({"id": t.get("id"), "content": "  ".join(line)},
                                    ensure_ascii=False) + "\n")
    sid = d.get("session_id")
    if sid:
        ctxlib.save(sid, {"swarm": snap, "swarm_ts": time.time()})


main()
