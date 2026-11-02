#!/usr/bin/env python3
"""prefs.py: persistent, structured user preferences for ZCode sessions.

Store: ~/.zcode/prefs-memory.json (created 0600), shape:
    {"prefs": [{"id": "p001", "pref": "...", "scope": "always|code|comms",
                "added": "2026-11-02"}]}

Stdlib only. Works on macOS, Linux, Windows.

Subcommands:
  set <text> [--scope S]   add a preference; dedupes similar ones; cap 50
  get <id-or-text>         show matching prefs
  list                     show all prefs
  remove <id-or-text>      remove matching prefs
  export                   print a compact markdown block for prompt injection
                           (empty output when there are no prefs)

Exit codes:
  0  success (including no-op duplicate set, and empty export)
  1  no match for get/remove, cap reached, or invalid scope
  2  store file could not be read or written
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

CAP = 50
SCOPES = ("always", "code", "comms")


def store_path() -> Path:
    return Path.home() / ".zcode" / "prefs-memory.json"


def load() -> list[dict]:
    p = store_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: cannot read {p}: {e}", file=sys.stderr)
        sys.exit(2)
    prefs = data.get("prefs", [])
    if not isinstance(prefs, list):
        print(f"error: 'prefs' is not a list in {p}", file=sys.stderr)
        sys.exit(2)
    return [x for x in prefs if isinstance(x, dict)]


def save(prefs: list[dict]) -> None:
    p = store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"prefs": prefs}, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    os.replace(tmp, p)
    try:
        p.chmod(0o600)
    except OSError:
        pass


def next_id(prefs: list[dict]) -> str:
    highest = 0
    for x in prefs:
        m = re.fullmatch(r"p(\d+)", str(x.get("id", "")))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"p{highest + 1:03d}"


def norm(text: str) -> str:
    text = text.lower().strip()
    text = text.rstrip(".")
    return re.sub(r"\s+", " ", text)


def tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]{2,}", text.lower()))


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def contains_boundary(short: str, long: str) -> bool:
    # short embedded in long, with word boundaries on both sides:
    # "preference number 1" does not match inside "preference number 10"
    # (no boundary before the trailing "0"), but matches inside
    # "preference number 1." or "preference number 12 is wrong".
    return re.search(rf"\b{re.escape(short)}\b", long) is not None


def find_similar(text: str, prefs: list[dict]) -> dict | None:
    t = norm(text)
    for x in prefs:
        p = norm(str(x.get("pref", "")))
        if t == p:
            return x
        if len(t) > 8 and contains_boundary(t, p):
            return x
        if len(p) > 8 and contains_boundary(p, t):
            return x
    for x in prefs:
        if jaccard(tokens(t), tokens(str(x.get("pref", "")))) >= 0.7:
            return x
    return None


def cmd_set(args: argparse.Namespace) -> int:
    if args.scope not in SCOPES:
        print(f"error: --scope must be one of {', '.join(SCOPES)}", file=sys.stderr)
        return 1
    prefs = load()
    dup = find_similar(args.text, prefs)
    if dup is not None:
        print(f"already stored (similar): {dup.get('id')} :: {dup.get('pref')} "
              f"[{dup.get('scope')}]; skipped")
        return 0
    if len(prefs) >= CAP:
        print(f"error: cap of {CAP} prefs reached; remove one first "
              f"(prefs.py remove ...)", file=sys.stderr)
        return 1
    entry = {
        "id": next_id(prefs),
        "pref": args.text.strip(),
        "scope": args.scope,
        "added": datetime.date.today().isoformat(),
    }
    prefs.append(entry)
    save(prefs)
    print(f"stored {entry['id']}: {entry['pref']} [{entry['scope']}] "
          f"({len(prefs)}/{CAP})")
    return 0


def match(query: str, prefs: list[dict]) -> list[dict]:
    q = norm(query)
    out = []
    for x in prefs:
        if str(x.get("id", "")) == query:
            out.append(x)
            continue
        p = str(x.get("pref", ""))
        if q and (q in norm(p) or norm(p) in q):
            out.append(x)
    return out


def cmd_get(args: argparse.Namespace) -> int:
    hits = match(args.query, load())
    if not hits:
        print(f"no preference matches {args.query!r}", file=sys.stderr)
        return 1
    for x in hits:
        print(f"{x['id']} [{x.get('scope')}] (added {x.get('added')}): {x.get('pref')}")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    prefs = load()
    if not prefs:
        print("(no preferences stored)")
        return 0
    print(f"{'ID':<6} {'SCOPE':<7} ADDED        PREFERENCE")
    for x in sorted(prefs, key=lambda d: str(d.get("id", ""))):
        print(f"{str(x.get('id')):<6} {str(x.get('scope')):<7} "
              f"{str(x.get('added')):<11} {x.get('pref')}")
    print(f"\n{len(prefs)}/{CAP} prefs in use")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    prefs = load()
    hits = match(args.query, prefs)
    if not hits:
        print(f"no preference matches {args.query!r}", file=sys.stderr)
        return 1
    ids = {str(x.get("id")) for x in hits}
    save([x for x in prefs if str(x.get("id")) not in ids])
    for x in hits:
        print(f"removed {x.get('id')}: {x.get('pref')}")
    return 0


def cmd_export(_: argparse.Namespace) -> int:
    prefs = load()
    if not prefs:
        # Nothing to inject: stay silent so the hook adds no context.
        return 0
    lines = [f"**User preferences ({len(prefs)}):**"]
    for scope in SCOPES:
        in_scope = [x for x in prefs if x.get("scope") == scope]
        if not in_scope:
            continue
        lines.append(f"- {scope}:")
        for x in sorted(in_scope, key=lambda d: str(d.get("id", ""))):
            pref = str(x.get("pref")).replace("\n", " ")
            if len(pref) > 120:
                pref = pref[:117] + "..."
            lines.append(f"  - `{x.get('id')}` {pref}")
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="prefs.py",
        description="Persistent, structured user preferences in ~/.zcode/prefs-memory.json "
                    "(0600). Stdlib only.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("set", help="add a preference (dedupes similar ones, cap 50)")
    s.add_argument("text", help="the preference, in imperative form")
    s.add_argument("--scope", default="always",
                   choices=list(SCOPES),
                   help="always (every session), code (coding tasks only), "
                        "comms (how to talk to the user)")
    s.set_defaults(func=cmd_set)

    g = sub.add_parser("get", help="show prefs matching an id or text fragment")
    g.add_argument("query")
    g.set_defaults(func=cmd_get)

    l = sub.add_parser("list", help="list all stored prefs")
    l.set_defaults(func=cmd_list)

    r = sub.add_parser("remove", help="remove prefs matching an id or text fragment")
    r.add_argument("query")
    r.set_defaults(func=cmd_remove)

    e = sub.add_parser("export", help="print a compact markdown block for prompt "
                                      "injection (empty output when no prefs)")
    e.set_defaults(func=cmd_export)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
