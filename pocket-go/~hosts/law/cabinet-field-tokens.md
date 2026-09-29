---
crate: crate.0C9928C0779D4519
title: cabinet field tokens
---

# cabinet field tokens

Agreed 2026-09-10.

## what

Compose clay from **this page's** cabinet shelves — one filed label at a time — so artifacts stay consistent without copying meta into page headers.

## tokens

| token | reads |
|---|---|
| `{{lib:label}}` | Librarian field `label` on this page |
| `{{agt:label}}` | Agent field `label` on this page |
| `{{librarian:label}}` | same as lib |
| `{{agent:label}}` | same as agt |

Missing label → blank (no leftover braces). Several values → joined with `, `.

## still separate

- `{{meta}}` / `{{chips}}` / `{{meta:agent}}` — full chip dump of that mouth
- page YAML `{{the-key}}` — headers on the note only
- Charlie — not in this law (weave, not artifact clay)
- TPS — stubbed for later (`{{tps:title}}` when we need stamps in prose)

## practice

File truth in Librarian / Agent. Print it into the page with lib/agt. Change the cabinet; the artifact follows.
