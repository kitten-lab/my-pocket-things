---
title: Layouts
deck: shell bones you do not invent from scratch
---

# Layouts

You are not supposed to invent grid from a blank coat every time.
These are **bones** — structure only. Dress (colors, type, paper) lives on the room letter `environment:` coat.

Ported from retired pocket-internet `~shells` + `~styles/forShells`.

## How to use

1. Pick a bone below.
2. Put the matching CSS skeleton at the top of your coat (or copy a starter under `mats/styles/layouts/`).
3. Keep inventing on color/type/paper — not on "where does the rail go."

Shell `_shell` holds the **slots** (`{{crumb}}`, `{{paper}}`, `{{doors}}`, etc.).
Room letter holds the **dress**.

---

## 1. Rail (header + side nav + body + footer)

Retired name: `default`

```
┌──────── header ────────┐
│ nav │      main        │
└──────── footer ────────┘
```

```css
.go-shell {
  display: grid;
  grid-template-rows: auto 1fr auto;
  grid-template-columns: 12rem 1fr;
  grid-template-areas:
    "head head"
    "rail main"
    "foot foot";
  min-height: 100%;
}
.go-shell .mast,
.go-shell .crumb { grid-area: head; }
.go-shell .doors,
.go-shell nav { grid-area: rail; }
.go-shell .go-paper,
.go-shell main { grid-area: main; }
.go-shell .foot,
.go-shell footer { grid-area: foot; }
```

Good for: halls with a permanent door list.

---

## 2. Stack (header → nav → body → footer)

Retired name: `simple`

```
┌──── header ────┐
│      nav       │
│     main       │
└──── footer ────┘
```

```css
.go-shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}
.go-shell .go-paper {
  flex: 1;
  max-width: 50rem;
  margin: 1.2rem auto;
  width: calc(100% - 2.4rem);
}
```

Good for: quiet reading rooms, notebooks, journals.

---

## 3. Stream (nav + mast + long body + foot)

Retired name: `leak`

```
│ nav (thin) │
│   mast     │
│  stream…   │
│   foot     │
```

```css
.go-shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}
.go-shell .doors { /* thin top or sticky */ }
.go-shell .mast { /* big title band */ }
.go-shell .go-paper {
  flex: 1;
  max-width: 42rem;
  margin: 0 auto;
  width: calc(100% - 2rem);
}
```

Good for: logs, leaks, long vertical reading.

---

## 4. Notebook page (journal default)

Not a multi-region shell — one paper sheet on a desk.
Already lived as `mats/styles/journal.css` (Literata on cream paper, red margin rule, green desk).

Use when the room *is* the page, not a building with wings.

---

## PocketGo mapping cheat

| retired drop spot | PocketGo-ish home |
| --- | --- |
| header / mast | `{{.mast}}` / title band |
| navigation | `{{doors}}` |
| body | `{{paper}}` |
| footer | chips / uses / headers block |

Edit this page anytime. Add a fifth bone when you invent one worth keeping.
