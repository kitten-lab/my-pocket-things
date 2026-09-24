
# Pocket Go keys

How clay talks to the reader. Tokens are `{{like this}}`. They work in any `.md` under a go.* host (a folder in `~hosts/`) and on the start page. The skin (`environment:`) decides how a list *looks*; the token decides *what* is listed.

Two special filenames:

| file | job |
|---|---|
| `_shell.md` | optional shell for a folder. If it contains `{{paper}}`, notes in that folder (and below) wear this chrome. |
| `index.md` | the blotter / paper that fills `{{paper}}`. Hidden from `{{files}}` so it does not list itself. |

Names that start with `~` or `.` stay off the lists. Underscore folders are ordinary (they sort above A-Z). `_shell.md` is never a listed note. Pictures live in `mats/imgs/`. Skins live in `mats/styles/`.

---

## Hosts

The address bar is `go.{host}/path`. Hosts are not a hardcoded list. Home is not a host.

| lives at | becomes |
|---|---|
| `~hosts/start.md` | `/` — the front door. bar says `start` |
| `~hosts/{name}/` | `go.{name}` as soon as the folder exists |
| `~hosts/_hosts.yaml` | optional aliases and titles. not required. a folder still resolves without a line here |

Type `go.terminal/` in the bar when that room is there. Type a name that has no folder yet and the pocket says the room isn't here *now* — not that it can never be. `library` is just another possible folder: `~hosts/library/` → `go.library`.

Wiki, tags, images, and `{{slots}}` stay inside the host you are standing in. On start, `{{doors}}` lists host folders as `go.*` doors. Librarian / charlie / readme for a named host live under that host's name (`~librarian/terminal/…`). The start page uses the unprefixed drawer (`~librarian/_index.yaml`).

Outside worlds are only the drawers. Not another vault beside hosts.

---

## Slots

Put these where you want the machine to print a list or a hole.

| token | also | prints |
|---|---|---|
| `{{files}}` | | notes in **this folder** (not subfolders). Bookstore paints them as face-up covers. On `_shell.md` this repeats on every note that wears the shell — put it on `index.md` if it should only be the folder hall. |
| `{{spines}}` | | same notes as `{{files}}`, with a `spines` class. Bookstore paints them as shelf spines. |
| `{{doors}}` | `{{worlds}}` | **subfolders** as door cards (name + note count). |
| `{{dir}}` | `{{list}}` | notes **and** subfolders together. |
| `{{paper}}` | `{{insertdata}}` | hole in a `_shell.md` shell. Filled with that folder’s `index.md`, or with the note you opened. |

If a page has **none** of `{{files}}` / `{{spines}}` / `{{doors}}` / `{{dir}}`, the reader appends doors (at vault root) or a full `{{dir}}` listing (everywhere else).

---

## This page

These read **the file you are in** (its YAML). `{{the-key}}` prints that field. Empty or missing → nothing (no leftover token). Wiki `[[links]]` in a field stay links.

`{{title}}` and `{{author}}` are just the common ones. `{{environment}}` `{{aliases}}` `{{color}}` — any key the note actually has.

Slots still win: `{{files}}` `{{paper}}` `{{crumb}}` and the other list/hole tokens are not YAML.

Window bar is separate: nearest `_shell.md` `title:` , then this page’s `title:`.

---

## Crumbs

| token | also | prints |
|---|---|---|
| `{{crumb}}` | `{{bread}}` | full trail: `~/ / folder / note` |
| `{{shellcrumb}}` | | trail from the nearest `_shell.md` paper-shell to here |
| `{{crumbback}}` | | one step up: parent title (or `~` at root) |

---

## Uses

On a **note** (not a folder shell), the reader also finds other files with the same stem and pages that `[[wikilink]]` this name.

| token | also | prints |
|---|---|---|
| `{{uses}}` | `{{bags}}` | that block, right here. |

If you omit it, the drawer is appended at the bottom when there is something to show — folded like `headers`. The floor of a page does not list every inbound `[[link]]`.

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

**Span** — inline:

```
{{span:accent}}kitten detective{{/span}}
{{span:.mute#here}}quiet{{/span}}
```

**Div / block** — each on its own line:

```
{{div:side}}
{{div:card}}
inside
{{/div}}
{{/div}}
```

`{{block:name}}` / `{{/block}}` is the same as `div`. Nest them. Close what you open.

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

---

## Frontmatter the reader honors

YAML at the top of a note or `_shell.md`. Other keys are kept (headers drawer). Any of them can print with `{{the-key}}`.

| key | does |
|---|---|
| `title:` | list label, `{{title}}`, second half of the window bar. |
| `author:` | `{{author}}`. |
| `color:` | accent, and bookstore cloth. Names: `red` `green` `purple` `blue` `amber` `yellow` `orange`. |
| `environment:` | loads `mats/styles/{name}.css`. Drop a css file there and the name works. |
| `shell:` | `none` / `off` / `no` / `false` / `0` — this page will not wear a parent `_shell.md` shell. |
| `tags:` / `tag:` | plus `#hash` in the body. `/ ?t=slug` lists notes with that tag. |

---

## Also clay, not tokens

| write | does |
|---|---|
| `[[Note]]` or `[[Note\|label]]` | wiki. Resolves to a file of that name. |
| `#tag` | chip; click goes to the tag page. |
| `# Heading` | ordinary markdown. `# {{title}}` is a heading that prints the YAML title. |

`[[wiki]]` and `#tags` are not `{{slots}}`. They just work.

---

## Librarian

A drawer, not a token. **Ctrl+B** or the gem menu item **Librarian**. Composer at the top; thoughts drop below. Click a slip to amend it (same `LBR-` id). **Ctrl+Enter** keeps the amendment; **Esc** cancels. Void still drops. The visitor page does not change.

Notes live beside the vault, not in it: `pocket-go/~librarian/` mirrors the host path as `.yaml` (`~librarian/` for start, `~librarian/{host}/` for a go.* room). Off the hopper. Not wiki. Not `{{files}}`.

Marks are **in the leaf**, not extra fields. Parsed on store; painted only in the drawer.

| sigil | meaning | example |
|---|---|---|
| `#` | simple tag | `#glenshadow` |
| `$` | namespace | `$names` `$oix` |
| `@` | time marker | `@1996` `@3:33` |
| `^` | cite chip | `^OT-093.T01.B011` `^crate.ABC` |

`# heading` with a space is not a tag. Charlie `a*rel>b` stays raw in the leaf. `^` is not resolved against glass. A note is another thought — there is no second field.
