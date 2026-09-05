# -*- coding: utf-8 -*-
"""The status line.

On the left — this session: the project, the branch, the model, the fill of the window. On the
right — the subscription limits: the five-hour one and the weekly one. Each limit carries a pace
cursor in its bar — the share of the window until the reset that has already passed. Spend to the
left of the cursor means you are on schedule; to the right — that you will burn the limit out
before it resets.

It also drops a snapshot of the window into ~/.claude/ctx/<sid>.json — the watchdog and the swarm
monitor take it from there.
"""
import os, re, sys, time

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

R, DIM, RED, YEL, GRN, CYA, MAG = ("\033[0m", "\033[2m", "\033[31m", "\033[33m",
                                   "\033[32m", "\033[36m", "\033[35m")
ANSI = re.compile(r"\033\[[0-9;]*m")
WINDOW = {"five_hour": 5 * 3600, "seven_day": 7 * 86400}


def vlen(s):
    return len(ANSI.sub("", s))


def branch(d):
    try:
        head = open(os.path.join(d, ".git", "HEAD"), encoding="utf-8").read().strip()
        return head.rsplit("/", 1)[-1] if head.startswith("ref:") else head[:7]
    except Exception:
        return ""


CUR = "[97m"      # the pace cursor is drawn in bright white: it has to be readable both on
                      # the filled part of the bar and on the empty one, or its place is unclear


def bar(pct, width=14, pace=None, col=""):
    """The spend bar. `pace` is the share of the window until the reset that has already passed:
    the cursor is put on top of the bar in its own character and color, so that it blends neither
    into the spend nor into the background."""
    n = max(0, min(width, int(round(pct * width / 100.0))))
    cells = ["█"] * n + ["░"] * (width - n)
    if pace is not None:
        i = max(0, min(width - 1, int(pace * width / 100.0)))
        cells[i] = CUR + "│" + (col or R)
    return "".join(cells)


def left(d, c):
    cw = d.get("context_window") or {}
    ws = d.get("workspace") or {}
    # For display — the current directory; for matching sessions up — the project ROOT:
    # current_dir slides into a subfolder as soon as the agent does a cd, and then a closed
    # session and a new one look like different pieces of work.
    cur = ws.get("current_dir") or d.get("cwd") or ""
    root = ws.get("project_dir") or cur
    used = (cw.get("total_input_tokens") or 0) + (cw.get("total_output_tokens") or 0)
    size = cw.get("context_window_size") or 0
    pct = cw.get("used_percentage")
    if pct is None and size:
        pct = used * 100.0 / size
    pct = float(pct or 0)

    sid = d.get("session_id", "")
    if sid and size:
        patch = {"pct": round(pct, 1), "used": used, "size": size, "cwd": root, "dir": cur,
                 "model": (d.get("model") or {}).get("display_name", ""), "ts": time.time()}
        if d.get("rate_limits"):        # hooks never get the limits, and the panel has to show them
            patch["limits"] = d["rate_limits"]
        ctxlib.save(sid, patch)

    col = RED if pct >= c["hard_pct"] else (YEL if pct >= c["soft_pct"] else GRN)
    parts = [CYA + os.path.basename(cur.rstrip("/\\")) + R]
    b = branch(cur)
    if b:
        parts.append(DIM + b + R)
    mdl = (d.get("model") or {}).get("display_name")
    if mdl:
        parts.append(DIM + mdl + R)
    parts.append("%s%s %d%%%s" % (col, bar(pct), round(pct), R))
    if size:
        parts.append(DIM + ctxlib.fmt(used, size) + R)
    # A command is shown in the line ONLY when an action is required from the human. The ritual
    # and the journal are kept by the agent on the watchdog's instructions — offering them to the
    # human would be lying to him that nothing happens until he presses something.
    st = ctxlib.state_load(sid) if sid else {}
    if st.get("state") == "closed":
        parts.append(GRN + "closed → /clear" + R)
    elif pct >= c["hard_pct"]:
        parts.append(RED + "closing" + R)
    return "  ".join(parts)


def left_short(d, c):
    cw = d.get("context_window") or {}
    pct = float(cw.get("used_percentage") or 0)
    col = RED if pct >= c["hard_pct"] else (YEL if pct >= c["soft_pct"] else GRN)
    cur = (d.get("workspace") or {}).get("current_dir") or ""
    return "%s  %s%s %d%%%s" % (CYA + os.path.basename(cur.rstrip("/\\"))[:12] + R,
                                col, bar(pct, 8), round(pct), R)


def left_ctx_only(d, c):
    pct = float((d.get("context_window") or {}).get("used_percentage") or 0)
    col = RED if pct >= c["hard_pct"] else (YEL if pct >= c["soft_pct"] else GRN)
    return "%s%d%%%s" % (col, round(pct), R)


def eta(sec, coarse=False):
    """How much is left until the reset. The weekly window needs no hours: it is thought of in
    days anyway, and the extra characters make the terminal truncate the line."""
    if sec <= 0:
        return "0m"
    d, h, m = int(sec // 86400), int(sec % 86400 // 3600), int(sec % 3600 // 60)
    if d:
        return "%dd" % d if coarse else "%dd%dh" % (d, h)
    return "%dh%02dm" % (h, m) if h else "%dm" % m


def limit(label, w, width=8):
    """A limit bar with the pace cursor. The color follows how far the spend lags the clock."""
    pct = w.get("used_percentage")
    if pct is None:
        return None
    resets = w.get("resets_at")
    pace = None
    tail = ""
    if resets:
        left_s = resets - time.time()
        full = WINDOW.get(label[1], 0)
        if full:
            pace = max(0.0, min(100.0, (full - left_s) * 100.0 / full))
        tail = DIM + "·" + eta(left_s, coarse=(label[1] == "seven_day")) + R
    if pace is None:
        col = RED if pct >= 90 else (YEL if pct >= 70 else GRN)
    else:                       # overtaking the cursor means the limit runs out before the reset
        over = pct - pace
        col = RED if over >= 20 else (YEL if over >= 5 else CYA)
    return "%s%s %s%s %d%%%s%s" % (DIM, label[0], col, bar(pct, width, pace, col),
                                   round(pct), R, tail)


def right(d):
    rl = d.get("rate_limits") or {}
    out = []
    for key, name in (("five_hour", "5h"), ("seven_day", "7d"), ("spend_limit", "$")):
        w = rl.get(key)
        if w:
            s = limit((name, key), w)
            if s:
                out.append(s)
    return "  ".join(out)


def swarm_items(c, sid):
    """The live sessions other than one's own: the name and the percentage, nothing else."""
    import view
    out = []
    for x in view.rows()[0]:
        if x.get("sid") == sid:
            continue
        pct = x.get("pct") or 0
        col = RED if pct >= c["hard_pct"] else (YEL if pct >= c["soft_pct"] else GRN)
        mark = "!" if x.get("compacted") else (
            "~" if (time.time() - (x.get("ts") or 0)) > c["stale_sec"] else "")
        out.append("%s%s %d%%%s%s" % (col, os.path.basename((x.get("cwd") or "?")
                   .rstrip("/\\"))[:14], round(pct), mark, R))
    return out


def alarm():
    """One mark instead of a separate summary: a stop that was not followed by a closing, and
    the friction entries that have piled up — the only things worth looking at the events by
    hand for."""
    try:
        ev = ctxlib.events(500)
    except Exception:
        return ""
    by = {}
    for e in ev:
        by.setdefault(e.get("sid"), set()).add(e.get("kind"))
    stuck = sum(1 for ks in by.values() if "block" in ks and "done" not in ks)
    return RED + " !%d" % stuck + R if stuck else ""


def swarm_line(items, hidden=0):
    if not items:
        return ""
    line = DIM + "swarm: " + R + (DIM + " · " + R).join(items)
    return line + (DIM + " +%d" % hidden + R if hidden else "") + alarm()


def main():
    ctxlib.utf8_io()
    d = ctxlib.stdin_json()
    c = ctxlib.cfg()
    cols = int(os.environ.get("COLUMNS") or 0)
    l, r = left(d, c), right(d)
    items = swarm_items(c, d.get("session_id")) if ctxlib.panel_on() else []

    # Layout: own session on the left, then the swarm, the limits on the right. The order of
    # shrinking when there is not enough room is the reverse of importance: first the swarm is cut,
    # then one's own part is shortened, the limits — never.
    def compose(left_part, swarm):
        mid = left_part + ("   " + swarm if swarm else "")
        if not r:
            return mid
        if not cols:
            return mid + "   " + r
        gap = cols - vlen(mid) - vlen(r) - 6     # slack against the terminal truncating the line
        return mid + " " * gap + r if gap >= 2 else None

    for n in range(len(items), -1, -1):
        line = compose(l, swarm_line(items[:n], len(items) - n))
        if line is not None:
            sys.stdout.write(line)
            return
    for short in (left_short(d, c), left_ctx_only(d, c)):
        line = compose(short, swarm_line(items[:1], max(0, len(items) - 1)) if items else "")
        if line is not None:
            sys.stdout.write(line)
            return
    sys.stdout.write(r or l)


main()
