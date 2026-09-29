---
crate: crate.652F0580BAED0095
title: bug - clay {{link:crate...}} tokens resolve as no crate on Lenovo client
status: open
kind: broken
reported: 2026-09-16
by: Skyline via Kitten
where: Pocket Go clay links / Lenovo client; go.skyline mornings/2026-09-16 and evenings/2026-09-15
---

# Clay crate-link tokens show "no crate" on Lenovo

## Symptom
Skyline stamped morning/evening letters with {{link:crate.XXXX|label}} doors (per KEYS / ~help/tokens). On the Lenovo client they all resolve as "no crate" instead of opening the target page.

## Where
- go.skyline mornings/2026-09-16
- go.skyline evenings/2026-09-15
- Links section of those letters

## Examples that failed for Kitten
- crate.682A8182EF84BBAA (skyline)
- crate.D1CC1274060D2A41 (poet)
- crate.4E5678372ED9B4FD (mythleak)
- crate.B6F5189FDD44625D (stamp bug note)

## Context
- Classic Markdown [go.x](go.x) also does not parse (expected).
- Wiki [[same-host]] may be fine.
- The broken ones are the cross-host {{link:crate...}} tokens.

## Wanted
{{link:crate.XXXX|label}} doors open the target page on the Lenovo client instead of showing "no crate".

## Kitten theory (soft, via Skyline)
"no crate" may be because outbound {{link:crate...}} doors pointed at _index.md shell crates, not the page / index.md fill crates. Underscore index is the shell (poorly named); doors should hit the page, not the shell.

Skyline is reverting those stamped letters to readable Markdown [go.x](go.x) for now so labels stay visible. Theory parked here for harness - no fix from Skyline/Hop.

## Notes
Broken-bug. Kitten said she does not know what to do with it and asked Skyline not to get technical - parked with Hop / harness. Soft ask from Skyline. Do not fix mid-session.