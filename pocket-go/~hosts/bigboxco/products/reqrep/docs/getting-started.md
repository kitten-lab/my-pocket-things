---
kind: getting-started
order: 2
crate: crate.B160B0C0E0004B16
title: Getting started
deck: open the desk · create a request · find your way around
product: ReqRep
---

{{div:.bbc-kicker}}
products · reqrep · docs · getting started
{{/div}}

# Getting started

## Open the desk

1. Launch ReqRep from Deck Host (ROM `reqrep-414b`), or run `run-reqrep.bat` from the product `prod` folder.
2. You should land on the **Request bay** list.
3. Use the theme control if you want light or dark.

At the top of a case you will see an **as** control: **Hands** or **Agent**. That chooses who the next comment is attributed to. When you are speaking for yourself, leave it on Hands. When the desk assistant should post in-character as the assistant, switch to Agent.

## Create a request

Click **+ REQ**.

You will fill:

| Field | Meaning |
|--------|---------|
| **Type** | `REQ` new product/SKU · `MOD` change an existing one · `ADDENDUM` · `BUG` |
| **SKU** | Product chip code, e.g. `CO.BBC-002-RR` |
| **Product** | Human name, e.g. `ReqRep` |
| **Producer** | The studio or house filing it (e.g. Big Box Company) |
| **Hands** | The human face on the filing (your name or badge) |
| **Priority** | Normal, High, Low, or Urgent |
| **Seed discussion** | Optional. Paragraphs separated by a blank line become the first discussion tickets |

The **title** is composed for you from type, SKU, and product name. You do not free-type a diary title. Example shape:

`REQ: ROM SKU CO.BBC-002-RR "ReqRep"`

Each case also gets a bay file code such as `REQ-001`. That is the case id inside the bay. It is not the same thing as the product SKU.

Submit with **Open bay**.

## Find your way around the list

The request list shows title, producer, Hands, priority, status, and a sense of open tickets.

Status on a case moves through the pipeline, including labels such as discuss, scope lock, prep, signed, build, done, and park.

Beside the list, an **Open board** rail summarizes tickets by work lane (discussion, run, test, paused, closed). That is how you see, at a glance, whether the assistant should be talking, building, or waiting on your QA.

## Open a case

Click a row. Inside the case you will find:

- Intake / meta (read first; edit when you choose)
- Purpose (scope) with lock controls
- Discussion tickets with threads
- A **Product prep** dock for generate, edit, and sign

Read the quiet key/value readouts first. Forms open when you ask to edit. The desk is designed so information stays readable instead of sitting forever inside empty input fields.

{{div:.bbc-go}}
[[working-together|Working together]] · [[features|Features]] · [[index|Docs home]]
{{/div}}

{{div:.stockroom}}
{{images}}
{{/div}}
