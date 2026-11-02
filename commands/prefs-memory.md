---
description: Manage stored user preferences (remember, show, forget)
allowed-tools: Read, Write, Bash
argument-hint: remember <pref> | show | forget <id-or-text>
---

Invoke the `prefs-memory` skill with this input: **$ARGUMENTS**

If $ARGUMENTS starts with `remember`, store the rest of the input as a
preference (`prefs.py set`, scope `always` unless the user says otherwise).
If it starts with `forget`, look up and remove the matching pref (show the
match first). Anything else is treated as a lookup: run `prefs.py list`
when empty, `prefs.py get <term>` when it names something.
