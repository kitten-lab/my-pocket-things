---
crate: crate.5BF1F67F7659ED21
title: token system
---

# {{title}}
Inside the #bios, shell and pages are editable in a tokenized markdown format. The mypi:bios uses standard markdown formatting, plus the addition of exclusive tokens which help format your pages and extend their functionality with unique tools.

Tokens are formatted `{{like this}}`. They work in any .md under a go. host and on start. The token can be used to create spans or divs around you content, or call special inserts and tools to define *what* is listed.

## Files and directories
### most common displays
- `files` - notes in this folder (not subfolders)
- `doors` - subfolders as door cards
- `list` - notes and subfolders together (alias `dir`)
### trees and navigations
- `tree` - file tree from the dress shell; folders open and close
- `navbar` - child folders as a simple link strip (alias `nav`)

More list layouts (spines, dirtree, door chips, roam doors, and others) live in [[token-repo]].

## Dress
- `paper` - hole in a `_shell.md` filled by `index.md` or the open note
- `span` - wrap inline text
- `div` - wrap a block of content

## Pictures
- `img` - one image by filename
- `images` - slideshow of images in this folder

## Links
- `link` - title link to a note by crate
- `[[Note]]` - wiki link inside this host
- `outlink` - open an http(s) URL outside the pocket

## Token repo
The full token list, aliases, and how each token works: [[token-repo]].
