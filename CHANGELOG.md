# Changelog

## 0.1.0 - 2026-11-02

- Initial release: stdlib CLI (`set`, `get`, `list`, `remove`, `export`) over `~/.zcode/prefs-memory.json` (0600, capped at 50 prefs).
- Similarity dedupe on write: substring 8+ chars or word-token Jaccard >= 0.7 skips the duplicate.
- SessionStart hook injects the compact `export` markdown block as additionalContext, per scope groups.
- `remember` / `show` / `forget` workflows in the skill.
