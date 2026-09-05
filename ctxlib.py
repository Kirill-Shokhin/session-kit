# -*- coding: utf-8 -*-
"""Shared layer: where the window state lives, how it is read and how it is written.

The unit of state is the file ~/.claude/ctx/<session_id>.json. It is written by the
status line (often, cheaply) and read by the hooks and the monitor. Computing it from
the transcript is the fallback path in case the status line is not installed.
"""
import json, os, sys, time

HOME = os.path.expanduser("~")
CTX_DIR = os.path.join(HOME, ".claude", "ctx")
CFG_PATH = os.path.join(HOME, ".claude", "kit", "config.json")

DEFAULTS = {
    "soft_pct": 60,       # reminder: time to record decisions and plan the closing
    "hard_pct": 75,       # block the stop until close has been performed
    "nudge_from": 20,     # from which fill level to start reminding about the journal
    "nudge_step": 10,     # and after what increment of the window to repeat
    "snooze_pct": 5,      # by how many % of the window the watchdog goes quiet after a refusal
    "regate_pct": 10,     # window growth after which the critic gate is armed again
    # HOW LONG A CLOSING STAYS AVAILABLE TO THE NEXT SESSION. It was half an hour, and the budget
    # started ticking at `ctx.py done` — which the ritual calls BEFORE the gate and the re-check,
    # so the closing's own tail ate most of it: measured intervals from done to the next session
    # run 8 to 24.5 minutes, the last of them 82 % of what there was. Step away from the machine
    # after closing and the intake silently degrades to "the ritual is in force here", with no
    # stream and no path — the exact failure this whole contract exists to prevent.
    "handoff_sec": 43200,  # 12 hours
    "stale_sec": 600,     # older than this a ctx file is not a live reading
    "hide_sec": 120,      # older than this reading a session is considered closed
    "panel_sec": 15,      # how many seconds the panel stays unfolded
    "panel_on_prompt": True,  # and it unfolds by itself after every message
    "fallback_window": 200000,
    # The switch: autonomous — the agent decides on its own and brings only what passed the
    # critics; stepwise — the author verifies every step (the mode for scarce limits).
    "mode": "autonomous",
}


_NUM = ("soft_pct", "hard_pct", "nudge_from", "nudge_step", "snooze_pct", "regate_pct",
        "stale_sec", "hide_sec", "panel_sec", "fallback_window", "handoff_sec")


def cfg():
    """config.json is hand-edited by the author, so it is not trusted to hold numbers.

    A threshold that arrives as a string or null makes every comparison in the watchdog raise —
    and a hook that raises is silent, so the whole thing would go dark with nothing on screen.
    A bad value falls back to the default rather than taking the watchdog down with it.
    """
    d = dict(DEFAULTS)
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            d.update(json.load(f))
    except Exception:
        pass
    for k in _NUM:
        try:
            d[k] = float(d[k]) if isinstance(d[k], str) else d[k] + 0
        except Exception:
            d[k] = DEFAULTS[k]
    if d.get("mode") not in ("autonomous", "stepwise"):
        d["mode"] = DEFAULTS["mode"]
    if not isinstance(d.get("panel_on_prompt"), bool):
        d["panel_on_prompt"] = DEFAULTS["panel_on_prompt"]
    return d


def _path(sid):
    return os.path.join(CTX_DIR, "%s.json" % sid)


def load(sid):
    try:
        with open(_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _replace(tmp, dst, tries=12):
    """`os.replace` with a short retry: on Windows it fails while another process holds the target
    open, and two writers a few seconds apart do meet. The last failure is not swallowed."""
    for i in range(tries):
        try:
            os.replace(tmp, dst)
            return
        except OSError:
            if i == tries - 1:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                raise
            time.sleep(min(0.05, 0.005 * (i + 1)))


def save(sid, patch):
    """Write the metrics atomically, over a file two processes write a few seconds apart.

    The status line and the subagent line carry the SAME session id. A single fixed
    `<sid>.json.tmp` made them collide on the temporary file, so it carries the pid — but that was
    only half of it: on Windows `os.replace` also fails while the OTHER process still holds the
    TARGET open, and the trail kept collecting `PermissionError` after the first fix. A short retry
    covers it; the window is milliseconds wide, and a lost tick costs the watchdog its measurement.
    """
    os.makedirs(CTX_DIR, exist_ok=True)
    d = load(sid)
    d.update(patch)
    d["sid"] = sid
    # the subagent line used to write the swarm snapshot in here; `update` never removes a key, so
    # a frozen snapshot from before that change would be carried forward as live for ever
    d.pop("swarm", None)
    d.pop("swarm_ts", None)
    tmp = _path(sid) + ".tmp-%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    _replace(tmp, _path(sid))
    return d


def swarm_path(sid):
    """The subagent line's own file. IT USED TO WRITE INTO THE SESSION'S METRICS FILE, which the
    status line rewrites every few seconds under the SAME id: two processes over one file, and on
    Windows `os.replace` fails while the other still holds it. Retrying only narrows the window —
    the defect is the sharing. Each writer owns its file; the reader merges them."""
    return os.path.join(CTX_DIR, "%s.swarm.json" % sid)


def swarm_save(sid, patch):
    os.makedirs(CTX_DIR, exist_ok=True)
    tmp = swarm_path(sid) + ".tmp-%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(patch, f, ensure_ascii=False)
    _replace(tmp, swarm_path(sid))


def swarm_load(sid):
    try:
        with open(swarm_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _state_path(sid):
    return os.path.join(CTX_DIR, "%s.state.json" % sid)


def state_load(sid):
    """Session flags set by the hooks. A separate file from the metrics: the status line
    rewrites its own file every few seconds, and a flag placed there by a hook was lost on
    the very first rewrite."""
    try:
        with open(_state_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def state_save(sid, patch):
    os.makedirs(CTX_DIR, exist_ok=True)
    d = state_load(sid)
    d.update(patch)
    tmp = _state_path(sid) + ".tmp-%d" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    _replace(tmp, _state_path(sid))
    return d


def from_transcript(path):
    """Context size = the usage fields of the last NON-sidechain assistant record.

    input + cache_creation + cache_read is exactly what went into the model on the
    last call, that is, the current fill of the window.
    """
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            chunk = min(size, 400000)
            f.seek(size - chunk)
            lines = f.read().decode("utf-8", "replace").splitlines()
    except Exception:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line.startswith("{") or '"usage"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant" or d.get("isSidechain"):
            continue
        u = (d.get("message") or {}).get("usage") or {}
        used = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                + u.get("cache_read_input_tokens", 0))
        if used:
            return {"used": used, "model": (d.get("message") or {}).get("model", "")}
    return None


def usage(sid, transcript_path=None):
    """Current fill: (pct, used, window, source). None — cannot be determined."""
    c = cfg()
    d = load(sid)
    fresh = d.get("ts") and (time.time() - d["ts"]) < c["stale_sec"]
    if fresh and d.get("used") and d.get("size"):
        return d["used"] * 100.0 / d["size"], d["used"], d["size"], "statusline"
    t = from_transcript(transcript_path)
    if t:
        win = d.get("size") or int(os.environ.get("CLAUDE_CTX_WINDOW", 0)) or c["fallback_window"]
        return t["used"] * 100.0 / win, t["used"], win, "transcript"
    return None


def fmt(used, size):
    return "%dk/%dk" % (round(used / 1000.0), round(size / 1000.0))


PANEL_FLAG = os.path.join(CTX_DIR, "panel")


def panel_on(seconds=None):
    """The panel is unfolded if the flag was touched recently. A file instead of state in
    memory: a hook touches it, the status line reads it — these are different processes."""
    try:
        left = (cfg()["panel_sec"] if seconds is None else seconds) - (time.time() - os.path.getmtime(PANEL_FLAG))
        return left > 0
    except OSError:
        return False


def panel_toggle():
    os.makedirs(CTX_DIR, exist_ok=True)
    if panel_on():
        try:
            os.remove(PANEL_FLAG)
        except OSError:
            pass
        return False
    open(PANEL_FLAG, "w").close()
    return True


def event(kind, sid, pct, cwd="", extra=None):
    """A watchdog event into ~/.claude/kit/events.jsonl. Without this trail a crooked wording
    in a skill pushes in the wrong direction for years, and the author never learns of it."""
    rec = {"ts": time.time(), "kind": kind, "sid": sid, "pct": round(pct, 1), "cwd": cwd}
    if extra:
        rec.update(extra)
    try:
        p = os.path.join(HOME, ".claude", "kit", "events.jsonl")
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def events(limit=200):
    p = os.path.join(HOME, ".claude", "kit", "events.jsonl")
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8", errors="replace") as f:
        for line in f.readlines()[-limit:]:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def console():
    """Every name this terminal answers to — an identity that SURVIVES `/clear`.

    `/clear` resets the conversation inside the same `claude` process; it does not restart it. The
    process exports its own identity to everything it spawns — hooks and shells alike — so a
    closing and the intake that follows it in the same window agree here, while a second window
    does not.

    BOTH NAMES, NOT THE BETTER ONE. The socket is per-process and never reused, but it belongs to a
    subsystem that can be switched off while the process runs — a closing would then be recorded
    under one name and the intake would look for another, and the whole mechanism would fall back
    to asking without a word about why. The pid is always exported and never disappears, but the
    operating system reuses pids. Neither alone is enough; agreeing on EITHER is.

    Empty when neither exists (another host, an older build). Everything below then falls back to
    what it did before: the directory filters, and ambiguity goes to the author.
    """
    out = []
    s = os.path.basename(os.environ.get("CLAUDE_CODE_MESSAGING_SOCKET") or "")
    if s:
        out.append(s)
    pid = os.environ.get("CLAUDE_PID") or ""
    if pid:
        out.append("pid:" + pid)
    return out


def _names(v):
    return [v] if isinstance(v, str) and v else [x for x in (v or []) if x]


def same_console(rec, me):
    """Does a recorded closing belong to the terminal `me`.

    THE STRONG NAME OVERRULES THE WEAK ONE. The socket is one per process and never reused; the pid
    always exists but the system hands it out again. Agreement on either used to be enough, which
    made the whole thing exactly as trustworthy as its weakest name: a recycled pid matched a
    stranger's closing and handed it over without a question. So when BOTH sides name a socket and
    the sockets differ, these are different terminals whatever the pid says. The pid decides only
    where a socket is missing on one of the sides.
    """
    was, mine = _names(rec.get("console")), _names(me)
    ws = [x for x in was if not x.startswith("pid:")]
    ms = [x for x in mine if not x.startswith("pid:")]
    if ws and ms:
        return bool(set(ws) & set(ms))
    return bool(set(was) & set(mine))


def marked(rec):
    """Was this closing attributed to a terminal at all. An unmarked one is legacy, not foreign."""
    c = rec.get("console")
    return bool(c)


def under(closed_cwd, cwd):
    """Was the closed work sitting in THIS console's tree — at its root or deeper.

    ONE-DIRECTIONAL ON PURPOSE. It used to accept the ancestor direction too, and that gave the
    directory back the deciding vote it had just been stripped of: a work closed in the home
    directory matched every project underneath it, and any session started there within the half
    hour was told, with no clarifying questions, to open it. The other direction — the console
    reopened deeper than the work closed — loses an invitation at worst, and a missing invitation
    is the safe failure: the agent asks. A wrong one is silent.
    """
    if not closed_cwd or not cwd:
        return False
    a = os.path.normcase(os.path.abspath(closed_cwd))
    b = os.path.normcase(os.path.abspath(cwd))
    return a == b or a.startswith(b + os.sep)


def _work_key(e):
    """What makes two closings the same work. Empty fields are NOT a match: two closings that
    both named nothing used to collapse into one, the ambiguity branch never fired, and the agent
    was sent to find a handoff by directory — the very incident this is here to prevent."""
    s, h = (e.get("stream") or "").strip(), (e.get("handoff") or "").strip()
    if not s and not h:
        return ("sid", e.get("sid") or id(e))
    return (s.lower(), os.path.normcase(h))


def closed_works(cwd, within=None, limit=2000):
    """Works closed in this console recently: one entry per distinct work, newest last.

    THE KEY OF A WORK IS ITS HANDOFF, NOT THE DIRECTORY. A console can host two unrelated
    streams at once, and it did: two sessions closed in the same directory a minute apart, the
    pick was `closed[-1]` by time, and the intake silently took the wrong work and presented a
    confident gate on it. The directory stays as the filter for "this console" and never decides
    WHICH work was closed — when more than one answers, the ambiguity is surfaced, not guessed.

    The trail is read wide: the window here is TIME, and a swarm of agents writes nudges and
    thresholds fast enough to push a closing out of a short tail — after which the next session
    is told nothing at all.

    Within ONE terminal the last closing wins and the earlier ones are not even shown: they have
    already been continued by the sessions that followed them there. Freshness never chooses
    BETWEEN terminals — that is what once handed an agent someone else's work.
    """
    now = time.time()
    within = cfg()["handoff_sec"] if within is None else within
    me = console()
    raw = []
    for e in events(limit):
        if e.get("kind") != "done" or (now - e.get("ts", 0)) >= within:
            continue
        if not under(e.get("cwd"), cwd):
            continue
        raw.append(e)
    # THE TERMINAL FILTERS BEFORE ANYTHING ELSE IS COLLAPSED. Deduplicating first would let a later
    # closing of the same work from ANOTHER window erase my own record of it, and my window would
    # then be offered its previous work instead.
    if me:
        mine = [e for e in raw if same_console(e, me)]
        # A closing from another terminal is never handed over silently — but it is not thrown away
        # either. Dropping it meant that restarting the terminal (a reboot, a crash, simply closing
        # the window) left the next session with no stream and no path at all, which is the exact
        # failure the twelve-hour window exists to prevent: the process is new, so nothing matches,
        # and a work closed an hour ago became unreachable. It stays a candidate and goes to the
        # author as a question — `pending` below refuses to call a foreign closing an exact match.
        if mine:
            raw = mine
    out = []
    for e in raw:
        k = _work_key(e)
        out = [c for c in out if _work_key(c) != k]
        out.append(e)
    # THE TERMINAL IS THE UNIT, AND INSIDE IT TIME ORDERS. Freshness must never choose BETWEEN
    # windows — that is what once handed an agent someone else's work. Within one window there is
    # nothing to choose: the session that just closed there is the one being continued, and the
    # earlier closings in it have already been continued by the sessions that followed them.
    #
    # The question to the author is not the design, it is the fallback: it stands for the case
    # where the terminal cannot be identified at all.
    if me and out and same_console(out[-1], me):
        return out[-1:]
    return out


def open_arg(work):
    """What `open` is handed: the stream AND the path to its handoff.

    A name alone is not enough. `open` looks for the handoff through the CURRENT project's
    `.claude/ritual.md`, so a work whose files lie outside it — the kit develops itself exactly
    that way — is unreachable by name: the agent would have to guess the path. Empty means the
    closing recorded neither, and then the agent has to find the handoff and say where it was.
    """
    s, h = (work.get("stream") or "").strip(), (work.get("handoff") or "").strip()
    if s and h:
        return "%s — handoff: %s" % (s, h)
    return s or (("handoff: %s" % h) if h else "")


def pending(works, cwd=""):
    """What the intake is handed. One work closed EXACTLY here — its stream and the path to its
    handoff; anything else — the list, because which work is being continued is then NOT derivable
    and guessing it is how an agent once got handed someone else's and presented a gate on it.

    THE TERMINAL OUTRANKS THE DIRECTORY. A closing of this same terminal is handed over whatever
    the directory says — an agent does `cd`, a window is opened deeper, and the terminal already
    answers the question the directory was standing in for. A closing carrying ANOTHER terminal is
    never exact, however well the directory matches. With no terminal known at all, the directory
    decides as before: exact is handed over, a subdirectory costs one line of a question.
    """
    me = console()
    exact = []
    for w in works:
        if me and marked(w):
            if same_console(w, me):
                exact.append(w)
            continue          # somebody else's terminal: never exact, always a question
        if cwd and (os.path.normcase(os.path.abspath(w.get("cwd") or "."))
                    == os.path.normcase(os.path.abspath(cwd))):
            exact.append(w)
    if len(works) == 1 and (not cwd or exact):
        return {"arg": open_arg(works[0]), "choices": []}
    return {"arg": "", "choices": [open_arg(w) or "(the closing named nothing)" for w in works]}


def intake_body(pend):
    """The instruction itself, in the three cases that actually occur.

    IT LIVES IN ONE PLACE. The branching was written twice, once per hook, and the two had
    already drifted: the copy that reaches the agent for certain — the one wedged into the first
    prompt — had lost the warning that explains WHY freshness must not decide. Each hook frames
    this with its own preamble; the fork itself is not theirs to keep.
    """
    if not isinstance(pend, dict):                       # sessions from before the split
        pend = {"arg": pend if isinstance(pend, str) else "", "choices": []}
    if pend.get("choices"):
        many = len(pend["choices"]) > 1
        return ("%s: %s. Which work is being continued does not follow from the directory — ask "
                "the author in one line BEFORE the intake and open the one he names. Do not "
                "decide it by freshness or by proximity: deciding it once handed an agent someone "
                "else's work, and every link of the ritual reported success. Ask first; the gate "
                "comes after."
                % ("MORE THAN ONE work was closed in this console" if many else
                   "A work was closed NEARBY but not in this exact directory",
                   "; ".join('"%s"' % c for c in pend["choices"])))
    if pend.get("arg"):
        where = ("take the handoff AT THE PATH NAMED THERE" if "handoff:" in pend["arg"]
                 else "the closing named the stream but not where its handoff lies — find it and "
                      "say in the gate what you opened")
        return ('Run Skill(skill="open") with the argument "%s" right now, with no clarifying '
                'questions: %s.' % (pend["arg"], where))
    return ('Run Skill(skill="open") right now, with no clarifying questions. The closing recorded '
            'neither the stream nor the path to the handoff, so find the handoff yourself and NAME '
            'IT in the gate — and do not assume it is the one this directory\'s ritual points at: '
            'the work may live outside the directory the console stands in.')


def shield(fn, hook, sid="", cwd=""):
    """Run a hook body so that its failure costs only itself.

    A HOOK THAT RAISES IS SILENT: the console shows nothing, and the agent loses whatever that
    hook was supposed to give it — its session id, the rules of the mode, the intake invitation,
    or the whole watchdog. A recorded failure and a live session beat both being lost, so the
    traceback goes to stderr and a `hook_error` lands in the trail where kit-review will see it.
    """
    try:
        return fn()
    except SystemExit:
        raise
    except Exception:
        import traceback
        try:
            # ONE ENTRY PER HOOK PER FIVE MINUTES. The status line runs every few seconds, so a
            # broken one wrote twelve records a minute — some seventeen thousand a day — and the
            # trail, `stats` and `log` filled up with them until nothing else was visible. The
            # failure must be recorded, not amplified: the tenth identical line says nothing the
            # first did not.
            stamp = os.path.join(CTX_DIR, "err-%s" % hook)
            fresh = os.path.exists(stamp) and (time.time() - os.path.getmtime(stamp)) < 300
            if not fresh:
                # THE STAMP MOVES ONLY WHEN A RECORD IS WRITTEN. Touching it on every failure —
                # including the suppressed ones — turned "once per five minutes" into "once per
                # five minutes of SILENCE": a hook failing every five seconds, which is exactly
                # what the status line does, recorded once and then never again.
                os.makedirs(CTX_DIR, exist_ok=True)
                open(stamp, "w").close()
                # the traceback is throttled with the record, and for the same reason: a status
                # line failing every few seconds would otherwise pour tracebacks into the terminal
                sys.stderr.write(traceback.format_exc())
                exc = sys.exc_info()[1]
                event("hook_error", sid, 0, cwd,
                      {"hook": hook, "error": "%s: %s" % (type(exc).__name__, exc)[:200]})
        except Exception:
            pass
        return None


def bar(pct, width=14, pace=None, cursor="│"):
    """The spend bar. `pace` is the share of the window until the reset that has already passed;
    the cursor is drawn on top of the bar in its own character so that it blends neither into the
    spend nor into the background — pass the escape codes around it as `cursor`.

    ONE IMPLEMENTATION. There were three, with different widths, different cursor characters and
    different signatures, in a kit that ships "two units incomplete without each other — merge
    them" as a rule it installs into every agent's instructions.
    """
    n = max(0, min(width, int(round(pct * width / 100.0))))
    cells = ["█"] * n + ["░"] * (width - n)
    if pace is not None:
        i = max(0, min(width - 1, int(pace * width / 100.0)))
        cells[i] = cursor
    return "".join(cells)


def eta(sec, coarse=False):
    """How much is left until a reset. The weekly window needs no hours — it is thought of in days,
    and the extra characters make the terminal truncate the line."""
    if sec <= 0:
        return "0m"
    d, h, m = int(sec // 86400), int(sec % 86400 // 3600), int(sec % 3600 // 60)
    if d:
        return "%dd" % d if coarse else "%dd%dh" % (d, h)
    return "%dh%02dm" % (h, m) if h else "%dm" % m


# The subscription windows, in seconds. One place: the CLI and the status line each had their own.
LIMIT_WINDOW = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}


def stdin_json():
    """stdin always arrives in UTF-8; the local Windows code page has nothing to do with it."""
    try:
        raw = sys.stdin.buffer.read()
    except Exception:
        raw = (sys.stdin.read() or "").encode("utf-8", "replace")
    try:
        return json.loads(raw.decode("utf-8", "replace") or "{}")
    except Exception:
        return {}


def utf8_io():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
