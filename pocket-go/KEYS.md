# Pocket Go keys

How clay talks to the reader. Tokens are `{{like this}}`. They work in any `.md` under a go.* host (a folder in `~hosts/`) and on the start page. The skin (`environment:`) decides how a list *looks*; the token decides *what* is listed. Tool slots also accept `{{tool:codelook}}` (same as `{{codelook}}`).

Two special filenames:

| file | job |
|---|---|
| `_shell.md` | optional shell for a folder. `{{paper}}` makes it the dress room — notes below wear this chrome. `{{subshell}}` instead of paper nests in the *next* shell's paper hole (campus stays the environment; the hall still has a crate). |
| `index.md` | the blotter / paper that fills `{{paper}}`. Hidden from `{{files}}` so it does not list itself. Has its own crate (the fill). Librarian and Charlie hang here. |

Names that start with `~` or `.` stay off the lists. Underscore folders are ordinary (they sort above A-Z). `_shell.md` is never a listed note. Pictures live in `mats/imgs/`. Skins live in `mats/styles/`.

---

## Hosts

The address bar is `go.{host}/path` or `roam.{slug}/path`. Hosts are not a hardcoded list. Home is not a host. Closing the pocket remembers the last desk page on disk; the next open returns there. Home on the bar still goes to Go. The bar is back, forward, home, refresh, then the address.

| lives at | becomes |
|---|---|
| `~hosts/start.md` | `/` - the Go lobby. bar says `go`. Type `go` or `start`. |
| `~hosts/roam.md` | `/?p=roam` - connected roam libraries. bar says `roam`. Type `Roam`. |
| `~hosts/recent.md` | `/?p=recent` - last 25 kept notes. bar says `recent`. Type `recent` on the bar. |
| `~hosts/{name}/` | `go.{name}` as soon as the folder exists |
| `~hosts/_hosts.yaml` | optional aliases, titles, and `kind: roam` + `source:` for exterior folders |

Type `go.terminal/` in the bar when that room is there. Type a name that has no folder yet and the pocket says the room isn't here *now* — not that it can never be. `library` is just another possible folder: `~hosts/library/` → `go.library`.

`kind: roam` plus `source:` in `_hosts.yaml` connects an exterior markdown folder as `roam.{slug}` (Desktop is legal; the yaml line is the allowlist). The station FILES vault is `sdk-import-station/library/` as `roam.files` (Go-paper halls). Sophia Desk's library is `roam.sophia`. Writes from README New / Keep go into that folder for markdown notes. Cabinets still live under `~librarian/{slug}/`. Full map: Help → Roam libraries.

`.chip` files are **guest paper**. Go may look, crate, and cabinet-mark. The producer (Sophia / FILES) keeps the pen. BIOS Keep / Rename / page face stay off the chip; the hall `_shell.md` is still editable. Crate ids live in `~librarian/{host}/_chip_crates.yaml` keyed by `chip.uid` (`leaf[6]`, `card[7]`), so a producer overwrite does not mint a new crate. A top-level `crate:` on the chip is a courtesy sticker only.

Plain `.txt` / `.py` / other source files are guest paper too: listed in the hall, opened as a read-only text sheet (not markdown). BIOS Keep / Rename stay off. No crate is stamped into the file. Images still use `/i/`. Binary files are skipped.

Live `.html` / `.htm` sit in a frame on the paper so the page paints. CSS, pictures, and fonts next to the file load with it. BIOS Keep / Rename stay off.

Wiki, tags, images, and `{{slots}}` stay inside the host you are standing in. On Go, `{{doors}}` lists native `~hosts` folders as `go.*` doors. Type `Roam` for the roam lobby (`{{doors:roam}}`). Librarian / charlie / readme for a named host live under that host's name (`~librarian/terminal/…`). The Go page uses the unprefixed drawer (`~librarian/_index.yaml`).

Outside worlds are the drawers, plus any `roam.*` libraries you connect. Not a second vault beside hosts.

---

## Slots

Put these where you want the machine to print a list or a hole.

| token | also | prints |
|---|---|---|
| `{{files}}` | | notes in **this folder** (not subfolders). Bookstore paints them as face-up covers. A note with `cover:` and a real picture wears that art as the jacket; otherwise cloth + title. On `_shell.md` this repeats on every note that wears the shell — put it on `index.md` if it should only be the folder hall. |
| `{{spines}}` | | same notes as `{{files}}`, with a `spines` class. Bookstore paints them as shelf spines. |
| `{{doors}}` | `{{worlds}}` | **subfolders** as door cards (name + note count). On Go, native hosts only. |
| `{{doors:roam}}` | `{{roam}}` | connected `roam.*` libraries as door cards. Type `Roam` on the bar. |
| `{{dir}}` | `{{list}}` | notes **and** subfolders together. |
| `{{dirtree}}` | | notes **and** subfolders as a nested tree, **3 levels** from the folder of the page you are on. Same hide rules as `{{dir}}` (`_`, `.`, `~` names, `index.md`). Folders use the room title when they have one. The open page (and its path of folders) wears `on`. |
| `{{tree}}` | `{{dirtree:shell}}` | file tree rooted at the **dress shell** (the `_shell.md` with `{{paper}}`), not the open hall. Folders open and close. The path you are on stays open and wears `on`. Put this on `_shell.md` for a sidebar that does not follow you. `{{dirtree:root}}` is the same. |
| `{{paper}}` | `{{insertdata}}` | hole in a dress `_shell.md`. Filled with that folder’s `index.md`, the note you opened, or a nested subshell. |
| `{{subshell}}` | | hole in a nested `_shell.md`. Picks up the next `{{paper}}` shell and sits in that paper hole; this file's chrome wraps the inner page. Cabinets stamp this hall's crate. |
| `{{images}}` | `{{slides}}` | image files in **this folder** (not subfolders) as a slideshow. Filename order. A thumbnail rail is part of the show; a standalone `{{thumbs}}` can split later. |
| `{{faces}}` | `{{cards}}` | the **body** of each note in the open hall, printed in place (a grid of card faces). Follows the paper room, not a parent shell's folder. Each note fills from its own YAML; `{{meta}}` / cabinet chips on that note print. Click a face to open it on the desk. Listing slots (`{{files}}` `{{faces}}` `{{doors}}`) inside those notes are not expanded. Not subfolders. |
| `{{face:crate.XXXX}}` | `{{card:crate.XXXX}}` | one note, anywhere under a go.* or roam.* host, whose `crate:` matches. Prints that file's body in place. Click it the same way as a face in the grid. Cross-host. Not wiki. The 16 hex can omit the `crate.` prefix. |
| `{{link:crate.XXXX}}` | `{{crate:XXXX}}` | plain door to that crate — title as a wiki-style link (`/?k=`). Optional `\|label`. Cross-host. Not the face/frame. |
| `{{cover}}` | `{{jacket}}` | this page's cover object, printed where you put the token. Reads YAML `cover:` (or `jacket:`). Picture from `mats/imgs/` or this host. No picture → cloth with the title. The **environment** dresses it: bookstore makes a book; another skin can make a banner. Same art `{{files}}` uses on a shelf. |
| `{{meta}}` | `{{chips}}` | this page's Librarian catalog, printed as chips. `{{meta:detective}}` / `{{chips:detective}}` is Detective's. `{{meta:agent}}` still works.
| `{{lib:label}}` | `{{det:label}}` | one filed value from this page's Librarian / Detective shelf (aliases `librarian:` / `detective:` / `agt:` / `agent:`). Missing → blank. Multi → comma-joined. Not Charlie. Not page YAML. | Click a label for that field's ledger. Click a value as a motif across fields, mouths, and lore titles. Optional paint — the drawer is the real shelf. Not Charlie. Not `#tags`. |
| `{{edges}}` | | crates this lore card touches, as doors. Born-on first (`source_crate`), then pins from Attach Lore. The card is the edge. |
| `{{headers}}` | | this page's YAML as a folded slip. Opt-in. The page does not print headers on its own. `crate:` stays off the slip. |
| `{{injector}}` … `{{/injector}}` | | on-page insert form. Clay outside `{{hidden:…}}` is the page body. `{{hidden:frontmatter}}` is YAML identity (`{{text:title}}`). `{{hidden:lib}}` / `{{hidden:tps}}` file that cabinet (`lib` → librarian). Nested `{{text:type}}` is a form field that files on that row. Standing `{{log-type}}` and `{{time:now}}` fill from the hall / the clock. Minted note prints in injector order (`# {{title}}`, body fields, then `{{meta}}` / `{{meta:tps}}` where those cabinets sat). YAML stays thin (`crate` `title` `environment`). |
| `{{recent}}` | `{{recent:N}}` | last 25 notes and canvases kept (disk mtime), newest first, as jump links. Across every host plus lobby notes. Type `recent` on the bar. Optional count, cap 100. Hidden names (`_` `.` `~`) stay off. `recent.md` does not list itself. |

If a page has **none** of `{{files}}` / `{{spines}}` / `{{doors}}` / `{{dir}}` / `{{dirtree}}` / `{{tree}}` / `{{images}}` / `{{faces}}` / `{{recent}}`, the reader appends doors (at vault root) or a full `{{dir}}` listing (everywhere else).

Every slot also answers `{{tool:name}}` - `{{tool:codelook}}`, `{{tool:doors:roam}}`. Bare `{{codelook}}` still works.

---

## This page

These read **the file you are in** (its YAML). `{{the-key}}` prints that field. Empty or missing → nothing (no leftover token). Wiki `[[links]]` in a field stay links.

If the same stem has a `{key}_href:` (a path starting `/`), `{{key}}` prints as a working door — `<a href="…">`. That is how a lore card points back at another host. If `{key}_href:` is `http://` or `https://`, `{{key}}` is an **outlink** — it leaves the pocket (OS browser). Markdown `[label](url)` is not parsed.

`{{title}}` and `{{author}}` are just the common ones. `{{environment}}` `{{aliases}}` `{{color}}` — any key the note actually has.

Slots still win: `{{files}}` `{{paper}}` `{{crumb}}` and the other list/hole tokens are not YAML.

Window bar is separate: nearest `_shell.md` `title:` , then this page’s `title:`.

---

## Crumbs

| token | also | prints |
|---|---|---|
| `{{crumb}}` | `{{bread}}` | full trail: `home / folder / note` |
| `{{shellcrumb}}` | | trail from the nearest `_shell.md` paper-shell to here |
| `{{crumbback}}` | | one step up: parent title (or `home` at the start page) |
| `{{home}}` | `{{root}}` | one door: the nearest `_shell.md` walking up (this room). Label is that shell's title. No `_shell` → the host root. |

---

## Uses

On a **note** (not a folder shell), the reader also finds other files with the same stem and pages that `[[wikilink]]` this name.

| token | also | prints |
|---|---|---|
| `{{uses}}` | `{{bags}}` | that block, right here. |

If you omit it, the drawer is appended at the bottom when there is something to show. The floor of a page does not list every inbound `[[link]]`.

---

## Dress

Class and id for CSS. Safe names only: letters, numbers, `_`, `-`.

**Lead** — at the start of a paragraph or heading, sticks a class (and optional id) on that block:

```
{{.mast}}THE BOOKSTORE
{{.foot}}HANDLE WITH CARE
{{.tagshelf}}#bookstore #excerpts
```

`{{#some-id}}` alone sets an id. `{{.class#id}}` does both.

**Span** — inline, or one per line (rest of the line is the span; close is optional):

```
{{span:accent}}kitten detective{{/span}}
{{span:.mute#here}}quiet{{/span}}

{{span}}Home
{{span}}Products
{{span}}Contact
```

**Div / block** — own line, or content on the same line:

```
{{div:side}}
{{div:card}}
inside
{{/div}}
{{/div}}

{{div:.main-title}}HOME OF N&N
{{/div}}

{{div:.button}}INFORMATION{{/div}}
```

`{{block:name}}` / `{{/block}}` is the same as `div`. Nest them. Close what you open.

---

## Bullets

A list line can wear a mark. The mark is the bullet object. Rooms dress it from CSS (`ul.bullets > li[data-mark="…"]`). Click **task** and **done** to cycle them; that writes the clay.

```
- [.] still holding
- [ ] same as [.]
- [x] done
- [>] migrated
- [<] scheduled
- [o] event
- [-] note
- [*] look at this
- [/] in progress
- [!] bang
- [?] ask
- a plain line stays a plain line
```

Bare bujo (`- . task`, `- x done`) still reads. After a click, task clay is `.` and done is `x`. Wiki `[[links]]` are not marks. `environment:` is how a host restyles the set — CC stamps them as gold boxes.

---

## Images

```
{{img:typing-computer.gif}}
{{img:typing-computer.gif|alt text}}
![[typing-computer.gif]]
![[typing-computer.gif|alt]]
![alt](typing-computer.gif)
```

Looks up by filename (or path) in `mats/imgs/`, then by vault-relative path or filename in the current host.

A folder of scans or zine pages: drop the files next to `index.md` / `_shell.md`, name them for order (`01.png`, `02.png`), put `{{images}}` on that paper. Hidden `_` / `.` names stay off. Does not recurse. Does not auto-show if you omit the token. That slideshow is the room's own pictures — shared art goes in `mats/imgs/`.

---

## Out

A door that leaves the pocket. Click opens the OS browser — not a new Go window, not the desk.

```
{{outlink:https://example.com}}
{{outlink:https://example.com|the label}}
{{out:https://example.com|short}}
```

http and https only. Wiki `[[page]]` stays inside this host. Markdown `[label](url)` is still not parsed — write the token.

YAML can do the same: `podio: brochure` plus `podio_href: https://…` then `{{podio}}` on the page.

---

## ROM launch

Opens another Deck Host window via the ROM Launcher recipes (`launches.json`). Same glass as the start-menu cases. Does **not** leave to the OS browser.

```
{{rom:reqrep-414b|Open the bay}}
{{rom:great-road-mapper|Open the board}}
```

YAML: `open_the_bay: Open the bay` plus `open_the_bay_rom: reqrep-414b` then `{{open_the_bay}}`. `{key}_rom` wins over `{key}_href`.

---

## Frontmatter the reader honors

YAML at the top of a note or `_shell.md`. Fills (`{{title}}`, `{{the-key}}`) and `crate:` are what the page uses. Catalog data lives in the drawers, not in this slip. Put `{{headers}}` on a page if you want the YAML printed.

| key | does |
|---|---|
| `title:` | list label, `{{title}}`, second half of the window bar. |
| `author:` | `{{author}}`. |
| `color:` | accent, and bookstore cloth. Names: `red` `green` `purple` `blue` `amber` `yellow` `orange`. Or a `#hex`. On a lore card this is the strip. |
| `strip:` | lore card stripe only. A `#hex` (or a color name). Wins over `color:` for the strip. The card does not have to wear the room. |
| `cover:` / `jacket:` | picture filename (looked up like `{{img:}}` in `mats/imgs/`, then this host). Face-up jacket for `{{files}}` and for `{{cover}}` on the page. Spines stay cloth. |
| `icon:` / `favicon:` / `avatar:` / `faveicon:` | host face. A picture in `mats/imgs/` (or this host). Shows on start `{{doors}}` cards as a wee favicon. Also the tab icon while you are in that host. No picture → a letter tile from the title. `_hosts.yaml` can set `icon:` too. `cover:` is the jacket; this is the face. |
| `environment:` | loads `mats/styles/{name}.css`. Drop a css file there and the name works. A lore card born in that room reads the skin's `:root` for the strip: `--strip`, then `--card-strip`, then `--accent`, then `--stamp`. `var(--name)` in the same file (or an `@import`) resolves. A YAML `strip:` / `color:` on the card still wins. |
| `shell:` | `none` / `off` / `no` / `false` / `0` — this page will not wear a parent `_shell.md` shell. |
| `codeword:` | soft room gate on a folder `_shell.md`. Aliases: `password:` `lock:` `code:`. Visitors must enter the matching word before the room body shows. Unlock sticks in a session cookie for that host+shell path (and descendants that inherit the lock). Clear with `?cw=clear` on the page, or by clearing site cookies. Not crypto — a polite door. BIOS / librarian API writes stay ungated. |
| `tags:` / `tag:` | plus `#hash` in the body. `/ ?t=slug` lists notes with that tag. |
| `mark:` / `marks:` | comma list of registry words. A hit paints a floating rubber stamp on the paper (cabinets: librarian, detective, charlie, tps, cards). Unknown words stay quiet. Edit `~hosts/_marks.yaml` to add or override. |
| `crate:` | stable id (`crate.` + 16 hex). Does not follow the filename. Go mints it the first time the page is opened. `_shell.md` (the room) and `index.md` (the paper) each get their own. Guest `.chip` files bind the same id in `~librarian/{host}/_chip_crates.yaml` by `chip.uid`; a `crate:` on the chip is a courtesy sticker that may be restamped, never reminted. Drawers show it; click it for the crate report. The page body does not print it. |
| `threads-*` | Charlie chain. Any key starting `threads-`; the suffix is **who observed** that chain (`threads-mouse`, `threads-sam`, `threads-charlie`, …). Same grammar on every mouth. The reader does not paint this. Ocean ingest indexes it. |

Charlie grammar (on a `threads-*` line):

```
a*rel>b
a*rel>b,c
a*rel>b&other>d
a*rel>b; next*rel>to
bare-tag
```

`;` starts a new chain. `,` fans destinations. `&` keeps the same subject and adds another `rel>to`. Bare words (no `*`) are still tags. Rel names are free strings — they emerge from what gets written.

Mouse is the primary agent mouth, not required. She can thread as `sam` or `charlie`. Agents land playable lines in YAML; living names stay off Go.

---

## Also clay, not tokens

| write | does |
|---|---|
| `[[Note]]` or `[[Note\|label]]` | wiki. Resolves to a file of that name, **or a room**: a folder of that name, or the YAML `title:` on that folder's `index.md` / `_shell.md`. One hit goes there. `[[index]]` is not a name — halls stay hidden from the stem `index`. |
| `- [x] line` | marked bullet. See **Bullets**. |
| `#tag` | chip; click goes to the tag page. |
| `^crate.XXXX` | cite chip; click opens that crate's report. |
| `^OT-008.T01.B002.L03` | one chip-code chain, not three tags. OT / NT / ONT is the group, then the log number, trunk (`T`), branch (`B`), leaf (`L`). Using a cite mints `go.codes/OT/008/T01/B002/L03`. Click a depth to open that bin. The node lists notes that referenced it. |
| `# Heading` | ordinary markdown. `# {{title}}` is a heading that prints the YAML title. |

`[[wiki]]` and `#tags` are not `{{slots}}`. They just work.

---

The drawers live under **mypi:go**. In Deck Host that is the gem **Cabinets** menu (Window or Dock). In the IDE / a plain browser, the same mark docks a rail only — no window. Only one catalog dock at a time; BIOS can sit beside it. Dock again puts the overlay away. **Ctrl+Shift+O** or **Cabinets → All windows** opens every mouth as a rail (Deck Host). Already-open ones come forward.

---

## README

A drawer, not a token. **Ctrl+Shift+L** or gem **Cabinets → README**. Companion rail, BIOS dress: clean blue field, white type, yellow section marks. The Window pop-out is resizable from the corner — grow it while you edit. Two faces:

- **room** — one letter for the index of the section you are standing in (`~readme/{host}/…/README.md`). How we use this space. Unchanged.
- **page** — the vault note you are on. **headers** is the YAML front matter (no `---` fences). **markdown** is the body. Keep, **Ctrl+S**, or **Ctrl+Enter** writes the file. **Tab** indents two spaces (Shift+Tab peels them). A live `crate:` is never overwritten. The desk reloads so you see the clay. When the folder has both `index.md` (paper) and `_shell.md` (shell), the page face offers **paper** | **shell**. Default is paper. A nested folder with no `_shell.md` of its own still has paper: this folder’s `index.md`, created on Keep if it is missing — never the ancestor’s. **+shell** on a nested hall mints a **subshell** (`{{subshell}}` instead of `{{paper}}`) so it sits in the parent shell's paper hole — Big Box Co stays the campus, Products still gets a crate. The filename sits in the kicker so you can see which clay you are holding. A named note (`journal-entry-02.md`) is just itself — no extra tabs. Switch without Keep reloads from disk.
- **New** — writes a named `.md` into the folder you are standing in (this hall, or the parent of this note). Title in the YAML, crate minted on write. Does not spawn from the address bar. Does not overwrite. `index.md` / `_shell.md` stay Keep, not New. The desk opens the new page.

Not parchment.

---

## Librarian

A drawer, not a token. **Ctrl+Shift+B** or gem **Cabinets → Librarian**. Pop is a companion rail (440×760), booth color. Catalog card: two rectangular actions, then the filed meta and lore. Not ISSUE SLIP stamps.

Librarian catalogs the page you are on. Two actions:

- **Add Meta Data** — type (`time` `bool` `input` `textbox`), a label (autosuggest from labels already used for that type), and the value. Stored on the page's YAML in `pocket-go/~librarian/` (mirrors the host path). Off the hopper. Not wiki. Not `{{files}}`. Includes the page crate.
- **Add Lore** — class (autosuggest), title, a 255-character line, and an optional time (unix or a common datetime; blank is now). Writes one `.md` into `go.inbox/librarian/` named `{Title}-LORE_{n}.md`. The face is the body: type, house, title, line, and the crate id as a quiet serial. The back holds `crate` `source_crate` `edges` `from` `house` `tps`. `from` is the host plus the nearest `_shell` (the room), not a filename and not a `/?h=` door — files move; crate ids are the thread. `#hashes` written in the line travel with the card and show as Charlie hashes. Cabinet marks (Librarian catalog, TPS `created`, Charlie pins) stay in the sidecars and do not leave the pocket with the file. Own crate is minted on write. Skin is `environment: lorecard`. Detective cards land at `go.trays/detective/` (`go.inbox/agent/` still finds them). On write, Librarian files three ordinary fields on the new card: `class` = lore card, `author` = The Librarian / Detective / Charlie, `card type` = the deck. TPS stamps `created` on the card. Live labels are never overwritten.
- **Attach Lore** — pick an existing card from this mouth and pin this page’s crate onto its `edges`. The card is the edge: click it, hop the crates it touches. Born-on stays `source_crate` / `from`. Cabinets list a card on every page it touches.
- **Edit Lore** — **edit** on a card in this drawer. Same class / title / line / time. Writes that file. Crate, edges, and from stay. Time blank keeps the stamp. The filename does not rename.
- **Pop** — **pop** beside edit. Opens a small copy of the card (`/?card=`) as a sheet. Float and close. The pop prints the face and the back: every YAML field held on the card (`from`, crate ids, `tps`, house, type). The inbox page stays the face only. Not a here: the desk and cabinets stay. The title on the row still takes the desk to the inbox note, for tagging.

The drawer lists this page's fields and lore. Old ISSUE SLIP thoughts are not migrated. Click a field label to open a ledger of other pages that share it — same idea as Charlie, not Charlie's words, not `#tags`. Chests are **by that field** (`author` — one chest per author). Toggle **by host** / **by author** (the field name) on the sheet. Click a value as a motif, not as that one label: other fields on this mouth that wear the same chip, the other mouth, and lore cards whose title or class is the word (a multi-word phrase also matches a line). Theme *She Does Not Hear Herself* finds the Detective card of that name. *buddy* on about is also *buddy* on author. A crate id (`crate.` plus sixteen hex) is a door to the crate report, not a catalog of the word. Click opens a report sheet, dressed as **mypi:lib** (booth green, manila slip). No address bar. The page and the cabinets stay. A note title on the sheet sends the desk there. A value chip drills into that motif; the field name drops back to the whole label. **edit** opens the same modal on that row; **×** drops the field. Comma-separated input values still split for research (`Brancrug, Paris`), so a date with a comma is one field you amend if it should stay whole. `{{meta}}` can print those chips onto a page if you want them visible; you do not need the token to research.

Wiki, tags, and `{{slots}}` stay inside the host you are standing in, so `[[wiki]]` on a lore card will not resolve a name from `go.build`. Hop back by crate, not by a stored path.

---

## Detective

A drawer, not a token. **Ctrl+Shift+A** or gem **Cabinets → Detective**. Same companion rail as Librarian (440×760). Dress is the stamp-red cabinet: dirt shell, hot head, manila scan. Red of the four. (Used to be called Agent — that name still opens this drawer.)

Detective indexes the page you are on. Same two actions as Librarian, different shelf:

- **Add Meta Data** — same types (`time` `bool` `input` `textbox`). Labels live on their own bank (`faction`, `case`, whatever you file). Stored in `pocket-go/~detective/` (mirrors the host path). Off the hopper. Includes the page crate. Librarian's YAML on the same page is a different file.
- **Add Lore** — same card object (`class` `title` `line` `house` `from` `source_crate` `edges` `tps`). Writes one `.md` into `go.trays/detective/` named `{Title}-LORE_{n}.md`. `house: DETECTIVE`. Own crate on write. Same face. Same TPS `created`. Same Librarian catalog stamp.
- **Attach Lore** — same picker as Librarian. Pins this page onto a Detective card’s `edges`.
- **Edit Lore** — same as Librarian, this house’s cards.
- **Pop** — same small copy as Librarian.

The drawer lists this page's detective fields and the lore *this mouth* filed. Librarian lore on the same crate stays in the Librarian drawer. Click a field label to open Detective's ledger for that filing — **mypi:hunt**, stamp red, a report sheet, no address bar. Same host / field toggle as Librarian. Click a value as a motif, same as Librarian: other fields, Librarian's shelf, lore titles. Same edit / × as Librarian. One trays host, a tray per mouth. `go.agent` is a different host (the lookout) and is not this cabinet.

---

## Charlie

A drawer, not a token. **Ctrl+Shift+C** or gem **Cabinets → Charlie**. Companion rail (440×760), amber phosphor term — yellow of the four, not green, not a cork board. Charlie is the weaver: tags as a buffer, not scraps.

Charlie tags the page you are on. The term is three boxes: **from * rel > to**. Enter writes. Fill one box and it is still a pin (comma splits into several). Fill two or three and it is a thread. Empty rel with both ends means `is` (`aaron` / · / `ava` → `aaron*is>ava`). Commas fan that box (`ava, danielle`). × drops that pin or that thread. Click a name — pin, **from**, **rel**, or **to** — for Charlie's lookup. Same idea as the old Dewey `by_tag` reports and Charlie `by_aven` / `by_relativity` / `by_insect` chests: one word, every chain it sat in. The ledger lists **as from**, **as connector**, **as to**, **as pin**, then **as hash** (`#word` in a note body, or YAML `tags:`). One door: `/?c=`. Body hashes are not a second search. The word you filed is the word you search (`jsn` is not `json`). The lookup wears **mypi:bay** — Charlie phosphor CRT, compact rows, crate and path as quiet meta. Click opens a report sheet. No address bar. The page and the cabinets stay. A note title on the sheet sends the desk there. The Charlie cabinet lists **threads**, **tags**, then **hashes**. Tags are pins you wrote on the term (no `#`, × unpins). Hashes are `#word` printed on this note (body, YAML `tags:`, or a lore card’s `line`) — a view of the page, not a pin. Click a tag and the lookup opens as a tag (as pin first). Click a hash and it opens as a hash (`#word`, as hash first). Same listings either way. A global hit for this note says **here**.

**Add Lore** — same card object as Librarian and Detective. Writes one `.md` into `go.inbox/charlie/` named `{Title}-LORE_{n}.md`. `house: CHARLIE`. Own crate on write. Same face. Edges stay crate ids on the back, not printed on the face. The cabinet lists this page’s lore above the threads and tags (title, class, house, the line). Add Lore shows which page it will stamp; the rail asks the desk again before it files, so a stale sidecar cannot pin the card to the blotter. **Attach Lore** pins this page onto an existing Charlie card. **edit** on a card in this drawer amends class / title / line / time. Crate, edges, and from stay. **pop** opens a small copy.

Tags and threads live in `pocket-go/~charlie/` (mirrors the host path). Lore lives in the inbox tray. Not catalog meta — that's Librarian / Detective. Charlie weaves the words.

---

## TPS

A drawer, not a token. **Ctrl+Shift+T** or gem **Cabinets → TPS**. Companion rail (440×760), carbon time-card. The fifth mouth. Time Machina still walks glass logs; this drawer stamps **Go pages**.

TPS files named dates on the page you are on. **Add date**: a title (`created`, `referenced`, or any title you type — the title is the metadata) and a when. The clock picker is an instant. **As known** is what the paper actually said: a year (`1999`), a month (`March 1999`), a day (`2001-02-24` / `24 February 2001`), or a unix. Stored in `pocket-go/~tps/` (mirrors the host path). Off the hopper.

**Pin event** tags this page onto a named event. Title is the event name (find or mint). Optional **event code** is the filename on `go.code.event` (`EV-001.md`). Leave the code blank and TPS assigns the next `EV-00n`. Optional **perspective** is the sit. Body is what happened here, this time. Event codes are a separate bank from Glass Compost chip codes (`go.code.glass` / `^OT-…`). A `^EV-001` cite is that event page, not a compost ZIP. Clocks stay **created** / **referenced**.

People codes live on `go.code.people` (`MIS-777.md`). Eddy still prints the YAML face from the Encoder paper folder. A `^MIS-777` cite is that person slip, not a compost ZIP. `OT` / `NT` / `ONT` / `EV` stay the other banks.

**Created** and **referenced** are the clocks that count. Do not stamp bulk `imported on`. Do not stamp last-write from a file transfer — copy day, vault write, hopper dump. Those pile every page on the same C and wreck the report.

The drawer lists each stamp (title and the date as known). Slices under that are only the pieces that stamp actually has — **year**, and month / day / hour when those were on the paper. A year-only stamp is `1999`. It does not sit in January or at midnight. Click a chip to open the TPS report as a sheet. No address bar. Inside the report you **narrow** by the slices that exist. Those combine. Click a column head to sort. Chests are the date type (`created`, `referenced`), not "as slice". Columns are when, page, environment, path.

Click a title in the drawer for every page that used that title. Click the date for that instant. The bay is **mypi:tps**.

Not Librarian meta. Vault and author stay in Librarian. Charlie still weaves words.

---

## Crate

The crate is the page. Click the crate chip in any drawer — or a crate sitting in another lookup — to open the crate report. One door: `/?k=`.

The report is every cabinet on that one page. **headers** first — the YAML on the paper, the hidden cabinet. Librarian and Detective sit next, then TPS, then lore cards as a tile grid, then Charlie pins and hashes as chips. Empty chests stay off. Click the crate — or a Charlie thread, or a Librarian / Detective / TPS chip — and it launches a report sheet. The page you were on stays. Not an overlay. Not a browser tab. No address bar. No DESK. A note title on the sheet sends the desk there; the sheet stays the sheet. House dress stays (cardboard crate, phosphor Charlie, manila Librarian, stamp Detective, carbon TPS). No blinking cursor. Resize from the corner. The report is not a here: README / Charlie / TPS / Librarian / Detective keep following the desk. You write on the page you are standing on. The sheet does not steal them.

A lore card on the sheet is a fragment, not the printout. The house is the catalog stamp (**Charlie**), then **lore card**, then the deck (**Name Game**), then the title (**Jax**) as one tag line. The crate id stays inside the tile. Maker does not read as the name. The line lives on the card. Other makers later are the same grammar.

Not a sixth mouth. The crate is the box the five already share.

A lore card is still a crate on the backside. Do not mint `card.` ids. Edges, `^crate.`, hop, and the crate report all key off `crate.`. The face is a card; the nail stays a crate.

Opening the inbox note used to wear the tray hall (crumb, paper slot, a scrap on a blotter). A filed card now stands as the card: window title is `class · title` (Name Game · Jax), and the top strip / kicker pick up the born-on room’s skin (`--accent` on that environment), or a `strip:` / `color:` hex on the card. Title click from a cabinet still goes there so you can tag. A printed `{{faces}}` card is the same door — click the face, not a hash on it. **pop** is the small copy when you only wanted to look.

## Type catalog

`/styles/fonts.css` — shared Google `@import` + local `@font-face` + `--font-*` roles (arcade, glass, px437, …). Specimen: `go.law` → [[type]]. Files: `mats/styles/fonts/`.

## BIOS Help

Editable field manual in BIOS → **help** door. Pages live in `~help/` (`_index.md`, `tokens.md`, `type.md`, …). API: `/api/help`. Law archive stays at `go.law`.
