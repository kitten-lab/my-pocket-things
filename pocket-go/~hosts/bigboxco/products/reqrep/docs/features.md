---
kind: reference
order: 4
crate: crate.B160B0C0E0004B14
title: Features
deck: what the current product can do
product: ReqRep
---

{{div:.bbc-kicker}}
products · reqrep · docs · features
{{/div}}

# Features

Everything below is supported by the shipping desk UI. Futures are listed separately at the end so they are not confused with live capacity.

## Request list

- Browse all cases in one table
- See title, producer, Hands, priority, status, and open-ticket pressure
- Open-board rail with counts by work lane
- Agent inbox hints for what needs action versus what can wait
- Create a new case with **+ REQ**

## Case intake

- Type: REQ, MOD, ADDENDUM, BUG
- SKU, product name, producer, Hands, priority
- Composed title line (not free-typed diary titles)
- Optional seeded discussion that splits on blank lines into first tickets
- Bay file code for the case (for example `REQ-001`)

## Discussion desk

- Numbered tickets / blocks with expand and collapse
- Comment threads under each ticket
- Attribute the next post as Hands (you) or Agent (desk assistant)
- Edit comments after posting
- Seal a ticket (for example AGREED) and reopen deliberately
- Set work lane per ticket: DISCUSSION, PAUSED, RUN, TEST, CLOSED
- In-desk dialogs for stamps and confirms (no browser prompt/confirm popups)

## Purpose and Product prep

- Purpose body with read-first display and explicit edit
- Lock and unlock purpose
- Soft banner when purpose is locked and tickets may still move
- Product prep dock: generate, edit, save, sign
- Signed banner when prep is leave-bay law
- Local generate template in this slice (not an LLM rewrite)

## Chrome and comfort

- BIGBOX / ReqRep desk chrome meant for Deck Host
- Light and dark theme
- Read-first meta panels (edit on demand) so the desk stays readable under load

## Not in this slice

- Automatic LLM rewrite of Product prep
- Analytics / reporting suite
- Multi-tenant workspaces
- Bulk Confluence-style import

## Coming soon / ideas on the table

These are not live features. They are honest future notes:

- A clearer case-level “discussion locked” control, if “all blocks sealed” is not enough
- Stronger Product prep templates (job, in scope, out of scope, first slice, non-goals)
- Richer reply-stamp receipts on seals
- Default collapsing of closed blocks for quieter scanning

{{div:.bbc-go}}
[[getting-started|Getting started]] · [[working-together|Working together]] · [[index|Docs home]]
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
