# session-kit

A kit for Claude Code that closes a session before the agent starts making mistakes, and opens the
next one on an assembled handoff.

The cycle "closed the session — opened a clean agent" is reliable exactly up to the point where the
moment of closing is decided by a human. What is automated here is the moment, not the ritual: the
session announces on its own that it is time to close, and does not let the agent go until the
handoff is assembled.

Compaction is not used: a clean agent on a handoff works better than a compacted one, costs less, and
a closed session stays in the history and remains available for `--resume`.

Switching sessions stays with the human — one keystroke, `/clear`. It cannot be removed entirely in
an interactive console, and that is a platform limitation, not an omission: see [Why one keystroke
remains](#why-one-keystroke-remains).

## Installation

```bash
git clone https://github.com/Kirill-Shokhin/session-kit ~/.claude/kit
python ~/.claude/kit/install.py
```

Requires Python 3.8+, nothing else. Restarting Claude Code after installation is not necessary: it
re-reads the settings by itself.

```bash
python ~/.claude/kit/install.py --update              # pull a fresh version and reinstall
python ~/.claude/kit/install.py --publish "what changed" # send your edits to the repository
python ~/.claude/kit/install.py --dry-run             # see what would be done
python ~/.claude/kit/install.py --soft 60 --hard 75   # your own thresholds
```

The installer puts the skills into `~/.claude/skills`, merges the status line and five hooks into
`~/.claude/settings.json`, disables auto-compaction and runs a self-check. Existing settings are
preserved, the file is backed up before editing, other people's hooks are left alone. The absolute
path to the current interpreter is written into the settings, so on a new machine run the installer
with whatever python is there, and do not copy `settings.json` by hand.

## The session cycle

```
work … 75% … the watchdog does not let go
  → close          the agent writes the handoff, the DAG, the journal, commits, silences the watchdog
  → recheck        the watchdog demands one pass over what it wrote itself
  → /clear         the human clears the context
  → any message    the intake wedges in ahead of the reply to it
  → GATE           the human checks the restored state and the plan
```

The human has two actions: `/clear` and a message. There is nothing to remove the second one with —
only a message starts the agent, and no other way to begin its turn exists.

The point of the automation is that the second action stopped being a chore. It used to be spent on a
ritual command (`/open`); now it is an ordinary remark on the matter at hand — "let's continue with
task such-and-such" — and the intake wedges in ahead of the reply to it. After `/clear` a hook marks
the session as awaiting intake, prints a hint on the screen and duplicates the instruction into the
first prompt. If the message itself cancels the intake ("no intake, just answer"), the agent obeys
the human.

The second action stays empty in exactly one case: when only the gate is needed and nothing else.
Then writing "go" is enough.

## Why one keystroke remains

Only a human can clear the context and continue the work. Checked against the documentation and live:

- **hooks** can neither clear the context nor start the agent's turn. `Stop` with code 2 continues a
  turn already under way, but does not begin a new one; `SessionStart` puts text into a context that
  nobody will read until the human writes a message;
- **slash commands** (`/clear`, `/compact`, `/fork`, `/rewind`) are recognized only at the start of a
  human's message — the agent cannot invoke them;
- **key bindings** are assigned only to built-in actions, and there is no "clear the context" action
  among them;
- **auto-compaction** does both by itself, but is no good as a switch: to reach its threshold the
  context window would have to be padded artificially, the ritual might not make it in time — and
  compaction would eat what was not written down, producing exactly the false session this whole
  thing was set up against; and if the work stalls before the threshold, compaction never comes at
  all.

A fully autonomous cycle is possible outside the interactive console — under an external orchestrator
on the Agent SDK or `claude -p`, where the context reset is done by the wrapper code. The price is
that the work stops happening in a live dialogue.

## How it works

1. **The status line** receives ready-made `context_window.used_percentage` and
   `context_window_size` from Claude Code (it knows about the 200k and 1M windows) and on every tick
   drops a snapshot into `~/.claude/ctx/<session_id>.json`. It shows the fill level of its own
   window, the swarm — the other live sessions — and the subscription limits: the five-hour and the
   weekly one, with a pace cursor.

   The cursor `│` marks the share of the window until the reset that has already passed, and is drawn
   in a separate color on top of the bar — otherwise it would blend into the spend wherever it lands
   on it. Filled area **beyond** the cursor means overspending: the limit will run out before it
   resets. The weekly window has only days in its tail: hours are not needed there, and the extra
   characters make the terminal truncate the line.

   A command appears in the line ONLY when an action is required from the human, and there is exactly
   one such moment: `closed → /clear`. Below the threshold the line stays silent, above it shows the
   `closing` state — that is the agent's work, not an invitation to press anything. The ritual and
   the journal are kept by the agent, on the watchdog's instructions.

   The swarm panel unfolds **by itself after every message** and stays for 15 seconds. There is
   deliberately no separate command for it: a hook can stop a prompt only with exit code 2, and that
   makes Claude Code print a system frame with paths; blocking via a decision in JSON does not stop
   the prompt at all. Zero tokens and clean output are simultaneously achievable only without a
   command.

2. **The context window watchdog** (a `Stop` hook) fires when the agent has finished a reply — that
   is, at a micro-task boundary. Every +10% of fill it reminds you to go over the list of forks and
   write what happened into the journal; nothing happened — no entry. At 60% it demands that no new
   branches be started. At 75% it returns code 2 and does not allow a stop until the `close` skill
   has been executed.

   The watchdog does not block the human's question and does not interfere with the reply — it
   prevents the agent from STOPPING after the reply. That is why "answer me, then close" works by
   itself, and there is no need to write it.

   A refusal ("hold on, finish this first") is respected **by deferral, not by capitulation**: the
   watchdog stays silent until the window grows by `snooze_pct`, and then demands again — the more
   insistently the closer the limit is (5% up to 85, 2% up to 92, after that almost every reply). It
   goes quiet for good only after the ritual has been performed: otherwise a pair of "got it, ok"
   would cost the closing altogether.

   If the status line did not do its job, the fill level is computed straight from the transcript:
   `input + cache_creation + cache_read` of the last non-sidechain assistant record.

3. **After the ritual comes one recheck pass.** The handoff was assembled on a full window, and
   things left unwritten systematically remain in it; the watchdog forces a re-read of what the agent
   wrote itself, through the eyes of the one receiving it, and a silent fix of whatever is found.

4. **The watchdog does not touch subagents** (the hook input carries `agent_id`). They are executors
   of subtasks: they write nothing out, go through no rituals, and their window is the concern of
   whoever called them. Their fill level is visible in the swarm line under each task.

5. **A trail is written** into `events.jsonl`: every nudge, threshold, stop and closing. Without it a
   crooked wording pushes in the wrong direction silently — the firings happen with no human present.
   An agent that ran into friction writes a line into `FEEDBACK.md`, and `kit-review` goes through
   what has accumulated and proposes edits. If there was a stop and no closing followed it, a red
   `!N` appears at the end of the swarm line — that is a defect in the wording, not an accident.

6. **Auto-compaction is disabled** (`autoCompactEnabled: false`). It masks the overflow, and a masked
   overflow is exactly what makes the agent quietly get worse. If compaction happened anyway,
   `SessionStart` looks at the trail: was there a ritual. There was — it orders the agent to accept
   the handoff and not to trust the digest; there was not — it orders an emergency close, because
   causality has already been lost.

## Rules and the working mode

The kit puts a block between the `session-kit:rules` markers into `~/.claude/CLAUDE.md` — the rules
that travel with it to other machines. Personal rules next to it are not touched; make edits in
`kit/rules/global.md`, the installer will carry them over.

The working mode is injected at the start of every session and is switched with a single lever:

```bash
python ~/.claude/kit/bin/ctx.py mode            # which mode is on now
python ~/.claude/kit/bin/ctx.py mode autonomous # the agent decides itself, brings back verified work
python ~/.claude/kit/bin/ctx.py mode stepwise   # the human verifies every step
```

**Autonomous mode** (the default) rests on two rules.

*Whose question is this* — before asking the human, run the question through two branches:
**not derivable** (an input, an axiom, a product promise) or **requires the person themselves**
(their hands, their eyes, a judgement only they can make, their accounts, their money). Hit neither — the question is struck out, the agent makes the decision, and a
line "did it this way because" goes into the report. This applies to the large and the irreversible
as well: large and reversible is done with a note on how to roll it back; large and irreversible is
made reversible instead of being turned into a question. Internal technical forks do not belong to
the human — they do not know about them and should not.

*Done = passed the critics* — before saying "done", the agent runs a fresh critic with no context to
convergence. The human sees the result of a consensus, not the moment when it seemed to the agent
that the work was over. The watchdog checks this: declaring readiness without a credited check stops
the agent once and sends it back to the critics.

**Stepwise mode** — for meager limits, when there are no parallel streams and the human's resource is
cheaper than autonomy: the agent presents every step, brings out the forks, the critic gate is off —
the human checks. The lever swaps the body of rules whole, rather than leaving both in the context.

## Skills

| skill | when | what it does |
|---|---|---|
| `open` | first in a new session | shift onto the project's language, intake of the last handoff and DAG, **verification of what was written against reality**, counting from the pinned version, plan, gate |
| `mark` | at the moment of a fork | one entry in the current session's journal: what was discarded and what refuted it, what was decided, a measurement, a divergence, the author's intent |
| `close` | on the watchdog's demand | laying knowledge out by levels, an equivalence test, a causal DAG with negative edges, separating advancement from curing one's own noise, a vector forward, cleanup, commit |
| `pin` | when a version is worth checking by hand | diff from the previous mark, three buckets (planned / housekeeping / surfaced along the way), a check by a fresh critic, presentation to the human, a new mark |
| `kit-review` | once every few sessions | a review of the kit itself, by the watchdog's trail and the friction entries |

### The law of the version — what `pin` is for

Between two marks lie a dozen sessions. Each introduced noise and cured someone else's, each measured
itself from its own beginning and reported advancement. The sum of such reports does not equal the
change of the version: it is inflated and biased towards whatever surfaced along the way. Ten
sessions later you get a different product with a full sense of progress. That is why `open` and
`close` count advancement from `.claude/BASELINE.md` — from the version the human checked by hand —
and do not count agents curing their own noise as an achievement.

## A new project — nothing needs to be set up

The kit is global: the watchdog, the status line and the skills work in any directory right after
installation.

The project frame (`.claude/ritual.md`) is created by itself: `open` in a project without one goes
through the repository, fills in with facts everything that can be established by reading, and asks
the human, in a single message, only what cannot be derived from the repository — which document is
the main one here, whether push is allowed, what the streams are, what counts as the last verified
version. Until the answers arrive the defaults hold: push is forbidden, there is one stream, the
count runs from the current HEAD as a draft. `.claude/BASELINE.md` appears at the first pinning of a
version by the `pin` skill.

## What is inside

```
kit/
  ctxlib.py              window state: where it lies, how it is read, how it is computed
  view.py                how the swarm state and the watchdog trail are drawn
  install.py             installation, updating and publishing of edits
  config.json            this machine's thresholds (created by the installer)
  events.jsonl           the trail of watchdog firings (created by itself)
  FEEDBACK.md            friction entries about the ritual (created by the installer from a template)
  hooks/
    guard.py             Stop: reminders, the stop at the threshold, the recheck after the ritual
    panel.py             UserPromptSubmit: unfolds the swarm panel
    sessionstart.py      SessionStart: tells the agent its sid, starts the intake after /clear
    sessionend.py        SessionEnd: removes the state of the finished session
    precompact.py        PreCompact: marks the session as compacted
  statusline/
    statusline.py        status line: own window, swarm, subscription limits
    subagent.py          a line for each subagent with its own percentage
  bin/
    ctx.py               the same data from an ordinary terminal, outside Claude Code
  rules/                 global.md (goes into CLAUDE.md), autonomous.md, stepwise.md
  skills/                open, close, mark, pin, kit-review
  skills-local/          personal layer: glossary and own skills (does not go to the repository)
  templates/             ritual.md, BASELINE.md, FEEDBACK.md
```

## Configuration

`~/.claude/kit/config.json`:

| key | default | meaning |
|---|---|---|
| `soft_pct` | 60 | do not start new branches, record the forks |
| `hard_pct` | 75 | stop until `close` has been performed |
| `snooze_pct` | 5 | by how many percent of the window the watchdog goes quiet after a refusal |
| `nudge_from` | 20 | from which fill level to start reminding about the journal |
| `nudge_step` | 10 | and after what increment of the window to repeat |
| `stale_sec` | 600 | older than this, a reading is marked as "asleep" |
| `hide_sec` | 120 | older than this, a session is considered closed and is not shown |
| `panel_sec` | 15 | how many seconds the unfolded swarm panel stays |
| `panel_on_prompt` | true | whether to unfold the panel after every message |
| `regate_pct` | 10 | window growth after which the critic gate is armed again |
| `mode` | autonomous | which body of rules is injected: `autonomous` or `stepwise` |
| `fallback_window` | 200000 | window size if it was not reported (can be set via `CLAUDE_CTX_WINDOW`) |

The closing itself costs 1–5% of the window, so the reserve from 75% is more than enough: the
threshold was chosen for the sake of the quality of judgment, not for the room the ritual takes.

## The personal layer

Everything that pertains to a particular human and their projects does not go to the repository and
is listed in `.gitignore`: the thresholds, the trail of firings, the friction entries, the session
journals, the filled-in project frames and the `skills-local/` directory.

`skills-local/` is the personal layer, arranged in two ways:

- **`glossary.json`** — a substitution glossary, "public wording → personal one". The installer
  applies it to the already installed skills, so the repository holds depersonalized text while the
  work runs in your own language. A glossary precisely, not copies of the files: a copy falls behind
  with every edit of the public skill, and the divergence grows silently. The order of the pairs
  matters — long ones before short ones.
- **Skill directories** that have no public counterpart at all. They are installed as they are, on
  top of the public ones.

## The data from an ordinary terminal

```bash
python ~/.claude/kit/bin/ctx.py          # a table of live sessions and limits
python ~/.claude/kit/bin/ctx.py watch    # the same, refreshed every 5 seconds
python ~/.claude/kit/bin/ctx.py log 60   # the latest watchdog firings
python ~/.claude/kit/bin/ctx.py stats    # how they ended
python ~/.claude/kit/bin/ctx.py clean    # remove session files older than a day
python ~/.claude/kit/bin/ctx.py done <sid>   # silence the watchdog by hand
```

Inside Claude Code this is not needed: the swarm is visible in the status line, and the alarm comes
as the `!N` mark.

## Debugging

```bash
echo '{"session_id":"t","model":{"display_name":"O"},"workspace":{"current_dir":"."},"context_window":{"total_input_tokens":150000,"total_output_tokens":2000,"context_window_size":200000,"used_percentage":76}}' | python ~/.claude/kit/statusline/statusline.py
echo '{"session_id":"t","hook_event_name":"Stop"}' | python ~/.claude/kit/hooks/guard.py; echo "code $?"
```

Code 2 from the watchdog is normal, that is how it stops the agent. `claude --debug` shows that the
hooks really are being called. The watchdog stays silent if the session is marked as closed — the
mark can be removed by deleting its file in `~/.claude/ctx/`. The subscription limits appear only for
Pro and Max subscribers and only after the model's first reply in the session.

## How to turn it off

Remove the `statusLine` and `subagentStatusLine` keys and the hooks with `kit/hooks/` paths from
`~/.claude/settings.json` — or restore the `settings.json.bak-*` backup. The skills will remain and
will keep working by hand.

## License

MIT.
