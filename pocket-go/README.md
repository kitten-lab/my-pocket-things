```
=================================================
  MY POCKET THINGS · POCKET GO
  CO.MYPT-004-GO · early internet · WWW chrome
=================================================
```

**My Pocket Go** — a little net. Worlds as pages. Deck Host dresses as a Win 3.1 WWW explorer for this ROM: the blue title bar and address bar *are* the window chrome (`data-deck-chrome`). Not a library. Not a terminal.

Vault clay lives in [`~library/`](./~library/) (the Obsidian root). Reader code lives in `prod/www_sys/`.

### Run

```bat
cd C:\ALICE_BOX\my-pocket-things\pocket-go\prod
run-go.bat
```

- Deck Host · port **43210**
- Browser: `run-go-browser.bat` → http://127.0.0.1:43210/

### Address bar

Pocket paths, not `?p=`:

- `/` — home (`~library/_index.md`)
- `/Chester's Imports/` — folder
- `/Chester's Imports/.../note.md` — note

Wiki `[[links]]` still resolve. Extra skins via note frontmatter `environment: terminal-io` → `www_sys/styles/terminal-io.css`.

Home (`/`) is [`~library/_index.md`](./~library/_index.md). Drop `_index.md` in any folder the same way — optional. Tokens: `{{doors}}` folder cards, `{{files}}` the note/folder list. Look: `prod/www_sys/index.css`. Don't need to touch `server.py`.

GO on a path that is not a vault path is a later pocket door (my-pocket-internet rooms). Not this cut.

### Vault

Default: `pocket-go/~library`. Override: `BONEYARD_VAULT`.

Worlds were copied here from `C:\_BONEYARD`. When nothing has that folder open (Obsidian / Cursor), turn the old path into a junction:

```bat
rename C:\_BONEYARD _BONEYARD_PRE_LIBRARY
mklink /J C:\_BONEYARD C:\ALICE_BOX\my-pocket-things\pocket-go\~library
```

Until then, open Obsidian on `pocket-go/~library`. `C:\_BONEYARD\go-boneyard.bat` already launches this ROM.
