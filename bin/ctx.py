# -*- coding: utf-8 -*-
"""A CLI on top of view.py — for when output is needed outside Claude Code.
Inside the console the same is available via the /swarm command, without spending context.

  python ctx.py [watch|log N|stats|clean|done <sid> [stream]|verified <sid>|mode [mode]]
"""
import os, sys, time

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib, view  # noqa: E402


def main():
    ctxlib.utf8_io()
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "done":
        if len(a) < 2:
            print("a session id is required")
            return 1
        d = ctxlib.load(a[1])
        stream = a[2] if len(a) > 2 else d.get("stream", "")
        ctxlib.state_save(a[1], {"state": "closed", "stream": stream})
        ctxlib.event("done", a[1], d.get("pct", 0), d.get("cwd", ""), {"stream": stream})
        print("session %s marked as closed%s" % (a[1], (", stream: " + stream) if stream else ""))
    elif cmd == "verified":
        if len(a) < 2:
            print("a session id is required")
            return 1
        d = ctxlib.load(a[1])
        ctxlib.state_save(a[1], {"verified": True, "verified_at": d.get("pct", 0)})
        ctxlib.event("verify", a[1], d.get("pct", 0), d.get("cwd", ""))
        print("the critics' check is counted for session %s" % a[1])
    elif cmd == "mode":
        import json as _json
        c = ctxlib.cfg()
        if len(a) < 2:
            print("current mode: %s" % c.get("mode", "autonomous"))
            return 0
        if a[1] not in ("autonomous", "stepwise"):
            print("the mode is either autonomous or stepwise")
            return 1
        try:
            raw = _json.load(open(ctxlib.CFG_PATH, encoding="utf-8"))
        except Exception:
            raw = {}
        raw["mode"] = a[1]
        _json.dump(raw, open(ctxlib.CFG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("mode switched: %s" % a[1])
        print("the mechanisms (the critic gate) obey at once; the rule set reaches the agents "
              "from the next session on — tell the running ones about the switch in words.")
    elif cmd == "log":
        print(view.log(int(a[1]) if len(a) > 1 else 40))
    elif cmd == "stats":
        print(view.stats())
    elif cmd == "clean":
        print(view.clean())
    elif cmd == "watch":
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                print(view.table(), flush=True)
                time.sleep(5)
        except KeyboardInterrupt:
            pass
    else:
        print(view.table())
    return 0


sys.exit(main())
