# Prefs Memory

The preferences you tell ZCode once stick: stored as structured records and re-injected at the start of every session.

## Why

You keep repeating yourself: "stop auto-committing", "keep replies short", "always use pnpm here". Without a store, every new session starts amnesic and you lose ten minutes to the same re-briefing. Prefs Memory keeps a small, versioned (by id and date) list of standing instructions in one 0600 JSON file and injects it automatically, so a preference stated once applies to every future session.

## How it works

| Piece | What it does |
|-------|--------------|
| Store | `~/.zcode/prefs-memory.json` (created 0600): `{"prefs": [{"id","pref","scope":"always\|code\|comms","added"}]}`, capped at 50 entries |
| CLI | stdlib `scripts/prefs.py`: `set`, `get`, `list`, `remove`, `export` |
| Dedupe | `set` skips an entry when the new text matches a stored one (substring 8+ chars, or word-token Jaccard >= 0.7) |
| Skill | `remember <pref>` / `forget <id-or-text>` / `show` workflows over the CLI |
| Hook | SessionStart (matcher `startup\|clear\|compact`) runs `prefs.py export` |

### Exactly what the hook injects

The hook runs:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/prefs-memory/scripts/prefs.py export
```

If the store is empty, `export` prints nothing and the hook adds no context.
Otherwise it prints a compact markdown block, grouped by scope, one line per
pref, pref text truncated to 120 chars:

```
**User preferences (3):**
- always:
  - `p001` Never auto-commit or push; leave the working tree for me to review
  - `p002` Keep replies under 5 paragraphs
- code:
  - `p003` Use pnpm in this repo, not npm
```

ZCode attaches that stdout as additionalContext for the session. It is kept
small on purpose: no explanation, no ids of non-matching scopes, each line
capped. The block is regenerated from the store on every session start, so
`forget` takes effect from the next session.

## Install

Option A, self-installable marketplace:

1. Download or clone this repo to a folder.
2. In ZCode: Plugin Marketplace, Add, Add Plugin Marketplace, paste that folder path.
3. Install Prefs Memory.

Option B, manual:

Copy the `prefs-memory/` folder into your workspace `plugins/` directory.
The hook only fires once the plugin is registered; the CLI works either way.

## Try it

```
remember Always run `make check` before reporting a fix as done
/prefs-memory show
```

Expected: the first stores `p001` under scope `always` and prints the id and
count; the second lists it. At the next session start the injected context
contains the `User preferences (1)` block.

## Requirements

Python 3 (stdlib only). macOS, Linux, Windows.

## Honest limits

Within the current session, honoring a pref you just added is on the agent; the store only re-injects from the next session start. Similarity dedupe is text-based, so
two words-that-mean-the-same prefs both survive until you `forget` one.
The store is per-machine; copy the JSON to move it.

---

<p align="center">
  <a href="https://z.ai/subscribe?ic=R0K78RJKNW"><img alt="z.ai coding plans - 10% OFF coupon" src="https://img.shields.io/badge/z.ai%20coding%20plans-10%25%20OFF%20coupon-blueviolet" /></a>
  <a href="https://zcode.z.ai/invite/ALWM9JUA"><img alt="Try ZCode free" src="https://img.shields.io/badge/Try%20ZCode-free%20invite-0969da" /></a>
</p>

## License

MIT.
