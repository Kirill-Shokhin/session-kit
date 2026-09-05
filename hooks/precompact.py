# -*- coding: utf-8 -*-
"""The PreCompact event. Auto-compaction is disabled, so what gets here is either a manual
/compact or an emergency. Compaction cannot be blocked — but a mark can be left, so that the
agent after it knows it is working on a compacted context."""
import os, sys, time

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

d = ctxlib.stdin_json()
sid = d.get("session_id")
if sid:
    ctxlib.state_save(sid, {"compacted": True, "compact_trigger": d.get("trigger", "?"),
                      "compact_ts": time.time()})
