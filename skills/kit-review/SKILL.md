---
name: kit-review
description: A review of the session kit itself — read the watchdog's trail, the friction entries and the session journals, find the places where the wordings of the skills led past the point, and propose pinpoint edits to the author. Call it once every few sessions, or when the author feels the ritual has started to work worse.
argument-hint: [opt. what feels off / which period to look at]
---

Reviewing the kit. What feels off: $ARGUMENTS.

The rituals are now executed by agents, and part of the firings happen without the author's participation:
he sees neither the nudges, nor the moment of the stop, nor what the agent did with them. In such a scheme
a crooked wording pushes the wrong way silently, and for years. This skill is the only place where the
scheme is checked against itself.

You edit the WORDINGS, not the behavior of the agents: the kit is text, and its entire effect lives in the
text.

## PHASE 0 — what to look at

- `python ~/.claude/kit/bin/ctx.py stats` — a summary of the firings;
- `python ~/.claude/kit/bin/ctx.py log 200` — the trail itself;
- `~/.claude/kit/FEEDBACK.md` — the friction entries from the agents;
- the projects' session journals and archives (`.claude/journal/`, `.claude/sessions/`);
- the kit's `git log` — what was edited in the skills themselves, and when.

## PHASE 1 — four questions to the data

1. **Stops without a closing.** Are there sessions where the watchdog stopped the agent and the ritual was
   never carried out? That is a direct defect: the instruction did not see it through. Look at what the
   agent did instead.
2. **Empty journals under dense nudging.** Many nudges and zero entries means the criterion for a fork is
   not being recognized: either the list of events does not cover the subject matter of the project, or the
   wording sounds optional. The opposite skew — an entry for every sneeze — means the criterion is too
   broad.
3. **What did not survive the transition.** Take a pair of adjacent sessions of one stream: what was in the
   journal and handoff of the closing session, and what the opening one lacked. A hole here is a defect of
   `close`, not of the agent's memory.
4. **Recurrence of friction.** One entry in FEEDBACK is an incident. Three entries about one place — the
   wording is at fault, and an edit is obligatory.

## PHASE 2 — separating a defect of the text from a defect of the case

Before proposing an edit, answer this: was it the wording that led past the point, or did the particular
task not fit into the frame? The second is not cured by an edit — the skills end with the words "this is
ordinary logic, not dogma", and a single deviation on common sense is legitimate. We edit only what recurs
or what led past the point unambiguously.

## PHASE 3 — the proposal to the author (a gate)

For every place give a quadruple:
- WHERE: the file and the paragraph;
- WHAT IT SAYS NOW: verbatim;
- WHAT CAME OUT: evidence from the trail, a journal or FEEDBACK — not reasoning;
- THE EDIT: the new wording in full, and not a description of the intent.

Separately, say what you propose NOT to touch, even though it looks suspicious, and why. The kit has been
edited several times already; every edit made without evidence removes something that someone had been
debugging over dozens of sessions.

STOP. You edit only after the author's OK.

## PHASE 4 — applying it

The edits go into `~/.claude/kit/`, then `python ~/.claude/kit/install.py` (the skills are installed by
copying; without a reinstall the edit will not travel), then a commit in the kit's repository with a
description of WHAT the edit was caused by — the evidence, not the intent. Move the processed entries from
`FEEDBACK.md` to the end of the file under `## Processed <date>`, so that the next review does not count
them again.
