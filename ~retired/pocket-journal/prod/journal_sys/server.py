#!/usr/bin/env python3
"""My Pocket Journal · CO.MYPT-003-JOURNAL · .bok books on disk"""

from __future__ import annotations

import json
import re
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent  # journal_sys (code)
PROD = ROOT.parent
SAFE = PROD / "safe_box"
BOOKS = SAFE / "books"
SHELF = SAFE / "shelf.json"  # lastOpened only — not page bodies
HOST = "127.0.0.1"
PORT = int(__import__("os").environ.get("JOURNAL_PORT", "43166"))
SKU = "CO.MYPT-003-JOURNAL"


def now() -> int:
    return int(time.time())


def load_shelf() -> dict[str, Any]:
    if not SHELF.is_file():
        return {"schema": "mypt-journal-shelf.v1", "sku": SKU, "lastOpened": []}
    try:
        return json.loads(SHELF.read_text(encoding="utf-8"))
    except Exception:
        return {"schema": "mypt-journal-shelf.v1", "sku": SKU, "lastOpened": []}


def save_shelf(doc: dict[str, Any]) -> None:
    doc = dict(doc)
    doc["schema"] = "mypt-journal-shelf.v1"
    doc["sku"] = SKU
    SHELF.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def slugify(title: str, fallback: str = "book") -> str:
    s = re.sub(r"[^\w\s-]", "", (title or "").strip(), flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s).strip("-").lower()
    return (s[:48] if s else fallback) or fallback


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    raw = text.replace("\r\n", "\n")
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return {}, raw
    block = raw[4:end]
    body = raw[end + 5 :]
    meta: dict[str, Any] = {}
    for line in block.split("\n"):
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        if k in ("created", "updated", "position") and v.isdigit():
            meta[k] = int(v)
        else:
            meta[k] = v
    return meta, body


def dump_frontmatter(meta: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for k in ("id", "title", "whisper", "cloth", "created", "updated", "position", "mark"):
        if k not in meta or meta[k] is None or meta[k] == "":
            if k == "mark":
                continue
            if k not in meta:
                continue
        val = meta[k]
        if isinstance(val, str) and (":" in val or val.startswith(" ") or "\n" in val):
            val = json.dumps(val, ensure_ascii=False)
        lines.append(f"{k}: {val}")
    lines.append("---")
    body = body if body is not None else ""
    if body and not body.startswith("\n"):
        return "\n".join(lines) + "\n" + body.lstrip("\n")
    return "\n".join(lines) + "\n" + body


def bok_dir_for_id(book_id: str) -> Path | None:
    if not BOOKS.is_dir():
        return None
    for p in BOOKS.iterdir():
        if not p.is_dir() or not p.name.endswith(".bok"):
            continue
        book_md = p / "book.md"
        if not book_md.is_file():
            continue
        meta, _ = parse_frontmatter(book_md.read_text(encoding="utf-8"))
        if meta.get("id") == book_id:
            return p
    return None


def page_filename(position: int, page_id: str, title: str) -> str:
    slug = slugify(title or page_id, page_id[-8:] if page_id else "page")
    return f"{int(position):03d}-{slug}.md"


def read_book(bok: Path) -> dict[str, Any] | None:
    book_md = bok / "book.md"
    if not book_md.is_file():
        return None
    meta, _ = parse_frontmatter(book_md.read_text(encoding="utf-8"))
    pages_dir = bok / "pages"
    pages: list[dict[str, Any]] = []
    if pages_dir.is_dir():
        for pf in sorted(pages_dir.glob("*.md")):
            pm, body = parse_frontmatter(pf.read_text(encoding="utf-8"))
            pages.append(
                {
                    "id": pm.get("id") or pf.stem,
                    "position": int(pm.get("position") or 0),
                    "title": pm.get("title") or "",
                    "body": body,
                    "mark": pm.get("mark") or "",
                    "updated": int(pm.get("updated") or 0),
                    "_file": pf.name,
                }
            )
    pages.sort(key=lambda p: (p.get("position") or 0, p.get("id") or ""))
    for i, p in enumerate(pages):
        if not p.get("position"):
            p["position"] = i + 1
    return {
        "id": meta.get("id") or bok.stem.replace(".bok", ""),
        "title": meta.get("title") or bok.stem.replace(".bok", ""),
        "whisper": meta.get("whisper") or "",
        "cloth": meta.get("cloth") or "oxblood",
        "created": int(meta.get("created") or 0),
        "updated": int(meta.get("updated") or 0),
        "pages": [{k: v for k, v in p.items() if k != "_file"} for p in pages],
        "_path": str(bok),
    }


def write_book(nb: dict[str, Any], prefer_dir: Path | None = None) -> Path:
    """Write notebook dict to a .bok package. Returns path."""
    BOOKS.mkdir(parents=True, exist_ok=True)
    book_id = nb.get("id") or f"nb-{now()}"
    nb["id"] = book_id
    existing = prefer_dir or bok_dir_for_id(book_id)
    if existing is None:
        base = slugify(nb.get("title") or book_id, book_id)
        candidate = BOOKS / f"{base}.bok"
        n = 2
        while candidate.exists() and bok_dir_for_id(book_id) is None:
            # if folder exists for another book, pick new name
            other = read_book(candidate)
            if other and other.get("id") == book_id:
                break
            if other is None:
                break
            candidate = BOOKS / f"{base}-{n}.bok"
            n += 1
        existing = candidate
    existing.mkdir(parents=True, exist_ok=True)
    pages_dir = existing / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    # wipe old page files then rewrite (simple, safe for small journals)
    for old in pages_dir.glob("*.md"):
        old.unlink()

    pages = list(nb.get("pages") or [])
    pages.sort(key=lambda p: (p.get("position") or 0, p.get("id") or ""))
    for i, pg in enumerate(pages):
        pos = int(pg.get("position") or (i + 1))
        pg["position"] = pos
        pid = pg.get("id") or f"pg-{i+1}"
        pg["id"] = pid
        fname = page_filename(pos, pid, pg.get("title") or "")
        meta = {
            "id": pid,
            "position": pos,
            "title": pg.get("title") or "",
            "mark": pg.get("mark") or "",
            "updated": int(pg.get("updated") or now()),
        }
        (pages_dir / fname).write_text(
            dump_frontmatter(meta, pg.get("body") or ""), encoding="utf-8"
        )

    book_meta = {
        "id": book_id,
        "title": nb.get("title") or "untitled",
        "whisper": nb.get("whisper") or "",
        "cloth": nb.get("cloth") or "oxblood",
        "created": int(nb.get("created") or now()),
        "updated": int(nb.get("updated") or now()),
    }
    (existing / "book.md").write_text(
        dump_frontmatter(book_meta, ""), encoding="utf-8"
    )
    return existing


def list_books() -> list[dict[str, Any]]:
    BOOKS.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, Any]] = []
    for p in sorted(BOOKS.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and p.name.endswith(".bok"):
            nb = read_book(p)
            if nb:
                out.append(nb)
    return out


def library_payload() -> dict[str, Any]:
    shelf = load_shelf()
    books = list_books()
    # strip internal path for client
    clean = []
    for b in books:
        c = {k: v for k, v in b.items() if not k.startswith("_")}
        clean.append(c)
    return {
        "schema": "mypt-journal.v1",
        "sku": SKU,
        "notebooks": clean,
        "lastOpened": shelf.get("lastOpened") or [],
        "books_dir": str(BOOKS),
    }


def persist_library(doc: dict[str, Any]) -> dict[str, Any]:
    notebooks = doc.get("notebooks")
    if not isinstance(notebooks, list):
        notebooks = []
    # map existing dirs by id
    known = {b["id"]: Path(b["_path"]) for b in list_books() if b.get("id")}
    seen_ids: set[str] = set()
    for nb in notebooks:
        if not isinstance(nb, dict):
            continue
        bid = nb.get("id")
        if not bid:
            continue
        seen_ids.add(bid)
        write_book(nb, prefer_dir=known.get(bid))
    # remove books deleted from library
    for bid, path in known.items():
        if bid not in seen_ids and path.is_dir():
            # only delete .bok packages we own
            if path.parent.resolve() == BOOKS.resolve() and path.name.endswith(".bok"):
                for child in path.rglob("*"):
                    if child.is_file():
                        child.unlink()
                for child in sorted(path.rglob("*"), reverse=True):
                    if child.is_dir():
                        child.rmdir()
                path.rmdir()
    shelf = load_shelf()
    if isinstance(doc.get("lastOpened"), list):
        shelf["lastOpened"] = doc["lastOpened"][:8]
    save_shelf(shelf)
    return library_payload()


def ensure_seed() -> None:
    BOOKS.mkdir(parents=True, exist_ok=True)
    if any(BOOKS.glob("*.bok")):
        return
    t = now()
    write_book(
        {
            "id": "nb-project-map",
            "title": "Project Map",
            "whisper": "what we made · why · bag pulls",
            "cloth": "forest",
            "created": t,
            "updated": t,
            "pages": [
                {
                    "id": "pg-rom-launcher",
                    "position": 1,
                    "title": "ROM Launcher",
                    "mark": "brass",
                    "updated": t,
                    "body": (
                        "**Name on the shelf**: the-deck-host/rom-launcher\n"
                        "**Port it claims**: 43170\n\n"
                        "What the box says it is (one breath, not truth): the start menu — "
                        "little cases on a desk that quietly boot the other toys.\n\n"
                        "# Why Does This Exist?\n"
                        "My Pocket Internet had died, and with it, the concept of containing "
                        "small toys and tools inside of launchable/clickable \"ROM Cases\" in any "
                        "\"ROOM\" in the pocket internet. Conceptually, the ROM LAUNCHER exists as "
                        "a means to quietly launch small web-tech and/or python application, "
                        "running independently of any browser chrome.\n\n"
                        "The ROM LAUNCHER purpose is to allow me to explore the toys I have made "
                        "in ALICE_BOX which are the figment ideas of the pocket internet ROMs for "
                        "ROOMs. It is helpful, since you can place \"launch icons\" onto a rail and "
                        "easily manage your ROM applications in one tool bar.\n\n"
                        "It is directly connected in the backend to the ROM CAT.\n"
                        "~Sadly, at the time of this note, the ROM LAUNCHER does not display "
                        "itself inside of itself.~\n"
                    ),
                },
                {
                    "id": "pg-notes-chords",
                    "position": 2,
                    "title": "Notes & Chords",
                    "mark": "hot",
                    "updated": t,
                    "body": (
                        "**Name on the shelf**: charlies-toys/kde-notes-chords\n"
                        "**Label on the box**: CO.KDE-001-INSTR · “Notes & Chords”\n\n"
                        "# What is this?\n"
                        "This toy started as the first exploration taken into JS code. Adverse "
                        "before, didn't like the markup. Self is a 24-year veteran of iGaming "
                        "industry, having worked at the same producer for that entire duration. "
                        "The intent was to spell break the concept of the infinite loop:\n\n"
                        "Self desires pattern seeking (look for signs of fruit)\n"
                        "Self expects something from finding pattern (fruit taste good!)\n"
                        "Self not actually satiated, so self keep going.\n\n"
                        "Most times, fruit isn't even real.\n"
                        "Pay to Play took everything that was slot manipulation methods and "
                        "gamified them more. Now, no even real fruit. Pixels on the screen. "
                        "Sense of collection.\n\n"
                        "Self want collection.\n"
                        "Self want show off collection.\n\n"
                        "So, produce slot machine concept. What if not pays money, pays in story? "
                        "But random. How do you handle? Same story pieces, different landing "
                        "results. So each spin becomes a chance at the next piece of the story, "
                        "and even when the story does not change, the way it prints does. Like "
                        "the concept that the emphasis changes the whole meaning in the sentence:\n\n"
                        "`I didn't say he stole my money.'\n\n"
                        "Each change shifts the meaning dramatically.\n"
                        "So, each time you randomly roll the keyboard, you get a chance to "
                        "understand something more. The weight changes, so the meaning may shift. "
                        "Can you make meaning from the same stories if the weight changes in the "
                        "narrative?\n\n"
                        "Bonus: just add tone.js cause it looks like a piano.\n"
                    ),
                },
            ],
        }
    )
    write_book(
        {
            "id": "nb-blank-field",
            "title": "Field Journal",
            "whisper": "empty pocket · for new pulls",
            "cloth": "sand",
            "created": t,
            "updated": t,
            "pages": [
                {
                    "id": "pg-hello",
                    "position": 1,
                    "title": "hello",
                    "body": "Blank page for the next bag pull.\n\nWrite here. Agents read the same `.md` file.\n",
                    "mark": "",
                    "updated": t,
                }
            ],
        }
    )
    save_shelf({"lastOpened": ["nb-project-map"]})


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, obj: Any) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(
                200,
                {
                    "ok": True,
                    "sku": SKU,
                    "service": "pocket-journal",
                    "port": PORT,
                    "books": str(BOOKS),
                },
            )
            return
        if path == "/api/library":
            self._json(200, {"ok": True, "library": library_payload()})
            return
        if path.startswith("/api/book/") and path.count("/") == 3:
            bid = unquote(path.split("/")[-1])
            for b in list_books():
                if b.get("id") == bid:
                    clean = {k: v for k, v in b.items() if not k.startswith("_")}
                    self._json(200, {"ok": True, "book": clean})
                    return
            self._json(404, {"ok": False, "error": "book not found"})
            return
        return super().do_GET()

    def do_PUT(self) -> None:
        if urlparse(self.path).path == "/api/library":
            body = self._read_json()
            doc = body.get("library") if isinstance(body.get("library"), dict) else body
            if not isinstance(doc, dict):
                self._json(400, {"ok": False, "error": "object required"})
                return
            lib = persist_library(doc)
            self._json(200, {"ok": True, "library": lib})
            return
        self._json(404, {"ok": False, "error": "not found"})


def main() -> None:
    ensure_seed()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"My Pocket Journal  http://{HOST}:{PORT}/")
    print(f"SKU {SKU} · books {BOOKS}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nclosed the journal")


if __name__ == "__main__":
    main()
