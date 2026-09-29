---
crate: crate.B70922D48036FA6B
title: discussing-merging-terminals
---

# {{title}}
There is no straight merge. The two programs already decided that, in law and in code. The workable join is not “one store.” It is a **crate nail** on living ROM objects, with cabinets remaining a pocket-go overlay.

## Why it feels pathless

You are looking at **two cousins of the same paper**, not two skins of one app.

**sdk-import-station** is a live little program. Rooms (`?room=files|mail|desk…`), station paper as `.chip` files, shared mail JSON, glass as an IO-only ritual, chip-switch chrome. PORT.md is explicit: not pocket-as-OS, not one global store, per-station paper is right.

**`go.terminals`** is a pocket-go host: markdown + `environment:` coats that *look like* import-station. Cabinets work there because every Go page can mint a `crate:` and the drawers key off that page. Mail, fileKeeper, glass, and the other stations are not running. You get the coat and a frozen dump of Sam/K notes.

Cabinets are not a widget you drop on a page. They are five mouths that **follow the page you are standing on**, stored as path-mirrored YAML under `~librarian/`, `~detective/`, `~charlie/`, `~tps/`, plus lore cards in trays. `librarian.js` only binds when the document has a Go vault path (`data-vault`). Go’s shelf code only files against `.md` / `.canvas` inside the vault:

```1449:1483:C:\ALICE_BOX\my-pocket-things\pocket-go\prod\www_sys\server.py
def shelf_file(kind: str, target: Path) -> Path | None:
    ...
    elif page.suffix.lower() == ".md":
        rel = page.relative_to(vault).with_suffix(".yaml")
    elif page.suffix.lower() == ".canvas":
        ...
    else:
        return None
```

So: work in the ROM → no crate, no vault path, no cabinets. Work in `go.terminals` → cabinets, but the living rooms are gone. That is the whole knot.

## The two data methods are closer than they look — and that is a trap

A chip is already a note:

```1:13:C:\ALICE_BOX\charlies-toys\sdk-import-station\paper\io\_root\leaf[40]-welcomemessagedonotdel.chip
---
store:
  file: leaf[40]-welcomemessagedonotdel.chip
chip:
  uid: leaf[40]
  name: !! Welcome Message DO NOT DEL !!
  auth: IOX
pin:
  tps_created: 1758003800
  tps_updated: 1784757863
  tags: []
  legacy_stem: FK-IO-welcome-message-do-not-del-WMDND-a945e1
---
```

A Go page is YAML + body too, but the **nail** is `crate.`, and the **runtime** is Go’s reader + cabinet APIs. The ROM’s nail is `leaf[n]` + station auth, and the runtime is PHP rooms.

Same prose can exist twice. It already does: `leaf[43]-whoismiseryakaoyzis.chip` beside `~hosts/terminals/IO/SAM'S FILES/WHO is MISERY aka OYZIS.md`. Two files, two identities, no shared crate. Syncing bodies would make a third problem.

PORT.md already named the later exit for paper that outgrows the station: promote a chip *out* into a mat. That is promotion, not a live dual-write.

## What not to do

**Do not make the ROM a Go host.** That is the current `go.terminals` state: coat without the program. You would keep losing mail, glass, chip-switch, station paper roots.

**Do not copy `librarian.js` into PHP.** Cabinets are the Go catalog: lore cards, motif ledgers, crate reports, Charlie grammar, TPS slices. A PHP clone would drift in a week.

**Do not dual-write chip body ↔ markdown.** You will not know which file is true. Cabinets were designed to sit *off* the hopper for this reason.

**Do not use README on ROM paper.** README is Go’s editor for `.md`. In the ROM, the editor is fileKeeper. If cabinets come to the station, they should be Librarian / Detective / Charlie / TPS, not a second writer.

**Do not merge mail.** ROM mail is a wire (`mail/messages/*.json`, station↔station, inject token, Sophia desk POST). `go.terminals/IO/E-Mail/` is narrative props. Keep the room. If a letter needs a cabinet, stamp a crate on that JSON and let drawers follow the *message*, not a copied `.md`.

That last piece already has a precedent: the ROM already POSTs to another local desk instead of becoming it.

```192:200:C:\ALICE_BOX\charlies-toys\sdk-import-station\app\mail\mail_lib.php
function sdk_mail_bridge_to_desk(...): array {
    $url = getenv('SOPHIA_DESK_URL') ?: getenv('POCKET_DESKTOP_URL') ?: 'http://127.0.0.1:43167';
    $url = rtrim(...) . '/api/mail/send';
```

Cabinets should be the same kind of neighbor, toward Go on `:43210`, not a second paper store.

## The join that respects both laws

Three layers, not one:

| Layer | Lives where | Job |
|---|---|---|
| Life | ROM chips, mail JSON, glass, rooms | The thing you *are in* |
| Catalog | Go cabinets + lore cards | What you *file about* the thing |
| Nail | `crate.` on the ROM object | The only shared id |

**1. Stamp crates onto ROM objects, never overwrite.**  
Chips already have YAML. Add `crate: crate.XXXXXXXXXXXXXXXX` beside `chip.uid` / `pin`. Mail can carry the same field. Mint on first cabinet open, same as Go’s `ensure_crate`. Do not replace `leaf[40]`. `leaf[n]` stays the station’s file id; crate is the pocket’s nail.

**2. Teach Go shelves a crate-first key, with ROM as a foreign `pocket`.**  
Today sidecars are `~librarian/terminals/IO/….yaml` because the page is a vault path. For a chip, the sidecar should key off crate (or a synthetic pocket like `rom:sdk-import/io/leaf[40]`), same YAML shape Go already writes. Lore cards already attach by `edges: [crate.…]` — they do not care that the born-on page was a chip.

That is the actual code wall. Until shelves can file without a vault `.md`, cabinets cannot follow a chip.

**3. Open cabinets as Go sidecars from the ROM window, do not paint them inside phosphor.**  
Deck Host already pops cabinets as Go windows (`/?sidecar=`). The ROM already has a gem menu (`DECK_ROM_MENU`). The pleasant path is: standing on a chip in FILES, Cabinets → Librarian opens the *same* rail you know, bound to that crate, still served by Go. The phosphor field stays the ROM. You do not embed MyPI chrome in the CRT.

Cross-origin (43101 vs 43210) is why a sidecar or a Deck Host handoff is better than fetching Go APIs from PHP pages. The ROM only needs to pass crate + a return door (`/?room=files&station=io&c=leaf[40]`).

**4. Let crate reports grow a “open in station” door.**  
In Go, clicking a crate sends the desk to the `.md`. For a ROM object, “there” is the FILES/mail URL. That is a `pocket:` / `from:` problem, not a new catalog. `^crate.` in detective notes can then point at a chip you filed while you were in the station.

## What “pages” even are in the ROM

If you try to cabinet *the whole shell*, you will cabinet the chrome. Bind to objects, not rooms:

- **A chip** — the main ask. One crate per leaf. Folders are not pages.
- **A mail message** — optional, when a letter is worth Librarian/Detective.
- **Welcome land HTML** — skip. Not catalog paper.
- **Glass cores / `.glassbox`** — skip until something is promoted. Glass stays the mountain; cabinets are for life paper.

Charlie is two different verbs. PORT.md’s Charlie is “AI reads station files, mails connections into a station.” Go Charlie is `from * rel > to` on a crate. Keep both. ROM Charlie produces mail; Go Charlie weaves the nail. Do not flatten them.

TPS is similar: chips already have `pin.tps_created`. On crate mint, copy **created** once into Go TPS. Do not stamp import/copy day. KEYS.md already forbids that.

## What to do with `go.terminals`

Treat it as **lobby + coat**, not a second fileKeeper.

Keep: `_shell.md`, IO/AB coats, chip rail CSS, `{{rom:sdk-import}}` as the door into the live program.

Stop treating `SAM'S FILES`, `E-Mail`, `Daily Inventory` as the living set. Those are the fork. Cabinets on that tree file against copies, so the ROM will never see them.

A later, optional step: shadow stubs in `go.terminals` that hold only YAML (`crate`, title, `source: rom:…`) and no body. That is a compatibility shim if you want crate reports to land on a Go page at all. It is not the living paper. Prefer crate-first shelves so you do not have to keep stubs forever.

## A sequence that does not boil the ocean

1. **Prove the nail on one chip.** Pick `leaf[40]` or Misery. Mint a crate into the chip YAML. Hand-file one Librarian field in a crate-keyed sidecar. Confirm the crate report can see it from Go even though there is no matching `.md` body.
2. **ROM → sidecar.** From FILES, gem Cabinets opens Go’s Librarian bound to that crate. Edit a field, reload, still there. Body still saves only through fileKeeper.
3. **Return door.** Crate report “open in station” hits `:43101` on the right leaf.
4. **Mail later, as a second object type.** Same nail, different room. Do not replace the MAIL room.
5. **Ignore glass and the extra stations** until the chip path feels like the same cabinets you already love.

That is small on purpose. The pleasure you do not want to lose is the ROM as a program. The pleasure you want to add is the catalog mouths. Those pleasures live in different processes on purpose. The crate is the only thing that should be shared.

If you want this built next, the first design freeze is: **crate on chip, cabinets stay Go, no body sync.** Everything else is an implementation of that.
