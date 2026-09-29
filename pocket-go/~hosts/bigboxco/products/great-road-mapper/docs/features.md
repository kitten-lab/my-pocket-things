---
kind: reference
order: 6
crate: crate.B160B0C0E0004B25
title: Features
deck: what the current product can do
product: Great Road Mapper
---

{{div:.bbc-kicker}}
products · great-road-mapper · docs · features
{{/div}}

# Features

Current features = what the shipping desk UI supports. The deepest product idea is documented under {{link:crate.B160B0C0E0004B26|Configurations}}.

## Configurations

- Templates: bins, workstreams, gate rules
- Variations: numbers-only children of a template
- Reverse-from-ship minting when a title gets a ship date
- Gate anchors to phase, workstream, or release (days or weeks)
- Blank template creation; spawn variation from template
- Ship-immovable mid-spine edits that cascade earlier

## Titles and schedule

- Create titles with code, optional name, product model, ship date, line
- Ship date reverse-fills model bins; blank ship = unscheduled until set
- Quarter follows ship date (or unassigned)
- Lifecycle states: Planning, Active, Scope change, Shelved, Cancelled
- Title drawer for detail work
- Optional twin / linked-title jumps when two titles share a story

## Phases, gates, workstreams

- Spine from product model
- Phase vs gate editing with required reason (change trail)
- Workstreams under phases
- In-desk edit modals

## People

- Roster
- Assign person to phase or workstream with role
- Crew cues on cards and in drawers

## Views and filters

- Board, List, Gantt (read-only), By quarter, Phases & gates, People, Configurations
- Filters: product line, schedule lane, lifecycle, multi-select quarters
- Light / dark theme
- BIGBOX / Road Mapper Deck Host chrome

## Storage

- Local `safe_box/roadmaps.json`
- Mausoleum folder for old import debris only

## Coming soon / ideas on the table

These are not live features:

- Treating this board as the company-wide system of record (another calendar may still be authoritative)
- Stronger import paths that do not leave mausoleum debris
- Anything not visible in the current tabs and modals

{{div:.bbc-go}}
{{link:crate.B160B0C0E0004B21|Overview}} · {{link:crate.B160B0C0E0004B26|Configurations}} · {{link:crate.B160B0C0E0004B22|Getting started}} · {{link:crate.B160B0C0E0004B12|Docs home}}
{{/div}}

{{div:.bbc-meta}}
Verified against product overview, README, UI source, and schedule/spine reverse-from-ship logic.
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
