---
name: pin
description: Finalizing a version on top of the previously pinned one — a diff from the last mark (and not from the start of the session), separating the planned from the noise and the curing of it, checks by a fresh critic until convergence, presenting to the author "what is now called the new version", and after his check — a new mark in BASELINE.md and in git. Call it when the result has reached a state that is worth checking by hand.
argument-hint: [opt. what to treat as the content of the version]
---

Finalizing the version. Content: $ARGUMENTS.

The mark is set by the AUTHOR, not by the agent. Your work is to prepare the pinning so that the author has
something to check by hand, and so that the new version is described relative to the PREVIOUS PINNED one,
and not relative to whatever the agents have managed to pile up since.

## Why this exists

A dozen sessions lie between two marks. Each introduced noise and cured someone else's, each measured
itself from its own start and reported progress. The sum of such reports does not equal the change in the
version: it is systematically inflated and skewed toward what surfaced along the way rather than toward
what had been planned. The outcome — ten sessions later you get a different product, with a full sense of
progress. This skill is the point where the count returns to reality.

## PHASE 0 — the previous mark

`.claude/BASELINE.md` and the corresponding tag or commit in git. What the author checked by hand back
then, what he considered working, which top-level goals were declared to be next. No mark — this is the
first pinning: ask the author which state to treat as the starting one, and describe the version from it.

## PHASE 1 — a diff from the mark, not from yesterday

`git diff <mark>..HEAD` and `git log <mark>..HEAD` in full. Read the changes, not the commit messages: the
messages were written by agents that measured themselves from the starts of their own sessions. Assemble a
factual list of what changed in the subject matter, not in the files.

## PHASE 2 — three buckets, do not mix them

- **PLANNED**: the top-level goals declared at the previous pinning. Which of them are closed, which are
  closed partially with a boundary, which were not started. This is precisely the content of the new
  version.
- **HOUSEKEEPING**: the noise agents introduced after the mark, and the curing of it. Repairing your own
  breakage does NOT enter the content of the version and is not raised into the highlights. A separate
  list, without adjectives.
- **UNPLANNED BUT DONE**: what surfaced along the way and turned out to be needed. Every item comes with an
  answer to why the planned work would not close without it. There is no such answer — the item moves into
  housekeeping or into the vector of the next version.

If the planned work is not closed in full, say so plainly: a version is not "everything that piled up", it
is precisely the progress on the declared goals.

## PHASE 3 — polishing to convergence

Critic cycles over everything that enters the version: a fresh critic with no context, who has not seen the
edits and is not hunting for petty nitpicks. It passes when he finds no SIGNIFICANT defects in the
iteration's changes. The pre-existing and the unrelated go into the agenda, not into a block. The final
pass is one cold critic over the artifact as a whole; whoever did the editing does not deliver the final
verdict.

## PHASE 4 — presenting it to the author (a gate, mandatory here)

Give exactly this:
1. **What is now called the version** — a list of top-level changes relative to the previous mark, in the
   language of the subject matter, not of files.
2. **What of the planned work is closed and what is not** — with the boundaries and the reasons.
3. **Housekeeping** — in one line, what was broken and repaired inside the interval.
4. **What to check by hand** — concrete scenarios by which the author will decide whether the version works
   or not.
5. **The risk delta** — what of the previously working could have broken, and how to see it.

STOP. Onward only after the author has checked by hand and said that the version works.

## PHASE 5 — pinning

After the confirmation:
- rewrite `.claude/BASELINE.md`: the mark (a tag or a sha), the date, what exactly the author verified, the
  content of the version in one line, the top-level goals for the next interval;
- put a git tag on this commit;
- do not delete the previous BASELINE, shift it into the file's history: the sequence of marks is the line
  of real versions, and it shows where the project has been going;
- tell the author in one line that the mark is set and that the count for the following sessions runs from
  it.

Pushing — by the project policy in `.claude/ritual.md`.
