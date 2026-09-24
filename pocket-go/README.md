```
=================================================
  MY POCKET THINGS · POCKET GO
  CO.MYPT-004-GO · early internet · WWW chrome
=================================================
```

**My Pocket Go** — a little net. Worlds as pages. Deck Host dresses as a Win 3.1 WWW explorer for this ROM: the blue title bar and address bar *are* the window chrome (`data-deck-chrome`). Not a library. Not a terminal.

Worlds live in [`~hosts/`](./~hosts/). Home is [`~hosts/start.md`](./~hosts/start.md). A folder there is `go.(name)` the moment it exists. Skins and pictures live in [`mats/`](./mats/) (`styles/`, `imgs/`). Reader chrome lives in `prod/www_sys/`. Drawers (librarian, charlie, readme, agent) live beside the worlds — not visitor pages, not hosts.

### Run

```bat
cd C:\ALICE_BOX\my-pocket-things\pocket-go\prod
run-go.bat
```

- Deck Host · port **43210**
- Browser: `run-go-browser.bat` → http://127.0.0.1:43210/

### Address bar

Pocket paths, not `?p=`:

- `/` — start (`~hosts/start.md`)
- `go.terminal/` — a host, if `~hosts/terminal/` exists
- `go.stores/bookstore/note.md` — a note in a host

Wiki `[[links]]` still resolve, inside the host you are on. Extra skins via note frontmatter `environment: terminal-io` → `mats/styles/terminal-io.css`.

Home (`/`) is [`~hosts/start.md`](./~hosts/start.md). Drop `_shell.md` in any host folder the same way — optional. Every `{{token}}` is listed in [`KEYS.md`](./KEYS.md). Look: `prod/www_sys/index.css`. Don't need to touch `server.py`.

Type `go.{name}/` in the bar. If that folder is not in `~hosts/` yet, the pocket says the room isn't here now. Hosts are found, not predefined. Optional aliases: [`~hosts/_hosts.yaml`](./~hosts/_hosts.yaml).
