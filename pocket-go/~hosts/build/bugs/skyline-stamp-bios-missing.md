---
crate: crate.B6F5189FDD44625D
title: bug - Skyline badge on wrong chrome (librarian, detective, etc.) instead of BIOS only
status: open
kind: broken
reported: 2026-09-15
updated: 2026-09-16
by: Cedric (scout) via Kitten; Kitten follow-ups
where: PocketGo BIOS / librarian / detective / room chrome
---

# Skyline approved badge - wrong homes / too many homes

## Symptom (original)
After install + PocketGo reboot, Kitten still does not see the Skyline stamp on Lenovo LAN client - neither inline cabinet nor popped-out window (where she wanted it: BIOS).

## Kitten realization (2026-09-15 evening)
The stamp that was supposed to end up on the BIOS is on the librarian instead. Wrong home / wrong chrome.

## Kitten expansion (2026-09-16)
It is also on the detective cabinet. It is like every room is Skyline approved. Kind of funny, but it is a bug - the badge is leaking onto cabinets / rooms that should not all carry it.

## What was done (from Cedric park)
- Asset landed: mats/imgs/skyline-approved-stamp.png (serves 200 at /i/skyline-approved-stamp.png)
- Thin hang: librarian.js injects .skyline-stamp img on catalog BIOS mast (beside title; Quire seal unchanged)
- CSS: .librarian .skyline-stamp in librarian.css
- Cache-bust ?v= on librarian.js/css in server.py; server bounced with GO_HOST=0.0.0.0 on :43210
- Live check from cave: librarian.js contains the stamp string; PNG serves

## Likely snags for whoever fixes
- Badge wired into shared mast / cabinet chrome so it appears on librarian, detective, and possibly other rooms - not scoped to BIOS-only
- Stamp may live in catalog / cabinet mast HTML branch that many rooms share
- LAN browser cache on the Lenovo may still hold old assets despite ?v=
- Popped cabinet may load under data-sidecar rules that omit or restyle mast chrome
- Transparent PNG + size may be easy to miss next to Quire larger seal when looking for it on BIOS

## Wanted
Visible small Skyline-approved mark on Pocket Internet BIOS chrome (inline + pop) where intended - not sprayed across librarian, detective, and every room. Also usable via /i/skyline-approved-stamp.png in places that should opt in.

## Notes
Broken-bug. Thickened in place - no new card. Kind of funny, still wrong. Parked for harness / BIOS owner - not scout coat work. Soft-dump to Hop.