---
kind: overview
order: 1
crate: crate.B160B0C0E0004B21
title: Overview
deck: what Great Road Mapper is and why it helps
product: Great Road Mapper
---

{{div:.bbc-kicker}}
products · great-road-mapper · docs · overview
{{/div}}

# Overview

## What Great Road Mapper is

Great Road Mapper is a **personal production board** for multi-title pipelines. It holds phases, people, and release-driven dates in one place so you can see the quarter without drowning in paste-wall schedules.

It sits in the Alice Box line under Big Box Company. The product code is `CO.BBC-001-GRM`. Company-wide adoption is optional — the board still works if only you use it.

## The problem it solves

Forward-built roadmaps are cognitively hostile when ship is the only date you truly know and every title needs the same multi-goal spine with different week lengths. Spreadsheets and Confluence force you to re-derive that spine under stress, then lose the reason when something slips.

Great Road Mapper’s answer is **Configurations**: reusable schedule machines that **reverse-fill from ship**. Templates own structure; variations own numbers; titles mint against a model. See {{link:crate.B160B0C0E0004B26|Configurations}}.

Around that:

1. Each game is a **title** with a code, optional name, product model, and ship date.
2. **Phases** and **gates** carry the spine; edits ask for a **reason**.
3. **People** pin from a roster onto a phase or workstream.
4. Views share filters — Board, List, Gantt, By quarter, Phases & gates, People, Configurations.

## Who it is for

You — the person who needs production visibility across a slate without holding every offset in your head. Another calendar may still be the official source of truth; this board is your readable strut.

## What you get out of it

- Complex roadmaps from one ship date
- Templates and variations instead of copy-paste boards
- Change reasons on schedule edits; ship-immovable cascades earlier
- Optional linked titles when two configs belong to one story
- Filters by line, schedule lane, lifecycle, and quarter

## How to open it

Preferred path: launch **Great Road Mapper** from Deck Host (ROM id `great-road-mapper`).

```bat
cd C:\ALICE_BOX\big-box-company\great-road-mapper\prod
run-grm.bat
```

- Port: **42960**
- Local data: `prod/safe_box/roadmaps.json` (gitignored)

{{div:.bbc-go}}
{{link:crate.B160B0C0E0004B26|Configurations}} · {{link:crate.B160B0C0E0004B22|Getting started}} · {{link:crate.B160B0C0E0004B25|Features}} · {{link:crate.B160B0C0E0004B12|Docs home}}
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
