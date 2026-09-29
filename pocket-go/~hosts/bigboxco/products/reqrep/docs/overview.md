---
kind: overview
order: 1
crate: crate.B160B0C0E0004B13
title: Overview
deck: what ReqRep is and why it helps
product: ReqRep
---

{{div:.bbc-kicker}}
products · reqrep · docs · overview
{{/div}}

# Overview

## What ReqRep is

ReqRep is a **request bay**: a dedicated desk where a product ask can be discussed in pieces, clarified until it is true, frozen as purpose, and turned into a clean **Product prep** document that you sign before anyone builds.

It sits in the Alice Box line under Big Box Company. The product code is `CO.BBC-002-RR`. It is meant to feel like the same family as Great Road Mapper — clear type, gold accent, BIGBOX chrome — a serious office tool, not a chat dump.

## The problem it solves

Product asks often start as hallway talk, Slack threads, or pasted notes. That fog is easy to misread. Someone builds from an open comment. Someone else thought the scope had already changed. The assistant and the human talk past each other because nothing was sealed.

ReqRep gives that conversation a place with structure:

1. The ask becomes a **case** with a clear title and owner fields.
2. Talk happens in **tickets** (discussion blocks) with threads under each block.
3. You can **seal** a block when you agree it is settled.
4. You write and **lock** the case purpose so it stops drifting under your feet.
5. The desk produces a separate **Product prep** document — a sibling artifact, not a scrubbed comment thread.
6. You **sign** that prep. Only then is it the contract for the first slice of work.

That last step is the point of the product. Unsigned talk is not law. Signed prep is.

## Who it is for

| Role in real life | How the product labels it | What they do here |
|-------------------|---------------------------|-------------------|
| You — the person running the desk, owning the ask, and approving the contract | **Hands** in the UI | File requests, discuss, seal agreements, lock purpose, sign Product prep, run QA on work lanes |
| The desk assistant working with you on that ask | **Agent** in the UI | Discuss when invited, reply on open discussion tickets, implement only on **RUN**, move finished work to **TEST** for your review |

If you see the word **Hands** in the interface, that means **you** (or whoever is filing as the human operator). It is not a mysterious third character. The product needed a short badge label; the documentation will keep saying “you” whenever that is clearer.

## What you get out of it

- A single place to hold requests before (and while) products exist
- Discussion that can be closed in pieces instead of one endless scroll
- A purpose statement you can lock so build work has a floor
- Work lanes that separate “we are still talking” from “you may build” from “I am checking it”
- A signed Product prep that is allowed to leave the bay as the build contract

## What this version is

This is the **first shipping slice** of ReqRep. It is a working desk: list, intake, discussion tickets, seals, purpose lock, Product prep generate/edit/sign, light and dark theme, Deck Host launch.

It does **not** yet include LLM rewriting of prep, analytics dashboards, multi-tenant workspaces, or bulk import from Confluence-style dumps. Those are out of scope for this slice, not missing buttons you should expect to find.

## How to open it

Preferred path: launch **ReqRep** from Deck Host (ROM id `reqrep-414b`). Day-to-day work belongs in that host window so the product stays with the rest of your desks.

```bat
cd C:\ALICE_BOX\big-box-company\reqrep\prod
run-reqrep.bat
```

- Port: **42962**
- Local data: `prod/safe_box/cases.json`

A browser-only launcher exists for emergencies. Prefer Deck Host for normal use.

{{div:.bbc-go}}
[[getting-started|Getting started]] · [[working-together|Working together]] · [[index|Docs home]]
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
