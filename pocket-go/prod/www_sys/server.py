#!/usr/bin/env python3
"""My Pocket Go — early internet in WWW chrome. Edit in Obsidian, refresh here."""

from __future__ import annotations

import html
import json
import os
import re
import threading
import time
from datetime import datetime
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, parse_qsl, quote, unquote, urlencode, urlparse

SYS = Path(__file__).resolve().parent
ROOT = SYS.parents[1]  # pocket-go/
MATS = ROOT / "mats"
STYLES = MATS / "styles"
MATS_IMGS = MATS / "imgs"
BEEN_FILE = ROOT / "prod" / "been.json"
BEEN_LOCK = threading.Lock()
LAST_FILE = ROOT / "prod" / "last.json"
LAST_LOCK = threading.Lock()
_LAST_RESTORED = False
LIBRARIAN = ROOT / "~librarian"
AGENT_ROOT = ROOT / "~agent"
README_ROOT = ROOT / "~readme"
CHARLIE_ROOT = ROOT / "~charlie"
TPS_ROOT = ROOT / "~tps"
LBR_LOCK = threading.Lock()
SHELF_KIND = {
    "librarian": {
        "root": LIBRARIAN,
        "house": "LIBRARIAN",
        "prefix": "LBR",
        "scope": "page",
    },
    "agent": {
        "root": AGENT_ROOT,
        "house": "AGENT",
        "prefix": "AGE",
        "scope": "page",
    },
    "charlie": {
        "root": CHARLIE_ROOT,
        "house": "CHARLIE",
        "prefix": "TAG",
        "scope": "page",
    },
    "tps": {
        "root": TPS_ROOT,
        "house": "TPS",
        "prefix": "TPS",
        "scope": "page",
    },
}
HOST = "127.0.0.1"
PORT = int(os.environ.get("GO_PORT", os.environ.get("LIBRARY_PORT", "43210")))
SKU = "CO.MYPT-004-GO"
SKIP = {".obsidian", ".agents", ".claude", ".opencode", ".git", "~reader"}
START_NAME = "start.md"
ENV_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
FIELD_TOKEN = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]*)\}\}")
SLOT_NAMES = {
    "files",
    "spines",
    "doors",
    "worlds",
    "dir",
    "list",
    "paper",
    "insertdata",
    "images",
    "slides",
    "thumbs",
    "faces",
    "cards",
    "cover",
    "jacket",
    "crumb",
    "bread",
    "shellcrumb",
    "crumbback",
    "home",
    "root",
    "uses",
    "bags",
    "meta",
    "chips",
    "edges",
    "headers",
}


def stash_name(name: str) -> bool:
    """Dot, underscore, and tilde names stay off lists. Media still finds them unless SKIP."""
    return bool(name) and name[0] in "._~"
WIKI_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<![&/\w])#([A-Za-z][\w/-]*)")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,5})\s+(.*)$")
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
OUTLINK_RE = re.compile(r"\{\{(?:outlink|out):([^}|]+)(?:\|([^}]*))?\}\}", re.I)
IMG_MD_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
FACE_CRATE_RE = re.compile(
    r"\{\{(?:face|card):(crate\.[A-Fa-f0-9]{16}|[A-Fa-f0-9]{16})\}\}",
    re.I,
)
CHIP_SPLIT = re.compile(r"\s*[,;]\s*")
META_SLOT_RE = re.compile(r"\{\{(?:meta|chips)(?::(librarian|agent))?\}\}", re.I)
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

HOSTS_ROOT = ROOT / "~hosts"
HOSTS_FILE = HOSTS_ROOT / "_hosts.yaml"
HOST_SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
GO_PREFIX = re.compile(r"^go\.([A-Za-z0-9][A-Za-z0-9_-]*)(?:/(.*))?$", re.I)


@dataclass(frozen=True)
class Host:
    name: str
    root: Path
    title: str = ""


_CURRENT_HOST: ContextVar[Host | None] = ContextVar("pocket_go_host", default=None)


def host_slug(name: str) -> str:
    s = (name or "").strip().lower()
    return s if s and HOST_SLUG.fullmatch(s) else ""


# One-release alias: old go.inbox/{mouth}/... still finds trays/bay homes.
INBOX_LEGACY_HOME = {
    "librarian": "trays",
    "agent": "trays",
    "charlie": "trays",
    "tps": "trays",
    "boybots": "bay",
    "gemini": "bay",
}


def remap_legacy_inbox(name: str, rel: str) -> tuple[str, str]:
    if (name or "").strip().lower() != "inbox":
        return name, rel
    parts = [p for p in (rel or "").replace("\\", "/").strip("/").split("/") if p]
    if not parts:
        return name, rel
    dest = INBOX_LEGACY_HOME.get(parts[0].lower())
    if not dest:
        return name, rel
    return dest, "/".join(parts)


def load_hosts_map(text: str) -> dict[str, dict[str, str]]:
    """Optional ~hosts/_hosts.yaml. Folders still resolve with no file."""
    out: dict[str, dict[str, str]] = {}
    current = ""
    for line in (text or "").replace("\r\n", "\n").split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  ") and ":" in line and current:
            k, v = line.strip().split(":", 1)
            k = k.strip().lower()
            v = v.strip().strip('"').strip("'")
            if k in ("as", "root"):
                k = "folder"
            if k in ("folder", "title") and v:
                out.setdefault(current, {})[k] = v
            continue
        if line[0] not in " \t" and ":" in line:
            k, v = line.split(":", 1)
            current = k.strip()
            v = v.strip().strip('"').strip("'")
            out.setdefault(current, {})
            if v:
                out[current]["folder"] = v
    return out


def discover_hosts() -> dict[str, Host]:
    """A folder under ~hosts is go.{name}. Nothing is reserved. Start is not a host."""
    found: dict[str, Host] = {}
    aliases: dict[str, dict[str, str]] = {}
    if HOSTS_FILE.is_file():
        try:
            aliases = load_hosts_map(HOSTS_FILE.read_text(encoding="utf-8"))
        except OSError:
            aliases = {}
    if HOSTS_ROOT.is_dir():
        try:
            hosts_root = HOSTS_ROOT.resolve()
        except OSError:
            hosts_root = HOSTS_ROOT
        for child in sorted(HOSTS_ROOT.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            if stash_name(child.name) or child.name in SKIP:
                continue
            slug = host_slug(child.name)
            if not slug:
                continue
            found[slug] = Host(slug, child, child.name)
        for name, meta in aliases.items():
            slug = host_slug(name)
            if not slug:
                continue
            folder = str(meta.get("folder") or name).strip() or name
            root = (HOSTS_ROOT / folder).resolve()
            try:
                root.relative_to(hosts_root)
            except ValueError:
                continue
            if not root.is_dir():
                continue
            title = str(meta.get("title") or "").strip() or found.get(slug, Host(slug, root)).title or slug
            found[slug] = Host(slug, root, title)
    return found


def lobby_host() -> Host:
    return Host("", HOSTS_ROOT, "start")


def is_lobby() -> bool:
    spec = _CURRENT_HOST.get()
    return spec is not None and spec.name == ""


def get_host(name: str) -> Host | None:
    s = (name or "").strip().lower()
    if not s:
        return lobby_host()
    slug = host_slug(s)
    if not slug:
        return None
    return discover_hosts().get(slug)


def active_host() -> str:
    spec = _CURRENT_HOST.get()
    return spec.name if spec is not None else ""


def active_vault() -> Path:
    spec = _CURRENT_HOST.get()
    return spec.root if spec is not None else HOSTS_ROOT


@contextmanager
def using_host(host: Host | None):
    if host is None:
        yield None
        return
    tok = _CURRENT_HOST.set(host)
    try:
        yield host
    finally:
        _CURRENT_HOST.reset(tok)


def split_pocket(raw: str) -> tuple[str, str]:
    """Address or shelf pocket → (host, rel). Empty host is the start page."""
    s = (raw or "").replace("\\", "/").strip()
    m = GO_PREFIX.match(s)
    if m:
        rel = (m.group(2) or "").strip("/")
        if rel.lower() in ("_index", INDEX_NAME, "index", PAPER_NAME):
            rel = ""
        return remap_legacy_inbox(m.group(1).lower(), rel)
    rel = s.strip("/")
    if rel.lower() in ("start", START_NAME, "_index", INDEX_NAME, "index", PAPER_NAME):
        rel = ""
    return remap_legacy_inbox("", rel)


def pocket_host_bin(pocket: str) -> str:
    """Chest label for a page: go.{host}, or start."""
    name, _rel = split_pocket(pocket)
    if not name:
        return "start"
    return "go." + name


def parse_request_pocket(qs: dict) -> tuple[str, str]:
    h = host_slug(unquote((qs.get("h") or [""])[0]))
    p = unquote((qs.get("p") or [""])[0])
    name, rel = split_pocket(p)
    if h:
        name = h
        if not GO_PREFIX.match((p or "").replace("\\", "/").strip()):
            rel = (p or "").replace("\\", "/").strip("/")
            if rel.lower() in ("start", START_NAME, "_index", INDEX_NAME, "index", PAPER_NAME):
                rel = ""
    return remap_legacy_inbox(name, rel)


@contextmanager
def using_pocket(raw: str):
    name, _rel = split_pocket(raw)
    with using_host(get_host(name)) as host:
        yield host


def page_href(rel: str = "", is_dir: bool = False) -> str:
    p = (rel or "").replace("\\", "/").strip("/")
    host = active_host()
    if not host:
        if not p or p.lower() in ("start", START_NAME.replace(".md", "")):
            return "/"
        return "/?p=" + quote(p, safe="/")
    href = "/?h=" + quote(host)
    if p:
        href += "&p=" + quote(p, safe="/")
    return href


def href_from_pocket(pocket: str) -> str:
    name, rel = split_pocket(pocket)
    host = get_host(name)
    if host is None:
        return "/"
    with using_host(host):
        return page_href(rel)


def tag_href(slug: str) -> str:
    crate = norm_crate(str(slug or "").lstrip("#"))
    if crate:
        return crate_href(crate)
    return "/?c=" + quote(slug)


def crate_href(crate: str) -> str:
    c = norm_crate(crate)
    return "/?k=" + quote(c) if c else "/"


def card_pop_href(crate: str) -> str:
    c = norm_crate(crate)
    return "/?card=" + quote(c) if c else "/"


def value_door_href(mouth: str, label: str, value: str) -> str:
    """A crate id is a crate door. Anything else is the catalog ledger for that value."""
    crate = norm_crate(value)
    if crate:
        return crate_href(crate)
    return catalog_field_href(mouth, label, value)


def wiki_href(query: str) -> str:
    host = active_host()
    if not host:
        return "/?q=" + quote(query)
    return "/?h=" + quote(host) + "&q=" + quote(query)


def outlink_ok(raw: str) -> str:
    """http(s) only. Empty if the string is not a real outside URL."""
    s = (raw or "").strip()
    if not s or len(s) > 2000 or any(c in s for c in "\n\r\t "):
        return ""
    try:
        u = urlparse(s)
    except Exception:
        return ""
    if u.scheme not in ("http", "https") or not u.netloc:
        return ""
    return s


def outlink_html(url: str, label: str = "") -> str:
    href = outlink_ok(url)
    if not href:
        return ""
    shown = (label or "").strip()
    if not shown:
        shown = urlparse(href).netloc or href
    return (
        f'<a class="outlink" href="{html.escape(href, True)}" '
        f'data-outlink="1" rel="noopener noreferrer" title="outside the pocket">'
        f"{html.escape(shown)}</a>"
    )


def img_href(rel: str) -> str:
    p = (rel or "").replace("\\", "/").strip("/")
    host = active_host()
    if not host:
        return "/i/" + quote(p, safe="/")
    return "/i/" + quote("go." + host + "/" + p, safe="/")


def mats_img_href(p: Path) -> str:
    rel = p.relative_to(MATS_IMGS).as_posix()
    return "/i/" + quote(rel, safe="/")


def find_mats_img(name: str) -> Path | None:
    raw = (name or "").strip().replace("\\", "/").strip("/")
    if not raw or "://" in raw or ".." in Path(raw).parts:
        return None
    if not MATS_IMGS.is_dir():
        return None
    try:
        root = MATS_IMGS.resolve()
    except OSError:
        return None
    if "/" in raw:
        target = (MATS_IMGS / raw).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            return None
        if target.is_file() and target.suffix.lower() in IMAGE_EXT:
            return target
    needle = Path(raw).name.lower()
    hits: list[Path] = []
    for p in MATS_IMGS.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:
            continue
        if p.name.lower() != needle:
            continue
        try:
            p.relative_to(root)
        except ValueError:
            continue
        hits.append(p)
    if not hits:
        return None
    hits.sort(key=lambda x: x.as_posix().lower())
    return hits[0]


def shelf_rel(root: Path, rel: Path) -> Path | None:
    dest = (root / rel).resolve() if not active_host() else (root / active_host() / rel).resolve()
    try:
        dest.relative_to(root.resolve())
    except (ValueError, OSError):
        return None
    return dest


def kid_href(p: Path) -> str:
    """Lobby folders are go.* doors. Inside a host they are ordinary paths."""
    try:
        r = p.relative_to(active_vault()).as_posix()
    except ValueError:
        return "/"
    if is_lobby() and p.is_dir():
        slug = host_slug(p.name)
        if slug:
            return "/?h=" + quote(slug)
    return page_href(r)

COLORS = {
    "yellow": "#c9a227",
    "orange": "#c45c26",
    "red": "#a33b3b",
    "green": "#2d6a4f",
    "purple": "#6b3fa0",
    "blue": "#2c5aa0",
    "amber": "#c9892d",
}
ENV_STRIP = {
    "cc": "#e8a317",
    "journal": "#6a4028",
    "canvas": "#2a3f3d",
    "danyi": "#7a4a8a",
    "ports": "#e8b923",
    "bookstore": "#c9892d",
    "writing-club": "#2a4a8a",
    "whitepages": "#1e3a5f",
    "pulls": "#8a5a18",
    "oix": "#6b5ea8",
    "business": "#9b1209",
    "yellowpages": "#9b1209",
    "desk": "#2c4a6e",
    "agentk": "#9a1c18",
    "terminal-ab": "#ff2400",
    "terminal-io": "#38b433",
    "poetry-club": "#a84c6c",
    "kmoire": "#c45c48",
    "chester": "#2bff00",
    "terminal-root": "#2bff00",
    "build-desk": "#2c4a6e",
    "mythleak": "#8a000c",
    "buddy": "#8a4aaa",
    "trays": "#2d6a4f",
    "bay": "#c45828",
}
HOUSE_STRIP = {
    "agent": "#a33b3b",
    "charlie": "#c9892d",
    "librarian": "#2d6a4f",
}
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{3,8}$")
CSS_IMPORT = re.compile(r"""@import\s+(?:url\()?["']([^"']+)["']""", re.I)
CSS_ROOT = re.compile(r":root\s*\{", re.I)
CSS_DECL = re.compile(r"--([A-Za-z0-9_-]+)\s*:\s*([^;]+);")
CSS_VAR = re.compile(r"""var\(\s*--([A-Za-z0-9_-]+)\s*(?:,[^)]*)?\)""", re.I)
CSS_RGB = re.compile(
    r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
    re.I,
)
_ENV_CSS_STRIP: dict[str, str] = {}


def css_hex(raw: str) -> str:
    s = str(raw or "").strip()
    return s if HEX_COLOR.fullmatch(s) else ""

STATIC = {
    "/www.css": ("text/css; charset=utf-8", SYS / "www.css"),
    "/www.js": ("text/javascript; charset=utf-8", SYS / "www.js"),
    "/dress.css": ("text/css; charset=utf-8", SYS / "dress.css"),
    "/index.css": ("text/css; charset=utf-8", SYS / "index.css"),
    "/librarian.css": ("text/css; charset=utf-8", SYS / "librarian.css"),
    "/librarian.js": ("text/javascript; charset=utf-8", SYS / "librarian.js"),
    "/tagbay.css": ("text/css; charset=utf-8", SYS / "tagbay.css"),
    "/canvas.css": ("text/css; charset=utf-8", SYS / "canvas.css"),
    "/canvas.js": ("text/javascript; charset=utf-8", SYS / "canvas.js"),
}
CATALOG_API = {
    "/api/librarian": "librarian",
    "/api/agent": "agent",
}
SHELF_API = {
    "/api/charlie": "charlie",
}
TPS_TITLES = ("created", "referenced")
INDEX_NAME = "_index.md"
PAPER_NAME = "index.md"
PAPER_HOLE = re.compile(
    r"(?:<p>\s*)?\{\{(?:paper|insertdata)\}\}(?:\s*</p>)?",
    re.I,
)
BEEN_MAX = 2000
SIGIL_RE = re.compile(r"(?<![A-Za-z0-9._:/-])([#$^@])([A-Za-z0-9._:/-]+)")
CITE_CRATE_RE = re.compile(
    r"(?<![A-Za-z0-9._:/-])\^((?:crate\.)?[A-Fa-f0-9]{16})\b",
    re.I,
)
LEAF_MAX = 20_000
README_MAX = 200_000


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


LAST_BLOCK = frozenset(
    {"sidecar", "k", "crate", "c", "t", "m", "f", "bay", "as", "bin", "v", "here", "card"}
)


def desk_href_ok(href: str) -> bool:
    href = (href or "").strip()
    if not href.startswith("/") or href.startswith("//") or len(href) > 500:
        return False
    try:
        u = urlparse(href)
    except ValueError:
        return False
    if u.scheme or u.netloc or u.path != "/":
        return False
    pairs = parse_qsl(u.query, keep_blank_values=True)
    if any(k in LAST_BLOCK for k, _ in pairs):
        return False
    return True


def desk_href_from_url(path: str) -> str | None:
    try:
        u = urlparse(path)
    except ValueError:
        return None
    if u.path != "/":
        return None
    pairs = parse_qsl(u.query, keep_blank_values=True)
    if any(k in LAST_BLOCK for k, _ in pairs):
        return None
    kept = [(k, v) for k, v in pairs if k not in ("_cb", "home")]
    if not kept:
        return "/"
    href = "/?" + urlencode(kept)
    return href if desk_href_ok(href) else None


def last_load() -> str:
    with LAST_LOCK:
        if not LAST_FILE.is_file():
            return ""
        try:
            data = json.loads(LAST_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""
    href = ""
    if isinstance(data, dict):
        href = str(data.get("href") or "")
    elif isinstance(data, str):
        href = data
    href = href.strip()
    if href in ("", "/") or not desk_href_ok(href):
        return ""
    return href


def last_save(href: str) -> str:
    href = desk_href_from_url(href) or ""
    if not href or not desk_href_ok(href):
        return last_load()
    with LAST_LOCK:
        LAST_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_FILE.write_text(json.dumps({"href": href}, indent=0) + "\n", encoding="utf-8")
    return href


def blank_home_qs(qs: dict) -> bool:
    for k in qs:
        if k == "_cb":
            continue
        return False
    return True


def take_launch_restore() -> bool:
    global _LAST_RESTORED
    with LAST_LOCK:
        if _LAST_RESTORED:
            return False
        _LAST_RESTORED = True
        return True


def parse_sigils(leaf: str) -> dict[str, list[str]]:
    tags: list[str] = []
    namespaces: list[str] = []
    times: list[str] = []
    cites: list[str] = []
    buckets = {"#": tags, "$": namespaces, "@": times, "^": cites}
    seen = {"#": set(), "$": set(), "@": set(), "^": set()}
    for m in SIGIL_RE.finditer(leaf or ""):
        sig, tok = m.group(1), m.group(2)
        if tok in seen[sig]:
            continue
        seen[sig].add(tok)
        buckets[sig].append(tok)
    return {
        "tags": tags,
        "namespaces": namespaces,
        "times": times,
        "cites": cites,
    }


def yaml_scalar(s: str) -> str:
    if s == "":
        return '""'
    if s.strip() != s or any(c in s for c in ":#{}[]&*!|>%@`'\",\n"):
        return json.dumps(s, ensure_ascii=False)
    return s


def yaml_str_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(yaml_scalar(x) for x in items) + "]"


def parse_flow_list(raw: str) -> list[str]:
    s = (raw or "").strip()
    if not s or s == "[]":
        return []
    if s.startswith("["):
        try:
            v = json.loads(s)
        except json.JSONDecodeError:
            v = None
        if isinstance(v, list):
            return [str(x) for x in v if str(x)]
        inner = s[1:-1].strip() if s.endswith("]") else s[1:].strip()
        if not inner:
            return []
        return [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
    return [s.strip().strip('"').strip("'")] if s else []


def blot_dump(obj: dict) -> str:
    lines = [
        "house: " + yaml_scalar(str(obj.get("house") or "LIBRARIAN")),
        "pocket: " + yaml_scalar(str(obj.get("pocket") or "/")),
    ]
    crate = str(obj.get("crate") or "").strip()
    if crate:
        lines.append("crate: " + yaml_scalar(crate))
    try:
        nxt = int(obj.get("next") or 1)
    except (TypeError, ValueError):
        nxt = 1
    if nxt < 1:
        nxt = 1
    lines.append("next: " + str(nxt))
    thoughts = obj.get("thoughts") or []
    if not isinstance(thoughts, list) or not thoughts:
        lines.append("thoughts: []")
    else:
        lines.append("thoughts:")
        for t in thoughts:
            if not isinstance(t, dict):
                continue
            leaf = str(t.get("leaf") or "").replace("\r\n", "\n").replace("\r", "\n")
            if leaf.endswith("\n"):
                leaf = leaf[:-1]
            try:
                at = int(t.get("at") or 0)
            except (TypeError, ValueError):
                at = 0
            lines.append("  - id: " + yaml_scalar(str(t.get("id") or "")))
            lines.append("    at: " + str(at))
            lines.append("    leaf: |")
            if not leaf:
                lines.append("      ")
            else:
                for line in leaf.split("\n"):
                    lines.append("      " + line)
            lines.append("    tags: " + yaml_str_list([str(x) for x in (t.get("tags") or [])]))
            lines.append(
                "    namespaces: " + yaml_str_list([str(x) for x in (t.get("namespaces") or [])])
            )
            lines.append("    times: " + yaml_str_list([str(x) for x in (t.get("times") or [])]))
            lines.append("    cites: " + yaml_str_list([str(x) for x in (t.get("cites") or [])]))
    threads = obj.get("threads") or []
    if isinstance(threads, list) and threads:
        lines.append("threads:")
        for t in threads:
            if not isinstance(t, dict):
                continue
            try:
                at = int(t.get("at") or 0)
            except (TypeError, ValueError):
                at = 0
            lines.append("  - id: " + yaml_scalar(str(t.get("id") or "")))
            lines.append("    at: " + str(at))
            lines.append("    from: " + yaml_scalar(str(t.get("from") or "")))
            lines.append("    rel: " + yaml_scalar(str(t.get("rel") or "")))
            lines.append("    to: " + yaml_scalar(str(t.get("to") or "")))
    return "\n".join(lines) + "\n"


def blot_load(text: str) -> dict:
    empty = empty_blot("/")
    if not (text or "").strip():
        return empty
    house = "LIBRARIAN"
    pocket = "/"
    crate = ""
    nxt = 1
    thoughts: list[dict] = []
    threads: list[dict] = []
    section = "thoughts"
    cur: dict | None = None
    in_leaf = False
    leaf_lines: list[str] = []

    def finish_leaf() -> None:
        nonlocal in_leaf, leaf_lines, cur
        if cur is not None and in_leaf:
            leaf = "\n".join(leaf_lines)
            if leaf.endswith("\n"):
                leaf = leaf[:-1]
            marks = parse_sigils(leaf)
            cur["leaf"] = leaf
            cur["tags"] = marks["tags"]
            cur["namespaces"] = marks["namespaces"]
            cur["times"] = marks["times"]
            cur["cites"] = marks["cites"]
        in_leaf = False
        leaf_lines = []

    def finish_item() -> None:
        nonlocal cur
        finish_leaf()
        if cur is None:
            return
        if section == "threads":
            threads.append(cur)
        else:
            thoughts.append(cur)
        cur = None

    def new_thought() -> dict:
        return {
            "id": "",
            "at": 0,
            "leaf": "",
            "tags": [],
            "namespaces": [],
            "times": [],
            "cites": [],
        }

    def new_thread() -> dict:
        return {"id": "", "at": 0, "from": "", "rel": "", "to": ""}

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if in_leaf:
            if raw_line.startswith("      "):
                leaf_lines.append(raw_line[6:])
                continue
            if raw_line.strip() == "":
                leaf_lines.append("")
                continue
            finish_leaf()
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw_line.startswith((" ", "\t")) and ":" in stripped:
            finish_item()
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if key == "house":
                house = val.strip('"').strip("'") or house
            elif key == "pocket":
                pocket = val.strip('"').strip("'") or "/"
            elif key == "crate":
                crate = val.strip('"').strip("'")
            elif key == "next":
                try:
                    nxt = int(val)
                except ValueError:
                    nxt = 1
            elif key == "thoughts":
                section = "thoughts"
            elif key == "threads":
                section = "threads"
            continue
        if raw_line.startswith("  - "):
            finish_item()
            cur = new_thread() if section == "threads" else new_thought()
            rest = raw_line[4:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                if k.strip() == "id":
                    cur["id"] = v.strip().strip('"').strip("'")
            continue
        if cur is None or ":" not in stripped:
            continue
        key, val = stripped.split(":", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key == "id":
            cur["id"] = val
        elif key == "at":
            try:
                cur["at"] = int(val)
            except ValueError:
                cur["at"] = 0
        elif section == "threads":
            if key == "from":
                cur["from"] = val
            elif key == "rel":
                cur["rel"] = val
            elif key == "to":
                cur["to"] = val
        elif key == "leaf":
            if val == "|" or val.startswith("|"):
                in_leaf = True
                leaf_lines = []
            else:
                cur["leaf"] = val
                marks = parse_sigils(cur["leaf"])
                cur.update(marks)
        elif key == "tags":
            cur["tags"] = parse_flow_list(val)
        elif key == "namespaces":
            cur["namespaces"] = parse_flow_list(val)
        elif key == "times":
            cur["times"] = parse_flow_list(val)
        elif key == "cites":
            cur["cites"] = parse_flow_list(val)
    finish_item()
    if nxt < 1:
        nxt = 1
    return {
        "house": house or "LIBRARIAN",
        "pocket": pocket or "/",
        "crate": crate,
        "next": nxt,
        "thoughts": thoughts,
        "threads": threads,
    }


def empty_blot(pocket: str, house: str = "LIBRARIAN") -> dict:
    return {
        "house": house or "LIBRARIAN",
        "pocket": pocket or "/",
        "crate": "",
        "next": 1,
        "thoughts": [],
        "threads": [],
    }


def resolve_vault_page(raw: str) -> Path | None:
    _name, rel = split_pocket(raw)
    if not rel:
        root = active_vault()
        return root if root.is_dir() else None
    target = safe_rel(rel)
    if (target is None or not target.exists()) and not rel.lower().endswith(".md"):
        alt = safe_rel(rel + ".md")
        if alt is not None and alt.exists():
            target = alt
    if target is None or not target.exists():
        return None
    if target.is_file() and target.name.lower() in {INDEX_NAME, PAPER_NAME}:
        return target.parent
    return target


def shelf_file(kind: str, target: Path) -> Path | None:
    spec = SHELF_KIND.get(kind)
    if not spec:
        return None
    try:
        root = spec["root"].resolve()
        vault = active_vault().resolve()
        page = target.resolve()
    except OSError:
        return None
    if spec["scope"] == "index":
        folder = nearest_index_folder(page)
        if folder is None:
            return None
        page = folder
    if is_vault_root(page):
        rel = Path("_index.yaml")
    elif page.is_dir():
        try:
            rel = page.relative_to(vault) / "_index.yaml"
        except ValueError:
            return None
    elif page.suffix.lower() == ".md":
        try:
            rel = page.relative_to(vault).with_suffix(".yaml")
        except ValueError:
            return None
    elif page.suffix.lower() == ".canvas":
        # Keep full name so sibling foo.md / foo.canvas do not share one yaml.
        try:
            rel = Path(str(page.relative_to(vault)) + ".yaml")
        except ValueError:
            return None
    else:
        return None
    if ".." in rel.parts:
        return None
    return shelf_rel(root, rel)


def readme_dest_for_folder(folder: Path) -> Path | None:
    """~readme/{vault-rel}/README.md for one index folder."""
    try:
        root = README_ROOT.resolve()
        vault = active_vault().resolve()
        page = folder.resolve()
    except OSError:
        return None
    if is_vault_root(page):
        rel = Path("README.md")
    else:
        try:
            rel = page.relative_to(vault) / "README.md"
        except ValueError:
            return None
    if ".." in rel.parts:
        return None
    return shelf_rel(root, rel)


def readme_resolve(target: Path) -> tuple[Path, Path] | None:
    """Room letter. Nearest existing README walking up; else the nearest _index."""
    folder = nearest_index_folder(target)
    if folder is None:
        return None
    nearest_dest = readme_dest_for_folder(folder)
    if nearest_dest is None:
        return None
    try:
        vault = active_vault().resolve()
        cur = folder.resolve()
    except OSError:
        return None
    while True:
        dest = readme_dest_for_folder(cur)
        if dest is not None and dest.is_file():
            return cur, dest
        if is_vault_root(cur):
            return folder, nearest_dest
        parent = cur.parent
        if parent == cur:
            return folder, nearest_dest
        try:
            parent.relative_to(vault)
        except ValueError:
            return folder, nearest_dest
        cur = parent


def readme_get(pocket_raw: str) -> tuple[int, dict | None, str]:
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_get(pocket_raw)


def _readme_get(pocket_raw: str) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    found = readme_resolve(target)
    if found is None:
        return 400, None, "not a vault page"
    folder, dest = found
    body = ""
    if dest.is_file():
        try:
            body = dest.read_text(encoding="utf-8")
        except OSError:
            return 500, None, "could not read readme"
    return 200, _readme_payload(folder, dest, body, target), ""


def readme_put(pocket_raw: str, body: str) -> tuple[int, dict | None, str]:
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    if len(body) > README_MAX:
        return 413, None, "readme too long"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_put(pocket_raw, body)


def _readme_put(pocket_raw: str, body: str) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    found = readme_resolve(target)
    if found is None:
        return 400, None, "not a vault page"
    folder, dest = found
    with LBR_LOCK:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")
    obj = _readme_payload(folder, dest, body, target)
    return 200, obj, ""


def split_note(text: str) -> tuple[str, str]:
    """Front matter (no fences) and the markdown body."""
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end >= 0:
            return raw[4:end].strip("\n"), raw[end + 5 :].lstrip("\n")
    return "", raw


def join_note(headers: str, markdown: str) -> str:
    h = (headers or "").replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    b = (markdown or "").replace("\r\n", "\n").replace("\r", "\n")
    if h.startswith("---"):
        h = h[3:].lstrip("\n")
    if h.endswith("\n---"):
        h = h[: -4].rstrip("\n")
    if h.strip():
        out = "---\n" + h.strip() + "\n---\n"
        return out + (("\n" + b) if b else "")
    return b


def force_crate_line(text: str, crate: str) -> str:
    """Keep the live crate. Never overwrite with a different one."""
    crate = (crate or "").strip()
    if not crate:
        return text
    raw = text.replace("\r\n", "\n")
    if not raw.startswith("---\n"):
        return "---\ncrate: " + crate + "\n---\n\n" + raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return text
    head = raw[4:end]
    rest = raw[end + 5 :]
    lines = head.split("\n")
    found = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith("crate:"):
            found = True
            new_lines.append("crate: " + crate)
        else:
            new_lines.append(line)
    if not found:
        new_lines.insert(0, "crate: " + crate)
    return "---\n" + "\n".join(new_lines) + "\n---\n" + rest


def patch_fm_keys(text: str, updates: dict[str, str]) -> str:
    """Rewrite named YAML keys. Never touches `crate:` — call force_crate_line for that."""
    raw = (text or "").replace("\r\n", "\n")
    if not updates or not raw.startswith("---\n"):
        return text
    end = raw.find("\n---\n", 4)
    if end < 0:
        return text
    head = raw[4:end]
    rest = raw[end + 5 :]
    pending = dict(updates)
    pending.pop("crate", None)
    new_lines: list[str] = []
    for line in head.split("\n"):
        if ":" in line and not line.startswith(" "):
            k = line.split(":", 1)[0].strip()
            if k == "crate":
                new_lines.append(line)
                continue
            if k in pending:
                new_lines.append(k + ": " + pending.pop(k))
                continue
        new_lines.append(line)
    for k, v in pending.items():
        if k == "crate":
            continue
        new_lines.append(k + ": " + v)
    return "---\n" + "\n".join(new_lines) + "\n---\n" + rest


def folder_clay_files(target: Path) -> list[tuple[str, Path]]:
    """Which vault notes the page face can edit. A named note is just itself.
    A folder (or index/_index, which resolve to the folder) offers this folder's
    paper, then its shell if that file exists. Paper is always this folder —
    never an ancestor's. The file may not exist yet; Keep writes it."""
    if target.is_file() and target.suffix.lower() == ".md":
        name = target.name.lower()
        if name not in {INDEX_NAME, PAPER_NAME}:
            return [("note", target)]
        target = target.parent
    if not target.is_dir():
        return []
    out: list[tuple[str, Path]] = []
    start = lobby_start(target)
    if start is not None:
        out.append(("note", start))
        return out
    out.append(("paper", target / PAPER_NAME))
    shell = target / INDEX_NAME
    if shell.is_file():
        out.append(("shell", shell))
    return out


def page_note_file(target: Path, which: str = "") -> Path | None:
    files = folder_clay_files(target)
    if not files:
        if target.is_file() and target.suffix.lower() == ".md":
            return target
        return None
    want = (which or "").strip().lower()
    if want:
        for kind, path in files:
            if kind == want:
                return path
    return files[0][1]


def clay_payload(path: Path, kind: str) -> dict | None:
    headers, markdown, crate = "", "", ""
    if path.is_file():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            text = ""
        headers, markdown = split_note(text)
        crate = file_crate(path)
    try:
        here = path if path.is_file() else path.parent
        pocket = pocket_key(here)
    except OSError:
        pocket = pocket_key(path.parent)
    return {
        "kind": kind,
        "pocket": pocket,
        "crate": crate,
        "headers": headers,
        "markdown": markdown,
        "file": path.name,
    }


def page_note_payload(target: Path, which: str = "") -> dict | None:
    files = folder_clay_files(target)
    if not files:
        dest = page_note_file(target, which)
        if dest is None:
            return None
        files = [("note", dest)]
    pages: list[dict] = []
    for kind, path in files:
        item = clay_payload(path, kind)
        if item:
            pages.append(item)
    if not pages:
        return None
    want = (which or "").strip().lower()
    chosen = pages[0]
    if want:
        for item in pages:
            if item.get("kind") == want:
                chosen = item
                break
    chosen = dict(chosen)
    chosen["pages"] = pages
    return chosen


def _readme_payload(folder: Path, dest: Path, body: str, target: Path) -> dict:
    pocket = pocket_key(folder)
    obj = {
        "house": "README",
        "pocket": pocket,
        "crate": page_crate(folder),
        "body": body,
        "route": pocket,
        "face": "room",
    }
    page = page_note_payload(target)
    if page is not None:
        obj["page"] = page
    return obj


def readme_page_put(
    pocket_raw: str, headers: str, markdown: str, which: str = ""
) -> tuple[int, dict | None, str]:
    headers = (headers or "").replace("\r\n", "\n").replace("\r", "\n")
    markdown = (markdown or "").replace("\r\n", "\n").replace("\r", "\n")
    if len(headers) + len(markdown) > README_MAX:
        return 413, None, "page too long"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_page_put(pocket_raw, headers, markdown, which)


def _readme_page_put(
    pocket_raw: str, headers: str, markdown: str, which: str = ""
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = page_note_file(target, which)
    if dest is None:
        return 400, None, "no page file"
    found = readme_resolve(target)
    if found is None:
        return 400, None, "not a vault page"
    folder, room_dest = found
    mint = False
    with LBR_LOCK:
        try:
            old = dest.read_text(encoding="utf-8")
        except OSError:
            old = ""
        live = file_crate(dest) if dest.is_file() else ""
        if not live:
            live = str(parse_fm(old)[0].get("crate") or "").strip()
        text = join_note(headers, markdown)
        if live:
            text = force_crate_line(text, live)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        mint = not live
        room_body = ""
        if room_dest.is_file():
            try:
                room_body = room_dest.read_text(encoding="utf-8")
            except OSError:
                room_body = ""
    if mint:
        ensure_crate(dest)
    obj = _readme_payload(folder, room_dest, room_body, target)
    page = page_note_payload(target, which)
    if page is not None:
        obj["page"] = page
    obj["face"] = "page"
    return 200, obj, ""


RESERVED_NOTES = {INDEX_NAME, PAPER_NAME, START_NAME, "readme.md"}
WIN_DEVICE = re.compile(r"^(con|prn|aux|nul|com[1-9]|lpt[1-9])$", re.I)


def clay_folder(target: Path) -> Path | None:
    """The folder a launched note lands in: this hall, or the parent of this note."""
    if target.is_file():
        return target.parent
    if target.is_dir():
        return target
    return None


def note_stem(title: str) -> str:
    s = (title or "").replace("\r", " ").replace("\n", " ").strip()
    s = s.replace("\\", " ").replace("/", " ")
    s = re.sub(r'[<>:"|?*]', "", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    if s.lower().endswith(".md"):
        s = s[:-3].rstrip(" .")
    if len(s) > 120:
        s = s[:120].rstrip(" .")
    return s


def note_filename(title: str) -> str | None:
    stem = note_stem(title)
    if not stem or WIN_DEVICE.match(stem):
        return None
    name = stem + ".md"
    if name.lower() in {n.lower() for n in RESERVED_NOTES}:
        return None
    if stash_name(name):
        return None
    return name


def readme_note_add(pocket_raw: str, title: str) -> tuple[int, dict | None, str]:
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not title:
        return 400, None, "need a name"
    fname = note_filename(title)
    if fname is None:
        stem = note_stem(title)
        if stem and (stem + ".md").lower() in {n.lower() for n in RESERVED_NOTES}:
            return 400, None, "that's paper or shell — Keep on page"
        return 400, None, "need a name"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_note_add(pocket_raw, title, fname)


def _readme_note_add(
    pocket_raw: str, title: str, fname: str
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    folder = clay_folder(target)
    if folder is None or not folder.is_dir():
        return 400, None, "not a vault page"
    if not _in_active_vault(folder):
        return 400, None, "not a vault page"
    dest = folder / fname
    try:
        for p in folder.iterdir():
            if p.name.lower() == fname.lower():
                return 409, None, "already a page by that name"
    except OSError:
        return 500, None, "could not read folder"
    crate = mint_crate_id()
    text = (
        "---\n"
        "crate: " + crate + "\n"
        "title: " + yaml_scalar(title) + "\n"
        "---\n\n"
        "# {{title}}\n"
    )
    with LBR_LOCK:
        if dest.exists():
            return 409, None, "already a page by that name"
        dest.write_text(text, encoding="utf-8")
    rel = dest.relative_to(active_vault()).as_posix()
    return 200, {
        "file": fname,
        "href": page_href(rel),
        "pocket": pocket_key(dest),
        "crate": crate,
    }, ""


def librarian_file(target: Path) -> Path | None:
    return shelf_file("librarian", target)


def pocket_key(target: Path) -> str:
    root = active_vault().resolve()
    host = active_host()
    try:
        page = target.resolve()
    except OSError:
        return "go." + host + "/" if host else "/"
    if is_vault_root(page):
        rel = ""
    else:
        try:
            rel = page.relative_to(root).as_posix()
        except ValueError:
            return "go." + host + "/" if host else "/"
    if not host:
        if not rel or rel.lower() in ("start", START_NAME):
            return "/"
        return "/" + rel
    return "go." + host + "/" + rel if rel else "go." + host + "/"


def lobby_start(folder: Path) -> Path | None:
    """start.md is the lobby front door, not a shell/paper pair."""
    if is_lobby() and is_vault_root(folder):
        p = folder / START_NAME
        if p.is_file():
            return p
    return None


def read_canvas_crate(path: Path) -> str:
    """Crate stamped into canvas JSON metadata.crate (nodes/edges untouched)."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    meta = data.get("metadata")
    if isinstance(meta, dict):
        return str(meta.get("crate") or "").strip()
    # tolerate a bare top-level crate if an older stamp used it
    return str(data.get("crate") or "").strip()


def apply_canvas_crate(path: Path, crate: str) -> bool:
    """Write metadata.crate into a .canvas file. Never overwrite a live one.
    Keeps nodes/edges; uses tab indent to match typical Obsidian canvas files.
    """
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    have = str(meta.get("crate") or data.get("crate") or "").strip()
    if have:
        return False
    meta = dict(meta)
    meta["crate"] = crate
    data["metadata"] = meta
    # drop legacy top-level crate if we are standardizing on metadata
    data.pop("crate", None)
    try:
        dumped = json.dumps(data, ensure_ascii=False, indent="\t") + "\n"
        path.write_text(dumped, encoding="utf-8")
    except OSError:
        return False
    return True


def file_crate(path: Path) -> str:
    if not path.is_file():
        return ""
    suf = path.suffix.lower()
    if suf == ".md":
        return str(read_md_meta(path).get("crate") or "").strip()
    if suf == ".canvas":
        return read_canvas_crate(path)
    return ""


def page_crate(target: Path) -> str:
    """Room crate. Shell first. README hangs here."""
    if target.is_dir():
        start = lobby_start(target)
        if start is not None:
            return file_crate(start)
        for name in (INDEX_NAME, PAPER_NAME):
            c = file_crate(target / name)
            if c:
                return c
        return ""
    return file_crate(target)


def bag_crate(target: Path) -> str:
    """Page crate. Paper first on a folder — tagging hangs on the fill."""
    if target.is_dir():
        start = lobby_start(target)
        if start is not None:
            return file_crate(start)
        for name in (PAPER_NAME, INDEX_NAME):
            c = file_crate(target / name)
            if c:
                return c
        return ""
    return file_crate(target)


def blot_read(path: Path, pocket: str, house: str = "LIBRARIAN") -> dict:
    empty = empty_blot(pocket, house)
    if not path.is_file():
        return empty
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return empty
    obj = blot_load(text)
    obj["house"] = house
    obj["pocket"] = pocket or obj.get("pocket") or "/"
    try:
        nxt = int(obj.get("next") or 1)
    except (TypeError, ValueError):
        nxt = 1
    obj["next"] = max(1, nxt)
    thoughts = obj.get("thoughts") or []
    obj["thoughts"] = [t for t in thoughts if isinstance(t, dict)]
    threads = obj.get("threads") or []
    obj["threads"] = [t for t in threads if isinstance(t, dict)]
    return obj


def blot_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(blot_dump(obj), encoding="utf-8")


FIELD_TYPES = ("time", "bool", "input", "textbox")
LORE_LINE_MAX = 255
TRAYS_HOST = HOSTS_ROOT / "trays"
BAY_HOST = HOSTS_ROOT / "bay"
INBOX_HOST = HOSTS_ROOT / "inbox"  # thin legacy redirect host
LORE_INBOX = TRAYS_HOST / "librarian"
AGENT_INBOX = TRAYS_HOST / "agent"
CHARLIE_INBOX = TRAYS_HOST / "charlie"
TPS_INBOX = TRAYS_HOST / "tps"
CATALOG = {
    "librarian": {
        "house": "LIBRARIAN",
        "made": "Librarian",
        "inbox": LORE_INBOX,
        "serial": LORE_INBOX / "_serial.yaml",
        "suggest": LIBRARIAN / "_suggest.yaml",
        "tray": "librarian",
    },
    "agent": {
        "house": "AGENT",
        "made": "Agent",
        "inbox": AGENT_INBOX,
        "serial": AGENT_INBOX / "_serial.yaml",
        "suggest": AGENT_ROOT / "_suggest.yaml",
        "tray": "agent",
    },
    "charlie": {
        "house": "CHARLIE",
        "made": "Weaver",
        "inbox": CHARLIE_INBOX,
        "serial": CHARLIE_INBOX / "_serial.yaml",
        "suggest": CHARLIE_ROOT / "_suggest.yaml",
        "tray": "charlie",
        "blot": True,
    },
    "tps": {
        "house": "TPS",
        "made": "TPS event",
        "inbox": TPS_INBOX,
        "serial": TPS_INBOX / "_serial.yaml",
        "suggest": TPS_ROOT / "_suggest-lore.yaml",
        "tray": "tps",
    },
}


def catalog_dump(obj: dict) -> str:
    lines = [
        "house: " + yaml_scalar(str(obj.get("house") or "LIBRARIAN")),
        "pocket: " + yaml_scalar(str(obj.get("pocket") or "/")),
    ]
    crate = str(obj.get("crate") or "").strip()
    if crate:
        lines.append("crate: " + yaml_scalar(crate))
    fields = obj.get("fields") or []
    if not isinstance(fields, list) or not fields:
        lines.append("fields: []")
        return "\n".join(lines) + "\n"
    lines.append("fields:")
    for f in fields:
        if not isinstance(f, dict):
            continue
        kind = str(f.get("type") or "input").strip().lower()
        if kind not in FIELD_TYPES:
            kind = "input"
        lines.append("  - type: " + kind)
        lines.append("    label: " + yaml_scalar(str(f.get("label") or "")))
        val = f.get("value")
        if kind == "bool":
            lines.append("    value: " + ("true" if val in (True, "true", "1", 1) else "false"))
        elif kind == "time":
            try:
                lines.append("    value: " + str(int(val)))
            except (TypeError, ValueError):
                lines.append("    value: " + yaml_scalar(str(val or "")))
        else:
            lines.append("    value: " + yaml_scalar("" if val is None else str(val)))
    return "\n".join(lines) + "\n"


def empty_catalog(pocket: str, house: str = "LIBRARIAN") -> dict:
    return {
        "house": house or "LIBRARIAN",
        "pocket": pocket or "/",
        "crate": "",
        "fields": [],
        "lore": [],
    }


def catalog_load(text: str, house: str = "LIBRARIAN") -> dict:
    empty = empty_catalog("/", house)
    if not (text or "").strip():
        return empty
    pocket = "/"
    crate = ""
    fields: list[dict] = []
    cur: dict | None = None
    in_fields = False

    def finish() -> None:
        nonlocal cur
        if cur is not None:
            fields.append(cur)
            cur = None

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("thoughts:"):
            in_fields = False
            finish()
            continue
        if stripped.startswith("fields:"):
            in_fields = True
            finish()
            continue
        if raw_line.startswith("  - "):
            if not in_fields:
                continue
            finish()
            finish()
            cur = {"type": "input", "label": "", "value": ""}
            rest = raw_line[4:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                if k.strip() == "type":
                    t = v.strip().strip('"').strip("'").lower()
                    cur["type"] = t if t in FIELD_TYPES else "input"
            continue
        if ":" not in stripped:
            continue
        key, val = stripped.split(":", 1)
        key = key.strip()
        val = val.strip()
        if cur is None:
            if key == "house":
                house = val.strip('"').strip("'") or house
            elif key == "pocket":
                pocket = val.strip('"').strip("'") or "/"
            elif key == "crate":
                crate = val.strip('"').strip("'")
            continue
        if key == "type":
            t = val.strip('"').strip("'").lower()
            cur["type"] = t if t in FIELD_TYPES else "input"
        elif key == "label":
            cur["label"] = val.strip('"').strip("'")
        elif key == "value":
            kind = str(cur.get("type") or "input")
            raw = val.strip('"').strip("'")
            if kind == "bool":
                cur["value"] = raw.lower() in ("true", "1", "yes")
            elif kind == "time":
                try:
                    cur["value"] = int(raw)
                except ValueError:
                    cur["value"] = raw
            else:
                cur["value"] = raw
    finish()
    return {
        "house": house or "LIBRARIAN",
        "pocket": pocket or "/",
        "crate": crate,
        "fields": fields,
        "lore": [],
    }


def catalog_read(path: Path, pocket: str, house: str = "LIBRARIAN") -> dict:
    empty = empty_catalog(pocket, house)
    if not path.is_file():
        return empty
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return empty
    obj = catalog_load(text, house)
    obj["house"] = house or "LIBRARIAN"
    obj["pocket"] = pocket or obj.get("pocket") or "/"
    return obj


def catalog_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(catalog_dump(obj), encoding="utf-8")


def suggest_empty() -> dict[str, list[str]]:
    return {k: [] for k in (*FIELD_TYPES, "class")}


def suggest_load(path: Path | None = None) -> dict[str, list[str]]:
    out = suggest_empty()
    dest = path if path is not None else CATALOG["librarian"]["suggest"]
    if not dest.is_file():
        return out
    try:
        text = dest.read_text(encoding="utf-8")
    except OSError:
        return out
    cur = ""
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line and not line.startswith("-"):
            key, rest = line.split(":", 1)
            key = key.strip().lower()
            if key not in out:
                continue
            cur = key
            rest = rest.strip()
            if rest and rest != "[]":
                out[key] = parse_flow_list(rest)
            continue
        if line.startswith("-") and cur:
            word = line[1:].strip().strip('"').strip("'")
            if word and word not in out[cur]:
                out[cur].append(word)
    return out


def suggest_dump(obj: dict[str, list[str]]) -> str:
    lines = []
    for key in (*FIELD_TYPES, "class"):
        lines.append(key + ": " + yaml_str_list(obj.get(key) or []))
    return "\n".join(lines) + "\n"


def suggest_remember(mouth: str, kind: str, word: str) -> None:
    spec = CATALOG.get(mouth)
    kind = (kind or "").strip().lower()
    word = (word or "").strip()
    if not spec or kind not in (*FIELD_TYPES, "class") or not word:
        return
    dest = spec["suggest"]
    bank = suggest_load(dest)
    if word not in bank[kind]:
        bank[kind].append(word)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(suggest_dump(bank), encoding="utf-8")


def parse_librarian_time(raw: str) -> int | None:
    s = (raw or "").strip()
    if not s:
        return int(time.time())
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    iso = s.replace("Z", "+00:00")
    try:
        return int(datetime.fromisoformat(iso).timestamp())
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y",
        "%m/%d/%Y %H:%M",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
    ):
        try:
            return int(datetime.strptime(s, fmt).timestamp())
        except ValueError:
            continue
    return None


TPS_GRAINS = ("year", "month", "day", "clock")
TPS_GRAIN_SLICES = {
    "year": ("year",),
    "month": ("year", "month"),
    "day": ("year", "month", "day"),
    "clock": ("year", "month", "day", "hour", "clock"),
}
TPS_PARSE_MONTHS = {
    "january": 1,
    "february": 2,
    "febuary": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def tps_norm_grain(raw) -> str:
    g = str(raw or "").strip().lower()
    return g if g in TPS_GRAINS else "clock"


def tps_anchor(year: int, month: int = 1, day: int = 1, hour: int = 0, minute: int = 0) -> int:
    return int(datetime(int(year), int(month), int(day), int(hour), int(minute)).timestamp())


def parse_tps_time(raw: str) -> tuple[int, str] | None:
    s = (raw or "").strip()
    if not s:
        return None
    if re.fullmatch(r"-?\d+", s):
        n = int(s)
        if 1000 <= n <= 2999:
            return tps_anchor(n), "year"
        return n, "clock"
    iso = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(iso)
        grain = "clock" if ("T" in iso or ":" in s) else "day"
        return int(dt.timestamp()), grain
    except ValueError:
        pass
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", s)
    if m:
        try:
            return tps_anchor(int(m.group(1)), int(m.group(2))), "month"
        except ValueError:
            return None
    cleaned = re.sub(r"^[©ฉ]\s*", "", s)
    jam = re.fullmatch(
        r"(?i)(\d{4})\s*(january|february|febuary|march|april|may|june|july|august|september|october|november|december)",
        cleaned,
    )
    if jam:
        return tps_anchor(int(jam.group(1)), TPS_PARSE_MONTHS[jam.group(2).lower()]), "month"
    jam = re.fullmatch(
        r"(?i)(january|february|febuary|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
        cleaned,
    )
    if jam:
        return tps_anchor(int(jam.group(2)), TPS_PARSE_MONTHS[jam.group(1).lower()]), "month"
    dayish = re.fullmatch(
        r"(?i)(january|february|febuary|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
        cleaned,
    )
    if dayish:
        return (
            tps_anchor(int(dayish.group(3)), TPS_PARSE_MONTHS[dayish.group(1).lower()], int(dayish.group(2))),
            "day",
        )
    dayish = re.fullmatch(
        r"(?i)(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|febuary|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
        cleaned,
    )
    if dayish:
        return (
            tps_anchor(int(dayish.group(3)), TPS_PARSE_MONTHS[dayish.group(2).lower()], int(dayish.group(1))),
            "day",
        )
    dayish = re.fullmatch(
        r"(?i)(\d{4})\s+(jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec|january|february|febuary|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?",
        cleaned,
    )
    if dayish:
        return (
            tps_anchor(int(dayish.group(1)), TPS_PARSE_MONTHS[dayish.group(2).lower()], int(dayish.group(3))),
            "day",
        )
    for fmt, grain in (
        ("%Y-%m-%d %H:%M:%S", "clock"),
        ("%Y-%m-%d %H:%M", "clock"),
        ("%Y-%m-%dT%H:%M:%S", "clock"),
        ("%Y-%m-%dT%H:%M", "clock"),
        ("%Y-%m-%d", "day"),
        ("%m/%d/%Y %H:%M", "clock"),
        ("%m/%d/%Y", "day"),
        ("%d/%m/%Y %H:%M", "clock"),
        ("%d/%m/%Y", "day"),
        ("%B %Y", "month"),
        ("%b %Y", "month"),
        ("%Y %B", "month"),
        ("%Y %b", "month"),
        ("%B %d %Y", "day"),
        ("%b %d %Y", "day"),
        ("%d %B %Y", "day"),
        ("%d %b %Y", "day"),
        ("%Y %B %d", "day"),
        ("%Y %b %d", "day"),
    ):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return int(dt.timestamp()), grain
        except ValueError:
            continue
    return None


def tps_ordinal(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def tps_clock(stamp: datetime) -> str:
    hour = stamp.strftime("%I").lstrip("0") or "12"
    return hour + stamp.strftime(":%M").lower() + stamp.strftime("%p").lower()


def tps_hour(stamp: datetime) -> str:
    hour = stamp.strftime("%I").lstrip("0") or "12"
    return hour + stamp.strftime("%p").lower()


def tps_slices_of(at: int, grain: str = "clock") -> dict[str, str]:
    try:
        stamp = datetime.fromtimestamp(int(at))
    except (TypeError, ValueError, OSError):
        return {}
    grain = tps_norm_grain(grain)
    full = {
        "month": stamp.strftime("%B").lower(),
        "day": tps_ordinal(stamp.day),
        "year": str(stamp.year),
        "hour": tps_hour(stamp),
        "clock": tps_clock(stamp),
    }
    return {k: full[k] for k in TPS_GRAIN_SLICES[grain] if full.get(k)}


def tps_when(at: int, grain: str = "clock") -> str:
    try:
        stamp = datetime.fromtimestamp(int(at))
    except (TypeError, ValueError, OSError):
        return str(at)
    grain = tps_norm_grain(grain)
    if grain == "year":
        return str(stamp.year)
    if grain == "month":
        return stamp.strftime("%B %Y")
    if grain == "day":
        return stamp.strftime("%d %B %Y").lstrip("0")
    return stamp.strftime("%d %B %Y").lstrip("0") + ", " + tps_clock(stamp)


def tps_when_href(at: int, grain: str, slices: dict) -> str:
    grain = tps_norm_grain(grain)
    if grain == "clock":
        return tps_href("unix", str(at))
    filt = {}
    for kind in TPS_GRAIN_SLICES[grain]:
        word = str((slices or {}).get(kind) or "").strip()
        if word:
            filt[kind] = word
    return tps_href(filt) if filt else ""


def tps_title_slug(title: str) -> str:
    s = re.sub(r"\s+", "-", (title or "").strip().lower())
    s = re.sub(r"[^a-z0-9-]+", "", s).strip("-")
    return s[:48] or "date"


TPS_FILTER_KEYS = ("title", "month", "day", "year", "hour", "clock", "unix")
TPS_SORT_KEYS = ("when", "page", "environment", "path")


def tps_href(kind_or_filters=None, value: str = "", extra: dict | None = None, sort: str = "", order: str = "") -> str:
    if isinstance(kind_or_filters, dict):
        filt = dict(kind_or_filters)
    elif kind_or_filters:
        filt = {str(kind_or_filters): value}
    else:
        filt = {}
    if extra:
        for k, v in extra.items():
            if v:
                filt[k] = v
    parts = ["m=tps"]
    for k in TPS_FILTER_KEYS:
        val = str(filt.get(k) or "").strip()
        if val:
            parts.append(k + "=" + quote(val))
    sort = (sort or "").strip().lower()
    if sort in TPS_SORT_KEYS:
        parts.append("sort=" + quote(sort))
    order = (order or "").strip().lower()
    if order in ("asc", "desc"):
        parts.append("dir=" + quote(order))
    return "/?" + "&".join(parts)


def tps_filters_from_qs(qs: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    f = unquote((qs.get("f") or [""])[0]).strip().lower()
    v = unquote((qs.get("v") or [""])[0]).strip()
    if f in TPS_FILTER_KEYS and v:
        out[f] = v
    for k in TPS_FILTER_KEYS:
        val = unquote((qs.get(k) or [""])[0]).strip()
        if val:
            out[k] = val
    return out


def tps_qs_is_report(qs: dict) -> bool:
    mouth = unquote((qs.get("m") or [""])[0]).strip().lower()
    if mouth != "tps":
        return False
    if "f" in qs:
        return True
    return any(k in qs for k in TPS_FILTER_KEYS)


def catalog_from_qs(qs: dict) -> tuple[str, str, str, str]:
    mouth = unquote((qs.get("m") or ["librarian"])[0]).strip().lower() or "librarian"
    label = unquote((qs.get("f") or [""])[0]).strip()
    value = unquote((qs.get("v") or [""])[0]).strip()
    binning = unquote((qs.get("bin") or [""])[0]).strip().lower()
    return mouth, label, value, binning


def catalog_qs_is_report(qs: dict) -> bool:
    mouth, label, value, _binning = catalog_from_qs(qs)
    if mouth not in ("librarian", "agent"):
        return False
    return bool(label or value)


def tps_stamp_matches(
    filters: dict[str, str], title: str, at: int, slices: dict, grain: str = "clock"
) -> bool:
    grain = tps_norm_grain(grain)
    for kind, raw in (filters or {}).items():
        want = norm_chip(raw)
        if not want:
            continue
        if kind == "title":
            word = title
        elif kind == "unix":
            if grain != "clock":
                return False
            word = str(at)
        elif kind == "hour":
            word = str(slices.get("hour") or "")
        elif kind == "clock":
            clock = str(slices.get("clock") or "")
            hour = str(slices.get("hour") or "")
            if ":" not in want:
                word = hour
            else:
                word = clock
        else:
            word = str(slices.get(kind) or "")
        if not word or norm_chip(word) != want:
            return False
    return True


def tps_page_env(target: Path | None) -> str:
    if target is None:
        return ""
    page = target if target.is_file() else None
    if page is not None:
        env = env_name(str(read_md_meta(page).get("environment") or ""))
        if env:
            return env
    folder = nearest_index_folder(target)
    if folder is None:
        return ""
    shell = folder / INDEX_NAME
    if not shell.is_file():
        return ""
    return env_name(str(read_md_meta(shell).get("environment") or "")) or ""


def empty_tps(pocket: str) -> dict:
    return {
        "house": "TPS",
        "pocket": pocket or "/",
        "crate": "",
        "stamps": [],
        "slices": {
            "title": [],
            "month": [],
            "day": [],
            "year": [],
            "hour": [],
            "clock": [],
        },
        "titles": [],
    }


def tps_dump(obj: dict) -> str:
    lines = [
        "house: TPS",
        "pocket: " + yaml_scalar(str(obj.get("pocket") or "/")),
    ]
    crate = str(obj.get("crate") or "").strip()
    if crate:
        lines.append("crate: " + yaml_scalar(crate))
    stamps = obj.get("stamps") or []
    if not isinstance(stamps, list) or not stamps:
        lines.append("stamps: []")
        return "\n".join(lines) + "\n"
    lines.append("stamps:")
    for s in stamps:
        if not isinstance(s, dict):
            continue
        lines.append("  - id: " + yaml_scalar(str(s.get("id") or "")))
        lines.append("    title: " + yaml_scalar(str(s.get("title") or "")))
        try:
            lines.append("    at: " + str(int(s.get("at") or 0)))
        except (TypeError, ValueError):
            lines.append("    at: 0")
        grain = tps_norm_grain(s.get("grain"))
        if grain != "clock":
            lines.append("    grain: " + grain)
    return "\n".join(lines) + "\n"


def tps_stamp_apply(cur: dict, k: str, v: str) -> None:
    if k == "id":
        cur["id"] = v
    elif k == "title":
        cur["title"] = v
    elif k == "at":
        try:
            cur["at"] = int(v)
        except ValueError:
            cur["at"] = 0
    elif k == "grain":
        cur["grain"] = tps_norm_grain(v)


def tps_load(text: str, pocket: str) -> dict:
    obj = empty_tps(pocket)
    stamps: list[dict] = []
    cur: dict | None = None
    for raw_line in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and ":" in stripped:
            if cur:
                stamps.append(cur)
            cur = {"id": "", "title": "", "at": 0, "grain": "clock"}
            rest = stripped[2:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                tps_stamp_apply(cur, k.strip().lower(), v.strip().strip('"').strip("'"))
            continue
        if cur is not None and stripped.startswith(("id:", "title:", "at:", "grain:")):
            k, v = stripped.split(":", 1)
            tps_stamp_apply(cur, k.strip().lower(), v.strip().strip('"').strip("'"))
            continue
        if ":" in stripped and not stripped.startswith("-"):
            k, v = stripped.split(":", 1)
            k = k.strip().lower()
            v = v.strip().strip('"').strip("'")
            if k == "pocket" and v:
                obj["pocket"] = v
            elif k == "crate" and v:
                obj["crate"] = v
    if cur:
        stamps.append(cur)
    obj["stamps"] = [s for s in stamps if s.get("title") and s.get("at")]
    return obj


def tps_read(path: Path, pocket: str) -> dict:
    empty = empty_tps(pocket)
    if not path.is_file():
        return empty
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return empty
    obj = tps_load(text, pocket)
    obj["pocket"] = pocket or obj.get("pocket") or "/"
    return obj


def tps_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tps_dump(obj), encoding="utf-8")


def tps_stamp_view(raw: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None
    try:
        at = int(raw.get("at") or 0)
    except (TypeError, ValueError):
        return None
    title = str(raw.get("title") or "").strip()
    if not title or not at:
        return None
    grain = tps_norm_grain(raw.get("grain"))
    slices = tps_slices_of(at, grain)
    when_href = tps_when_href(at, grain, slices)
    return {
        "id": str(raw.get("id") or ""),
        "title": title,
        "at": at,
        "grain": grain,
        "when": tps_when(at, grain),
        "title_href": tps_href("title", title),
        "unix_href": tps_href("unix", str(at)) if grain == "clock" else "",
        "when_href": when_href,
        "slices": slices,
        "slice_chips": [
            {"kind": k, "value": v, "href": tps_href(k, v)}
            for k, v in slices.items()
            if v
        ],
    }


def tps_decorate_stamps(stamps: list) -> list[dict]:
    out = []
    for s in stamps:
        item = tps_stamp_view(s)
        if item:
            out.append(item)
    out.sort(key=lambda s: int(s.get("at") or 0))
    return out


TPS_MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)


def tps_bucket_key(kind: str, word: str):
    w = (word or "").strip().lower()
    if kind == "month":
        try:
            return (0, TPS_MONTHS.index(w), w)
        except ValueError:
            return (1, 0, w)
    if kind == "day":
        m = re.match(r"(\d+)", w)
        return (0, int(m.group(1)) if m else 0, w)
    if kind == "year":
        try:
            return (0, int(w), w)
        except ValueError:
            return (1, 0, w)
    if kind == "clock":
        m = re.match(r"(\d+):(\d+)\s*(am|pm)$", w)
        if m:
            hour = int(m.group(1))
            minute = int(m.group(2))
            ap = m.group(3)
            if ap == "pm" and hour != 12:
                hour += 12
            if ap == "am" and hour == 12:
                hour = 0
            return (0, hour * 60 + minute, w)
        return (1, 0, w)
    if kind == "hour":
        m = re.match(r"(\d+)\s*(am|pm)$", w)
        if m:
            hour = int(m.group(1))
            ap = m.group(2)
            if ap == "pm" and hour != 12:
                hour += 12
            if ap == "am" and hour == 12:
                hour = 0
            return (0, hour, w)
        return (1, 0, w)
    return (0, 0, w)


def tps_gather_slices(stamps: list[dict]) -> dict[str, list[dict]]:
    buckets = {"title": {}, "month": {}, "day": {}, "year": {}, "hour": {}, "clock": {}}
    for s in stamps:
        title = str(s.get("title") or "").strip()
        if title:
            buckets["title"][title] = buckets["title"].get(title, 0) + 1
        slices = s.get("slices") or {}
        for kind in ("month", "day", "year", "hour", "clock"):
            word = str(slices.get(kind) or "").strip()
            if not word:
                continue
            buckets[kind][word] = buckets[kind].get(word, 0) + 1
    out = {}
    for kind, counts in buckets.items():
        rows = [
            {"value": word, "n": n, "href": tps_href(kind, word)}
            for word, n in counts.items()
        ]
        rows.sort(key=lambda r: tps_bucket_key(kind, str(r["value"])))
        out[kind] = rows
    return out


def tps_payload(dest: Path, pocket: str, crate: str) -> dict:
    obj = tps_read(dest, pocket)
    if crate:
        obj["crate"] = crate
    stamps = tps_decorate_stamps(obj.get("stamps") or [])
    obj["stamps"] = stamps
    obj["slices"] = tps_gather_slices(stamps)
    seen = []
    for s in stamps:
        t = str(s.get("title") or "").strip()
        if t and t not in seen:
            seen.append(t)
    obj["titles"] = seen
    obj["lore"] = lore_cards_for("tps", crate or str(obj.get("crate") or ""))
    return obj


def tps_suggest_path() -> Path:
    return TPS_ROOT / "_suggest.yaml"


def tps_suggest_load() -> list[str]:
    out = list(TPS_TITLES)
    dest = tps_suggest_path()
    if not dest.is_file():
        return out
    try:
        text = dest.read_text(encoding="utf-8")
    except OSError:
        return out
    seen = {t.lower() for t in out}
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip().lstrip("-").strip().strip('"').strip("'")
        if not line or line.endswith(":") or line.startswith("#"):
            continue
        if line.lower() in seen:
            continue
        seen.add(line.lower())
        out.append(line)
    return out


def tps_suggest_remember(title: str) -> None:
    title = (title or "").strip()
    if not title:
        return
    have = tps_suggest_load()
    if any(h.lower() == title.lower() for h in have):
        return
    have.append(title)
    dest = tps_suggest_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = ["titles:"]
    for t in have:
        lines.append("- " + yaml_scalar(t))
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def tps_stamp_add(pocket_raw: str, title: str, raw_time: str) -> tuple[int, dict | None, str]:
    title = (title or "").strip()
    if not title:
        return 400, None, "need a title"
    raw_time = (raw_time or "").strip()
    if not raw_time:
        return 400, None, "need a time"
    parsed = parse_tps_time(raw_time)
    if parsed is None:
        return 400, None, "could not read time"
    at, grain = parsed
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        target = resolve_vault_page(pocket_raw)
        if target is None:
            return 400, None, "not a vault page"
        dest = shelf_file("tps", target)
        if dest is None:
            return 400, None, "not a vault page"
        pocket = pocket_key(shelf_anchor("tps", target))
        crate = bag_crate(shelf_anchor("tps", target))
        with LBR_LOCK:
            obj = tps_read(dest, pocket)
            stamps = list(obj.get("stamps") or [])
            stamp_id = tps_title_slug(title) + "-" + str(at)
            have = {str(s.get("id") or "") for s in stamps if isinstance(s, dict)}
            if stamp_id in have:
                stamp_id = stamp_id + "-" + str(len(stamps) + 1)
            stamps.append({"id": stamp_id, "title": title, "at": at, "grain": grain})
            obj["stamps"] = stamps
            if crate:
                obj["crate"] = crate
            obj["pocket"] = pocket
            tps_write(dest, obj)
            tps_suggest_remember(title)
            out = tps_payload(dest, pocket, crate)
        return 200, out, ""


def tps_stamp_delete(pocket_raw: str, stamp_id: str) -> tuple[int, dict | None, str]:
    stamp_id = (stamp_id or "").strip()
    if not stamp_id:
        return 400, None, "need an id"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        target = resolve_vault_page(pocket_raw)
        if target is None:
            return 400, None, "not a vault page"
        dest = shelf_file("tps", target)
        if dest is None:
            return 400, None, "not a vault page"
        pocket = pocket_key(shelf_anchor("tps", target))
        crate = bag_crate(shelf_anchor("tps", target))
        with LBR_LOCK:
            obj = tps_read(dest, pocket)
            stamps = [
                s
                for s in (obj.get("stamps") or [])
                if isinstance(s, dict) and str(s.get("id") or "") != stamp_id
            ]
            obj["stamps"] = stamps
            if crate:
                obj["crate"] = crate
            tps_write(dest, obj)
            out = tps_payload(dest, pocket, crate)
        return 200, out, ""


def tps_hits(filters: dict[str, str] | None = None, kind: str = "", value: str = "") -> list[dict]:
    filt = dict(filters or {})
    kind = (kind or "").strip().lower()
    if kind in TPS_FILTER_KEYS and value:
        filt.setdefault(kind, value)
    if any(k not in TPS_FILTER_KEYS for k in filt):
        filt = {k: v for k, v in filt.items() if k in TPS_FILTER_KEYS}
    root = TPS_ROOT
    if not root.is_dir():
        return []
    try:
        base = root.resolve()
    except OSError:
        return []
    out: list[dict] = []
    for path in root.rglob("*.yaml"):
        try:
            path.resolve().relative_to(base)
        except ValueError:
            continue
        if path.name.lower() == "_suggest.yaml":
            continue
        obj = tps_read(path, "")
        pocket = str(obj.get("pocket") or "").strip()
        if not pocket:
            continue
        matched: list[dict] = []
        for raw in obj.get("stamps") or []:
            view = tps_stamp_view(raw)
            if not view:
                continue
            if filt and not tps_stamp_matches(
                filt, view["title"], view["at"], view["slices"], view["grain"]
            ):
                continue
            matched.append(
                {
                    "stamp_title": view["title"],
                    "when": view["when"],
                    "at": view["at"],
                    "grain": view["grain"],
                    "title_href": view["title_href"],
                    "unix_href": view["unix_href"],
                    "when_href": view["when_href"],
                    "slices": view["slices"],
                }
            )
        if not matched:
            continue
        with using_pocket(pocket) as host:
            if host is None:
                continue
            target = resolve_vault_page(pocket)
            crate = bag_crate(target) if target is not None else str(obj.get("crate") or "")
            env = tps_page_env(target)
            page_name = pocket_title(pocket)
            href = href_from_pocket(pocket)
            for s in matched:
                row = dict(s)
                row.update(
                    {
                        "pocket": pocket,
                        "page": page_name,
                        "href": href,
                        "crate": crate,
                        "environment": env,
                    }
                )
                out.append(row)
    return out


def lore_slug(title: str) -> str:
    s = re.sub(r"\s+", "_", (title or "").strip())
    s = re.sub(r"[^\w\-]", "", s)
    s = s.strip("_-") or "lore"
    return s[:80]


def lore_next_n(mouth: str) -> int:
    spec = CATALOG[mouth]
    serial = spec["serial"]
    inbox = spec["inbox"]
    n = 1
    if serial.is_file():
        try:
            text = serial.read_text(encoding="utf-8")
        except OSError:
            text = ""
        for line in text.split("\n"):
            if line.strip().startswith("next:"):
                try:
                    n = int(line.split(":", 1)[1].strip())
                except ValueError:
                    n = 1
                break
    if n < 1:
        n = 1
    inbox.mkdir(parents=True, exist_ok=True)
    serial.write_text("next: " + str(n + 1) + "\n", encoding="utf-8")
    return n


def lore_href(tray: str, filename: str) -> str:
    return "/?h=trays&p=" + quote(tray + "/" + filename, safe="/")


def lore_edge_crates(meta: dict) -> list[str]:
    """Crates this card touches. Born-on first, then edges."""
    out: list[str] = []
    seen: set[str] = set()

    def add(raw: object) -> None:
        c = norm_crate(str(raw or ""))
        if c and c not in seen:
            out.append(c)
            seen.add(c)

    add(meta.get("source_crate"))
    raw = meta.get("edges")
    items = raw if isinstance(raw, list) else parse_flow_list(str(raw or ""))
    for x in items:
        add(x)
    return out


def door_for_path(p: Path | None) -> dict | None:
    """Title + go.* door for a note path. None if it is not under a host."""
    if p is None or not p.is_file():
        return None
    title = md_list_label(p)
    crate = str(file_crate(p) or "").strip()
    try:
        here = p.resolve()
    except OSError:
        return None
    start = HOSTS_ROOT / START_NAME
    if start.is_file():
        try:
            if here == start.resolve():
                return {
                    "crate": crate,
                    "title": title,
                    "pocket": "/",
                    "href": "/",
                    "path": p,
                }
        except OSError:
            pass
    for name, host in discover_hosts().items():
        try:
            rel = here.relative_to(host.root.resolve()).as_posix()
        except (OSError, ValueError):
            continue
        pocket = "go." + name + "/" + rel
        return {
            "crate": crate,
            "title": title,
            "pocket": pocket,
            "href": href_from_pocket(pocket),
            "path": p,
        }
    return None


def door_for_crate(crate: str) -> dict | None:
    """Title + go.* door for a page crate. None if the crate is not on a note."""
    crate = norm_crate(crate)
    if not crate:
        return None
    door = door_for_path(find_file_by_crate(crate))
    if door is None:
        return None
    door["crate"] = crate
    return door


def paint_lore_edges(meta: dict) -> str:
    crates = lore_edge_crates(meta)
    if not crates:
        return ""
    born = norm_crate(str(meta.get("source_crate") or ""))
    items: list[str] = []
    for c in crates:
        door = door_for_crate(c)
        mark = " is-born" if c == born else ""
        if door is None:
            items.append(
                "<li class=\"lore-edge"
                + mark
                + '"><code>'
                + html.escape(c)
                + "</code></li>"
            )
            continue
        items.append(
            "<li class=\"lore-edge"
            + mark
            + '"><a href="'
            + html.escape(str(door["href"]), True)
            + '">'
            + html.escape(str(door["title"]))
            + "</a><code>"
            + html.escape(c)
            + "</code></li>"
        )
    return '<ul class="lore-edges">' + "".join(items) + "</ul>"


def apply_lore_edges_fm(text: str, crates: list[str]) -> str:
    raw = text.replace("\r\n", "\n")
    line = "edges: " + yaml_str_list(crates)
    if not raw.startswith("---\n"):
        return "---\n" + line + "\n---\n\n" + raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return raw
    head = raw[4:end]
    rest = raw[end + 5 :]
    lines = head.split("\n")
    found = False
    new_lines: list[str] = []
    for row in lines:
        if row.startswith("edges:"):
            found = True
            new_lines.append(line)
        else:
            new_lines.append(row)
    if not found:
        inserted = False
        out: list[str] = []
        for row in new_lines:
            out.append(row)
            if row.startswith("source_crate:"):
                out.append(line)
                inserted = True
        if not inserted:
            out.insert(0, line)
        new_lines = out
    return "---\n" + "\n".join(new_lines) + "\n---\n" + rest


def find_lore_file(mouth: str, card_crate: str) -> Path | None:
    spec = CATALOG.get(mouth)
    want = norm_crate(card_crate)
    if not spec or not want:
        return None
    inbox = spec["inbox"]
    if not inbox.is_dir():
        return None
    for p in inbox.glob("*.md"):
        if p.name.lower() in {INDEX_NAME, PAPER_NAME}:
            continue
        if norm_crate(file_crate(p)) == want:
            return p
    return None


def lore_cards_for(mouth: str, crate: str) -> list[dict]:
    spec = CATALOG.get(mouth)
    crate = (crate or "").strip()
    if not spec or not crate:
        return []
    inbox = spec["inbox"]
    if not inbox.is_dir():
        return []
    tray = spec["tray"]
    out: list[dict] = []
    for p in sorted(inbox.glob("*.md"), key=lambda x: x.name.lower()):
        if p.name.lower() in {INDEX_NAME, PAPER_NAME}:
            continue
        meta = read_md_meta(p)
        own = str(meta.get("crate") or "").strip()
        touches = lore_edge_crates(meta)
        if crate not in touches and own != crate:
            continue
        born = norm_crate(str(meta.get("source_crate") or ""))
        out.append(
            {
                "title": str(meta.get("title") or p.stem).strip() or p.stem,
                "class": str(meta.get("class") or "").strip(),
                "house": str(meta.get("house") or spec["house"]).strip(),
                "maker": card_maker(meta, house=str(meta.get("house") or spec["house"]).strip()),
                "tps": str(meta.get("tps") or "").strip(),
                "file": p.name,
                "href": lore_href(tray, p.name),
                "crate": str(meta.get("crate") or "").strip(),
                "line": str(meta.get("line") or "").strip(),
                "source_crate": born,
                "edges": touches,
                "born": born == crate,
            }
        )
    return out


LORE_HOUSES = {"librarian": "librarian", "agent": "agent", "charlie": "charlie"}


def lore_house_label(house: str = "", mouth: str = "") -> str:
    h = (house or "").strip().lower()
    if h in LORE_HOUSES:
        return h
    m = (mouth or "").strip().lower()
    if m in LORE_HOUSES:
        return m
    spec = CATALOG.get(m)
    if spec:
        return str(spec.get("house") or m).strip().lower()
    return h


def is_lore_card(meta: dict | None) -> bool:
    if not meta:
        return False
    env = (env_name(str(meta.get("environment") or "")) or "").lower()
    if env == "lorecard":
        return True
    klass = str(meta.get("class") or "").strip()
    house = lore_house_label(str(meta.get("house") or ""))
    return bool(klass and house in LORE_HOUSES)


def is_card_note(meta: dict | None) -> bool:
    """A filed card, not the trays home's own lorecard skin."""
    if not is_lore_card(meta):
        return False
    blob = (
        str((meta or {}).get("class") or "")
        + str((meta or {}).get("line") or "")
        + str((meta or {}).get("source_crate") or "")
    )
    return bool(blob.strip())


def card_chrome(meta: dict | None) -> str:
    """Window sense: deck/type, then the card's title."""
    meta = meta or {}
    klass = str(meta.get("class") or "").strip() or "lore card"
    title = str(meta.get("title") or "").strip()
    if not title:
        return klass
    if klass.lower() == title.lower():
        return title
    return f"{klass} · {title}"


def css_color_to_hex(raw: str) -> str:
    s = str(raw or "").strip()
    if HEX_COLOR.fullmatch(s):
        return s
    m = CSS_RGB.fullmatch(s)
    if m:
        return "#{:02x}{:02x}{:02x}".format(
            int(m.group(1)), int(m.group(2)), int(m.group(3))
        )
    return ""


def _css_root_block(text: str) -> str:
    m = CSS_ROOT.search(text or "")
    if not m:
        return ""
    i = m.end() - 1
    depth = 0
    for j, ch in enumerate(text[i:], i):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1 : j]
    return ""


def _style_vars(path: Path, depth: int = 0) -> dict[str, str]:
    if depth > 3 or not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    out: dict[str, str] = {}
    for imp in CSS_IMPORT.findall(text):
        name = Path(str(imp).split("?")[0]).name
        if not name.lower().endswith(".css"):
            continue
        other = path.parent / name
        if other.is_file():
            for k, v in _style_vars(other, depth + 1).items():
                out.setdefault(k, v)
    for m in CSS_DECL.finditer(_css_root_block(text)):
        out[m.group(1).lower()] = m.group(2).strip()
    return out


def style_file_for(name: str) -> Path | None:
    want = (name or "").strip().lower() + ".css"
    if not want or want == ".css" or not STYLES.is_dir():
        return None
    direct = STYLES / want
    if direct.is_file():
        return direct
    for p in STYLES.iterdir():
        if p.is_file() and p.name.lower() == want:
            return p
    return None


def env_css_strip(env: str) -> str:
    """Hex from the room skin: --strip, then --card-strip, then --accent, then --stamp."""
    key = (env_name(env) or "").lower()
    if not key or key == "lorecard":
        return ""
    if key in _ENV_CSS_STRIP:
        return _ENV_CSS_STRIP[key]
    path = style_file_for(key)
    got = ""
    if path is not None:
        vars_map = _style_vars(path)

        def resolve(raw: str, hops: int = 0) -> str:
            raw = str(raw or "").strip()
            hexv = css_color_to_hex(raw)
            if hexv:
                return hexv
            if hops > 4:
                return ""
            m = CSS_VAR.match(raw)
            if not m:
                return ""
            return resolve(vars_map.get(m.group(1).lower(), ""), hops + 1)

        for token in ("strip", "card-strip", "accent", "stamp"):
            got = resolve(vars_map.get(token, ""))
            if got:
                break
    _ENV_CSS_STRIP[key] = got
    return got


def env_strip(env: str) -> str:
    key = (env_name(env) or "").lower()
    if not key or key == "lorecard":
        return ""
    return env_css_strip(key) or ENV_STRIP.get(key, "")


def meta_strip_hex(meta: dict | None) -> str:
    """YAML strip: or color: — a #hex, or a named hue."""
    meta = meta or {}
    for key in ("strip", "color"):
        raw = str(meta.get(key) or "").strip()
        if not raw:
            continue
        hexv = css_color_to_hex(raw)
        if hexv:
            return hexv
        low = raw.lower()
        if low in COLORS:
            return COLORS[low]
        for name in COLORS:
            if name in low.split():
                return COLORS[name]
    return ""


def room_strip_for_page(path: Path | None) -> str:
    """Hall this page sits in: environment CSS, then that room's YAML hex."""
    if path is None:
        return ""
    try:
        here = path if path.is_file() else path
    except OSError:
        here = path
    meta = read_md_meta(here) if here.is_file() else {}
    got = env_strip(str(meta.get("environment") or ""))
    if got:
        return got
    room = nearest_index_folder(here)
    if room is not None:
        for fname in (INDEX_NAME, PAPER_NAME):
            rm = read_md_meta(room / fname)
            got = env_strip(str(rm.get("environment") or ""))
            if got:
                return got
            got = meta_strip_hex(rm)
            if got:
                return got
    return meta_strip_hex(meta)


def card_strip_color(meta: dict | None, *, hop: bool = True) -> str:
    """This card's strip:/color:, else the born-on room's skin accent, else house."""
    meta = meta or {}
    own = meta_strip_hex(meta)
    if own:
        return own
    got = env_strip(str(meta.get("environment") or ""))
    if got:
        return got
    if hop:
        src = find_file_by_crate(str(meta.get("source_crate") or ""))
        if src is not None:
            got = room_strip_for_page(src)
            if got:
                return got
    house = lore_house_label(str(meta.get("house") or ""))
    if house in HOUSE_STRIP:
        return HOUSE_STRIP[house]
    return "#c45c4a" if hop else ""


def stamp_lorecard_strip(inner: str, meta: dict | None) -> str:
    """Put --card-strip on the .lorecard so own page, pop, and faces share one hue."""
    strip = css_hex(card_strip_color(meta)) if is_card_note(meta) else ""
    if not strip or "--card-strip:" in inner:
        return inner
    bit = f' style="--card-strip:{strip}"'
    for old in (
        'class="lorecard has-back"',
        'class="lorecard"',
        "class='lorecard has-back'",
        "class='lorecard'",
    ):
        if old in inner:
            return inner.replace(old, old + bit, 1)
    return inner


def lore_facts(meta: dict | None, path: Path | None = None) -> dict:
    meta = meta or {}
    title = str(meta.get("title") or "").strip()
    if not title and path is not None:
        title = md_list_label(path)
    return {
        "class": str(meta.get("class") or "").strip(),
        "title": title,
        "house": lore_house_label(str(meta.get("house") or "")),
        "made": str(meta.get("made") or "").strip(),
        "line": str(meta.get("line") or "").strip(),
        "from": str(meta.get("from") or "").strip(),
        "from_href": str(meta.get("from_href") or "").strip(),
        "source_crate": norm_crate(str(meta.get("source_crate") or "")),
        "crate": norm_crate(str(meta.get("crate") or "")),
    }


def lore_facts_for_path(p: Path | None) -> dict | None:
    if p is None or not p.is_file():
        return None
    meta = read_md_meta(p)
    if not is_lore_card(meta):
        return None
    return lore_facts(meta, p)



def catalog_onto_bag(mouth: str, target: Path, onto: str = "") -> tuple[Path | None, Path, str, str]:
    """dest, anchor, pocket, crate. onto=shell uses the nearest _index bag."""
    want = (onto or "page").strip().lower()
    if want in {"shell", "room", "index"}:
        folder = nearest_index_folder(target)
        if folder is not None:
            dest = shelf_file(mouth, folder)
            return dest, folder, pocket_key(folder), bag_crate(folder)
    dest = shelf_file(mouth, target)
    anchor = shelf_anchor(mouth, target)
    return dest, anchor, pocket_key(anchor), bag_crate(anchor)


def catalog_shell_of(mouth: str, target: Path, page_dest: Path) -> dict | None:
    """Nearest _index catalog, when it is a different yaml than this page."""
    folder = nearest_index_folder(target)
    if folder is None:
        return None
    dest = shelf_file(mouth, folder)
    if dest is None:
        return None
    try:
        if dest.resolve() == page_dest.resolve():
            return None
    except OSError:
        return None
    pocket = pocket_key(folder)
    crate = bag_crate(folder)
    obj = catalog_payload(mouth, dest, pocket, crate)
    obj["onto"] = "shell"
    obj["route"] = pocket_key(folder)
    return obj


def catalog_view(mouth: str, target: Path) -> dict | None:
    dest = shelf_file(mouth, target)
    if dest is None:
        return None
    anchor = shelf_anchor(mouth, target)
    pocket = pocket_key(anchor)
    crate = bag_crate(anchor)
    obj = catalog_payload(mouth, dest, pocket, crate)
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    shell = catalog_shell_of(mouth, target, dest)
    if shell is not None:
        obj["shell"] = shell
    return obj


def catalog_payload(mouth: str, dest: Path, pocket: str, crate: str) -> dict:
    spec = CATALOG[mouth]
    obj = catalog_read(dest, pocket, spec["house"])
    if crate:
        obj["crate"] = crate
    obj["lore"] = lore_cards_for(mouth, crate or str(obj.get("crate") or ""))
    fields = []
    raw = obj.get("fields") or []
    for i, f in enumerate(raw):
        if not isinstance(f, dict):
            continue
        item = dict(f)
        label = str(item.get("label") or "").strip()
        item["i"] = i
        item["label_href"] = catalog_field_href(mouth, label)
        item["chips"] = [
            {"value": v, "href": value_door_href(mouth, label, v)}
            for v in chip_values(item)
        ]
        fields.append(item)
    obj["fields"] = fields
    return obj


def catalog_coerce_value(kind: str, value) -> tuple[int, object | None, str]:
    if kind == "bool":
        return 200, value in (True, "true", "1", 1, "yes", "on"), ""
    if kind == "time":
        tps = parse_librarian_time("" if value is None else str(value))
        if tps is None:
            return 400, None, "could not read time"
        return 200, tps, ""
    stored = "" if value is None else str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if kind == "textbox" and len(str(stored)) > LEAF_MAX:
        return 413, None, "value too long"
    if kind == "input" and len(str(stored)) > 500:
        return 413, None, "value too long"
    return 200, stored, ""


def catalog_field_index(raw) -> int | None:
    try:
        i = int(raw)
    except (TypeError, ValueError):
        return None
    if i < 0:
        return None
    return i


def catalog_field_add(
    mouth: str, pocket_raw: str, kind: str, label: str, value, onto: str = ""
) -> tuple[int, dict | None, str]:
    if mouth not in CATALOG:
        return 400, None, "no such catalog"
    kind = (kind or "").strip().lower()
    label = (label or "").strip()
    if kind not in FIELD_TYPES:
        return 400, None, "no such type"
    if not label:
        return 400, None, "empty label"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _catalog_field_add(mouth, pocket_raw, kind, label, value, onto)


def _catalog_field_add(
    mouth: str, pocket_raw: str, kind: str, label: str, value, onto: str = ""
) -> tuple[int, dict | None, str]:
    spec = CATALOG[mouth]
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest, anchor, pocket, crate = catalog_onto_bag(mouth, target, onto)
    if dest is None:
        return 400, None, "not a vault page"
    code, stored, err = catalog_coerce_value(kind, value)
    if stored is None:
        return code, None, err
    with LBR_LOCK:
        obj = catalog_read(dest, pocket, spec["house"])
        fields = list(obj.get("fields") or [])
        fields.append({"type": kind, "label": label, "value": stored})
        obj["fields"] = fields
        obj["pocket"] = pocket
        obj["house"] = spec["house"]
        if crate:
            obj["crate"] = crate
        catalog_write(dest, obj)
        suggest_remember(mouth, kind, label)
    obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
    return 200, obj, ""


def catalog_field_update(
    mouth: str, pocket_raw: str, index: int, kind: str, label: str, value, onto: str = ""
) -> tuple[int, dict | None, str]:
    if mouth not in CATALOG:
        return 400, None, "no such catalog"
    kind = (kind or "").strip().lower()
    label = (label or "").strip()
    if kind not in FIELD_TYPES:
        return 400, None, "no such type"
    if not label:
        return 400, None, "empty label"
    if catalog_field_index(index) is None:
        return 400, None, "no such field"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _catalog_field_update(mouth, pocket_raw, int(index), kind, label, value, onto)


def _catalog_field_update(
    mouth: str, pocket_raw: str, index: int, kind: str, label: str, value, onto: str = ""
) -> tuple[int, dict | None, str]:
    spec = CATALOG[mouth]
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest, anchor, pocket, crate = catalog_onto_bag(mouth, target, onto)
    if dest is None:
        return 400, None, "not a vault page"
    code, stored, err = catalog_coerce_value(kind, value)
    if stored is None:
        return code, None, err
    with LBR_LOCK:
        obj = catalog_read(dest, pocket, spec["house"])
        fields = list(obj.get("fields") or [])
        if index >= len(fields):
            return 404, None, "no such field"
        fields[index] = {"type": kind, "label": label, "value": stored}
        obj["fields"] = fields
        obj["pocket"] = pocket
        obj["house"] = spec["house"]
        if crate:
            obj["crate"] = crate
        catalog_write(dest, obj)
        suggest_remember(mouth, kind, label)
    obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
    return 200, obj, ""


def catalog_field_delete(
    mouth: str, pocket_raw: str, index: int, onto: str = ""
) -> tuple[int, dict | None, str]:
    if mouth not in CATALOG:
        return 400, None, "no such catalog"
    if catalog_field_index(index) is None:
        return 400, None, "no such field"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _catalog_field_delete(mouth, pocket_raw, int(index), onto)


def _catalog_field_delete(
    mouth: str, pocket_raw: str, index: int, onto: str = ""
) -> tuple[int, dict | None, str]:
    spec = CATALOG[mouth]
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest, anchor, pocket, crate = catalog_onto_bag(mouth, target, onto)
    if dest is None:
        return 400, None, "not a vault page"
    with LBR_LOCK:
        obj = catalog_read(dest, pocket, spec["house"])
        fields = list(obj.get("fields") or [])
        if index >= len(fields):
            return 404, None, "no such field"
        fields.pop(index)
        obj["fields"] = fields
        obj["pocket"] = pocket
        obj["house"] = spec["house"]
        if crate:
            obj["crate"] = crate
        catalog_write(dest, obj)
    obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
    return 200, obj, ""


def catalog_lore_add(
    mouth: str, pocket_raw: str, klass: str, title: str, line: str, when: str, onto: str = "", maker: str = ""
) -> tuple[int, dict | None, str]:
    if mouth not in CATALOG:
        return 400, None, "no such catalog"
    klass = (klass or "").strip()
    title = (title or "").strip()
    line = (line or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not title:
        return 400, None, "empty title"
    if not line:
        return 400, None, "empty lore"
    if len(line) > LORE_LINE_MAX:
        return 413, None, "lore too long"
    tps = parse_librarian_time(when)
    if tps is None:
        return 400, None, "could not read time"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _catalog_lore_add(mouth, pocket_raw, klass, title, line, tps, onto, maker)


LORE_CARD_LAYOUT = """
{{div:lorecard}}

{{.kicker}}{{class}}

{{.house}}{{maker}}

# {{title}}

{{.line}}{{line}}

{{.id}}{{crate}}

{{/div}}
""".lstrip("\n")


def lore_from_room(target: Path | None) -> str:
    """Geography the card carries: host plus nearest _index. No filename."""
    if target is None:
        return ""
    host = host_for_path(target)
    ctx = using_host(host) if host is not None else using_host(None)
    with ctx:
        try:
            here = target
            if here.is_file():
                here = here.parent
        except OSError:
            return ""
        room = nearest_index_folder(target)
        if room is not None:
            here = room
        key = pocket_key(here).replace("\\", "/").rstrip("/")
        return key



def card_maker(meta: dict | None = None, house: str = "", mouth: str = "", maker: str = "") -> str:
    """Corner identity. Explicit maker wins; else the filing house."""
    explicit = (maker or "").strip() or str((meta or {}).get("maker") or "").strip()
    if explicit:
        return explicit
    return lore_maker_shown(
        house or str((meta or {}).get("house") or ""),
        mouth,
    )


def lore_card_md(
    *,
    crate: str,
    source_crate: str,
    title: str,
    klass: str,
    line: str,
    tps: int,
    from_label: str,
    house: str,
    maker: str = "",
    edges: list[str] | None = None,
) -> str:
    """Face in the body. Crate ids and room on the back. No path snapshots."""
    seen: set[str] = set()
    crates: list[str] = []
    born = norm_crate(source_crate)
    raw_list = list(edges) if edges is not None else ([source_crate] if source_crate else [])
    for raw in raw_list:
        c = norm_crate(raw)
        if c and c not in seen:
            seen.add(c)
            crates.append(c)
    if born:
        crates = [born] + [c for c in crates if c != born]
    return (
        "---\n"
        "crate: " + crate + "\n"
        "source_crate: " + source_crate + "\n"
        "edges: " + yaml_str_list(crates) + "\n"
        "title: " + yaml_scalar(title) + "\n"
        "class: " + yaml_scalar(klass) + "\n"
        "line: " + yaml_scalar(line) + "\n"
        "tps: " + str(tps) + "\n"
        "house: " + yaml_scalar(house) + "\n"
        "maker: " + yaml_scalar(card_maker(house=house, maker=maker)) + "\n"
        "from: " + yaml_scalar(from_label) + "\n"
        "environment: lorecard\n"
        "---\n\n"
        + LORE_CARD_LAYOUT
    )


LORE_LIBRARIAN_AUTHOR = {
    "librarian": "The Librarian",
    "agent": "Agent",
    "charlie": "Charlie",
}


def lore_card_stamp_librarian(
    path: Path, mouth: str, klass: str, crate: str
) -> None:
    """File class / author / card type on the new card's Librarian sidecar.

    Ordinary catalog fields so the Librarian drawer shows them. Never overwrite
    a label that is already live.
    """
    spec = CATALOG.get(mouth) or CATALOG["librarian"]
    tray = spec.get("tray") or "librarian"
    pocket = "go.trays/" + tray + "/" + path.name
    author = LORE_LIBRARIAN_AUTHOR.get((mouth or "").strip().lower()) or (
        lore_maker_shown(str(spec.get("house") or mouth)) or "Librarian"
    )
    klass = (klass or "").strip()
    with using_pocket(pocket) as host:
        if host is None:
            return
        dest = shelf_file("librarian", path)
        if dest is None:
            return
        obj = catalog_read(dest, pocket, "LIBRARIAN")
        have = {
            norm_chip(str(f.get("label") or ""))
            for f in (obj.get("fields") or [])
            if isinstance(f, dict)
        }
        fields = list(obj.get("fields") or [])
        added = False
        for label, value in (
            ("class", "lore card"),
            ("author", author),
            ("card type", klass),
        ):
            if not value or norm_chip(label) in have:
                continue
            fields.append({"type": "input", "label": label, "value": value})
            have.add(norm_chip(label))
            added = True
            suggest_remember("librarian", "input", label)
        if not added and str(obj.get("crate") or "").strip() == (crate or "").strip():
            return
        obj["fields"] = fields
        obj["pocket"] = pocket
        obj["house"] = "LIBRARIAN"
        if crate:
            obj["crate"] = crate
        catalog_write(dest, obj)


def lore_cards_stamp_librarian_missing() -> None:
    """One-shot: stamp Librarian fields onto lore cards that do not have them yet."""
    with LBR_LOCK:
        for mouth, spec in CATALOG.items():
            inbox = spec.get("inbox")
            if inbox is None or not inbox.is_dir():
                continue
            for p in sorted(inbox.glob("*.md"), key=lambda x: x.name.lower()):
                if p.name.lower() in {INDEX_NAME, PAPER_NAME}:
                    continue
                meta = read_md_meta(p)
                if not is_lore_card(meta):
                    continue
                klass = str(meta.get("class") or "").strip()
                crate = str(meta.get("crate") or "").strip()
                lore_card_stamp_librarian(p, mouth, klass, crate)


def _catalog_lore_add(
    mouth: str, pocket_raw: str, klass: str, title: str, line: str, tps: int, onto: str = "", maker: str = ""
) -> tuple[int, dict | None, str]:
    spec = CATALOG[mouth]
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest, anchor, pocket, crate = catalog_onto_bag(mouth, target, onto)
    if dest is None:
        return 400, None, "not a vault page"
    if not crate:
        dest_md = crate_file_for(anchor)
        if dest_md is not None:
            crate = ensure_crate(dest_md)
    if not crate:
        return 400, None, "no crate on this page"
    from_label = lore_from_room(target)
    slug = lore_slug(title)
    inbox = spec["inbox"]
    tray = spec["tray"]
    maker = (maker or "").strip() or str(spec.get("made") or "").strip()
    with LBR_LOCK:
        n = lore_next_n(mouth)
        fname = f"{slug}-LORE_{n}.md"
        path = inbox / fname
        if path.exists():
            fname = f"{slug}-LORE_{n}-{os.urandom(2).hex()}.md"
            path = inbox / fname
        own = mint_crate_id()
        body = lore_card_md(
            crate=own,
            source_crate=crate,
            title=title,
            klass=klass,
            line=line,
            tps=tps,
            from_label=from_label,
            house=spec["house"],
            maker=maker,
        )
        inbox.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        lore_card_stamp_librarian(path, mouth, klass, own)
        suggest_remember(mouth, "class", klass)
        if spec.get("blot"):
            obj = blot_read(dest, pocket, spec["house"])
            if crate:
                obj["crate"] = crate
            if mouth == "charlie":
                charlie_normalize(obj)
                charlie_decorate(obj, pocket)
            obj["lore"] = lore_cards_for(mouth, crate)
        else:
            obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
    tps_stamp_add("go.trays/" + tray + "/" + fname, "created", str(tps))
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    obj["href"] = lore_href(tray, fname)
    obj["file"] = fname
    return 200, obj, ""


def lore_mouth_blot(
    mouth: str, dest: Path, pocket: str, crate: str, target: Path
) -> dict:
    spec = CATALOG[mouth]
    if spec.get("blot"):
        obj = blot_read(dest, pocket, spec["house"])
        if crate:
            obj["crate"] = crate
        if mouth == "charlie":
            charlie_normalize(obj)
            charlie_decorate(obj, pocket)
        obj["lore"] = lore_cards_for(mouth, crate)
    else:
        obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
        obj["route"] = pocket_key(nearest_index_folder(target) or target)
        return obj
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    return obj


def lore_card_amend_card_type(path: Path, mouth: str, klass: str) -> None:
    """Keep Librarian `card type` in step with the deck. Does not touch crate."""
    klass = (klass or "").strip()
    spec = CATALOG.get(mouth) or CATALOG["librarian"]
    tray = spec.get("tray") or "librarian"
    pocket = "go.trays/" + tray + "/" + path.name
    with using_pocket(pocket) as host:
        if host is None:
            return
        dest = shelf_file("librarian", path)
        if dest is None:
            return
        obj = catalog_read(dest, pocket, "LIBRARIAN")
        fields = list(obj.get("fields") or [])
        want = norm_chip("card type")
        found = False
        for f in fields:
            if not isinstance(f, dict):
                continue
            if norm_chip(str(f.get("label") or "")) != want:
                continue
            found = True
            if klass:
                f["value"] = klass
        if not found and klass:
            fields.append({"type": "input", "label": "card type", "value": klass})
        obj["fields"] = fields
        catalog_write(dest, obj)


def catalog_lore_update(
    mouth: str,
    pocket_raw: str,
    card_crate: str,
    klass: str,
    title: str,
    line: str,
    when: str,
    maker: str = "",
) -> tuple[int, dict | None, str]:
    if mouth not in CATALOG:
        return 400, None, "no such catalog"
    card_crate = norm_crate(card_crate)
    if not card_crate:
        return 400, None, "need a lore crate"
    klass = (klass or "").strip()
    title = (title or "").strip()
    line = (line or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not title:
        return 400, None, "empty title"
    if not line:
        return 400, None, "empty lore"
    if len(line) > LORE_LINE_MAX:
        return 413, None, "lore too long"
    when = (when or "").strip()
    tps = None
    if when:
        tps = parse_librarian_time(when)
        if tps is None:
            return 400, None, "could not read time"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _catalog_lore_update(
            mouth, pocket_raw, card_crate, klass, title, line, tps, maker
        )


def _catalog_lore_update(
    mouth: str,
    pocket_raw: str,
    card_crate: str,
    klass: str,
    title: str,
    line: str,
    tps: int | None,
    maker: str = "",
) -> tuple[int, dict | None, str]:
    spec = CATALOG[mouth]
    path = find_lore_file(mouth, card_crate)
    if path is None or not path.is_file():
        return 404, None, "no such lore"
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = shelf_file(mouth, target)
    if dest is None:
        return 400, None, "not a vault page"
    anchor = shelf_anchor(mouth, target)
    pocket = pocket_key(anchor)
    crate = bag_crate(anchor)
    with LBR_LOCK:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return 500, None, "could not read lore"
        live = str(parse_fm(text)[0].get("crate") or "").strip()
        if live and norm_crate(live) != card_crate:
            return 400, None, "crate mismatch"
        who = card_maker(house=spec["house"], maker=maker)
        updates = {
            "title": yaml_scalar(title),
            "class": yaml_scalar(klass),
            "line": yaml_scalar(line),
            "maker": yaml_scalar(who),
        }
        if tps is not None:
            updates["tps"] = str(tps)
        out = patch_fm_keys(text, updates)
        if live:
            out = force_crate_line(out, live)
        if not out.endswith("\n"):
            out += "\n"
        try:
            path.write_text(out, encoding="utf-8")
        except OSError:
            return 500, None, "could not write lore"
        lore_card_amend_card_type(path, mouth, klass)
        suggest_remember(mouth, "class", klass)
        obj = lore_mouth_blot(mouth, dest, pocket, crate, target)
    obj["href"] = lore_href(spec["tray"], path.name)
    obj["file"] = path.name
    return 200, obj, ""


def catalog_lore_list(mouth: str) -> tuple[int, dict | None, str]:
    spec = CATALOG.get(mouth)
    if not spec:
        return 400, None, "no such catalog"
    inbox = spec["inbox"]
    tray = spec["tray"]
    cards: list[dict] = []
    if inbox.is_dir():
        for p in sorted(inbox.glob("*.md"), key=lambda x: x.name.lower()):
            if p.name.lower() in {INDEX_NAME, PAPER_NAME}:
                continue
            meta = read_md_meta(p)
            own = str(meta.get("crate") or "").strip()
            if not own:
                continue
            cards.append(
                {
                    "title": str(meta.get("title") or p.stem).strip() or p.stem,
                    "class": str(meta.get("class") or "").strip(),
                    "maker": card_maker(meta, house=str(meta.get("house") or spec["house"]).strip()),
                    "house": str(meta.get("house") or spec["house"]).strip(),
                    "line": str(meta.get("line") or "").strip(),
                    "tps": str(meta.get("tps") or "").strip(),
                    "file": p.name,
                    "href": lore_href(tray, p.name),
                    "crate": own,
                    "source_crate": norm_crate(str(meta.get("source_crate") or "")),
                    "edges": lore_edge_crates(meta),
                }
            )
    return 200, {"cards": cards, "house": spec["house"]}, ""


def catalog_lore_attach(
    mouth: str, pocket_raw: str, card_crate: str, onto: str = ""
) -> tuple[int, dict | None, str]:
    spec = CATALOG.get(mouth)
    if not spec:
        return 400, None, "no such catalog"
    card_crate = norm_crate(card_crate)
    if not card_crate:
        return 400, None, "need a lore crate"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _catalog_lore_attach(mouth, pocket_raw, card_crate, onto)


def _catalog_lore_attach(
    mouth: str, pocket_raw: str, card_crate: str, onto: str = ""
) -> tuple[int, dict | None, str]:
    spec = CATALOG[mouth]
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest, anchor, pocket, crate = catalog_onto_bag(mouth, target, onto)
    if dest is None:
        return 400, None, "not a vault page"
    if not crate:
        dest_md = crate_file_for(anchor)
        if dest_md is not None:
            crate = ensure_crate(dest_md)
    if not crate:
        return 400, None, "no crate on this page"
    if crate == card_crate:
        return 400, None, "a card cannot touch itself"
    path = find_lore_file(mouth, card_crate)
    if path is None:
        return 404, None, "no such lore"
    with LBR_LOCK:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return 500, None, "could not read lore"
        meta, _body = parse_fm(text)
        if norm_crate(str(meta.get("crate") or "")) != card_crate:
            return 404, None, "no such lore"
        edges = lore_edge_crates(meta)
        already = crate in edges
        if not already:
            edges.append(crate)
            path.write_text(apply_lore_edges_fm(text, edges), encoding="utf-8")
        if spec.get("blot"):
            obj = blot_read(dest, pocket, spec["house"])
            if crate:
                obj["crate"] = crate
            if mouth == "charlie":
                charlie_normalize(obj)
                charlie_decorate(obj, pocket)
            obj["lore"] = lore_cards_for(mouth, crate)
        else:
            obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    obj["href"] = lore_href(spec["tray"], path.name)
    obj["file"] = path.name
    obj["attached"] = not already
    return 200, obj, ""


def suggest_get(mouth: str = "librarian") -> dict:
    spec = CATALOG.get(mouth) or CATALOG["librarian"]
    return suggest_load(spec["suggest"])


def shelf_anchor(kind: str, target: Path) -> Path:
    spec = SHELF_KIND.get(kind) or SHELF_KIND["librarian"]
    if spec["scope"] == "index":
        folder = nearest_index_folder(target)
        return folder if folder is not None else target
    return target


def tag_slug(raw: str) -> str:
    """The word is the tag. ROSE and rose are the same bag-label."""
    s = (raw or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    s = s.lstrip("#").strip()
    s = re.sub(r"\s+", "-", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9_/-]+", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-/")
    if not s or not re.match(r"[a-z0-9]", s):
        return ""
    return s


def charlie_split(raw: str) -> list[str]:
    """Comma fans a box into words."""
    out: list[str] = []
    seen: set[str] = set()
    for part in str(raw or "").split(","):
        slug = tag_slug(part)
        if slug and slug not in seen:
            seen.add(slug)
            out.append(slug)
    return out


def charlie_thread_id(frm: str, rel: str, to: str) -> str:
    return f"{frm}*{rel}>{to}"


def charlie_weave(obj: dict, frm_raw: str, rel_raw: str, to_raw: str) -> list[str]:
    """One box → pins. Two or three → threads. Commas fan. Bare from+to is is."""
    froms = charlie_split(frm_raw)
    rels = charlie_split(rel_raw)
    tos = charlie_split(to_raw)
    filled = sum(1 for col in (froms, rels, tos) if col)
    now = int(time.time())
    if filled == 0:
        return []
    if filled == 1:
        words = froms or rels or tos
        thoughts = list(obj.get("thoughts") or [])
        have = {str(t.get("id") or "") for t in thoughts}
        batch: list[dict] = []
        for slug in words:
            if slug in have:
                continue
            batch.append(
                {
                    "id": slug,
                    "at": now,
                    "leaf": slug,
                    "tags": [],
                    "namespaces": [],
                    "times": [],
                    "cites": [],
                }
            )
            have.add(slug)
        obj["thoughts"] = batch + thoughts
        return [t["id"] for t in batch]
    threads = list(obj.get("threads") or [])
    have = {str(t.get("id") or "") for t in threads}
    batch = []
    for frm in froms or [""]:
        for rel in rels or [""]:
            for to in tos or [""]:
                use_rel = rel or ("is" if frm and to else "")
                if not frm and not use_rel and not to:
                    continue
                tid = charlie_thread_id(frm, use_rel, to)
                if tid in have:
                    continue
                batch.append(
                    {
                        "id": tid,
                        "at": now,
                        "from": frm,
                        "rel": use_rel,
                        "to": to,
                    }
                )
                have.add(tid)
    obj["threads"] = batch + threads
    return [t["id"] for t in batch]


def pocket_title(pocket: str) -> str:
    target = resolve_vault_page(pocket)
    if target is None:
        return (pocket or "").strip("/") or "/"
    if target.is_dir():
        t = (
            str(read_md_meta(target / INDEX_NAME).get("title") or "").strip()
            or str(read_md_meta(target / PAPER_NAME).get("title") or "").strip()
        )
        return t or target.name
    t = str(read_md_meta(target).get("title") or "").strip()
    return t or target.stem


def charlie_normalize(obj: dict) -> dict:
    seen: set[str] = set()
    out: list[dict] = []
    for t in obj.get("thoughts") or []:
        if not isinstance(t, dict):
            continue
        slug = tag_slug(str(t.get("leaf") or t.get("id") or ""))
        if not slug or slug in seen:
            continue
        seen.add(slug)
        item = dict(t)
        item["id"] = slug
        item["leaf"] = slug
        item.pop("also", None)
        out.append(item)
    obj["thoughts"] = out
    tseen: set[str] = set()
    tout: list[dict] = []
    for t in obj.get("threads") or []:
        if not isinstance(t, dict):
            continue
        frm = tag_slug(str(t.get("from") or ""))
        rel = tag_slug(str(t.get("rel") or ""))
        to = tag_slug(str(t.get("to") or ""))
        if not frm and not rel and not to:
            continue
        tid = str(t.get("id") or "").strip() or charlie_thread_id(frm, rel, to)
        if tid in tseen:
            continue
        tseen.add(tid)
        item = dict(t)
        item["id"] = tid
        item["from"] = frm
        item["rel"] = rel
        item["to"] = to
        tout.append(item)
    obj["threads"] = tout
    return obj


def charlie_weave_map() -> dict[str, dict[str, list[dict]]]:
    """Inverted Charlie lookup — Dewey by_tag / Charlie by_aven, by_relativity, by_insect.

    pin  — one-box tags
    from — left of a thread (aven)
    rel  — middle connector (relativity)
    to   — right of a thread (insect)
    bags — union, for the pin 'also' count
    """
    out: dict[str, dict[str, list[dict]]] = {
        "pin": {},
        "from": {},
        "rel": {},
        "to": {},
        "bags": {},
    }
    if not CHARLIE_ROOT.is_dir():
        return out
    try:
        root = CHARLIE_ROOT.resolve()
    except OSError:
        return out

    def wear_bag(slug: str, bag: dict) -> None:
        if not slug:
            return
        lst = out["bags"].setdefault(slug, [])
        if any(b.get("pocket") == bag.get("pocket") for b in lst):
            return
        lst.append(bag)

    def wear_thread(role: str, slug: str, hit: dict, bag: dict) -> None:
        if not slug:
            return
        out[role].setdefault(slug, []).append(hit)
        wear_bag(slug, bag)

    for path in root.rglob("*.yaml"):
        try:
            path.relative_to(root)
        except ValueError:
            continue
        obj = blot_read(path, "", "CHARLIE")
        charlie_normalize(obj)
        pocket = str(obj.get("pocket") or "").strip()
        if not pocket or pocket == "/":
            continue
        crate = str(obj.get("crate") or "").strip()
        title = onto_name(pocket)
        href = "/"
        with using_pocket(pocket) as host:
            if host is not None:
                title = pocket_title(pocket) or title
                href = href_from_pocket(pocket)
                target = resolve_vault_page(pocket)
                if target is not None:
                    crate = bag_crate(target) or crate
        bag = {"pocket": pocket, "title": title, "href": href, "crate": crate}
        for t in obj.get("thoughts") or []:
            slug = str(t.get("id") or "")
            if slug:
                out["pin"].setdefault(slug, []).append(dict(bag))
                wear_bag(slug, bag)
        for th in obj.get("threads") or []:
            frm = str(th.get("from") or "")
            rel = str(th.get("rel") or "")
            to = str(th.get("to") or "")
            hit = {
                "pocket": pocket,
                "title": title,
                "href": href,
                "crate": crate,
                "from": frm,
                "rel": rel,
                "to": to,
            }
            wear_thread("from", frm, hit, bag)
            wear_thread("rel", rel, hit, bag)
            wear_thread("to", to, hit, bag)
    return out


def onto_name(pocket: str) -> str:
    p = (pocket or "").replace("\\", "/").strip("/")
    name = p.split("/")[-1] if p else pocket
    if name.lower().endswith(".md"):
        name = name[:-3]
    return name or pocket or "this page"


def charlie_bags_index() -> dict[str, list[dict]]:
    return charlie_weave_map().get("bags") or {}


def charlie_decorate(obj: dict, current_pocket: str) -> dict:
    charlie_normalize(obj)
    bags = charlie_bags_index()
    here = (current_pocket or "").strip() or "/"
    for t in obj.get("thoughts") or []:
        slug = str(t.get("id") or "")
        others = [b for b in bags.get(slug, []) if b.get("pocket") != here]
        t["also"] = others
    obj["hashes"] = [{"id": s, "leaf": s} for s in hashes_on_pocket(here)]
    return obj


def mint_crate_id() -> str:
    return "crate." + os.urandom(8).hex().upper()


def crate_file_for(target: Path) -> Path | None:
    if target.is_file() and target.suffix.lower() in {".md", ".canvas"}:
        return target
    if target.is_dir():
        start = lobby_start(target)
        if start is not None:
            return start
        for name in (PAPER_NAME, INDEX_NAME):
            p = target / name
            if p.is_file():
                return p
    return None


def _in_active_vault(path: Path) -> bool:
    try:
        path.resolve().relative_to(active_vault().resolve())
        return True
    except (OSError, ValueError):
        return False


def ensure_crate(path: Path) -> str:
    """Stamp crate onto this vault page the first time Go opens it. Never overwrite.
    .md -> YAML frontmatter crate:; .canvas -> JSON metadata.crate.
    """
    if not path.is_file():
        return ""
    suf = path.suffix.lower()
    if suf not in {".md", ".canvas"}:
        return ""
    if not _in_active_vault(path):
        return ""
    have = file_crate(path)
    if have:
        return have
    with LBR_LOCK:
        have = file_crate(path)
        if have:
            return have
        crate = mint_crate_id()
        if suf == ".canvas":
            if not apply_canvas_crate(path, crate):
                # race: someone else stamped, or write failed
                return file_crate(path) or ""
            return crate
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return ""
        have = str(parse_fm(text)[0].get("crate") or "").strip()
        if have:
            return have
        new_text, changed = apply_crate_fm(text, crate)
        if not changed:
            return str(parse_fm(new_text)[0].get("crate") or "").strip() or crate
        try:
            path.write_text(new_text, encoding="utf-8")
        except OSError:
            return ""
        return crate


def apply_crate_fm(text: str, crate: str) -> tuple[str, bool]:
    """Stamp crate into frontmatter. Never overwrite a live one."""
    raw = text.replace("\r\n", "\n").lstrip("\ufeff")
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end >= 0:
            head = raw[4:end]
            rest = raw[end + 5 :]
            lines = head.split("\n")
            found = False
            new_lines: list[str] = []
            for line in lines:
                if line.startswith("crate:"):
                    found = True
                    cur = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if cur:
                        return text, False
                    new_lines.append("crate: " + crate)
                else:
                    new_lines.append(line)
            if not found:
                new_lines.insert(0, "crate: " + crate)
            return "---\n" + "\n".join(new_lines) + "\n---\n" + rest, True
    return "---\ncrate: " + crate + "\n---\n\n" + raw, True


def crate_issue(pocket_raw: str) -> tuple[int, dict | None, str]:
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _crate_issue(pocket_raw)


def _crate_issue(pocket_raw: str) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = crate_file_for(target)
    if dest is None:
        return 400, None, "no page to stamp"
    before = file_crate(dest)
    crate = ensure_crate(dest)
    if not crate:
        return 500, None, "could not stamp page"
    return 200, {
        "crate": crate,
        "pocket": pocket_key(target),
        "minted": not bool(before),
    }, ""


def _charlie_word_link(word: str, cls: str = "") -> str:
    slug = tag_slug(word)
    if not slug:
        return '<span class="cork-gap">·</span>'
    klass = ' class="' + html.escape(cls, True) + '"' if cls else ""
    return (
        f'<a{klass} href="/?c={html.escape(quote(slug), True)}">'
        f"{html.escape(slug)}</a>"
    )


def _tagbay_meta(pocket: str, crate: str = "", off: bool = False) -> str:
    bits = []
    if crate:
        href = crate_href(crate)
        bits.append(
            f'<a class="tagbay-crate-id" href="{html.escape(href, True)}">'
            f"{html.escape(crate)}</a>"
        )
    elif off:
        bits.append('<em class="tagbay-off">off ledger</em>')
    if pocket:
        bits.append(
            f'<span class="hit-path" title="{html.escape(pocket, True)}">'
            f"{html.escape(pocket)}</span>"
        )
    if not bits:
        return ""
    return '<span class="tagbay-meta">' + "".join(bits) + "</span>"


def _tagbay_note(href: str, title: str) -> str:
    return (
        f'<a class="tagbay-note" href="{html.escape(href, True)}">'
        f"{html.escape(title)}</a>"
    )



def _tagbay_fold_lis(items: list[str], fold_at: int = 8) -> str:
    """Join <li>…</li> rows; tuck the overflow under a show-more."""
    if fold_at <= 0 or len(items) <= fold_at:
        return "".join(items)
    head = "".join(items[:fold_at])
    rest_n = len(items) - fold_at
    rest = "".join(items[fold_at:])
    return (
        head
        + '<li class="tagbay-fold">'
        + '<details class="tagbay-more">'
        + f"<summary>show {rest_n} more</summary>"
        + f"<ul>{rest}</ul>"
        + "</details></li>"
    )


def _tagbay_chest(label: str, inner: str, n: int, focus: bool = False, layout: str = "") -> str:
    cls = "tagbay-chest" + (" is-focus" if focus else "")
    extra = (layout or "").strip()
    if extra:
        cls += " " + extra
    return (
        f'<section class="{cls}" data-bay="{html.escape(label, True)}">'
        '<header class="tagbay-chest-head">'
        f"<h2>{html.escape(label)}</h2>"
        f'<span class="tagbay-n">{n:02d}</span>'
        "</header>"
        f"<ul>{inner}</ul>"
        "</section>"
    )


def _tagbay_article(slug: str, inner: str, role: str = "") -> str:
    shown = slug or "tag"
    role = (role or "").strip().lower()
    if role == "pin":
        role = "tag"
    kicker = "charlie lookup"
    if role in ("tag", "hash"):
        kicker = "charlie lookup · " + role
    mark = (
        '<span class="tagbay-hash">#</span>'
        if role != "tag"
        else ""
    )
    skin = f" is-as-{role}" if role in ("tag", "hash") else ""
    return (
        f'<article class="tagbay{skin}">'
        '<header class="tagbay-mast">'
        '<p class="tagbay-sys">'
        f"<span>mypi:bay</span> {html.escape(kicker)}"
        "</p>"
        f"<h1>{mark}{html.escape(shown)}"
        '<span class="tagbay-cursor" aria-hidden="true"></span></h1>'
        "</header>"
        f"{inner}"
        "</article>"
    )


def _tagbay_body(slug: str, here: str = "", role: str = "") -> str:
    slug = tag_slug(slug)
    role = (role or "").strip().lower()
    if role == "pin":
        role = "tag"
    if role not in ("tag", "hash"):
        role = ""
    catalog = charlie_weave_map()
    pins = catalog["pin"].get(slug, []) if slug else []
    as_from = catalog["from"].get(slug, []) if slug else []
    as_rel = catalog["rel"].get(slug, []) if slug else []
    as_to = catalog["to"].get(slug, []) if slug else []
    hashes = hashes_for_word(slug) if slug else []
    if not pins and not as_from and not as_rel and not as_to and not hashes:
        return _tagbay_article(
            slug,
            '<p class="tagbay-void">Charlie has not woven this word yet.</p>',
            role,
        )
    chests: list[tuple[str, str, int]] = []
    for label, hits, stance in (
        ("as from", as_from, "from"),
        ("as connector", as_rel, "rel"),
        ("as to", as_to, "to"),
    ):
        if hits:
            chests.append(
                (label, _charlie_chain_items(hits, here, stance=stance), len(hits))
            )
    if pins:
        chests.append(
            (
                "as pin",
                _tagbay_page_hits(pins, off_if_empty=True, here=here),
                len(pins),
            )
        )
    if hashes:
        chests.append(
            ("as hash", _tagbay_page_hits(hashes, here=here), len(hashes))
        )
    want = {"tag": "as pin", "hash": "as hash"}.get(role, "")
    if want:
        chests.sort(key=lambda c: 0 if c[0] == want else 1)
    parts = [
        _tagbay_chest(label, inner, n, focus=(want == label))
        for label, inner, n in chests
    ]
    return _tagbay_article(slug, "".join(parts), role)


def charlie_tag_fragment(slug: str, here: str = "", role: str = "") -> bytes:
    return _tagbay_body(slug, here, role).encode("utf-8")


def charlie_tag_page(slug: str, role: str = "") -> bytes:
    slug = tag_slug(slug)
    mark = "#" if (role or "").strip().lower() != "tag" else ""
    return sheet_page(
        f"{mark}{slug}",
        _tagbay_body(slug, role=role),
        "#1a1204",
        "is-tagbay",
        "mypi:bay",
        extra_css=["/tagbay.css"],
        kind="charlie",
    )


def _charlie_chain_items(
    hits: list[dict], here: str = "", stance: str = "from"
) -> str:
    """Connector bins first; source pages stay quiet citations under the chips."""
    stance = (stance or "from").strip().lower()
    if stance not in ("from", "to", "rel"):
        stance = "from"

    # rel -> pocket -> {meta, tos, froms, pairs}
    bins: dict[str, dict[str, dict]] = {}
    for t in hits:
        if not isinstance(t, dict):
            continue
        pocket = str(t.get("pocket") or "").lstrip("/")
        if not pocket:
            continue
        rel = str(t.get("rel") or "").strip() or "—"
        frm = str(t.get("from") or "").strip()
        to = str(t.get("to") or "").strip()
        by_page = bins.setdefault(rel, {})
        page = by_page.get(pocket)
        if page is None:
            page = {
                "pocket": pocket,
                "title": str(t.get("title") or pocket),
                "href": str(
                    t.get("href") or href_from_pocket(str(t.get("pocket") or ""))
                ),
                "crate": str(t.get("crate") or "").strip(),
                "tos": [],
                "froms": [],
                "pairs": [],
            }
            by_page[pocket] = page
        if to and to not in page["tos"]:
            page["tos"].append(to)
        if frm and frm not in page["froms"]:
            page["froms"].append(frm)
        pair = (frm, to)
        if pair not in page["pairs"]:
            page["pairs"].append(pair)

    def page_sort_key(page: dict) -> tuple:
        pocket = str(page.get("pocket") or "")
        here_rank = 0 if here and _pocket_same(pocket, here) else 1
        return (here_rank, str(page.get("title") or pocket).lower(), pocket.lower())

    items: list[str] = []
    for rel, by_page in sorted(bins.items(), key=lambda kv: kv[0].lower()):
        page_blocks: list[str] = []
        n_words = 0
        for page in sorted(by_page.values(), key=page_sort_key):
            if stance == "from":
                words = page["tos"]
                chips = "".join(
                    f'<li class="charlie-bin-word">{_charlie_word_link(w)}</li>'
                    for w in words
                )
            elif stance == "to":
                words = page["froms"]
                chips = "".join(
                    f'<li class="charlie-bin-word">{_charlie_word_link(w)}</li>'
                    for w in words
                )
            else:
                words = page["pairs"]
                chips = "".join(
                    '<li class="charlie-bin-word charlie-bin-pair">'
                    + _charlie_word_link(frm)
                    + ' <span class="charlie-sep charlie-sep-soft">to</span> '
                    + _charlie_word_link(to)
                    + "</li>"
                    for frm, to in page["pairs"]
                    if frm or to
                )
            if not chips:
                continue
            n_words += len(words)
            here_cls = (
                " is-here"
                if here and _pocket_same(str(page.get("pocket") or ""), here)
                else ""
            )
            cite = (
                f'<p class="charlie-bin-cite{here_cls}">'
                f'{_tagbay_note(page["href"], page["title"])}'
                f'<span class="charlie-bin-cite-meta">'
                f'{html.escape(" · ".join(x for x in (page["crate"], page["pocket"]) if x))}'
                f"</span></p>"
            )
            page_blocks.append(
                f'<div class="charlie-bin-page{here_cls}">'
                f'<ul class="charlie-bin-words">{chips}</ul>'
                f"{cite}"
                "</div>"
            )
        if not page_blocks:
            continue
        items.append(
            '<li class="tagbay-hit tagbay-relbin">'
            '<div class="charlie-bin">'
            f'<h3 class="charlie-bin-rel">{_charlie_word_link(rel, "cork-rel")}</h3>'
            f'<div class="charlie-bin-pages">{"".join(page_blocks)}</div>'
            "</div>"
            "</li>"
        )
    return _tagbay_fold_lis(items)


def _tagbay_page_hits(hits: list[dict], off_if_empty: bool = False, here: str = "") -> str:
    items = []
    for b in hits:
        pocket = str(b.get("pocket") or "").lstrip("/")
        title = str(b.get("title") or pocket)
        crate = str(b.get("crate") or "").strip()
        href = str(b.get("href") or href_from_pocket(str(b.get("pocket") or "")))
        here_cls = " is-here" if here and _pocket_same(pocket, here) else ""
        items.append(
            f'<li class="tagbay-hit{here_cls}">'
            '<div class="tagbay-hit-main">'
            f"{_tagbay_note(href, title)}"
            "</div>"
            f"{_tagbay_meta(pocket, crate, off=off_if_empty and not crate)}"
            "</li>"
        )
    return _tagbay_fold_lis(items)


def catalog_field_href(mouth: str, label: str, value: str = "", binning: str = "") -> str:
    parts = []
    host = active_host()
    if host:
        parts.append("h=" + quote(host))
    parts.append("m=" + quote(mouth))
    if label:
        parts.append("f=" + quote(label))
    if value:
        parts.append("v=" + quote(value))
    binning = (binning or "").strip().lower()
    if binning in ("host", "value"):
        parts.append("bin=" + quote(binning))
    return "/?" + "&".join(parts)


def catalog_bin_of(value: str, raw: str = "") -> str:
    raw = (raw or "").strip().lower()
    if raw in ("host", "value"):
        return raw
    return "host" if (value or "").strip() else "value"


def norm_chip(raw: str) -> str:
    return re.sub(r"\s+", " ", (raw or "").strip()).lower()


def catalog_chip_hits(mouth: str, value: str) -> list[dict]:
    """Pages where any field chip equals this value. One bag per pocket+label."""
    if mouth not in ("librarian", "agent"):
        return []
    spec = SHELF_KIND.get(mouth)
    if not spec:
        return []
    root = spec["root"]
    want_value = norm_chip(value)
    if not want_value or not root.is_dir():
        return []
    seen: set[str] = set()
    out: list[dict] = []
    try:
        base = root.resolve()
    except OSError:
        return []
    for path in root.rglob("*.yaml"):
        try:
            path.resolve().relative_to(base)
        except ValueError:
            continue
        if path.name.lower() == "_suggest.yaml":
            continue
        obj = catalog_read(path, "", CATALOG[mouth]["house"])
        pocket = str(obj.get("pocket") or "").strip()
        if not pocket:
            continue
        matched: dict[str, list[str]] = {}
        for f in obj.get("fields") or []:
            if not isinstance(f, dict):
                continue
            lab = str(f.get("label") or "").strip()
            if not lab:
                continue
            hits = [v for v in chip_values(f) if norm_chip(v) == want_value]
            if not hits:
                continue
            matched.setdefault(lab, []).extend(hits)
        if not matched:
            continue
        with using_pocket(pocket) as host:
            if host is None:
                continue
            target = resolve_vault_page(pocket)
            crate = bag_crate(target) if target is not None else str(obj.get("crate") or "")
            title = pocket_title(pocket)
            href = href_from_pocket(pocket)
        for lab, hit_vals in matched.items():
            key = pocket + "\0" + lab
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "pocket": pocket,
                    "title": title,
                    "href": href,
                    "crate": crate,
                    "label": lab,
                    "values": hit_vals,
                }
            )
    out.sort(
        key=lambda b: (
            str(b.get("label") or "").lower(),
            str(b.get("title") or b.get("pocket") or "").lower(),
        )
    )
    return out


def lore_motif_hits(needle: str) -> list[dict]:
    """Lore cards whose title or class is this word, or whose line holds the phrase."""
    want = norm_chip(needle)
    if not want:
        return []
    out: list[dict] = []
    seen: set[str] = set()
    for mouth, spec in CATALOG.items():
        inbox = spec.get("inbox")
        if inbox is None or not inbox.is_dir():
            continue
        tray = spec.get("tray") or mouth
        for p in sorted(inbox.glob("*.md"), key=lambda x: x.name.lower()):
            if p.name.lower() in {INDEX_NAME, PAPER_NAME}:
                continue
            meta = read_md_meta(p)
            if not is_card_note(meta):
                continue
            title = str(meta.get("title") or p.stem).strip() or p.stem
            klass = str(meta.get("class") or "").strip()
            line = str(meta.get("line") or "").strip()
            hit = norm_chip(title) == want or norm_chip(klass) == want
            if not hit and " " in want and want in norm_chip(line):
                hit = True
            if not hit:
                continue
            crate = norm_crate(str(meta.get("crate") or ""))
            key = crate or str(p)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "title": title,
                    "class": klass,
                    "house": str(meta.get("house") or spec.get("house") or "").strip(),
                    "file": p.name,
                    "href": lore_href(tray, p.name),
                    "crate": crate,
                    "line": line,
                    "mouth": mouth,
                }
            )
    out.sort(key=lambda b: str(b.get("title") or "").lower())
    return out


def catalog_field_hits(mouth: str, label: str, value: str) -> list[dict]:
    """Pages whose catalog YAML has this label, and this value if given."""
    if mouth == "tps":
        return tps_hits(kind=label, value=value)
    if mouth not in ("librarian", "agent"):
        return []
    spec = SHELF_KIND.get(mouth)
    if not spec:
        return []
    root = spec["root"]
    want_label = norm_chip(label)
    want_value = norm_chip(value)
    if not want_label or not root.is_dir():
        return []
    seen: set[str] = set()
    out: list[dict] = []
    try:
        base = root.resolve()
    except OSError:
        return []
    for path in root.rglob("*.yaml"):
        try:
            path.resolve().relative_to(base)
        except ValueError:
            continue
        if path.name.lower() == "_suggest.yaml":
            continue
        obj = catalog_read(path, "", CATALOG[mouth]["house"])
        pocket = str(obj.get("pocket") or "").strip()
        if not pocket or pocket in seen:
            continue
        hit_vals: list[str] = []
        for f in obj.get("fields") or []:
            if not isinstance(f, dict):
                continue
            if norm_chip(str(f.get("label") or "")) != want_label:
                continue
            vals = chip_values(f)
            if want_value:
                if not any(norm_chip(v) == want_value for v in vals):
                    continue
                hit_vals.append(value)
            else:
                hit_vals.extend(vals)
            break
        else:
            continue
        seen.add(pocket)
        with using_pocket(pocket) as host:
            if host is None:
                continue
            target = resolve_vault_page(pocket)
            crate = bag_crate(target) if target is not None else str(obj.get("crate") or "")
            out.append(
                {
                    "pocket": pocket,
                    "title": pocket_title(pocket),
                    "href": href_from_pocket(pocket),
                    "crate": crate,
                    "values": hit_vals,
                }
            )
    out.sort(key=lambda b: str(b.get("title") or b.get("pocket") or "").lower())
    return out


CATALOG_BAY = {
    "librarian": {
        "who": "librarian catalog",
        "brick": "mypi:lib",
        "mark": "mypi:lib",
        "accent": "#2a3f3d",
        "skin": "is-libbay",
        "cls": "is-lib",
        "empty": "Librarian has not filed this field yet.",
        "kicker": "as field",
    },
    "agent": {
        "who": "agent index",
        "brick": "mypi:hunt",
        "mark": "mypi:hunt",
        "accent": "#c4202a",
        "skin": "is-agentbay",
        "cls": "is-hunt",
        "empty": "Agent has not indexed this field yet.",
        "kicker": "as field",
    },
    "tps": {
        "who": "tps report",
        "brick": "mypi:tps",
        "mark": "mypi:tps",
        "accent": "#3a3c34",
        "skin": "is-tpsbay",
        "cls": "is-tps",
        "empty": "TPS has not stamped this yet.",
        "kicker": "created",
    },
}

CRATE_BAY = {
    "who": "crate report",
    "brick": "mypi:crate",
    "mark": "mypi:crate",
    "accent": "#5c3e28",
    "skin": "is-cratebay",
    "cls": "is-crate",
    "empty": "Nothing else has touched this crate yet.",
}


def _crate_header_href(meta: dict, key: str) -> str:
    want = str(key or "").strip().lower() + "_href"
    for k, raw in (meta or {}).items():
        if str(k).strip().lower() == want:
            return str(raw or "").strip()
    return ""


def _crate_header_val(meta: dict, key: str, raw: object) -> str:
    low = str(key or "").strip().lower()
    if low == "edges":
        items = raw if isinstance(raw, list) else parse_flow_list(str(raw or ""))
        crates = []
        seen: set[str] = set()
        for x in items:
            c = norm_crate(str(x))
            if c and c not in seen:
                crates.append(c)
                seen.add(c)
        if not crates:
            return ""
        bits = [
            f'<a class="tagbay-val" href="{html.escape(crate_href(c), True)}">'
            f"{html.escape(c)}</a>"
            for c in crates
        ]
        return '<span class="tagbay-vals">' + "".join(bits) + "</span>"
    if low in ("crate", "source_crate"):
        c = norm_crate(str(raw or ""))
        if not c:
            return ""
        return (
            '<span class="tagbay-vals">'
            f'<a class="tagbay-val" href="{html.escape(crate_href(c), True)}">'
            f"{html.escape(c)}</a></span>"
        )
    if low in ("tags", "tag"):
        chips = "".join(tag_chip(t) for t in split_tags(str(raw or "")))
        return ('<span class="tagbay-vals">' + chips + "</span>") if chips else ""
    text = str(raw or "").strip().strip('"').strip("'")
    if not text:
        return ""
    as_crate = norm_crate(text)
    if as_crate:
        return (
            '<span class="tagbay-vals">'
            f'<a class="tagbay-val" href="{html.escape(crate_href(as_crate), True)}">'
            f"{html.escape(as_crate)}</a></span>"
        )
    painted = fm_inline(text)
    href = _crate_header_href(meta, key)
    if painted and href.startswith("/") and not href.startswith("//"):
        return (
            '<span class="tagbay-vals">'
            f'<a class="tagbay-val" href="{html.escape(href, True)}">{painted}</a>'
            "</span>"
        )
    outside = outlink_html(href, text) if painted and href else ""
    if outside:
        return '<span class="tagbay-vals">' + outside + "</span>"
    return '<span class="tagbay-vals">' + painted + "</span>"


def _crate_header_items(meta: dict | None) -> str:
    """The paper's YAML — the hidden cabinet. Crate ids and tags stay doors."""
    meta = meta or {}
    rows: list[str] = []
    seen: set[str] = set()

    def emit(key: object, raw: object) -> None:
        name = str(key or "").strip()
        low = name.lower()
        if not name or low in seen or low.endswith("_href"):
            return
        seen.add(low)
        val = _crate_header_val(meta, name, raw)
        if not val:
            return
        rows.append(
            '<li class="tagbay-hit">'
            '<div class="tagbay-hit-main">'
            f'<span class="crate-mark">{html.escape(name)}</span>'
            f"{val}"
            "</div></li>"
        )

    for key in CARD_META_ORDER:
        emit(key, meta.get(key))
    for key, raw in meta.items():
        emit(key, raw)
    return "".join(rows)


def _catalog_vals(mouth: str, label: str, vals: list) -> str:
    bits = []
    for v in vals:
        v = str(v or "").strip()
        if not v:
            continue
        bits.append(
            f'<a class="tagbay-val" href="{html.escape(value_door_href(mouth, label, v), True)}">'
            f"{html.escape(v)}</a>"
        )
    if not bits:
        return ""
    return '<span class="tagbay-vals">' + "".join(bits) + "</span>"


def _tps_stamp_vals(stamps: list) -> str:
    bits = []
    for s in stamps:
        if not isinstance(s, dict):
            continue
        title = str(s.get("title") or s.get("stamp_title") or "").strip()
        if not title:
            continue
        when = str(s.get("when") or "").strip()
        title_href = str(s.get("title_href") or tps_href("title", title))
        when_href = str(s.get("when_href") or s.get("unix_href") or "")
        kind = (
            f'<a class="tagbay-val tps-kind" href="{html.escape(title_href, True)}">'
            f"{html.escape(title)}</a>"
        )
        when_html = ""
        if when:
            shown = html.escape(when)
            if when_href:
                shown = (
                    f'<a class="tps-hit-when" href="{html.escape(when_href, True)}">'
                    f"{shown}</a>"
                )
            else:
                shown = f'<span class="tps-hit-when">{shown}</span>'
            when_html = shown
        bits.append(f'<span class="tps-hit-stamp">{kind}{when_html}</span>')
    if not bits:
        return ""
    return '<span class="tagbay-vals tps-hit-vals">' + "".join(bits) + "</span>"


def tps_sort_rows(rows: list[dict], sort: str, order: str) -> list[dict]:
    sort = (sort or "when").strip().lower()
    if sort not in TPS_SORT_KEYS:
        sort = "when"
    reverse = (order or "asc").strip().lower() == "desc"

    def key(r: dict):
        if sort == "when":
            return int(r.get("at") or 0)
        if sort == "page":
            return str(r.get("page") or "").lower()
        if sort == "environment":
            return str(r.get("environment") or "").lower()
        return str(r.get("pocket") or "").lower()

    return sorted(rows, key=key, reverse=reverse)


def tps_crumb(filters: dict[str, str]) -> str:
    if not filters:
        return ""
    bits = []
    sofar: dict[str, str] = {}
    for k in TPS_FILTER_KEYS:
        val = str(filters.get(k) or "").strip()
        if not val:
            continue
        sofar[k] = val
        drop = {x: y for x, y in filters.items() if x != k}
        bits.append(
            '<span class="tps-crumb-bit">'
            f'<a class="tps-crumb-on" href="{html.escape(tps_href(sofar), True)}">'
            f"{html.escape(k)} {html.escape(val)}</a>"
            f'<a class="tps-crumb-x" href="{html.escape(tps_href(drop), True)}" title="drop {html.escape(k, True)}">×</a>'
            "</span>"
        )
    return '<p class="tps-crumb">' + "".join(bits) + "</p>"


def tps_further_html(rows: list[dict], filters: dict[str, str]) -> str:
    kinds = ("month", "day", "year", "hour")
    blocks = []
    for kind in kinds:
        if str(filters.get(kind) or "").strip():
            continue
        counts: dict[str, int] = {}
        for r in rows:
            word = str((r.get("slices") or {}).get(kind) or "").strip()
            if word:
                counts[word] = counts.get(word, 0) + 1
        if not counts:
            continue
        chips = []
        items = [{"value": w, "n": n} for w, n in counts.items()]
        items.sort(key=lambda x: tps_bucket_key(kind, str(x["value"])))
        for it in items:
            href = tps_href(filters, extra={kind: it["value"]})
            count = int(it["n"] or 0)
            nbit = f'<span class="tps-n">{count}</span>' if count > 1 else ""
            chips.append(
                f'<a class="catalog-hit" href="{html.escape(href, True)}">'
                f"{html.escape(str(it['value']))}{nbit}</a>"
            )
        blocks.append(
            '<div class="tps-bin"><span class="tps-bin-label">'
            + html.escape(kind)
            + '</span><span class="tps-bucket">'
            + "".join(chips)
            + "</span></div>"
        )
    if not blocks:
        return ""
    return '<div class="tps-narrow"><div class="catalog-head">narrow</div>' + "".join(blocks) + "</div>"


def tps_sort_href(filters: dict[str, str], col: str, cur_sort: str, cur_order: str) -> str:
    if cur_sort == col:
        nxt = "desc" if cur_order != "desc" else "asc"
    else:
        nxt = "asc" if col != "when" else "asc"
    return tps_href(filters, sort=col, order=nxt)


def tps_table(rows: list[dict], filters: dict[str, str], sort: str, order: str) -> str:
    def th(col: str, label: str) -> str:
        href = tps_sort_href(filters, col, sort, order)
        mark = ""
        if sort == col:
            mark = " ↓" if order == "desc" else " ↑"
        return (
            f'<th class="tps-col-{html.escape(col, True)}">'
            f'<a href="{html.escape(href, True)}">{html.escape(label)}{html.escape(mark)}</a></th>'
        )

    body = []
    for r in rows:
        page_name = str(r.get("page") or r.get("pocket") or "")
        href = str(r.get("href") or "#")
        when = str(r.get("when") or "")
        when_href = str(r.get("when_href") or r.get("unix_href") or "")
        env = str(r.get("environment") or "").strip() or "—"
        pocket = str(r.get("pocket") or "").lstrip("/")
        when_cell = (
            f'<a href="{html.escape(when_href, True)}">{html.escape(when)}</a>'
            if when_href
            else html.escape(when)
        )
        body.append(
            "<tr>"
            f'<td class="tps-col-when">{when_cell}</td>'
            f'<td class="tps-col-page">{_tagbay_note(href, page_name)}</td>'
            f'<td class="tps-col-environment">{html.escape(env)}</td>'
            f'<td class="tps-col-path" title="{html.escape(pocket, True)}">{html.escape(pocket)}</td>'
            "</tr>"
        )
    return (
        '<table class="tps-table">'
        "<colgroup>"
        '<col class="tps-col-when">'
        '<col class="tps-col-page">'
        '<col class="tps-col-environment">'
        '<col class="tps-col-path">'
        "</colgroup>"
        "<thead><tr>"
        + th("when", "when")
        + th("page", "page")
        + th("environment", "environment")
        + th("path", "path")
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


def _tps_report_body(filters: dict[str, str], sort: str = "when", order: str = "asc") -> str:
    spec = CATALOG_BAY["tps"]
    sort = (sort or "when").strip().lower()
    if sort not in TPS_SORT_KEYS:
        sort = "when"
    order = (order or "asc").strip().lower()
    if order not in ("asc", "desc"):
        order = "asc"
    rows = tps_sort_rows(tps_hits(filters), sort, order)
    shown_bits = [str(filters.get(k) or "") for k in TPS_FILTER_KEYS if filters.get(k)]
    shown = html.escape(" · ".join(shown_bits) if shown_bits else "all dates")
    if not rows:
        inner = f'<p class="tagbay-void">{html.escape(spec["empty"])}</p>'
    else:
        groups: dict[str, list[dict]] = {}
        for r in rows:
            t = str(r.get("stamp_title") or "date").strip() or "date"
            groups.setdefault(t, []).append(r)
        inner = tps_further_html(rows, filters)
        for title, group in groups.items():
            inner += _tagbay_chest(
                title,
                '<li class="tps-table-hit">' + tps_table(group, filters, sort, order) + "</li>",
                len(group),
            )
    return (
        f'<article class="tagbay {spec["cls"]} is-tps-report">'
        '<header class="tagbay-mast">'
        f'<p class="tagbay-sys"><span>{html.escape(spec["brick"])}</span> '
        f'{html.escape(spec["who"])}</p>'
        f"<h1>{shown}<span class=\"tagbay-cursor\" aria-hidden=\"true\"></span></h1>"
        f"{tps_crumb(filters)}"
        "</header>"
        f"{inner}"
        "</article>"
    )


def tps_report_fragment(qs: dict) -> bytes:
    try:
        filters = tps_filters_from_qs(qs)
        sort = unquote((qs.get("sort") or ["when"])[0])
        order = unquote((qs.get("dir") or ["asc"])[0])
        return _tps_report_body(filters, sort, order).encode("utf-8")
    except Exception:
        return b'<p class="tagbay-void">could not build this tps report.</p>'


def tps_report_page(qs: dict) -> bytes:
    filters = tps_filters_from_qs(qs)
    sort = unquote((qs.get("sort") or ["when"])[0])
    order = unquote((qs.get("dir") or ["asc"])[0])
    spec = CATALOG_BAY["tps"]
    shown_bits = [str(filters.get(k) or "") for k in TPS_FILTER_KEYS if filters.get(k)]
    shown = " · ".join(shown_bits) if shown_bits else "tps"
    return sheet_page(
        shown,
        _tps_report_body(filters, sort, order),
        spec["accent"],
        spec["skin"],
        spec["mark"],
        extra_css=["/tagbay.css"],
        kind="tps",
    )


def crate_id_from_qs(qs: dict) -> str:
    raw = unquote((qs.get("k") or qs.get("crate") or [""])[0])
    return norm_crate(raw)


def crate_qs_is_report(qs: dict) -> bool:
    return bool(crate_id_from_qs(qs))


def faces_of_crate(crate: str) -> list[dict]:
    """Pages that print this crate with {{face:}} / {{card:}}. Cross-host."""
    crate = norm_crate(crate)
    if not crate:
        return []
    out: list[dict] = []
    seen: set[str] = set()

    def consider(p: Path) -> None:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return
        _meta, body = parse_fm(text)
        hit = False
        for m in FACE_CRATE_RE.finditer(body):
            if norm_crate(m.group(1)) == crate:
                hit = True
                break
        if not hit:
            return
        door = door_for_path(p)
        if door is None:
            return
        pocket = str(door.get("pocket") or "")
        if pocket in seen:
            return
        if norm_crate(str(door.get("crate") or "")) == crate:
            return
        seen.add(pocket)
        out.append(door)

    start = HOSTS_ROOT / START_NAME
    if start.is_file():
        consider(start)
    for host in discover_hosts().values():
        if not host.root.is_dir():
            continue
        for p in host.root.rglob("*.md"):
            try:
                rel_parts = p.relative_to(host.root).parts
            except ValueError:
                continue
            if any(part in SKIP or stash_name(part) for part in rel_parts):
                continue
            consider(p)
    out.sort(key=lambda d: str(d.get("title") or d.get("pocket") or "").lower())
    return out


def _crate_word_hits(slugs: list[str], role: str = "") -> str:
    items = []
    for slug in slugs:
        slug = tag_slug(slug)
        if not slug:
            continue
        href = tag_href(slug)
        if role and not norm_crate(slug):
            href += "&as=" + quote(role)
        shown = "#" + slug if role == "hash" else slug
        items.append(
            '<li class="tagbay-hit crate-chip">'
            '<div class="tagbay-hit-main">'
            f"{_tagbay_note(href, shown)}"
            "</div></li>"
        )
    return _tagbay_fold_lis(items)


def _crate_thread_items(threads: list) -> str:
    """Subject word, then a bin per connector with targets as chips."""
    subjects: dict[str, dict[str, list[str]]] = {}
    for t in threads:
        if not isinstance(t, dict):
            continue
        frm = str(t.get("from") or "").strip() or "—"
        rel = str(t.get("rel") or "").strip() or "—"
        to = str(t.get("to") or "").strip()
        bag = subjects.setdefault(frm, {})
        tos = bag.setdefault(rel, [])
        if to and to not in tos:
            tos.append(to)

    items: list[str] = []
    for frm, bins in sorted(subjects.items(), key=lambda kv: kv[0].lower()):
        bins_html: list[str] = []
        for rel, tos in sorted(bins.items(), key=lambda kv: kv[0].lower()):
            chips = "".join(
                f'<li class="charlie-bin-word">{_charlie_word_link(w)}</li>'
                for w in tos
            )
            if not chips:
                continue
            bins_html.append(
                '<div class="charlie-bin">'
                f'<h3 class="charlie-bin-rel">{_charlie_word_link(rel, "cork-rel")}</h3>'
                f'<ul class="charlie-bin-words">{chips}</ul>'
                "</div>"
            )
        if not bins_html:
            continue
        items.append(
            '<li class="tagbay-hit tagbay-thread-subject">'
            '<div class="tagbay-hit-main">'
            f'<span class="tagbay-chain-subject">{_charlie_word_link(frm)}</span>'
            "</div>"
            f'<div class="charlie-bins">{"".join(bins_html)}</div>'
            "</li>"
        )
    return _tagbay_fold_lis(items)


def lore_maker_shown(house: str = "", mouth: str = "") -> str:
    who = lore_house_label(house, mouth)
    if not who:
        return ""
    if who.isupper() or who.islower():
        return who[:1].upper() + who[1:]
    return who


def _crate_maker_kind(house: str) -> str:
    maker = lore_maker_shown(house)
    return (maker + " lore card") if maker else "Lore card"


def _crate_lore_hit(
    *,
    href: str,
    klass: str,
    title: str,
    house: str,
    crate_id: str,
    pocket: str = "",
    li_class: str = "",
) -> str:
    name = title or klass or "lore"
    house_shown = lore_maker_shown(house)
    deck = (klass or "").strip()
    if deck and name.lower() == deck.lower():
        deck = ""
    note = (
        _tagbay_note(href, name)
        if href
        else f'<span class="tagbay-note">{html.escape(name)}</span>'
    )
    house_bit = (
        f'<span class="crate-house">{html.escape(house_shown)}</span>'
        if house_shown
        else ""
    )
    deck_bit = (
        f'<span class="crate-deck">{html.escape(deck)}</span>' if deck else ""
    )
    extra_cls = (" " + li_class.strip()) if li_class else ""
    return (
        f'<li class="tagbay-hit is-lore{extra_cls}">'
        '<div class="tagbay-hit-main">'
        f"{house_bit}"
        '<span class="crate-kind">lore card</span>'
        f"{deck_bit}"
        f"{note}"
        "</div>"
        f"{_tagbay_meta(pocket, crate_id)}"
        "</li>"
    )


def _crate_lore_items(cards: list[dict]) -> str:
    items = []
    for card in cards:
        items.append(
            _crate_lore_hit(
                href=str(card.get("href") or ""),
                klass=str(card.get("class") or "").strip(),
                title=str(card.get("title") or card.get("file") or "").strip(),
                house=str(card.get("house") or card.get("mouth") or "").strip(),
                crate_id=str(card.get("crate") or "").strip(),
            )
        )
    return "".join(items)


def _crate_field_items(mouth: str, fields: list) -> str:
    items = []
    for f in fields:
        if not isinstance(f, dict):
            continue
        label = str(f.get("label") or "").strip()
        if not label:
            continue
        vals = chip_values(f)
        extra = _catalog_vals(mouth, label, vals)
        href = catalog_field_href(mouth, label)
        items.append(
            '<li class="tagbay-hit">'
            '<div class="tagbay-hit-main">'
            f'<a class="tagbay-field" href="{html.escape(href, True)}">'
            f"{html.escape(label)}</a>"
            f"{extra}"
            "</div></li>"
        )
    return "".join(items)


def _crate_stamp_items(stamps: list) -> str:
    items = []
    for s in stamps:
        if not isinstance(s, dict):
            continue
        title = str(s.get("title") or "").strip()
        when = str(s.get("when") or "").strip()
        title_href = str(s.get("title_href") or tps_href("title", title))
        when_href = str(s.get("when_href") or s.get("unix_href") or "")
        when_bit = (
            f'<a class="tps-hit-when" href="{html.escape(when_href, True)}">'
            f"{html.escape(when)}</a>"
            if when_href and when
            else (f'<span class="tps-hit-when">{html.escape(when)}</span>' if when else "")
        )
        items.append(
            '<li class="tagbay-hit">'
            '<div class="tagbay-hit-main">'
            f'<a class="tps-kind" href="{html.escape(title_href, True)}">'
            f"{html.escape(title)}</a>"
            f"{when_bit}"
            "</div></li>"
        )
    return "".join(items)


def _crate_touch_items(crates: list[str], born: str = "") -> str:
    items = []
    for c in crates:
        c = norm_crate(c)
        if not c:
            continue
        door = door_for_crate(c)
        if door is None:
            items.append(
                '<li class="tagbay-hit">'
                '<div class="tagbay-hit-main">'
                f"<code>{html.escape(c)}</code>"
                "</div></li>"
            )
            continue
        facts = lore_facts_for_path(door.get("path"))
        if facts:
            items.append(
                _crate_lore_hit(
                    href=str(door.get("href") or ""),
                    klass=str(facts.get("class") or ""),
                    title=str(facts.get("title") or ""),
                    house=str(facts.get("house") or ""),
                    crate_id=c,
                    pocket=str(door.get("pocket") or ""),
                )
            )
            continue
        items.append(
            '<li class="tagbay-hit">'
            '<div class="tagbay-hit-main">'
            f'{_tagbay_note(str(door.get("href") or "/"), str(door.get("title") or c))}'
            "</div>"
            f"{_tagbay_meta(str(door.get('pocket') or ''), c)}"
            "</li>"
        )
    return "".join(items)


def _crate_report_body(crate: str) -> str:
    spec = CRATE_BAY
    crate = norm_crate(crate)
    if not crate:
        return (
            f'<article class="tagbay {spec["cls"]}">'
            f'<p class="tagbay-void">no crate.</p></article>'
        )
    door = door_for_crate(crate)
    pocket = str((door or {}).get("pocket") or "")
    title = str((door or {}).get("title") or crate)
    href = str((door or {}).get("href") or "")
    path = (door or {}).get("path")
    env = ""
    page_meta: dict = {}
    lore_self: dict | None = None
    fields_lib: list = []
    fields_agent: list = []
    stamps: list = []
    pins: list[str] = []
    threads: list = []
    hashes: list[str] = []
    others: list[Path] = []
    linked: list[Path] = []
    touches: list[str] = []
    born = ""

    lore_all: list[dict] = []
    for mouth in ("librarian", "agent", "charlie"):
        for card in lore_cards_for(mouth, crate):
            item = dict(card)
            item["mouth"] = mouth
            lore_all.append(item)

    faces = faces_of_crate(crate)

    if door is not None and path is not None:
        with using_pocket(pocket):
            target = path if isinstance(path, Path) else resolve_vault_page(pocket)
            if target is not None:
                env = tps_page_env(target)
                page_meta = read_md_meta(target) if target.is_file() else {}
                if is_lore_card(page_meta):
                    lore_self = lore_facts(page_meta, target)
                meta = page_meta
                touches = lore_edge_crates(meta)
                born = norm_crate(str(meta.get("source_crate") or ""))
                touches = [c for c in touches if c != crate]
                with LBR_LOCK:
                    lib_dest = shelf_file("librarian", target)
                    age_dest = shelf_file("agent", target)
                    tps_dest = shelf_file("tps", target)
                    cha_dest = shelf_file("charlie", target)
                    crate_on = bag_crate(shelf_anchor("librarian", target)) or crate
                    if lib_dest is not None:
                        fields_lib = catalog_payload(
                            "librarian", lib_dest, pocket, crate_on
                        ).get("fields") or []
                    if age_dest is not None:
                        fields_agent = catalog_payload(
                            "agent", age_dest, pocket, crate_on
                        ).get("fields") or []
                    if tps_dest is not None:
                        stamps = tps_payload(tps_dest, pocket, crate_on).get("stamps") or []
                    if cha_dest is not None:
                        blot = blot_read(cha_dest, pocket, "CHARLIE")
                        charlie_normalize(blot)
                        pins = [
                            str(t.get("id") or "")
                            for t in (blot.get("thoughts") or [])
                            if str(t.get("id") or "")
                        ]
                        threads = list(blot.get("threads") or [])
                hashes = hashes_on_pocket(pocket)
                stem = target.stem if target.is_file() else ""
                if stem:
                    others, linked = uses_of(stem, target)

    def path_hits(paths: list[Path]) -> list[dict]:
        bags = []
        seen: set[str] = set()
        for p in paths:
            d = door_for_path(p)
            if d is None:
                continue
            pk = str(d.get("pocket") or "")
            if not pk or pk == pocket or pk in seen:
                continue
            seen.add(pk)
            bags.append(d)
        return bags

    also = path_hits(others)
    uses = path_hits(linked)

    chests: list[tuple[str, str, int, str]] = []

    def add_chest(label: str, inner: str, n: int, layout: str = "") -> None:
        if n and inner:
            chests.append((label, inner, n, layout))

    headers = _crate_header_items(page_meta)
    add_chest("headers", headers, headers.count("<li "))
    add_chest("librarian", _crate_field_items("librarian", fields_lib), len(fields_lib))
    add_chest("agent", _crate_field_items("agent", fields_agent), len(fields_agent))
    add_chest("tps", _crate_stamp_items(stamps), len(stamps))
    add_chest("noted on", _crate_lore_items(lore_all), len(lore_all), "is-tiles")
    add_chest("touches", _crate_touch_items(touches, born), len(touches), "is-tiles")
    add_chest("as pin", _crate_word_hits(pins, "tag"), len(pins), "is-chips")
    add_chest("as thread", _crate_thread_items(threads), len(threads))
    add_chest("as hash", _crate_word_hits(hashes, "hash"), len(hashes), "is-chips")
    add_chest("uses", _tagbay_page_hits(uses), len(uses))
    add_chest("also this name", _tagbay_page_hits(also), len(also))
    add_chest("as face", _tagbay_page_hits(faces), len(faces))

    if not chests:
        inner = f'<p class="tagbay-void">{html.escape(spec["empty"])}</p>'
    else:
        inner = "".join(
            _tagbay_chest(label, html_inner, n, layout=layout)
            for label, html_inner, n, layout in chests
        )

    shown = html.escape(title)
    if lore_self:
        shown = html.escape(str(lore_self.get("title") or title))
    if href:
        shown = (
            f'<a class="tagbay-note" href="{html.escape(href, True)}">'
            f"{shown}</a>"
        )
    who = spec["who"]
    skin_cls = spec["cls"]
    before_name = ""
    if lore_self:
        who = _crate_maker_kind(str(lore_self.get("house") or ""))
        skin_cls += " is-lore"
        deck = str(lore_self.get("class") or "").strip()
        card_name = str(lore_self.get("title") or "").strip()
        if deck and card_name and deck.lower() == card_name.lower():
            deck = ""
        if deck:
            before_name = f'<p class="crate-deck">{html.escape(deck)}</p>'
    sub_bits = [crate]
    if env and env.lower() != "lorecard":
        sub_bits.append(env)
    if pocket:
        sub_bits.append(pocket)
    sub = (
        f'<p class="tagbay-sub">{html.escape(" · ".join(sub_bits))}</p>'
        if sub_bits
        else ""
    )
    return (
        f'<article class="tagbay {skin_cls}">'
        '<header class="tagbay-mast">'
        f'<p class="tagbay-sys"><span>{html.escape(spec["brick"])}</span> '
        f"{html.escape(who)}</p>"
        f"{before_name}"
        f"<h1>{shown}<span class=\"tagbay-cursor\" aria-hidden=\"true\"></span></h1>"
        f"{sub}"
        "</header>"
        f"{inner}"
        "</article>"
    )


def crate_report_fragment(qs: dict) -> bytes:
    try:
        return _crate_report_body(crate_id_from_qs(qs)).encode("utf-8")
    except Exception:
        return b'<p class="tagbay-void">could not build this crate report.</p>'


def crate_report_page(qs: dict) -> bytes:
    crate = crate_id_from_qs(qs)
    spec = CRATE_BAY
    door = door_for_crate(crate) if crate else None
    shown = str((door or {}).get("title") or crate or "crate")
    facts = lore_facts_for_path((door or {}).get("path")) if door else None
    if facts:
        shown = str(facts.get("title") or facts.get("class") or shown)
    try:
        body = _crate_report_body(crate)
    except Exception:
        body = '<p class="tagbay-void">could not build this crate report.</p>'
    return sheet_page(
        shown,
        body,
        spec["accent"],
        spec["skin"],
        spec["mark"],
        extra_css=["/tagbay.css"],
        kind="crate",
    )


def host_for_path(p: Path | None) -> Host | None:
    if p is None:
        return None
    try:
        here = p.resolve()
    except OSError:
        return None
    for host in discover_hosts().values():
        try:
            here.relative_to(host.root.resolve())
            return host
        except (OSError, ValueError):
            continue
    return None


def crate_mark_html(crate: str) -> str:
    c = norm_crate(crate)
    if not c:
        return html.escape(str(crate or ""))
    door = door_for_crate(c)
    href = crate_href(c)
    label = html.escape(str((door or {}).get("title") or c))
    return (
        f'<a href="{html.escape(href, True)}">{label}</a>'
        f"<code>{html.escape(c)}</code>"
    )


CARD_META_ORDER = (
    "title",
    "class",
    "house",
    "line",
    "from",
    "source_crate",
    "edges",
    "tps",
    "crate",
    "environment",
    "strip",
    "color",
)


def paint_card_meta(meta: dict | None) -> str:
    """Every held YAML field, for the pop copy. Inbox face stays sparse."""
    meta = meta or {}
    rows: list[str] = []
    seen: set[str] = set()

    def emit(key: object, raw: object) -> None:
        name = str(key or "").strip()
        low = name.lower()
        if not name or low in seen:
            return
        seen.add(low)
        if low == "edges":
            crates = lore_edge_crates(meta)
            if not crates:
                return
            val = "".join(
                f'<span class="card-meta-crate">{crate_mark_html(c)}</span>'
                for c in crates
            )
        elif low in ("crate", "source_crate"):
            c = norm_crate(str(raw or ""))
            if not c:
                return
            val = crate_mark_html(c)
        else:
            text = str(raw or "").strip().strip('"').strip("'")
            if not text or text.startswith("["):
                return
            val = html.escape(text)
        rows.append(
            '<div class="card-meta-row">'
            f"<dt>{html.escape(name)}</dt>"
            f"<dd>{val}</dd>"
            "</div>"
        )

    for key in CARD_META_ORDER:
        emit(key, meta.get(key))
    for key, raw in meta.items():
        emit(key, raw)
    if not rows:
        return ""
    return '<dl class="card-back">' + "".join(rows) + "</dl>"


def attach_card_meta(inner: str, meta: dict | None) -> str:
    back = paint_card_meta(meta)
    if not back:
        return inner
    marked = inner.replace('class="lorecard"', 'class="lorecard has-back"', 1)
    marked = marked.replace("class='lorecard'", 'class="lorecard has-back"', 1)
    close = marked.rfind("</div>")
    if close < 0:
        return marked + back
    return marked[:close] + back + marked[close:]


def paint_card_inner(p: Path, meta: dict, src: str) -> str:
    host = host_for_path(p)
    rel = p.name
    if host is not None:
        try:
            rel = p.relative_to(host.root).as_posix()
        except ValueError:
            rel = p.name

    def _paint() -> str:
        return fill_slots(
            md_lite(src), p.parent, auto=False, crumb_rel=rel, meta=meta
        )

    if host is not None:
        with using_host(host):
            return _paint()
    return _paint()


def paint_lorecard_shelf_item(p: Path) -> str:
    """One traveler-dressed .lorecard for the cards cabinet shelf."""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    meta, src = parse_fm(text)
    if not is_card_note(meta):
        return ""
    meta = dict(meta or {})
    meta["maker"] = card_maker(meta)
    inner = attach_card_meta(paint_card_inner(p, meta, src), meta)
    inner = stamp_lorecard_strip(inner, meta)
    crate = str(meta.get("crate") or "").strip()
    klass = str(meta.get("class") or "").strip()
    title = str(meta.get("title") or p.stem).strip() or p.stem
    crate_attr = f' data-crate="{html.escape(crate, True)}"' if crate else ""
    class_attr = f' data-class="{html.escape(klass, True)}"' if klass else ""
    title_attr = f' data-title="{html.escape(title, True)}"'
    return (
        f'<article class="card-shelf-item"{crate_attr}{class_attr}{title_attr}>'
        f"{inner}</article>"
    )


def cards_shelf_get(pocket_raw: str) -> tuple[int, dict | None, str]:
    """View-only shelf of lore cards attached to the current page/pocket."""
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        target = resolve_vault_page(pocket_raw)
        if target is None:
            return 400, None, "not a vault page"
        pocket = pocket_key(target)
        crate = bag_crate(target)
        route = pocket_key(nearest_index_folder(target) or target)
        seen: set[str] = set()
        cards: list[dict] = []
        bits: list[str] = []
        for mouth in ("librarian", "agent", "charlie", "tps"):
            for card in lore_cards_for(mouth, crate):
                own = str(card.get("crate") or "").strip()
                key = own or f"{mouth}:{card.get('file')}"
                if key in seen:
                    continue
                seen.add(key)
                spec = CATALOG.get(mouth) or {}
                inbox = spec.get("inbox")
                p = None
                fname = str(card.get("file") or "").strip()
                if inbox is not None and fname:
                    cand = inbox / fname
                    if cand.is_file():
                        p = cand
                if p is None and own:
                    p = find_file_by_crate(own)
                painted = paint_lorecard_shelf_item(p) if p is not None else ""
                item = dict(card)
                item["mouth"] = mouth
                item["html"] = painted
                cards.append(item)
                if painted:
                    bits.append(painted)
        shelf_html = (
            '<div class="card-shelf">' + "".join(bits) + "</div>" if bits else ""
        )
        return (
            200,
            {
                "house": "CARDS",
                "pocket": pocket,
                "crate": crate or "",
                "route": route,
                "cards": cards,
                "html": shelf_html,
            },
            "",
        )


def card_pop_page(qs: dict) -> bytes:
    crate = norm_crate(unquote((qs.get("card") or [""])[0]))
    miss = (
        "<p class=\"card-miss\">that card isn't here.</p>"
    )
    p = find_file_by_crate(crate) if crate else None
    if p is None or not p.is_file():
        return sheet_page(
            "lore card",
            miss,
            "#c45c4a",
            "is-lorecard",
            "mypi:card",
            extra_css=["/dress.css", "/styles/lorecard.css"],
            kind="card",
        )
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return sheet_page(
            "lore card",
            miss,
            "#c45c4a",
            "is-lorecard",
            "mypi:card",
            extra_css=["/dress.css", "/styles/lorecard.css"],
            kind="card",
        )
    meta, src = parse_fm(text)
    if not is_card_note(meta):
        return sheet_page(
            "lore card",
            miss,
            "#c45c4a",
            "is-lorecard",
            "mypi:card",
            extra_css=["/dress.css", "/styles/lorecard.css"],
            kind="card",
        )
    inner = attach_card_meta(paint_card_inner(p, meta, src), meta)
    inner = stamp_lorecard_strip(inner, meta)
    strip = css_hex(card_strip_color(meta)) or "#c45c4a"
    return sheet_page(
        card_chrome(meta),
        inner,
        strip,
        "is-lorecard",
        "mypi:card",
        extra_css=["/dress.css", "/styles/lorecard.css"],
        kind="card",
        strip=strip,
    )


def _catalog_bay_article(
    mouth: str, label: str, value: str, inner: str, binning: str = ""
) -> str:
    spec = CATALOG_BAY[mouth]
    word = (value or "").strip()
    shown_label = (label or "").strip() or (word and "word") or "field"
    shown = html.escape(shown_label)
    if word and label:
        shown = (
            f'<a class="tagbay-field" href="{html.escape(catalog_field_href(mouth, label), True)}">'
            f"{html.escape(label)}</a>"
        )
    elif word:
        shown = html.escape(word)
    sub = (
        f'<p class="tagbay-sub">{html.escape(word)}</p>' if word and label else ""
    )
    return (
        f'<article class="tagbay {spec["cls"]}">'
        '<header class="tagbay-mast">'
        f'<p class="tagbay-sys"><span>{html.escape(spec["brick"])}</span> '
        f'{html.escape(spec["who"])}</p>'
        f'<h1>{shown}<span class="tagbay-cursor" aria-hidden="true"></span></h1>'
        f"{sub}"
        f"{_catalog_bin_nav(mouth, label, value, binning) if binning else ''}"
        "</header>"
        f"{inner}"
        "</article>"
    )


def _catalog_bin_nav(mouth: str, label: str, value: str, mode: str) -> str:
    mode = catalog_bin_of(value, mode)
    by_val = "by " + (label.strip() or "value")
    host_on = ' class="is-on"' if mode == "host" else ""
    val_on = ' class="is-on"' if mode == "value" else ""
    return (
        '<p class="tagbay-bin">'
        f'<a data-sheet-stay href="{html.escape(catalog_field_href(mouth, label, value, "host"), True)}"{host_on}>by host</a>'
        f'<a data-sheet-stay href="{html.escape(catalog_field_href(mouth, label, value, "value"), True)}"{val_on}>{html.escape(by_val)}</a>'
        "</p>"
    )


def _catalog_hit_li(
    mouth: str, label: str, value: str, b: dict, hide_vals: bool = False, skip_val: str = ""
) -> str:
    pocket = str(b.get("pocket") or "").lstrip("/")
    title = str(b.get("title") or pocket)
    crate = str(b.get("crate") or "").strip()
    href = str(b.get("href") or href_from_pocket(str(b.get("pocket") or "")))
    vals = [v for v in (b.get("values") or []) if v]
    if skip_val:
        skip = norm_chip(skip_val)
        vals = [v for v in vals if norm_chip(v) != skip]
    extra = "" if hide_vals else _catalog_vals(mouth, label, vals)
    return (
        '<li class="tagbay-hit">'
        '<div class="tagbay-hit-main">'
        f"{_tagbay_note(href, title)}"
        f"{extra}"
        "</div>"
        f"{_tagbay_meta(pocket, crate, off=not crate)}"
        "</li>"
    )


def _catalog_motif_body(mouth: str, label: str, value: str) -> str:
    """A value is a motif: this field, other fields, the other mouth, lore titles."""
    chests: list[str] = []

    def add_field_chests(who: str, prefix: str) -> None:
        groups: dict[str, list[dict]] = {}
        for b in catalog_chip_hits(who, value):
            lab = str(b.get("label") or "").strip() or "field"
            groups.setdefault(lab, []).append(b)
        names: list[str] = []
        if who == mouth and label:
            for k in groups:
                if norm_chip(k) == norm_chip(label):
                    names.append(k)
                    break
        names.extend(sorted(k for k in groups if k not in names))
        for lab in names:
            bags = groups.get(lab) or []
            if not bags:
                continue
            items = [
                _catalog_hit_li(who, lab, value, b, skip_val=value) for b in bags
            ]
            mark = "as " + lab if not prefix else prefix + " · " + lab
            chests.append(_tagbay_chest(mark, "".join(items), len(bags)))

    add_field_chests(mouth, "")
    other = "agent" if mouth == "librarian" else "librarian" if mouth == "agent" else ""
    if other:
        add_field_chests(other, "as " + other)
    lore = lore_motif_hits(value)
    if lore:
        tiles = "".join(
            _crate_lore_hit(
                href=str(card.get("href") or ""),
                klass=str(card.get("class") or ""),
                title=str(card.get("title") or ""),
                house=str(card.get("house") or card.get("mouth") or ""),
                crate_id=str(card.get("crate") or ""),
            )
            for card in lore
        )
        chests.append(_tagbay_chest("as lore", tiles, len(lore), "is-tiles"))
    if not chests:
        inner = f'<p class="tagbay-void">nothing else wears this word.</p>'
    else:
        inner = "".join(chests)
    return _catalog_bay_article(mouth, label, value, inner, "")


def _catalog_body(mouth: str, label: str, value: str, binning: str = "") -> str:
    mouth = (mouth or "librarian").strip().lower()
    if mouth not in CATALOG_BAY:
        mouth = "librarian"
    label = (label or "").strip()
    value = (value or "").strip()
    spec = CATALOG_BAY[mouth]
    if mouth == "tps":
        filt = {label: value} if value else ({label: ""} if label else {})
        filt = {k: v for k, v in filt.items() if k in TPS_FILTER_KEYS and v}
        return _tps_report_body(filt)
    if value:
        return _catalog_motif_body(mouth, label, value)
    bags = catalog_field_hits(mouth, label, value)
    mode = catalog_bin_of(value, binning)
    if not bags:
        return _catalog_bay_article(
            mouth,
            label,
            value,
            f'<p class="tagbay-void">{html.escape(spec["empty"])}</p>',
            mode,
        )
    bins: dict[str, list[dict]] = {}
    shown: dict[str, str] = {}
    if mode == "host":
        for b in bags:
            key = pocket_host_bin(str(b.get("pocket") or ""))
            bins.setdefault(key, []).append(b)
            shown[key] = key

        def sort_key(name: str) -> tuple:
            return (0, name) if name == "start" else (1, name.lower())

    else:
        for b in bags:
            vals = [v for v in (b.get("values") or []) if str(v).strip()]
            if not vals:
                key = ""
                bins.setdefault(key, []).append(b)
                shown[key] = "unfiled"
                continue
            seen_n: set[str] = set()
            for v in vals:
                n = norm_chip(v)
                if not n or n in seen_n:
                    continue
                seen_n.add(n)
                bins.setdefault(n, []).append(b)
                shown.setdefault(n, str(v).strip())

        def sort_key(name: str) -> tuple:
            return (1, "") if name == "" else (0, shown.get(name, name).lower())

    parts = []
    hide_vals = bool(value) and mode == "host"
    for key in sorted(bins, key=sort_key):
        hits = bins[key]
        skip = shown.get(key, key) if mode == "value" else ""
        items = [
            _catalog_hit_li(mouth, label, value, b, hide_vals=hide_vals, skip_val=skip)
            for b in hits
        ]
        parts.append(_tagbay_chest(shown.get(key, key), "".join(items), len(hits)))
    return _catalog_bay_article(mouth, label, value, "".join(parts), mode)


def catalog_field_fragment(mouth: str, label: str, value: str, binning: str = "") -> bytes:
    return _catalog_body(mouth, label, value, binning).encode("utf-8")


def catalog_field_page(mouth: str, label: str, value: str, binning: str = "") -> bytes:
    mouth = (mouth or "librarian").strip().lower()
    if mouth not in CATALOG_BAY:
        mouth = "librarian"
    label = (label or "").strip()
    value = (value or "").strip()
    spec = CATALOG_BAY[mouth]
    shown = (label + ((" · " + value) if value else "")).strip(" ·") or value or mouth
    return sheet_page(
        shown,
        _catalog_body(mouth, label, value, binning),
        spec["accent"],
        spec["skin"],
        spec["mark"],
        extra_css=["/tagbay.css"],
        kind=mouth,
    )


def shelf_get(kind: str, pocket_raw: str) -> tuple[int, dict | None, str]:
    spec = SHELF_KIND.get(kind)
    if not spec:
        return 400, None, "no such shelf"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _shelf_get(kind, pocket_raw, spec)


def _shelf_get(kind: str, pocket_raw: str, spec: dict) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = shelf_file(kind, target)
    if dest is None:
        return 400, None, "not a vault page"
    anchor = shelf_anchor(kind, target)
    pocket = pocket_key(anchor)
    crate = bag_crate(anchor)
    if kind == "tps":
        with LBR_LOCK:
            obj = tps_payload(dest, pocket, crate)
        obj["route"] = pocket_key(nearest_index_folder(target) or target)
        return 200, obj, ""
    if kind in CATALOG and not CATALOG[kind].get("blot"):
        with LBR_LOCK:
            obj = catalog_view(kind, target)
        if obj is None:
            return 400, None, "not a vault page"
        return 200, obj, ""
    with LBR_LOCK:
        obj = blot_read(dest, pocket, spec["house"])
        if kind == "charlie":
            before_ids = [str(t.get("id") or "") for t in (obj.get("thoughts") or [])]
            charlie_normalize(obj)
            after_ids = [str(t.get("id") or "") for t in (obj.get("thoughts") or [])]
            if dest.is_file() and before_ids != after_ids:
                blot_write(dest, obj)
            charlie_decorate(obj, pocket)
    crate = bag_crate(anchor)
    if crate:
        obj["crate"] = crate
    elif not obj.get("crate"):
        obj["crate"] = ""
    if kind == "charlie":
        obj["lore"] = lore_cards_for("charlie", crate or str(obj.get("crate") or ""))
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    return 200, obj, ""


def shelf_add(
    kind: str,
    pocket_raw: str,
    leaf: str,
    frm: str = "",
    rel: str = "",
    to: str = "",
) -> tuple[int, dict | None, str]:
    spec = SHELF_KIND.get(kind)
    if not spec:
        return 400, None, "no such shelf"
    leaf = (leaf or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    frm = str(frm or "").strip()
    rel = str(rel or "").strip()
    to = str(to or "").strip()
    if kind == "charlie":
        if not frm and not rel and not to:
            frm = leaf
        if not charlie_split(frm) and not charlie_split(rel) and not charlie_split(to):
            return 400, None, "empty leaf"
    else:
        if not leaf:
            return 400, None, "empty leaf"
        if len(leaf) > LEAF_MAX:
            return 413, None, "leaf too long"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _shelf_add(kind, pocket_raw, spec, leaf, frm, rel, to)


def _shelf_add(
    kind: str,
    pocket_raw: str,
    spec: dict,
    leaf: str,
    frm: str = "",
    rel: str = "",
    to: str = "",
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = shelf_file(kind, target)
    if dest is None:
        return 400, None, "not a vault page"
    anchor = shelf_anchor(kind, target)
    pocket = pocket_key(anchor)
    crate = bag_crate(anchor)
    marks = parse_sigils(leaf)
    prefix = spec["prefix"]
    with LBR_LOCK:
        obj = blot_read(dest, pocket, spec["house"])
        if crate:
            obj["crate"] = crate
        nxt = int(obj.get("next") or 1)
        if nxt < 1:
            nxt = 1
        if kind == "charlie":
            charlie_normalize(obj)
            issued = charlie_weave(obj, frm, rel, to)
            obj["pocket"] = pocket
            obj["house"] = spec["house"]
            blot_write(dest, obj)
            charlie_decorate(obj, pocket)
            obj["lore"] = lore_cards_for("charlie", crate)
            obj["route"] = pocket_key(nearest_index_folder(target) or target)
            obj["issued"] = issued
            return 200, obj, ""
        thought_id = f"{prefix}-{nxt:04d}"
        thought = {
            "id": thought_id,
            "at": int(time.time()),
            "leaf": leaf,
            "tags": marks["tags"],
            "namespaces": marks["namespaces"],
            "times": marks["times"],
            "cites": marks["cites"],
        }
        thoughts = list(obj.get("thoughts") or [])
        thoughts.insert(0, thought)
        obj["thoughts"] = thoughts
        obj["next"] = nxt + 1
        obj["pocket"] = pocket
        obj["house"] = spec["house"]
        blot_write(dest, obj)
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    return 200, obj, ""


def shelf_update(
    kind: str, pocket_raw: str, thought_id: str, leaf: str
) -> tuple[int, dict | None, str]:
    spec = SHELF_KIND.get(kind)
    if not spec:
        return 400, None, "no such shelf"
    thought_id = (thought_id or "").strip()
    if not thought_id:
        return 400, None, "missing id"
    leaf = (leaf or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not leaf:
        return 400, None, "empty leaf"
    if len(leaf) > LEAF_MAX:
        return 413, None, "leaf too long"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _shelf_update(kind, pocket_raw, spec, thought_id, leaf)


def _shelf_update(
    kind: str, pocket_raw: str, spec: dict, thought_id: str, leaf: str
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = shelf_file(kind, target)
    if dest is None:
        return 400, None, "not a vault page"
    anchor = shelf_anchor(kind, target)
    pocket = pocket_key(anchor)
    crate = bag_crate(anchor)
    marks = parse_sigils(leaf)
    with LBR_LOCK:
        obj = blot_read(dest, pocket, spec["house"])
        if crate:
            obj["crate"] = crate
        found = False
        thoughts = list(obj.get("thoughts") or [])
        for t in thoughts:
            if str(t.get("id") or "") != thought_id:
                continue
            t["leaf"] = leaf
            t["tags"] = marks["tags"]
            t["namespaces"] = marks["namespaces"]
            t["times"] = marks["times"]
            t["cites"] = marks["cites"]
            found = True
            break
        if not found:
            return 404, None, "no such thought"
        obj["thoughts"] = thoughts
        obj["pocket"] = pocket
        obj["house"] = spec["house"]
        blot_write(dest, obj)
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    return 200, obj, ""


def shelf_delete(
    kind: str, pocket_raw: str, thought_id: str, what: str = ""
) -> tuple[int, dict | None, str]:
    spec = SHELF_KIND.get(kind)
    if not spec:
        return 400, None, "no such shelf"
    thought_id = (thought_id or "").strip()
    if not thought_id:
        return 400, None, "missing id"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _shelf_delete(kind, pocket_raw, spec, thought_id, what)


def _shelf_delete(
    kind: str, pocket_raw: str, spec: dict, thought_id: str, what: str = ""
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = shelf_file(kind, target)
    if dest is None:
        return 400, None, "not a vault page"
    anchor = shelf_anchor(kind, target)
    pocket = pocket_key(anchor)
    crate = bag_crate(anchor)
    drop_thread = (what or "").strip().lower() == "thread" or "*" in thought_id
    with LBR_LOCK:
        obj = blot_read(dest, pocket, spec["house"])
        if crate:
            obj["crate"] = crate
        if kind == "charlie":
            charlie_normalize(obj)
            thoughts = list(obj.get("thoughts") or [])
            threads = list(obj.get("threads") or [])
            if drop_thread:
                after_th = [t for t in threads if str(t.get("id") or "") != thought_id]
                if len(after_th) == len(threads):
                    return 404, None, "no such thought"
                obj["threads"] = after_th
            else:
                slug = tag_slug(thought_id)
                after = [t for t in thoughts if str(t.get("id") or "") != slug]
                if len(after) == len(thoughts):
                    return 404, None, "no such thought"
                obj["thoughts"] = after
            thoughts = list(obj.get("thoughts") or [])
            threads = list(obj.get("threads") or [])
            empty = not thoughts and not threads
        else:
            before = list(obj.get("thoughts") or [])
            after = [t for t in before if str(t.get("id") or "") != thought_id]
            if len(after) == len(before):
                return 404, None, "no such thought"
            obj["thoughts"] = after
            empty = not after
        obj["pocket"] = pocket
        obj["house"] = spec["house"]
        if empty and dest.is_file():
            try:
                dest.unlink()
            except OSError:
                blot_write(dest, obj)
        else:
            blot_write(dest, obj)
        if kind == "charlie":
            charlie_decorate(obj, pocket)
    if kind == "charlie":
        obj["lore"] = lore_cards_for("charlie", crate)
    obj["route"] = pocket_key(nearest_index_folder(target) or target)
    return 200, obj, ""


def librarian_get(pocket_raw: str) -> tuple[int, dict | None, str]:
    return shelf_get("librarian", pocket_raw)


def librarian_add(pocket_raw: str, leaf: str) -> tuple[int, dict | None, str]:
    return shelf_add("librarian", pocket_raw, leaf)


def librarian_update(pocket_raw: str, thought_id: str, leaf: str) -> tuple[int, dict | None, str]:
    return shelf_update("librarian", pocket_raw, thought_id, leaf)


def librarian_delete(pocket_raw: str, thought_id: str) -> tuple[int, dict | None, str]:
    return shelf_delete("librarian", pocket_raw, thought_id)


def safe_rel(rel: str) -> Path | None:
    rel = rel.replace("\\", "/").strip("/")
    if not rel or ".." in Path(rel).parts:
        return None
    root = active_vault()
    first = Path(rel).parts[0]
    if is_lobby() and host_slug(first) and (HOSTS_ROOT / first).is_dir():
        return None
    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    if any(part in SKIP for part in target.relative_to(root).parts):
        return None
    return target


def find_media(name: str) -> Path | None:
    raw = name.strip().replace("\\", "/").strip("/")
    if not raw or "://" in raw:
        return None
    found = find_mats_img(raw)
    if found is not None:
        return found
    if "/" in raw:
        target = safe_rel(raw)
        if target is not None and target.is_file() and target.suffix.lower() in IMAGE_EXT:
            return target
    needle = Path(raw).name.lower()
    hits: list[Path] = []
    root = active_vault()
    if root.is_dir():
        walk = root.iterdir() if is_lobby() else root.rglob("*")
        for p in walk:
            if is_lobby():
                continue
            if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:
                continue
            if p.name.lower() != needle:
                continue
            if any(part in SKIP for part in p.relative_to(root).parts):
                continue
            hits.append(p)
    if not hits:
        return None
    hits.sort(key=lambda x: x.as_posix().lower())
    return hits[0]


def media_src(name: str) -> tuple[str, str] | None:
    """Resolved picture href and filename, or None."""
    p = find_media(name)
    if p is None:
        return None
    try:
        p.resolve().relative_to(MATS_IMGS.resolve())
        src = mats_img_href(p)
    except (ValueError, OSError):
        rel = p.relative_to(active_vault()).as_posix()
        src = img_href(rel)
    return src, p.name


def img_tag(name: str, alt: str = "") -> str:
    found = media_src(name)
    if found is None:
        label = html.escape(name.strip() or "picture")
        return f'<span class="pic-miss">[no picture: {label}]</span>'
    src, fname = found
    label = (alt or "").strip() or fname
    return (
        f'<img class="pic" src="{html.escape(src, True)}" '
        f'alt="{html.escape(label, True)}">'
    )


def cover_name(meta: dict | None) -> str:
    meta = meta or {}
    return str(meta.get("cover") or meta.get("jacket") or "").strip()


def cover_art(meta: dict | None, alt: str = "") -> str:
    """Jacket picture only. Empty if cover: is missing or the file is not on the shelf."""
    name = cover_name(meta)
    if not name:
        return ""
    found = media_src(name)
    if found is None:
        return ""
    src, fname = found
    label = (alt or "").strip() or fname
    return (
        f'<img class="pic jacket-art" src="{html.escape(src, True)}" '
        f'alt="{html.escape(label, True)}">'
    )


def jacket_block(meta: dict | None) -> str:
    """Fake cover for this page. Art if cover: resolves; otherwise cloth and title."""
    meta = meta or {}
    title = str(meta.get("title") or "").strip()
    art = cover_art(meta, title)
    if not title and not art and not cover_name(meta):
        return ""
    hue = hue_name(meta)
    classes = ["jacket"]
    if art:
        classes.append("has-cover")
    if hue:
        classes.append(f"hue-{hue}")
    name = html.escape(title or "untitled")
    return (
        f'<figure class="{" ".join(classes)}">'
        f"{art}"
        f'<span class="name">{name}</span>'
        f"</figure>"
    )


def chip_values(field: dict) -> list[str]:
    kind = str(field.get("type") or "input").strip().lower()
    val = field.get("value")
    if kind == "bool":
        return ["yes"] if val in (True, "true", "1", 1, "yes", "on") else ["no"]
    if kind == "time":
        try:
            t = int(val)
            stamp = datetime.fromtimestamp(t)
            if stamp.hour or stamp.minute or stamp.second:
                return [stamp.strftime("%Y-%m-%d %H:%M")]
            return [stamp.strftime("%Y-%m-%d")]
        except (TypeError, ValueError, OSError):
            s = str(val or "").strip()
            return [s] if s else []
    text = ("" if val is None else str(val)).replace("\r\n", "\n").strip()
    if not text:
        return []
    if kind in ("input", "textbox") and ("," in text or ";" in text):
        parts = [p for p in CHIP_SPLIT.split(text) if p]
        return parts or [text]
    return [text]


def slot_page(folder: Path, rel: str | None) -> Path:
    if rel:
        hit = safe_rel(rel)
        if hit is not None and hit.exists():
            return hit
    return folder


def meta_chips(folder: Path, rel: str | None, mouth: str | None = None) -> str:
    """Print this page's catalog as clickable chips. Optional; the drawer is the real shelf."""
    mouth = (mouth or "librarian").strip().lower()
    if mouth not in ("librarian", "agent"):
        mouth = "librarian"
    target = slot_page(folder, rel)
    dest = shelf_file(mouth, target)
    if dest is None:
        return ""
    house = CATALOG[mouth]["house"]
    obj = catalog_read(dest, pocket_key(target), house)
    chips: list[str] = []
    for f in obj.get("fields") or []:
        if not isinstance(f, dict):
            continue
        label = str(f.get("label") or "").strip()
        if not label:
            continue
        label_href = catalog_field_href(mouth, label)
        for value in chip_values(f):
            chips.append(
                '<span class="chip">'
                '<a class="chip-label" href="'
                + html.escape(label_href, True)
                + '">'
                + html.escape(label)
                + '</a><a class="chip-value" href="'
                + html.escape(value_door_href(mouth, label, value), True)
                + '">'
                + html.escape(value)
                + "</a></span>"
            )
    if not chips:
        return ""
    return (
        '<span class="chips chips-'
        + html.escape(mouth, True)
        + '">'
        + "".join(chips)
        + "</span>"
    )


def pocket_bar(rel: str, is_dir: bool = False) -> str:
    host = active_host()
    p = (rel or "").replace("\\", "/").strip("/")
    if p.lower().endswith(".md"):
        p = p[:-3]
    if not host:
        if not p or p.lower() == "start":
            return "start"
        bar = "start/" + p
        if is_dir:
            bar += "/"
        return bar
    if not p:
        return "go." + host + "/"
    bar = "go." + host + "/" + p
    if is_dir:
        bar += "/"
    return bar


def parse_fm(text: str) -> tuple[dict, str]:
    raw = text.replace("\r\n", "\n").lstrip("\ufeff")
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


def read_md_meta(p: Path) -> dict:
    if not p.is_file() or p.suffix.lower() != ".md":
        return {}
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    return parse_fm(text)[0]


def md_list_label(p: Path) -> str:
    """List label: frontmatter title if present, else the filename without .md."""
    title = str(read_md_meta(p).get("title", "")).strip()
    return title or p.stem


def hue_name(meta: dict) -> str:
    raw = str(meta.get("color", "")).strip().lower()
    if raw in COLORS:
        return raw
    for name in COLORS:
        if name in raw.split():
            return name
    return ""


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


def md_row_cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells: list[str] = []
    buf: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "`":
            j = s.find("`", i + 1)
            if j < 0:
                buf.append(s[i:])
                break
            buf.append(s[i : j + 1])
            i = j + 1
            continue
        if ch == "[" and i + 1 < n and s[i + 1] == "[":
            j = s.find("]]", i + 2)
            if j < 0:
                buf.append(ch)
                i += 1
                continue
            buf.append(s[i : j + 2])
            i = j + 2
            continue
        if ch == "\\" and i + 1 < n:
            buf.append(s[i + 1])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def md_sep_aligns(cells: list[str]) -> list[str] | None:
    aligns: list[str] = []
    for c in cells:
        bit = re.sub(r"\s+", "", c)
        if not re.fullmatch(r":?-+:?", bit):
            return None
        left = bit.startswith(":")
        right = bit.endswith(":")
        if left and right:
            aligns.append("center")
        elif right:
            aligns.append("right")
        elif left:
            aligns.append("left")
        else:
            aligns.append("")
    return aligns or None


def md_table_html(lines: list[str], inline) -> str:
    rows = [md_row_cells(ln) for ln in lines]
    if not rows:
        return ""
    aligns: list[str] = []
    head: list[str] = rows[0]
    body = rows[1:]
    if body:
        got = md_sep_aligns(body[0])
        if got is not None:
            aligns = got
            body = body[1:]
        else:
            body = rows
            head = []
    width = max((len(r) for r in rows), default=0)
    if aligns:
        width = max(width, len(aligns))

    def pad(row: list[str]) -> list[str]:
        if len(row) < width:
            return row + [""] * (width - len(row))
        return row[:width]

    def cells(row: list[str], tag: str) -> str:
        bits = []
        for i, text in enumerate(pad(row)):
            al = aligns[i] if i < len(aligns) else ""
            attr = f' class="is-{al}"' if al else ""
            bits.append(f"<{tag}{attr}>" + inline(text) + f"</{tag}>")
        return "".join(bits)

    parts = ['<div class="md-table-wrap"><table class="md-table">']
    if head:
        parts.append("<thead><tr>" + cells(head, "th") + "</tr></thead>")
    if body:
        parts.append("<tbody>")
        for row in body:
            parts.append("<tr>" + cells(row, "td") + "</tr>")
        parts.append("</tbody>")
    parts.append("</table></div>")
    return "".join(parts)


BULLET_KEYS = {
    "": "task",
    ".": "task",
    "x": "done",
    "X": "done",
    ">": "migrated",
    "<": "scheduled",
    "o": "event",
    "O": "event",
    "-": "note",
    "*": "star",
    "/": "progress",
    "!": "bang",
    "?": "ask",
}
BULLET_TOGGLE = frozenset({"task", "done"})
BULLET_BRACKET_RE = re.compile(r"^([-*])(\s+)\[(.{0,2})\](\s*)(.*)$")
BULLET_BARE_RE = re.compile(r"^([-*])(\s+)([.xX><oO\-*\/!?])(?:\s+|$)(.*)$")
BULLET_LIST_RE = re.compile(r"^[-*]\s+")


def bullet_key(inner: str) -> str:
    return BULLET_KEYS.get((inner or "").strip(), "")


def parse_bullet_line(line: str) -> dict | None:
    """Obsidian `- [x] text` or bujo `- x text`. Unknown brackets stay ordinary lists."""
    m = BULLET_BRACKET_RE.match(line)
    if m:
        key = bullet_key(m.group(3))
        if not key:
            return None
        return {
            "style": "bracket",
            "inner": m.group(3),
            "key": key,
            "lead": m.group(1) + m.group(2),
            "gap": m.group(4),
            "rest": m.group(5),
        }
    m = BULLET_BARE_RE.match(line)
    if m:
        key = bullet_key(m.group(3))
        if not key:
            return None
        return {
            "style": "bare",
            "inner": m.group(3),
            "key": key,
            "lead": m.group(1) + m.group(2),
            "gap": " ",
            "rest": m.group(4),
        }
    return None


def format_bullet_line(parsed: dict, inner: str) -> str:
    rest = parsed.get("rest") or ""
    lead = parsed.get("lead") or "- "
    if parsed.get("style") == "bracket":
        gap = parsed.get("gap") if parsed.get("gap") is not None else " "
        if rest and not gap:
            gap = " "
        return f"{lead}[{inner}]{gap}{rest}".rstrip()
    if rest:
        return f"{lead}{inner} {rest}".rstrip()
    return f"{lead}{inner}".rstrip()


def bullet_li_html(
    text: str, cls: str, eid: str, mark: str, index: int | None, inline
) -> str:
    classes = ["bullet", f"is-{mark}"]
    if cls:
        classes.append(cls)
    bits = [f'class="{html.escape(" ".join(classes), True)}"']
    if eid:
        bits.append(f'id="{html.escape(eid, True)}"')
    bits.append(f'data-mark="{html.escape(mark, True)}"')
    if index is not None:
        bits.append(f'data-i="{index}"')
        bits.append('role="checkbox"')
        bits.append(f'aria-checked="{"true" if mark == "done" else "false"}"')
        bits.append('tabindex="0"')
    return f"<li {' '.join(bits)}>" + inline(text) + "</li>"


def iter_toggle_bullets(body: str):
    """Same skip rules as md_lite: fences, quotes, tables. Yields (line_index, parsed)."""
    fence = False
    for i, line in enumerate((body or "").replace("\r\n", "\n").split("\n")):
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if line.lstrip().startswith(">") or line.lstrip().startswith("|"):
            continue
        parsed = parse_bullet_line(line)
        if parsed and parsed["key"] in BULLET_TOGGLE:
            yield i, parsed


def toggle_nth_bullet(body: str, index: int) -> tuple[str, bool]:
    lines = (body or "").replace("\r\n", "\n").split("\n")
    for n, (i, parsed) in enumerate(iter_toggle_bullets(body)):
        if n != index:
            continue
        inner = "x" if parsed["key"] == "task" else "."
        lines[i] = format_bullet_line(parsed, inner)
        return "\n".join(lines), True
    return body, False


def bullet_toggle(pocket_raw: str, index) -> tuple[int, dict | None, str]:
    try:
        n = int(index)
    except (TypeError, ValueError):
        return 400, None, "no such bullet"
    if n < 0:
        return 400, None, "no such bullet"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _bullet_toggle(pocket_raw, n)


def _bullet_toggle(pocket_raw: str, index: int) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = page_note_file(target)
    if dest is None or not dest.is_file() or dest.suffix.lower() != ".md":
        return 400, None, "not a note"
    with LBR_LOCK:
        try:
            text = dest.read_text(encoding="utf-8")
        except OSError:
            return 500, None, "could not read note"
        raw = text.replace("\r\n", "\n")
        head, body = "", raw
        if raw.startswith("---\n"):
            end = raw.find("\n---\n", 4)
            if end >= 0:
                head = raw[: end + 5]
                body = raw[end + 5 :]
        new_body, found = toggle_nth_bullet(body, index)
        if not found:
            return 404, None, "no such bullet"
        out = head + new_body
        if not out.endswith("\n"):
            out += "\n"
        try:
            dest.write_text(out, encoding="utf-8")
        except OSError:
            return 500, None, "could not write note"
    return 200, {"ok": True, "i": index}, ""


def md_lite(src: str) -> str:
    lines = src.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    buf: list[str] = []
    open_divs = 0

    fence: list[str] | None = None
    table: list[str] | None = None
    in_quote = False
    in_list = False
    bullet_i = 0

    def end_quote() -> None:
        nonlocal in_quote
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

    def end_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def start_list() -> None:
        nonlocal in_list
        if not in_list:
            out.append('<ul class="bullets">')
            in_list = True

    def flush() -> None:
        if not buf:
            return
        para, cls, eid = take_dress("\n".join(buf))
        out.append(f"<p{html_attrs(cls, eid)}>" + inline(para) + "</p>")
        buf.clear()

    def flush_fence() -> None:
        nonlocal fence
        if fence is None:
            return
        body = html.escape("\n".join(fence))
        out.append(f"<pre class='code'><code>{body}</code></pre>")
        fence = None

    def flush_table() -> None:
        nonlocal table
        if table is None:
            return
        out.append(md_table_html(table, inline))
        table = None

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
        s = OUTLINK_RE.sub(
            lambda m: hold(outlink_html(m.group(1), m.group(2) or "")),
            s,
        )
        s = IMG_MD_RE.sub(
            lambda m: hold(img_tag(m.group(2), m.group(1) or "")),
            s,
        )
        s = re.sub(
            r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
            lambda m: hold(
                f'<a class="wiki" href="{html.escape(wiki_href(m.group(1)), True)}">'
                f"{html.escape(m.group(2) or m.group(1))}</a>"
            ),
            s,
        )
        s = TAG_RE.sub(lambda m: hold(tag_chip(m.group(1))), s)
        s = CITE_CRATE_RE.sub(lambda m: hold(crate_cite_chip(m.group(1))), s)
        s = SPAN_RE.sub(
            lambda m: hold(f"<span{html_attrs(*parse_spec(m.group(1)))}>")
            + m.group(2)
            + hold("</span>"),
            s,
        )
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"~~(.+?)~~", r"<del>\1</del>", s)
        return re.sub(r"\x00@(\d+)@\x00", lambda m: held[int(m.group(1))], s)

    for line in lines:
        if fence is not None:
            if line.strip().startswith("```"):
                flush_fence()
            else:
                fence.append(line)
            continue
        if line.strip().startswith("```"):
            end_quote()
            end_list()
            flush()
            flush_table()
            fence = []
            continue
        if line.lstrip().startswith("|"):
            end_quote()
            end_list()
            flush()
            if table is None:
                table = []
            table.append(line)
            continue
        flush_table()
        quoted = line.lstrip().startswith(">")
        if quoted:
            end_list()
            flush()
            if not in_quote:
                out.append('<blockquote class="window">')
                in_quote = True
            q = re.sub(r"^\s*>\s?", "", line)
            if q.strip():
                text, cls, eid = take_dress(q)
                out.append(f"<p{html_attrs(cls, eid)}>" + inline(text) + "</p>")
            continue
        end_quote()
        raw = line.strip()
        if FACE_CRATE_RE.fullmatch(raw) or raw in (
            "{{images}}",
            "{{slides}}",
            "{{files}}",
            "{{spines}}",
            "{{doors}}",
            "{{worlds}}",
            "{{dir}}",
            "{{list}}",
            "{{faces}}",
            "{{cards}}",
            "{{cover}}",
            "{{jacket}}",
        ):
            end_list()
            flush()
            out.append(raw)
            continue
        opened = DIV_OPEN.match(raw)
        if opened:
            end_list()
            flush()
            out.append(f"<div{html_attrs(*parse_spec(opened.group(1)))}>")
            open_divs += 1
            continue
        if DIV_CLOSE.match(raw):
            end_list()
            flush()
            if open_divs:
                out.append("</div>")
                open_divs -= 1
            continue
        hm = HEADING_RE.match(line)
        if hm:
            end_list()
            flush()
            n = min(max(len(hm.group(1)), 1), 5)
            text, cls, eid = take_dress(hm.group(2).strip())
            out.append(f"<h{n}{html_attrs(cls, eid)}>" + inline(text) + f"</h{n}>")
        elif line.strip() == "---":
            end_list()
            flush()
            out.append("<hr>")
        elif BULLET_LIST_RE.match(line):
            flush()
            start_list()
            parsed = parse_bullet_line(line)
            if parsed:
                text, cls, eid = take_dress(parsed["rest"])
                mark = parsed["key"]
                idx = None
                if mark in BULLET_TOGGLE:
                    idx = bullet_i
                    bullet_i += 1
                out.append(bullet_li_html(text, cls, eid, mark, idx, inline))
            else:
                text, cls, eid = take_dress(re.sub(r"^[-*]\s+", "", line))
                out.append(f"<li{html_attrs(cls, eid)}>" + inline(text) + "</li>")
        elif not line.strip():
            end_list()
            flush()
        else:
            end_list()
            buf.append(line)
    flush()
    flush_fence()
    flush_table()
    end_quote()
    end_list()
    while open_divs:
        out.append("</div>")
        open_divs -= 1
    return "\n".join(out)


def iter_notes() -> list[Path]:
    root = active_vault()
    if not root.is_dir():
        return []
    out: list[Path] = []
    hide = {INDEX_NAME, PAPER_NAME, START_NAME, "readme.md"}
    if is_lobby():
        for p in root.iterdir():
            if not p.is_file() or p.suffix.lower() != ".md":
                continue
            if p.name in SKIP or stash_name(p.name):
                continue
            if p.name.lower() in hide:
                continue
            out.append(p)
        return out
    for p in root.rglob("*.md"):
        if any(part in SKIP or stash_name(part) for part in p.relative_to(root).parts):
            continue
        if p.name.lower() in {INDEX_NAME, PAPER_NAME}:
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
        f'<a class="tag" href="{html.escape(tag_href(slug), True)}">'
        f"#{html.escape(slug)}</a>"
    )


def crate_cite_chip(raw: str) -> str:
    c = norm_crate(raw)
    if not c:
        return html.escape("^" + str(raw or ""))
    return (
        f'<a class="cite" href="{html.escape(crate_href(c), True)}">'
        f"^{html.escape(c)}</a>"
    )


def wiki_target(raw: str) -> str:
    """Stem for wiki lookup. Colon and [RP] fold to the same hyphen stem as the file."""
    t = raw.strip().replace("\\", "/")
    t = t.split("/")[-1].strip().lower()
    t = t.replace(":", "-")
    t = re.sub(r"\s*\[([^\]]+)\]", r"-\1", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t


def hall_wiki_hits(needle: str) -> list[Path]:
    """Rooms wiki may name: the folder, or the title on that folder's paper/shell.

    Stem `index` / `_index` stays off — that would hit every hall.
    """
    if not needle or needle in {"index", "_index"}:
        return []
    root = active_vault()
    if not root.is_dir() or is_lobby():
        return []
    hits: list[Path] = []
    seen: set[str] = set()

    def consider(hall: Path) -> None:
        names = {wiki_target(hall.name)}
        dest: Path | None = None
        for fname in (PAPER_NAME, INDEX_NAME):
            f = hall / fname
            if not f.is_file():
                continue
            if dest is None:
                dest = f
            title = str(read_md_meta(f).get("title") or "").strip()
            if title:
                names.add(wiki_target(title))
        if hall == root:
            host = active_host()
            if host:
                names.add(wiki_target(host))
        if needle not in names:
            return
        dest = dest or hall
        try:
            key = str(dest.resolve())
        except OSError:
            key = str(dest)
        if key in seen:
            return
        seen.add(key)
        hits.append(dest)

    consider(root)
    for p in root.rglob("*"):
        if not p.is_dir():
            continue
        try:
            parts = p.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP or stash_name(part) for part in parts):
            continue
        consider(p)
    return hits


def wiki_hit_label(p: Path) -> str:
    if p.is_dir():
        return p.name
    if p.name.lower() in {INDEX_NAME, PAPER_NAME}:
        return str(read_md_meta(p).get("title") or "").strip() or p.parent.name
    return p.stem


def wiki_hit_rel(p: Path) -> str:
    if p.is_file() and p.name.lower() in {INDEX_NAME, PAPER_NAME}:
        try:
            if p.parent.resolve() == active_vault().resolve():
                return ""
        except OSError:
            pass
        try:
            return p.parent.relative_to(active_vault()).as_posix()
        except ValueError:
            return p.parent.name
    rel = p.relative_to(active_vault()).as_posix()
    if p.is_file() and rel.lower().endswith(".md"):
        return rel[:-3]
    return rel.strip("/")


def hit_list(paths: list[Path]) -> str:
    if not paths:
        return "<p>none.</p>"
    items = []
    for p in sorted(paths, key=lambda x: x.as_posix().lower()):
        rel = wiki_hit_rel(p)
        label = wiki_hit_label(p)
        shown = rel or (active_host() or p.name)
        items.append(
            f'<li><a href="{html.escape(page_href(rel), True)}">{html.escape(label)}</a>'
            f'<span class="hit-path">{html.escape(shown)}</span></li>'
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
        rel = p.relative_to(active_vault()).as_posix()[:-3].lower()
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
    for p in hall_wiki_hits(needle):
        if p not in exact:
            exact.append(p)
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
    return page(
        f"[[{query}]]",
        "\n".join(bits),
        "#6e6254",
        "query",
        pocket_bar(""),
        librarian=False,
    )


def notes_with_tag(slug: str) -> list[Path]:
    needle = tag_slug(slug)
    if not needle:
        return []
    hits: list[Path] = []
    for p in iter_notes():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = parse_fm(text)
        tags = {
            tag_slug(t)
            for k, v in meta.items()
            if k.lower() in ("tags", "tag")
            for t in split_tags(str(v))
        }
        tags.update(tag_slug(m.group(1)) for m in TAG_RE.finditer(body))
        for blob in (
            str(meta.get("line") or ""),
            str(meta.get("title") or ""),
        ):
            tags.update(tag_slug(m.group(1)) for m in TAG_RE.finditer(blob))
        tags.discard("")
        if needle in tags:
            hits.append(p)
    return hits


def _pocket_same(a: str, b: str) -> bool:
    x = str(a or "").replace("\\", "/").strip().strip("/")
    y = str(b or "").replace("\\", "/").strip().strip("/")
    if not x or not y:
        return False
    return x.lower() == y.lower()


def hashes_on_pocket(pocket: str) -> list[str]:
    """#words printed on this note: YAML tags: and body hashes. Not Charlie pins."""
    if not pocket:
        return []
    with using_pocket(pocket) as host:
        if host is None and str(pocket).strip("/") not in ("", "/"):
            return []
        target = resolve_vault_page(pocket)
        if target is None:
            return []
        if target.is_dir():
            paper = target / PAPER_NAME
            note = target / START_NAME if is_lobby() else None
            if paper.is_file():
                target = paper
            elif note is not None and note.is_file():
                target = note
            else:
                return []
        if not target.is_file() or target.suffix.lower() != ".md":
            return []
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        meta, body = parse_fm(text)
        out: list[str] = []
        seen: set[str] = set()
        for k, v in meta.items():
            if k.lower() not in ("tags", "tag"):
                continue
            for t in split_tags(str(v)):
                s = tag_slug(t)
                if s and s not in seen:
                    seen.add(s)
                    out.append(s)
        for m in TAG_RE.finditer(body):
            s = tag_slug(m.group(1))
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        for blob in (
            str(meta.get("line") or ""),
            str(meta.get("title") or ""),
        ):
            for m in TAG_RE.finditer(blob):
                s = tag_slug(m.group(1))
                if s and s not in seen:
                    seen.add(s)
                    out.append(s)
        return out


def hashes_for_word(slug: str) -> list[dict]:
    """Body #hashes and YAML tags: across every host, same word as Charlie lookup."""
    needle = tag_slug(slug)
    if not needle:
        return []
    hits: list[dict] = []
    seen: set[str] = set()
    hosts = [lobby_host()] + list(discover_hosts().values())
    for host in hosts:
        with using_host(host):
            for p in notes_with_tag(needle):
                pocket = pocket_key(p)
                if not pocket or pocket in seen:
                    continue
                seen.add(pocket)
                hits.append(
                    {
                        "pocket": pocket,
                        "title": pocket_title(pocket) or p.stem,
                        "href": href_from_pocket(pocket) if host.name else page_href(
                            p.relative_to(active_vault()).as_posix()
                        ),
                        "crate": file_crate(p),
                    }
                )
    return hits


def tag_page(slug: str) -> bytes:
    return charlie_tag_page(slug)


def fm_inline(s: str) -> str:
    held: list[str] = []

    def hold(bit: str) -> str:
        held.append(bit)
        return f"\x00@{len(held) - 1}@\x00"

    s = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda m: hold(
            f'<a class="wiki" href="{html.escape(wiki_href(m.group(1)), True)}">'
            f"{html.escape(m.group(2) or m.group(1))}</a>"
        ),
        s,
    )
    s = TAG_RE.sub(lambda m: hold(tag_chip(m.group(1))), s)
    s = CITE_CRATE_RE.sub(lambda m: hold(crate_cite_chip(m.group(1))), s)
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
    rows = "".join(
        fm_row(k, str(v))
        for k, v in meta.items()
        if k.lower() != "crate" and not str(k).lower().endswith("_href")
    )
    if not rows:
        return ""
    return (
        "<details class='headers'>"
        "<summary>headers</summary>"
        f"<dl class='fm'>{rows}</dl>"
        "</details>"
    )


def is_vault_root(folder: Path) -> bool:
    try:
        return folder.resolve() == active_vault().resolve()
    except OSError:
        return False


def load_index(folder: Path) -> tuple[dict, str] | None:
    p = folder / INDEX_NAME
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    return parse_fm(text)


def nearest_index_folder(page: Path | None) -> Path | None:
    """Closest folder that has _index.md, walking up. The room letter hangs here."""
    if page is None:
        return None
    cur = page
    try:
        if cur.is_file():
            cur = cur.parent
    except OSError:
        return None
    try:
        vault = active_vault().resolve()
        cur = cur.resolve()
    except OSError:
        return None
    while True:
        if (cur / INDEX_NAME).is_file():
            return cur
        if is_vault_root(cur):
            return cur
        parent = cur.parent
        if parent == cur:
            return cur
        try:
            cur.relative_to(vault)
        except ValueError:
            return None
        cur = parent


def nearest_index_title(folder: Path | None) -> str:
    """Closest _index.md title walking up from this folder (the shell, not vault root)."""
    if folder is None:
        return ""
    cur = folder
    try:
        if cur.is_file():
            cur = cur.parent
    except OSError:
        cur = active_vault()
    while True:
        loaded = load_index(cur)
        if loaded:
            t = str(loaded[0].get("title", "")).strip()
            if t:
                return t
        if is_vault_root(cur):
            break
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return active_host()


def header_label(host: str, page_title: str) -> str:
    """Window bar: nearest _index title, then this page's title."""
    site = str(host or "").strip()
    page = str(page_title or "").strip()
    if not page:
        return site or active_host()
    if not site or site == page:
        return page
    return f"{site} | {page}"


def visible_kids(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    kids = []
    for p in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if p.name in SKIP or stash_name(p.name):
            continue
        if p.name.lower() == PAPER_NAME:
            continue
        if is_lobby() and p.name.lower() in {START_NAME, "readme.md"}:
            continue
        if p.is_dir() or p.suffix.lower() in {".md", ".canvas"}:
            kids.append(p)
    return kids


def door_slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s if s and ENV_NAME.fullmatch(s) else ""


def door_cards(folder: Path) -> str:
    """Folder doors. On lobby/start, title + deck come from each host's shell front matter."""
    cards = []
    i = 0
    for w in visible_kids(folder):
        if not w.is_dir():
            continue
        i += 1
        n = sum(
            1
            for _ in w.rglob("*.md")
            if not any(
                stash_name(part) or part in SKIP for part in _.relative_to(w).parts
            )
            and _.name.lower() not in {INDEX_NAME, PAPER_NAME}
        )
        slug = door_slug(w.name)
        classes = ["world", f"door-n{i}"]
        if slug:
            classes.append(f"door-{slug}")
        meta: dict = {}
        loaded = load_index(w)
        if loaded:
            meta = loaded[0] or {}
        label = str(meta.get("title") or "").strip() or w.name
        deck = ""
        for key in ("deck", "blurb", "lede", "description", "summary"):
            raw = str(meta.get(key) or "").strip()
            if raw:
                deck = raw
                break
        bits = [f"<strong>{html.escape(label)}</strong>"]
        if deck:
            bits.append(f"<span class='door-deck'>{html.escape(deck)}</span>")
            classes.append("has-deck")
        bits.append(f"<span class='note-details'>{n}</span>")
        cards.append(
            f'<a class="{html.escape(" ".join(classes), True)}" href="{html.escape(kid_href(w), True)}" '
            f'data-door="{html.escape(w.name, True)}">'
            + "".join(bits)
            + "</a>"
        )
    if not cards:
        return "<p>no folders here.</p>"
    return "<div class='worlds'>" + "".join(cards) + "</div>"


def folder_images(folder: Path) -> list[Path]:
    """Image files in this folder only. Same hide rules as notes. No recurse."""
    if not folder.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(folder.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_file():
            continue
        if p.name in SKIP or stash_name(p.name):
            continue
        if p.suffix.lower() in IMAGE_EXT:
            out.append(p)
    return out


def slides_block(folder: Path) -> str:
    pics = folder_images(folder)
    if not pics:
        return "<p>no pictures here.</p>"

    def src_for(p: Path) -> str:
        return img_href(p.relative_to(active_vault()).as_posix())

    n = len(pics)
    first = pics[0]
    first_src = src_for(first)
    first_name = first.name
    rail = []
    for i, p in enumerate(pics):
        src = src_for(p)
        on = " on" if i == 0 else ""
        rail.append(
            f'<li><button type="button" class="slides-thumb{on}" data-i="{i}" '
            f'data-src="{html.escape(src, True)}" data-name="{html.escape(p.name, True)}">'
            f'<img src="{html.escape(src, True)}" alt="" loading="lazy"></button></li>'
        )
    nav = ""
    if n > 1:
        nav = (
            '<p class="slides-nav">'
            '<button type="button" class="slides-prev">prev</button>'
            '<button type="button" class="slides-next">next</button>'
            "</p>"
        )
    rail_html = (
        f'<ol class="slides-rail{" one" if n < 2 else ""}">{"".join(rail)}</ol>'
    )
    return (
        f'<div class="slides" data-slides tabindex="0">'
        f'<figure class="slides-frame">'
        f'<img class="pic slides-pic" src="{html.escape(first_src, True)}" '
        f'alt="{html.escape(first_name, True)}">'
        f'<figcaption class="slides-meta">'
        f'<span class="slides-cap">{html.escape(first_name)}</span>'
        f'<span class="slides-n">1 / {n}</span>'
        f"</figcaption></figure>"
        f"{nav}{rail_html}</div>"
    )


def file_list(folder: Path, kind: str = "files", extra: str = "", here: str = "") -> str:
    items = []
    face_up = extra != "spines"
    here_n = (here or "").replace("\\", "/").strip("/").lower()
    for p in visible_kids(folder):
        if kind == "files" and p.is_dir():
            continue
        if kind == "dirs" and not p.is_dir():
            continue
        mark = "/" if p.is_dir() else ""
        classes: list[str] = []
        art = ""
        try:
            rel = p.relative_to(active_vault()).as_posix()
        except ValueError:
            rel = p.name
        if here_n and rel.replace("\\", "/").strip("/").lower() == here_n:
            classes.append("on")
        if p.is_dir():
            label = p.name
        else:
            meta = read_md_meta(p)
            label = str(meta.get("title", "")).strip() or p.stem
            hue = hue_name(meta)
            if hue:
                classes.append(f"hue-{hue}")
            if face_up:
                art = cover_art(meta, label)
                if art:
                    classes.append("has-cover")
        cls_attr = f' class="{html.escape(" ".join(classes), True)}"' if classes else ""
        items.append(
            f'<li><a{cls_attr} href="{html.escape(kid_href(p), True)}">'
            f"{art}"
            f'<span class="name">{html.escape(label)}{mark}</span></a></li>'
        )
    if not items:
        if kind == "files":
            return "<p>no notes here.</p>"
        if kind == "dirs":
            return "<p>no folders here.</p>"
        return "<p>empty.</p>"
    ul = "dir" + (f" {extra}" if extra else "")
    return f"<ul class='{html.escape(ul, True)}'>" + "".join(items) + "</ul>"


def norm_crate(raw: str) -> str:
    s = (raw or "").strip()
    if s.lower().startswith("crate."):
        s = s[6:]
    s = re.sub(r"[^A-Fa-f0-9]", "", s).upper()
    return ("crate." + s) if len(s) == 16 else ""


def find_file_by_crate(crate: str) -> Path | None:
    """Any host note whose YAML crate matches. Crate ids are unique."""
    crate = norm_crate(crate)
    if not crate:
        return None
    roots: list[Path] = []
    for host in discover_hosts().values():
        if host.root.is_dir():
            roots.append(host.root)
    start = HOSTS_ROOT / START_NAME
    if start.is_file():
        if norm_crate(file_crate(start)) == crate:
            return start
    for root in roots:
        if not root.is_dir():
            continue
        for p in root.rglob("*.md"):
            try:
                rel_parts = p.relative_to(root).parts
            except ValueError:
                continue
            if any(part in SKIP or stash_name(part) for part in rel_parts):
                continue
            if norm_crate(file_crate(p)) == crate:
                return p
    return None


def paint_face(path: Path, meta: dict | None = None, src: str | None = None) -> str:
    if meta is None or src is None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        meta, src = parse_fm(text)
    meta = dict(meta or {})
    meta["maker"] = card_maker(meta)
    inner = stamp_lorecard_strip(fill_fields(md_lite(src), meta), meta)
    crate = str(meta.get("crate") or "").strip()
    klass = str(meta.get("class") or "").strip()
    stem = html.escape(path.stem, True)
    crate_attr = f' data-crate="{html.escape(crate, True)}"' if crate else ""
    class_attr = f' data-class="{html.escape(klass, True)}"' if klass else ""
    card_attr = ' data-card="1"' if is_card_note(meta) else ""
    door = door_for_path(path)
    href = str((door or {}).get("href") or "").strip() or kid_href(path)
    href_attr = f' data-href="{html.escape(href, True)}"' if href else ""
    strip = css_hex(card_strip_color(meta)) if is_card_note(meta) else ""
    style = f' style="--card-strip:{strip}"' if strip else ""
    door_bits = ' role="link" tabindex="0"' if href else ""
    return (
        f'<article class="face" data-face="{stem}"{crate_attr}{class_attr}{card_attr}{href_attr}'
        f"{style}{door_bits}>{inner}</article>"
    )


def face_deck_key(meta: dict | None) -> str:
    """The label a card sorts under — class first, then untitled."""
    meta = meta or {}
    klass = str(meta.get("class") or "").strip()
    if klass:
        return klass
    if is_card_note(meta):
        return "unfiled"
    return ""


def face_list(folder: Path) -> str:
    """Print each note as a face. Cards group under their class label, A-Z."""
    rows: list[tuple[str, str, str, Path, dict, str]] = []
    for p in visible_kids(folder):
        if not p.is_file() or p.suffix.lower() != ".md":
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = parse_fm(text)
        painted = paint_face(p, meta, body)
        if not painted:
            continue
        deck = face_deck_key(meta)
        title = str(meta.get("title") or p.stem).strip() or p.stem
        rows.append((deck.lower(), title.lower(), p.name.lower(), p, meta, painted))
    if not rows:
        return "<p>no notes here.</p>"
    rows.sort(key=lambda r: (r[0] == "", r[0], r[1], r[2]))
    chunks: list[str] = []
    current: str | None = None
    opened = False
    for deck_l, _title_l, _name_l, _p, meta, painted in rows:
        deck = face_deck_key(meta)
        if not opened or deck != current:
            if opened:
                chunks.append("</section>")
            current = deck
            opened = True
            if deck:
                label = html.escape(deck)
                chunks.append(
                    f'<section class="face-deck" data-class="{label}">'
                    f'<h2 class="face-deck-label">{label}</h2>'
                )
            else:
                chunks.append('<section class="face-deck is-loose">')
        chunks.append(painted)
    if opened:
        chunks.append("</section>")
    return '<div class="faces">' + "".join(chunks) + "</div>"



TRAY_MOUTHS = ("librarian", "agent", "charlie", "tps")


def tray_mouth_of(path: Path | None) -> str:
    """Which go.trays mouth this path lives under, else ''."""
    if path is None:
        return ""
    try:
        here = path.resolve()
        root = TRAYS_HOST.resolve()
        rel = here.relative_to(root)
    except (OSError, ValueError):
        return ""
    parts = rel.parts
    if not parts:
        return ""
    mouth = str(parts[0] or "").strip().lower()
    return mouth if mouth in TRAY_MOUTHS else ""


def paint_tray_rail(folder: Path, current: Path | None) -> str:
    """Quiet index of sibling cards — class + title only, not mini pages."""
    rows: list[tuple[str, str, str, Path, dict]] = []
    cur = None
    try:
        cur = current.resolve() if current is not None else None
    except OSError:
        cur = current
    for p in visible_kids(folder):
        if not p.is_file() or p.suffix.lower() != ".md":
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, _body = parse_fm(text)
        if not is_card_note(meta):
            continue
        klass = str(meta.get("class") or "").strip()
        title = str(meta.get("title") or p.stem).strip() or p.stem
        rows.append((klass.lower(), title.lower(), p.name.lower(), p, meta))
    if not rows:
        return '<p class="tray-rail-empty">.</p>'
    rows.sort(key=lambda r: (r[0] == "", r[0], r[1], r[2]))
    bits: list[str] = ['<nav class="tray-index" aria-label="tray">']
    for _k, _t, _n, p, meta in rows:
        here = False
        if cur is not None:
            try:
                here = p.resolve() == cur
            except OSError:
                here = p == current
        door = door_for_path(p)
        href = str((door or {}).get("href") or "").strip() or kid_href(p)
        klass = str(meta.get("class") or "").strip()
        title = str(meta.get("title") or p.stem).strip() or p.stem
        strip = css_hex(card_strip_color(meta)) if is_card_note(meta) else ""
        style = f' style="--card-strip:{strip}"' if strip else ""
        cls = "tray-index-item is-here" if here else "tray-index-item"
        bits.append(
            f'<a class="{cls}" href="{html.escape(href, True)}"{style}>'
            f'<span class="tray-index-class">{html.escape(klass or "·")}</span>'
            f'<span class="tray-index-title">{html.escape(title)}</span>'
            f"</a>"
        )
    bits.append("</nav>")
    return "".join(bits)


def paint_tray_hinterland(meta: dict | None, current: Path | None = None) -> str:
    """Readable edge marks under the stage: where this card is also referenced."""
    meta = meta or {}
    crates = lore_edge_crates(meta)
    if not crates:
        return ""
    cur_crate = norm_crate(str(meta.get("crate") or ""))
    cur_key = ""
    if current is not None:
        try:
            cur_key = str(current.resolve())
        except OSError:
            cur_key = ""

    def _where_for(p: Path, door: dict | None) -> str:
        host = str((door or {}).get("host") or (door or {}).get("h") or "").strip()
        rel = ""
        try:
            # pocket path under ~hosts/<host>/...
            parts = list(p.parts)
            if "~hosts" in parts:
                i = parts.index("~hosts")
                host = host or (parts[i + 1] if i + 1 < len(parts) else "")
                rest = parts[i + 2 :] if i + 2 <= len(parts) else []
                if rest:
                    rel = "/".join(rest[:-1]) if len(rest) > 1 else ""
        except Exception:
            pass
        room = str((door or {}).get("room") or (door or {}).get("title") or "").strip()
        bits = [b for b in (host, rel or room) if b]
        return " / ".join(bits) if bits else (host or "elsewhere")

    bits: list[str] = []
    for c in crates:
        if c == cur_crate:
            continue
        p = find_file_by_crate(c)
        if p is not None and p.is_file():
            try:
                if cur_key and str(p.resolve()) == cur_key:
                    continue
            except OSError:
                pass
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                text = ""
            m, _body = parse_fm(text) if text else ({}, "")
            door = door_for_path(p)
            href = str((door or {}).get("href") or "").strip() or kid_href(p)
            title = str((m or {}).get("title") or (door or {}).get("title") or p.stem).strip()
            where = _where_for(p, door if isinstance(door, dict) else None)
            bits.append(
                f'<a class="tray-slip" href="{html.escape(href, True)}">'
                f'<span class="tray-slip-where">{html.escape(where)}</span>'
                f'<span class="tray-slip-title">{html.escape(title or c)}</span>'
                f"</a>"
            )
            continue
        door = door_for_crate(c)
        if door is None:
            continue
        href = html.escape(str(door.get("href") or ""), True)
        title = html.escape(str(door.get("title") or c))
        where = html.escape(str(door.get("host") or door.get("h") or "elsewhere"))
        bits.append(
            f'<a class="tray-slip" href="{href}">'
            f'<span class="tray-slip-where">{where}</span>'
            f'<span class="tray-slip-title">{title}</span>'
            f"</a>"
        )
    if not bits:
        return ""
    return (
        '<aside class="tray-hinterland">'
        '<span class="tray-hinter-label">Also referenced on</span>'
        '<div class="tray-hinter-list">'
        + "".join(bits)
        + "</div></aside>"
    )



def wrap_tray_room(inner: str, path: Path, meta: dict | None) -> str:
    """Dress an open lore card as still-in-the-tray: stage + rail + mouth + hinterland."""
    if not is_card_note(meta):
        return inner
    mouth = tray_mouth_of(path)
    if not mouth:
        return inner
    folder = path.parent
    rail = paint_tray_rail(folder, path)
    hinter = paint_tray_hinterland(meta, path)
    mouth_e = html.escape(mouth)
    trays_href = html.escape("/?h=trays", True)
    mouth_href = html.escape(f"/?h=trays&p={mouth}", True)
    return (
        f'<div class="tray-room" data-mouth="{mouth_e}">'
        f'<header class="tray-mouth" data-mouth="{mouth_e}">'
        f'<nav class="tray-mouth-crumbs" aria-label="tray path">'
        f'<a class="tray-mouth-up" href="{trays_href}">trays</a>'
        f'<span class="tray-mouth-sep" aria-hidden="true">/</span>'
        f'<a class="tray-mouth-name" href="{mouth_href}">{mouth_e}</a>'
        f"</nav>"
        f"</header>"
        f'<div class="tray-stage">{inner}</div>'
        f'<aside class="tray-rail" data-mouth="{mouth_e}">{rail}</aside>'
        f"{hinter}"
        f"</div>"
    )


def print_crate_face(raw_id: str) -> str:
    crate = norm_crate(raw_id)
    if not crate:
        return '<span class="pic-miss">[no crate]</span>'
    p = find_file_by_crate(crate)
    if p is None:
        return (
            f'<span class="pic-miss">[no crate: {html.escape(crate)}]</span>'
        )
    return paint_face(p)


def fill_fields(body: str, meta: dict | None) -> str:
    meta = meta or {}
    by_low = {str(k).lower(): v for k, v in meta.items()}

    def lookup(name: str):
        if name in meta:
            return meta[name]
        return by_low.get(name.lower())

    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key.lower() == "edges":
            return paint_lore_edges(meta)
        if key.lower() in SLOT_NAMES:
            return m.group(0)
        raw = lookup(key)
        if raw is None:
            return ""
        text = str(raw or "").strip()
        painted = fm_inline(text) if text else ""
        href = str(lookup(key + "_href") or "").strip()
        if painted and href.startswith("/") and not href.startswith("//"):
            return (
                f'<a class="wiki" href="{html.escape(href, True)}">{painted}</a>'
            )
        outside = outlink_html(href, text) if painted and href else ""
        if outside:
            return outside
        return painted

    return FIELD_TOKEN.sub(repl, body)


def flip_sibs(folder: Path, rel: str) -> tuple[Path | None, Path | None]:
    """The note before and the note after this one, in the order the lists show."""
    here = (rel or "").replace("\\", "/").strip("/")
    if not here.lower().endswith(".md"):
        return None, None
    seat = safe_rel(here)
    room = seat.parent if (seat is not None and seat.is_file()) else folder
    notes = [p for p in visible_kids(room) if not p.is_dir()]
    at = -1
    for i, p in enumerate(notes):
        try:
            r = p.relative_to(active_vault()).as_posix()
        except ValueError:
            r = p.name
        if r.replace("\\", "/").strip("/").lower() == here.lower():
            at = i
            break
    if at < 0:
        return None, None
    back = notes[at - 1] if at > 0 else None
    on = notes[at + 1] if at + 1 < len(notes) else None
    return back, on


def flip_link(p: Path | None, way: str) -> str:
    """One step along the shelf. A dead end still prints, so a layout keeps its shape."""
    if p is None:
        return f'<span class="flip {way} none"><span class="way">{way}</span></span>'
    meta = read_md_meta(p)
    name = str(meta.get("title", "")).strip() or p.stem
    return (
        f'<a class="flip {way}" href="{html.escape(kid_href(p), True)}">'
        f'<span class="way">{way}</span>'
        f'<span class="name">{html.escape(name)}</span></a>'
    )


def fill_slots(
    body: str,
    folder: Path,
    auto: bool = True,
    crumb_rel: str | None = None,
    meta: dict | None = None,
) -> str:
    rel = (
        crumb_rel
        if crumb_rel is not None
        else ("" if is_vault_root(folder) else folder.relative_to(active_vault()).as_posix())
    )
    doors = door_cards(folder)
    notes = file_list(folder, "files", extra="files", here=rel)
    spines = file_list(folder, "files", extra="spines", here=rel)
    listing = file_list(folder, "all", here=rel)
    had = False
    if "{{doors}}" in body or "{{worlds}}" in body:
        body = body.replace("{{doors}}", doors).replace("{{worlds}}", doors)
        had = True
    if "{{files}}" in body:
        body = body.replace("{{files}}", notes)
        had = True
    if "{{spines}}" in body:
        body = body.replace("{{spines}}", spines)
        had = True
    if "{{dir}}" in body or "{{list}}" in body:
        body = body.replace("{{dir}}", listing).replace("{{list}}", listing)
        had = True
    if "{{images}}" in body or "{{slides}}" in body:
        show = slides_block(folder)
        body = body.replace("{{images}}", show).replace("{{slides}}", show)
        had = True
    if "{{cover}}" in body or "{{jacket}}" in body:
        jacket = jacket_block(meta)
        body = body.replace("{{cover}}", jacket).replace("{{jacket}}", jacket)
    if "{{prev}}" in body or "{{next}}" in body or "{{flip}}" in body:
        back_p, on_p = flip_sibs(folder, rel)
        back = flip_link(back_p, "prev")
        on = flip_link(on_p, "next")
        body = body.replace("{{prev}}", back).replace("{{next}}", on)
        body = body.replace("{{flip}}", f'<nav class="flipper">{back}{on}</nav>')
    if META_SLOT_RE.search(body):
        def _meta_slot(m: re.Match[str]) -> str:
            who = (m.group(1) or "librarian").lower()
            return meta_chips(folder, crumb_rel, who)

        body = META_SLOT_RE.sub(_meta_slot, body)
    if "{{edges}}" in body:
        body = body.replace("{{edges}}", paint_lore_edges(meta or {}))
    if "{{headers}}" in body:
        body = body.replace("{{headers}}", headers_block(meta or {}))
    need_faces = "{{faces}}" in body or "{{cards}}" in body
    if need_faces:
        had = True
    body = fill_fields(body, meta)
    if need_faces:
        faces = face_list(folder)
        body = body.replace("{{faces}}", faces).replace("{{cards}}", faces)
    if FACE_CRATE_RE.search(body):
        body = FACE_CRATE_RE.sub(lambda m: print_crate_face(m.group(1)), body)
    body = place_crumb(body, rel, folder, meta)
    if auto and not had:
        body = body + "\n" + (doors if is_vault_root(folder) else listing)
    return body


def paper_off(meta: dict) -> bool:
    return str(meta.get("shell", "")).strip().lower() in {
        "none",
        "off",
        "no",
        "false",
        "0",
    }


def has_paper_slot(src: str) -> bool:
    return "{{paper}}" in src or "{{insertdata}}" in src


def load_paper(folder: Path) -> tuple[dict, str] | None:
    p = folder / PAPER_NAME
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    return parse_fm(text)


def find_shell(folder: Path) -> tuple[Path, dict, str] | None:
    cur = folder
    while True:
        loaded = load_index(cur)
        if loaded:
            meta, src = loaded
            if not paper_off(meta) and has_paper_slot(src):
                return cur, meta, src
        if is_vault_root(cur):
            return None
        parent = cur.parent
        if parent == cur:
            return None
        cur = parent


def place_paper(shell_html: str, inner: str) -> str:
    if not PAPER_HOLE.search(shell_html):
        return shell_html
    return PAPER_HOLE.sub(lambda _m: inner, shell_html, count=1)


SHELL_OWN = {"crate", "shell"}


def shell_dress(shell_meta: dict | None, page_meta: dict | None) -> dict:
    """What a shell's tokens read: the open page's front matter over the room's own."""
    dress = dict(shell_meta or {})
    for k, v in (page_meta or {}).items():
        if k in SHELL_OWN or v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        dress[k] = v
    return dress


def wear_shell(
    shell_src: str,
    shell_folder: Path,
    inner: str,
    page_rel: str,
    shell_meta: dict | None = None,
    page_meta: dict | None = None,
) -> str:
    dressed = fill_slots(
        md_lite(shell_src),
        shell_folder,
        auto=False,
        crumb_rel=page_rel,
        meta=shell_dress(shell_meta, page_meta),
    )
    return place_paper(dressed, inner)


def wrap_in_shell(folder: Path, inner: str, page_rel: str, meta: dict | None = None) -> tuple[str, dict | None]:
    if meta and paper_off(meta):
        return inner, None
    if is_card_note(meta):
        return inner, None
    found = find_shell(folder)
    if not found:
        return inner, None
    shell_folder, shell_meta, shell_src = found
    return wear_shell(shell_src, shell_folder, inner, page_rel, shell_meta, meta), shell_meta


def sight_stage(here: Path) -> None:
    """Mint a crate on every vault page on stage (.md / .canvas). Shell and paper stay distinct."""
    seen: set[str] = set()

    def one(p: Path | None) -> None:
        if p is None or not p.is_file():
            return
        try:
            key = str(p.resolve())
        except OSError:
            key = str(p)
        if key in seen:
            return
        seen.add(key)
        ensure_crate(p)

    if here.is_file():
        one(here)
        folder = here.parent
    else:
        folder = here
        one(folder / INDEX_NAME)
        one(folder / PAPER_NAME)
        one(lobby_start(folder))
    found = find_shell(folder)
    if found:
        one(found[0] / INDEX_NAME)


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
    return (
        "<details class='uses'>"
        "<summary>uses</summary>"
        + "".join(bits)
        + "</details>"
    )


def fill_uses(body: str, name: str, current: Path) -> str:
    has_slot = "{{uses}}" in body or "{{bags}}" in body
    block = uses_block(name, current, empty=has_slot)
    if has_slot:
        body = body.replace("{{uses}}", block).replace("{{bags}}", block)
    elif block:
        body = body + "\n" + block
    rel = current.relative_to(active_vault()).as_posix()
    here = current.parent if current.is_file() else current
    return place_crumb(body, rel, here)


def crumb_part_label(part: str) -> str:
    return part[:-3] if part.lower().endswith(".md") else part


def folder_crumbs(rel: str) -> str:
    home = f'<a href="{html.escape(page_href(""), True)}">home</a>'
    if not rel:
        return home
    parts = Path(rel.replace("\\", "/")).parts
    rest = "/".join(
        f'<a href="{html.escape(page_href("/".join(parts[: i + 1])), True)}">'
        f"{html.escape(crumb_part_label(part))}</a>"
        for i, part in enumerate(parts)
    )
    return home + "/" + rest


def crumb_folder(rel: str, folder: Path | None = None) -> Path:
    if folder is not None:
        return folder
    if not rel:
        return active_vault()
    target = active_vault() / rel.replace("\\", "/")
    if target.suffix.lower() == ".md" or target.is_file():
        return target.parent
    return target


def crumb_join(parts: tuple[str, ...], start: int = 0) -> str:
    return "/".join(
        f'<a href="{html.escape(page_href("/".join(parts[: i + 1])), True)}">'
        f"{html.escape(crumb_part_label(part))}</a>"
        for i, part in enumerate(parts)
        if i >= start
    )


def shell_crumbs(rel: str, folder: Path | None = None, meta: dict | None = None) -> str:
    """Trail from the nearest paper-shell folder to here. No shell → full {{crumb}} trail."""
    here = crumb_folder(rel, folder)
    found = None if (meta and paper_off(meta)) else find_shell(here)
    if not found or is_vault_root(found[0]):
        return folder_crumbs(rel)
    shell_rel = found[0].relative_to(active_vault()).as_posix()
    parts = Path(rel.replace("\\", "/")).parts if rel else ()
    shell_parts = Path(shell_rel.replace("\\", "/")).parts
    if not parts or parts[: len(shell_parts)] != shell_parts:
        return folder_crumbs(rel)
    return crumb_join(parts, start=len(shell_parts) - 1)


def crumb_back_name(folder: Path) -> str:
    """Parent label for a backlink: paper title, then shell title, then the folder name."""
    if is_vault_root(folder):
        return "home"
    for loaded in (load_paper(folder), load_index(folder)):
        if not loaded:
            continue
        t = str(loaded[0].get("title", "")).strip()
        if t:
            return t
    return folder.name


def crumb_back(rel: str) -> str:
    parts = Path(rel.replace("\\", "/")).parts if rel else ()
    if not parts:
        return ""
    parent_rel = "/".join(parts[:-1])
    folder = active_vault() if not parent_rel else (active_vault() / parent_rel)
    href = page_href("") if not parent_rel else page_href(parent_rel)
    return f'<a class="crumbback" href="{html.escape(href, True)}">{html.escape(crumb_back_name(folder))}</a>'


def home_link(rel: str, folder: Path | None = None) -> str:
    """Door to the nearest `_index.md` walking up. Vault root if none."""
    here = crumb_folder(rel, folder)
    dest = nearest_index_folder(here) or active_vault()
    if is_vault_root(dest):
        href = page_href("")
    else:
        try:
            href = page_href(dest.relative_to(active_vault()).as_posix())
        except ValueError:
            href = page_href("")
    return (
        f'<a class="home" href="{html.escape(href, True)}">'
        f"{html.escape(crumb_back_name(dest))}</a>"
    )


def place_crumb(
    body: str,
    rel: str,
    folder: Path | None = None,
    meta: dict | None = None,
) -> str:
    nav = f'<nav class="crumb">{folder_crumbs(rel)}</nav>'
    if "{{crumb}}" in body or "{{bread}}" in body:
        body = body.replace("{{crumb}}", nav).replace("{{bread}}", nav)
    if "{{shellcrumb}}" in body:
        body = body.replace(
            "{{shellcrumb}}",
            f'<nav class="shellcrumb">{shell_crumbs(rel, folder, meta)}</nav>',
        )
    if "{{crumbback}}" in body:
        body = body.replace("{{crumbback}}", crumb_back(rel))
    if "{{home}}" in body or "{{root}}" in body:
        door = home_link(rel, folder)
        body = body.replace("{{home}}", door).replace("{{root}}", door)
    return body


def render_folder(folder: Path) -> bytes:
    sight_stage(folder)
    rel = "" if is_vault_root(folder) else folder.relative_to(active_vault()).as_posix()
    extras = ["/index.css"] if (SYS / "index.css").is_file() else []
    loaded = load_index(folder)
    paper = load_paper(folder)
    crumb = folder_crumbs(rel)
    bar = pocket_bar(rel, True)

    if loaded and has_paper_slot(loaded[1]) and not paper_off(loaded[0]):
        shell_meta, shell_src = loaded
        inner = ""
        inner_meta: dict = {}
        if paper:
            inner_meta, inner_src = paper
            inner = fill_slots(
                md_lite(inner_src), folder, auto=False, crumb_rel=rel, meta=inner_meta
            )
        title = (
            str(inner_meta.get("title") or "").strip()
            or str(shell_meta.get("title") or "").strip()
            or (folder.name if rel else "root")
        )
        env = inner_meta.get("environment") or shell_meta.get("environment")
        body = wear_shell(shell_src, folder, inner, rel, shell_meta, inner_meta)
        return page(
            title,
            body,
            accent_for(rel, inner_meta or shell_meta),
            crumb,
            bar,
            env,
            extras,
            here=folder,
            vault=pocket_key(folder),
        )

    meta: dict = {}
    if loaded:
        meta, src = loaded
        title = meta.get("title") or (folder.name if rel else "root")
        body = fill_slots(md_lite(src), folder, meta=meta)
        env = meta.get("environment")
    elif paper:
        meta, src = paper
        title = meta.get("title") or (folder.name if rel else "root")
        body = fill_slots(md_lite(src), folder, auto=False, crumb_rel=rel, meta=meta)
        env = meta.get("environment")
    elif not rel:
        spec = _CURRENT_HOST.get()
        title = (spec.title if spec else "") or active_host()
        body = f"<h1>{html.escape(title)}</h1>" + door_cards(folder)
        env = None
    else:
        title = folder.name
        body = f"<h1>{html.escape(folder.name)}</h1>" + file_list(folder, "all")
        env = None

    body, shell_meta = wrap_in_shell(folder, body, rel, meta)
    if shell_meta:
        env = env or shell_meta.get("environment")
    return page(
        title,
        body,
        accent_for(rel, meta),
        crumb,
        bar,
        env,
        extras,
        here=folder,
        vault=pocket_key(folder),
    )


def page(
    title: str,
    body: str,
    accent: str,
    crumb: str,
    bar: str = "/",
    environment: str | None = None,
    extra_css: list[str] | None = None,
    here: Path | None = None,
    vault: str | None = None,
    librarian: bool = True,
    body_class: str = "",
    mark: str = "mypi:go",
    chrome: str | None = None,
    strip: str | None = None,
    extra_js: list[str] | None = None,
) -> bytes:
    shown = (chrome or "").strip() or header_label(nearest_index_title(here), title)
    skin = env_name(environment)
    extra = ""
    if skin:
        extra += f'<link rel="stylesheet" href="/styles/{html.escape(skin, True)}.css">\n'
    extra += '<link rel="stylesheet" href="/librarian.css">\n'
    for href in extra_css or []:
        extra += f'<link rel="stylesheet" href="{html.escape(href, True)}">\n'
    html_attrs = f'data-pocket="{html.escape(bar, True)}"'
    if librarian and vault is not None:
        vault_attr = vault if str(vault).strip("/") else "/"
        html_attrs += f' data-vault="{html.escape(vault_attr, True)}"'
        if here is not None:
            route_folder = nearest_index_folder(here)
            if route_folder is not None:
                route = pocket_key(route_folder).lstrip("/")
                html_attrs += f' data-route="{html.escape(route, True)}"'
    else:
        html_attrs += ' data-librarian="off"'
    body_attr = f' class="{html.escape(body_class, True)}"' if body_class else ""
    extra_scripts = ""
    for href in extra_js or []:
        extra_scripts += f'<script src="{html.escape(href, True)}"></script>\n'
    root = f"--note-accent: {accent};"
    hue = css_hex(strip or "")
    hue_css = f"<style>:root {{ --card-strip: {hue}; }}</style>\n" if hue else ""
    html_out = f"""<!doctype html>
<html lang="en" {html_attrs}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(shown)}</title>
<link rel="stylesheet" href="/www.css">
<link rel="stylesheet" href="/dress.css">
<style>:root {{ {root} }}</style>
{extra}{hue_css}</head>
<body{body_attr}>
<header class="wwwExplorer_chrome" data-deck-chrome>
  <div class="wwwExplorer_windowTitleBar" data-deck-drag>
    <button type="button" class="wwwExplorer_mark" data-deck-menu title="Menu">{html.escape(mark)}</button>
    <span class="wwwExplorer_title" data-deck-drag>{html.escape(shown)}</span>
    <div class="wwwExplorer_win" data-deck-window-controls aria-label="Window"></div>
  </div>
  <div class="wwwExplorer_linkBar">
    <button type="button" data-webbar="back" title="Back" aria-label="Back">
      <svg viewBox="0 0 16 16" aria-hidden="true"><polygon points="11,2.5 4,8 11,13.5"/></svg>
    </button>
    <button type="button" data-webbar="forward" title="Forward" aria-label="Forward">
      <svg viewBox="0 0 16 16" aria-hidden="true"><polygon points="5,2.5 12,8 5,13.5"/></svg>
    </button>
    <button type="button" data-webbar="home" title="Home" aria-label="Home">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8 L8 2.5 L14 8"/><path d="M4.2 7.5 V13.2 H7 V10 H9 V13.2 H11.8 V7.5"/></svg>
    </button>
    <button type="button" id="REFRESH" data-webbar="refresh"
            title="Refresh · Shift/Ctrl+click = hard refresh" aria-label="Refresh">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 8a5 5 0 1 1-1.4-3.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><polygon points="13.5,1.5 13.8,6.2 9.2,5.2"/></svg>
    </button>
    <span id="wwwBar" class="linkSlug" spellcheck="false" title="click to type · Enter or GO">{html.escape(bar)}</span>
    <button type="button" id="GO" data-webbar="go">GO!</button>
  </div>
</header>
<div class="wwwExplorer_stage">
<div class="wwwExplorer_innerShell">
  <main id="browserWindow">
{body}
  </main>
</div>
</div>
<footer class="wwwExplorer_status"><span id="wwwStatus">Done</span></footer>
<script src="/www.js"></script>
<script src="/librarian.js"></script>
{extra_scripts}</body></html>"""
    return html_out.encode("utf-8")



def canvas_page(target: Path, rel: str) -> bytes:
    """Read-only Obsidian .canvas board viewer."""
    raw = target.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"nodes": [], "edges": [], "_error": "invalid canvas json"}
    if not isinstance(data, dict):
        data = {"nodes": [], "edges": []}
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    payload = json.dumps(data, ensure_ascii=False)
    # Embed as text inside script — escape </script> breakouts
    safe = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("</", "<\\/")
    title = target.stem.replace("-", " ").replace("_", " ").strip() or "canvas"
    body = (
        '<div class="canvas-shell">'
        '<div class="canvas-toolbar">'
        f"<span>{html.escape(title)}</span>"
        '<button type="button" id="canvas-fit">fit</button>'
        '<button type="button" id="canvas-zoom-out">-</button>'
        '<span id="canvas-zoom-label">100%</span>'
        '<button type="button" id="canvas-zoom-in">+</button>'
        '<span style="opacity:.6;margin-left:auto">pan · wheel zoom · read-only</span>'
        "</div>"
        '<div id="canvas-viewport" class="canvas-viewport">'
        '<div id="canvas-world" class="canvas-world"></div>'
        "</div>"
        f'<script type="application/json" id="canvas-data">{safe}</script>'
        "</div>"
    )
    return page(
        title,
        body,
        "#2a3f3d",
        folder_crumbs(rel),
        pocket_bar(rel),
        environment="canvas",
        extra_css=["/canvas.css"],
        here=target.parent,
        vault=pocket_key(target),
        librarian=True,
        body_class="is-canvas",
        mark="mypi:canvas",
        extra_js=["/canvas.js"],
    )


def sheet_page(
    title: str,
    body: str,
    accent: str,
    body_class: str,
    mark: str,
    extra_css: list[str] | None = None,
    kind: str = "crate",
    strip: str | None = None,
) -> bytes:
    """Lookup window: a report sheet. No www address bar, no explorer, no DESK."""
    extra = ""
    for href in extra_css or []:
        extra += f'<link rel="stylesheet" href="{html.escape(href, True)}">\n'
    shown = html.escape(title)
    sheet = html.escape((kind or "crate").strip().lower() or "crate")
    root = f"--note-accent: {accent};"
    hue = css_hex(strip or "")
    hue_css = f"<style>:root {{ --card-strip: {hue}; }}</style>\n" if hue else ""
    html_out = f"""<!doctype html>
<html lang="en" data-librarian="off" data-sheet="{sheet}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{shown}</title>
<link rel="stylesheet" href="/www.css">
<style>:root {{ {root} }}</style>
{extra}{hue_css}</head>
<body class="{html.escape(body_class, True)} is-sheet">
<header class="sheet-cap" data-deck-chrome data-deck-controls="min,close">
  <div class="sheet-cap-bar" data-deck-drag>
    <span class="sheet-cap-mark">{html.escape(mark)}</span>
    <span class="sheet-cap-title" data-deck-drag>{shown}</span>
    <div class="wwwExplorer_win" data-deck-window-controls aria-label="Window"></div>
  </div>
</header>
<main id="browserWindow" class="sheet-face">
{body}
</main>
<script src="/librarian.js"></script>
</body></html>"""
    return html_out.encode("utf-8")


def missing_host_page(name: str) -> bytes:
    slug = host_slug(name) or (name or "???").strip()
    shown = "go." + slug
    body = (
        f"<h1>{html.escape(shown)}</h1>"
        "<p>that room isn't in the pocket yet!! "
        "a folder under ~hosts with that name makes the door. "
        "it isn't missing forever. it just isn't here <em>now</em>.</p>"
    )
    return page(shown, body, "#6e6254", shown, shown + "/", "www", librarian=False)


SIDECAR_HOUSES = {
    "readme": ("README", "#0000aa", "mypi:readme"),
    "librarian": ("LIBRARIAN", "#2a3f3d", "mypi:lib"),
    "charlie": ("CHARLIE", "#1a1204", "mypi:bay"),
    "agent": ("AGENT", "#140808", "mypi:hunt"),
    "tps": ("TPS", "#2a2c28", "mypi:tps"),
    "cards": ("CARDS", "#3a3226", "mypi:deck"),
}


def sidecar_page(house: str) -> bytes:
    """Second window for one blotter. Follows the deck's vault path."""
    title, accent, brick = SIDECAR_HOUSES[house]
    card_css = (
        '''<link rel="stylesheet" href="/dress.css">\n'''
        '''<link rel="stylesheet" href="/styles/lorecard.css">\n'''
        if house == "cards"
        else ""
    )
    grip = (
        '<div class="sheet-resize" aria-label="Resize"></div>\n'
        if house == "readme"
        else ""
    )
    html_out = f"""<!doctype html>
<html lang="en" data-sidecar="{html.escape(house, True)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="/www.css">
<style>:root {{ --note-accent: {accent}; }}</style>
<link rel="stylesheet" href="/librarian.css">
{card_css}</head>
<body class="is-sidecar">
<header class="wwwExplorer_chrome" data-deck-chrome data-deck-controls="min,close">
  <div class="wwwExplorer_windowTitleBar" data-deck-drag>
    <button type="button" class="wwwExplorer_mark" data-deck-menu title="Menu">{html.escape(brick)}</button>
    <span class="wwwExplorer_title" id="sidecarTitle" data-deck-drag>{html.escape(title)}</span>
    <div class="wwwExplorer_win" data-deck-window-controls aria-label="Window"></div>
  </div>
</header>
<div class="wwwExplorer_stage"></div>
{grip}<script src="/librarian.js"></script>
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

    def remember_desk(self) -> None:
        href = desk_href_from_url(self.path)
        if href:
            last_save(href)

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
                "start": str(HOSTS_ROOT / START_NAME),
                "hosts": sorted(discover_hosts().keys()),
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
        if u.path == "/api/last":
            self.send_bytes(
                json.dumps({"href": last_load()}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path in ("/api/readme", "/api/rules"):
            qs = parse_qs(u.query)
            pocket = unquote((qs.get("p") or [""])[0])
            code, obj, err = readme_get(pocket)
            if obj is None:
                self.send_bytes(
                    json.dumps({"error": err}).encode("utf-8"),
                    "application/json; charset=utf-8",
                    code,
                )
                return
            self.send_bytes(
                json.dumps(obj).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path in ("/api/librarian/lore", "/api/agent/lore", "/api/charlie/lore", "/api/tps/lore"):
            mouth = u.path.split("/")[2]
            code, obj, err = catalog_lore_list(mouth)
            if obj is None:
                self.send_bytes(
                    json.dumps({"error": err}).encode("utf-8"),
                    "application/json; charset=utf-8",
                    code,
                )
                return
            self.send_bytes(
                json.dumps(obj).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path in ("/api/librarian/suggest", "/api/agent/suggest", "/api/charlie/suggest"):
            mouth = u.path.split("/")[2]
            self.send_bytes(
                json.dumps(suggest_get(mouth)).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/tps/suggest":
            self.send_bytes(
                json.dumps({"titles": tps_suggest_load()}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/cards":
            qs = parse_qs(u.query)
            pocket = unquote((qs.get("p") or [""])[0])
            code, obj, err = cards_shelf_get(pocket)
            if obj is None:
                self.send_bytes(
                    json.dumps({"error": err}).encode("utf-8"),
                    "application/json; charset=utf-8",
                    code,
                )
                return
            self.send_bytes(
                json.dumps(obj).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/tps":
            qs = parse_qs(u.query)
            pocket = unquote((qs.get("p") or [""])[0])
            code, obj, err = shelf_get("tps", pocket)
            if obj is None:
                self.send_bytes(
                    json.dumps({"error": err}).encode("utf-8"),
                    "application/json; charset=utf-8",
                    code,
                )
                return
            self.send_bytes(
                json.dumps(obj).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path in CATALOG_API:
            qs = parse_qs(u.query)
            pocket = unquote((qs.get("p") or [""])[0])
            code, obj, err = shelf_get(CATALOG_API[u.path], pocket)
            if obj is None:
                self.send_bytes(
                    json.dumps({"error": err}).encode("utf-8"),
                    "application/json; charset=utf-8",
                    code,
                )
                return
            self.send_bytes(
                json.dumps(obj).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path in SHELF_API:
            qs = parse_qs(u.query)
            pocket = unquote((qs.get("p") or [""])[0])
            code, obj, err = shelf_get(SHELF_API[u.path], pocket)
            if obj is None:
                self.send_bytes(
                    json.dumps({"error": err}).encode("utf-8"),
                    "application/json; charset=utf-8",
                    code,
                )
                return
            self.send_bytes(
                json.dumps(obj).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path.startswith("/i/"):
            raw = unquote(u.path[len("/i/") :]).strip("/")
            mats_hit = find_mats_img(raw)
            if mats_hit is not None:
                ctype = IMAGE_TYPE.get(mats_hit.suffix.lower(), "application/octet-stream")
                self.send_bytes(mats_hit.read_bytes(), ctype)
                return
            name, path = split_pocket(raw)
            img_host = get_host(name)
            if img_host is None:
                self.send_error(404)
                return
            with using_host(img_host):
                target = safe_rel(path)
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
        if u.path == "/" and blank_home_qs(qs) and take_launch_restore():
            dest = last_load()
            if dest and dest != "/":
                self.send_response(302)
                self.send_header("Location", dest)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
        if "sidecar" in qs:
            house = (qs.get("sidecar") or [""])[0].strip().lower()
            if house not in SIDECAR_HOUSES:
                self.send_error(404)
                return
            self.send_html(sidecar_page(house))
            return
        if "card" in qs:
            self.send_html(card_pop_page(qs))
            return
        if crate_qs_is_report(qs):
            if "bay" in qs:
                self.send_html(crate_report_fragment(qs))
                return
            if "h" not in qs and "p" not in qs:
                self.send_html(crate_report_page(qs))
                return
        if "c" in qs or "t" in qs:
            word = (qs.get("c") or qs.get("t") or [""])[0]
            crate = norm_crate(word)
            if crate:
                dest = crate_href(crate)
                if "bay" in qs:
                    dest += "&bay=1"
                self.send_response(302)
                self.send_header("Location", dest)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            role = (qs.get("as") or [""])[0]
            if "bay" in qs:
                here = (qs.get("here") or [""])[0]
                self.send_html(charlie_tag_fragment(word, here, role))
                return
            if "h" not in qs and "p" not in qs:
                self.send_html(charlie_tag_page(word, role))
                return
        if tps_qs_is_report(qs):
            if "bay" in qs:
                self.send_html(tps_report_fragment(qs))
                return
            if "h" not in qs and "p" not in qs:
                self.send_html(tps_report_page(qs))
                return
        if catalog_qs_is_report(qs):
            mouth, label, value, binning = catalog_from_qs(qs)
            if "bay" in qs:
                self.send_html(catalog_field_fragment(mouth, label, value, binning))
                return
            if "h" not in qs and "p" not in qs:
                self.send_html(catalog_field_page(mouth, label, value, binning))
                return
        host_name, rel = parse_request_pocket(qs)
        host = get_host(host_name)
        if host is None:
            self.send_html(missing_host_page(host_name), 404)
            return
        with using_host(host):
            self.serve_vault(qs, rel)

    def serve_vault(self, qs: dict, rel: str) -> None:
        if "q" in qs:
            q = qs["q"][0]
            exact, nearby, linked = lookup_wiki(q)
            if len(exact) == 1:
                hit = exact[0]
                rel_hit = wiki_hit_rel(hit)
                self.send_response(302)
                self.send_header("Location", page_href(rel_hit))
                self.end_headers()
                return
            self.send_html(wiki_page(q, exact, nearby, linked))
            self.remember_desk()
            return
        if crate_qs_is_report(qs):
            self.send_html(crate_report_page(qs))
            return
        if tps_qs_is_report(qs):
            self.send_html(tps_report_page(qs))
            return
        if catalog_qs_is_report(qs):
            mouth, label, value, binning = catalog_from_qs(qs)
            self.send_html(catalog_field_page(mouth, label, value, binning))
            return
        if "t" in qs:
            self.send_html(tag_page(qs["t"][0]))
            return
        if not rel:
            start = active_vault() / START_NAME
            if is_lobby() and start.is_file():
                target = start
            else:
                self.send_html(self.index())
                self.remember_desk()
                return
        else:
            target = safe_rel(rel)
            if (target is None or not target.exists()) and not rel.lower().endswith(".md"):
                alt = safe_rel(rel + ".md")
                if alt is not None and alt.exists():
                    target = alt
                    rel = rel + ".md"
        if target is None or not target.exists():
            self.send_html(page("missing", "<p>gone.</p>", "#6e6254", rel, pocket_bar(rel), librarian=False), 404)
            return
        if target.is_file() and target.name.lower() in {INDEX_NAME, PAPER_NAME}:
            parent = target.parent
            self.send_html(self.index() if is_vault_root(parent) else self.listing(parent))
            self.remember_desk()
            return
        if target.is_dir():
            self.send_html(self.listing(target))
            self.remember_desk()
            return
        if target.suffix.lower() == ".md":
            sight_stage(target)
            text = target.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_fm(text)
            accent = accent_for(rel, meta)
            inner = fill_slots(
                md_lite(body), target.parent, auto=False, crumb_rel=rel, meta=meta
            )
            inner = fill_uses(inner, target.stem, target)
            wrapped, shell_meta = wrap_in_shell(target.parent, inner, rel, meta)
            env = meta.get("environment")
            extras = None
            if shell_meta:
                env = env or shell_meta.get("environment")
                extras = ["/index.css"] if (SYS / "index.css").is_file() else None
            crumb = folder_crumbs(rel)
            card = is_card_note(meta)
            if card:
                env = env or "lorecard"
            strip = css_hex(card_strip_color(meta)) if card else ""
            if card:
                wrapped = stamp_lorecard_strip(wrapped, meta)
                wrapped = wrap_tray_room(wrapped, target, meta)
            tray_room = card and tray_mouth_of(target)
            body_class = "is-lorecard" if card else ""
            if tray_room:
                body_class = (body_class + " is-tray-room").strip()
            mark = "mypi:card" if card else "mypi:go"
            if is_lobby() and target.name.lower() == START_NAME:
                body_class = (body_class + " is-start").strip()
                mark = "mypi:start"
            self.send_html(
                page(
                    meta.get("title") or target.stem,
                    wrapped,
                    strip or accent,
                    crumb,
                    pocket_bar(rel),
                    env,
                    extras,
                    here=target.parent,
                    vault=pocket_key(target),
                    chrome=card_chrome(meta) if card else None,
                    strip=strip or None,
                    body_class=body_class,
                    mark=mark,
                )
            )
            self.remember_desk()
            return
        if target.suffix.lower() == ".canvas":
            sight_stage(target)
            self.send_html(canvas_page(target, rel))
            self.remember_desk()
            return
        self.send_html(page("no", "<p>not a note.</p>", "#6e6254", rel, pocket_bar(rel), librarian=False), 415)

    def read_json_body(self, default=None):
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            n = 0
        if n < 0 or n > 200_000:
            return None, 413
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return default if default is not None else {}, 200
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None, 400
        return data, 200

    def send_blot(self, code: int, obj: dict | None, err: str) -> None:
        if obj is None:
            self.send_bytes(
                json.dumps({"error": err}).encode("utf-8"),
                "application/json; charset=utf-8",
                code,
            )
            return
        self.send_bytes(
            json.dumps(obj).encode("utf-8"),
            "application/json; charset=utf-8",
            code,
        )

    def do_POST(self) -> None:
        u = urlparse(self.path)
        if u.path in ("/api/readme", "/api/rules"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = readme_note_add(
                str(data.get("pocket") or ""),
                str(data.get("title") or data.get("name") or data.get("leaf") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path in (
            "/api/librarian/lore/attach",
            "/api/agent/lore/attach",
            "/api/charlie/lore/attach",
            "/api/tps/lore/attach",
        ):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            mouth = u.path.split("/")[2]
            code, obj, err = catalog_lore_attach(
                mouth,
                str(data.get("pocket") or ""),
                str(data.get("crate") or data.get("card") or ""),
                str(data.get("onto") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path in ("/api/librarian/lore", "/api/agent/lore", "/api/charlie/lore", "/api/tps/lore"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            mouth = u.path.split("/")[2]
            code, obj, err = catalog_lore_add(
                mouth,
                str(data.get("pocket") or ""),
                str(data.get("class") or ""),
                str(data.get("title") or ""),
                str(data.get("line") or ""),
                str(data.get("time") if data.get("time") is not None else data.get("tps") or ""),
                str(data.get("onto") or ""),
                str(data.get("maker") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/tps":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = tps_stamp_add(
                str(data.get("pocket") or ""),
                str(data.get("title") or data.get("label") or ""),
                str(
                    data.get("time")
                    if data.get("time") is not None
                    else data.get("at")
                    if data.get("at") is not None
                    else data.get("value")
                    or ""
                ),
            )
            self.send_blot(code, obj, err)
            return
        if u.path in CATALOG_API:
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = catalog_field_add(
                CATALOG_API[u.path],
                str(data.get("pocket") or ""),
                str(data.get("type") or ""),
                str(data.get("label") or ""),
                data.get("value"),
                str(data.get("onto") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path in SHELF_API:
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = shelf_add(
                SHELF_API[u.path],
                str(data.get("pocket") or ""),
                str(data.get("leaf") or ""),
                str(data.get("from") or ""),
                str(data.get("rel") or ""),
                str(data.get("to") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/crate":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = crate_issue(str(data.get("pocket") or ""))
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/bullet":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            idx = data.get("i") if data.get("i") is not None else data.get("index")
            code, obj, err = bullet_toggle(str(data.get("pocket") or ""), idx)
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/last":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            href = ""
            if isinstance(data, dict):
                href = str(data.get("href") or "")
            elif isinstance(data, str):
                href = data
            saved = last_save(href)
            self.send_bytes(
                json.dumps({"href": saved}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path != "/api/been":
            self.send_error(404)
            return
        data, status = self.read_json_body([])
        if status != 200:
            self.send_error(status)
            return
        have = been_load()
        incoming = been_clean(data)
        merged = been_clean(have + incoming)
        saved = been_save(merged)
        self.send_bytes(
            json.dumps({"been": saved}).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def do_PUT(self) -> None:
        u = urlparse(self.path)
        if u.path in ("/api/readme", "/api/rules"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            what = str(data.get("what") or data.get("face") or "room").strip().lower()
            if what == "page":
                md = data.get("markdown")
                if md is None:
                    md = data.get("body")
                if md is None:
                    md = data.get("leaf") or ""
                code, obj, err = readme_page_put(
                    str(data.get("pocket") or ""),
                    str(data.get("headers") if data.get("headers") is not None else ""),
                    str(md),
                    str(data.get("which") or data.get("kind") or ""),
                )
            else:
                code, obj, err = readme_put(
                    str(data.get("pocket") or ""),
                    str(data.get("body") if data.get("body") is not None else data.get("leaf") or ""),
                )
            self.send_blot(code, obj, err)
            return
        if u.path in ("/api/librarian/lore", "/api/agent/lore", "/api/charlie/lore", "/api/tps/lore"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            mouth = u.path.split("/")[2]
            code, obj, err = catalog_lore_update(
                mouth,
                str(data.get("pocket") or ""),
                str(data.get("crate") or data.get("card") or ""),
                str(data.get("class") or ""),
                str(data.get("title") or ""),
                str(data.get("line") or ""),
                str(data.get("time") if data.get("time") is not None else data.get("tps") or ""),
                str(data.get("maker") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path in CATALOG_API:
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            idx = data.get("index") if data.get("index") is not None else data.get("i")
            code, obj, err = catalog_field_update(
                CATALOG_API[u.path],
                str(data.get("pocket") or ""),
                idx,
                str(data.get("type") or ""),
                str(data.get("label") or ""),
                data.get("value"),
                str(data.get("onto") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path not in SHELF_API:
            self.send_error(404)
            return
        data, status = self.read_json_body({})
        if status != 200:
            self.send_error(status)
            return
        if not isinstance(data, dict):
            self.send_error(400)
            return
        code, obj, err = shelf_update(
            SHELF_API[u.path],
            str(data.get("pocket") or ""),
            str(data.get("id") or ""),
            str(data.get("leaf") or ""),
        )
        self.send_blot(code, obj, err)

    def do_DELETE(self) -> None:
        u = urlparse(self.path)
        if u.path == "/api/tps":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = tps_stamp_delete(
                str(data.get("pocket") or ""),
                str(data.get("id") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path in CATALOG_API:
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            idx = data.get("index") if data.get("index") is not None else data.get("i")
            code, obj, err = catalog_field_delete(
                CATALOG_API[u.path],
                str(data.get("pocket") or ""),
                idx,
                str(data.get("onto") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path not in SHELF_API:
            self.send_error(404)
            return
        data, status = self.read_json_body({})
        if status != 200:
            self.send_error(status)
            return
        if not isinstance(data, dict):
            self.send_error(400)
            return
        code, obj, err = shelf_delete(
            SHELF_API[u.path],
            str(data.get("pocket") or ""),
            str(data.get("id") or ""),
            str(data.get("what") or ""),
        )
        self.send_blot(code, obj, err)

    def index(self) -> bytes:
        return render_folder(active_vault())

    def listing(self, folder: Path) -> bytes:
        return render_folder(folder)


if __name__ == "__main__":
    print(f"pocket-go  http://{HOST}:{PORT}/   start={HOSTS_ROOT / START_NAME}  hosts={sorted(discover_hosts().keys())}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
