# -*- coding: utf-8 -*-
"""Unfolds the swarm panel in the status line after every message from the author
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

def main(d):
    ctxlib.utf8_io()
    if ctxlib.cfg().get("panel_on_prompt", True) and not ctxlib.panel_on():
        ctxlib.panel_toggle()

    # The intake after a closing: SessionStart only puts the instruction into the context, while the
    # agent can start work only from a message. We duplicate the instruction into the very first
    # prompt — that way the intake starts regardless of what the author wrote.
    sid = d.get("session_id")
    st = ctxlib.state_load(sid) if sid else {}
    if st.get("pending_open"):
        ctxlib.state_save(sid, {"pending_open": False})
        pend = st.get("pending_open")
        sys.stdout.write(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext":
                "BEFORE answering this message: the previous session in this console was closed by "
                "the ritual, and the context was cleared for the sake of continuing. "
                + ctxlib.intake_body(pend)
                + ("" if isinstance(pend, dict) and pend.get("choices") else
                   " Verify what is written against reality and reach the gate, then answer.")
                + " If the message cancels the intake — obey it."}},
            ensure_ascii=False))


# stdin is a stream and it is read ONCE. Computing the argument of `shield` by reading
# it here drained the buffer before the body ran, and the body then saw an empty
# payload — the hook stayed alive, did nothing, and said nothing.
_D = ctxlib.stdin_json()
ctxlib.shield(lambda: main(_D), "panel", _D.get("session_id", ""), _D.get("cwd", ""))
