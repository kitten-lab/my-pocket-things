---
crate: crate.E392F2087DF11714
title: Person crate cites
status: PLAN
captured: 2026-09-15
environment: build-desk
section: running
related: [go.cast]
---

# Person crate cites

**Status:** PLAN - Kitten + Quire, 2026-09-15

## Problem
We want real names on Cast faces *for now*, and later the option to flip a person to a code name everywhere - without hunting every string. Renaming the spoken word in every leaf is the wrong spine.

## Vocabulary
- **Venn code** - human-stable person/project code stamped on the Cast (and later across ABC projects). Example: `SDK-808` for Sam Ra-Rosewater (narrative character). Format lives as a field on the Cast leaf (e.g. `venn: SDK-808`), not as the only id.
- **Venn chip** - the insert/print face that cites a Venn code (or its crate) and **renders the current Cast title** when meta/body prints.
- **crate.XXXX** - machine spine under the Venn code. Permanent. Edges, lore, cabinets, and `{{face:crate.}}` already speak crates.

Everybody in Cast gets a Venn code. Over time Venn codes normalize across Alice Box / ABC projects - same habit for people, eventually for more node kinds.

## Spine
1. Each person / archetype = a **Cast leaf** under `go.cast` with permanent **`crate.XXXX`** *and* a **Venn code** (`SDK-808` style).
2. Cast **title** = **print face** only - real name today, code name tomorrow. Title can change; crate and Venn code do not (unless you deliberately retire a code).
3. Durable references hang on **crate** and/or **Venn code**, never on the display string alone.
4. When a **Venn chip** / meta insert prints, resolve Venn code (or crate) to **current Cast title**. Flip the title once; every chip reprints the new face.
5. Old body strings that typed a name stay historical unless rewritten. New writing prefers Venn chips / crate cites.

## What already exists
- Cast leaves with crates (Shane, Andy, Sid, Katie, Elon figure, ...)
- Host `aliases:` for spelling / Charlie prints (not separate people)
- Edges / lore `source_crate` / crate report doors / `{{face:crate.}}`
- Name Game stays **Agent** (what the name is doing), not Cast title
- Tag word-crates may edge the Cast figure; they are words, not people
- Precedent: `SDK-808` as a Venn code for Sam Ra-Rosewater

## Unpaid (coat / engine)
1. **Venn chip render** - type/paste `SDK-808` (or pick from Cast) and print shows current Cast title in body / meta.
2. **Venn field on Cast** - Librarian pot + host FM: `venn: SDK-808` mapped 1:1 to that leaf crate.
3. Lookup: Venn code -> crate -> current title (and reverse).

Nice later: Cast title edit warns "print face only - cites are Venn/crate."

## Practice until the chip exists
- Cast titles may stay real names
- Mint/stamp `venn:` when a face is ready (start with known ones like SDK-808 when Sam lands in Cast)
- Grow `aliases` on the leaf
- Green pots: prefer crate ids (and venn when stamped) in crossings / references
- Fleet talk: Venn code or "Andy crate" until chips render

## Anti-patterns
- Second people ledger beside Cast
- New page per spelling (Kat / KD / Katy) - aliases only
- Body prose into known-for
- Mass string-replace of names as the primary plan
- Treating display title as the stable id
- Parking person facts on Big Box Co or tag bay by mistake

## Rollout
1. This plan leaf (here)
2. Venn chip + venn field ask when Kitten greenlights coat/engine
3. On-touch: walk Cast; assign Venn codes; crate-ify crossings
4. Normalize Venn habit across ABC projects as desks adopt it
5. When ready to code-name someone: change Cast title only; cull aliases; Venn code stays

## Open questions
- Venn format bank (SDK-###, QR-#, project prefixes) - one house style or per-desk?
- Does Venn chip live in Librarian meta, Charlie cork, or both?
- Retro cite pass on old Cast crossings that still use display strings?
- When does Sam Ra-Rosewater / SDK-808 get a Cast leaf if not already?
