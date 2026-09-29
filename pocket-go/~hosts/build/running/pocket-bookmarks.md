---
crate: crate.A35C72FF1866B972
title: In-pocket bookmarks bar
status: shipped
captured: 2026-09-13
environment: build-desk
section: running
---

# In-pocket bookmarks bar

## Lived example (2026-09-13)
Mausoleum (old kitten-lab files) → classify → go.journal/developer → piece is AIDM-quality → copy crate → go.build/AIDM plant face → back to developer journal mark outported + link crate → back to mausoleum for next file. Too much hallway.

## Pain
Beside cabinets, the bigger frustration is **walking**: inside build, cannot quick-jump to the dev journal and back; working AIDM means too much hallway between rooms.

## Why not real browser tabs
Real tabs break cabinet focus — cabinets do not know which browser window/tab to target. The tab/bookmark system has to be built **into the pocket**.

## Shape
A quick bookmarks bar (jump rail) for pinned pocket paths — build, journal, AIDM, running, etc. — so deep work stays one window with fast room-hopping.

## Kin
Pairs with master cabinets sheet: cabinets = faculty voices; bookmarks = room doors you keep under your thumb.

## Shipped MVP (2026-09-13)
- Star **pin button** on the link-bar rail (with back/home/refresh) — pins/unpins the *current page* (not host-only start pins)
- Thin sticky **jump bar** under the URL chrome with chips; click to hop same-window; × removes
- Seeded defaults: mausoleum, developer journal, AIDM, running
- Stored in browser localStorage (pocket-go-jumps-v1) so it stays with this Chromium profile

