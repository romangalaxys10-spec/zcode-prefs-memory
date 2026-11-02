---
name: prefs-memory
description: "Persistent, structured user preferences applied to every ZCode session. Use when the user states a lasting preference ('always X', 'I prefer Y', 'never Z', 'remember that ...') and it should survive across sessions; when the user asks to see, edit, or drop stored preferences ('show my prefs', 'forget that', 'what do I always tell you?'). The SessionStart hook already injects stored prefs, so this skill manages the store, it does not re-announce them."
---

# Prefs Memory

Store: `~/.zcode/prefs-memory.json` (created 0600). Shape:

    {"prefs": [{"id": "p001", "pref": "...", "scope": "always|code|comms",
                "added": "2026-11-02"}]}

The stdlib CLI is `scripts/prefs.py` (relative to this skill dir). A
SessionStart hook runs its `export` subcommand, so stored preferences load
into the session automatically; the skill below manages the store.

## Workflows

### remember <pref>

When the user states a lasting preference:

1. Pick the scope:
   - `always` (default): behavior that applies no matter the task.
   - `code`: applies to coding tasks only (style, review, tooling).
   - `comms`: how to talk to the user (tone, length, language).
2. Run:

       python3 scripts/prefs.py set "the preference" --scope always

   Write the pref text in imperative form ("Use tabs for new Rust files"),
   short, one line. The script dedupes: an identical or near-identical
   preference (substring of length 8+, or Jaccard >= 0.7 on word tokens)
   is reported as already stored and skipped, so repeats do not pile up.
   "Similar" means: identical, one text embedded in the other with word
   boundaries (8+ chars, so "number 1" does not match inside "number 10"),
   or word-token Jaccard >= 0.7.
   The store caps at 50 prefs; when the cap is hit the script exits 1 and
   tells you to `remove` one first.
3. Report the id and current count the script printed. If it deduped, point
   the user at the existing id.

### show

Either request:

       python3 scripts/prefs.py list

or a targeted lookup:

       python3 scripts/prefs.py get "framing"

Present the result as-is; do not editorialize. Empty store: say so in one
line.

### forget <id-or-text>

1. Preview with `python3 scripts/prefs.py get <query>` so the user sees
   exactly which prefs match.
2. On confirmation, run `python3 scripts/prefs.py remove <query>`.
   Matching accepts an exact id or a text fragment; when more than one pref
   matches, show all of them and ask which to drop before removing.

## Guardrails

- One preference per call. "Always keep replies short and use British
  spelling" is two prefs: store them separately so `forget` can drop one.
- No secrets in the store. A pref that names an API key value is rejected
  at capture time; store the env var name instead.
- The store is per-machine at `~/.zcode/prefs-memory.json`. It does not
  sync between machines; copying the JSON file is a supported manual path.

## Honest limits

Similarity detection is text-based: exact match, word-boundary containment
(8+ chars), or Jaccard >= 0.7 on word tokens. Two prefs that mean the same
thing but use different words are not deduped; that is the user's call when
reviewing `list`. The hook injects the prefs block at
SessionStart; prefs set mid-session apply from the next session's start,
and the agent should still honor them immediately in the current one.
