---
kind: guide
order: 3
crate: crate.B160B0C0E0004B35
title: How it works
deck: cognitive problem · bins · stable part codes
product: sopr Documenter
---

{{div:.bbc-kicker}}
products · sopr-documenter · docs · how it works
{{/div}}

# How it works

## What was cognitively upsetting

You often know the scraps before you know the outline. Traditional doc tools punish that: they want a clean tree first, then content. When you are compiling something hard — platform story, GDD outline, product law — intake order lies, and rewriting structure by hand loses the leaves.

An older failure mode made it worse: encoding the **section into the fragment id**. Move the scrap to another bin and every reference wants a rename. Resort becomes terror instead of thinking.

## The idea in one sentence

**Dump under headers now. Resort until the outline stops lying. Part codes never rename.**

## The machine

| Piece | Job |
|-------|-----|
| Document bag (`.sopr`) | One topic, one outline-in-progress |
| Sections | Header bins with ordered `part_ids` |
| Parts (`SPR-####`) | Stable leaves — text, image, or table |
| Composer | Always top of the active bucket; stack grows downward |
| Resort | Re-bin and reorder only — membership and order, never identity |
| Print / reader | Honest outline view when you are ready |

Section membership is a **pointer**, not baked into the code. That is product law.

## Fragment types

- **Text** — the leaf scrap; optional monospace (`as_pre`) for ASCII or code
- **Image** — vault media under `safe_box/_media/` plus caption
- **Table** — text-only grid (header + rows); edit the full grid later

One leaf = one sopr. A note is another fragment (or another section), not a sidecar field on the same act.

## Loose / unbinned

Intake can sit loose until you place it. Print / reader skips Loose on purpose so the read-out is the outline you meant, not the junk drawer.

## Production chips (optional)

When Machina (glass) is corded, the desk can stamp **document-level** `tps_chips` — chip ids used while producing this doc. Deduped. Not per-fragment archaeology. Not on the compose chrome. See them under **Document → About this document…**. Product documentation tracking, not narrative bookkeeping.

## Why this improves the process

| Old pain | sopr answer |
|----------|-------------|
| Must outline before dumping | Dump first; outline emerges |
| Move = rename storm | Stable `SPR-####` identity |
| Chat heat as the store | `.sopr` bag on disk |
| Extra notes field muddies the leaf | Another fragment |
| Finish line unclear | Resort until honest, then Ctrl+3 |

{{div:.bbc-go}}
{{link:crate.B160B0C0E0004B36|Resort}} · {{link:crate.B160B0C0E0004B34|Getting started}} · {{link:crate.B160B0C0E0004B37|Features}} · {{link:crate.B160B0C0E0004B32|Docs home}}
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
