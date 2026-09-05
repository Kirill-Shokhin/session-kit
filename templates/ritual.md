# The session ritual of this project

This file is read by the `open`, `close`, `mark`, `pin` skills. It describes the layout of THIS
repository in particular — the skills themselves are project-neutral. Fill it in with facts, not with
intentions: a wrong field here means a ritual performed past the mark.

## Levels of knowledge

- PUBLIC (results, conclusions, boundaries; zero process):
  - `README.md`
  - <the main document of the project and its companions>
- SESSION-LEVEL (state, the unfinished; in the repository, but not announced):
  - <what is here>
- The agent's MEMORY (behavior, bayes, process — not the course of the project):
  - `~/.claude/projects/<project>/memory/` + `MEMORY.md` as the index

## The main document

The one that is read at the opening WITH YOUR OWN EYES before anything else:
- <path> — <why the agent invents things without it>

## The journal and the session archive

- The current session's journal: `.claude/journal/<YYYY-MM-DD>-<slug>.md`
- The archive of closed sessions: `.claude/sessions/<date>-<stream>/` — handoff, DAG, journal
- The index: `.claude/sessions/INDEX.md`, the newest entry on top, with the stream's name
- By default a new agent reads ONLY the last entry. Deeper — on the author's instruction ("read the
  last five DAGs"), when the agent starts stepping on the same rake over and over.
- The archive is not retired: it is provenance, not a draft.

## Streams

Logically independent directions of work. Each has its own handoff and its own archive; the author
maintains the separation, the agent's job is not to confuse its own stream with someone else's. The
stream's name is passed in `/open <stream>`.

- <name> — <its files, branch or worktree, what it works on>

The freshest file or commit does NOT mean "mine": streams run asynchronously and may live in
different worktrees. A project with a single orchestrator is a special case: there is one stream, and
the field is filled in with its name.

## The pinned version

- `.claude/BASELINE.md` — the last version the author checked by hand.
- Everything that landed after the mark is a draft, including the work of past sessions.
- Advancement is measured from the mark. Curing the noise introduced by agents after it is not an
  achievement.
- It is set by the author only, through the `pin` skill.

## Baseline checks

What reality is checked with at the opening (the commands that must work):
```
<tests / build / run>
```

## Commit and push

- Commit, amend, squash: <freely, without asking — the history is kept logical>
- Message style: <public, about the result, without process>
- **Push: <FORBIDDEN without the author's permission | ALLOWED, agents keep the repository themselves>**
  Forbidden by default: incremental noise must not travel out past the versions the author expects.

## The gate

What the author expects at the stop before continuing:
- <the verified state, the divergences, the unverified, which mark the count runs from, the plan>
