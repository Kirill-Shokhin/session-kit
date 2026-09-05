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
    "stale_sec": 600,     # older than this a ctx file is not a live reading
    "hide_sec": 120,      # older than this reading a session is considered closed
    "panel_sec": 15,      # how many seconds the panel stays unfolded
    "panel_on_prompt": True,  # and it unfolds by itself after every message
    "fallback_window": 200000,
    # The switch: autonomous — the agent decides on its own and brings only what passed the
    # critics; stepwise — the human verifies every step (the mode for scarce limits).
    "mode": "autonomous",
}


def cfg():
    d = dict(DEFAULTS)
    try:
        with open(CFG_PATH, encoding="utf-8") as f:
            d.update(json.load(f))
    except Exception:
        pass
    return d


def _path(sid):
    return os.path.join(CTX_DIR, "%s.json" % sid)


def load(sid):
    try:
        with open(_path(sid), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(sid, patch):
    os.makedirs(CTX_DIR, exist_ok=True)
    d = load(sid)
    d.update(patch)
    d["sid"] = sid
    tmp = _path(sid) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, _path(sid))
    return d


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
        # A session started before the split keeps its flags together with the metrics.
        # Without this, an already closed session would be told to close a second time.
        old = load(sid)
        return {k: old[k] for k in ("state", "verified", "verified_at", "gate_at", "blocked_at",
                                    "soft_warned", "nudged_at", "recheck_asked", "pending_open",
                                    "compacted", "stream") if k in old}


def state_save(sid, patch):
    os.makedirs(CTX_DIR, exist_ok=True)
    d = state_load(sid)
    d.update(patch)
    tmp = _state_path(sid) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, _state_path(sid))
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
    in a skill pushes in the wrong direction for years, and the human never learns of it."""
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
    with open(p, encoding="utf-8") as f:
        for line in f.readlines()[-limit:]:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


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
