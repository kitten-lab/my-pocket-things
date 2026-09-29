---
kind: guide
order: 3
crate: crate.B160B0C0E0004B17
title: Working together
deck: how you and the desk assistant communicate and hand off
product: ReqRep
---

{{div:.bbc-kicker}}
products · reqrep · docs · working together
{{/div}}

# Working together

This is the heart of ReqRep: a clean back-and-forth between **you** and the **desk assistant**, with seals that mean something.

## The conversation shape

Talk does not live as one endless comment wall. It lives as **tickets** (also called chunks or blocks).

- A blank line in seed text, or a new ticket you add, starts a new block.
- Each block has a body and a thread of comments underneath.
- You and the assistant post into those threads using the **as Hands / as Agent** control.
- You can expand or collapse a ticket body so the desk stays scannable.

While a ticket is open, you are still negotiating. Open comments are not build law. The assistant should not treat an unsettled thread as permission to ship product work.

## Sealing a block

When a topic is actually agreed, you close it on purpose.

Use the hand stamp / seal control on the ticket. House language is often **AGREED**, but the important part is that **you** marked the block closed. Closed blocks are settled for scope purposes. Reopening is a deliberate act, not a silent edit.

Two different ideas live side by side:

| Idea | What it means |
|------|----------------|
| **Seal** (AGREED / IMPLEMENTED, etc.) | Human approval mark on that ticket |
| **Work lane** | Where the ticket sits in the workflow (discussion, paused, run, test, closed) |

Changing a lane is not the same as sealing. Lane moves organize work. Seals record agreement.

## Purpose (scope)

Every case has a **purpose** body — the case-level statement of what this request is for.

1. Write and revise it until it reads true.
2. **Lock** it when it should stop drifting.
3. Unlock only when you intend to rewrite the purpose.

After purpose is locked, you can still add tickets, comment, move lanes, and stamp. Lock freezes the purpose text, not the whole board. That “workboard” mode is intentional: the floor stays stable while tickets keep moving.

## When the assistant may build

The assistant may implement only when a ticket’s work lane is **RUN**.

| Lane | Meaning | Assistant may implement? | Assistant should reply? |
|------|---------|--------------------------|-------------------------|
| **DISCUSSION** | Active shared talk | No | Yes — clarify, do not freestyle build |
| **PAUSED** | Hold for later | No | No |
| **RUN** | Assistant work queue | Yes | Optional |
| **TEST** | Your QA bag | No freestyle | Only if you ask |
| **CLOSED** | Done for the assistant on that ticket | No | No |

Handoff pattern:

1. Assistant finishes work on a **RUN** ticket.
2. Assistant moves that ticket to **TEST** (lane only — not a seal).
3. You review. Seal if it is good, or send it back to **RUN** if more cut is needed.

## Leaving the bay

After purpose is locked and discussion is settled enough, generate **Product prep**, edit it if needed, then **sign** it as yourself.

Only signed Product prep is the contract that may leave the bay. Discussion and locked purpose remain as archive. First-slice build work should follow the signed prep, not the fog of open threads.

```
Talk in tickets
    → you seal what is agreed
    → purpose written and locked
    → Product prep generated and edited
    → you sign Product prep
    → first slice may begin
```

That is the repaired working relationship the desk is built for: clear talk, clear seals, clear handoff.

{{div:.bbc-go}}
[[roles-and-lanes|Roles and work lanes]] · [[product-prep|Product prep]] · [[index|Docs home]]
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
