# -*- coding: utf-8 -*-
"""The PreCompact event. Auto-compaction is disabled, so what gets here is either a manual
/compact or an emergency. Compaction cannot be blocked — but a mark can be left, so that the
agent after it knows it is working on a compacted context."""
import os, sys, time

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

def main(d):
    sid = d.get("session_id")
    if sid:
        ctxlib.state_save(sid, {"compacted": True, "compact_trigger": d.get("trigger", "?"),
                          "compact_ts": time.time()})


# stdin is a stream and it is read ONCE. Computing the argument of `shield` by reading
# it here drained the buffer before the body ran, and the body then saw an empty
# payload — the hook stayed alive, did nothing, and said nothing.
_D = ctxlib.stdin_json()
ctxlib.shield(lambda: main(_D), "precompact", _D.get("session_id", ""), _D.get("cwd", ""))
