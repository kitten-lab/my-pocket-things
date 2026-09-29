---
kind: guide
order: 5
crate: crate.B160B0C0E0004B18
title: Roles and work lanes
deck: who may talk · who may build · who approves
product: ReqRep
---

{{div:.bbc-kicker}}
products · reqrep · docs · roles and lanes
{{/div}}

# Roles and work lanes

## Roles

### You (Hands in the UI)

You own the request as a human operator.

You:

- File and prioritize cases
- Discuss in tickets
- Seal agreements
- Lock and unlock purpose
- Sign Product prep
- Review work in **TEST**
- Decide when something is actually done

### Desk assistant (Agent in the UI)

The assistant works the case with you inside the bay.

The assistant:

- Replies on **DISCUSSION** tickets
- Does not implement from open debate alone
- Implements only on **RUN**
- Moves finished RUN work to **TEST** for you
- Treats signed Product prep as the build contract after you sign

The assistant must not freestyle build from chat fog, unmarked paste, or open blocks.

## Work lanes

Lanes answer “where is this ticket in the workflow?” They are not seals.

| Lane | Owner energy | Assistant implement | Assistant reply |
|------|--------------|---------------------|-----------------|
| DISCUSSION | Shared active talk | No | Yes |
| PAUSED | Later | No | No |
| RUN | Assistant queue | Yes | Optional |
| TEST | Your QA | No freestyle | Only if asked |
| CLOSED | Done for assistant | No | No |

### Practical rules

- **DISCUSSION** means the topic is alive. Clarify. Do not ship.
- **PAUSED** means leave it alone this cycle.
- **RUN** means the assistant may do the work described on that ticket.
- **TEST** means the ball is with you for QA.
- **CLOSED** means the assistant is done with that ticket; seals remain a separate human mark.

Legacy lane names you may see in older notes: `run_test` maps to **RUN**, `in` maps to **CLOSED**.

## Two seals, two jobs

1. **Block seal** — you close a ticket when that piece of talk is agreed.
2. **Prep sign** — you accept the Product prep for the whole case.

Building from unsigned prep, or from open discussion alone, is the failure mode this product exists to prevent.

{{div:.bbc-go}}
[[working-together|Working together]] · [[product-prep|Product prep]] · [[index|Docs home]]
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
