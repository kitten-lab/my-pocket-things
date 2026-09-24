---
crate: crate.F2A59287891D7798
title: Tokens
deck: full slot / dress / clay map — from KEYS.md
---

# Tokens

How clay talks to the reader. Tokens are `{{like this}}`. They work in any `.md` under a go.* host and on start. The skin (`environment:`) decides how a list *looks*; the token decides *what* is listed. Tool slots also accept `{{tool:codelook}}` (same as `{{codelook}}`) so a local YAML key can keep `{{word}}` later.

Canonical long map: vault-root `KEYS.md`. This Help page is the editable field card — keep it complete when a new token lands.

## Special filenames

| file | job |
| --- | --- |
| `_shell.md` | optional shell. `{{paper}}` = dress chrome. `{{subshell}}` instead = nest in the next shell's paper hole. Own crate either way. |
| `index.md` | blotter / paper that fills `{{paper}}`. Hidden from `{{files}}`. Own crate (the fill). |
| `recent.md` | lobby jump list. bar says `recent`. Last 25 kept notes. |

Names starting `~` or `.` stay off lists. Underscore folders are ordinary. `_shell.md` is never a listed note. Pictures: `mats/imgs/`. Skins: `mats/styles/`.

---

## Slots (lists & holes)

| token | also | prints |
| --- | --- | --- |
| `{{files}}` | | notes in **this folder** (not subfolders) |
| `{{spines}}` | | same notes, `spines` class (shelf spines) |
| `{{navbar:files}}` | `{{nav:files}}` / `{{navfiles}}` | same strip as navbar, but files in this hall (not folders) |
| `{{navbar}}` | `{{nav}}` | child folders of this hall as a simple link strip (not door cards) |
| `{{doors}}` | `{{worlds}}` | **subfolders** as door cards. On Go, native hosts only. |
| `{{doors:chips}}` | `{{worlds:chips}}` | doors as chips |
| `{{doors:cards}}` | `{{worlds:cards}}` | doors as cards (explicit) |
| `{{doors:roam}}` | `{{roam}}` | connected roam libraries as door cards |
| `{{dir}}` | `{{list}}` | notes **and** subfolders together |
| `{{dirtree}}` | | nested file tree, **3 levels** from this page's folder (same hide rules as `{{dir}}`) |
| `{{tree}}` | `{{dirtree:shell}}` | file tree rooted at the dress shell. Folders open and close. Open path stays open. |
| `{{paper}}` | `{{insertdata}}` | hole in a dress `_shell.md` — filled with `index.md`, the opened note, or a nested subshell |
| `{{subshell}}` | | hole in a nested `_shell.md` — sits in the next shell's `{{paper}}`; this chrome wraps the inner page |
| `{{images}}` | `{{slides}}` | images in **this folder** as slideshow (+ thumb rail) |
| `{{faces}}` | `{{cards}}` | body of each note in the open hall as a face grid |
| `{{face:crate.XXXX}}` | `{{card:crate.XXXX}}` | one note anywhere under `~hosts` by crate (16 hex; `crate.` optional) |
| `{{link:crate.XXXX}}` | `{{crate:XXXX}}` | plain title link to that crate (`/?k=`); optional `\|label` |
| `{{cover}}` | `{{jacket}}` | this page's cover object (`cover:` / `jacket:` YAML) |
| `{{shelf}}` | | page card shelf for this place |
| `{{tagsearch}}` | | tag search form. Clay: drop on any page, not only go.tags |
| `{{taglook}}` | | tag look block for this page |
| `{{codesearch}}` | | chip-code search / mint. Clay: drop on any page, not only go.codes |
| `{{codelook}}` | | notes that cited this chain address |
| `{{huntsearch}}` | | keyword hunt across thought slips. Clay: drop on any page |
| `{{huntlook}}` | | hunt hits for the current query |
| `{{erasearch}}` | | keyword look across named eras and their TPS tags. Clay: drop on any page |
| `{{eralook}}` | | noted eras, then every TPS tagging, linking back to the page |
| `{{loresearch}}` | `{{cardsearch}}` | keyword look across filed lore cards. Clay: drop on any page, not only go.trays |
| `{{lorelook}}` | `{{cardlook}}` | lore hits for the current query |
| `{{compost}}` | | compost headline, cut note, and tags at this ZIP. Accepted Agent Eyes shots lead (log throughline + trunks); handwritten cuts stay secondary. Stamps the first-to-last sitting (local date and clock, or a span if it crosses days). On a log (OT-001), yard-face tags and energy go into the librarian as `references` / `energy` and into Charlie as threads, not as page hashes. Compost `title` and yard message `chip_id`s rewrite on peek as librarian `title` / `messages` (trunk and branch hold the messages inside that cut; a leaf holds its parent message). The whole log's message list stays off the log paper. Branch and leaf papers also print the live message under the code; trunk and log stay code-only. Stamps the message `create_time` into TPS as `created`. Does not mint extra codes pages. |
| `{{recent}}` | `{{recent:N}}` | last 25 kept notes/canvases across the pocket (mtime). Type `recent` on the bar. Cap 100. |
| `{{flip}}` | | prev/next nav as a flipper |
| `{{prev}}` | | previous sibling note link |
| `{{next}}` | | next sibling note link |

If a page has **none** of `{{files}}` / `{{spines}}` / `{{doors}}` / `{{dir}}` / `{{dirtree}}` / `{{tree}}` / `{{images}}` / `{{faces}}` / `{{recent}}`, the reader appends doors (at start) or a full `{{dir}}` (elsewhere).

Every slot also answers `{{tool:name}}` - `{{tool:codelook}}`, `{{tool:doors:roam}}`. Bare `{{codelook}}` still works.

---

## Crumbs & home

| token | also | prints |
| --- | --- | --- |
| `{{crumb}}` | `{{bread}}` | full trail `home / folder / note` |
| `{{shellcrumb}}` | | trail from nearest `_shell.md` shell to here |
| `{{crumbback}}` | | one step up |
| `{{home}}` | `{{root}}` | door to nearest `_shell` walking up (room title). No shell → host root |

---

## Cabinet fields

| token | also | prints |
| --- | --- | --- |
| `{{lib:label}}` | `{{librarian:label}}` | Librarian field value only (no label) |
| `{{det:label}}` | `{{detective:label}}` / `{{agt:label}}` / `{{agent:label}}` | Detective field value only |
| `{{tps:label}}` | | TPS stamp when(s) for that title (value only) |
| `{{chip:lib:label}}` | `{{chip:tps:label}}` / `{{chip:det:label}}` | one tiny labeled chip (same atom as meta drops) |
| `{{meta}}` | `{{chips}}` | every cabinet's chips in one strip |
| `{{meta:librarian}}` | `{{meta:lib}}` / `{{chips:librarian}}` | Librarian chips only |
| `{{meta:detective}}` | `{{chips:detective}}` / `{{meta:agent}}` | Detective chips |
| `{{meta:tps}}` | `{{chips:tps}}` | TPS chips |
| `{{meta:all}}` | | same as bare `{{meta}}` |
| `{{edges}}` | | lore-card edge crates as doors |
| `{{headers}}` | | this page's YAML as a folded slip (`crate:` omitted) |
| `{{injector}}` … `{{/injector}}` | | insert form. Clay outside hidden is the page. `{{hidden:frontmatter}}` is YAML. `{{hidden:lib}}` / `{{hidden:tps}}` file that cabinet. Minted note prints in injector order. |

Missing cabinet label → blank. Multi → comma-joined. Charlie is weave, not these tokens.

---

## This page (YAML fills)

`{{the-key}}` prints any frontmatter key on **this file**. Empty/missing → nothing (no leftover braces). Wiki in a field stays links.

Common: `{{title}}` `{{author}}` `{{environment}}` `{{aliases}}` `{{color}}` `{{crate}}` — any key the note has.

If `{key}_href:` is a path starting `/`, `{{key}}` becomes an in-pocket door. If `http(s):`, it becomes an **outlink**.

Slots win over YAML names: `{{files}}` `{{paper}}` `{{crumb}}` etc. are never treated as YAML.

---

## Uses

On a **note** (not a folder shell):

| token | also | prints |
| --- | --- | --- |
| `{{uses}}` | `{{bags}}` | same-stem files + inbound `[[wikilinks]]` |

Omit it and the block may append at the bottom when there is something to show.

---

## Dress

Safe names: letters, numbers, `_`, `-`.

**Lead** (start of paragraph/heading):

```
{{.mast}}THE BOOKSTORE
{{.ff-arcade}}type sample
{{#some-id}}
{{.class#id}}both
```

**Span** (inline, or one per line — rest of the line is the span; close is optional):

```
{{span:accent}}kitten{{/span}}
{{span:.mute#here}}quiet{{/span}}

{{span}}Home
{{span}}Products
{{span}}Contact
```

**Div / block** (own line, or content on the same line):

```
{{div:device}}
{{div:sheet}}
inside
{{/div}}
{{/div}}

{{div:.main-title}}HOME OF N&N
{{/div}}

{{div:.button}}INFORMATION{{/div}}
```

`{{block:name}}` / `{{/block}}` = same as div. Nest; close what you open.

---

## Images

```
{{img:typing-computer.gif}}
{{img:typing-computer.gif|alt text}}
![[typing-computer.gif]]
![[typing-computer.gif|alt]]
![alt](typing-computer.gif)
```

Lookups `mats/imgs/`, then this host.

---

## Outlinks

Leaves the pocket (OS browser):

```
{{outlink:https://example.com}}
{{outlink:https://example.com|the label}}
{{out:https://example.com|short}}
```

http/https only. Wiki `[[page]]` stays inside. Markdown `[label](url)` is not parsed — write the token.

---

## ROM launch

Opens another Deck Host window. Recipe ids live in ROM Launcher `launches.json`.

```
{{rom:reqrep-414b|Open the bay}}
{{rom:great-road-mapper|Open the board}}
```

YAML: `{key}_rom:` plus `{{key}}`. Wins over `{key}_href`.

---

## Bullets (marks)

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
```

Bare bujo (`- . task`, `- x done`) still reads. Rooms dress via `ul.bullets > li[data-mark="…"]`.

---

## Also clay, not `{{slots}}`

| write | does |
| --- | --- |
| `[[Note]]` / `[[Note\|label]]` | wiki inside this host |
| `#tag` | chip → tag page |
| `# Heading` | markdown heading (`# {{title}}` works) |
| `^crate.XXXX` | cite chip to crate |

---

## Frontmatter the reader honors

| key | does |
| --- | --- |
| `title:` | list label, `{{title}}`, window bar |
| `author:` | `{{author}}` |
| `color:` / `strip:` | accent / lore strip |
| `cover:` / `jacket:` | picture for `{{files}}` / `{{cover}}` |
| `icon:` / `favicon:` / `avatar:` | host face on start door cards + tab icon |
| `environment:` | loads `mats/styles/{name}.css` |
| `shell:` | `none`/`off`/… — do not wear parent shell |
| `codeword:` | soft lock on `_shell.md` (aliases `password:`/`lock:`/`code:`). Session cookie unlock; `?cw=clear` to forget |
| `section:` | doors grouping on start |
| `tags:` / `tag:` | plus `#hash` in body |
| `mark:` / `marks:` | comma list of registry words. A hit paints a floating rubber stamp (cabinets: librarian, detective, charlie, tps, cards). Unknown words stay quiet. Registry: `~hosts/_marks.yaml` |

---

## Drawers (not tokens)

Librarian, Detective, Charlie, TPS, Crate reports — cabinets / Ctrl shortcuts. Full map in `KEYS.md`.

Type specimens: Help → Type, or `go.law` → type. Fonts: `/styles/fonts.css`.
