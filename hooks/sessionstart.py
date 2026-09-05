# -*- coding: utf-8 -*-
"""The SessionStart event. Two jobs: tell the agent its own session id (without it the agent
cannot silence the watchdog) and, if the session started after a compaction, warn it honestly
that the context is already compacted."""
import json, os, sys, time

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

MARKS = ("HANDOFF.md", "STATE.md", ".claude/handoff.md")


def same_tree(a, b):
    """Is this the same tree of work. A closed session could have been sitting in a subdirectory
    of the project while a new one starts at its root — strict path equality broke on that."""
    if not a or not b:
        return False
    a, b = os.path.normcase(os.path.abspath(a)), os.path.normcase(os.path.abspath(b))
    return a == b or a.startswith(b + os.sep) or b.startswith(a + os.sep)


def main():
    ctxlib.utf8_io()
    d = ctxlib.stdin_json()
    sid = d.get("session_id", "")
    src = d.get("source", "")
    cwd = d.get("cwd") or ""
    c = ctxlib.cfg()
    lines = []

    if src == "compact":
        prev = ctxlib.state_load(sid)
        done = [e for e in ctxlib.events(200)
                if e.get("kind") == "done" and (time.time() - e.get("ts", 0)) < 3600
                and same_tree(e.get("cwd"), cwd)]
        if done:
            # The compaction happened after the ritual: the handoff is written, there is nothing
            # to lose. We accept it and work on, but we do not trust the digest.
            stream = done[-1].get("stream") or ""
            lines.append(
                "The context is compacted, but this session's work was closed by the ritual "
                "earlier, so nothing is lost. Do not trust the digest: the source of truth is the "
                "written handoff. Run Skill(skill=\"open\"%s): accept the handoff, verify what is "
                "written against reality and reach the gate."
                % ((" with the argument \"%s\"" % stream) if stream else ""))
        else:
            lines.append(
                "ATTENTION: the context is compacted and the closing ritual was never performed — "
                "part of the causality and the discarded options is lost. Start no new branches: "
                "run Skill(skill=\"close\"), gather what is left, and tell the human."
                + (" The compaction happened at %s%% of the window." % prev.get("last_pct")
                   if prev.get("last_pct") else ""))
        ctxlib.state_save(sid, {"state": "live", "soft_warned": False, "blocked_at": None,
                          "compacted": not done})
    else:
        ctxlib.state_save(sid, {"state": "live", "soft_warned": False, "cwd": cwd})
        # right after the closing ritual the intake is not up for discussion: the human already
        # approved it by pressing /clear, and awaits not the question "should I run open" but the
        # gate that follows it
        closed = [e for e in ctxlib.events(200)
                  if e.get("kind") == "done" and (time.time() - e.get("ts", 0)) < 1800
                  and same_tree(e.get("cwd"), cwd)]
        if closed and src in ("clear", "startup", "resume"):
            ctxlib.state_save(sid, {"pending_open": closed[-1].get("stream") or True})
            # the stream carries over by itself: the human pressed /clear rather than opening a
            # new piece of work, and has no reason to state again what the closed session knew
            stream = closed[-1].get("stream") or ""
            lines.append(
                "The previous session in this directory was closed by the ritual, and the context "
                "was cleared for the sake of continuing. Run Skill(skill=\"open\"%s) right "
                "now, with no clarifying questions: accept the handoff, verify what is written "
                "against reality and reach the gate. The human awaits the gate, not a question of "
                "whether to start the intake."
                % (" with the argument \"%s\" — the closed session's stream" % stream
                   if stream else ""))
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
            # begins with a message from the human. So the hint goes to his screen.
            out["systemMessage"] = ("The previous session was closed by the ritual. Write what we "
                                    "are doing next — the handoff intake runs before the reply. "
                                    "If you only need the gate — write \"go\".")
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return

main()
