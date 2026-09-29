---
crate: crate.68986C3F88519008
title: bug - minting new host from BIOS creates bad starting page / incorrect room letter
status: open
kind: broken
reported: 2026-09-15
updated: 2026-09-15
by: Kitten
where: PocketGo BIOS / new host mint / room letter
---

# BIOS mint host - bad starting page / incorrect room letter

## Symptom
When minting a new host from the BIOS, PocketGo does not create a good starting page. It does it incorrectly. It tries to use tokens. The BIOS room letter does not work like that. The created room letter also ends up with front matter that does not belong.

## Expected
A newly minted host should get a correct starting page / room letter that follows how BIOS room letters actually work - not a token-based generation path that does not apply, and not misplaced front matter.

## Kitten detail (same dump, thickened)
- Incorrect starting page on mint
- Tries to use tokens; BIOS room letter does not work that way
- Front matter that does not belong

## Notes
Broken-bug (incorrect behavior). Related open: bios-room-letter-shell-scope (room letter scope vs shells). Parked for later Cursor harness. Soft-dump to Hop. Do not fix mid-session.