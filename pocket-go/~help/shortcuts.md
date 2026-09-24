---
title: Shortcuts
deck: LAN / sidecar keyboard opens
---

# Shortcuts

When you’re on the land setup (no ROM launcher trays), open sidecars with **Ctrl+Shift** (Mac: **Cmd+Shift**):

| tray | keys |
| --- | --- |
| **BIOS** | `Ctrl+Shift+B` (or **mypi:go** → BIOS in the IDE) |
| **Librarian** | `Ctrl+Shift+L` |
| **Charlie** (tags bay) | `Ctrl+Shift+C` |
| **Detective** | `Ctrl+Shift+A` |
| **TPS** | `Ctrl+Shift+T` |
| **Cards** | `Ctrl+Shift+D` |

Same chord again in an open sidecar closes that window.

**Ctrl/Cmd+S** inside BIOS keeps the active face (letter, page, coat, or help).

**Ctrl/Cmd+E** opens the room letter editor (Edit).

Hard-refresh (`Ctrl+Shift+F5` / the land refresh) if a tray script feels stale after a coat change.

**BIOS Crates** (FAB next to Hosts): search by title / path / hex and copy `crate.HEX` or `{{link:crate.HEX}}` without leaving the page.

## Bar words (Enter / GO!)

The jump bar is a nickname list. Type one word, hit Enter or **GO!**.

- Every room's folder name works: `codes`, `tags`, `detective`, `logger`.
- Extra spoken names live on that room in `~hosts/_hosts.yaml` as `bar:` (hunt is `bar: hunt` on detective; lore/cards land on trays).
- Built-in: `go` (Go lobby; `start` still works), `roam` (connected libraries), `recent` (last 25 notes).
- Full path still works: `go.codes/OT/001`. `roam.drop/` is a connected library.

Clay searches are the same idea as nicknames - a token you can plant. `{{tagsearch}}`, `{{codesearch}}`, `{{huntsearch}}`, `{{erasearch}}`, and `{{loresearch}}` work on any `.md`, not only their home bays. Map: Help → Tokens.

## Line breaks (letter / pages)

- **New paragraph:** leave a blank line between blocks.
- **Extra air:** stack more blank lines — each one keeps a visible gap (no longer collapses).
- **Soft break (same paragraph):** end a line with two spaces, then Enter — classic markdown `<br>`.
- Single Enter without the two spaces still shows as a line break in the BIOS letter printout (`pre-wrap`).

**Rename folder** — in BIOS next to + folder: renames the hall you are standing in. Crumbs and navbar follow the disk name; notes get a best-effort path rewrite.
