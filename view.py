# -*- coding: utf-8 -*-
"""How the swarm state is drawn. A shared layer for the CLI (`bin/ctx.py`), for the panel in
the status line and for the `ctx.py` subcommands."""
import glob, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctxlib  # noqa: E402

R, DIM, RED, YEL, GRN, CYA = "\033[0m", "\033[2m", "\033[31m", "\033[33m", "\033[32m", "\033[36m"
KIND = {"nudge": "nudge", "soft": "soft threshold", "block": "stop", "done": "closed"}




def age(ts):
    s = int(time.time() - (ts or 0))
    return "%ds" % s if s < 60 else ("%dm" % (s // 60) if s < 3600 else "%dh" % (s // 3600))




def rows():
    c = ctxlib.cfg()
    out = []
    # `.state.json` — a file left by a session whose id was empty — is not matched by `*.json`:
    # glob does not match a leading dot, and such a file used to stay there forever
    for p in (glob.glob(os.path.join(ctxlib.CTX_DIR, "*.json"))
              + glob.glob(os.path.join(ctxlib.CTX_DIR, ".*.json"))
              + glob.glob(os.path.join(ctxlib.CTX_DIR, "err-*"))
              + glob.glob(os.path.join(ctxlib.CTX_DIR, "*.tmp-*"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        # Liveness is judged by the freshness of the reading. The status line ticks every
        # refreshInterval seconds, so a live session updates the file even while idle and a
        # closed one stops. Judging by the process is impossible: the status line is started by
        # an intermediate shell, and its id is dead by the time of the write — that is how every
        # session used to look dead.
        if d.get("size") and (time.time() - (d.get("ts") or 0)) < c["hide_sec"]:
            st = ctxlib.state_load(d.get("sid") or "")   # flags live in their own file
            st.pop("cwd", None)          # the project root comes from the metrics, not from a hook
            d.update(st)
            out.append(d)
    out.sort(key=lambda d: -(d.get("pct") or 0))
    return out, c


def limits():
    """The subscription limits live in the last status line snapshot: the hook never gets them."""
    out, _ = rows()
    fresh = sorted([d for d in out if d.get("limits")], key=lambda d: -(d.get("ts") or 0))
    if not fresh:
        return ""
    rl, seen = fresh[0]["limits"], fresh[0].get("ts", 0)
    parts = []
    for key, name in (("five_hour", "5h"), ("seven_day", "7d"), ("spend_limit", "$")):
        w = rl.get(key)
        if not w or w.get("used_percentage") is None:
            continue
        pct, resets = w["used_percentage"], w.get("resets_at")
        pace, tail = None, ""
        if resets:
            left = resets - time.time()
            full = ctxlib.LIMIT_WINDOW.get(key, 0)
            if full:
                pace = max(0.0, min(100.0, (full - left) * 100.0 / full))
            tail = DIM + "·" + ctxlib.eta(left) + R
        if pace is None:
            col = RED if pct >= 90 else (YEL if pct >= 70 else GRN)
        else:
            over = pct - pace
            col = RED if over >= 20 else (YEL if over >= 5 else CYA)
        parts.append("%s%s %s%s %d%%%s%s" % (DIM, name, col, ctxlib.bar(pct, 10, pace), round(pct), R, tail))
    if not parts:
        return ""
    return "  ".join(parts) + DIM + "   (taken %s ago)" % age(seen) + R


def table():
    out, c = rows()
    if not out:
        return "no active sessions (the status line has not drawn even once yet)"
    lines = []
    for d in out:
        pct = d.get("pct") or 0
        stale = (time.time() - (d.get("ts") or 0)) > c["stale_sec"]
        col = RED if pct >= c["hard_pct"] else (YEL if pct >= c["soft_pct"] else GRN)
        state = d.get("state", "live")
        tag = GRN + "closed" + R if state == "closed" else ""
        if d.get("compacted"):
            tag = RED + "COMPACTED" + R
        if stale and state != "closed":
            tag = tag or DIM + "asleep" + R
        lines.append("%-22s %s%s %3d%%%s %s%-9s%s %s %s" % (
            os.path.basename((d.get("cwd") or "?").rstrip("/\\"))[:22],
            col, ctxlib.bar(pct, 16), round(pct), R,
            DIM, ctxlib.fmt(d.get("used", 0), d["size"]), R,
            DIM + age(d.get("ts")) + R, tag))
        sw = ctxlib.swarm_load(d.get("sid") or "")
        # the snapshot ages on its own: without this a finished swarm was drawn as running, and a
        # fallback to the metrics file made an empty swarm impossible to express at all
        fresh_sw = sw.get("swarm_ts") and (time.time() - sw["swarm_ts"]) < ctxlib.cfg()["hide_sec"]
        for t in ((sw.get("swarm") or []) if fresh_sw else []):
            sp = t.get("pct") or 0
            sc = RED if sp >= c["hard_pct"] else (YEL if sp >= c["soft_pct"] else GRN)
            lines.append("   %s└ %-17s%s %s%s %3d%%%s %s" % (
                DIM, t.get("name", "")[:17], R, sc, ctxlib.bar(sp, 10), round(sp), R,
                DIM + (t.get("status") or "") + R))
    lim = limits()
    if lim:
        lines += ["", lim]
    return "\n".join(lines)


def log(n=40):
    ev = ctxlib.events(2000)[-n:]
    if not ev:
        return "no events"
    lines = []
    for e in ev:
        col = {"block": RED, "soft": YEL, "done": GRN}.get(e.get("kind"), DIM)
        lines.append("%s  %s%-13s%s %3d%%  %-18s %s" % (
            time.strftime("%d.%m %H:%M", time.localtime(e.get("ts", 0))),
            col, KIND.get(e.get("kind"), e.get("kind")), R, round(e.get("pct", 0)),
            os.path.basename((e.get("cwd") or "").rstrip("/\\"))[:18],
            # the stream is shown: two closings in one directory look identical without it, and
            # that is exactly what kit-review has to be able to tell apart in the trail
            DIM + (e.get("sid") or "")[:8] + (" " + e["stream"] if e.get("stream") else "") + R))
    return "\n".join(lines)


def stats():
    """The summary answers one question: is the watchdog working as intended. A stop that was
    not followed by a closing is a defect in the wording, not an accident."""
    ev = ctxlib.events(5000)
    if not ev:
        return "no events"
    broke = [e for e in ev if e.get("kind") == "hook_error"]
    by_sid, cnt = {}, {}
    for e in ev:
        k = e.get("kind")
        cnt[k] = cnt.get(k, 0) + 1
        by_sid.setdefault(e.get("sid"), set()).add(k)
    unclosed = [s for s, ks in by_sid.items() if "block" in ks and "done" not in ks]
    ungated = [s for s, ks in by_sid.items() if "verify_gate" in ks and "verify" not in ks]
    clean = [s for s, ks in by_sid.items() if "done" in ks and "block" not in ks]
    out = ["nudges %d · soft thresholds %d · stops %d · closings %d · critic gates %d"
           % (cnt.get("nudge", 0), cnt.get("soft", 0), cnt.get("block", 0), cnt.get("done", 0),
              cnt.get("verify_gate", 0)),
           "closed before the stop: %s%d%s (the watchdog worked as a reminder, not as a stop)"
           % (GRN, len(clean), R)]
    if unclosed:
        out.append("%sstops without a closing: %d%s — %s"
                   % (RED, len(unclosed), R, ", ".join(s[:8] for s in unclosed[:6])))
        out.append(DIM + "  defect: the watchdog's instruction did not lead to the ritual. "
                         "See FEEDBACK.md and fix the wording (the kit-review skill)." + R)
    if ungated:
        out.append("%scritic gates with no check counted: %d%s — %s"
                   % (RED, len(ungated), R, ", ".join(s[:8] for s in ungated[:6])))
        out.append(DIM + "  the agent declared readiness but never went to the critics." + R)
    fb = os.path.join(os.path.expanduser("~"), ".claude", "kit", "FEEDBACK.md")
    if os.path.exists(fb):
        n, code = 0, False
        for line in open(fb, encoding="utf-8"):    # a format sample, not an entry
            if line.startswith("```"):
                code = not code
            elif line.startswith("## ") and not code and not line.startswith("## <"):
                n += 1
        if n:
            out.append("entries in FEEDBACK.md: %d (go through them with kit-review)" % n)
    cut = time.time() - 86400
    dn = [e for e in ev if e.get("kind") == "done" and e.get("ts", 0) >= cut]
    if dn:
        att = sum(1 for e in dn if e.get("console"))
        out.append("closings attributed to a terminal: %d of %d%s" % (
            att, len(dn), "" if att == len(dn) else
            " — the rest fall back to asking which work is continued"))
    if broke:
        # a hook that raises is silent; the shield keeps the session alive but the failure has to
        # surface SOMEWHERE, and this is the place built for exactly that
        out.append(RED + "hooks that failed: %d (%s)" % (
            len(broke), ", ".join(sorted({e.get("hook", "?") for e in broke}))) + R)
    return "\n".join(out)


def clean():
    n = 0
    # the dotted variant too: a session whose id was empty left `.state.json`, and `*.json` never
    # matched it — the file would have sat there forever
    for p in (glob.glob(os.path.join(ctxlib.CTX_DIR, "*.json"))
              + glob.glob(os.path.join(ctxlib.CTX_DIR, ".*.json"))):
        if time.time() - os.path.getmtime(p) > 86400:
            os.remove(p)
            n += 1
    return "files removed: %d" % n
