# -*- coding: utf-8 -*-
"""The SessionEnd event: remove the state of a session that has ended.

Without it the list of live ones keeps windows closed an hour ago: the state file stays, and
there is nothing to tell "the agent is thinking" from "the console has long been gone"."""
import os, sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

d = ctxlib.stdin_json()
sid = d.get("session_id")
if sid:
    try:
        for suffix in (".json", ".state.json"):
            try:
                os.remove(os.path.join(ctxlib.CTX_DIR, sid + suffix))
            except OSError:
                pass
    except OSError:
        pass
