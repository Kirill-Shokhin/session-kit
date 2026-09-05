---
name: mark
description: Write a fork into the current session's journal at the moment it happened — a discarded option with its reason, a decision that changes direction, a measurement, a divergence from expectation, a course correction from the author. One entry, cheap. Call it right away, without deferring it to the closing of the session.
argument-hint: <what happened>
---

Recording: $ARGUMENTS.

## When to write

Not on a schedule, but on an EVENT. The watchdog's reminder arrives as the context window fills, but it is
not what decides: ten percent of the window may hold three forks, or none at all. An entry is needed if
one of these has happened:

1. AN OPTION WAS DISCARDED — which one exactly, and what refuted it.
2. A DECISION THAT CHANGES DIRECTION — one of the paths was chosen, the rest are closed.
3. A MEASUREMENT — a number was obtained that went, or is going, into a decision.
4. A DIVERGENCE — reality did not match the handoff, the plan or the expectation.
5. A COURSE CORRECTION FROM THE AUTHOR — his intent, in his words, while the wording is fresh.

None of this happened — there is no entry, and the reminder needs no answer. Routine edits, intermediate
runs and small fixes do not go into the journal: it is not a work log, it is a map of forks.

## Where

`.claude/journal/<YYYY-MM-DD>-<short task slug>.md` — a file per session, relative to the WORK (its
`.claude/ritual.md` overrides both the place and the naming), not to the directory the console stands in.
The date in the name is the day the session BEGAN, read off the machine like the timestamps below — the
closing takes the name of the archive from this one.

One shared file will not do: it grows, and the closing ritual is forced to read the
whole history of the project instead of its own session. Provenance rests not on the number of files, but
on the timestamp, the ban on backdated editing, and git.

On the first entry put a header: the date, the session id, the session's task in one line, and the version
mark from the work's `.claude/BASELINE.md` that the count runs from.

## What it is and what it is not

The journal is RAW MATERIAL for the closing ritual, living inside a single session. It is not a handoff and
not a DAG: those are assembled in `close`, out of the journal and out of checking the files, and are placed
into the session archive in full. A new agent reads the previous session's handoff and DAG, and writes into
the journal of its own — that is what holds the provenance: it is visible who decided what and when.

## Format

READ THE TIME OFF THE MACHINE, never off your own sense of it:

```bash
date +%FT%H:%M                          # Git Bash and other POSIX shells
```
```powershell
Get-Date -Format "yyyy-MM-ddTHH:mm"     # PowerShell
```

Late in a session the estimate drifts, and it drifts one way: a real session ran from midday to evening
and stamped its entries past midnight of the NEXT day. By the closing the drift had moved into the name
of the archive, into the titles of the handoff and the DAG, and into the index — the series of days
skipped one. A time you cannot recompute is not a record of when something happened, it is a guess
wearing the clothes of one.

```
## <ISO time> · <short title>
- DISCARDED: <what, and in which formulation> — REFUTED BY: <measurement, argument, fact>
- DECIDED: <what was accepted and what that closes> [measurement|inference|stated]
- INTENT: <why the author saw it this way, if the decision came from him, in his own wording>
- ANCHOR: <file:line | commit | the command this is reproduced by>
```

RULES:
- What was discarded matters more than what was accepted. What was accepted lives in the code and the docs
  and will be found; what was discarded leaves no trail anywhere, and the next agent will walk that path
  again.
- The reason for discarding is WHAT refuted it, not "it did not fit".
- Do not edit past entries after the fact. Something changed — a new entry with a reference to the old one.
- One fork, one entry. Accumulating three at a time is not allowed: they congeal and lose their reasons.
