# -*- coding: utf-8 -*-
"""Installing the kit on a machine. Idempotent: a repeated run updates.

  python install.py                 install or update
  python install.py --update        pull the fresh version from the repository and reinstall
  python install.py --publish "..." commit your own edits and push them to the repository
  python install.py --dry-run       show what will be done
  python install.py --soft 60 --hard 75   the context window watchdog thresholds

What it does: puts the skills into ~/.claude/skills and the commands into ~/.claude/commands,
merges the status line and five hooks into ~/.claude/settings.json, disables auto-compaction.
Existing settings are preserved, the file is backed up before it is edited.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
CLAUDE = os.path.join(HOME, ".claude")
KIT = os.path.join(CLAUDE, "kit")
PY = sys.executable
MARK = os.path.join("kit", "hooks")  # by this substring we recognize our own hooks on update


def cmd(rel):
    return '"%s" "%s"' % (PY, os.path.join(KIT, *rel.split("/")))


def hook(event, script, matcher=None):
    h = {"hooks": [{"type": "command", "command": cmd("hooks/" + script), "timeout": 20}]}
    if matcher:
        h["matcher"] = matcher
    return event, h


def merge_hooks(cur, event, entry):
    lst = cur.setdefault("hooks", {}).setdefault(event, [])
    new_cmd = entry["hooks"][0]["command"]
    script = new_cmd.rsplit(os.sep, 1)[-1]
    for i, e in enumerate(lst):
        for hh in e.get("hooks", []):
            c = hh.get("command", "")
            if MARK in c and script in c:      # our own hook — update it in place
                lst[i] = entry
                return "updated"
    lst.append(entry)
    return "added"


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--update", action="store_true",
                    help="git pull in the kit, then the usual installation")
    ap.add_argument("--publish", metavar="MESSAGE",
                    help="commit the kit's edits and push them to the repository")
    ap.add_argument("--soft", type=int, default=None)
    ap.add_argument("--hard", type=int, default=None)
    a = ap.parse_args()
    log = []

    # 0. synchronization with the repository — the kit lives on several machines
    src = HERE if os.path.exists(os.path.join(HERE, ".git")) else KIT
    if a.update:
        r = subprocess.run(["git", "-C", src, "pull", "--ff-only"], capture_output=True, text=True)
        log.append("update: " + (r.stdout or r.stderr).strip().splitlines()[-1])
        if r.returncode:
            print("\n".join("  " + x for x in log))
            print("\nThe pull failed — sort the repository out and try again.")
            return
    if a.publish:
        subprocess.run(["git", "-C", src, "add", "-A"], check=False)
        msg = a.publish
        r = subprocess.run(["git", "-C", src, "commit", "-m", msg], capture_output=True, text=True)
        log.append("commit: " + (r.stdout or r.stderr).strip().splitlines()[-1])
        r = subprocess.run(["git", "-C", src, "push"], capture_output=True, text=True)
        log.append("push: " + ((r.stdout or r.stderr).strip().splitlines() or ["ok"])[-1])

    # 1. the kit itself into its place
    # Personal files installing from a clone must not wipe. All of them are in .gitignore,
    # so a clone does not carry them — whatever is lost here cannot be restored.
    KEEP = ("config.json", "events.jsonl", "FEEDBACK.md", "journal", "examples",
            "legacy", "skills-local", os.path.join("commands", "client-doc.md"))
    if os.path.abspath(HERE) != os.path.abspath(KIT):
        log.append("kit → %s" % KIT)
        if not a.dry_run:
            # The stash goes OUTSIDE KIT: the directory is removed whole, and anything put
            # inside it is removed with it. That is exactly how the earlier version broke.
            stash_dir = tempfile.mkdtemp(prefix="kit-keep-")
            stashed = []
            try:
                for name in KEEP:
                    src_p = os.path.join(KIT, name)
                    if os.path.exists(src_p):
                        dst_p = os.path.join(stash_dir, name.replace(os.sep, "__"))
                        shutil.move(src_p, dst_p)
                        stashed.append((name, dst_p))
                if os.path.exists(KIT):
                    shutil.rmtree(KIT)
                shutil.copytree(HERE, KIT, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            finally:
                # The return happens even if the installation failed midway: otherwise the
                # personal files stay orphaned in a temp directory and nobody ever learns of it.
                os.makedirs(KIT, exist_ok=True)
                left = []
                for name, tmp in stashed:
                    dst_p = os.path.join(KIT, name)
                    try:
                        os.makedirs(os.path.dirname(dst_p), exist_ok=True)
                        if os.path.exists(dst_p):
                            shutil.rmtree(dst_p) if os.path.isdir(dst_p) else os.remove(dst_p)
                        shutil.move(tmp, dst_p)
                    except OSError:
                        left.append(tmp)
                if left:
                    log.append("COULD NOT RETURN, files are here: " + ", ".join(left))
                else:
                    shutil.rmtree(stash_dir, ignore_errors=True)
                if stashed:
                    log.append("personal kept: " + ", ".join(sorted(n for n, _ in stashed)))

    # 2. skills and commands
    for kind in ("skills", "commands", "skills-local"):
        src = os.path.join(KIT if not a.dry_run else HERE, kind)
        if not os.path.isdir(src):
            continue
        # the personal layer lies on top of the public skills: it is what applies in the work
        dst = os.path.join(CLAUDE, "skills" if kind == "skills-local" else kind)
        for name in sorted(os.listdir(src)):
            s, d = os.path.join(src, name), os.path.join(dst, name)
            if kind == "skills-local" and not os.path.isdir(s):
                continue                      # the layer's explanatory README is not a skill
            log.append("%s/%s" % (kind, name))
            if a.dry_run:
                continue
            os.makedirs(dst, exist_ok=True)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

    # 2.5 the personal glossary: public wording → personal one. It is applied to the INSTALLED
    # skills, so the repository keeps depersonalized text while the work runs in your own language.
    # A glossary instead of copies: a copy falls behind with every edit of the public skill.
    gl = os.path.join(KIT, "skills-local", "glossary.json")
    if os.path.exists(gl) and not a.dry_run:
        pairs = json.load(open(gl, encoding="utf-8"))
        changed = 0
        for dp, _, fns in os.walk(os.path.join(CLAUDE, "skills")):
            for fn in fns:
                if not fn.endswith(".md"):
                    continue
                f = os.path.join(dp, fn)
                t = orig = open(f, encoding="utf-8").read()
                for src_s, dst_s in pairs:
                    t = t.replace(src_s, dst_s)
                if t != orig:
                    open(f, "w", encoding="utf-8", newline="\n").write(t)
                    changed += 1
        log.append("personal glossary: %d pairs, skills touched %d" % (len(pairs), changed))

    # 2.7 the kit's global rules go into ~/.claude/CLAUDE.md between the markers. The file is
    # personal, hence: a backup before editing, a refusal on broken markers, line endings preserved.
    B, E = "<!-- session-kit:rules:start -->", "<!-- session-kit:rules:end -->"
    rules = os.path.join(KIT if not a.dry_run else HERE, "rules", "global.md")
    md = os.path.join(CLAUDE, "CLAUDE.md")
    if os.path.exists(rules):
        nl = chr(10)
        body = open(rules, encoding="utf-8").read().strip()
        note = "<!-- placed by ~/.claude/kit/install.py; edits go to kit/rules/global.md -->"
        block = nl.join([B, note, body, E])
        raw = ""
        if os.path.exists(md):
            with open(md, "rb") as f:
                raw = f.read().decode("utf-8", "replace")
        crlf = raw.count(chr(13) + nl) > raw.count(nl) / 2 if raw else False
        cur_md = raw.replace(chr(13) + nl, nl)
        nb, ne = cur_md.count(B), cur_md.count(E)
        if nb > 1 or ne > 1 or (nb == 1) != (ne == 1) or (nb and cur_md.index(B) > cur_md.index(E)):
            # The markers are broken. A blind replacement by slice would eat everything between
            # them — that is, the human's own rules. We touch nothing and say so out loud.
            log.append("rules NOT updated: the markers in CLAUDE.md are broken, fix them by hand")
        else:
            if nb:
                new_md = cur_md[:cur_md.index(B)] + block + cur_md[cur_md.index(E) + len(E):]
                act = "updated"
            else:
                new_md = (cur_md.rstrip() + nl + nl + block + nl) if cur_md.strip() else block + nl
                act = "added"
            if new_md != cur_md:
                log.append("global rules %s in CLAUDE.md" % act)
                if not a.dry_run:
                    if raw:
                        shutil.copy2(md, md + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
                    out = new_md.replace(nl, chr(13) + nl) if crlf else new_md
                    with open(md, "wb") as f:
                        f.write(out.encode("utf-8"))

    # 3. thresholds and the working friction file (personal: it does not go to the repository)
    cfgp = os.path.join(KIT, "config.json")
    cfg, broken = {}, False
    if os.path.exists(cfgp):
        try:
            cfg = json.load(open(cfgp, encoding="utf-8"))   # mode and thresholds survive install
        except Exception:
            broken = True          # a broken config is no reason to silently reset the settings
    if broken:
        log.append("config.json is unreadable — left as is, the settings are untouched")
    if a.soft is not None:
        cfg["soft_pct"] = a.soft
    if a.hard is not None:
        cfg["hard_pct"] = a.hard
    if broken and (a.soft is not None or a.hard is not None):
        # With the file unwritten, reporting applied thresholds would be a lie: the old ones stay.
        log.append("THRESHOLDS FROM FLAGS NOT APPLIED: config.json is unreadable, fix or delete it")
    elif not broken:
        log.append("thresholds: reminder %d%%, stop %d%%"
                   % (cfg.get("soft_pct", 60), cfg.get("hard_pct", 75)))
    if not a.dry_run and not broken:
        os.makedirs(KIT, exist_ok=True)
        json.dump(cfg, open(cfgp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        fb, tpl = os.path.join(KIT, "FEEDBACK.md"), os.path.join(KIT, "templates", "FEEDBACK.md")
        if not os.path.exists(fb) and os.path.exists(tpl):
            shutil.copy2(tpl, fb)
            log.append("FEEDBACK.md created")

    # 4. settings
    sp = os.path.join(CLAUDE, "settings.json")
    cur = {}
    if os.path.exists(sp):
        cur = json.load(open(sp, encoding="utf-8"))
        if not a.dry_run:
            shutil.copy2(sp, sp + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
    cur["statusLine"] = {"type": "command", "command": cmd("statusline/statusline.py"),
                         "padding": 0, "refreshInterval": 5}   # seconds
    cur["subagentStatusLine"] = {"type": "command", "command": cmd("statusline/subagent.py")}
    # Auto-compaction is disabled. As a session switch it is no good: the window would have to
    # be filled up artificially to reach its threshold, the ritual might not make it in time — and
    # compaction would eat what was not written down, giving exactly the false session all of this
    # was started against. And if the work stopped before the threshold, compaction never comes.
    cur["autoCompactEnabled"] = False
    cur.pop("autoCompactWindow", None)
    WANTED = (hook("Stop", "guard.py"),
                      hook("PreCompact", "precompact.py"),
                      hook("SessionStart", "sessionstart.py", "startup|resume|clear|compact"),
                      hook("SessionEnd", "sessionend.py"),
                      hook("UserPromptSubmit", "panel.py"))
    for ev, entry in WANTED:
        log.append("hook %s %s" % (ev, merge_hooks(cur, ev, entry) if not a.dry_run else "will be added"))
    # commands the kit no longer has are removed from ~/.claude/commands
    cdir = os.path.join(CLAUDE, "commands")
    ksrc = os.path.join(KIT, "commands")
    if os.path.isdir(cdir) and os.path.isdir(ksrc):
        for name in os.listdir(cdir):
            if name.endswith(".md") and not os.path.exists(os.path.join(ksrc, name))                     and name in ("pulse.md",):        # only ours, other people's are left alone
                os.remove(os.path.join(cdir, name))
                log.append("command %s removed" % name)

    # our entries on events the kit no longer uses are taken off: otherwise Claude Code keeps
    # calling the hook on an event it has long stopped being installed for
    mine = {(ev, e["hooks"][0]["command"]) for ev, e in WANTED}
    for ev, lst in list(cur.get("hooks", {}).items()):
        keep = [e for e in lst if not any(
            MARK in h.get("command", "") and (ev, h.get("command")) not in mine
            for h in e.get("hooks", []))]
        if len(keep) != len(lst):
            log.append("hook %s: a stale kit entry removed" % ev)
        if keep:
            cur["hooks"][ev] = keep
        else:
            del cur["hooks"][ev]
    if not a.dry_run:
        json.dump(cur, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 5. self-check
    if not a.dry_run:
        probe = ('{"session_id":"__selftest__","model":{"display_name":"T"},'
                 '"workspace":{"current_dir":"%s"},"context_window":'
                 '{"total_input_tokens":10,"total_output_tokens":1,"context_window_size":200000,'
                 '"used_percentage":1}}' % HOME.replace("\\", "/"))
        r = subprocess.run([PY, os.path.join(KIT, "statusline", "statusline.py")],
                           input=probe.encode("utf-8"), capture_output=True)
        log.append("status line self-check: %s" % ("ok" if r.returncode == 0 and r.stdout else
                                                   "ERROR " + r.stderr.decode("utf-8", "replace")[:200]))
        r = subprocess.run([PY, os.path.join(KIT, "hooks", "guard.py")],
                           input=b'{"session_id":"__selftest__","hook_event_name":"Stop"}',
                           capture_output=True)
        log.append("watchdog self-check: %s" % ("ok" if r.returncode == 0 else "code %d" % r.returncode))
        for suffix in (".json", ".state.json"):
            try:
                os.remove(os.path.join(CLAUDE, "ctx", "__selftest__" + suffix))
            except OSError:
                pass

    print("\n".join("  " + x for x in log))
    print("\nInterpreter: %s" % PY)
    print("Done. Restart Claude Code so the settings are picked up." if not a.dry_run
          else "\n(--dry-run: nothing was written)")


main()
