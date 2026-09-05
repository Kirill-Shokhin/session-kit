---
name: open
description: "Session opening — handoff intake: the shift into the project's language (the project's main document with your own eyes), identifying your own stream, restoring state from the handoff and the DAG, verifying what is written against reality, counting from the version the author pinned, a plan for the next steps, a gate for the author. Call it first in a new session that continues work."
argument-hint: [stream whose handoff to take + opt. focus]
---

Taking the handoff and opening the session. Stream and focus: $ARGUMENTS.

The goal — by the end of the ritual, to be equivalent to the agent who closed the previous session of THIS
stream: same language, same causality, same protected positions, a plan for the next step. I write NOTHING
final before the gate.

FIRST, WHOSE WORK THIS IS — before reading a single project file. If $ARGUMENTS carries a path to a
handoff, THAT PATH NAMES THE WORK, and the repository it lies in is the one everything else comes from:
the frame, the baseline, the journal, the archive, the push policy — and every git command you run. If the
INVITATION that brought you here lists several closed works instead (the argument is empty in that case),
ask the author which one, in one line, and do nothing else until he answers.

WITH NEITHER — no path and no list — the current directory is a HYPOTHESIS, not an answer. Read its
archive, and if it holds exactly one stream, take it and SAY IN THE GATE which work you opened and on
what evidence. More than one, or none — ask, one line, before reading anything else. What is forbidden
is the silent version: opening whatever the directory suggests and reporting as if the work had been
named to you. The subject of a work is not the directory the console stands in — the two come
apart exactly when it is expensive, and taking the directory's word for it once had an agent restore a
stream that was not its own, verify it honestly and present a confident gate on it.

Take the frame from the `.claude/ritual.md` OF THAT WORK (what the main document is, where the session
docs, the journal and the archive are, which streams exist, what the baseline is checked by, how to commit
and whether pushing is allowed). Reading it from the wrong repository hands you someone else's push policy.

NO FRAME — CREATE IT YOURSELF, do not defer it to the author. Take `~/.claude/kit/templates/ritual.md`, walk
the repository and fill in with facts everything that can be established by reading: the layout across the
three levels, the project's main document, the journal and archive paths, the baseline commands from the
README or the build configs. A few things will remain that cannot be derived from the repository — ASK the
author about those right here, as a short list, in one message:
- which document is the main one here, if that is not obvious;
- whether pushing is allowed in this repository;
- which streams exist, if there is more than one;
- what counts as the last version he verified — write the answer into the work's `.claude/BASELINE.md`
  yourself, from `~/.claude/kit/templates/BASELINE.md`, marked [stated]: it is his word, not a check of
  yours, and `pin` will not ask again.
Write the answers into the files yourself. The author must not fill anything in by hand: he answers the
questions, you write the files. Until the answers arrive, work by defaults — pushing forbidden, one stream,
counting from the current HEAD as a draft.

PHASE 0 — THE SHIFT (do NOT skip it). Read the project's root domain document YOURSELF —
in full, or its load-bearing parts by the table of contents, but with your own eyes, not through retellings
from memory: without this the agent does not understand the domain and invents incorrectly. This is the
shift from the base model to the project's mode of thinking, the precondition for speaking one language at
one level. Plus the main document's key companions, by the sense of the task.

PHASE 1 — STREAM, HANDOFF, MEMORY. First determine WHOSE handoff you are taking. The stream is named in
$ARGUMENTS or follows from the task; streams are logically independent and may run in different worktrees,
so the freshest file or commit ≠ your handoff — a lesson proven the expensive way. The author holds the
separation of the streams; your job is not to mistake someone else's for your own.

Take:
(a) the LATEST handoff of your own stream with all its attachments — DAG, vector, holes: the path from
    $ARGUMENTS, else wherever the work's ritual says its archive is (by default `.claude/sessions/` and the
    top index entry for this stream; some repositories keep it elsewhere and say so). What is load-bearing
    in the DAG are the
    edges, the author's intents and the NEGATIVE edges, that is, where the work already went and why that
    was the wrong way. Do not go deeper into the archive without being told: old journals and DAGs lie there
    as provenance, and the author will send you there himself ("read the last five DAGs") when he sees you
    repeating the same mistakes;
(b) the Bayes memory in full — ALWAYS (it is behavior, not project);
(c) the architectural landmarks and the code map of your own track.
Other streams — by headings, do not go deeper, but know who is alive and where their files are, so as not
to disturb them.

PHASE 2 — THE ADJACENT. The levels below: the internal plan or roadmap (where your block and its gates
are), the session docs, and the CODE the handoff points at with landmarks. An engineering handoff transfers
together with its files. Not everything indiscriminately, but the load-bearing parts are better read than
not.

PHASE 3 — VERIFICATION AGAINST REALITY (the load-bearing phase of the ritual). Do not take the handoff's
claims on faith — open the persisted state: `git log` and `git status` (a neighbor in the repository may
have committed, or may be working right now — note the delta since the handoff), run the baseline checks,
look at the live services and artifacts the handoff refers to. Whoever wrote the previous session was
writing on a filled context window and could be wrong in a particular while right in general. A divergence
between handoff and reality is a flag for the plan, not a silent memory edit. Mark for yourself what each
load-bearing claim rests on: [measurement] is recomputed by a command, [inference] is someone else's
interpretation, [stated] is the author's position, [unverified] has not been checked for at least a session.
Building something new on the unverified without checking it is not allowed.

PHASE 4 — WHAT PROGRESS IS MEASURED FROM. Read the work's `.claude/BASELINE.md` — the last version PINNED
by the author: he checked it by hand and treats it as working. Everything laid down after the mark is draft,
including the work of past sessions and their upbeat reports. Any "progress" is counted from the mark, not
from the start of your session and not from what you found in the repository. Cleaning up the noise agents
introduced after the mark is not an achievement: it returns to zero. The goals remain the planned top-level
ones, not the tasks that surfaced along the way. No BASELINE file, and you have not already asked about it
while creating the frame — ask the author what to treat as the last
verified version, and create it (skill pin).

PHASE 5 — PLAN. Take the forward vector from the handoff and propose the steps of your block with
justifications. Do not attack what is marked as parked with a reason, or the named boundaries.

PHASE 6 — GATE. Present compactly: (1) the restored state — verified facts, not a retelling of the handoff,
(2) the divergences from reality and the neighbors' delta, (3) what remains unverified, (4) which mark the
count runs from and what has been draft since, (5) the plan of steps with justifications. STOP — the author
checks that the state was reproduced correctly and that there is no bias. After that you work on your own
along the approved plan. Only an explicit "just execute" in $ARGUMENTS replaces the gate with a short
status. A short first message from the author — a one-word go-ahead in any language — is the opposite:
he is being told by his console that writing anything at all starts the intake, and what he is waiting for
is exactly this gate.

AFTER THE GATE: start this session's journal (skill mark) and write the forks into it at the moment they
happen, especially the discarded options. The closing ritual assembles the journal, not recollections.

RULES ON TOP (from the Bayes memory, apply from the first step): do not re-litigate the author's protected
positions · do not attack named boundaries and things parked with a reason as unfinished work (when in
doubt — finish it, do not attack) · read past sessions' "done / not-done" as a result with a boundary ·
committing and bringing history into a logical form is free, pushing — only if the project policy allows ·
with a live neighbor: only explicit paths in git, `commit --only`, `log` and `status` immediately before
committing, no history rewriting while the neighbor has not been stopped.
