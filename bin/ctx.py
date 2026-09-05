# -*- coding: utf-8 -*-
"""A CLI on top of view.py — for when output is needed outside Claude Code.
Inside the console the same is shown by the status line, without spending context.

  python ctx.py [watch|log N|stats|clean|done <sid> <stream> <handoff>|verified <sid>|mode [mode]]
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ctxlib, view  # noqa: E402


def _date_defect(path):
    """A complaint about the dates in an archive name, or None.

    BOTH SEGMENTS ARE CHECKED, and every date in each — the file and the directory holding it.
    Stopping at the first segment that carried a date let the original incident through: where the
    handoff is named `<date>-handoff.md` the file always answers first, and a directory dated a day
    forward was never looked at. Both layouts in this kit put a date in one of the two — the
    default archive dates the directory, the kit's own journal dates the file — so a check that
    reads only one of them is a check that can be arranged around.

    Nothing further left is looked at: dates out there belong to somebody else — a dated worktree,
    a `runs/<date>/` — and refusing over them would leave the agent with nothing to rename.
    """
    import datetime
    import re
    today = datetime.date.today()
    for seg in (os.path.basename(path), os.path.basename(os.path.dirname(path))):
        for m in re.finditer(r"(?<!\d)(\d{4})-(\d\d)-(\d\d)(?!\d)", seg):
            try:
                when = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return ("`%s` in `%s` is not a date that exists. Take it from the machine: "
                        "`date +%%F`, or `Get-Date -Format yyyy-MM-dd` in PowerShell."
                        % (m.group(0), seg))
            if when > today:
                return ("`%s` in `%s` is dated ahead of today (%s) — a date that has not come yet "
                        "means the closing took it from memory instead of the clock. Rename it to "
                        "the real date (`date +%%F`, or `Get-Date -Format yyyy-MM-dd` in "
                        "PowerShell), fix the index if the work keeps one, then close."
                        % (m.group(0), seg, today.isoformat()))
    return None


def main():
    ctxlib.utf8_io()
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "done":
        # ALL THREE VALUES ARE REQUIRED, AND THE REFUSAL IS LOUD. They used to be optional, and an
        # empty stream is indistinguishable from "this project has no streams": two works closed
        # in one console, the later one recorded nothing, and the next agent took the wrong
        # handoff without a single error along the way. A silent wrong intake is dearer than one
        # extra call, so a closing that names no work does not go through.
        if len(a) < 4:
            print("usage: ctx.py done <session id> <stream> <path to this stream's handoff>")
            print("       ctx.py done <session id> <stream> -      (no handoff: a session that "
                  "wrote none)")
            print("all three values are what the next agent is opened with; without them the "
                  "intake has to guess, and a wrong guess is silent")
            return 1
        sid, stream = a[1], a[2].strip()
        raw = " ".join(a[3:]).strip()
        if not stream:
            print("the stream must be named: it is what the next agent is opened with")
            return 1
        # THE WAY OUT FOR A SESSION WITH NO HANDOFF. The watchdog stops at the threshold in ANY
        # session, including a one-off in a directory that has no ritual and will write no
        # handoff. Demanding a file there would leave such a session unable to close at all — it
        # would be blocked over and over, and the trail would score the kit's own refusal as a
        # defect of the human. `-` says plainly that there is none, and the next agent is told so.
        if raw == "-":
            h = ""
        else:
            h = os.path.abspath(os.path.expanduser(raw))
            if not os.path.isfile(h):
                print("there is no file at %s — the path must point at the file the next agent "
                      "reads, and it must already be written. If this session wrote none, say so "
                      "explicitly: ctx.py done %s %s -" % (h, sid, stream))
                return 1
        # A DATE IN THE ARCHIVE NAME THAT HAS NOT COME YET IS ALWAYS WRONG. Archive names order
        # the provenance, and an agent that writes the date from memory instead of reading the
        # clock dates the closing forward: it happened, the archive jumped a day, the series
        # skipped one, and the closing of the real date would have collided with it.
        #
        # ONLY THE LAST TWO SEGMENTS ARE LOOKED AT — the file and the directory holding it. The
        # whole path was searched at first, and it failed both ways at once: a dated directory
        # anywhere to the left (`runs/2026-08-01/`, a dated worktree) masked the future date on the
        # right, and it also refused closings whose archive name was perfectly correct, over a date
        # the agent had never written and could not rename. A date in the PAST is fine and stays
        # fine: a session that began yesterday and ran through the night keeps its start date.
        #
        # A layout that puts no date in the name at all is not covered here. This is a cheap net
        # over the one surface a machine can check, not a proof that the dates are right.
        why = _date_defect(h)
        if why:
            print(why)
            return 1
        d, st = ctxlib.load(sid), ctxlib.state_load(sid)
        # THE DIRECTORY COMES FROM WHICHEVER OF THE TWO FILES HAS IT. The metrics file is written
        # by the status line, and where it is not installed the closing recorded an empty cwd —
        # after which the intake matched nothing and the next agent was told nothing at all. The
        # hook writes the same field into the state file, so one of the two always knows.
        cwd = d.get("cwd") or st.get("cwd") or os.getcwd()
        ctxlib.state_save(sid, {"state": "closed", "stream": stream, "handoff": h})
        # THE TERMINAL OF THE SESSION BEING CLOSED, and nobody else's. Its own hook wrote it into
        # the session state. If the state is gone — SessionEnd removes it, so tidying up after a
        # dead session lands here — the terminal is UNKNOWN, and unknown must stay unknown: taking
        # the caller's would brand a foreign work as this window's and hand it over on the next
        # `/clear`. An unmarked closing is offered as a question, which is the honest outcome.
        ctxlib.event("done", sid, d.get("pct", 0), cwd,
                     {"stream": stream, "handoff": h, "console": st.get("console") or []})
        print("session %s marked as closed, stream: %s, handoff: %s"
              % (sid, stream, h or "NONE — the next agent will be told to find it itself"))
    elif cmd == "verified":
        if len(a) < 2:
            print("a session id is required")
            return 1
        # WHERE THE CHECK STANDS ON THE WINDOW, OR NOTHING AT ALL. `0` was written here when the
        # fill was unknown, and zero is a POSITION: every later delivery then read as "the window
        # grew by more than the re-arm step since the check", so the gate fired on every single
        # turn and the session could never finish an answer. Unknown must stay unknown — the
        # watchdog knows how to fall back on the point where it demanded the check.
        d, c = ctxlib.load(a[1]), ctxlib.cfg()
        fresh = d.get("ts") and (time.time() - d["ts"]) < c["stale_sec"]
        at = round(d["used"] * 100.0 / d["size"], 1) if fresh and d.get("used") and d.get("size") else None
        ctxlib.state_save(a[1], {"verified": True, "verified_at": at, "gate_blind": False})
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
        try:
            n = int(a[1]) if len(a) > 1 else 40
        except ValueError:
            n = 0
        if n < 1:
            # `log 0` printed the whole trail and `log -5` printed all but the first five: int()
            # accepted them and the slice quietly meant something else entirely.
            print("usage: ctx.py log <how many entries, 1 or more>")
            return 1
        print(view.log(n))
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
    elif not cmd:
        print(view.table())
    else:
        # A MISTYPED COMMAND USED TO PRINT THE TABLE AND EXIT 0. `ctx.py doen <sid> ...` reported
        # success while the session stayed open — the silent wrong outcome this file exists to
        # prevent, one letter away.
        print("unknown command: %s" % cmd)
        print("usage: ctx.py [watch|log N|stats|clean|done <sid> <stream> <handoff>"
              "|verified <sid>|mode [mode]]")
        return 1
    return 0


sys.exit(main())
