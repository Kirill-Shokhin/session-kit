# The session ritual of the kit itself

The kit was the only work developed OUTSIDE its own ritual, and that is what it cost: a closing that
named no stream and no handoff, and the next agent opened a foreign project's stream instead. Filled in
with facts on 2026-09-05.

## The subject of the work

`C:\Users\<user>\.claude\kit` (`~/.claude/kit`) — this repository, and not the directory the
console happens to stand in. The console is routinely opened elsewhere; that is normal here, and it
is exactly why every path below is absolute and every git command belongs to THIS repository.

## Levels of knowledge

- PUBLIC (goes to github.com/Kirill-Shokhin/session-kit):
  - `README.md` — what the kit is, what it automates and what it deliberately does not.
  - `skills/`, `rules/`, `templates/` — the ritual itself; `install.py` — its delivery.
  - `ctxlib.py`, `view.py`, `hooks/`, `bin/`, `statusline/` — the mechanism.
  - `.claude/ritual.md` (this file) and `.claude/BASELINE.md` — the kit's own frame. Public on
    purpose: the kit developing itself by its own ritual is the point, and its absence is what
    let a closing name no work at all.
  - `LICENSE`.
- SESSION-LEVEL (personal, in `.gitignore`, never published):
  - `journal/<YYYY-MM-DD>-<slug>.md` — the journal of the running session.
  - `journal/<date>[-<slug>]-handoff.md` and `-dag.md` — the closed session's handoff and DAG. The
    slug is required from the SECOND closing of a day: `journal/` is not under version control, so a
    name collision destroys the earlier pair with nothing to restore it from.
  - `FEEDBACK.md` — friction with the wordings; `events.jsonl` — the trail of firings.
  - `config.json` — thresholds and mode of this machine; `skills-local/`, `legacy/`, `examples/`.
  - `commands/` — the whole directory. Holding that line by file name cost the other personal
    commands once: `.gitignore` had moved on to the directory, the installer had not, and an
    install from a clone destroyed what git did not know about.
- The agent's MEMORY: `~/.claude/projects/<project>/memory/` + `MEMORY.md` as the index.

## The main document

`~/.claude/kit/README.md`, read at the opening with your own eyes. Without it the agent takes the kit
for a set of scripts and starts improving the mechanism past the point of it: what is automated here is
the MOMENT of closing, not the ritual, and the boundary between the two is the whole design.

Right after it — `FEEDBACK.md`: every entry there is a place where a wording led an agent past the
point, and they recur.

## The journal and the session archive

- Everything lives in `~/.claude/kit/journal/` — journal, handoff and DAG side by side, named by date.
- **There is no `sessions/INDEX.md` here, and that is deliberate:** one stream and three files per
  session make a directory listing the index. Do not add a second location for the same thing.
- **A second closing on the same day must not overwrite the first:** the file names carry a slug,
  not only the date.
- `journal/` is in `.gitignore`, so this archive is NOT under version control: a deletion here is
  final and `open` cannot check a handoff against `git log`. That is the author's privacy call, and
  the price of it is that the cleanup phase must name every deletion out loud.

## Streams

- **kit** — the only one. The whole repository. Everything the author has that runs the ritual depends
  on it, so a broken mechanism here breaks every other stream at once.

## The pinned version

- `~/.claude/kit/.claude/BASELINE.md` — the last version the author checked by hand. It is IN the
  repository (unlike the journal): the line of versions is the history of the kit itself.
- The first mark is `pin/2026-09-05-named-work`: a closing names its work, and the intake opens that
  instead of resolving it from the directory. Checked by hand, live, in two projects.
- **A mark is a tag on a commit, and `pin` measures `git diff <mark>..HEAD`** — so nothing may rewrite
  a marked commit afterwards.
- It is set by the author only, through the `pin` skill.

## Baseline checks

```
python ~/.claude/kit/install.py --dry-run     # what the installation would do
python ~/.claude/kit/bin/ctx.py               # live sessions and limits
python ~/.claude/kit/bin/ctx.py stats         # how the firings ended
cd ~/.claude/kit && python -m py_compile ctxlib.py view.py install.py bin/ctx.py hooks/*.py statusline/*.py
python "$HOME/.claude/kit/install.py" --check   # the repository against what agents actually read
```

**AN EDIT OF A SKILL IS NOT DONE UNTIL `install.py` HAS RUN.** Agents read `~/.claude/skills`, not
this repository, and the two drifted apart silently once already: a defect was fixed in the source
and every running agent went on executing the old wording. A bare `diff` cannot tell that apart from
the personal glossary rewriting the installed copies — `--check` applies the glossary first. Publishing without installing changes
nothing for the agents; installing without publishing changes nothing for anyone else.

The mechanism is verified by running it, not by reading it: the hooks are separate processes, and a
hook that raises is silent — the console shows nothing.

## Commit and push

- Commit, amend, squash: freely, without asking.
- Message style: public, about the result, no process and no session identifiers.
- **Push: ALLOWED** — the author delegated publishing to the agents.
- **The mirror APPENDS; it is no longer squashed to one commit.** It was published as a single commit
  once, to leave the private history out of it. That is done, and from here each closing adds its own
  commit: `install.py --publish` never squashed anyway, so the old rule described nothing, and a squash
  would destroy the tag and the diff that `pin` measures every count from. `--force-with-lease` stays
  as the push, so a rewrite is possible when it is genuinely meant.
- Nothing personal travels: check `git status` against `.gitignore` before publishing.

## The gate

- the verified state — what was checked by running it, not by reading it;
- the divergences between the handoff and the repository, with the evidence;
- what remains unverified;
- which mark the count runs from (while there is none — say so plainly);
- the plan of the next steps.
