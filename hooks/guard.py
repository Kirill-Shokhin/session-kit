# -*- coding: utf-8 -*-
"""The context window watchdog (the Stop event): it does not let a session quietly creep into
the zone where the agent is already imprecise. It fires the moment the agent has finished a
reply — at a natural micro-task boundary.

The watchdog does not block the author's question and does not interfere with the reply: it keeps
the agent from STOPPING after the reply. That is why "answer me, then close" works by itself.

A refusal ("hold on, finish this first") is respected by deferral, not by capitulation: the
watchdog stays silent until the window grows, and demands again — the more insistently the closer
the limit is. It goes quiet for good only after the ritual has been performed. Otherwise a pair of
"got it, ok" would cost the closing altogether.
"""
import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

CTX_CMD = os.path.join(os.path.expanduser("~"), ".claude", "kit", "bin", "ctx.py")
# Recognizing the DELIVERY of a result. A narrow list of phrasings missed real reports, a wide
# one caught negations and intermediate steps, so two signs decide together: a delivery marker is
# there and a sign of the work continuing is not. Both languages are listed: the agent may report
# in either one.
DONE_RE = re.compile(
    r"(вс[её] готово|готово к проверк|можно (проверять|тестировать|принимать|смотреть)|"
    r"работа (завершена|закончена)|задача выполнена|полностью реализован|реализовано полностью|"
    r"^готово[.!]?$|^сделано[.!]?$|собрано и работает|готов к сдаче|"
    r"(everything|it|all|the work) is (now )?(done|ready|complete|finished)|"
    r"ready (for (review|testing|a check|checking)|to (ship|hand over))|"
    r"you can (check|test|review|take a look)|(the )?task (is )?(complete|completed|done)|"
    r"fully implemented|implemented in full|built and works|"
    r"^done[.!]?$|^finished[.!]?$)", re.I | re.M)
# Continuation comes in two kinds, and only the first may cancel a delivery.
# SELF — the agent keeps working itself, so this is not a delivery.
SELF_RE = re.compile(
    r"(иду дальше|перехожу|продолжаю|сейчас займусь|начинаю|"
    r"moving on|continuing|i'?ll now|now i'?ll|starting (on|with|the))", re.I)
# WEAK — "next step", "in progress": in a delivery report these address the author rather
# than describe the agent's work. They cancel a delivery only when placed BEFORE its marker.
WEAK_RE = re.compile(
    r"(следующ\w* (шаг\w*|задач\w*)|в процессе|next (up|step)s?|in progress|"
    r"still (need|have) to)", re.I)
NEG_RE = re.compile(r"(не|ещ[её] не|пока не)\s+(вс[её] )?готово|"
                    r"(завершена|закончена|выполнена|реализовано) не полностью|"
                    r"not\s+(yet\s+)?(quite\s+)?(all\s+)?(done|ready|finished|complete|fully)", re.I)


def is_delivery(msg):
    """A delivery is work presented to the author as finished. The word "done" in the middle of
    a turn is not one, and a list of further steps FOR THE HUMAN does not cancel one."""
    # The field is whatever the host puts there. It has always been a string so far, and that is
    # precisely why the assumption is untested: were it ever to arrive as a list of content
    # blocks, `re.search` would raise on EVERY Stop and the watchdog — nudges, the threshold, the
    # block, the recheck — would go dark with nothing on the console.
    if isinstance(msg, (list, tuple)):
        msg = " ".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in msg)
    if not isinstance(msg, str) or not msg:
        return False
    done = DONE_RE.search(msg)
    if not done or SELF_RE.search(msg):
        return False
    neg = NEG_RE.search(msg)
    if neg and abs(neg.start() - done.start()) < 60:   # a negation next to the readiness marker
        return False
    weak = WEAK_RE.search(msg)
    return not (weak and weak.start() < done.start())

def out(ctx):
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "Stop", "additionalContext": ctx}}, ensure_ascii=False))


def snooze(pct, c):
    """By how much the window must grow before demanding again.
    The closer the limit, the shorter the deferral; zero is not allowed — that would be a loop."""
    if pct >= 92:
        return 0.3
    if pct >= 85:
        return 2.0
    return float(c["snooze_pct"])


def main(d):
    ctxlib.utf8_io()
    if d.get("agent_id"):          # a subagent ends on its own, the ritual is not its business
        return 0
    sid = d.get("session_id")
    if not sid:
        return 0
    c = ctxlib.cfg()
    st = ctxlib.state_load(sid)
    u = ctxlib.usage(sid, d.get("transcript_path"))
    pct = u[0] if u else None

    # The critic gate does not depend on measuring the window: consensus is needed regardless of
    # whether the fill could be computed. Past the closing threshold the gate stays silent — there
    # the ritual has priority.
    #
    # Protection against loops and repeats. The gate fires again only once the window has grown by
    # regate_pct since the LATER of two marks — the last demand and the last counted check — that
    # is, once a new portion of work has appeared. Throttling by only one of the two produced both
    # extremes in turn: a demand on every single turn, and silence for the rest of the session.
    if (c.get("mode", "autonomous") == "autonomous"
            and st.get("state") != "closed"
            and (pct is None or pct < c["hard_pct"])
            and is_delivery(d.get("last_assistant_message"))):
        # A SESSION ALREADY CLOSED IS NOT GATED. The ritual ends by declaring the work finished,
        # and that phrasing is exactly what the detector looks for: the closing collided with the
        # gate and the agent was sent to the critics while the handoff was already written.
        gate_at, ver_at = st.get("gate_at"), st.get("verified_at")
        # POSITIONS BELOW THE CURRENT FILL ARE STALE. They are absolute marks on a window that can
        # SHRINK — a model change alters its size, host-side context editing lowers the fill — and
        # signed arithmetic then answered "it has not grown" for the whole run back up, killing
        # the gate for the rest of the session.
        if pct is not None:
            gate_at = None if gate_at is not None and gate_at > pct else gate_at
            ver_at = None if ver_at is not None and ver_at > pct else ver_at
        # `ctx.py verified` can only read the metrics file, and without a status line there is
        # none: it writes no position at all. The firing point is the honest fallback — the check
        # was counted somewhere at or after the demand.
        if st.get("verified") and ver_at is None:
            ver_at = gate_at
        if pct is None:
            # THE FILL CANNOT BE MEASURED — no status line and no transcript. There is no
            # distance by which to tell new work from old, so the gate demands consensus once and
            # then trusts the counted check for the rest of the session. The alternative — never
            # settling — would demand the critics on every single delivery with no way out. The
            # trade is deliberate; recording a numeric position here (it used to write zero) was
            # not: it left both re-arming branches unreachable and `verified` unread.
            fire = not st.get("verified") and not st.get("gate_blind")
            settled = False
        else:
            # Settled: the check is counted and no new portion of work has piled up since.
            settled = (st.get("verified") and ver_at is not None
                       and pct - ver_at < c["regate_pct"])
            # Re-arms on growth — measured from the LATER of the two marks. From `ver_at` alone it
            # fired on every single turn once the check fell behind; from `gate_at` alone an
            # ignored demand disarmed the gate for the whole session. Both are marks of "you were
            # already asked here", and the later one is the one that counts.
            marks = [x for x in (gate_at, ver_at) if x is not None]
            fire = not marks or pct - max(marks) >= c["regate_pct"]
        if fire and not settled:
            ctxlib.state_save(sid, {"gate_at": pct, "gate_blind": pct is None})
            ctxlib.event("verify_gate", sid, pct or 0, d.get("cwd", ""))
            sys.stderr.write(chr(10).join([
                "READINESS DECLARED, THERE IS NO CONSENSUS.",
                "The author looks at a result that passed a check, not at the moment when it seemed",
                "to you that the work had ended.",
                "",
                "You ALREADY ran the check and it converged — just count it in and deliver, do not",
                "run it again:",
                "    python \"%s\" verified %s" % (CTX_CMD, sid),
                "",
                "You did not run it — then before delivering:",
                "1. A fresh critic with no context, unaware of the edits, over all you deliver.",
                "2. A fix — and a fresh critic again, until the iteration's changes hold no",
                "   significant defects.",
                "3. Count the check in with the command above and deliver in a single message, on",
                "   the substance of the result.",
                "Do not ask permission to run the critics: it is an ordinary part of the work.",
            ]) + chr(10))
            return 2

    if not u:
        return 0
    pct, used, size, _src = u
    # BOOKKEEPING MUST NOT COST THE STOP. This field is cosmetic — it only tells the compaction
    # branch how full the window was — but its write stood ahead of every threshold, and a failing
    # `os.replace` (another process holding the file, which does happen on Windows) took the whole
    # branch down with it: no stop, no message, exit 0.
    try:
        ctxlib.state_save(sid, {"last_pct": round(pct, 1)})
    except Exception:
        pass

    # the ritual is done — one recheck pass is left, the author used to ask for it by hand
    if st.get("state") == "closed":
        if not st.get("recheck_asked"):
            ctxlib.state_save(sid, {"recheck_asked": True})
            ctxlib.event("recheck", sid, pct, d.get("cwd", ""))
            sys.stderr.write(
                "RECHECK AFTER THE CLOSING (one pass, then I let go).\n"
                "You have just assembled the handoff on a full window — such a handoff\n"
                "systematically holds unfinished and imprecise places. Re-read YOUR OWN files\n"
                "through the eyes of the one receiving them:\n"
                "1. The handoff, the DAG and the vector: is every claim backed, does every link\n"
                "   resolve, are there no broken-off thoughts and no 'will write this later'.\n"
                "2. The negative edges: are all discarded paths written down WITH THEIR REASON.\n"
                "3. The docs you edited: are there no contradictions left with what you wrote.\n"
                "Whatever you find — fix it silently and in place, without asking. Then tell the\n"
                "human in one line that the recheck passed and what was fixed.\n")
            return 2
        return 0
    if pct >= c["hard_pct"]:
        last = st.get("blocked_at")
        if last is None or (pct - last) >= snooze(pct, c):
            # the record of "already blocked here" guards against a loop, but losing it must not
            # lose the block itself: the message and the code below matter more
            try:
                ctxlib.state_save(sid, {"blocked_at": pct})
            except Exception:
                pass
            ctxlib.event("block", sid, pct, d.get("cwd", ""))
            sys.stderr.write(
                "STOP ON WINDOW FILL: %d%% (%s).\n"
                "From this level on your judgment is biased, and it only gets worse.\n\n"
                "1. Bring the current micro-task to a meaningful boundary, start no new ones.\n"
                "2. Run the closing skill: Skill(skill=\"close\").\n"
                "3. When the ritual is finished — run python \"%s\" done %s <stream> <path to the handoff you wrote>\n"
                "   All three: they are the whole of what the next agent is opened with,\n"
                "   and the call refuses without them. No handoff written — put `-`.\n"
                "4. If the wording of the ritual got in the way or led past the point — a line in\n"
                "   ~/.claude/kit/FEEDBACK.md: what was said, what came out, what was missing.\n\n"
                "If the author asked you to hold on — obey him, finish what he named and close\n"
                "right after. I will not stay silent until the end of the session: I will remind\n"
                "you when the window grows, the more often the closer the limit is.\n"
                % (round(pct), ctxlib.fmt(used, size), CTX_CMD, sid))
            # the stop code must survive a failure of this cosmetic line: it only sets the
            # terminal title, and losing the block over it would be absurd
            try:
                sys.stdout.write(json.dumps({"terminalSequence": "]0;%d%% CLOSING · %s"
                                             % (round(pct), os.path.basename((d.get("cwd") or "").rstrip("/\\")))}))
            except Exception:
                pass
            return 2
        return 0

    if pct >= c["soft_pct"] and not st.get("soft_warned"):
        ctxlib.state_save(sid, {"soft_warned": True, "nudged_at": pct})
        ctxlib.event("soft", sid, pct, d.get("cwd", ""))
        out("The window is %d%% full (%s). The closing threshold is %d%%. Start no new large "
            "branches. If there was a fork since the last journal entry — a discarded option, a "
            "change of direction, a measurement, a divergence from expectation, a course "
            "correction from the author — write it down now (the mark skill). There were no "
            "forks — nothing needs to be written."
            % (round(pct), ctxlib.fmt(used, size), c["hard_pct"]))
        return 0

    # a quiet nudge on the GROWTH of the window: the growth is proportional to the work done,
    # and hence to the number of forks that would otherwise stay unwritten
    base = st.get("nudged_at")
    if base is None:
        if pct >= c["nudge_from"]:
            ctxlib.state_save(sid, {"nudged_at": pct})
        return 0
    if pct - base >= c["nudge_step"]:
        ctxlib.state_save(sid, {"nudged_at": pct})
        ctxlib.event("nudge", sid, pct, d.get("cwd", ""))
        out("Window: %d%% (+%d%% since the last mark). Go over the list of forks: a discarded "
            "option · a decision that changes direction · a measurement · a divergence from "
            "expectation · a course correction from the author. Whatever of that happened since "
            "the last mark — write it into the session journal (the mark skill), one entry per "
            "fork. Nothing happened — carry on, this needs no reply."
            % (round(pct), round(pct - base)))
    return 0


# stdin once, before the shield: computing its arguments here would drain the stream, and
# reading the globals here would read them BEFORE main() ever set them
_D = ctxlib.stdin_json()
sys.exit(ctxlib.shield(lambda: main(_D), "guard", _D.get("session_id", ""),
                       _D.get("cwd", "")) or 0)
