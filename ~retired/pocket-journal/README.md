```
=================================================
  MY POCKET THINGS · POCKET JOURNAL
  CO.MYPT-003-JOURNAL · .bok books · human+agent
=================================================
```

**My Pocket Journal** — fork of Pocket Notebook so that app can stay stable.

Same front face (recents + spine shelf → open cloth book).  
**Different bones:** each journal is a **`.bok` package** on disk — Markdown pages agents and you read the same way.

### Why a fork

Notebook keeps work-brain / daily tracker in `library.json`.  
Journal is for **what we made / why / bag pulls / SDK-for-us** without trashing Notebook while we change storage and editing.

Producer: still under `my-pocket-things/` for now. Rehome to Chester later if you want — don’t freeze on the label.

### Desk wiring (required on this island)

| | |
|--|--|
| **ROM Cat** | `pocket-journal` · `CO.MYPT-003-JOURNAL` · `launcher_show: true` |
| **Launcher recipe** | `pocket-journal` → `run-in-deck-host.py` · port **43166** |

A product that isn’t in Cat + Launcher isn’t on the desk. File both when you add a sibling.

### Run

```bat
cd C:\ALICE_BOX\my-pocket-things\pocket-journal\prod
run-journal.bat
```

- Deck Host · port **43166** · or open from **ROM Launcher** after Cat refresh
- Browser: `run-journal-browser.bat` → http://127.0.0.1:43166/

### Storage (type A)

```text
prod/
  journal_sys/           ← code only
  safe_box/books/*.bok/  ← operator packs
  safe_box/shelf.json
```

- **Canonical** = Markdown in `safe_box` (not under `*_sys/`).  
- House layout: same as sopr / lore-box / notebook.

### Edit (always on · honest)

No E / view flip. Open page = **markdown source** on the paper (you type `#`, `**`, lists yourself).  
Same bytes as the `.md` in the `.bok`. No contenteditable, no B/I toolbar, no fake WYSIWYG  
(that path was broken — stuck headers/lists/ghost text).  

True Obsidian live-preview (type `#` → styled line, table widgets, etc.) is a real editor engine  
(CodeMirror/ProseMirror), not a weekend `execCommand`. Not claimed until we do that job properly.

Ctrl+S / SAVE. Flip page / shelf auto-harvests.

### Keys

Same pocket grammar as Notebook: N · E · T · B · ← → · Alt↑↓ · Esc · Ctrl+S.

### Seed

First launch creates **Project Map** (ROM Launcher + Notes & Chords pages from the bag ritual) and **Field Journal** (blank-ish).
