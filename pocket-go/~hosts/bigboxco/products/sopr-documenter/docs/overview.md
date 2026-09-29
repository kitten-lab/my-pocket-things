---
kind: overview
order: 1
crate: crate.B160B0C0E0004B33
title: Overview
deck: what sopr Documenter is and why it helps
product: sopr Documenter
---

{{div:.bbc-kicker}}
products · sopr-documenter · docs · overview
{{/div}}

# Overview

## What sopr Documenter is

**sopr Documenter** is a desk for compiling documentation from fragmented thinking. You open a document bag, dump scraps under section headers, resort the rows until the outline is honest, and only then treat it as a finished document shape.

It sits in the Alice Box line under Big Box Company. The product code is `CO.BBC-003-SPR`. Port **42950**. Deck Host ROM id `SPR-403`.

## The problem it solves

Most doc tools assume you can outline first. That is cognitively hostile when your real process is dump-brain: headers that made sense in the moment, scraps that arrive out of order, and a need for a real document only after the structure stops lying.

What hurts without sopr:

- Pretending intake order is final outline
- Baking section names into leaf IDs so a move forces a rename storm
- Leaving chat heat as the only store for hard-to-compile notes
- Muddying one scrap with a sidecar "notes" field instead of making another fragment

sopr’s answer: **bins + ordered leaves + resort**. Part codes stay stable. Section membership is a field, not identity. See {{link:crate.B160B0C0E0004B35|How it works}}.

## Who it is for

You — when the document is hard to compile and you need timber for an outline, not collaboration theater. This is Office / Confluence energy for one operator: section structure, movable leaves, reader when ready. No emoji reactions. No wiki cosplay required.

## What you get out of it

- Documents as `.sopr` bags in a vault
- Inline composer at the top of the active section bucket
- Text, image, and table fragment types
- Resort kanban (Ctrl+2) and print / reader (Ctrl+3)
- Stable `SPR-####` part codes that survive moves
- Optional document-level production chip tracking (About this document) when Machina is corded

## How to open it

Preferred path: launch **sopr Documenter** from Deck Host (ROM id `SPR-403`).

```bat
cd C:\ALICE_BOX\big-box-company\sopr-documenter\prod
run-sopr.bat
```

Browser-only: `run-sopr-browser.bat`, or `cd box_sys` and `python server.py`.

- Desk: `http://127.0.0.1:42950/`
- Local documents: `prod/safe_box/*.sopr`

{{div:.bbc-go}}
{{link:crate.B160B0C0E0004B34|Getting started}} · {{link:crate.B160B0C0E0004B35|How it works}} · {{link:crate.B160B0C0E0004B37|Features}} · {{link:crate.B160B0C0E0004B32|Docs home}}
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
