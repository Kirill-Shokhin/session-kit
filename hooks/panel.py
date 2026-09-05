# -*- coding: utf-8 -*-
"""Unfolds the swarm panel in the status line after every message from the human
(UserPromptSubmit, without blocking).

Intercepting the /pulse command and answering it here was tried twice. Both times it ran into the
same thing: a prompt can be stopped only with exit code 2, and that makes Claude Code print a
system frame with the paths to the interpreter and the hook. Blocking by a decision in JSON
(permissionDecision: deny) does not stop the prompt — the command reaches the model and costs
tokens. Zero tokens and clean output are unreachable at the same time, so there is no command at
all: the panel shows itself.
"""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "kit"))
import ctxlib  # noqa: E402

ctxlib.utf8_io()
d = ctxlib.stdin_json()
if ctxlib.cfg().get("panel_on_prompt", True) and not ctxlib.panel_on():
    ctxlib.panel_toggle()

# The intake after a closing: SessionStart only puts the instruction into the context, while the
# agent can start work only from a message. We duplicate the instruction into the very first
# prompt — that way the intake starts regardless of what the human wrote.
sid = d.get("session_id")
st = ctxlib.state_load(sid) if sid else {}
if st.get("pending_open"):
    ctxlib.state_save(sid, {"pending_open": False})
    stream = st.get("pending_open")
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext":
            "BEFORE answering this message run Skill(skill=\"open\"%s): the previous session in "
            "this directory was closed by the ritual, and the context was cleared for the sake of "
            "continuing. Accept the handoff, verify what is written against reality and reach the "
            "gate, then answer. If the message cancels the intake — obey it."
            % ((" with the stream \"%s\"" % stream) if isinstance(stream, str) else "")}},
        ensure_ascii=False))
