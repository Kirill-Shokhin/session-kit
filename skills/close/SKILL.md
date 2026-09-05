---
name: close
description: Session closing — lay knowledge out across the levels (public / session / memory), assemble the causal DAG with negative edges and the author's intent, separate progress from curing your own noise, Bayes corrections, the forward vector, cleanup of what is no longer current, commit, a gate before a clean agent is opened. Call it when the context-window watchdog demands it or the author asks.
argument-hint: [opt. what to preserve especially / focus]
---

Closing the session. The goal — everything valuable at the RIGHT level, the project's main document
self-sufficient, causality and intent carried over, and a clean agent continuing without sagging on the
goals and without bias. Focus: $ARGUMENTS.

Closing costs 1–5% of the context window: it is an assembly of what is already known, not research. It
becomes expensive only if the session journal was not kept and you have to recall things. Take the project
frame from `.claude/ritual.md` (levels, journal, session archive, streams, baseline checks, commit and push
policy). No file — create it yourself from `~/.claude/kit/templates/ritual.md`, filling in everything that
can be established by reading the repository, and ask the author only about what cannot be derived from
there (pushing, the project's main document, the streams, the last verified version).

WORKING MODE: do NOT turn plan mode on. The ritual must be carried to the end without the author's
participation — he may be away from the machine, and a session hanging on a confirmation loses both time
and context window.
- ADDITIVE work (journal, handoff, DAG, memory, vector, writing what was missed into the docs) — do it
  IMMEDIATELY, asking nothing. Something superfluous that got written is cheap; what is not written is
  recoverable by nothing.
- COMMITS, amends and squashes — also without asking: history is kept logical rather than breeding dozens
  of entries.
- PUSHING — only if the project policy in `.claude/ritual.md` allows it. Forbidden by default:
  incremental noise must not travel into the repository past the versions the author expects.

THREE LEVELS (the boundary is loose but recognizable) — and ALL three must be used correctly:
1. PUBLIC — for an outside audience (results, conclusions, boundaries; zero process).
2. SESSION — ideas, state, the unfinished; in the repository, but not announced.
3. The agent's MEMORY (+ git-ignored temp) — not the course of the project, but the agent's behavior,
   Bayes, process.

"CLOSED" = a formally named boundary with a reason — a result, not a hole. "To close" ≠ "to invent an
explanation where there is a boundary" and ≠ "to remove the boundary". The real REMAINDER is what lives
ONLY in the dialogue. A piece's states: (A) on paper and named with a reason · (B) on paper, not in the
public level — a follow-up · (C) only in the dialogue — catch it NOW.

PHASE 0 — orientation: the project's actual layout across the three levels (which files go where).

PHASE 0.5 — THE JOURNAL FIRST. Read THIS session's journal (`.claude/journal/`, skill mark). The entries
were made as things happened; your present recollections are after the fact. On a divergence the journal is
right, and your version is a hypothesis to be checked in the files. The journal is raw material, not a
finished handoff: it removes the dependence on memory, but all the work below you do again and in full. An
empty journal is a finding in itself — say so at the gate.

PHASE 1 — THE LAYOUT ACROSS LEVELS (the core). Every piece of the session's knowledge → its correct level,
by type:
- A RESULT, a conclusion, a boundary stuck in memory (lvl 3) or in a draft (lvl 2) → RAISE it into the
  public doc (lvl 1) IN PLACE. Fix gaps IN the main document, do not shove them into memory.
- Process, Bayes, agent behavior that has seeped into a public or session doc → LOWER it into memory.
- A live idea or state with no place → a session doc.
The goal is not "where does the new thing go", but that ALL of the session's knowledge sits at its own
level.

PHASE 2 — THE EQUIVALENCE TEST (the deletion gate, judged at the level of the public doc). Is a fresh agent
that has read ONLY the public docs equivalent — for CONTINUING the work (goals, intent, frame, no
regression) — to an agent that has also read the drafts slated for deletion? Wherever it is not equivalent,
you did not raise it all the way: raise it into the project's main document BEFORE deleting, in place, not
into memory. Method: write out what the "full" one knows and what the "public-only" one does not.

PHASE 3 — THE CAUSAL DAG (what carries "me" over into the new agent):
- NODES (links, ideas, states, what was touched) · EDGES from→to with a justification and a type
  {enrichment | confirmation | refutation | rollback | replacement} · NEGATIVE edges are MANDATORY: where
  the work came from and why it was wrong — the proof of the path.
- The INTENT on the load-bearing edges: why the author saw it this way, in his own words. That is exactly
  what gives "me".
- RELIABILITY where it is not obvious: [measurement] — a recompute command exists · [inference] — my
  interpretation · [stated] — the author's position · [unverified] — taken on faith from a past handoff.
- lossy on node content, lossless on topology: collapse a heavy derivation down to its arguments and
  references; an edge and an intent — NEVER. Phrase it AS IT WAS DECIDED in the dialogue, do not
  reinterpret.
This session's DAG, journal and handoff go into its archive directory (`.claude/sessions/<date>-<stream>/`)
and into the index under the stream's name: intake at opening goes by stream, not by the freshness of a
file. Past ones are not rewritten — they are the provenance the author sends the agent back to when it
starts repeating the same mistakes.

PHASE 4 — WHAT PROGRESS IS MEASURED FROM (do not skip it, this is the main source of drift).
The basis is the last version PINNED by the author (`.claude/BASELINE.md`, skill pin), NOT the state at the
start of this session and not the result of the previous one. Everything laid down after the mark is draft,
including the work of past sessions. Separate them explicitly and do not mix:
- PROGRESS on the planned top-level goals — relative to the mark;
- HOUSEKEEPING: the noise agents introduced after the mark, and the curing of it. This is NOT an
  achievement and NOT progress. Repairing what you broke yourself returns to zero rather than moving
  forward, and it has no place among the report's highlights.
The mistake every next agent makes: it takes the start of its own session as the reference point, sees the
difference and declares it progress. Over a dozen such sessions the project drifts sideways amid upbeat
reports. If there is no progress on the planned goals — write exactly that, in exactly those words.

PHASE 5 — Bayes corrections (what NOT to reopen) → memory: the agent's recurring blind spots; the author's
protected positions (decided, no flip-flopping); the named boundaries. WARN SEPARATELY: "done /
not-done" is NOT to be read as "the author left it unfinished, it must be attacked" — distinguish a named
boundary (do not touch) / something parked with a reason / item B (finish it properly). When in doubt —
finish it, do not attack.

PHASE 6 — THE FORWARD VECTOR: the open frontier and the next real task; what is parked WITH A REASON; the
gates and conditions; the goals that must not sag. The top-level goals remain the planned ones, not the
ones that surfaced along the way.

PHASE 7 — VERIFICATION AGAINST THE FILES: check what you are writing out against what is REALLY in the
files — open the persisted state, do not trust your own claim. Check that every reference in the handoff
resolves (the file exists, the line is the right one, the command reproduces). Simulate it: will an agent
with no context reconstruct the path, the goals and the intent from what has been written out alone? Holes
and contradictions — as a list, without papering over.

PHASE 8 — CLEANUP (without asking, together with writing the new material): clear out what genuinely will
not be of use again — superseded drafts, stale pieces of memory, duplicates; update the indexes, do not
merely append to them.
DO NOT TOUCH: rejected branches and the reasons for the rejections (that knowledge stays current forever),
past sessions' journals and DAGs (provenance), the named boundaries. Git will not bring untracked files
back — name such deletions out loud.

PHASE 9 — COMMIT: reduce the session to ONE logical entry — one version per batch (an amend, or
`git reset --soft <last pushed sha>` and a single commit on top). Public style of message, about the
result, without process, Co-Authored-By. With a live neighbor in the repository: only explicit paths,
`commit --only`, `log` and `status` immediately before committing, no history rewriting while the neighbor
has not been stopped. Pushing — only if the project policy allows it.

PHASE 10 — FRICTION WITH THE RITUAL: if during the session the wording of a skill or of the watchdog got in
the way, led you past the point or did not cover the case — append an entry to `~/.claude/kit/FEEDBACK.md`
(what was said, what came out, what was missing). This is the only channel through which the author learns
about defects in the ritual: the watchdog fires without him. Do not write proposals of "how it should be";
the kit-review skill derives those from recurrence.

GATE — present it and STOP: (1) the map of the layout across the levels and the verdict of the equivalence
test, (2) the DAG with intent and negative edges, (3) progress relative to the PINNED version, and
separately the housekeeping curing of noise, (4) the holes from phase 7, (5) the Bayes corrections, (6) the
forward vector. Everything is already written and committed — the author is not unblocking the work, he is
checking that the state is reproducible.

PUT OUT THE WATCHDOG once the handoff is written and presented:
`python ~/.claude/kit/bin/ctx.py done <session id>` (the id was given at session start).
Immediately after that ONE re-check pass will come — do not argue with it and do not skip it: on a filled
context window your own write-up systematically leaves things unwritten, and this is the only cheap way to
catch them.

HAVING FINISHED the re-check, tell the author exactly one thing: the closing went through, press `/clear`.
Nothing else is required of him — the intake will start with his very next message, and what he sees will
already be the gate.
Until the switch, make no new decisions: the handoff is written, and anything you decide beyond it on a
filled context window will not get into it.

FLEXIBILITY: this is ordinary logic, not dogma; if the task does not fit — surface it and adapt, do not
autopilot.
