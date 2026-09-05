# -*- coding: utf-8 -*-
"""The SessionEnd event: remove the state of a session that has ended.

Without it the list of live ones keeps windows closed an hour ago: the state file stays, and
there is nothing to tell "the agent is thinking" from "the console has long been gone"."""
import os, sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

def main(d):
    sid = d.get("session_id")
    if not sid:
        return
    for suffix in (".json", ".state.json", ".swarm.json"):
        try:
            os.remove(os.path.join(ctxlib.CTX_DIR, sid + suffix))
        except OSError:
            pass


# stdin is a stream and it is read ONCE. Computing the argument of `shield` by reading
# it here drained the buffer before the body ran, and the body then saw an empty
# payload — the hook stayed alive, did nothing, and said nothing.
_D = ctxlib.stdin_json()
ctxlib.shield(lambda: main(_D), "sessionend", _D.get("session_id", ""), _D.get("cwd", ""))
