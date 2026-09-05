# Pinned versions

Set by the author through the `pin` skill, after they have checked the version by hand. The newest on
top. Everything that landed in the repository after the top mark counts as a DRAFT — including the
work of past sessions and their reports of advancement. Any "advancement" is counted from here.

---

## pin/2026-09-05-named-work · 2026-09-05

**The mark is the tag, not a sha.** A sha written into a file becomes wrong the moment that file is
committed — it names the commit before itself. `git rev-parse pin/2026-09-05-named-work` resolves it.

**What this version is:** a closing names its work — the stream and the absolute path to its handoff —
and the intake opens that, instead of resolving the work from the directory the console stands in.

**Checked by the author by hand:** the full cycle, live, twice.

- In a project where nothing had been closed, `/clear` gave the agent no argument. It did NOT guess by
  the directory: it stopped and asked which work was being continued. That is the failure of the
  morning — a confident gate on someone else's work — and it did not recur.
- In another project the author closed a session by the ritual and pressed `/clear`. The intake was
  handed `статья — handoff: <absolute path>`, and the trail carries the same pair on the `done` event.
  The chain close → done → hook → open holds end to end.

**Closed out of what was planned:**
- the work is named by a stream AND a handoff path, and `ctx.py done` refuses without them — closed
- the directory filters "this console" and no longer decides which work; anything short of an exact
  match asks — closed
- open, close, mark, pin distinguish the subject of the work from the current directory: frame,
  baseline, journal, archive, push policy and every git command belong to the work — closed
- the kit has its own frame, `.claude/ritual.md` — closed; it was the one work developed outside the
  ritual it ships
- the closing silences the watchdog BEFORE the gate: a call left behind a STOP never happens — closed
- the critic gate is one rule instead of four contradictory states; hooks survive their own failures
  and record them; a corrupt config or trail no longer takes the watchdog down — closed
- dates and times come from the machine, and a handoff path dated in the future is refused — closed

**Also measured, after the mark was set:** the soft half of the watchdog delivers. The hard stop was
already proven (stderr, exit code 2); the doubt was about the 60% threshold and the journal reminders,
which travel in a field the docs do not list for the Stop event. The nudge arrived in an agent's context
verbatim — character for character the string in `guard.py`, in the wording that existed only before a
later rename, with `nudge … 34.4%` in the trail to match. What would have refuted it: that same trail
entry with no text in the context. The opposite was observed.

**Not closed:**
- the timestamps inside one stream's journal are an estimate the agent wrote from memory; the real
  times are not recoverable after the fact. The identity artifacts were corrected, the prose was not.

**Housekeeping over the interval** (not part of the version's content): four regressions of my own,
each caught by a critic — a zero written where "unknown" belonged, which made the gate fire every
turn; a properly closed session flagged as compacted; stdin drained before the hook body ran, in three
hooks at once; and edits that never reached the agents at all, because they read `~/.claude/skills`
and not this repository.

**Top-level goals for the next interval:**
1. Run `kit-review` over the trail and the 11 FEEDBACK entries: this interval alone added three,
   and their recurrence is the signal the skill is built to read.
2. Close a session in every live stream once by the new contract, and see whether the handoff path
   makes the intake shorter — the point was never the argument, it was the agent not having to guess.
