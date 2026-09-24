---
title: Roam libraries
deck: connect an exterior markdown folder as roam.*
---

# Roam libraries

A pocket app can keep a markdown library anywhere. Pocket Go **connects** it as a full host under `roam.{slug}`. Native rooms stay `go.*`. Cabinets already follow the slug; they do not need a new mouth.

## Connect

BIOS Hosts -> **+ roam**. Name, source folder, optional title and coat. Keep writes the yaml. **Disconnect** drops the yaml line; the folder on disk stays.

You can also edit `~hosts/_hosts.yaml` yourself:

```
drop:
  kind: roam
  source: C:\Users\theda\Desktop\roam-drop
  title: roam drop

files:
  kind: roam
  source: C:\ALICE_BOX\charlies-toys\sdk-import-station\library
  title: FILES library

sophia:
  kind: roam
  source: C:\ALICE_BOX\le-awn-industries\el-desks-for-her\sophia-desk\~local\ADM\library
  title: Sophia library
```

- `kind: roam` makes the address `roam.drop/` (not `go.drop/`).
- `source:` is the folder. **The yaml line is the allowlist.** Desktop is legal. Nothing in the address bar can set a source.
- If the folder is missing, Go creates it.
- `environment:` is optional. If the folder has no `_shell.md`, that coat (or stock Go hall dress) wraps the listing. Go does not write a shell into the folder unless you make one.
- `go.terminals` and other `~hosts` folders stay as they are.

Type `roam.drop/` or `drop` on the jump bar. Type `Roam` for the roam lobby; Go lists native hosts only.

## Paper in the folder

Same paper as a go.* host:

- UTF-8 `.md`, ASCII `---` fences, flat YAML (`crate:`, `title:`, optional `environment:`, `edges:`).
- `_shell.md` is the dress (`{{paper}}` hole). `index.md` is the blotter.
- README New / Keep writes **into `source:`**, not into `~hosts`.
- Cabinets (Librarian, Detective, Charlie, TPS) still live under `~librarian/{slug}/` and friends. Lore cards stay in `go.trays`.

## Guest chips

`.chip` files from Sophia or FILES are guest paper. Go may **look**, **crate**, and **cabinet-mark**. The producer keeps the pen.

- List and open like a note. Title from nested `chip.name`. Body is the text after the first `---` / `---` fence. The page wears `is-chip-guest`.
- Crate source of truth is `~librarian/{host}/_chip_crates.yaml`, keyed by `chip.uid` (`leaf[6]`, `card[7]`). Filename slug may change; uid does not.
- If the chip has no top-level `crate:`, Go writes a courtesy sticker. If the producer rebuilds the header and drops it, Go restamps the same sidecar crate. It does not mint again.
- BIOS Keep / Rename / page face stay off the chip. The hall `_shell.md` is still editable.
- Cabinets write beside the file as `leaf[6]-foo.chip.yaml`, same pattern as `.canvas`.
- No `.md` duplicates. Station `paper/*.chip` is not connected unless you add another roam.

Proof: type `sophia` or `Roam`, open `leaf[6]-rosewoodpapers.chip`. Body shows. Sidecar gets `leaf[6]: crate.HEX`. Reload that leaf in Sophia and open it again in Go: same crate. BIOS Keep on that paper fails. BIOS Keep on the roam shell still works.

## Live: a ROM library

Import-station FILES lives at `sdk-import-station/library/` and is connected as `roam.files`. Halls match stations (io, ab, cu, dr, osx, dc) and start empty. Chip paper under `paper/{station}` and the `go.terminals` dump stay where they are. Mail and glass stay toy rooms. Do not dump life files into `go.terminals/IO/EXPORTS`.

Reuse this page each time you adapt another app: same format, one `_hosts.yaml` block, cabinets come free.
