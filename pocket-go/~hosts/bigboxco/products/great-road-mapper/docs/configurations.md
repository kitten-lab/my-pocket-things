---
kind: guide
order: 4
crate: crate.B160B0C0E0004B26
title: Configurations
deck: reverse-from-ship · templates · variations · why this exists
product: Great Road Mapper
---

{{div:.bbc-kicker}}
products · great-road-mapper · docs · configurations
{{/div}}

# Configurations

This is the heart of Great Road Mapper — not a side tab.

## What was cognitively upsetting

Most schedule tools want you to build a roadmap **forward**: invent every phase date, hope they still meet ship, then fix slips one cell at a time across sheets. When you have many titles, many craft goals, and one hard release day, that is the wrong direction for a human brain.

What hurts:

- Holding an entire multi-phase pipeline in working memory
- Re-deriving the same week offsets for every new title
- Spreading "what moved and why" across Confluence paste and hallway talk
- Treating two related pipelines (a full production path vs a thinner follow-on path) as copy-paste instead of structure + numbers

Great Road Mapper's configuration system is the invention that answers that: **define the machine once, then set ship, and let the board reverse-fill the rest.**

## The idea in one sentence

A **configuration** is a reusable schedule machine. You describe bins (phases), workstreams inside them, and gate rules relative to phases or to ship. When you create a title and give it a ship date, the desk stacks those bins **backward from release** so a complex roadmap appears from one date.

Ship is the immovable anchor. Earlier work makes room by moving earlier — not by shoving the release.

## Templates vs variations

### Templates

A **template** owns structure:

- Ordered **bins** (phases) with durations (weeks or days)
- **Workstreams** under a phase (full-phase or a portion window)
- **Gate rules** — point deadlines anchored to a phase, a workstream, or release (`on ship`, `N before ship`, `N after phase end`, and so on)

Templates are the configuration maker. Blank template, then add phases, then save. You are designing the reverse-engineering rules, not filling one title's calendar by hand.

### Variations

A **variation** hangs off a template. Structure is locked to the parent. You only tune **numbers**:

- Week lengths on bins
- Portion windows on workstreams (from week X for Y weeks inside the phase)

That is how you get "same pipeline shape, different speeds" without forking the whole machine. Primary / complex / clone-style differences in a real slate are usually variations of one template — not three unrelated boards.

## Reverse-from-ship in practice

1. Build or pick a **template** (bins + gates + streams).
2. Optionally spawn a **variation** and change week numbers only.
3. **+ Title**, choose that product model, set **ship date**.
4. The desk minting the title applies the model: phases stack by duration from ship; gates land from their rules; quarter follows ship.

If ship is blank, you get an unscheduled corner — empty dates until you set ship and refill.

When you later stretch a mid-spine phase, the product prefers **making room earlier** (cascade earlier lines back) while **ship stays put**. That is the same cognitive rule as the config: release is law; complexity grows backward.

## Gates are not phases

Phases are ranges of work. Gates are point deadlines / handoffs. Configurations keep them separate on purpose so a delivery day is not confused with a craft bin. Gate offsets can be days or weeks; edge tails ("2d after phase end", "4d after ship") are first-class.

## Linked titles as a configuration use — not the product identity

Some houses need two related schedules for one creative unit: a full production pipeline and a thinner follow-on pipeline that shares lineage. In Great Road Mapper you can model that with **two configurations** (or a full template plus a thin template) and optional twin links between titles.

In Danielle's own slate, that pattern shows up as Nucleus titles with Betsoft rebrand follow-ons. That is **an example of how to use configurations**, not a shipping feature of Great Road Mapper itself. A distributed product should not require those company names. The portable idea is: **configurations let you mint different schedule machines; titles can point at each other when two machines belong to one story.**

## Why this improves the process

| Old pain | Configuration answer |
|----------|----------------------|
| Rebuild the same multi-goal roadmap for every title | Mint from a template / variation |
| Only remember ship, invent everything else under stress | Reverse-fill from ship |
| Slip mid-spine and accidentally threaten release | Grow backward; ship immovable |
| Copy a whole board to change week lengths | Variation = numbers only |
| Company-specific twin workflows baked into the app identity | Express twins as config choice + optional title links |

## Where to work it

Open the **Configurations** tab on the desk. Templates list on one side, variations on the other. Edit bins and gate rules on templates; edit week lengths on variations. Then create titles against the model you meant.

{{div:.bbc-go}}
{{link:crate.B160B0C0E0004B22|Getting started}} · {{link:crate.B160B0C0E0004B24|Phases, gates, and people}} · {{link:crate.B160B0C0E0004B25|Features}} · {{link:crate.B160B0C0E0004B12|Docs home}}
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
