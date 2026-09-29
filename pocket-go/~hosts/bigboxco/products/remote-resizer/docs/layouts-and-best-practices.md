---
kind: guide
order: 3
crate: crate.B160B0C0E0004B45
title: Layouts and best practices
deck: open design · configure vs teach
product: Remote Resizer
---

{{div:.bbc-kicker}}
products · remote-resizer · docs · layouts
{{/div}}

# Layouts and best practices

**Coming soon design space.** Kitten has not locked this. Documenting the fork so we do not pretend it is settled.

## Why this matters

A dumb resize that only changes pixels will wreck game banners. Status, title/logo, character focal, and CTA need hierarchy that survives 320×150 and 1920×510 alike. House research already says what works and what fails (single focal read, quiet copy lane, logo clear of neck/face, one primary CTA).

Remote Resizer has to encode that somehow.

## Option A — Configure layouts

Operators define layout presets: safe zones, title band, status chip slot, CTA dock, crop priorities per aspect family (square / wide / skyscraper). Run uses the preset for each size class.

Feels like Big Box: explicit, editable, company-floor clear.

## Option B — Teach best practices

The allowed model is instructed (system / house pack) with the research rules and QA checklist. Less UI; more “it knows.” Harder to audit when a crop goes wrong.

## Option C — Both

Presets for geometry; taught rules for taste and failure modes. Likely where this lands, but not claimed as decided.

## What we will not do in docs yet

- Invent a live layout editor screen
- Claim the model already knows Betsoft-only lore as product law
- Bake competitor names into shipping identity (research notes can stay in the-marketeers)

When Kitten picks A, B, or C, this page gets rewritten as product law.

{{div:.bbc-go}}
{{link:crate.B160B0C0E0004B44|How it works}} · {{link:crate.B160B0C0E0004B46|Planned features}} · {{link:crate.B160B0C0E0004B42|Docs home}}
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
