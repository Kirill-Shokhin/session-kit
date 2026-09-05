# -*- coding: utf-8 -*-
"""Installing the kit on a machine. Idempotent: a repeated run updates.

  python install.py                 install or update
  python install.py --update        pull the fresh version from the repository and reinstall
  python install.py --publish "..." commit your own edits and push them to the repository
  python install.py --check         which installed skills are behind the repository
  python install.py --dry-run       show what will be done
  python install.py --soft 60 --hard 75   the context window watchdog thresholds

What it does: puts the skills into ~/.claude/skills and the commands into ~/.claude/commands,
merges the status line and five hooks into ~/.claude/settings.json, disables auto-compaction.
Existing settings are preserved, the file is backed up before it is edited.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, time

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


def backup(path):
    """Copy a file aside before editing it, keeping only the last three copies.

    Every run made one and none were ever removed: sixty-eight `settings.json.bak-*` had piled up
    in ~/.claude, all identical, and "restore the backup" stopped meaning anything when there are
    sixty-eight of them to choose from.
    """
    import glob
    shutil.copy2(path, path + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
    old = sorted(glob.glob(path + ".bak-*"))[:-3]
    for f in old:
        try:
            os.remove(f)
        except OSError:
            pass


def _force_remove(func, path, _exc):
    """Retry a removal after clearing the read-only bit.

    Git writes loose objects with mode 0444, and `shutil.rmtree` stops at the first one. On
    Windows that meant an install from a clone died halfway: `.claude/` was already gone (rmtree
    walks alphabetically), `.git` was half removed, the remaining steps never ran and the author
    saw a traceback instead of the log. This is the only path on which the KEEP list runs at all.
    """
    try:
        os.chmod(path, 0o700)
        func(path)
    except Exception:
        pass


def installed_drift():
    """Which installed skills differ from the repository BEYOND the personal glossary.

    A bare `diff -r` cannot answer this: the installer rewrites the installed copies through
    `skills-local/glossary.json`, so it always reports differences and the one case it is there to
    catch — an edit that never reached the agents — is invisible among them.
    """
    gl = os.path.join(KIT, "skills-local", "glossary.json")
    pairs = json.load(open(gl, encoding="utf-8")) if os.path.exists(gl) else []
    out = []
    root = HERE if os.path.isdir(os.path.join(HERE, "skills")) else KIT
    # skills-local too: the installer puts it into the same ~/.claude/skills, and the pipeline the
    # author works through lives there. Checking only the public half answered "everything matches"
    # while a personal skill sat a version behind.
    pairs_dirs = [os.path.join(root, "skills"), os.path.join(root, "skills-local")]
    seen = []
    for src_dir in pairs_dirs:
        if not os.path.isdir(src_dir):
            continue
        for name in sorted(os.listdir(src_dir)):
            seen.append((src_dir, name))
    for src_dir, name in seen:
        f = os.path.join(src_dir, name, "SKILL.md")
        g = os.path.join(CLAUDE, "skills", name, "SKILL.md")
        if not os.path.isfile(f):
            continue
        if not os.path.isfile(g):
            out.append(name + ": not installed")
            continue
        t = open(f, encoding="utf-8").read()
        for a_, b_ in pairs:
            t = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(a_), lambda m: b_, t)
        if t.strip() != open(g, encoding="utf-8").read().strip():
            out.append(name + ": the installed copy is behind the repository")
    return out


def report(log, tail):
    """Print the log and a closing line. One place: the same two lines were written out four
    times, and two of the copies had already lost the newline in an edit."""
    print(chr(10).join("  " + x for x in log))
    print(chr(10) + tail)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report skills whose installed copy is behind the repository")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--update", action="store_true",
                    help="git pull in the kit, then the usual installation")
    ap.add_argument("--publish", metavar="MESSAGE",
                    help="commit the kit's edits and push them to the repository")
    ap.add_argument("--soft", type=int, default=None)
    ap.add_argument("--hard", type=int, default=None)
    a = ap.parse_args()
    if a.check:
        if (a.update or a.publish or a.dry_run
                or a.soft is not None or a.hard is not None):
            print("--check reports and does nothing else; run it on its own")
            return 1
        bad = installed_drift()
        print(chr(10).join("  " + x for x in bad) if bad
              else "every skill installed matches the repository (glossary applied)")
        return 1 if bad else 0
    if a.soft is not None and a.hard is not None and a.soft >= a.hard:
        print("the reminder threshold must be below the stop: --soft %d --hard %d"
              % (a.soft, a.hard))
        return 1
    log = []

    # 0. synchronization with the repository — the kit lives on several machines
    src = HERE if os.path.exists(os.path.join(HERE, ".git")) else KIT
    if a.update and a.dry_run:
        log.append("update: skipped, --dry-run")
    elif a.update:
        r = subprocess.run(["git", "-C", src, "pull", "--ff-only"], capture_output=True, text=True)
        log.append("update: " + ((r.stdout or r.stderr).strip().splitlines() or ["ok"])[-1])
        if r.returncode:
            report(log, "The pull failed — sort the repository out and try again.")
            return 1
    if a.publish and a.dry_run:
        # --dry-run used to be ignored here: the flag documented as "see what would be done"
        # really committed and really pushed. Now it shows the list and stops.
        r = subprocess.run(["git", "-C", src, "add", "-A", "--dry-run"],
                           capture_output=True, text=True)
        for line in (r.stdout or "").strip().splitlines():
            log.append("would publish: " + line.strip())
    elif a.publish:
        # WHAT GOES OUT IS SHOWN BEFORE IT GOES. `add -A` is blind, and the only thing standing
        # between the personal layer and a public repository is .gitignore. Printing the list is
        # not a check, but it turns a silent leak into a visible one — and the frame requires the
        # agent to compare it against .gitignore before publishing.
        r = subprocess.run(["git", "-C", src, "add", "-A", "--dry-run"],
                           capture_output=True, text=True)
        for line in (r.stdout or "").strip().splitlines():
            log.append("publishing: " + line.strip())
        subprocess.run(["git", "-C", src, "add", "-A"], check=False)
        r = subprocess.run(["git", "-C", src, "commit", "-m", a.publish],
                           capture_output=True, text=True)
        log.append("commit: " + ((r.stdout or r.stderr).strip().splitlines() or ["ok"])[-1])
        if r.returncode and "nothing to commit" not in (r.stdout or "") + (r.stderr or ""):
            report(log, "The commit failed. Nothing was pushed.")
            return 1
        # --force-with-lease, not a bare push: the public mirror is kept as squashed history, so
        # --follow-tags: a pin creates a tag, and BASELINE.md is built on that tag resolving in a
        # clone. A push without it left the mark local and the doctrine false for everyone else.
        # The lease guards against overwriting a commit that arrived meanwhile.
        r = subprocess.run(["git", "-C", src, "push", "--follow-tags", "--force-with-lease"],
                           capture_output=True, text=True)
        for line in ((r.stdout or "") + (r.stderr or "")).strip().splitlines() or ["ok"]:
            log.append("push: " + line.strip())
        if r.returncode:
            report(log, "The push failed. Nothing else was done.")
            return 1

    # 1. the kit itself into its place
    # Personal files installing from a clone must not wipe. All of them are in .gitignore, so a
    # clone does not carry them — whatever is lost here cannot be restored. THE ENTRIES MUST TRACK
    # .gitignore: `commands` was held here by ONE file name while .gitignore had moved on to the
    # whole directory, so every other personal command was destroyed by an install from a clone
    # and the log reported them kept.
    # `.claude/BASELINE.md` — and only it, not the whole directory. It is the pinned-version mark,
    # and one made locally but not yet committed would be wiped by an install from a clone. Its
    # neighbour `.claude/ritual.md` IS tracked, so it must come FROM the clone: keeping the whole
    # directory would silently shadow a fresh frame with the local stale one.
    # `.claude/BASELINE.md` is NOT here: it is tracked by git, and `pin` commits the mark as it
    # sets it. Keeping a local copy would shadow a fresher one from the clone — the very argument
    # written just above for its neighbour `.claude/ritual.md`, and it must be answered the same
    # way for both.
    KEEP = ("config.json", "events.jsonl", "FEEDBACK.md", "journal", "examples", "legacy",
            "skills-local", "commands")
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
                    shutil.rmtree(KIT, onerror=_force_remove)
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
        # ONLY THE KIT'S OWN SKILLS. It used to walk every skill in ~/.claude/skills and rewrite
        # general phrases in place, without a backup: someone else's skill installed later would
        # be silently edited by a glossary that has nothing to do with it.
        mine = {n for n in os.listdir(os.path.join(KIT, "skills"))} | {
            n for n in (os.listdir(os.path.join(KIT, "skills-local"))
                        if os.path.isdir(os.path.join(KIT, "skills-local")) else [])}
        for dp, _, fns in os.walk(os.path.join(CLAUDE, "skills")):
            if os.path.basename(dp) not in mine:
                continue
            for fn in fns:
                if not fn.endswith(".md"):
                    continue
                f = os.path.join(dp, fn)
                t = orig = open(f, encoding="utf-8").read()
                for src_s, dst_s in pairs:
                    # ON WORD BOUNDARIES, not anywhere. A plain replace fired INSIDE a longer
                    # word: the pair "main document"→"canon" turned "the root domain document"
                    # into "the root docanon" in the installed skill, and the agent read that.
                    t = re.sub(r"(?<![\w-])%s(?![\w-])" % re.escape(src_s), lambda _m: dst_s, t)
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
                        backup(md)
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
        # By this point the kit is already replaced and CLAUDE.md rewritten. A traceback here would
        # leave the installation half applied with the hooks unregistered — and the two neighbours
        # in this same file (config.json, the CLAUDE.md markers) are both defended, this one was not.
        try:
            cur = json.load(open(sp, encoding="utf-8"))
        except Exception as e:
            print("settings.json is unreadable (%s).\n"
                  "The kit is in place, but the hooks are NOT registered: fix the file "
                  "and run the installer again." % e)
            return 1
        if not a.dry_run:
            backup(sp)
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
        if a.dry_run:
            # asking merge_hooks on a COPY: the dry run used to print "will be added" for every
            # event, including the five that were already there and would merely be updated
            import copy as _copy
            log.append("hook %s %s (dry run)" % (ev, merge_hooks(_copy.deepcopy(cur), ev, entry)))
        else:
            log.append("hook %s %s" % (ev, merge_hooks(cur, ev, entry)))
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


try:
    sys.exit(main() or 0)
except SystemExit:
    raise
except Exception:
    # the personal files are already returned by the `finally` inside; what the author must not
    # lose is the report of what happened — a traceback alone says nothing about what survived
    import traceback
    traceback.print_exc()
    print(chr(10) + "The installation stopped midway. Personal files were put back; run it again "
          "once the cause above is dealt with.")
    sys.exit(1)
