#!/usr/bin/env python3
"""My Pocket Go — early internet in WWW chrome. Edit in Obsidian, refresh here."""

from __future__ import annotations

import html
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

SYS = Path(__file__).resolve().parent
ROOT = SYS.parents[1]  # pocket-go/
STYLES = SYS / "styles"
BEEN_FILE = ROOT / "prod" / "been.json"
BEEN_LOCK = threading.Lock()
HOST = "127.0.0.1"
PORT = int(os.environ.get("GO_PORT", os.environ.get("LIBRARY_PORT", "43210")))
SKU = "CO.MYPT-004-GO"
GO_HOST = "library"
SKIP = {".obsidian", ".agents", ".claude", ".opencode", ".git", "~reader"}
ENV_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
WIKI_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<![&/\w])#([A-Za-z][\w/-]*)")
HEADING_RE = re.compile(r"^(#{1,5})\s+(.*)$")
DRESS_LEAD = re.compile(
    r"^(?:\{\{\.([A-Za-z][\w.-]*?)(?:#([A-Za-z][\w-]*))?\}\}|\{\{#([A-Za-z][\w-]*)\}\})\s*"
)
SPAN_RE = re.compile(
    r"\{\{span:(\.[A-Za-z][\w.-]*(?:#[A-Za-z][\w-]*)?|#[A-Za-z][\w-]*|[A-Za-z][\w.-]*)\}\}(.*?)\{\{/span\}\}"
)
DIV_OPEN = re.compile(
    r"^\{\{(?:div|block):(\.[A-Za-z][\w.-]*(?:#[A-Za-z][\w-]*)?|#[A-Za-z][\w-]*|[A-Za-z][\w.-]*)\}\}\s*$"
)
DIV_CLOSE = re.compile(r"^\{\{/(?:div|block)\}\}\s*$")
IMG_EMBED_RE = re.compile(r"!\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]")
IMG_TOKEN_RE = re.compile(r"\{\{img:([^}|]+)(?:\|([^}]*))?\}\}")
IMG_MD_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
IMAGE_EXT = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".bmp", ".ico"}
IMAGE_TYPE = {
    ".gif": "image/gif",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".bmp": "image/bmp",
    ".ico": "image/x-icon",
}

_vault_env = os.environ.get("BONEYARD_VAULT", "").strip()
VAULT = Path(_vault_env).resolve() if _vault_env else (ROOT / "~library")

COLORS = {
    "yellow": "#c9a227",
    "orange": "#c45c26",
    "red": "#a33b3b",
    "green": "#2d6a4f",
    "purple": "#6b3fa0",
    "blue": "#2c5aa0",
    "amber": "#c9892d",
}

STATIC = {
    "/www.css": ("text/css; charset=utf-8", SYS / "www.css"),
    "/www.js": ("text/javascript; charset=utf-8", SYS / "www.js"),
    "/dress.css": ("text/css; charset=utf-8", SYS / "dress.css"),
    "/index.css": ("text/css; charset=utf-8", SYS / "index.css"),
}
INDEX_NAME = "_index.md"
BEEN_MAX = 2000


def been_clean(raw) -> list[str]:
    if isinstance(raw, dict):
        raw = raw.get("been", [])
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for x in raw:
        if not isinstance(x, str) or not x.startswith("/") or len(x) > 500:
            continue
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out[-BEEN_MAX:]


def been_load() -> list[str]:
    with BEEN_LOCK:
        if not BEEN_FILE.is_file():
            return []
        try:
            return been_clean(json.loads(BEEN_FILE.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            return []


def been_save(keys: list[str]) -> list[str]:
    clean = been_clean(keys)
    with BEEN_LOCK:
        BEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        BEEN_FILE.write_text(json.dumps({"been": clean}, indent=0) + "\n", encoding="utf-8")
    return clean


def safe_rel(rel: str) -> Path | None:
    rel = rel.replace("\\", "/").strip("/")
    if not rel or ".." in Path(rel).parts:
        return None
    target = (VAULT / rel).resolve()
    try:
        target.relative_to(VAULT.resolve())
    except ValueError:
        return None
    if any(part in SKIP for part in target.relative_to(VAULT).parts):
        return None
    return target


def find_media(name: str) -> Path | None:
    raw = name.strip().replace("\\", "/").strip("/")
    if not raw or "://" in raw:
        return None
    if "/" in raw:
        target = safe_rel(raw)
        if target is not None and target.is_file() and target.suffix.lower() in IMAGE_EXT:
            return target
    needle = Path(raw).name.lower()
    hits: list[Path] = []
    if VAULT.is_dir():
        for p in VAULT.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:
                continue
            if p.name.lower() != needle:
                continue
            if any(part in SKIP for part in p.relative_to(VAULT).parts):
                continue
            hits.append(p)
    if not hits:
        return None
    hits.sort(key=lambda x: x.as_posix().lower())
    return hits[0]


def img_tag(name: str, alt: str = "") -> str:
    p = find_media(name)
    if p is None:
        label = html.escape(name.strip() or "picture")
        return f'<span class="pic-miss">[no picture: {label}]</span>'
    rel = p.relative_to(VAULT).as_posix()
    src = "/i/" + quote(rel, safe="/")
    label = (alt or "").strip() or p.name
    return (
        f'<img class="pic" src="{html.escape(src, True)}" '
        f'alt="{html.escape(label, True)}">'
    )


def pocket_bar(rel: str, is_dir: bool = False) -> str:
    host = "go." + GO_HOST
    if not rel:
        return host + "/"
    p = rel.replace("\\", "/").strip("/")
    bar = host + "/" + p
    if is_dir:
        bar += "/"
    return bar


def parse_fm(text: str) -> tuple[dict, str]:
    raw = text.replace("\r\n", "\n")
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return {}, raw
    meta: dict = {}
    for line in raw[4:end].split("\n"):
        if ":" not in line or line.startswith(" "):
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, raw[end + 5 :]


def accent_for(rel: str, meta: dict) -> str:
    blob = (rel + " " + str(meta.get("color", ""))).lower()
    for name, hexv in COLORS.items():
        if name in blob:
            return hexv
    return "#6e6254"


def env_name(raw: str | None) -> str | None:
    if not raw:
        return None
    name = str(raw).strip()
    if name.startswith("[[") and name.endswith("]]"):
        name = name[2:-2].strip()
        if "|" in name:
            name = name.split("|", 1)[0].strip()
    if name.lower().endswith(".css"):
        name = name[:-4]
    if not ENV_NAME.fullmatch(name):
        return None
    return name


def parse_spec(spec: str) -> tuple[str, str]:
    spec = spec.strip()
    cls, eid = "", ""
    if spec.startswith("#"):
        eid = spec[1:]
    else:
        if spec.startswith("."):
            spec = spec[1:]
        if "#" in spec:
            spec, eid = spec.split("#", 1)
        cls = " ".join(p for p in spec.split(".") if p)
    cls = " ".join(c for c in cls.split() if ENV_NAME.fullmatch(c))
    if eid and not ENV_NAME.fullmatch(eid):
        eid = ""
    return cls, eid


def html_attrs(cls: str, eid: str) -> str:
    bits = []
    if cls:
        bits.append(f'class="{html.escape(cls, True)}"')
    if eid:
        bits.append(f'id="{html.escape(eid, True)}"')
    return (" " + " ".join(bits)) if bits else ""


def take_dress(s: str) -> tuple[str, str, str]:
    classes: list[str] = []
    eid = ""
    while True:
        m = DRESS_LEAD.match(s)
        if not m:
            break
        if m.group(1):
            classes.extend(p for p in m.group(1).split(".") if ENV_NAME.fullmatch(p))
            if m.group(2) and ENV_NAME.fullmatch(m.group(2)):
                eid = m.group(2)
        elif m.group(3) and ENV_NAME.fullmatch(m.group(3)):
            eid = m.group(3)
        s = s[m.end() :]
    return s, " ".join(classes), eid


def md_lite(src: str) -> str:
    lines = src.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    buf: list[str] = []
    open_divs = 0

    fence: list[str] | None = None

    def flush() -> None:
        if not buf:
            return
        para, cls, eid = take_dress(" ".join(buf))
        out.append(f"<p{html_attrs(cls, eid)}>" + inline(para) + "</p>")
        buf.clear()

    def flush_fence() -> None:
        nonlocal fence
        if fence is None:
            return
        body = html.escape("\n".join(fence))
        out.append(f"<pre class='code'><code>{body}</code></pre>")
        fence = None

    def inline(s: str) -> str:
        held: list[str] = []

        def hold(bit: str) -> str:
            held.append(bit)
            return f"\x00@{len(held) - 1}@\x00"

        s = re.sub(
            r"`([^`]+)`",
            lambda m: hold("<code>" + html.escape(m.group(1)) + "</code>"),
            s,
        )
        s = IMG_EMBED_RE.sub(
            lambda m: hold(img_tag(m.group(1), m.group(2) or "")),
            s,
        )
        s = IMG_TOKEN_RE.sub(
            lambda m: hold(img_tag(m.group(1), m.group(2) or "")),
            s,
        )
        s = IMG_MD_RE.sub(
            lambda m: hold(img_tag(m.group(2), m.group(1) or "")),
            s,
        )
        s = re.sub(
            r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
            lambda m: hold(
                f'<a class="wiki" href="/?q={html.escape(m.group(1), True)}">'
                f"{html.escape(m.group(2) or m.group(1))}</a>"
            ),
            s,
        )
        s = TAG_RE.sub(lambda m: hold(tag_chip(m.group(1))), s)
        s = SPAN_RE.sub(
            lambda m: hold(f"<span{html_attrs(*parse_spec(m.group(1)))}>")
            + m.group(2)
            + hold("</span>"),
            s,
        )
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        return re.sub(r"\x00@(\d+)@\x00", lambda m: held[int(m.group(1))], s)

    for line in lines:
        if fence is not None:
            if line.strip().startswith("```"):
                flush_fence()
            else:
                fence.append(line)
            continue
        if line.strip().startswith("```"):
            flush()
            fence = []
            continue
        raw = line.strip()
        opened = DIV_OPEN.match(raw)
        if opened:
            flush()
            out.append(f"<div{html_attrs(*parse_spec(opened.group(1)))}>")
            open_divs += 1
            continue
        if DIV_CLOSE.match(raw):
            flush()
            if open_divs:
                out.append("</div>")
                open_divs -= 1
            continue
        hm = HEADING_RE.match(line)
        if hm:
            flush()
            n = min(max(len(hm.group(1)), 1), 5)
            text, cls, eid = take_dress(hm.group(2).strip())
            out.append(f"<h{n}{html_attrs(cls, eid)}>" + inline(text) + f"</h{n}>")
        elif line.strip() == "---":
            flush()
            out.append("<hr>")
        elif line.startswith("|"):
            flush()
            out.append("<pre class='tbl'>" + html.escape(line) + "</pre>")
        elif re.match(r"^[-*]\s+", line):
            flush()
            text, cls, eid = take_dress(re.sub(r"^[-*]\s+", "", line))
            out.append(f"<li{html_attrs(cls, eid)}>" + inline(text) + "</li>")
        elif not line.strip():
            flush()
        else:
            buf.append(line)
    flush()
    flush_fence()
    while open_divs:
        out.append("</div>")
        open_divs -= 1
    return "\n".join(out)


def iter_notes() -> list[Path]:
    if not VAULT.is_dir():
        return []
    out: list[Path] = []
    for p in VAULT.rglob("*.md"):
        if any(part in SKIP for part in p.relative_to(VAULT).parts):
            continue
        if p.name.lower() == INDEX_NAME:
            continue
        out.append(p)
    return out


def split_tags(raw: str) -> list[str]:
    s = str(raw).strip().strip("[]")
    tags = []
    for part in re.split(r",\s*", s):
        part = part.strip().strip("#").strip()
        if part:
            tags.append(part)
    return tags


def tag_chip(name: str) -> str:
    slug = name.strip().lstrip("#")
    return (
        f'<a class="tag" href="/?t={html.escape(slug, True)}">'
        f"#{html.escape(slug)}</a>"
    )


def wiki_target(raw: str) -> str:
    t = raw.strip().replace("\\", "/")
    return t.split("/")[-1].strip().lower()


def hit_list(paths: list[Path]) -> str:
    if not paths:
        return "<p>none.</p>"
    items = []
    for p in sorted(paths, key=lambda x: x.as_posix().lower()):
        rel = p.relative_to(VAULT).as_posix()
        items.append(
            f'<li><a href="/?p={html.escape(rel, True)}">{html.escape(p.stem)}</a>'
            f'<span class="hit-path">{html.escape(rel)}</span></li>'
        )
    return "<ul class='dir hits'>" + "".join(items) + "</ul>"


def lookup_wiki(title: str) -> tuple[list[Path], list[Path], list[Path]]:
    raw = title.strip().replace("\\", "/")
    needle = wiki_target(raw)
    want_path = raw.lower()[:-3] if raw.lower().endswith(".md") else raw.lower()
    want_path = want_path if "/" in raw else ""
    exact: list[Path] = []
    nearby: list[Path] = []
    linked: list[Path] = []
    path_hits: list[Path] = []
    for p in iter_notes():
        rel = p.relative_to(VAULT).as_posix()[:-3].lower()
        stem = p.stem.lower()
        if want_path and rel == want_path:
            path_hits.append(p)
        if stem == needle:
            exact.append(p)
        elif needle and stem.startswith(needle):
            nearby.append(p)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in WIKI_RE.finditer(text):
            if wiki_target(m.group(1)) == needle:
                linked.append(p)
                break
    if len(path_hits) == 1:
        exact = path_hits
    exact_ids = {id(p) for p in exact}
    linked = [p for p in linked if id(p) not in exact_ids]
    nearby = [p for p in nearby if id(p) not in exact_ids]
    return exact, nearby, linked


def wiki_page(query: str, exact: list[Path], nearby: list[Path], linked: list[Path]) -> bytes:
    q = html.escape(query)
    bits = [f"<h1>[[{q}]]</h1>"]
    if exact:
        bits.append("<h2>this name</h2>" + hit_list(exact))
    if nearby:
        bits.append("<h2>nearby names</h2>" + hit_list(nearby))
    if linked:
        bits.append("<h2>linked from</h2>" + hit_list(linked))
    if not exact and not nearby and not linked:
        bits.append("<p>no file by that name, and nobody wikilinked it.</p>")
    return page(f"[[{query}]]", "\n".join(bits), "#6e6254", "query", pocket_bar(""))


def notes_with_tag(slug: str) -> list[Path]:
    needle = slug.strip().lstrip("#").lower()
    hits: list[Path] = []
    for p in iter_notes():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = parse_fm(text)
        tags = {t.lower() for k, v in meta.items() if k.lower() in ("tags", "tag") for t in split_tags(str(v))}
        tags.update(m.group(1).lower() for m in TAG_RE.finditer(body))
        if needle in tags:
            hits.append(p)
    return hits


def tag_page(slug: str) -> bytes:
    slug = slug.strip().lstrip("#")
    hits = notes_with_tag(slug)
    body = f"<h1>{tag_chip(slug)}</h1>" + hit_list(hits)
    return page(f"#{slug}", body, "#6e6254", "tag", pocket_bar(""))


def fm_inline(s: str) -> str:
    held: list[str] = []

    def hold(bit: str) -> str:
        held.append(bit)
        return f"\x00@{len(held) - 1}@\x00"

    s = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda m: hold(
            f'<a class="wiki" href="/?q={html.escape(m.group(1), True)}">'
            f"{html.escape(m.group(2) or m.group(1))}</a>"
        ),
        s,
    )
    s = TAG_RE.sub(lambda m: hold(tag_chip(m.group(1))), s)
    s = html.escape(s)
    return re.sub(r"\x00@(\d+)@\x00", lambda m: held[int(m.group(1))], s)


def fm_row(k: str, v: str) -> str:
    if k.lower() in ("tags", "tag"):
        chips = "".join(tag_chip(t) for t in split_tags(str(v)))
        dd = chips or html.escape(str(v))
    else:
        dd = fm_inline(str(v))
    return f"<div><dt>{html.escape(k)}</dt><dd>{dd}</dd></div>"


def headers_block(meta: dict) -> str:
    if not meta:
        return ""
    rows = "".join(fm_row(k, str(v)) for k, v in meta.items())
    return (
        "<details class='headers'>"
        "<summary>headers</summary>"
        f"<dl class='fm'>{rows}</dl>"
        "</details>"
    )


def is_vault_root(folder: Path) -> bool:
    try:
        return folder.resolve() == VAULT.resolve()
    except OSError:
        return False


def load_index(folder: Path) -> tuple[dict, str] | None:
    p = folder / INDEX_NAME
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    return parse_fm(text)


def visible_kids(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    kids = []
    for p in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if p.name in SKIP or p.name.startswith(".") or p.name.startswith("_"):
            continue
        if p.is_dir() or p.suffix.lower() == ".md":
            kids.append(p)
    return kids


def door_cards(folder: Path) -> str:
    cards = []
    for w in visible_kids(folder):
        if not w.is_dir():
            continue
        n = sum(1 for _ in w.rglob("*.md") if "~reader" not in _.parts and _.name.lower() != INDEX_NAME)
        accent = accent_for(w.name, {})
        r = w.relative_to(VAULT).as_posix()
        cards.append(
            f'<a class="world" href="/?p={html.escape(r, True)}" style="--accent:{accent}">'
            f"<strong>{html.escape(w.name)}</strong><span>{n} notes</span></a>"
        )
    if not cards:
        return "<p>no folders here.</p>"
    return "<div class='worlds'>" + "".join(cards) + "</div>"


def file_list(folder: Path, kind: str = "files") -> str:
    items = []
    for p in visible_kids(folder):
        if kind == "files" and p.is_dir():
            continue
        if kind == "dirs" and not p.is_dir():
            continue
        r = p.relative_to(VAULT).as_posix()
        mark = "/" if p.is_dir() else ""
        items.append(
            f'<li><a href="/?p={html.escape(r, True)}">{html.escape(p.name)}{mark}</a></li>'
        )
    if not items:
        if kind == "files":
            return "<p>no notes here.</p>"
        if kind == "dirs":
            return "<p>no folders here.</p>"
        return "<p>empty.</p>"
    return "<ul class='dir'>" + "".join(items) + "</ul>"


def fill_slots(body: str, folder: Path) -> str:
    doors = door_cards(folder)
    notes = file_list(folder, "files")
    listing = file_list(folder, "all")
    rel = "" if is_vault_root(folder) else folder.relative_to(VAULT).as_posix()
    had = False
    if "{{doors}}" in body or "{{worlds}}" in body:
        body = body.replace("{{doors}}", doors).replace("{{worlds}}", doors)
        had = True
    if "{{files}}" in body:
        body = body.replace("{{files}}", notes)
        had = True
    if "{{dir}}" in body or "{{list}}" in body:
        body = body.replace("{{dir}}", listing).replace("{{list}}", listing)
        had = True
    body = place_crumb(body, rel)
    if not had:
        body = body + "\n" + (doors if is_vault_root(folder) else listing)
    return body


def uses_of(name: str, current: Path | None = None) -> tuple[list[Path], list[Path]]:
    exact, _nearby, linked = lookup_wiki(name)
    here = None
    if current is not None:
        try:
            here = current.resolve()
        except OSError:
            here = current
    if here is not None:
        exact = [p for p in exact if p.resolve() != here]
        linked = [p for p in linked if p.resolve() != here]
    return exact, linked


def uses_block(name: str, current: Path | None = None, empty: bool = False) -> str:
    others, linked = uses_of(name, current)
    bits = []
    if others:
        bits.append("<h2>also this name</h2>" + hit_list(others))
    if linked:
        bits.append(
            f"<h2>uses of [[{html.escape(name)}]]</h2>" + hit_list(linked)
        )
    if not bits:
        if not empty:
            return ""
        bits.append("<p>no other bags of this word yet.</p>")
    return "<section class='uses'>" + "".join(bits) + "</section>"


def fill_uses(body: str, name: str, current: Path) -> str:
    has_slot = "{{uses}}" in body or "{{bags}}" in body
    block = uses_block(name, current, empty=has_slot)
    if has_slot:
        body = body.replace("{{uses}}", block).replace("{{bags}}", block)
    elif block:
        body = body + "\n" + block
    rel = current.relative_to(VAULT).as_posix()
    return place_crumb(body, rel)


def folder_crumbs(rel: str) -> str:
    home = '<a href="/">~/</a>'
    if not rel:
        return home
    rest = " / ".join(
        f'<a href="/?p={html.escape("/".join(Path(rel).parts[: i + 1]), True)}">{html.escape(part)}</a>'
        for i, part in enumerate(Path(rel).parts)
    )
    return home + " / " + rest


def crumb_back(rel: str) -> str:
    parts = Path(rel.replace("\\", "/")).parts if rel else ()
    if not parts:
        return ""
    parent = parts[:-1]
    if not parent:
        link = '<a class="crumbback" href="/">../</a>'
    else:
        dest = "/".join(parent)
        link = (
            f'<a class="crumbback" href="/?p={html.escape(dest, True)}">'
            f"../{html.escape(parent[-1])}</a>"
        )
    return f'<nav class="crumb crumb-back">{link}</nav>'


def place_crumb(body: str, rel: str) -> str:
    nav = f'<nav class="crumb">{folder_crumbs(rel)}</nav>'
    if "{{crumb}}" in body or "{{bread}}" in body:
        body = body.replace("{{crumb}}", nav).replace("{{bread}}", nav)
    if "{{crumbback}}" in body:
        body = body.replace("{{crumbback}}", crumb_back(rel))
    return body


def render_folder(folder: Path) -> bytes:
    rel = "" if is_vault_root(folder) else folder.relative_to(VAULT).as_posix()
    extras = ["/index.css"] if (SYS / "index.css").is_file() else []
    loaded = load_index(folder)
    if loaded:
        meta, src = loaded
        title = meta.get("title") or (folder.name if rel else "root")
        body = fill_slots(md_lite(src), folder)
        crumb = folder_crumbs(rel)
        bar = pocket_bar(rel, True)
        return page(
            title,
            body,
            accent_for(rel, meta),
            crumb,
            bar,
            meta.get("environment"),
            extras,
        )
    if not rel:
        body = "<h1>root</h1>" + door_cards(folder)
        return page("root", body, "#6e6254", folder_crumbs(""), pocket_bar(""), extra_css=extras)
    body = f"<h1>{html.escape(folder.name)}</h1>" + file_list(folder, "all")
    return page(folder.name, body, accent_for(rel, {}), folder_crumbs(rel), pocket_bar(rel, True), extra_css=extras)


def page(
    title: str,
    body: str,
    accent: str,
    crumb: str,
    bar: str = "/",
    environment: str | None = None,
    extra_css: list[str] | None = None,
) -> bytes:
    skin = env_name(environment)
    extra = ""
    for href in extra_css or []:
        extra += f'<link rel="stylesheet" href="{html.escape(href, True)}">\n'
    if skin:
        extra += f'<link rel="stylesheet" href="/styles/{html.escape(skin, True)}.css">\n'
    html_out = f"""<!doctype html>
<html lang="en" data-pocket="{html.escape(bar, True)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · pocket-go</title>
<link rel="stylesheet" href="/www.css">
<link rel="stylesheet" href="/dress.css">
<style>:root {{ --note-accent: {accent}; }}</style>
{extra}</head>
<body>
<header class="wwwExplorer_chrome" data-deck-chrome>
  <div class="wwwExplorer_windowTitleBar" data-deck-drag>
    <span class="wwwExplorer_mark" data-deck-menu title="Menu">mypi:go</span>
    <span class="wwwExplorer_title">{html.escape(title)}</span>
    <div class="wwwExplorer_win" data-deck-window-controls aria-label="Window"></div>
  </div>
  <div class="wwwExplorer_linkBar">
    <button type="button" data-webbar="back">back</button>
    <button type="button" data-webbar="forward">forward</button>
    <button type="button" id="REFRESH" data-webbar="refresh"
            title="Shift/Ctrl+click = hard refresh">refresh</button>
    <span id="wwwBar" class="linkSlug" spellcheck="false" title="click a piece to go · double-click to type">{html.escape(bar)}</span>
    <button type="button" id="GO" data-webbar="go">GO!</button>
  </div>
</header>
<div class="wwwExplorer_innerShell">
  <main id="browserWindow">
{body}
  </main>
</div>
<footer class="wwwExplorer_status"><span id="wwwStatus">Done</span></footer>
<script src="/www.js"></script>
</body></html>"""
    return html_out.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[pocket-go]", args[0] if args else fmt)

    def send_html(self, blob: bytes, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(blob)

    def send_bytes(self, blob: bytes, ctype: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(blob)

    def send_style(self, path: str) -> None:
        name = unquote(path[len("/styles/") :])
        if "/" in name or "\\" in name or not name.lower().endswith(".css"):
            self.send_error(404)
            return
        stem = env_name(name)
        if not stem:
            self.send_error(404)
            return
        target = (STYLES / f"{stem}.css").resolve()
        try:
            target.relative_to(STYLES.resolve())
        except ValueError:
            self.send_error(404)
            return
        if not target.is_file():
            self.send_error(404)
            return
        self.send_bytes(target.read_bytes(), "text/css; charset=utf-8")

    def do_GET(self) -> None:
        u = urlparse(self.path)
        if u.path == "/api/health":
            payload = {
                "ok": True,
                "sku": SKU,
                "service": "pocket-go",
                "port": PORT,
                "vault": str(VAULT),
            }
            self.send_bytes(
                json.dumps(payload).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/been":
            self.send_bytes(
                json.dumps({"been": been_load()}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path.startswith("/i/"):
            rel = unquote(u.path[len("/i/") :]).strip("/")
            target = safe_rel(rel)
            if (
                target is None
                or not target.is_file()
                or target.suffix.lower() not in IMAGE_EXT
            ):
                self.send_error(404)
                return
            ctype = IMAGE_TYPE.get(target.suffix.lower(), "application/octet-stream")
            self.send_bytes(target.read_bytes(), ctype)
            return
        if u.path in STATIC:
            ctype, file = STATIC[u.path]
            if not file.is_file():
                self.send_error(404)
                return
            self.send_bytes(file.read_bytes(), ctype)
            return
        if u.path.startswith("/styles/"):
            self.send_style(u.path)
            return
        qs = parse_qs(u.query)
        if "q" in qs:
            q = qs["q"][0]
            exact, nearby, linked = lookup_wiki(q)
            if len(exact) == 1:
                rel = exact[0].relative_to(VAULT).as_posix()
                self.send_response(302)
                self.send_header("Location", "/?p=" + rel)
                self.end_headers()
                return
            self.send_html(wiki_page(q, exact, nearby, linked))
            return
        if "t" in qs:
            self.send_html(tag_page(qs["t"][0]))
            return
        rel = unquote(qs.get("p", [""])[0]).strip("/")
        if not rel or rel.lower() in ("_index", INDEX_NAME):
            self.send_html(self.index())
            return
        target = safe_rel(rel)
        if target is None or not target.exists():
            self.send_html(page("missing", "<p>gone.</p>", "#6e6254", rel, pocket_bar(rel)), 404)
            return
        if target.is_file() and target.name.lower() == INDEX_NAME:
            parent = target.parent
            self.send_html(self.index() if is_vault_root(parent) else self.listing(parent))
            return
        if target.is_dir():
            self.send_html(self.listing(target))
            return
        if target.suffix.lower() == ".md":
            text = target.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_fm(text)
            accent = accent_for(rel, meta)
            bits = [fill_uses(md_lite(body), target.stem, target)]
            slip = headers_block(meta)
            if slip:
                bits.append(slip)
            crumb = folder_crumbs(rel)
            self.send_html(
                page(
                    target.stem,
                    "\n".join(bits),
                    accent,
                    crumb,
                    pocket_bar(rel),
                    meta.get("environment"),
                )
            )
            return
        self.send_html(page("no", "<p>not a note.</p>", "#6e6254", rel, pocket_bar(rel)), 415)

    def do_POST(self) -> None:
        u = urlparse(self.path)
        if u.path != "/api/been":
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            n = 0
        if n < 0 or n > 200_000:
            self.send_error(413)
            return
        raw = self.rfile.read(n) if n else b"[]"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error(400)
            return
        have = been_load()
        incoming = been_clean(data)
        merged = been_clean(have + incoming)
        saved = been_save(merged)
        self.send_bytes(
            json.dumps({"been": saved}).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def index(self) -> bytes:
        return render_folder(VAULT)

    def listing(self, folder: Path) -> bytes:
        return render_folder(folder)


if __name__ == "__main__":
    print(f"pocket-go  http://{HOST}:{PORT}/   vault={VAULT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
