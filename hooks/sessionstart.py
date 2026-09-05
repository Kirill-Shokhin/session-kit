# -*- coding: utf-8 -*-
"""The SessionStart event. Two jobs: tell the agent its own session id (without it the agent
cannot silence the watchdog) and, if the session started after a compaction, warn it honestly
that the context is already compacted."""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

# `.claude/ritual.md` first: it IS the ritual, and its absence from this list is already
# a FEEDBACK entry — a session opened where the frame existed and nothing suggested `open`.
_SAID = False

MARKS = (".claude/ritual.md", "HANDOFF.md", "STATE.md", ".claude/handoff.md")


def main(d):
    global _SAID
    ctxlib.utf8_io()
    sid = d.get("session_id", "")
    if not sid:
        # every other hook guards this; here it left `~/.claude/ctx/.state.json` behind — a file
        # shared by all id-less sessions and never swept, since glob skips a leading dot
        _SAID = True
        return
    src = d.get("source", "")
    cwd = d.get("cwd") or ""
    c = ctxlib.cfg()
    lines = []

    if src == "compact":
        prev = ctxlib.state_load(sid)
        # A compaction keeps the session id, so THIS session's own closing is known exactly — no
        # need to ask the directory who closed here. The trail is only the fallback.
        own = ({"arg": ctxlib.open_arg(prev), "choices": []}
               if prev.get("state") == "closed" and (prev.get("stream") or prev.get("handoff"))
               else None)
        done = None if own else ctxlib.closed_works(cwd)
        if own or done:
            # The compaction happened after the ritual: the handoff is written, there is nothing
            # to lose. We accept it and work on, but we do not trust the digest.
            lines.append(
                "The context is compacted, but this session's work was closed by the ritual "
                "earlier, so nothing is lost. Do not trust the digest: the source of truth is the "
                "written handoff. " + ctxlib.intake_body(own or ctxlib.pending(done, cwd)))
        else:
            lines.append(
                "ATTENTION: the context is compacted and the closing ritual was never performed — "
                "part of the causality and the discarded options is lost. Start no new branches: "
                "run Skill(skill=\"close\"), gather what is left, and tell the author."
                + (" The compaction happened at %s%% of the window." % prev.get("last_pct")
                   if prev.get("last_pct") else ""))
        # `own` short-circuits the trail lookup, so `done` is None there by construction —
        # taking that for "no closing found" flagged a properly closed session as compacted.
        #
        # THE POSITIONS ON THE WINDOW ARE RESET TOO. `gate_at`, `verified_at` and `nudged_at` are
        # absolute marks on a fill that the compaction has just collapsed: kept across it, they
        # sit far above the new fill, and every "has it grown by the re-arm step" test answers no
        # for the rest of the session — the critic gate and the journal reminders both go dead.
        # `blocked_at` was already being reset; its two neighbours were not.
        ctxlib.state_save(sid, {"state": "live", "soft_warned": False, "blocked_at": None,
                          "gate_at": None, "verified_at": None, "nudged_at": None,
                          "verified": False, "gate_blind": False,
                          "compacted": not (own or done)})
    else:
        # A CLOSED SESSION STAYS CLOSED ACROSS `--resume`. Overwriting the state with "live" here
        # re-armed the watchdog on work that had already been closed and recorded: the soft
        # threshold came again, and at the hard one the agent was told to close what was closed.
        was = ctxlib.state_load(sid).get("state")
        # the terminal is recorded by the session's OWN hook: `ctx.py done` may be run from a
        # different window (recovering after a crash, tidying up a dead session), and stamping the
        # caller's terminal there would hand that window's next intake somebody else's work
        ctxlib.state_save(sid, {"state": was if was == "closed" else "live",
                                "cwd": cwd, "soft_warned": False,
                                "console": ctxlib.console()})
        # right after the closing ritual the intake is not up for discussion: the author already
        # approved it by pressing /clear, and awaits not the question "should I run open" but the
        # gate that follows it
        # A session's OWN closing is not an invitation to open it again: on `--resume` the id and
        # the whole context survive, and the agent was being told to take a handoff it had just
        # written. Its own re-check pass, if it had not happened yet, was lost with the flag.
        closed = [e for e in ctxlib.closed_works(cwd) if e.get("sid") != sid]
        if closed and src in ("clear", "startup", "resume"):
            # what the closing knew carries over by itself: the author pressed /clear rather than
            # opening a new piece of work, and has no reason to state it again
            pend = ctxlib.pending(closed, cwd)
            ctxlib.state_save(sid, {"pending_open": pend})
            lines.append(
                "The previous session in this console was closed by the ritual, and the context "
                "was cleared for the sake of continuing. " + ctxlib.intake_body(pend)
                + ("" if pend.get("choices") else
                   " Verify what is written against reality and reach the gate. The author awaits "
                   "the gate, not a question of whether to start the intake."))
        elif any(os.path.exists(os.path.join(cwd, m)) for m in MARKS):
            lines.append(
                "The session ritual is in force in this project. If you are continuing work "
                "started earlier — begin with the handoff intake: Skill(skill=\"open\"). If it is "
                "a one-off question, the ritual is not needed.")
    # The id and the rule set are needed in any session: after a compaction the agent is also
    # asked to run verified and done, and without the sid it cannot.
    lines.append("The id of this session: %s. The context window watchdog thresholds: reminder "
                 "%d%%, stop %d%%." % (sid, c["soft_pct"], c["hard_pct"]))
    mode = c.get("mode", "autonomous")
    rp = os.path.join(os.path.expanduser("~"), ".claude", "kit", "rules", mode + ".md")
    if os.path.exists(rp):
        lines.append(open(rp, encoding="utf-8").read().strip())

    ctxlib.event("start", sid, 0, cwd, {"source": src})   # so the reason is visible from the trail
    if lines:
        out = {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                      "additionalContext": "\n".join(lines)}}
        if ctxlib.state_load(sid).get("pending_open"):
            # SessionStart puts text into the context but does not start the agent: generation
            # begins with a message from the author. So the hint goes to his screen.
            out["systemMessage"] = ("The previous session was closed by the ritual. Write what we "
                                    "are doing next — the handoff intake runs before the reply. "
                                    "If you only need the gate — write \"go\".")
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        _SAID = True
        return

# stdin is read ONCE, outside the guard: the fallback below cannot read it a second time, and a
# fallback that reports "unknown" instead of the session id is no fallback at all.
_D = ctxlib.stdin_json()
ctxlib.shield(lambda: main(_D), "sessionstart", _D.get("session_id", ""),
              _D.get("cwd", ""))
if not _SAID:
    # the hook died before it printed anything: the agent must at least keep its session id,
    # otherwise it cannot silence the watchdog for the rest of the session
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "The id of this session: %s. The session-start hook itself failed "
                             "(see stderr); the window watchdog is live."
                             % _D.get("session_id", "unknown")}}, ensure_ascii=False))
