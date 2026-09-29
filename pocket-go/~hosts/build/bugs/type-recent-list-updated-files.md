---
crate: crate.69816B2A04E7D550
title: this-bugs-me - no way to type recent and list recently updated files
status: done
kind: this-bugs-me
reported: 2026-09-15
by: Kitten
where: PocketGo
---

# Type "recent" - list recently updated files

## Itch
It bugs Kitten that there is no way to type recent and get a list of all the recently updated files.

## Expected / wanted
A command / shortcut / surface where typing recent yields a list of recently updated files across the pocket (or current host scope - exact scope for harness to decide).

## Notes
Landed 2026-09-16. Lobby page `~hosts/recent.md`. Type `recent` on the bar. `{{recent}}` prints the last 25 kept notes and canvases (disk mtime) as jump links. Optional `{{recent:N}}`, cap 100.
