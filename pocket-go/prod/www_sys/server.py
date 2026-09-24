#!/usr/bin/env python3
"""My Pocket Go â€” early internet in WWW chrome. Edit in Obsidian, refresh here."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sqlite3
import subprocess
import sys
import threading
import time
import shutil
import urllib.error
import urllib.request
from datetime import datetime
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, parse_qsl, quote, unquote, urlencode, urlparse

SYS = Path(__file__).resolve().parent
ROOT = SYS.parents[1]  # pocket-go/
ALICE = ROOT.parents[1]  # ALICE_BOX/
# Glass Compost mountain (crate tags). Cut-room overlay is bench.db.
COMPOST_YARD_DEFAULT = Path(
    r"C:\Builds\_mausoleum\alice-box-exiles\nim-data-forestry\prod\yard_sys\store\yard.db"
)
COMPOST_BENCH_DEFAULT = (
    ALICE / "le-awn-industries" / "glass-compost" / "prod" / "bench_sys" / "store" / "bench.db"
)
ROM_LAUNCHES = (
    ALICE / "the-deck-host" / "rom-launcher" / "prod" / "launch_sys" / "data" / "launches.json"
)
MATS = ROOT / "mats"
STYLES = MATS / "styles"
MATS_IMGS = MATS / "imgs"
BEEN_FILE = ROOT / "prod" / "been.json"
BEEN_LOCK = threading.Lock()
JUMPS_FILE = ROOT / "prod" / "jumps.json"
JUMPS_LOCK = threading.Lock()
JUMPS_MAX = 80
LAST_FILE = ROOT / "prod" / "last.json"
LAST_LOCK = threading.Lock()
_LAST_RESTORED = False
LIBRARIAN = ROOT / "~librarian"
DETECTIVE_ROOT = ROOT / "~detective"
AGENT_ROOT = DETECTIVE_ROOT  # alias: old ~agent name
README_ROOT = ROOT / "~readme"
HELP_ROOT = ROOT / "~help"
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
    "detective": {
        "root": DETECTIVE_ROOT,
        "house": "DETECTIVE",
        "prefix": "DET",
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
HOST = os.environ.get("GO_HOST", "0.0.0.0").strip() or "0.0.0.0"
PORT = int(os.environ.get("GO_PORT", os.environ.get("LIBRARY_PORT", "43210")))
SKU = "CO.MYPT-004-GO"
SKIP = {".obsidian", ".agents", ".claude", ".opencode", ".git", "~reader"}
# Ledger yaml next to notes — not doors. _shell.md is RESERVED_NOTES.
MACHINE_FILES = frozenset({"_hosts.yaml", "_marks.yaml", "_serial.yaml"})
START_NAME = "start.md"
RECENT_NAME = "recent.md"
ROAM_NAME = "roam.md"
RESERVED_HOST_SLUGS = frozenset({"www", "start", "recent", "go", "roam"})
LOBBY_HOST_SLUGS = frozenset({"start", "recent", "go", "roam"})
CODES_HOST_SLUGS = frozenset({"codes", "code.glass", "codes.glass"})
RECENT_COUNT = 25
RECENT_CAP = 100
ENV_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
CHIP_UID_RE = re.compile(r"^(leaf|card)\[(\d+)\]$", re.I)
CHIP_STEM_RE = re.compile(r"^(leaf|card)\[\d+\]", re.I)
FIELD_TOKEN = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]*)\}\}")
TOOL_SLOT_RE = re.compile(
    r"\{\{tool:([A-Za-z][A-Za-z0-9_-]*(?::[A-Za-z0-9._-]*)*)\}\}",
    re.I,
)
SLOT_NAMES = {
    "files",
    "spines",
    "doors",
    "worlds",
    "dir",
    "list",
    "paper",
    "insertdata",
    "subshell",
    "images",
    "slides",
    "thumbs",
    "faces",
    "cards",
    "shelf",
    "cover",
    "jacket",
    "crumb",
    "bread",
    "shellcrumb",
    "crumbback",
    "home",
    "roam",
    "root",
    "uses",
    "bags",
    "meta",
    "chips",
    "edges",
    "headers",
    "injector",
    "tagsearch",
    "taglook",
    "codelook",
    "codesearch",
    "huntsearch",
    "huntlook",
    "blotsearch",
    "blotlook",
    "erasearch",
    "eralook",
    "eventsearch",
    "eventlook",
    "peoplesearch",
    "peoplelook",
    "kvensearch",
    "kvenlook",
    "loresearch",
    "lorelook",
    "cardsearch",
    "cardlook",
    "compost",
    "recent",
    "tree",
}


def stash_name(name: str) -> bool:
    """Tilde and dot names stay off lists. Underscore folders sort to the top on purpose."""
    return bool(name) and name[0] in ".~"
WIKI_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")
TAG_RE = re.compile(r"(?<![&/\w])#([A-Za-z0-9][\w/-]*)")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,5})\s+(.*)$")
DRESS_LEAD = re.compile(
    r"^(?:\{\{\.([A-Za-z][\w.-]*?)(?:#([A-Za-z][\w-]*))?\}\}|\{\{#([A-Za-z][\w-]*)\}\})\s*"
)
SPAN_RE = re.compile(
    r"\{\{span(?::(\.[A-Za-z][\w.-]*(?:#[A-Za-z][\w-]*)?|#[A-Za-z][\w-]*|[A-Za-z][\w.-]*))?\}\}(.*?)\{\{/span\}\}"
)
SPAN_LINE = re.compile(
    r"^\{\{span(?::(\.[A-Za-z][\w.-]*(?:#[A-Za-z][\w-]*)?|#[A-Za-z][\w-]*|[A-Za-z][\w.-]*))?\}\}(.*)$"
)
SPAN_CLOSE = re.compile(r"^\{\{/span\}\}\s*$")
SPAN_CLOSE_INLINE = re.compile(r"\{\{/span\}\}")
DIV_OPEN = re.compile(
    r"^\{\{(?:div|block):(\.[A-Za-z][\w.-]*(?:#[A-Za-z][\w-]*)?|#[A-Za-z][\w-]*|[A-Za-z][\w.-]*)\}\}(.*)$"
)
DIV_CLOSE = re.compile(r"^\{\{/(?:div|block)\}\}\s*$")
DIV_CLOSE_INLINE = re.compile(r"\{\{/(?:div|block)\}\}")
DIV_INLINE_RE = re.compile(
    r"\{\{(?:div|block):(\.[A-Za-z][\w.-]*(?:#[A-Za-z][\w-]*)?|#[A-Za-z][\w-]*|[A-Za-z][\w.-]*)\}\}(.*?)\{\{/(?:div|block)\}\}"
)
IMG_EMBED_RE = re.compile(r"!\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]")
IMG_TOKEN_RE = re.compile(r"\{\{img:([^}|]+)(?:\|([^}]*))?\}\}")
OUTLINK_RE = re.compile(r"\{\{(?:outlink|out):([^}|]+)(?:\|([^}]*))?\}\}", re.I)
ROM_TOKEN_RE = re.compile(
    r"\{\{rom:([A-Za-z0-9][A-Za-z0-9._-]{0,63})(?:\|([^}]*))?\}\}",
    re.I,
)
ROM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
IMG_MD_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
FACE_CRATE_RE = re.compile(
    r"\{\{(?:face|card):(crate\.[A-Fa-f0-9]{16}|[A-Fa-f0-9]{16})\}\}",
    re.I,
)
LINK_CRATE_RE = re.compile(
    r"\{\{(link|crate):([^}|]+)(?:\|([^}]*))?\}\}",
    re.I,
)  # POCKET_LINK_GO_HOST
CHIP_SPLIT = re.compile(r"\s*[,;]\s*")
META_SLOT_RE = re.compile(
    r"\{\{(?:meta|chips)(?::(all|librarian|lib|agent|detective|det|tps))?\}\}",
    re.I,
)
RECENT_SLOT_RE = re.compile(r"\{\{recent(?::(\d{1,3}))?\}\}", re.I)
TREE_SLOT_RE = re.compile(r"\{\{(?:tree|dirtree:(?:shell|root))\}\}", re.I)
DIRTREE_MODE_RE = re.compile(
    r"\{\{dirtree(?::(all|folders|files|flat))?\}\}", re.I
)
DOORS_SLOT_RE = re.compile(r"\{\{(?:doors|worlds)(?::(cards|chips))?\}\}", re.I)
CABINET_FIELD_RE = re.compile(
    r"\{\{(lib|agt|det|tps|librarian|agent|detective):([A-Za-z][A-Za-z0-9 _.-]*)\}\}",
    re.I,
)
# One labeled chip (label + value), same atom as {{meta}} drops.
CHIP_FIELD_RE = re.compile(
    r"\{\{chip:(lib|agt|det|tps|librarian|agent|detective):([A-Za-z][A-Za-z0-9 _.-]*)\}\}",
    re.I,
)
MOUTH_CANON = {
    "lib": "librarian",
    "librarian": "librarian",
    "library": "librarian",
    "agt": "detective",
    "agent": "detective",
    "det": "detective",
    "detective": "detective",
    "cha": "charlie",
    "charlie": "charlie",
    "tps": "tps",
}


def mouth_canon(raw: str) -> str:
    """Cabinet mouth. agent/agt → detective. The lookout host go.agent is not a mouth."""
    s = (raw or "").strip().lower()
    return MOUTH_CANON.get(s, s)
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
# Guest paper: listed and opened as a read-only text sheet (not markdown).
# Not images, not live HTML, not .md / .canvas / .chip.
TEXT_NOTE_EXT = frozenset(
    {
        ".txt",
        ".text",
        ".log",
        ".py",
        ".pyw",
        ".pyi",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".css",
        ".scss",
        ".json",
        ".jsonl",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".xml",
        ".csv",
        ".tsv",
        ".sql",
        ".sh",
        ".bash",
        ".ps1",
        ".bat",
        ".cmd",
        ".rs",
        ".go",
        ".rb",
        ".php",
        ".lua",
        ".pl",
        ".c",
        ".h",
        ".cc",
        ".cpp",
        ".hpp",
        ".java",
        ".kt",
        ".swift",
        ".cs",
        ".mdx",
        ".rst",
    }
)
TEXT_NOTE_MAX = 200_000
HTML_EXT = {".html", ".htm"}
HTML_ASSET_MAX = 5_000_000
HTML_ASSET_TYPE = {
    ".html": "text/html; charset=utf-8",
    ".htm": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".eot": "application/vnd.ms-fontobject",
}
HTML_ASSET_TYPE.update(IMAGE_TYPE)

HOSTS_ROOT = ROOT / "~hosts"
HOSTS_FILE = HOSTS_ROOT / "_hosts.yaml"
MARKS_FILE = HOSTS_ROOT / "_marks.yaml"
MARK_INK = frozenset({"teal", "rose", "brass", "dim", "ok", "violet"})
MARK_BUILTINS: dict[str, dict[str, str]] = {
    "librarian": {"label": "LIBRARIAN", "ink": "teal"},
    "detective": {"label": "DETECTIVE", "ink": "rose"},
    "charlie": {"label": "CHARLIE", "ink": "brass"},
    "tps": {"label": "TPS", "ink": "dim"},
    "cards": {"label": "CARDS", "ink": "violet"},
}
MARK_ALIASES = {
    "lib": "librarian",
    "library": "librarian",
    "lore": "cards",
    "agent": "detective",
    "hunt": "detective",
    "agt": "detective",
    "det": "detective",
    "cha": "charlie",
}
HOST_SLUG = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?$")
# go.* native vault hosts; roam.* connected libraries. Groups stay (host, rel).
# Dots in the slug are allowed so ~hosts/code.glass is go.code.glass.
GO_PREFIX = re.compile(
    r"^(?:go|roam)\.([A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?)(?:/(.*))?$",
    re.I,
)


@dataclass(frozen=True)
class Host:
    name: str
    root: Path
    title: str = ""
    kind: str = "go"
    environment: str = ""


_CURRENT_HOST: ContextVar[Host | None] = ContextVar("pocket_go_host", default=None)
_HUNT_Q: ContextVar[str] = ContextVar("pocket_go_hunt_q", default="")
_ERA_Q: ContextVar[str] = ContextVar("pocket_go_era_q", default="")
_PEOPLE_Q: ContextVar[str] = ContextVar("pocket_go_people_q", default="")
_LORE_Q: ContextVar[str] = ContextVar("pocket_go_lore_q", default="")


def host_slug(name: str) -> str:
    s = (name or "").strip().lower()
    return s if s and HOST_SLUG.fullmatch(s) else ""


# One-release alias: old go.inbox/{mouth}/... still finds trays/bay homes.
INBOX_LEGACY_HOME = {
    "librarian": "trays",
    "agent": "trays",
    "detective": "trays",
    "charlie": "trays",
    "tps": "trays",
    "boybots": "bay",
    "gemini": "bay",
}


def remap_legacy_inbox(name: str, rel: str) -> tuple[str, str]:
    name_n = (name or "").strip().lower()
    parts = [p for p in (rel or "").replace("\\", "/").strip("/").split("/") if p]
    if name_n == "inbox":
        if not parts:
            return name, rel
        dest = INBOX_LEGACY_HOME.get(parts[0].lower())
        if not dest:
            return name, rel
        parts[0] = mouth_canon(parts[0])
        return dest, "/".join(parts)
    if name_n == "trays" and parts:
        canon = mouth_canon(parts[0])
        if canon != parts[0].lower() and canon in (
            "librarian",
            "detective",
            "charlie",
            "tps",
        ):
            parts[0] = canon
            return name, "/".join(parts)
    return name, rel


def load_hosts_map(text: str) -> dict[str, dict[str, str]]:
    """Optional ~hosts/_hosts.yaml. Folders still resolve with no file.

    Keys: folder, title, pin (int order - lower floats higher on lobby doors),
    show (bool-ish; hide from start {{doors}} when false),
    icon (host face filename; aliases favicon, avatar, faveicon),
    bar (extra jump-bar words, comma or space; folder name already works).
    kind: roam + source: connect an exterior markdown folder as roam.{slug}.
    kind: go + source: same folder, but the door is go.{slug} (a code bay, not roam).
    environment: optional coat when a roam hall has no _shell.md.
    Aliases into show: active, visible. Aliases into bar: nick, nicks.
    Aliases into environment: env, coat.
    """
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
            if k in ("active", "visible"):
                k = "show"
            if k in ("favicon", "avatar", "faveicon"):
                k = "icon"
            if k in ("nick", "nicks"):
                k = "bar"
            if k in ("env", "coat"):
                k = "environment"
            if k in ("folder", "title", "pin", "show", "icon", "bar", "kind", "source", "environment") and v != "":
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


def host_pin_map() -> dict[str, int]:
    """go.* slug -> pin rank from _hosts.yaml. Missing = unpinned."""
    if not HOSTS_FILE.is_file():
        return {}
    try:
        aliases = load_hosts_map(HOSTS_FILE.read_text(encoding="utf-8"))
    except OSError:
        return {}
    out: dict[str, int] = {}
    for name, meta in aliases.items():
        slug = host_slug(name)
        if not slug:
            continue
        raw = str(meta.get("pin") or "").strip()
        if not raw:
            continue
        try:
            out[slug] = int(raw)
        except ValueError:
            continue
    return out


def bar_nicks() -> dict[str, str]:
    """Jump-bar word -> host slug, or go/roam/recent lobbies. Folder names always work."""
    out: dict[str, str] = {}
    for slug in discover_hosts():
        s = host_slug(slug)
        if s:
            out[s] = s
    for slug, host in discover_hosts().items():
        if host.kind == "roam":
            out["roam." + slug] = slug
    # Lobbies win over a host accidentally named go/roam/start.
    out["start"] = "start"
    out["go"] = "start"
    out["recent"] = "recent"
    out["roam"] = "roam"
    if not HOSTS_FILE.is_file():
        return out
    try:
        aliases = load_hosts_map(HOSTS_FILE.read_text(encoding="utf-8"))
    except OSError:
        return out
    for name, meta in aliases.items():
        slug = host_slug(name) or host_slug(str(meta.get("folder") or ""))
        if not slug:
            continue
        raw = str(meta.get("bar") or "").replace(",", " ")
        for word in raw.split():
            w = word.strip().lower().strip(".")
            if w.endswith(".md"):
                w = w[:-3]
            if w:
                out[w] = slug
    out["start"] = "start"
    out["go"] = "start"
    out["recent"] = "recent"
    out["roam"] = "roam"
    return out



def _parse_show_flag(raw: str) -> bool | None:
    """Parse show/active/visible. None = unset / unknown."""
    s = str(raw or "").strip().lower()
    if not s:
        return None
    if s in ("0", "no", "off", "false", "hidden", "hide", "n"):
        return False
    if s in ("1", "yes", "on", "true", "shown", "show", "y"):
        return True
    return None


def host_show_map() -> dict[str, bool]:
    """go.* slug -> explicit show flag from _hosts.yaml. Missing key = default shown."""
    if not HOSTS_FILE.is_file():
        return {}
    try:
        aliases = load_hosts_map(HOSTS_FILE.read_text(encoding="utf-8"))
    except OSError:
        return {}
    out: dict[str, bool] = {}
    for name, meta in aliases.items():
        slug = host_slug(name)
        if not slug:
            continue
        flag = _parse_show_flag(str(meta.get("show") or ""))
        if flag is None:
            continue
        out[slug] = flag
    return out


def host_icon_map() -> dict[str, str]:
    """go.* slug -> icon filename from _hosts.yaml."""
    if not HOSTS_FILE.is_file():
        return {}
    try:
        aliases = load_hosts_map(HOSTS_FILE.read_text(encoding="utf-8"))
    except OSError:
        return {}
    out: dict[str, str] = {}
    for name, meta in aliases.items():
        slug = host_slug(name)
        if not slug:
            continue
        raw = str(meta.get("icon") or "").strip()
        if raw:
            out[slug] = raw
    return out


def host_is_shown(slug: str) -> bool:
    """True unless _hosts.yaml sets show: false (etc.) for this go.* slug."""
    s = host_slug(slug) or (slug or "").strip().lower()
    if not s:
        return True
    return host_show_map().get(s, True)



def note_list_hidden(meta: dict | None) -> bool:
    """Frontmatter hide from dir/files/tree. hidden:true / show:false / hide:true."""
    meta = meta or {}
    for key in ("hidden", "hide", "list", "listed", "show", "visible"):
        if key not in meta:
            continue
        flag = _parse_show_flag(str(meta.get(key) or ""))
        if flag is None:
            continue
        if key in ("hidden", "hide"):
            # hidden:true => hide; hidden:false => show
            return flag is True
        if key in ("list", "listed", "show", "visible"):
            # show:false / listed:false => hide
            return flag is False
    return False


def path_list_hidden(p: Path) -> bool:
    """True if this vault file should stay off dir/files/tree listings."""
    try:
        if not p.is_file():
            return False
    except OSError:
        return False
    if p.suffix.lower() not in {".md", ".canvas"}:
        return False
    # Reserved papers already filtered elsewhere; still honor flag if set.
    try:
        return note_list_hidden(read_md_meta(p))
    except Exception:
        return False


def _hosts_folder_alias_slugs() -> dict[str, str]:
    """Map disk folder name/path (lower) -> alias go.* slug when they differ."""
    if not HOSTS_FILE.is_file():
        return {}
    try:
        aliases = load_hosts_map(HOSTS_FILE.read_text(encoding="utf-8"))
    except OSError:
        return {}
    out: dict[str, str] = {}
    for name, meta in aliases.items():
        slug = host_slug(name)
        if not slug:
            continue
        folder = str(meta.get("folder") or "").strip().replace("\\", "/")
        if not folder:
            continue
        base = folder.rstrip("/").split("/")[-1]
        base_l = base.lower()
        if base_l and host_slug(base) != slug:
            out[base_l] = slug
        out[folder.lower()] = slug
    return out


def meta_host_kind(meta: dict | None) -> str:
    """kind: roam, or a source: path without kind: go, makes a connected library."""
    meta = meta or {}
    k = str(meta.get("kind") or "").strip().lower()
    if k == "go":
        return "go"
    if k == "roam":
        return "roam"
    if str(meta.get("source") or "").strip():
        return "roam"
    return "go"


def roam_source_path(raw: str) -> Path | None:
    """Yaml source: is the allowlist. Create the directory if it is missing."""
    s = (raw or "").strip().strip('"').strip("'")
    if not s or "://" in s.replace("\\", "/"):
        return None
    p = Path(s).expanduser()
    try:
        p = p.resolve()
    except OSError:
        return None
    if p.exists() and not p.is_dir():
        return None
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
    if not p.is_dir():
        return None
    return p


def host_scheme_of(host: Host | None) -> str:
    if host is not None and (host.kind or "go").strip().lower() == "roam":
        return "roam"
    return "go"


def active_kind() -> str:
    spec = _CURRENT_HOST.get()
    if spec is None or not spec.name:
        return "go"
    return host_scheme_of(spec)


def pocket_scheme(name: str = "") -> str:
    slug = host_slug(name) if name else active_host()
    if not slug:
        spec = _CURRENT_HOST.get()
        if spec is not None and spec.name:
            return host_scheme_of(spec)
        return "go"
    spec = _CURRENT_HOST.get()
    if spec is not None and spec.name == slug:
        return host_scheme_of(spec)
    found = discover_hosts().get(slug)
    return host_scheme_of(found)


def format_pocket(name: str, rel: str = "") -> str:
    """go.{host}/rel or roam.{host}/rel. Empty host is a lobby path."""
    slug = (name or "").strip()
    path = (rel or "").replace("\\", "/").strip("/")
    if not slug:
        return ("/" + path) if path else "/"
    base = pocket_scheme(slug) + "." + slug
    return base + "/" + path if path else base + "/"


def host_scheme_map() -> dict[str, str]:
    return {slug: host_scheme_of(h) for slug, h in discover_hosts().items()}


def discover_hosts() -> dict[str, Host]:
    """A folder under ~hosts is go.{name}. kind: roam + source: is roam.{name}."""
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
            if not slug or slug in LOBBY_HOST_SLUGS:
                continue
            found[slug] = Host(slug, child, child.name)
        for name, meta in aliases.items():
            slug = host_slug(name)
            if not slug or slug in LOBBY_HOST_SLUGS:
                continue
            src = str(meta.get("source") or "").strip()
            if src:
                root = roam_source_path(src)
                if root is None:
                    continue
                title = str(meta.get("title") or "").strip() or slug
                env = env_name(str(meta.get("environment") or "")) or ""
                kind = meta_host_kind(meta)
                found[slug] = Host(slug, root, title, kind, env)
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
    else:
        for name, meta in aliases.items():
            slug = host_slug(name)
            src = str(meta.get("source") or "").strip()
            if not src:
                continue
            root = roam_source_path(src)
            if root is None:
                continue
            title = str(meta.get("title") or "").strip() or slug
            env = env_name(str(meta.get("environment") or "")) or ""
            kind = meta_host_kind(meta)
            found[slug] = Host(slug, root, title, kind, env)
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


def is_codes_host(host: Host | None = None) -> bool:
    """True for the compost codes bank (go.codes / go.code.glass)."""
    spec = host if host is not None else _CURRENT_HOST.get()
    if spec is None or not spec.name:
        return False
    name = str(spec.name or "").strip().lower()
    if name == EVENT_HOST_SLUG or name == PEOPLE_HOST_SLUG:
        return False
    if name in CODES_HOST_SLUGS:
        return True
    env = str(spec.environment or "").strip().lower()
    if env == "codes":
        return True
    shell = shell_path(spec.root)
    if shell.is_file():
        meta = read_md_meta(shell)
        if str(meta.get("environment") or "").strip().lower() == "codes":
            return True
    return False


def codes_host() -> Host | None:
    found = discover_hosts()
    for slug in ("codes", "code.glass", "codes.glass"):
        host = found.get(slug)
        if host is not None:
            return host
    for host in found.values():
        if (host.kind or "go") == "roam":
            continue
        if is_codes_host(host):
            return host
    return None


def on_codes_host() -> bool:
    return is_codes_host(_CURRENT_HOST.get())


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


def lobby_note_rel(raw: str) -> str | None:
    """Lobby files (roam.md, recent.md, start). None if this is a host path."""
    leaf = (raw or "").replace("\\", "/").strip("/")
    if not leaf or "/" in leaf:
        return None
    low = leaf.lower()
    if low in ("roam", ROAM_NAME.lower()):
        return ROAM_NAME
    if low in ("recent", RECENT_NAME.lower()):
        return RECENT_NAME
    if low in ("start", START_NAME.lower(), "go"):
        return ""
    return None


def split_pocket(raw: str) -> tuple[str, str]:
    """Address or shelf pocket -> (host, rel). Empty host is the start page."""
    s = (raw or "").replace("\\", "/").strip()
    lobby = lobby_note_rel(s)
    if lobby is not None:
        return "", lobby
    m = GO_PREFIX.match(s)
    if m:
        rel = strip_zone_leaf_rel(m.group(2) or "")
        return remap_legacy_inbox(m.group(1).lower(), rel)
    rel = strip_zone_leaf_rel(s)
    return remap_legacy_inbox("", rel)


def pocket_host_bin(pocket: str) -> str:
    """Chest label for a page: go.{host} / roam.{host}, or start."""
    name, _rel = split_pocket(pocket)
    if not name:
        return "start"
    return format_pocket(name).rstrip("/")


def parse_request_pocket(qs: dict) -> tuple[str, str]:
    h = host_slug(unquote((qs.get("h") or [""])[0]))
    p = unquote((qs.get("p") or [""])[0])
    if h in LOBBY_HOST_SLUGS:
        if h == "roam":
            extra = lobby_note_rel(p)
            return "", extra if extra is not None else ROAM_NAME
        if h == "recent":
            extra = lobby_note_rel(p)
            return "", extra if extra is not None else RECENT_NAME
        return "", ""
    name, rel = split_pocket(p)
    if h:
        name = h
        if not GO_PREFIX.match((p or "").replace("\\", "/").strip()):
            rel = strip_zone_leaf_rel(p)
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
        stem = p.lower()
        if stem.endswith(".md"):
            stem = stem[:-3]
        if not stem or stem in ("start", "go"):
            return "/"
        if stem == "roam" or p.lower() == ROAM_NAME:
            return "/?p=roam"
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
    word = tag_slug(slug)
    if not word:
        return "/?h=" + TAGS_HOST_SLUG
    return "/?h=" + TAGS_HOST_SLUG + "&p=" + quote(word + ".md", safe="/")


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


def rom_id_ok(raw: str) -> str:
    s = (raw or "").strip()
    if not ROM_ID_RE.match(s):
        return ""
    return s


def rom_recipe(rid: str) -> dict | None:
    rid = rom_id_ok(rid)
    if not rid or not ROM_LAUNCHES.is_file():
        return None
    try:
        data = json.loads(ROM_LAUNCHES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    rec = (data.get("recipes") or {}).get(rid)
    if not isinstance(rec, dict):
        return None
    return rec


def rom_port_up(port: int) -> bool:
    url = f"http://127.0.0.1:{int(port)}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=0.6) as r:
            return 200 <= int(getattr(r, "status", 200) or 200) < 500
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return False


def launch_rom(rid: str) -> dict:
    """Spawn a ROM's run-in-deck-host.py — same glass the ROM Launcher opens."""
    rid = rom_id_ok(rid)
    if not rid:
        return {"ok": False, "error": "id required"}
    rec = rom_recipe(rid)
    if not rec or not rec.get("run_script"):
        return {"ok": False, "error": "no launch recipe (coming soon?)"}
    if rec.get("coming_soon"):
        return {"ok": False, "error": "coming soon"}
    script = ALICE / str(rec["run_script"])
    if not script.is_file():
        return {"ok": False, "error": "run script missing"}
    port = rec.get("port")
    already = bool(port and rom_port_up(int(port)))
    log_path = ROOT / "prod" / "rom-launch.log"
    log_f = open(log_path, "a", encoding="utf-8", errors="replace")
    log_f.write(f"\n--- launch {rid} ---\n{script}\n")
    if already:
        log_f.write(f"(server already warm on :{port} — still opening glass)\n")
    log_f.flush()
    kwargs: dict = {
        "cwd": str(script.parent),
        "stdout": log_f,
        "stderr": subprocess.STDOUT,
    }
    if sys.platform == "win32":
        cf = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        cf |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        kwargs["creationflags"] = cf
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen([sys.executable, str(script)], **kwargs)
    msg = (
        f"glass pid={proc.pid} · server already warm on :{port}"
        if already
        else f"launched pid={proc.pid}"
    )
    return {
        "ok": True,
        "already": already,
        "pid": proc.pid,
        "port": port,
        "id": rid,
        "message": msg,
    }


def rom_launch_html(rid: str, label: str = "") -> str:
    rid = rom_id_ok(rid)
    if not rid:
        return ""
    shown = (label or "").strip() or rid
    return (
        f'<a class="rom-launch" href="#" data-rom="{html.escape(rid, True)}" '
        f'title="open in Deck Host">{html.escape(shown)}</a>'
    )


def img_href(rel: str) -> str:
    p = (rel or "").replace("\\", "/").strip("/")
    host = active_host()
    if not host:
        return "/i/" + quote(p, safe="/")
    return "/i/" + quote(format_pocket(host, p).rstrip("/"), safe="/")


def mats_img_href(p: Path) -> str:
    rel = p.relative_to(MATS_IMGS).as_posix()
    return "/i/" + quote(rel, safe="/")


def html_asset_href(rel: str) -> str:
    p = (rel or "").replace("\\", "/").strip("/")
    host = active_host()
    if not host:
        return "/h/" + quote(p, safe="/")
    return "/h/" + quote(format_pocket(host, p).rstrip("/"), safe="/")


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
    "cast": "#6b3a2a",
    "tags": "#2a6a52",
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
    "skyline": "#1b365d",
    "buddy": "#8a4aaa",
    "trays": "#2d6a4f",
    "bay": "#c45828",
    "logger": "#3d5c44",
    "logger-strange": "#6b3a42",
    "codes": "#3a5a6e",
    "stacks": "#2a5a48",
    "portico": "#c9a227",
}
HOUSE_STRIP = {
    "detective": "#a33b3b",
    "agent": "#a33b3b",
    "charlie": "#c9892d",
    "librarian": "#2d6a4f",
    "tps": "#c42820",
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
    "/api/detective": "detective",
    "/api/agent": "detective",
}
SHELF_API = {
    "/api/charlie": "charlie",
}
TPS_TITLES = ("created", "referenced")
INDEX_NAME = "_shell.md"
INDEX_LEGACY = "_index.md"
PAPER_NAME = "index.md"
_ZONE_LEAF = {
    "_index",
    "_shell",
    "index",
    INDEX_NAME,
    INDEX_LEGACY,
    PAPER_NAME,
}


def strip_zone_leaf_rel(rel: str) -> str:
    """Drop a trailing `_shell.md` / leftover `_index.md` / paper name from a path."""
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel:
        return ""
    extra = {"start", START_NAME}
    if rel.lower() in _ZONE_LEAF | extra:
        return ""
    parts = [p for p in rel.split("/") if p]
    if parts and parts[-1].lower() in _ZONE_LEAF:
        parts = parts[:-1]
    return "/".join(parts)


def is_shell_name(name: str) -> bool:
    return str(name or "").lower() in {INDEX_NAME, INDEX_LEGACY}


def shell_path(folder: Path) -> Path:
    """Canonical `_shell.md`, else leftover `_index.md`, else the path to mint."""
    modern = folder / INDEX_NAME
    if modern.is_file():
        return modern
    legacy = folder / INDEX_LEGACY
    if legacy.is_file():
        return legacy
    return modern


def has_shell(folder: Path) -> bool:
    return (folder / INDEX_NAME).is_file() or (folder / INDEX_LEGACY).is_file()
# Soft room gate: canonical frontmatter key is codeword: (aliases accepted).
CODEWORD_KEYS = ("codeword", "password", "lock", "code")
CW_COOKIE = "pg_cw"
CW_COOKIE_MAX_AGE = 60 * 60 * 12  # half-day soft session
PAPER_HOLE = re.compile(
    r"(?:<p>\s*)?\{\{(?:paper|insertdata)\}\}(?:\s*</p>)?",
    re.I,
)
SUBSHELL_HOLE = re.compile(
    r"(?:<p>\s*)?\{\{subshell\}\}(?:\s*</p>)?",
    re.I,
)
BEEN_MAX = 2000
SIGIL_RE = re.compile(r"(?<![A-Za-z0-9._:/-])([#$^@])([A-Za-z0-9._:/-]+)")
CITE_CRATE_RE = re.compile(
    r"(?<![A-Za-z0-9._:/-])\^((?:crate\.)?[A-Fa-f0-9]{16})\b",
    re.I,
)
# Segment: T01/B002/L03, or trunk wild * / T* (uncut — bag+seq only).
_CHIP_SEG = r"(?:\*|[A-Za-z]\*|[A-Za-z]\d{1,8})"
CHIP_CODE_BODY_RE = re.compile(
    rf"^[A-Za-z]{{1,12}}-\d{{1,8}}(?:\.{_CHIP_SEG})*$"
)
CHIP_CODE_RE = re.compile(
    rf"(?<![A-Za-z0-9._:/-])\^([A-Za-z]{{1,12}}-\d{{1,8}}(?:\.{_CHIP_SEG})*)"
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


def jumps_href_ok(href: str) -> bool:
    href = (href or "").strip()
    if not href.startswith("/") or href.startswith("//") or len(href) > 500:
        return False
    try:
        u = urlparse(href)
    except ValueError:
        return False
    return not (u.scheme or u.netloc)


def jumps_clean(raw) -> list[dict]:
    if isinstance(raw, dict):
        raw = raw.get("jumps") or raw.get("bookmarks") or []
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        href = str(item.get("href") or "").strip()
        label = str(item.get("label") or "").strip()
        if not label or not jumps_href_ok(href):
            continue
        if href in seen:
            continue
        seen.add(href)
        out.append({"label": label[:80], "href": href})
        if len(out) >= JUMPS_MAX:
            break
    return out


def jumps_load() -> tuple[bool, list[dict]]:
    """(disk_exists, jumps). Missing file is not an empty bar — client may seed."""
    with JUMPS_LOCK:
        if not JUMPS_FILE.is_file():
            return False, []
        try:
            return True, jumps_clean(json.loads(JUMPS_FILE.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            return False, []


def jumps_save(items) -> list[dict]:
    clean = jumps_clean(items)
    with JUMPS_LOCK:
        JUMPS_FILE.parent.mkdir(parents=True, exist_ok=True)
        JUMPS_FILE.write_text(
            json.dumps({"jumps": clean}, indent=2) + "\n", encoding="utf-8"
        )
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


def yaml_source_scalar(s: str) -> str:
    """Write a disk path for source:. Keep C:\\Users unquoted so load_hosts_map
    does not strip quotes and leave doubled backslashes."""
    s = (s or "").strip().strip('"').strip("'")
    if not s:
        return '""'
    if any(c in s for c in "#{}[]&*!|>%@`'\","):
        return json.dumps(s.replace("\\", "/"), ensure_ascii=False)
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
    rel_l = rel.lower()
    known_note = rel_l.endswith(".md") or rel_l.endswith(".chip")
    if (target is None or not target.exists()) and not known_note:
        alt = safe_rel(rel + ".md")
        if alt is not None and alt.exists():
            target = alt
        else:
            alt = safe_rel(rel + ".chip")
            if alt is not None and alt.exists():
                target = alt
    if target is None or not target.exists():
        # leftover `_index.md` after the `_shell.md` rename
        leaf = Path((rel or "").replace("\\", "/")).name.lower()
        if leaf == INDEX_LEGACY:
            parent = str(Path((rel or "").replace("\\", "/")).parent).replace("\\", "/")
            alt_rel = (parent + "/" + INDEX_NAME).strip("/") if parent not in (".", "") else INDEX_NAME
            alt = safe_rel(alt_rel)
            if alt is not None and alt.exists():
                target = alt
    if target is None or not target.exists():
        return None
    if target.is_file() and (
        is_shell_name(target.name) or target.name.lower() == PAPER_NAME
    ):
        return target.parent
    return target


def shelf_file(kind: str, target: Path) -> Path | None:
    spec = SHELF_KIND.get(mouth_canon(kind) if kind else kind)
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
    elif page.suffix.lower() in {".canvas", ".chip"}:
        # Keep full name so sibling foo.md / foo.canvas / foo.chip do not share one yaml.
        try:
            rel = Path(str(page.relative_to(vault)) + ".yaml")
        except ValueError:
            return None
    else:
        return None
    if ".." in rel.parts:
        return None
    return shelf_rel(root, rel)



def _shelf_retarget_pocket(kind: str, yaml_path: Path, pocket: str) -> None:
    """Refresh pocket: inside a cabinet sidecar after its page was renamed."""
    spec = SHELF_KIND.get(kind) or {}
    house = str(spec.get("house") or kind).upper()
    if kind == "tps":
        obj = tps_read(yaml_path, pocket)
        obj["pocket"] = pocket
        tps_write(yaml_path, obj)
        return
    obj = blot_read(yaml_path, pocket, house)
    obj["pocket"] = pocket
    blot_write(yaml_path, obj)


def rename_page_shelves(old_page: Path, new_page: Path) -> list[str]:
    """BIOS page rename: move filename-matched cabinet twins (~librarian/~tps/~detective/~charlie).

    Sidecars are vault-relative .yaml mirrors of the .md name. Also rewrite pocket:.
    Skips missing cabinets and destination collisions. Returns kinds that moved.
    """
    moved: list[str] = []
    try:
        if old_page.resolve() == new_page.resolve():
            return moved
    except OSError:
        pass
    new_pocket = pocket_key(new_page)
    for kind, spec in SHELF_KIND.items():
        if spec.get("scope") != "page":
            continue
        old_yaml = shelf_file(kind, old_page)
        new_yaml = shelf_file(kind, new_page)
        if old_yaml is None or new_yaml is None:
            continue
        if not old_yaml.is_file():
            continue
        try:
            same_yaml = old_yaml.resolve() == new_yaml.resolve()
        except OSError:
            same_yaml = False
        if same_yaml:
            try:
                _shelf_retarget_pocket(kind, new_yaml, new_pocket)
            except OSError:
                pass
            continue
        if new_yaml.exists():
            try:
                if new_yaml.resolve() != old_yaml.resolve():
                    # already a sidecar for the new name — leave both alone
                    continue
            except OSError:
                continue
        try:
            new_yaml.parent.mkdir(parents=True, exist_ok=True)
            if old_yaml.name.lower() == new_yaml.name.lower() and old_yaml.name != new_yaml.name:
                mid = old_yaml.with_name(new_yaml.name + ".__renaming__")
                if mid.exists():
                    continue
                old_yaml.replace(mid)
                mid.replace(new_yaml)
            else:
                old_yaml.replace(new_yaml)
            _shelf_retarget_pocket(kind, new_yaml, new_pocket)
            moved.append(kind)
        except OSError:
            continue
    return moved


def readme_dest_for_folder(folder: Path) -> Path | None:
    """~readme/{vault-rel}/README.md — room letter file for one index folder."""
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
    """Room letter. Nearest existing ~readme letter walking up; else the nearest _index."""
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
            return 500, None, "could not read room letter"
    return 200, _readme_payload(folder, dest, body, target), ""


def readme_put(pocket_raw: str, body: str) -> tuple[int, dict | None, str]:
    body = note_text(body or "")
    if len(body) > README_MAX:
        return 413, None, "room letter too long"
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


def note_text(text: str) -> str:
    """Normalize a vault note so --- fences parse.

    Grok / Windows writers often stamp a UTF-8 BOM (U+FEFF, or the
    latin-1 ghost ï»¿). That makes BIOS miss the opening fence, so YAML
    lands in the markdown box (red gutter on ---) instead of headers.
    """
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    while raw.startswith("\ufeff"):
        raw = raw[1:]
    if raw.startswith("ï»¿"):
        raw = raw[3:]
    return raw


def split_note(text: str) -> tuple[str, str]:
    """Front matter (no fences) and the markdown body."""
    raw = note_text(text)
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end >= 0:
            return raw[4:end].strip("\n"), raw[end + 5 :].lstrip("\n")
    return "", raw


def join_note(headers: str, markdown: str) -> str:
    h = note_text(headers or "").strip("\n")
    b = note_text(markdown or "")
    if not h.strip() and b.startswith("---\n"):
        h, b = split_note(b)
        h = (h or "").strip("\n")
    if h.startswith("---"):
        h = h[3:].lstrip("\n")
    if h.endswith("\n---"):
        h = h[: -4].rstrip("\n")
    if h.strip():
        out = "---\n" + h.strip() + "\n---\n"
        return out + (("\n" + b) if b else "")
    return b


def write_note(path: Path, text: str) -> None:
    """UTF-8, no BOM, LF. Bots/Windows like to stamp a BOM that breaks --- fences."""
    raw = note_text(text)
    if raw and not raw.endswith("\n"):
        raw += "\n"
    path.write_bytes(raw.encode("utf-8"))


def force_crate_line(text: str, crate: str) -> str:
    """Keep the live crate. Never overwrite with a different one."""
    crate = (crate or "").strip()
    if not crate:
        return text
    raw = note_text(text)
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
    raw = note_text(text)
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
    """Which vault notes the page face can edit.

    Named note: the note itself, plus the nearest `_shell` if you are
    still inside that shell's zone (so BIOS can open shell from deep pages).

    Guest `.chip` / plain text (`.py`, `.txt`, …): never a note clay.
    Only the ancestor `_shell.md`. BIOS Keep / Rename / page face stay
    off the guest paper.

    Folder (or index/_shell): this folder's paper, then local shell if it
    exists; else the ancestor zone shell. Paper stays this folder — never an
    ancestor's paper. The paper file may not exist yet; Keep writes it.
    """
    if target.is_file() and is_guest_paper_path(target):
        out: list[tuple[str, Path]] = []
        zone = nearest_index_folder(target) or target.parent
        shell = shell_path(zone)
        if shell.is_file():
            out.append(("shell", shell))
        return out
    if target.is_file() and target.suffix.lower() == ".md":
        name = target.name.lower()
        if name not in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
            out: list[tuple[str, Path]] = [("note", target)]
            try:
                here = target.resolve()
            except OSError:
                here = target
            zone = nearest_index_folder(target)
            if zone is not None:
                shell = shell_path(zone)
                try:
                    ok = shell.is_file() and shell.resolve() != here
                except OSError:
                    ok = shell.is_file()
                if ok:
                    out.append(("shell", shell))
            return out
        target = target.parent
    if not target.is_dir():
        return []
    out = []
    start = lobby_start(target)
    if start is not None:
        out.append(("note", start))
        return out
    out.append(("paper", target / PAPER_NAME))
    shell = shell_path(target)
    if shell.is_file():
        out.append(("shell", shell))
    else:
        zone = nearest_index_folder(target)
        if zone is not None:
            try:
                same = zone.resolve() == target.resolve()
            except OSError:
                same = zone == target
            if not same:
                zshell = shell_path(zone)
                if zshell.is_file():
                    out.append(("shell", zshell))
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
        return None
    return files[0][1]


def clay_payload(
    path: Path, kind: str, *, here_folder: Path | None = None
) -> dict | None:
    headers, markdown, crate = "", "", ""
    if path.is_file():
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            text = ""
        headers, markdown = split_note(text)
        crate = file_crate(path)
    try:
        here = path if path.is_file() else path.parent
        pocket = pocket_key(here)
    except OSError:
        pocket = pocket_key(path.parent)
    dir_rel = ""
    shell_here = True
    try:
        vault = active_vault().resolve()
        parent = path.parent.resolve() if path.is_file() else path.resolve()
        try:
            dir_rel = "" if is_vault_root(parent) else parent.relative_to(vault).as_posix()
        except ValueError:
            dir_rel = ""
        if kind == "shell" and here_folder is not None:
            try:
                shell_here = parent == here_folder.resolve()
            except OSError:
                shell_here = False
    except OSError:
        pass
    return {
        "kind": kind,
        "pocket": pocket,
        "crate": crate,
        "headers": headers,
        "markdown": markdown,
        "file": path.name,
        "dir": dir_rel,
        "here": shell_here,
    }


def page_note_payload(target: Path, which: str = "") -> dict | None:
    files = folder_clay_files(target)
    if not files:
        dest = page_note_file(target, which)
        if dest is None:
            return None
        files = [("note", dest)]
    here_folder = clay_folder(target)
    pages: list[dict] = []
    for kind, path in files:
        item = clay_payload(path, kind, here_folder=here_folder)
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
    here_folder = nearest_index_folder(target) or folder
    here_dest = readme_dest_for_folder(here_folder)
    obj = {
        "house": "BIOS",
        "pocket": pocket,
        "crate": page_crate(folder),
        "body": body,
        "body_html": md_lite(parse_fm(body or "")[1]),
        "route": pocket,
        "face": "room",
        "local_letter": bool(here_dest and here_dest.is_file()),
    }
    page = page_note_payload(target)
    if page is not None:
        obj["page"] = page
    coat = coat_payload(target, dest)
    if coat is not None:
        obj["coat"] = coat
    obj["chip_guest"] = is_guest_paper_path(target)
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
    if is_guest_paper_path(dest):
        return 400, None, "guest chip"
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
        write_note(dest, text)
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


RESERVED_NOTES = {INDEX_NAME, INDEX_LEGACY, PAPER_NAME, START_NAME, RECENT_NAME, ROAM_NAME, "readme.md"}
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


def readme_note_rename(
    pocket_raw: str, new_title: str, which: str = ""
) -> tuple[int, dict | None, str]:
    """Rename the open page file from the BIOS face. Keeps crate + body."""
    new_title = (new_title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not new_title:
        return 400, None, "need a name"
    fname = note_filename(new_title)
    if not fname:
        return 400, None, "bad name"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_note_rename(pocket_raw, fname, which, new_title)


def _readme_note_rename(
    pocket_raw: str, fname: str, which: str, new_title: str
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = page_note_file(target, which)
    if dest is None or not dest.is_file():
        return 400, None, "no page file"
    if is_guest_paper_path(dest):
        return 400, None, "guest chip"
    if dest.name.lower() in {n.lower() for n in RESERVED_NOTES}:
        return 400, None, "reserved page"
    folder = dest.parent
    if not _in_active_vault(folder):
        return 400, None, "not a vault page"
    new_path = folder / fname
    try:
        same = new_path.resolve() == dest.resolve()
    except OSError:
        same = False
    if not same:
        try:
            for p in folder.iterdir():
                if p.name.lower() == fname.lower() and p.resolve() != dest.resolve():
                    return 409, None, "already a page by that name"
        except OSError:
            return 500, None, "could not read folder"
    found = readme_resolve(target if same else dest)
    if found is None:
        # resolve against current dest
        found = readme_resolve(dest)
    if found is None:
        return 400, None, "not a vault page"
    room_folder, room_dest = found
    with LBR_LOCK:
        try:
            text = dest.read_text(encoding="utf-8")
        except OSError:
            return 500, None, "could not read page"
        meta = parse_fm(text)[0]
        live_title = str(meta.get("title") or "").strip()
        if not live_title or live_title == dest.stem:
            text = patch_fm_keys(text, {"title": yaml_scalar(new_title)})
        if same:
            dest.write_text(text, encoding="utf-8")
            out = dest
        else:
            if new_path.exists() and new_path.resolve() != dest.resolve():
                return 409, None, "already a page by that name"
            # Windows case-only rename via temp
            if dest.name.lower() == fname.lower() and dest.name != fname:
                mid = folder / (fname + ".__renaming__")
                if mid.exists():
                    return 500, None, "rename busy"
                dest.replace(mid)
                mid.replace(new_path)
            else:
                dest.replace(new_path)
            new_path.write_text(text, encoding="utf-8")
            out = new_path
            rename_page_shelves(dest, out)
        room_body = ""
        if room_dest.is_file():
            try:
                room_body = room_dest.read_text(encoding="utf-8")
            except OSError:
                room_body = ""
    rel = out.relative_to(active_vault()).as_posix()
    obj = _readme_payload(room_folder, room_dest, room_body, out)
    page = page_note_payload(out, which)
    if page is not None:
        obj["page"] = page
    obj["face"] = "page"
    obj["file"] = out.name
    obj["href"] = page_href(rel)
    obj["pocket"] = pocket_key(out)
    return 200, obj, ""


def readme_note_add(pocket_raw: str, title: str) -> tuple[int, dict | None, str]:
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not title:
        return 400, None, "need a name"
    fname = note_filename(title)
    if fname is None:
        stem = note_stem(title)
        if stem and (stem + ".md").lower() in {n.lower() for n in RESERVED_NOTES}:
            return 400, None, "that's paper or shell â€” Keep on page"
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





def readme_folder_rename(pocket_raw: str, title: str) -> tuple[int, dict | None, str]:
    """Rename the hall (folder) you are standing in from the BIOS."""
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not title:
        return 400, None, "need a name"
    stem = note_stem(title)
    if not stem or WIN_DEVICE.match(stem):
        return 400, None, "need a name"
    if stem.lower() in {n.lower().removesuffix(".md") for n in RESERVED_NOTES}:
        return 400, None, "reserved name"
    if stem.startswith(".") or stem.startswith("~"):
        return 400, None, "name can't start with . or ~"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_folder_rename(pocket_raw, title, stem)


def _readme_folder_rename(
    pocket_raw: str, title: str, stem: str
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    folder = clay_folder(target)
    if folder is None or not folder.is_dir():
        return 400, None, "not a vault page"
    if not _in_active_vault(folder):
        return 400, None, "not a vault page"
    try:
        vault = active_vault().resolve()
        folder_r = folder.resolve()
    except OSError:
        return 500, None, "could not resolve folder"
    if folder_r == vault:
        return 400, None, "can't rename the host root"
    parent = folder.parent
    dest = parent / stem
    try:
        same = dest.resolve() == folder_r
    except OSError:
        same = False
    if not same:
        try:
            for p in parent.iterdir():
                if p.name.lower() == stem.lower() and p.resolve() != folder_r:
                    return 409, None, "already something by that name"
        except OSError:
            return 500, None, "could not read parent"
    # standing relative path (file or dir) for href rewrite after move
    try:
        old_folder_rel = folder_r.relative_to(vault).as_posix()
        if target.is_file():
            old_stand_rel = target.resolve().relative_to(vault).as_posix()
        else:
            old_stand_rel = old_folder_rel
    except (ValueError, OSError):
        return 500, None, "not inside vault"
    with LBR_LOCK:
        try:
            if same:
                out = folder
            elif folder.name.lower() == stem.lower() and folder.name != stem:
                mid = parent / (stem + ".__renaming__")
                if mid.exists():
                    return 500, None, "rename busy"
                folder.rename(mid)
                mid.rename(dest)
                out = dest
            else:
                if dest.exists():
                    return 409, None, "already something by that name"
                folder.rename(dest)
                out = dest
        except OSError:
            return 500, None, "could not rename folder"
        # best-effort: rewrite old hall path prefix in notes under this vault
        try:
            new_folder_rel = out.resolve().relative_to(vault).as_posix()
        except (ValueError, OSError):
            new_folder_rel = stem
        if old_folder_rel != new_folder_rel:
            _rewrite_folder_refs(vault, old_folder_rel, new_folder_rel)
    # new standing href
    if old_stand_rel == old_folder_rel:
        new_stand = new_folder_rel
    elif old_stand_rel.startswith(old_folder_rel + "/"):
        new_stand = new_folder_rel + old_stand_rel[len(old_folder_rel) :]
    else:
        new_stand = new_folder_rel
    return 200, {
        "ok": True,
        "folder": out.name,
        "title": title,
        "href": page_href(new_stand, is_dir=not str(new_stand).lower().endswith((".md", ".chip", ".canvas"))),
        "pocket": pocket_key(out if not str(new_stand).lower().endswith((".md", ".chip", ".canvas")) else (vault / new_stand)),
        "old": old_folder_rel,
        "rel": new_folder_rel,
    }, ""


def _rewrite_folder_refs(vault: Path, old_rel: str, new_rel: str) -> None:
    """Rewrite hall path strings in markdown under the vault (best-effort)."""
    old = (old_rel or "").replace("\\", "/").strip("/")
    new = (new_rel or "").replace("\\", "/").strip("/")
    if not old or old == new:
        return
    # patterns: path as folder segment in links / wiki / plain
    needles = [
        (old + "/", new + "/"),
        (old + ".md", new + ".md"),  # unlikely for folder
    ]
    for path in vault.rglob("*.md"):
        try:
            if not path.is_file():
                continue
            # skip deep noise
            name = path.name
            if name.startswith(".") or name.startswith("~"):
                continue
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        orig = text
        for a, b in needles:
            if a in text:
                text = text.replace(a, b)
        # bare path as query p=
        text = text.replace("p=" + old + "/", "p=" + new + "/")
        text = text.replace("p=" + old + "&", "p=" + new + "&")
        text = text.replace("p=" + old + '"', "p=" + new + '"')
        if text != orig:
            try:
                path.write_text(text, encoding="utf-8")
            except OSError:
                pass


def readme_shell_add(pocket_raw: str, title: str = "") -> tuple[int, dict | None, str]:
    """Mint a local `_shell.md` subshell for the open folder (BIOS +shell).

    Nested halls sit in the parent shell's {{paper}} hole via {{subshell}}.
    They collect a crate/catalog bag without becoming the dress room.
    Does not recurse into children. Refuses if this folder already has a shell.
    """
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_shell_add(pocket_raw, title)


def _readme_shell_add(pocket_raw: str, title: str) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    folder = clay_folder(target)
    if folder is None or not folder.is_dir():
        return 400, None, "not a vault page"
    if not _in_active_vault(folder):
        return 400, None, "not a vault page"
    if lobby_start(folder) is not None:
        return 400, None, "start lobby has its own face"
    dest = folder / INDEX_NAME
    if dest.is_file():
        return 409, None, "this folder already has a shell"
    name = title or folder.name or "shell"
    crate = mint_crate_id()
    text = (
        "---\n"
        "crate: " + crate + "\n"
        "title: " + yaml_scalar(name) + "\n"
        "---\n\n"
        "{{subshell}}\n"
    )
    with LBR_LOCK:
        if dest.exists():
            return 409, None, "this folder already has a shell"
        try:
            dest.write_text(text, encoding="utf-8", newline="\n")
        except OSError:
            return 500, None, "could not write shell"
    rel = ""
    try:
        rel = "" if is_vault_root(folder) else folder.relative_to(active_vault()).as_posix()
    except ValueError:
        rel = ""
    return (
        200,
        {
            "ok": True,
            "file": dest.name,
            "folder": folder.name,
            "dir": rel,
            "href": page_href(rel, is_dir=True),
            "pocket": pocket_key(folder),
            "crate": crate,
        },
        "",
    )


def readme_letter_add(pocket_raw: str, title: str = "") -> tuple[int, dict | None, str]:
    """Mint a room letter for the nearest `_shell` hall. Manual — +shell does not."""
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_letter_add(pocket_raw, title)


def _readme_letter_add(pocket_raw: str, title: str) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    folder = nearest_index_folder(target)
    if folder is None:
        return 400, None, "not a vault page"
    if not _in_active_vault(folder):
        return 400, None, "not a vault page"
    if lobby_start(folder) is not None:
        return 400, None, "start lobby has its own face"
    dest = readme_dest_for_folder(folder)
    if dest is None:
        return 400, None, "not a vault page"
    if dest.is_file():
        return 409, None, "this room already has a letter"
    name = title or folder.name or "room"
    crate = mint_crate_id()
    text = (
        "---\n"
        "crate: " + crate + "\n"
        "title: " + yaml_scalar(name) + "\n"
        "---\n\n"
        "# " + name + "\n\n"
        "how we use this space.\n"
    )
    with LBR_LOCK:
        if dest.exists():
            return 409, None, "this room already has a letter"
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8", newline="\n")
        except OSError:
            return 500, None, "could not write room letter"
    return _readme_get(pocket_raw)


def readme_folder_add(pocket_raw: str, title: str) -> tuple[int, dict | None, str]:
    """Make a new subfolder (hall) in the open pocket from the BIOS."""
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not title:
        return 400, None, "need a name"
    stem = note_stem(title)
    if not stem or WIN_DEVICE.match(stem):
        return 400, None, "need a name"
    if stem.lower() in {n.lower().removesuffix(".md") for n in RESERVED_NOTES}:
        return 400, None, "reserved name"
    if stem.startswith(".") or stem.startswith("~"):
        return 400, None, "name can't start with . or ~"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_folder_add(pocket_raw, title, stem)


def _readme_folder_add(
    pocket_raw: str, title: str, stem: str
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    folder = clay_folder(target)
    if folder is None or not folder.is_dir():
        return 400, None, "not a vault page"
    if not _in_active_vault(folder):
        return 400, None, "not a vault page"
    dest = folder / stem
    try:
        for p in folder.iterdir():
            if p.name.lower() == stem.lower():
                return 409, None, "already something by that name"
    except OSError:
        return 500, None, "could not read folder"
    with LBR_LOCK:
        if dest.exists():
            return 409, None, "already something by that name"
        # Bare directory only — no `_shell.md` face. Nested +folder used to
        # mint crumbback/title/dir/files `_index`, which wrap_in_shell then stuffed
        # into the ancestor {{paper}} (yellow kraft / double paper under tags).
        # Opening a folder without _index hits render_folder's else: h1 + file_list,
        # then one wrap_in_shell into the parent. Host create still mints real
        # shells via mint_zone_room_letter elsewhere.
        dest.mkdir(parents=False, exist_ok=False)
    rel = dest.relative_to(active_vault()).as_posix()
    return 200, {
        "folder": stem,
        "href": page_href(rel),
        "pocket": pocket_key(dest),
    }, ""


def librarian_file(target: Path) -> Path | None:
    return shelf_file("librarian", target)


def pocket_key(target: Path) -> str:
    root = active_vault().resolve()
    host = active_host()
    try:
        page = target.resolve()
    except OSError:
        return format_pocket(host) if host else "/"
    if is_vault_root(page):
        rel = ""
    else:
        try:
            rel = page.relative_to(root).as_posix()
        except ValueError:
            return format_pocket(host) if host else "/"
    if not host:
        if not rel or rel.lower() in ("start", START_NAME):
            return "/"
        return "/" + rel
    return format_pocket(host, rel)


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


def is_chip_path(path: Path | None) -> bool:
    return bool(path) and str(getattr(path, "suffix", "")).lower() == ".chip"


def is_text_guest_path(path: Path | None) -> bool:
    """Plain .py / .txt / source: listed and opened as read-only guest paper."""
    if not path:
        return False
    try:
        if not path.is_file():
            return False
    except OSError:
        return False
    suf = str(getattr(path, "suffix", "")).lower()
    if not suf or suf in IMAGE_EXT or suf in HTML_EXT or suf in {".md", ".canvas", ".chip"}:
        return False
    return suf in TEXT_NOTE_EXT


def is_html_guest_path(path: Path | None) -> bool:
    """Live .html / .htm: listed and opened as a rendered frame on the paper."""
    if not path:
        return False
    try:
        if not path.is_file():
            return False
    except OSError:
        return False
    return str(getattr(path, "suffix", "")).lower() in HTML_EXT


def is_guest_paper_path(path: Path | None) -> bool:
    return is_chip_path(path) or is_text_guest_path(path) or is_html_guest_path(path)


def text_guest_inner(target: Path) -> str:
    """Escaped <pre> sheet. Clay tokens in the file stay literal."""
    suf = target.suffix.lower()
    lang = re.sub(r"[^a-z0-9]+", "", suf.lstrip("."))[:16]
    try:
        raw = target.read_bytes()
    except OSError:
        return "<p>could not read this file.</p>"
    if b"\x00" in raw[:8192]:
        return "<p>binary file - not shown.</p>"
    clipped = False
    if len(raw) > TEXT_NOTE_MAX:
        raw = raw[:TEXT_NOTE_MAX]
        clipped = True
    text = raw.decode("utf-8", errors="replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    cls = "code guest-text"
    if lang:
        cls += " lang-" + lang
    bits = [
        '<article class="guest-text-sheet">',
        '<p class="guest-text-name">' + html.escape(target.name) + "</p>",
        "<pre class='" + cls + "'><code>" + html.escape(text) + "</code></pre>",
    ]
    if clipped:
        bits.append(
            '<p class="guest-text-clip">shown first '
            + str(TEXT_NOTE_MAX)
            + " bytes</p>"
        )
    bits.append("</article>")
    return "".join(bits)


def html_guest_inner(rel: str, name: str) -> str:
    """Frame the live page. CSS / pictures / fonts next to it load via /h/."""
    src = html_asset_href(rel)
    return (
        '<article class="guest-html-sheet">'
        '<iframe class="guest-html-frame" src="'
        + html.escape(src, True)
        + '" sandbox="allow-scripts allow-popups allow-forms allow-modals" '
        'referrerpolicy="no-referrer" title="'
        + html.escape(name, True)
        + '"></iframe></article>'
    )


def norm_chip_uid(raw: str) -> str:
    s = str(raw or "").strip().strip('"').strip("'")
    m = CHIP_UID_RE.fullmatch(s)
    if not m:
        return ""
    return m.group(1).lower() + "[" + m.group(2) + "]"


def chip_uid_from_name(name: str) -> str:
    stem = Path(name).stem
    m = CHIP_STEM_RE.match(stem)
    return norm_chip_uid(m.group(0)) if m else ""


def chip_peek(path: Path) -> dict[str, str]:
    """Tiny indent peek: chip.uid, chip.name, top-level crate. Not a Sophia parser."""
    out = {"uid": "", "name": "", "crate": ""}
    if not path or path.suffix.lower() != ".chip":
        return out
    try:
        raw = note_text(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        out["uid"] = chip_uid_from_name(path.name)
        return out
    meta, _body = parse_fm(raw)
    out["crate"] = str(meta.get("crate") or "").strip()
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        head = raw[4:end] if end >= 0 else raw[4:]
        in_chip = False
        chip_indent = 0
        for line in head.split("\n"):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()
            if indent == 0 and stripped.lower().startswith("chip:"):
                in_chip = True
                chip_indent = 0
                continue
            if in_chip:
                if indent <= chip_indent:
                    in_chip = False
                elif ":" in stripped:
                    k, v = stripped.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip().strip('"').strip("'")
                    if k == "uid":
                        uid = norm_chip_uid(v)
                        if uid:
                            out["uid"] = uid
                    elif k in ("name", "title") and v and not out["name"]:
                        out["name"] = v
    if not out["uid"]:
        out["uid"] = chip_uid_from_name(path.name)
    return out


def chip_uid(path: Path) -> str:
    return chip_peek(path).get("uid") or ""


def chip_host_slug(path: Path | None = None) -> str:
    if path is not None:
        spec = host_for_path(path)
        if spec is not None and spec.name:
            return spec.name
    return active_host() or ""


def chip_crates_path(path: Path | None = None) -> Path:
    return LIBRARIAN / chip_host_slug(path) / "_chip_crates.yaml"


def _chip_crates_load(path: Path | None = None) -> dict[str, str]:
    p = chip_crates_path(path)
    if not p.is_file():
        return {}
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        k, v = s.split(":", 1)
        uid = norm_chip_uid(k)
        crate = norm_crate(v)
        if uid and crate:
            out[uid] = crate
    return out


def _chip_crates_save(data: dict[str, str], path: Path | None = None) -> None:
    dest = chip_crates_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Go crate ledger for guest .chip files. Keyed by chip.uid.", ""]
    for k in sorted(data):
        crate = data.get(k) or ""
        if k and crate:
            lines.append(f"{k}: {crate}")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def chip_crate_get(uid: str, path: Path | None = None) -> str:
    uid = norm_chip_uid(uid)
    if not uid:
        return ""
    with LBR_LOCK:
        return _chip_crates_load(path).get(uid, "")


def chip_crate_set(uid: str, crate: str, path: Path | None = None) -> None:
    uid = norm_chip_uid(uid)
    crate = norm_crate(crate)
    if not uid or not crate:
        return
    with LBR_LOCK:
        data = _chip_crates_load(path)
        data[uid] = crate
        _chip_crates_save(data, path)


def _chip_sticker(path: Path, crate: str) -> None:
    crate = norm_crate(crate)
    if not crate or not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    new_text, changed = apply_crate_fm(text, crate)
    if not changed:
        return
    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError:
        return


def _ensure_chip_crate(path: Path) -> str:
    """Sidecar uid first. Never remint. Courtesy crate: sticker may be restamped."""
    peek = chip_peek(path)
    uid = peek.get("uid") or ""
    if not uid:
        return ""
    on_file = norm_crate(peek.get("crate") or "")
    data = _chip_crates_load(path)
    have = norm_crate(data.get(uid) or "")
    if have:
        if not on_file:
            _chip_sticker(path, have)
        return have
    if on_file:
        data[uid] = on_file
        _chip_crates_save(data, path)
        return on_file
    crate = mint_crate_id()
    data[uid] = crate
    _chip_crates_save(data, path)
    _chip_sticker(path, crate)
    return crate


def file_crate(path: Path) -> str:
    if not path.is_file():
        return ""
    suf = path.suffix.lower()
    if suf == ".chip":
        peek = chip_peek(path)
        uid = peek.get("uid") or ""
        if uid:
            got = _chip_crates_load(path).get(uid, "")
            if got:
                return got
        return str(peek.get("crate") or "").strip()
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
        for name in (INDEX_NAME, INDEX_LEGACY, PAPER_NAME):
            c = file_crate(target / name)
            if c:
                return c
        return ""
    return file_crate(target)


def bag_crate(target: Path) -> str:
    """Page crate. Paper first on a folder â€” tagging hangs on the fill."""
    if target.is_dir():
        start = lobby_start(target)
        if start is not None:
            return file_crate(start)
        for name in (PAPER_NAME, INDEX_NAME, INDEX_LEGACY):
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
DETECTIVE_HOST = HOSTS_ROOT / "detective"
LIBRARIAN_HOST = HOSTS_ROOT / "librarian"


@dataclass(frozen=True)
class BlotterBank:
    """Page-level slip shelf: detective blotter, or librarian twin."""

    slug: str
    kind: str
    environment: str
    mouth: str
    q_name: str
    look_mark: str
    look_miss: str
    search_ph: str
    search_btn: str


BLOTTER_BANKS = {
    "detective": BlotterBank(
        slug="detective",
        kind="hunt",
        environment="hunt",
        mouth="detective",
        q_name="hunt",
        look_mark="on the pad",
        look_miss="nothing on the pad matches ",
        search_ph="hunt a word",
        search_btn="hunt",
    ),
    "librarian": BlotterBank(
        slug="librarian",
        kind="blot",
        environment="stacks",
        mouth="librarian",
        q_name="blot",
        look_mark="on the shelf",
        look_miss="nothing on the shelf matches ",
        search_ph="a note, a title",
        search_btn="look",
    ),
}


def blotter_spec(bank: str = "detective") -> BlotterBank:
    return BLOTTER_BANKS.get((bank or "").strip().lower()) or BLOTTER_BANKS["detective"]


def blotter_root(bank: str = "detective") -> Path:
    spec = blotter_spec(bank)
    if spec.slug == "detective":
        return DETECTIVE_HOST
    if spec.slug == "librarian":
        return LIBRARIAN_HOST
    return HOSTS_ROOT / spec.slug


def blotter_bank_for_path(path: Path) -> str:
    try:
        here = path.resolve()
    except OSError:
        return "detective"
    for name in BLOTTER_BANKS:
        root = blotter_root(name)
        try:
            here.relative_to(root.resolve())
            return name
        except (OSError, ValueError):
            continue
    return "detective"


def is_blotter_note(meta: dict | None, bank: str | None = None) -> bool:
    meta = meta or {}
    kind = str(meta.get("kind") or "").strip().lower()
    env = str(meta.get("environment") or "").strip().lower()
    src = norm_crate(str(meta.get("source_crate") or ""))
    if bank:
        spec = blotter_spec(bank)
        return kind == spec.kind or (env == spec.environment and bool(src))
    return kind in ("hunt", "blot") or (
        env in ("hunt", "stacks") and bool(src)
    )


ERA_SITS_FILE = TPS_ROOT / "_worldline.yaml"
EVENT_HOST_SLUG = "code.event"
EVENT_BANK_PREFIX = "EV"
EVENT_CODE_RE = re.compile(r"^EV-\d{1,8}$")
PEOPLE_HOST_SLUG = "code.people"
TAGS_HOST_SLUG = "code.tags"
PEOPLE_CODE_RE = re.compile(r"^[A-Z]{3}-\d{3}$")
PEOPLE_SKIP_GROUPS = frozenset({"OT", "NT", "ONT", "EV"})
BAY_HOST = HOSTS_ROOT / "bay"
INBOX_HOST = HOSTS_ROOT / "inbox"  # thin legacy redirect host
LORE_INBOX = TRAYS_HOST / "librarian"
DETECTIVE_INBOX = TRAYS_HOST / "detective"
AGENT_INBOX = DETECTIVE_INBOX  # alias: old trays/agent name
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
    "detective": {
        "house": "DETECTIVE",
        "made": "Detective",
        "inbox": DETECTIVE_INBOX,
        "serial": DETECTIVE_INBOX / "_serial.yaml",
        "suggest": DETECTIVE_ROOT / "_suggest.yaml",
        "tray": "detective",
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
    cleaned = re.sub(r"^[Â©à¸‰]\s*", "", s)
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
    mouth = mouth_canon(unquote((qs.get("m") or ["librarian"])[0]).strip().lower() or "librarian")
    label = unquote((qs.get("f") or [""])[0]).strip()
    value = unquote((qs.get("v") or [""])[0]).strip()
    binning = unquote((qs.get("bin") or [""])[0]).strip().lower()
    return mouth, label, value, binning


def catalog_qs_is_report(qs: dict) -> bool:
    mouth, label, value, _binning = catalog_from_qs(qs)
    if mouth not in ("librarian", "detective", "tps"):
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
    shell = shell_path(folder)
    if not shell.is_file():
        return ""
    return env_name(str(read_md_meta(shell).get("environment") or "")) or ""



COAT_MAX = 400_000


def zone_room_env(room_dest: Path | None) -> str:
    """Best-practice coat name: environment: on the room letter (~readme)."""
    if room_dest is None or not room_dest.is_file():
        return ""
    return env_name(str(read_md_meta(room_dest).get("environment") or "")) or ""


def zone_room_env_walk(target: Path | None) -> str:
    """Room-letter coat walking ancestors — nested boxes inherit the host letter."""
    if target is None:
        return ""
    folder = nearest_index_folder(target)
    if folder is None:
        return ""
    try:
        vault = active_vault().resolve()
        cur = folder.resolve()
    except OSError:
        return ""
    while True:
        dest = readme_dest_for_folder(cur)
        if dest is not None and dest.is_file():
            e = zone_room_env(dest)
            if e:
                return e
        if is_vault_root(cur):
            return ""
        parent = cur.parent
        if parent == cur:
            return ""
        try:
            parent.relative_to(vault)
        except ValueError:
            return ""
        cur = parent


def zone_shell_env(target: Path | None) -> str:
    """Fallback coat: environment on nearest _index, walking ancestors.

    Nested +folder boxes have no local environment — inherit the host coat
    (e.g. mausoleum/ALICE_BOX picks up mausoleum) instead of minting a stub.
    """
    if target is None:
        return ""
    folder = nearest_index_folder(target)
    if folder is None:
        return ""
    try:
        vault = active_vault().resolve()
        cur = folder.resolve()
    except OSError:
        return ""
    while True:
        shell = shell_path(cur)
        if shell.is_file():
            e = env_name(str(read_md_meta(shell).get("environment") or "")) or ""
            if e:
                return e
        if is_vault_root(cur):
            return ""
        parent = cur.parent
        if parent == cur:
            return ""
        try:
            parent.relative_to(vault)
        except ValueError:
            return ""
        cur = parent


def zone_page_env(target: Path | None) -> str:
    """Optional note-level environment override (dress: page can still win)."""
    if target is None or not target.is_file():
        return ""
    name = target.name.lower()
    if name in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
        return ""
    return env_name(str(read_md_meta(target).get("environment") or "")) or ""


def dress_environment(
    target: Path | None,
    page_meta: dict | None = None,
    shell_meta: dict | None = None,
) -> str:
    """Live coat name: page override, else room letter (walk up), else shell (walk up)."""
    if page_meta:
        e = env_name(str(page_meta.get("environment") or ""))
        if e:
            return e
    pe = zone_page_env(target)
    if pe:
        return pe
    re_ = zone_room_env_walk(target)
    if re_:
        return re_
    if shell_meta:
        e = env_name(str(shell_meta.get("environment") or ""))
        if e:
            return e
    got = zone_shell_env(target)
    if got:
        return got
    spec = _CURRENT_HOST.get()
    if spec is not None and spec.environment:
        return env_name(spec.environment) or ""
    return ""


def ensure_style_file(env: str) -> Path | None:
    """Mint mats/styles/{env}.css if the coat name is known but the sheet is missing."""
    env = env_name(env) or ""
    if not env:
        return None
    path = style_file_for(env)
    if path is None:
        path = STYLES / f"{env}.css"
    if path.is_file():
        return path
    try:
        STYLES.mkdir(parents=True, exist_ok=True)
        path.write_text("/* coat: %s — minted by BIOS */" % env + chr(10), encoding="utf-8")
    except OSError:
        return None
    return path


def _coat_file_payload(env: str, source: str, mint: bool = False) -> dict | None:
    env = env_name(env) or ""
    if not env:
        return None
    path = style_file_for(env)
    if mint and (path is None or not path.is_file()):
        path = ensure_style_file(env)
    body = ""
    exists = bool(path and path.is_file())
    if exists:
        try:
            body = path.read_text(encoding="utf-8")
        except OSError:
            body = ""
            exists = False
    return {
        "kind": "coat",
        "env": env,
        "file": f"{env}.css",
        "css": body,
        "exists": exists,
        "source": source,
    }


def stamp_room_environment(room_dest: Path, env: str) -> None:
    """Write environment: into the room letter frontmatter (create FM if needed)."""
    env = env_name(env) or ""
    if not env or not room_dest:
        return
    try:
        if room_dest.is_file():
            text = room_dest.read_text(encoding="utf-8")
        else:
            text = ""
            room_dest.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    meta, body = parse_fm(text)
    cur = env_name(str(meta.get("environment") or "")) or ""
    if cur.lower() == env.lower():
        return
    meta["environment"] = env
    # rebuild simple yaml frontmatter
    keys = list(meta.keys())
    fm_lines = ["---"]
    for k in keys:
        v = meta.get(k)
        if v is None or v == "":
            continue
        if isinstance(v, list):
            fm_lines.append(f"{k}:")
            for item in v:
                fm_lines.append(f"  - {item}")
        else:
            s = str(v).replace(chr(13), " ").replace(chr(10), " ").strip()
            fm_lines.append(f"{k}: {s}")
    fm_lines.append("---")
    new_text = chr(10).join(fm_lines) + chr(10) + (body or "").lstrip(chr(10))
    try:
        room_dest.write_text(new_text, encoding="utf-8")
    except OSError:
        return



def mint_zone_room_letter(
    folder: Path, title: str = "", env: str | None = None
) -> str:
    """New _index zone → own room letter + environment coat (best practice).

    Dress lives on the room letter, not on the shell _index. Folder-add and
    zone setup call this so each hall can wear a different coat without
    fighting the room-letter model.
    """
    dest = readme_dest_for_folder(folder)
    if dest is None:
        return ""
    env = env_name(env) or env_name(folder.name) or ""
    if not env:
        return ""
    ensure_style_file(env)
    title = (title or folder.name or env).strip() or env
    if not dest.is_file():
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            crate = mint_crate_id()
            text = (
                "---\n"
                "crate: "
                + crate
                + "\n"
                "title: "
                + yaml_scalar(title)
                + "\n"
                "environment: "
                + env
                + "\n"
                "---\n\n"
                "# {{title}}\n\n"
                "how we use this space.\n"
            )
            dest.write_text(text, encoding="utf-8")
        except OSError:
            return ""
    else:
        stamp_room_environment(dest, env)
    return env


def coat_payload(target: Path, room_dest: Path | None = None) -> dict | None:
    """BIOS coat: room letter environment first, then shell, then page override.

    Live dress still loads ONE stylesheet (page env if set, else shell/room).
    Nested boxes with empty local letters inherit the ancestor coat and surface
    that name in BIOS so inheritance is visible (not a blank coat pane).
    """
    local_room = zone_room_env(room_dest)
    room_env = local_room or zone_room_env_walk(target)
    shell_env = zone_shell_env(target)
    page_env = zone_page_env(target)
    # primary name: room letter wins (best practice)
    primary_env = room_env or shell_env or page_env
    if not primary_env:
        return None
    inherited = bool(room_env and not local_room)
    source = (
        "room"
        if room_env
        else "shell"
        if shell_env
        else "page"
    )
    primary = _coat_file_payload(primary_env, source, mint=True)
    if primary is None:
        return None
    if inherited:
        primary["inherited"] = True
    if page_env and primary_env.lower() != page_env.lower():
        override = _coat_file_payload(page_env, "page", mint=False)
        if override is not None:
            primary["page_override"] = {
                "env": override["env"],
                "file": override["file"],
                "exists": override["exists"],
                "source": "page",
            }
            primary["page_override_css"] = override["css"]
    return primary


def readme_coat_put(
    pocket_raw: str, css_body: str, which: str = ""
) -> tuple[int, dict | None, str]:
    css_body = (css_body or "").replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
    if len(css_body) > COAT_MAX:
        return 413, None, "coat css too long"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _readme_coat_put(pocket_raw, css_body, which)


def _readme_coat_put(
    pocket_raw: str, css_body: str, which: str = ""
) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    want = (which or "").strip().lower()
    found0 = readme_resolve(target)
    room_dest0 = found0[1] if found0 else None
    local_room = zone_room_env(room_dest0)
    room_env = local_room or zone_room_env_walk(target)
    shell_env = zone_shell_env(target)
    page_env = zone_page_env(target)
    if want in ("page", "override") and page_env:
        env = page_env
    else:
        env = room_env or shell_env or page_env
    if not env:
        return 400, None, "no environment on this zone (set environment: on the room letter)"
    dest = style_file_for(env)
    if dest is None:
        dest = STYLES / f"{env}.css"
    try:
        STYLES.mkdir(parents=True, exist_ok=True)
    except OSError:
        return 500, None, "could not open styles"
    with LBR_LOCK:
        try:
            dest.write_text(css_body, encoding="utf-8")
        except OSError:
            return 500, None, "could not write coat"
        key = env.lower()
        if key in _ENV_CSS_STRIP:
            _ENV_CSS_STRIP.pop(key, None)
    # only promote env onto room letter when room has none yet
    if want not in ("page", "override") and room_dest0 is not None and not local_room and env:
        stamp_room_environment(room_dest0, env)
    found = readme_resolve(target)
    if found is None:
        return 400, None, "not a vault page"
    folder, room_dest = found
    room_body = ""
    if room_dest.is_file():
        try:
            room_body = room_dest.read_text(encoding="utf-8")
        except OSError:
            room_body = ""
    obj = _readme_payload(folder, room_dest, room_body, target)
    obj["face"] = "coat"
    return 200, obj, ""

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


def tps_stamp_quiet(target: Path, title: str, at: int, grain: str = "clock") -> None:
    """Write one TPS stamp. No lock. Skip if this title is already on the page."""
    title = (title or "").strip()
    try:
        at = int(at)
    except (TypeError, ValueError):
        return
    if not title or at <= 0:
        return
    page = target
    if page.is_file() and (
        is_shell_name(page.name) or page.name.lower() == PAPER_NAME
    ):
        page = page.parent
    dest = shelf_file("tps", page)
    if dest is None:
        return
    pocket = pocket_key(shelf_anchor("tps", page))
    crate = bag_crate(shelf_anchor("tps", page))
    obj = tps_read(dest, pocket)
    stamps = list(obj.get("stamps") or [])
    want = title.lower()
    for s in stamps:
        if isinstance(s, dict) and str(s.get("title") or "").strip().lower() == want:
            return
    stamp_id = tps_title_slug(title) + "-" + str(at)
    have = {str(s.get("id") or "") for s in stamps if isinstance(s, dict)}
    if stamp_id in have:
        stamp_id = stamp_id + "-" + str(len(stamps) + 1)
    stamps.append(
        {"id": stamp_id, "title": title, "at": at, "grain": tps_norm_grain(grain)}
    )
    obj["stamps"] = stamps
    if crate:
        obj["crate"] = crate
    obj["pocket"] = pocket
    tps_write(dest, obj)
    tps_suggest_remember(title)


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
    obj["eras"] = eras_for_crate(crate or str(obj.get("crate") or ""))
    obj["era_names"] = era_name_list()
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
    for x in lore_edges_field(meta):
        add(x)
    return out


def lore_edges_field(meta: dict) -> list[str]:
    """Only the edges: YAML list — not source_crate / born-on."""
    out: list[str] = []
    seen: set[str] = set()
    raw = (meta or {}).get("edges")
    items = raw if isinstance(raw, list) else parse_flow_list(str(raw or ""))
    for x in items:
        c = norm_crate(str(x or ""))
        if c and c not in seen:
            out.append(c)
            seen.add(c)
    return out


def lore_reverse_edge_crates(card_crate: str) -> list[str]:
    """Other lore crates that already list this crate (cabinet attach is one-way onto them)."""
    want = norm_crate(card_crate)
    if not want:
        return []
    out: list[str] = []
    seen: set[str] = {want}
    for _mouth, spec in CATALOG.items():
        inbox = spec.get("inbox")
        if inbox is None or not Path(inbox).is_dir():
            continue
        try:
            kids = list(Path(inbox).glob("*.md"))
        except OSError:
            continue
        for p in kids:
            if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
                continue
            try:
                meta = read_md_meta(p)
            except Exception:
                continue
            other = norm_crate(str((meta or {}).get("crate") or ""))
            if not other or other in seen:
                continue
            if want in lore_edge_crates(meta or {}):
                out.append(other)
                seen.add(other)
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
        pocket = format_pocket(name, rel)
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
    raw = note_text(text)
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


def apply_lore_source_crate_fm(text: str, source_crate: str | None) -> str:
    """Set or remove source_crate in frontmatter. None/"" removes the key."""
    raw = note_text(text)
    want = norm_crate(str(source_crate or ""))
    if not raw.startswith("---\n"):
        if not want:
            return raw
        return "---\nsource_crate: " + yaml_scalar(want) + "\n---\n\n" + raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return raw
    head = raw[4:end]
    rest = raw[end + 5 :]
    lines = head.split("\n")
    new_lines: list[str] = []
    found = False
    for row in lines:
        if row.startswith("source_crate:"):
            found = True
            if want:
                new_lines.append("source_crate: " + yaml_scalar(want))
        else:
            new_lines.append(row)
    if want and not found:
        new_lines.insert(0, "source_crate: " + yaml_scalar(want))
    return "---\n" + "\n".join(new_lines) + "\n---\n" + rest


def find_lore_file(mouth: str, card_crate: str) -> Path | None:
    spec = CATALOG.get(mouth_canon(mouth))
    want = norm_crate(card_crate)
    if not spec or not want:
        return None
    inbox = spec["inbox"]
    if not inbox.is_dir():
        return None
    for p in inbox.glob("*.md"):
        if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
            continue
        if norm_crate(file_crate(p)) == want:
            return p
    return None


def lore_cards_for(mouth: str, crate: str) -> list[dict]:
    mouth = mouth_canon(mouth)
    spec = CATALOG.get(mouth)
    crate = norm_crate(crate) or (crate or "").strip()
    if not spec or not crate:
        return []
    inbox = spec["inbox"]
    if not inbox.is_dir():
        return []
    tray = spec["tray"]
    out: list[dict] = []
    for p in sorted(inbox.glob("*.md"), key=lambda x: x.name.lower()):
        if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
            continue
        meta = read_md_meta(p)
        own = norm_crate(str(meta.get("crate") or "")) or str(meta.get("crate") or "").strip()
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


LORE_HOUSES = {
    "librarian": "librarian",
    "detective": "detective",
    "agent": "detective",
    "charlie": "charlie",
    "tps": "tps",
}


def lore_house_label(house: str = "", mouth: str = "") -> str:
    h = mouth_canon((house or "").strip().lower())
    if h in ("librarian", "detective", "charlie", "tps"):
        return h
    m = mouth_canon((mouth or "").strip().lower())
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
    return f"{klass} Â· {title}"


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
    """YAML strip: or color: â€” a #hex, or a named hue."""
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
        for fname in (INDEX_NAME, INDEX_LEGACY, PAPER_NAME):
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
    """Put --card-strip and house-* class on the .lorecard.

    Body look comes from house class (lorecard.css lookbook). Strip/edition hue
    still rides --card-strip. Missing house keeps neutral traveler cream.
    """
    if not is_lore_card(meta):
        return inner
    strip = css_hex(card_strip_color(meta))
    house = lore_house_label(str((meta or {}).get("house") or ""))
    house_cls = f"house-{house}" if house in LORE_HOUSES else ""
    if not strip and not house_cls:
        return inner

    # Class openings longest-first so has-back wins over bare lorecard.
    opens = (
        'class="lorecard has-back"',
        'class="lorecard"',
        "class='lorecard has-back'",
        "class='lorecard'",
    )
    for old in opens:
        if old not in inner:
            continue
        quote = '"' if old.startswith("class=\"") else "'"
        # Rebuild class list, append house if needed
        core = old[len("class=") + 1 : -1]  # inside quotes
        bits = core.split()
        if house_cls and house_cls not in bits:
            bits.append(house_cls)
        new_class = f"class={quote}{' '.join(bits)}{quote}"
        # Decide style bit
        style_bit = ""
        if strip and "--card-strip:" not in inner:
            style_bit = f' style="--card-strip:{strip}"'
        return inner.replace(old, new_class + style_bit, 1)
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
    mouth = mouth_canon(mouth)
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
    folder = nearest_index_folder(target)
    obj["route"] = pocket_key(folder or target)
    if folder is not None:
        obj["shell_name"] = nearest_index_title(folder)
    shell = catalog_shell_of(mouth, target, dest)
    if shell is not None:
        obj["shell"] = shell
        obj["here"] = "page"
        return obj
    here_shell = False
    if folder is not None:
        shell_dest = shelf_file(mouth, folder)
        if dest is not None and shell_dest is not None:
            try:
                here_shell = dest.resolve() == shell_dest.resolve()
            except OSError:
                here_shell = False
    if here_shell:
        obj["here"] = "shell"
        obj["onto"] = "shell"
    else:
        obj["here"] = "page"
    return obj


def catalog_payload(mouth: str, dest: Path, pocket: str, crate: str) -> dict:
    mouth = mouth_canon(mouth)
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
    if mouth == "detective":
        obj["hunts"] = hunts_for_crate(crate or str(obj.get("crate") or ""), bank="detective")
    elif mouth == "librarian":
        obj["hunts"] = hunts_for_crate(crate or str(obj.get("crate") or ""), bank="librarian")
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
    mouth = mouth_canon(mouth)
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
        for zip_code in chip_codes_from_blob(str(stored or "")):
            ensure_code_chain(zip_code)
    obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
    return 200, obj, ""


def catalog_field_update(
    mouth: str, pocket_raw: str, index: int, kind: str, label: str, value, onto: str = ""
) -> tuple[int, dict | None, str]:
    mouth = mouth_canon(mouth)
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
        for zip_code in chip_codes_from_blob(str(stored or "")):
            ensure_code_chain(zip_code)
    obj = catalog_view(mouth, target) or catalog_payload(mouth, dest, pocket, crate)
    return 200, obj, ""


def catalog_field_delete(
    mouth: str, pocket_raw: str, index: int, onto: str = ""
) -> tuple[int, dict | None, str]:
    mouth = mouth_canon(mouth)
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
    mouth = mouth_canon(mouth)
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



def hunt_case_rel(target: Path, bank: str = "detective") -> str:
    """Folder under the blotter host for slips born on this page."""
    spec = blotter_spec(bank)
    root = blotter_root(bank)
    host = host_for_path(target)
    name = host.name if host is not None else (active_host() or "start")
    if name == spec.slug:
        here = target.parent if target.is_file() else target
        try:
            rel = here.resolve().relative_to(root.resolve()).as_posix()
        except (OSError, ValueError):
            rel = ""
        return rel.strip("/")
    ctx = using_host(host) if host is not None else using_host(None)
    with ctx:
        key = pocket_key(target)
    _host, rel = split_pocket(key)
    rel = (rel or "").replace("\\", "/").strip("/")
    reserved = {n.lower() for n in RESERVED_NOTES}
    if rel.lower().endswith(".md"):
        parent, leaf = (rel.rsplit("/", 1) if "/" in rel else ("", rel))
        if leaf.lower() in reserved:
            rel = parent
        else:
            rel = (parent + "/" + Path(leaf).stem).strip("/")
    return (name + "/" + rel).strip("/")


def hunt_unique_path(folder: Path, fname: str) -> Path:
    dest = folder / fname
    if not dest.exists():
        return dest
    stem = Path(fname).stem
    for i in range(2, 80):
        cand = folder / f"{stem}-{i}.md"
        if not cand.exists():
            return cand
    return folder / f"{stem}-{int(time.time())}.md"


def hunt_note_href(rel: str, bank: str = "detective") -> str:
    spec = blotter_spec(bank)
    host = get_host(spec.slug)
    if host is None:
        return "/?h=" + quote(spec.slug)
    with using_host(host):
        return page_href(rel)


def iter_hunt_notes(bank: str = "detective") -> list[Path]:
    root = blotter_root(bank)
    if not root.is_dir():
        return []
    hide = {n.lower() for n in RESERVED_NOTES}
    out: list[Path] = []
    for p in root.rglob("*.md"):
        parts = p.relative_to(root).parts
        if any(part in SKIP or stash_name(part) for part in parts):
            continue
        if p.name.lower() in hide:
            continue
        out.append(p)
    return out


def hunt_thought_body(body: str) -> str:
    lines = (body or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].strip() == "# {{title}}":
        i += 1
        if i < len(lines) and not lines[i].strip():
            i += 1
    return "\n".join(lines[i:]).strip()


def hunt_path_for_crate(crate: str, bank: str = "detective") -> Path | None:
    want = norm_crate(crate)
    if not want:
        return None
    for p in iter_hunt_notes(bank):
        meta = read_md_meta(p)
        if norm_crate(str(meta.get("crate") or "")) == want:
            return p
    return None


def hunt_created_at(path: Path, meta: dict | None = None) -> int:
    raw = str((meta or {}).get("tps") or "").strip()
    try:
        at = int(float(raw))
        if at > 0:
            return at
    except (TypeError, ValueError):
        pass
    try:
        return int(path.stat().st_mtime)
    except OSError:
        return 0


def hunt_record(path: Path, bank: str | None = None) -> dict | None:
    if not path.is_file():
        return None
    use = bank or blotter_bank_for_path(path)
    root = blotter_root(use)
    try:
        rel = path.relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = parse_fm(text)
    title = str(meta.get("title") or "").strip() or path.stem
    at = hunt_created_at(path, meta)
    when = tps_when(at) if at else ""
    return {
        "title": title,
        "href": hunt_note_href(rel, use),
        "rel": rel,
        "crate": norm_crate(str(meta.get("crate") or "")),
        "source_crate": norm_crate(str(meta.get("source_crate") or "")),
        "from": str(meta.get("from") or "").strip(),
        "mindset": str(meta.get("mindset") or "").strip(),
        "at": at,
        "when": when,
        "body": hunt_thought_body(body or ""),
        "snippet": " ".join(
            ln
            for ln in (body or "").splitlines()
            if ln.strip() and ln.strip() != "# {{title}}"
        )[:180],
    }


def hunts_for_crate(crate: str, bank: str = "detective") -> list[dict]:
    want = norm_crate(crate)
    if not want:
        return []
    hits: list[dict] = []
    for p in iter_hunt_notes(bank):
        meta = read_md_meta(p)
        src = norm_crate(str(meta.get("source_crate") or ""))
        edges = [
            norm_crate(x) for x in parse_flow_list(str(meta.get("edges") or ""))
        ]
        if src != want and want not in edges:
            continue
        rec = hunt_record(p, bank)
        if rec:
            hits.append(rec)
    hits.sort(key=lambda h: int(h.get("at") or 0), reverse=True)
    return hits[:80]


def hunt_search_notes(q: str, bank: str = "detective") -> list[dict]:
    needle = (q or "").strip().lower()
    if not needle:
        return []
    hits: list[dict] = []
    for p in iter_hunt_notes(bank):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        meta, body = parse_fm(text)
        blob = " ".join(
            [
                str(meta.get("title") or ""),
                str(meta.get("mindset") or ""),
                str(meta.get("from") or ""),
                body or "",
            ]
        ).lower()
        if needle not in blob:
            continue
        rec = hunt_record(p, bank)
        if rec:
            hits.append(rec)
    hits.sort(key=lambda h: int(h.get("at") or 0), reverse=True)
    return hits[:40]


def hunt_search_form(bank: str = "detective") -> str:
    spec = blotter_spec(bank)
    q = html.escape(_HUNT_Q.get() or "", True)
    return (
        '<form class="tag-search" method="get" action="/">'
        + '<input type="hidden" name="h" value="'
        + html.escape(spec.slug, True)
        + '">'
        + '<input type="search" name="'
        + html.escape(spec.q_name, True)
        + '" value="'
        + q
        + '" placeholder="'
        + html.escape(spec.search_ph, True)
        + '" '
        + 'autocomplete="off" spellcheck="false">'
        + '<button type="submit">'
        + html.escape(spec.search_btn)
        + "</button>"
        + "</form>"
    )


def paint_hunt_slip_meta(hit: dict) -> str:
    """When / mindset / from — same strip search results use."""
    parts: list[str] = ['<div class="hunt-slip-meta">']
    when = str(hit.get("when") or "").strip()
    if when:
        parts.append('<time class="hunt-when">' + html.escape(when) + "</time>")
    mind = str(hit.get("mindset") or "").strip()
    if mind:
        parts.append('<span class="hunt-mind">' + html.escape(mind) + "</span>")
    frm = str(hit.get("from") or "").strip()
    if frm:
        parts.append('<span class="hit-from">' + html.escape(frm) + "</span>")
    parts.append("</div>")
    if len(parts) == 2:
        return ""
    return "".join(parts)


def paint_hunt_slip(
    hit: dict, n: int = 1, *, link_title: bool = True, body: str | None = None
) -> str:
    """One blotter slip card — shared by hunt search, shelf faces, and open pages."""
    n = ((int(n) - 1) % 3) + 1
    href = html.escape(str(hit.get("href") or ""), True)
    title = html.escape(str(hit.get("title") or "slip"))
    parts: list[str] = [
        f'<article class="hunt-slip hunt-slip-n{n}">',
    ]
    if link_title and href:
        parts.append(f'<a class="hunt-slip-title" href="{href}">{title}</a>')
    else:
        parts.append(f'<span class="hunt-slip-title">{title}</span>')
    snip = (body if body is not None else str(hit.get("snippet") or "")).strip()
    if snip:
        # body may already be HTML (open page); snippets stay escaped
        if body is not None:
            parts.append('<div class="hunt-slip-body">' + snip + "</div>")
        else:
            parts.append('<p class="hunt-slip-body">' + html.escape(snip) + "</p>")
    parts.append(paint_hunt_slip_meta(hit))
    parts.append("</article>")
    return "".join(parts)


def wrap_hunt_open_page(inner: str, hit: dict) -> str:
    """Open slip: title + body like search, mindset strip under the thought."""
    meta = paint_hunt_slip_meta(hit)
    raw = (inner or "").lstrip()
    m = re.match(r"(<h1\b[^>]*>)(.*?)(</h1>)", raw, re.I | re.S)
    if m:
        title_html = m.group(2)
        rest = raw[m.end() :]
        return (
            '<article class="hunt-slip hunt-slip-open hunt-slip-n1">'
            + '<span class="hunt-slip-title">'
            + title_html
            + "</span>"
            + rest
            + meta
            + "</article>"
        )
    return (
        '<article class="hunt-slip hunt-slip-open hunt-slip-n1">'
        + raw
        + meta
        + "</article>"
    )

def hunt_look_block(bank: str = "detective") -> str:
    spec = blotter_spec(bank)
    q = (_HUNT_Q.get() or "").strip()
    if active_host() != spec.slug:
        return ""
    if not q:
        return ""
    hits = hunt_search_notes(q, bank)
    if not hits:
        return (
            '<div class="huntlook taglook-empty">'
            + spec.look_miss
            + html.escape(q)
            + "</div>"
        )
    items: list[str] = []
    for i, hit in enumerate(hits):
        items.append("<li>" + paint_hunt_slip(hit, n=(i % 3) + 1) + "</li>")
    return (
        '<div class="huntlook">'
        '<div class="huntlook-mark">'
        + html.escape(spec.look_mark)
        + "</div>"
        "<ul>"
        + "".join(items)
        + "</ul></div>"
    )


def hunt_ensure_case_paper(
    folder: Path,
    source_crate: str = "",
    bank: str = "detective",
    face_crate: str = "",
) -> None:
    """Page shelf paper: source page face (if known) + slips in this folder only."""
    spec = blotter_spec(bank)
    try:
        root = blotter_root(bank).resolve()
        here = folder.resolve()
        if here == root:
            return
        here.relative_to(root)
    except (OSError, ValueError):
        return
    paper = folder / PAPER_NAME
    if paper.is_file():
        return
    crate = mint_crate_id()
    src = norm_crate(source_crate)
    face = norm_crate(face_crate) or src
    lines = [
        "---",
        "crate: " + crate,
        "title: " + yaml_scalar(folder.name),
        "environment: " + spec.environment,
    ]
    if src:
        lines.append("source_crate: " + src)
    lines.extend(["---", ""])
    if face:
        lines.append("{{face:" + face + "}}")
        lines.append("")
    lines.append("{{faces}}")
    lines.append("")
    try:
        paper.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    except OSError:
        return



def hunt_shelf_rel_from_label(from_label: str) -> str:
    """Map a slip `from:` label to a go.detective-relative page shelf path."""
    s = (from_label or "").strip().replace("\\", "/")
    if s.lower().startswith("go."):
        s = s[3:]
    s = s.strip("/")
    if not s:
        return ""
    low = s.lower()
    for leaf in ("/index.md", "/_shell.md", "/_index.md"):
        if low.endswith(leaf):
            return s[: -len(leaf)].strip("/")
    if low.endswith(".md"):
        parent, leaf = (s.rsplit("/", 1) if "/" in s else ("", s))
        return (parent + "/" + Path(leaf).stem).strip("/")
    return s


def hunt_migrate_page_shelves() -> dict:
    """Move hall-flat hunt slips into page shelves using `from` / source_crate."""
    moved = 0
    skipped = 0
    ensured = 0
    errors: list[str] = []
    for p in list(iter_hunt_notes()):
        meta = read_md_meta(p)
        kind = str(meta.get("kind") or "").strip().lower()
        src = norm_crate(str(meta.get("source_crate") or ""))
        if kind != "hunt" and not src:
            skipped += 1
            continue
        from_label = str(meta.get("from") or "").strip()
        shelf = hunt_shelf_rel_from_label(from_label)
        if not shelf and src:
            src_file = find_file_by_crate(src)
            if src_file is not None:
                shelf = hunt_case_rel(src_file)
        if not shelf:
            skipped += 1
            continue
        dest_folder = DETECTIVE_HOST.joinpath(*shelf.split("/"))
        try:
            same = p.parent.resolve() == dest_folder.resolve()
        except OSError:
            same = False
        if same:
            before = (dest_folder / PAPER_NAME).is_file()
            hunt_ensure_case_paper(dest_folder, source_crate=src)
            if not before and (dest_folder / PAPER_NAME).is_file():
                ensured += 1
            skipped += 1
            continue
        try:
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest = hunt_unique_path(dest_folder, p.name)
            shutil.move(str(p), str(dest))
            hunt_ensure_case_paper(dest_folder, source_crate=src)
            moved += 1
            ensured += 1
        except OSError as exc:
            errors.append(f"{p}: {exc}")
    return {"moved": moved, "skipped": skipped, "ensured": ensured, "errors": errors}


def hunt_add(
    pocket_raw: str, title: str, body: str, mindset: str = "", bank: str = "detective"
) -> tuple[int, dict | None, str]:
    """Mint a thought slip on the blotter host, hanging on the page you were on."""
    spec = blotter_spec(bank)
    root = blotter_root(bank)
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    mindset = (mindset or "").replace("\r\n", " ").replace("\r", " ").strip()
    if len(body) > LEAF_MAX:
        return 413, None, "thought too long"
    if len(title) > 120:
        title = title[:120].rstrip()
    if not title:
        title = (body.split("\n", 1)[0].strip() if body else "")[:80]
    if not title:
        return 400, None, "need a thought"
    fname = note_filename(title)
    if not fname:
        return 400, None, "bad name"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        target = resolve_vault_page(pocket_raw)
        if target is None:
            return 400, None, "not a vault page"
        src_file = crate_file_for(target) or (target if target.is_file() else None)
        if src_file is None:
            return 400, None, "no crate on this page"
        source_crate = ensure_crate(src_file)
        if not source_crate:
            return 400, None, "no crate on this page"
        src_meta = read_md_meta(src_file) if src_file.is_file() else {}
        face_crate = source_crate
        nested = norm_crate(str(src_meta.get("source_crate") or ""))
        if nested and is_blotter_note(src_meta):
            face_crate = nested
        case_rel = hunt_case_rel(target, bank)
        from_label = ("go." + case_rel) if case_rel else (lore_from_room(target) or "")
        at = int(time.time())
        own = mint_crate_id()
        folder = root.joinpath(*case_rel.split("/")) if case_rel else root
        folder.mkdir(parents=True, exist_ok=True)
        hunt_ensure_case_paper(
            folder, source_crate=source_crate, bank=bank, face_crate=face_crate
        )
        dest = hunt_unique_path(folder, fname)
        lines = [
            "---",
            "crate: " + own,
            "title: " + yaml_scalar(title),
            "kind: " + spec.kind,
            "environment: " + spec.environment,
            "source_crate: " + source_crate,
            "edges: [" + source_crate + "]",
            "from: " + yaml_scalar(from_label),
            "tps: " + str(at),
        ]
        if mindset:
            lines.append("mindset: " + yaml_scalar(mindset))
        lines.extend(["---", "", "# {{title}}", ""])
        if body:
            lines.append(body)
            lines.append("")
        with LBR_LOCK:
            write_note(dest, "\n".join(lines))
        blot_host = get_host(spec.slug)
        rec = None
        if blot_host is not None:
            with using_host(blot_host):
                tps_stamp_quiet(dest, "created", at)
                rec = hunt_record(dest, bank)
        if rec is None:
            rec = hunt_record(dest, bank)
        obj = catalog_view(spec.mouth, target)
        if obj is None:
            obj = {"hunts": [], "fields": [], "lore": []}
        obj["hunt"] = rec or {
            "title": title,
            "href": hunt_note_href(
                dest.relative_to(root.resolve()).as_posix(), bank
            ),
        }
        return 200, obj, ""


def hunt_blot(pocket_raw: str, bank: str = "detective") -> dict:
    spec = blotter_spec(bank)
    with using_pocket(pocket_raw) as host:
        target = resolve_vault_page(pocket_raw) if host is not None else None
        obj = catalog_view(spec.mouth, target) if target is not None else None
    if obj is None:
        obj = {"hunts": [], "fields": [], "lore": []}
    return obj


def hunt_drop_sidecars(dest: Path, bank: str = "detective") -> None:
    spec = blotter_spec(bank)
    blot_host = get_host(spec.slug)
    if blot_host is None:
        return
    with using_host(blot_host):
        for kind in ("tps", "librarian", "detective", "charlie"):
            y = shelf_file(kind, dest)
            if y is not None and y.is_file():
                try:
                    y.unlink()
                except OSError:
                    pass


def hunt_prune_empty(folder: Path, bank: str = "detective") -> None:
    stop = blotter_root(bank).resolve()
    try:
        cur = folder.resolve()
    except OSError:
        return
    while cur != stop:
        try:
            if not cur.is_dir() or any(cur.iterdir()):
                break
            parent = cur.parent
            cur.rmdir()
            cur = parent
        except OSError:
            break


def hunt_save(
    pocket_raw: str,
    crate: str,
    title: str,
    body: str,
    mindset: str = "",
    bank: str = "detective",
) -> tuple[int, dict | None, str]:
    spec = blotter_spec(bank)
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    mindset = (mindset or "").replace("\r\n", " ").replace("\r", " ").strip()
    if len(body) > LEAF_MAX:
        return 413, None, "thought too long"
    if len(title) > 120:
        title = title[:120].rstrip()
    if not title:
        title = (body.split("\n", 1)[0].strip() if body else "")[:80]
    if not title:
        return 400, None, "need a thought"
    dest = hunt_path_for_crate(crate, bank)
    if dest is None:
        return 404, None, "no such slip"
    try:
        text = dest.read_text(encoding="utf-8")
    except OSError:
        return 404, None, "no such slip"
    meta, _old = parse_fm(text)
    own = norm_crate(str(meta.get("crate") or crate))
    source_crate = norm_crate(str(meta.get("source_crate") or ""))
    edges_raw = str(meta.get("edges") or "").strip()
    if not edges_raw and source_crate:
        edges_raw = "[" + source_crate + "]"
    from_label = str(meta.get("from") or "").strip()
    at = hunt_created_at(dest, meta)
    fname = note_filename(title)
    if not fname:
        return 400, None, "bad name"
    lines = [
        "---",
        "crate: " + own,
        "title: " + yaml_scalar(title),
        "kind: " + spec.kind,
        "environment: " + spec.environment,
    ]
    if source_crate:
        lines.append("source_crate: " + source_crate)
    if edges_raw:
        lines.append("edges: " + edges_raw)
    if from_label:
        lines.append("from: " + yaml_scalar(from_label))
    if at:
        lines.append("tps: " + str(at))
    if mindset:
        lines.append("mindset: " + yaml_scalar(mindset))
    lines.extend(["---", "", "# {{title}}", ""])
    if body:
        lines.append(body)
        lines.append("")
    new_text = "\n".join(lines)
    want = dest.parent / fname
    with LBR_LOCK:
        if want.resolve() != dest.resolve():
            fresh = hunt_unique_path(dest.parent, fname)
            hunt_drop_sidecars(dest, bank)
            write_note(fresh, new_text)
            try:
                dest.unlink()
            except OSError:
                pass
            dest = fresh
            blot_host = get_host(spec.slug)
            if blot_host is not None and at:
                with using_host(blot_host):
                    tps_stamp_quiet(dest, "created", at)
        else:
            write_note(dest, new_text)
    rec = hunt_record(dest, bank)
    obj = hunt_blot(pocket_raw, bank)
    obj["hunt"] = rec or {"title": title}
    return 200, obj, ""


def hunt_drop(
    pocket_raw: str, crate: str, bank: str = "detective"
) -> tuple[int, dict | None, str]:
    dest = hunt_path_for_crate(crate, bank)
    if dest is None:
        return 404, None, "no such slip"
    folder = dest.parent
    hunt_drop_sidecars(dest, bank)
    try:
        dest.unlink()
    except OSError:
        return 500, None, "could not drop"
    hunt_prune_empty(folder, bank)
    obj = hunt_blot(pocket_raw, bank)
    return 200, obj, ""


def era_sits_load() -> list[dict]:
    """Every TPS tagging of a named era. One row is one page, one time."""
    dest = ERA_SITS_FILE
    if not dest.is_file():
        return []
    try:
        text = dest.read_text(encoding="utf-8")
    except OSError:
        return []
    rows: list[dict] = []
    cur: dict | None = None
    in_sits = False
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "sits:" or stripped.startswith("sits:"):
            in_sits = True
            if stripped != "sits:" and stripped[5:].strip() in ("", "[]"):
                continue
            continue
        if not in_sits:
            continue
        if stripped.startswith("- ") and ":" in stripped:
            if cur:
                rows.append(cur)
            cur = {
                "id": "",
                "era": "",
                "crate": "",
                "pocket": "",
                "at": 0,
                "note": "",
            }
            rest = stripped[2:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                era_sit_apply(cur, k.strip().lower(), v.strip().strip('"').strip("'"))
            continue
        if cur is not None and ":" in stripped:
            k, v = stripped.split(":", 1)
            era_sit_apply(cur, k.strip().lower(), v.strip().strip('"').strip("'"))
    if cur:
        rows.append(cur)
    out: list[dict] = []
    for row in rows:
        era = norm_crate(str(row.get("era") or ""))
        crate = norm_crate(str(row.get("crate") or ""))
        pocket = str(row.get("pocket") or "").strip()
        if not era or (not crate and not pocket):
            continue
        row["era"] = era
        row["crate"] = crate
        row["pocket"] = pocket
        try:
            row["at"] = int(row.get("at") or 0)
        except (TypeError, ValueError):
            row["at"] = 0
        out.append(row)
    return out


def era_sit_apply(cur: dict, k: str, v: str) -> None:
    if k == "id":
        cur["id"] = v
    elif k == "era":
        cur["era"] = v
    elif k in ("crate", "page", "source"):
        cur["crate"] = v
    elif k == "pocket":
        cur["pocket"] = v
    elif k == "at":
        try:
            cur["at"] = int(v)
        except ValueError:
            cur["at"] = 0
    elif k in ("note", "body", "sit"):
        cur["note"] = v


def era_sits_save(rows: list[dict]) -> None:
    lines = ["sits:"]
    if not rows:
        lines = ["sits: []"]
    else:
        for row in rows:
            if not isinstance(row, dict):
                continue
            era = norm_crate(str(row.get("era") or ""))
            crate = norm_crate(str(row.get("crate") or ""))
            pocket = str(row.get("pocket") or "").strip()
            if not era or (not crate and not pocket):
                continue
            try:
                at = int(row.get("at") or 0)
            except (TypeError, ValueError):
                at = 0
            sid = str(row.get("id") or "").strip() or ("sit-" + str(at or int(time.time())))
            lines.append("  - id: " + yaml_scalar(sid))
            lines.append("    era: " + yaml_scalar(era))
            if crate:
                lines.append("    crate: " + yaml_scalar(crate))
            if pocket:
                lines.append("    pocket: " + yaml_scalar(pocket))
            lines.append("    at: " + str(at))
            note = str(row.get("note") or "").strip()
            if note:
                lines.append("    note: " + yaml_scalar(note))
    ERA_SITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ERA_SITS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def era_sit_view(raw: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None
    era = norm_crate(str(raw.get("era") or ""))
    crate = norm_crate(str(raw.get("crate") or ""))
    pocket = str(raw.get("pocket") or "").strip()
    if not era or (not crate and not pocket):
        return None
    try:
        at = int(raw.get("at") or 0)
    except (TypeError, ValueError):
        at = 0
    href = href_from_pocket(pocket) if pocket else (crate_href(crate) if crate else "")
    title = ""
    if pocket:
        try:
            with using_pocket(pocket) as host:
                if host is not None:
                    title = pocket_title(pocket)
        except Exception:
            title = ""
    title = title or pocket.split("/")[-1] or crate
    slices = tps_slices_of(at, "clock") if at else {}
    return {
        "id": str(raw.get("id") or ""),
        "era": era,
        "crate": crate,
        "pocket": pocket,
        "href": href,
        "title": title,
        "at": at,
        "when": tps_when(at) if at else "",
        "when_href": tps_when_href(at, "clock", slices) if at else "",
        "note": str(raw.get("note") or "").strip(),
    }


def events_root() -> Path | None:
    """Events live flat on go.code.event. Filename is the event code."""
    host = event_host()
    if host is None:
        return None
    return host.root


def on_events_pad(rel: str = "") -> bool:
    host = event_host()
    return host is not None and active_host() == host.name


def event_code_norm(raw: str) -> str:
    s = (raw or "").strip().upper().replace(" ", "").replace("_", "-")
    s = s.lstrip("^")
    if s.endswith(".MD"):
        s = s[:-3]
    s = s.split(".", 1)[0]
    return s if s and EVENT_CODE_RE.fullmatch(s) else ""


def is_event_cite(raw: str) -> bool:
    return bool(event_code_norm(raw))


def event_code_from_path(path: Path, meta: dict | None = None) -> str:
    meta = meta or {}
    code = event_code_norm(str(meta.get("code") or meta.get("event") or ""))
    if code:
        return code
    return event_code_norm(path.stem)


def next_event_code(prefix: str = "EV") -> str:
    prefix = (prefix or "EV").strip().upper() or "EV"
    n = 0
    root = events_root()
    if root is not None and root.is_dir():
        for p in iter_era_notes():
            meta = read_md_meta(p)
            code = event_code_from_path(p, meta)
            if not code or not code.startswith(prefix + "-"):
                continue
            try:
                n = max(n, int(code.split("-", 1)[1]))
            except (TypeError, ValueError, IndexError):
                continue
    return prefix + "-" + str(n + 1).zfill(3)


def era_note_href(rel: str) -> str:
    slug = event_host_slug()
    path = (rel or "").replace("\\", "/").strip("/")
    if path.lower().startswith("events/"):
        path = path[7:]
    if not path:
        return "/?h=" + quote(slug)
    return "/?h=" + quote(slug) + "&p=" + quote(path, safe="/")


def iter_era_notes() -> list[Path]:
    """Named events live flat under go.code.event. Filename is the event code."""
    root = events_root()
    if root is None or not root.is_dir():
        return []
    hide = {n.lower() for n in RESERVED_NOTES}
    out: list[Path] = []
    try:
        kids = list(root.iterdir())
    except OSError:
        return []
    for p in kids:
        if not p.is_file() or p.suffix.lower() != ".md":
            continue
        if p.name.lower() in hide:
            continue
        if stash_name(p.name):
            continue
        meta = read_md_meta(p)
        kind = str(meta.get("kind") or "").strip().lower()
        if kind not in ("event", "era"):
            continue
        out.append(p)
    out.sort(key=lambda p: p.name.lower())
    return out


def era_path_for_crate(crate: str) -> Path | None:
    want = norm_crate(crate)
    if not want:
        return None
    for p in iter_era_notes():
        if norm_crate(str(read_md_meta(p).get("crate") or "")) == want:
            return p
    return None


def era_path_for_title(title: str) -> Path | None:
    fname = note_filename(title)
    want_stem = (Path(fname).stem.lower() if fname else "")
    want_title = (title or "").strip().lower()
    if not want_stem and not want_title:
        return None
    root = events_root()
    if fname and root is not None:
        dest = root / fname
        kind = str(read_md_meta(dest).get("kind") or "").strip().lower() if dest.is_file() else ""
        if dest.is_file() and kind in ("event", "era"):
            return dest
    for p in iter_era_notes():
        if want_stem and p.stem.lower() == want_stem:
            return p
        meta = read_md_meta(p)
        if want_title and str(meta.get("title") or "").strip().lower() == want_title:
            return p
    return None


def era_record(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        root = events_root()
        if root is None:
            return None
        rel = path.relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = parse_fm(text)
    title = str(meta.get("title") or "").strip() or path.stem
    at = hunt_created_at(path, meta)
    when = tps_when(at) if at else ""
    sit = str(
        meta.get("perspective")
        or meta.get("sit")
        or meta.get("era")
        or ""
    ).strip()
    own = norm_crate(str(meta.get("crate") or ""))
    code = event_code_from_path(path, meta)
    return {
        "title": title,
        "code": code,
        "href": era_note_href(rel),
        "rel": rel,
        "crate": own,
        "perspective": sit,
        "at": at,
        "when": when,
        "body": hunt_thought_body(body or ""),
        "snippet": " ".join(
            ln
            for ln in (body or "").splitlines()
            if ln.strip() and ln.strip() != "# {{title}}"
        )[:180],
    }


def era_name_list() -> list[dict]:
    out: list[dict] = []
    for p in iter_era_notes():
        rec = era_record(p)
        if not rec:
            continue
        out.append(
            {
                "title": rec.get("title") or "",
                "code": rec.get("code") or "",
                "crate": rec.get("crate") or "",
                "perspective": rec.get("perspective") or "",
                "href": rec.get("href") or "",
            }
        )
    out.sort(key=lambda r: str(r.get("title") or "").lower())
    return out


def era_sits_for(era_crate: str) -> list[dict]:
    want = norm_crate(era_crate)
    if not want:
        return []
    hits: list[dict] = []
    for row in era_sits_load():
        if norm_crate(str(row.get("era") or "")) != want:
            continue
        view = era_sit_view(row)
        if view:
            hits.append(view)
    hits.sort(key=lambda h: int(h.get("at") or 0), reverse=True)
    return hits[:80]


def eras_for_crate(crate: str) -> list[dict]:
    """Eras this page has been tagged onto, with this sit's when/note."""
    want = norm_crate(crate)
    if not want:
        return []
    by_era: dict[str, dict] = {}
    for row in era_sits_load():
        if norm_crate(str(row.get("crate") or "")) != want:
            continue
        era = norm_crate(str(row.get("era") or ""))
        dest = era_path_for_crate(era)
        rec = era_record(dest) if dest is not None else None
        if rec is None:
            continue
        view = era_sit_view(row) or {}
        item = dict(rec)
        item["sit_id"] = view.get("id") or ""
        item["sit_at"] = view.get("at") or 0
        item["when"] = view.get("when") or rec.get("when") or ""
        item["body"] = view.get("note") or rec.get("body") or ""
        item["snippet"] = (view.get("note") or rec.get("snippet") or "")[:180]
        by_era[era] = item
    hits = list(by_era.values())
    hits.sort(key=lambda h: int(h.get("sit_at") or h.get("at") or 0), reverse=True)
    return hits[:80]


def era_search_notes(q: str) -> list[dict]:
    needle = (q or "").strip().lower()
    if not needle:
        return [r for r in (era_record(p) for p in iter_era_notes()) if r]
    hits: list[dict] = []
    sits = era_sits_load()
    notes_by_era: dict[str, list[str]] = {}
    for row in sits:
        era = norm_crate(str(row.get("era") or ""))
        blob = " ".join(
            [
                str(row.get("pocket") or ""),
                str(row.get("note") or ""),
                str(row.get("crate") or ""),
            ]
        )
        notes_by_era.setdefault(era, []).append(blob)
    for p in iter_era_notes():
        rec = era_record(p)
        if rec is None:
            continue
        extra = " ".join(notes_by_era.get(str(rec.get("crate") or ""), []))
        blob = " ".join(
            [
                str(rec.get("title") or ""),
                str(rec.get("perspective") or ""),
                str(rec.get("body") or ""),
                extra,
            ]
        ).lower()
        if needle not in blob:
            continue
        hits.append(rec)
    hits.sort(key=lambda h: str(h.get("title") or "").lower())
    return hits[:40]


def era_path_for_code(code: str) -> Path | None:
    want = event_code_norm(code)
    if not want:
        return None
    root = events_root()
    if root is not None:
        dest = root / (want + ".md")
        if dest.is_file():
            return dest
    for p in iter_era_notes():
        if event_code_from_path(p, read_md_meta(p)) == want:
            return p
    return None


def era_search_form() -> str:
    q = html.escape(_ERA_Q.get() or "", True)
    slug = html.escape(event_host_slug(), True)
    return (
        '<form class="tag-search era-search" method="get" action="/">'
        + '<input type="hidden" name="h" value="'
        + slug
        + '">'
        + '<input type="search" name="event" value="'
        + q
        + '" placeholder="an event, a code" '
        + 'autocomplete="off" spellcheck="false">'
        + '<button type="submit">look</button>'
        + "</form>"
    )


def era_sit_li(sit: dict) -> str:
    href = html.escape(str(sit.get("href") or "#"), True)
    title = html.escape(str(sit.get("title") or sit.get("pocket") or "page"))
    when = str(sit.get("when") or "").strip()
    when_href = str(sit.get("when_href") or "").strip()
    note = str(sit.get("note") or "").strip()
    parts = [
        '<li class="era-sit-row">',
        '<a class="era-sit-page" href="',
        href,
        '">',
        title,
        "</a>",
    ]
    if when:
        if when_href:
            parts.extend(
                [
                    '<a class="era-sit-when" href="',
                    html.escape(when_href, True),
                    '">',
                    html.escape(when),
                    "</a>",
                ]
            )
        else:
            parts.append('<span class="era-sit-when">' + html.escape(when) + "</span>")
    if note:
        parts.append('<p class="era-sit-note">' + html.escape(note) + "</p>")
    parts.append("</li>")
    return "".join(parts)


def era_entry_html(rec: dict, sits: list[dict], n: int) -> str:
    href = html.escape(str(rec.get("href") or "#"), True)
    title = html.escape(str(rec.get("title") or "event"))
    code = str(rec.get("code") or "").strip()
    sit = str(rec.get("perspective") or "").strip()
    parts = [
        '<article class="era-entry era-slip era-slip-n',
        str((n % 3) + 1),
        '">',
        '<a class="era-slip-title" href="',
        href,
        '">',
        title,
        "</a>",
    ]
    if code:
        parts.append('<p class="era-code">' + html.escape(code) + "</p>")
    if sit:
        parts.append('<p class="era-sit">' + html.escape(sit) + "</p>")
    if sits:
        parts.append('<ul class="era-sits">')
        parts.extend(era_sit_li(s) for s in sits)
        parts.append("</ul>")
    else:
        parts.append(
            '<p class="era-sits-empty">not tagged on a TPS yet</p>'
        )
    parts.append("</article>")
    return "".join(parts)


def era_look_block(rel: str = "", meta: dict | None = None) -> str:
    """Printout: noted events, then each TPS tagging, linking back to the page."""
    if not on_events_pad(rel):
        return ""
    q = (_ERA_Q.get() or "").strip()
    meta = meta or {}
    here = (rel or "").replace("\\", "/").strip("/")
    here_path: Path | None = None
    root = events_root()
    leaf = here.split("/")[-1] if here else ""
    if root is not None and leaf and leaf.lower() not in {n.lower() for n in RESERVED_NOTES}:
        cand = root / leaf
        kind = str(read_md_meta(cand).get("kind") or "").strip().lower() if cand.is_file() else ""
        if cand.is_file() and kind in ("event", "era"):
            here_path = cand
    if q:
        recs = era_search_notes(q)
        mark = "on the line"
        if not recs:
            return (
                '<div class="eralook taglook-empty">'
                "nothing on this worldline matches "
                + html.escape(q)
                + "</div>"
            )
    elif here_path is not None:
        rec = era_record(here_path)
        sits = era_sits_for(str((rec or {}).get("crate") or ""))
        if not sits:
            return (
                '<div class="eralook taglook-empty">'
                "not tagged on a TPS yet"
                "</div>"
            )
        items = ["<li>" + era_sit_li(s) + "</li>" for s in sits]
        return (
            '<div class="eralook era-ledger">'
            '<div class="eralook-mark">tagged on TPS</div>'
            '<ul class="era-sits">'
            + "".join(items)
            + "</ul></div>"
        )
    else:
        recs = era_search_notes("")
        mark = "noted events"
        if not recs:
            return (
                '<div class="eralook taglook-empty">'
                "no events on the line yet. pin one from TPS."
                "</div>"
            )
    items: list[str] = []
    for i, rec in enumerate(recs):
        sits = era_sits_for(str(rec.get("crate") or ""))
        items.append("<li>" + era_entry_html(rec, sits, i) + "</li>")
    return (
        '<div class="eralook era-ledger">'
        '<div class="eralook-mark">'
        + html.escape(mark)
        + "</div>"
        "<ul>"
        + "".join(items)
        + "</ul></div>"
    )


def era_write_note(
    dest: Path,
    *,
    own: str,
    title: str,
    sit: str,
    body: str | None,
    code: str = "",
) -> None:
    old_body = ""
    old_meta: dict = {}
    if dest.is_file() and body is None:
        try:
            old_meta, old_body = parse_fm(dest.read_text(encoding="utf-8"))
        except OSError:
            old_body = ""
        old_body = hunt_thought_body(old_body or "")
    use_body = old_body if body is None else (body or "").strip()
    use_code = event_code_norm(code) or event_code_from_path(dest, old_meta)
    lines = [
        "---",
        "crate: " + own,
        "title: " + yaml_scalar(title),
        "kind: event",
        "environment: event",
    ]
    if use_code:
        lines.append("code: " + use_code)
    if sit:
        lines.append("perspective: " + yaml_scalar(sit))
    lines.extend(["---", "", "# {{title}}", ""])
    if use_body:
        lines.append(use_body)
        lines.append("")
    write_note(dest, "\n".join(lines))


def ensure_events_index() -> None:
    root = events_root()
    host = event_host()
    if root is None or host is None:
        return
    dest = root / PAPER_NAME
    if dest.is_file():
        return
    root.mkdir(parents=True, exist_ok=True)
    crate = mint_crate_id()
    write_note(
        dest,
        "\n".join(
            [
                "---",
                "crate: " + crate,
                "title: events",
                "environment: event",
                "kind: bay",
                "---",
                "",
                "# events",
                "",
                "{{eventsearch}}",
                "",
                "{{eventlook}}",
                "",
            ]
        ),
    )


def era_mint(title: str, sit: str, code: str = "") -> tuple[Path | None, str]:
    title = (title or "").strip()
    sit = (sit or "").replace("\r\n", " ").replace("\r", " ").strip()
    if not title:
        return None, "need an event"
    root = events_root()
    if root is None:
        return None, "no event host"
    use_code = event_code_norm(code) or next_event_code()
    ensure_events_index()
    dest = root / (use_code + ".md")
    if dest.exists():
        dest = era_unique_path(root, use_code + ".md")
        use_code = dest.stem.upper()
    own = mint_crate_id()
    era_write_note(dest, own=own, title=title, sit=sit, body="", code=use_code)
    pad = event_host()
    if pad is not None:
        with using_host(pad):
            tps_stamp_quiet(dest, "created", int(time.time()))
    return dest, ""


def era_unique_path(folder: Path, fname: str) -> Path:
    dest = folder / fname
    if not dest.exists():
        return dest
    stem = Path(fname).stem
    for i in range(2, 80):
        cand = folder / f"{stem}-{i}.md"
        if not cand.exists():
            return cand
    return folder / f"{stem}-{int(time.time())}.md"


def era_tag_page(
    era_path: Path, page_crate: str, pocket: str, note: str, at: int
) -> dict | None:
    era_rec = era_record(era_path)
    if era_rec is None:
        return None
    era = str(era_rec.get("crate") or "")
    page_crate = norm_crate(page_crate)
    pocket = (pocket or "").strip()
    if not era or not page_crate:
        return None
    rows = era_sits_load()
    for row in rows:
        if norm_crate(str(row.get("era") or "")) != era:
            continue
        if norm_crate(str(row.get("crate") or "")) != page_crate:
            continue
        if note:
            row["note"] = note
        if pocket:
            row["pocket"] = pocket
        era_sits_save(rows)
        return era_sit_view(row)
    sid = "sit-" + str(at) + "-" + page_crate[-6:]
    row = {
        "id": sid,
        "era": era,
        "crate": page_crate,
        "pocket": pocket,
        "at": at,
        "note": (note or "").strip(),
    }
    rows.append(row)
    era_sits_save(rows)
    return era_sit_view(row)


def era_untag_page(era_crate: str, page_crate: str) -> bool:
    era = norm_crate(era_crate)
    page = norm_crate(page_crate)
    if not era or not page:
        return False
    rows = era_sits_load()
    keep = [
        row
        for row in rows
        if not (
            norm_crate(str(row.get("era") or "")) == era
            and norm_crate(str(row.get("crate") or "")) == page
        )
    ]
    if len(keep) == len(rows):
        return False
    era_sits_save(keep)
    return True


def era_add(
    pocket_raw: str, title: str, body: str, sit: str = "", code: str = ""
) -> tuple[int, dict | None, str]:
    """Find or mint a named event, then tag this TPS page onto it."""
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    sit = (sit or "").replace("\r\n", " ").replace("\r", " ").strip()
    want_code = event_code_norm(code)
    if len(body) > LEAF_MAX:
        return 413, None, "event too long"
    if len(title) > 120:
        title = title[:120].rstrip()
    if not title:
        title = (body.split("\n", 1)[0].strip() if body else "")[:80]
    if not title:
        return 400, None, "need an event"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        target = resolve_vault_page(pocket_raw)
        if target is None:
            return 400, None, "not a vault page"
        src_file = crate_file_for(target) or (target if target.is_file() else None)
        if src_file is None:
            return 400, None, "no crate on this page"
        source_crate = ensure_crate(src_file)
        if not source_crate:
            return 400, None, "no crate on this page"
        pocket = pocket_key(target)
        dest = era_path_for_code(want_code) if want_code else None
        if dest is None:
            dest = era_path_for_title(title)
        if dest is None:
            dest, err = era_mint(title, sit, want_code)
            if dest is None:
                return 400, None, err
        else:
            rec0 = era_record(dest)
            own = str((rec0 or {}).get("crate") or "")
            have = str((rec0 or {}).get("perspective") or "")
            shown = str((rec0 or {}).get("title") or title)
            have_code = str((rec0 or {}).get("code") or "")
            if own and (sit and sit != have or (want_code and want_code != have_code)):
                era_write_note(
                    dest,
                    own=own,
                    title=shown,
                    sit=sit or have,
                    body=None,
                    code=want_code or have_code,
                )
        at = int(time.time())
        era_tag_page(dest, source_crate, pocket, body, at)
        rec = era_record(dest)
        obj = era_blot(pocket_raw)
        obj["era"] = rec or {"title": title, "href": era_note_href(dest.name)}
        return 200, obj, ""


def era_blot(pocket_raw: str) -> dict:
    with using_pocket(pocket_raw) as host:
        target = resolve_vault_page(pocket_raw) if host is not None else None
        if host is None or target is None:
            return {"stamps": [], "slices": {}, "eras": [], "lore": []}
        dest = shelf_file("tps", target)
        pocket = pocket_key(shelf_anchor("tps", target) if dest is not None else target)
        crate = bag_crate(shelf_anchor("tps", target) if dest is not None else target)
        if dest is None:
            return {
                "stamps": [],
                "slices": {},
                "eras": eras_for_crate(crate),
                "era_names": era_name_list(),
                "lore": lore_cards_for("tps", crate),
                "pocket": pocket,
                "crate": crate,
            }
        return tps_payload(dest, pocket, crate)


def era_save(
    pocket_raw: str, crate: str, title: str, body: str, sit: str = "", code: str = ""
) -> tuple[int, dict | None, str]:
    title = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    sit = (sit or "").replace("\r\n", " ").replace("\r", " ").strip()
    want_code = event_code_norm(code)
    if len(body) > LEAF_MAX:
        return 413, None, "event too long"
    if len(title) > 120:
        title = title[:120].rstrip()
    if not title:
        title = (body.split("\n", 1)[0].strip() if body else "")[:80]
    if not title:
        return 400, None, "need an event"
    dest = era_path_for_crate(crate)
    if dest is None:
        return 404, None, "no such event"
    rec = era_record(dest)
    if rec is None:
        return 404, None, "no such event"
    own = str(rec.get("crate") or crate)
    have_code = str(rec.get("code") or "")
    use_code = want_code or have_code or event_code_from_path(dest)
    era_write_note(dest, own=own, title=title, sit=sit, body=None, code=use_code)
    if use_code:
        want = dest.parent / (use_code + ".md")
        if want.resolve() != dest.resolve():
            fresh = era_unique_path(dest.parent, use_code + ".md")
            pad = event_host()
            if pad is not None:
                with using_host(pad):
                    for kind in ("tps", "librarian", "detective", "charlie"):
                        y = shelf_file(kind, dest)
                        z = shelf_file(kind, fresh)
                        if y is not None and y.is_file() and z is not None:
                            z.parent.mkdir(parents=True, exist_ok=True)
                            try:
                                y.replace(z)
                            except OSError:
                                pass
            try:
                dest.replace(fresh)
                dest = fresh
            except OSError:
                write_note(fresh, dest.read_text(encoding="utf-8"))
                try:
                    dest.unlink()
                except OSError:
                    pass
                dest = fresh
    with using_pocket(pocket_raw) as host:
        page_crate = ""
        pocket = ""
        if host is not None:
            target = resolve_vault_page(pocket_raw)
            if target is not None:
                src_file = crate_file_for(target) or (
                    target if target.is_file() else None
                )
                if src_file is not None:
                    page_crate = ensure_crate(src_file)
                pocket = pocket_key(target)
        if page_crate:
            era_tag_page(dest, page_crate, pocket, body, int(time.time()))
    rec = era_record(dest)
    obj = era_blot(pocket_raw)
    obj["era"] = rec or {"title": title}
    return 200, obj, ""


def era_drop(pocket_raw: str, crate: str) -> tuple[int, dict | None, str]:
    """Untag this page from the era. The era stays on the pad."""
    dest = era_path_for_crate(crate)
    if dest is None:
        return 404, None, "no such era"
    rec = era_record(dest)
    era = str((rec or {}).get("crate") or crate)
    page_crate = ""
    with using_pocket(pocket_raw) as host:
        if host is not None:
            target = resolve_vault_page(pocket_raw)
            if target is not None:
                page_crate = bag_crate(target)
    if not page_crate or not era_untag_page(era, page_crate):
        return 404, None, "not tagged"
    obj = era_blot(pocket_raw)
    return 200, obj, ""


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
    "detective": "Detective",
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
                if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
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
    mouth = mouth_canon(mouth)
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
    mouth = mouth_canon(mouth)
    spec = CATALOG.get(mouth)
    if not spec:
        return 400, None, "no such catalog"
    inbox = spec["inbox"]
    tray = spec["tray"]
    cards: list[dict] = []
    if inbox.is_dir():
        for p in sorted(inbox.glob("*.md"), key=lambda x: x.name.lower()):
            if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
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
                    "strip": css_hex(card_strip_color(meta)) or "",
                    "source_crate": norm_crate(str(meta.get("source_crate") or "")),
                    "edges": lore_edge_crates(meta),
                }
            )
    return 200, {"cards": cards, "house": spec["house"]}, ""


def catalog_lore_attach(
    mouth: str, pocket_raw: str, card_crate: str, onto: str = ""
) -> tuple[int, dict | None, str]:
    mouth = mouth_canon(mouth)
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
        edge_list = lore_edges_field(meta)
        already = crate in edge_list or norm_crate(str(meta.get("source_crate") or "")) == crate
        if not already:
            edge_list.append(crate)
            path.write_text(apply_lore_edges_fm(text, edge_list), encoding="utf-8")
        # If the open page is itself a lore card, stamp the attached card back onto it.
        try:
            page_text = target.read_text(encoding="utf-8")
        except OSError:
            page_text = ""
        page_meta, _page_body = parse_fm(page_text) if page_text else ({}, "")
        if is_card_note(page_meta) and card_crate:
            page_edges = lore_edge_crates(page_meta)
            if card_crate not in page_edges:
                page_edges.append(card_crate)
                try:
                    target.write_text(
                        apply_lore_edges_fm(page_text, page_edges), encoding="utf-8"
                    )
                except OSError:
                    pass
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
    spec = CATALOG.get(mouth_canon(mouth)) or CATALOG["librarian"]
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
    """One box â†’ pins. Two or three â†’ threads. Commas fan. Bare from+to is is."""
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
            str(read_md_meta(shell_path(target)).get("title") or "").strip()
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
    """Inverted Charlie lookup â€” Dewey by_tag / Charlie by_aven, by_relativity, by_insect.

    pin  â€” one-box tags
    from â€” left of a thread (aven)
    rel  â€” middle connector (relativity)
    to   â€” right of a thread (insect)
    bags â€” union, for the pin 'also' count
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


def _hash_slugs_from_note(meta: dict, body: str) -> list[str]:
    """YAML tags: / tag: plus #hashes in body, title, and line. Unique, ordered."""
    out: list[str] = []
    seen: set[str] = set()
    for k, v in (meta or {}).items():
        if k.lower() not in ("tags", "tag"):
            continue
        for t in split_tags(str(v)):
            s = tag_slug(t)
            if s and s not in seen:
                seen.add(s)
                out.append(s)
    for blob in (
        body or "",
        str((meta or {}).get("line") or ""),
        str((meta or {}).get("title") or ""),
    ):
        for m in TAG_RE.finditer(str(blob)):
            s = tag_slug(m.group(1))
            if s and s not in seen:
                seen.add(s)
                out.append(s)
    return out


def charlie_word_use_tally() -> dict[str, dict[str, int]]:
    """Per-word use counts across look-through metrics: pin, hash, out, in, rel.

    Hash unique-pockets match hashes_for_word. Word pages on go.tags are skipped
    for hashes so a minted hang-tag is not a use of itself.
    """
    rows: dict[str, dict[str, int]] = {}

    def bump(slug: str, key: str, n: int = 1) -> None:
        if not slug or n < 1:
            return
        row = rows.get(slug)
        if row is None:
            row = {"pin": 0, "hash": 0, "from": 0, "to": 0, "rel": 0, "n": 0}
            rows[slug] = row
        row[key] = row.get(key, 0) + n
        row["n"] = row.get("n", 0) + n

    catalog = charlie_weave_map()
    for role in ("pin", "from", "rel", "to"):
        for slug, hits in (catalog.get(role) or {}).items():
            bump(str(slug or ""), role, len(hits))

    hosts = [lobby_host()] + list(discover_hosts().values())
    seen: dict[str, set[str]] = {}
    for host in hosts:
        if host is None:
            continue
        if str(getattr(host, "name", "") or "").strip().lower() == TAGS_HOST_SLUG:
            continue
        with using_host(host):
            for p in iter_hash_notes():
                pocket = pocket_key(p)
                if not pocket:
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                meta, body = parse_fm(text)
                for slug in _hash_slugs_from_note(meta, body):
                    pockets = seen.setdefault(slug, set())
                    if pocket in pockets:
                        continue
                    pockets.add(pocket)
                    bump(slug, "hash")
    return rows


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
    if target.is_file() and target.suffix.lower() in {".md", ".canvas", ".chip"}:
        return target
    if target.is_dir():
        start = lobby_start(target)
        if start is not None:
            return start
        for name in (PAPER_NAME, INDEX_NAME, INDEX_LEGACY):
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
    .chip -> per-host sidecar keyed by chip.uid; courtesy crate: sticker only.
    """
    if not path.is_file():
        return ""
    suf = path.suffix.lower()
    if suf not in {".md", ".canvas", ".chip"}:
        return ""
    if not _in_active_vault(path):
        return ""
    if suf == ".chip":
        with LBR_LOCK:
            return _ensure_chip_crate(path)
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
    raw = note_text(text)
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
    href = tag_page_href(slug)
    return (
        f'<a{klass} href="{html.escape(href, True)}">'
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


def _pocket_shop(pocket: str) -> str:
    """Short host name for a pocket path — go.cast/Andy.md → cast."""
    p = (pocket or "").replace("\\", "/").strip("/")
    low = p.lower()
    if low.startswith("go."):
        p = p[3:]
    elif low.startswith("roam."):
        p = p[5:]
    host = p.split("/")[0].strip()
    if host.lower().endswith(".md"):
        host = host[:-3]
    return host



def _tagbay_fold_lis(items: list[str], fold_at: int = 8) -> str:
    """Join <li>â€¦</li> rows; tuck the overflow under a show-more."""
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


_TAGBAY_CHEST_TITLE = {
    "as from": "threads out",
    "as to": "threads in",
    "as connector": "as rel",
    "as pin": "as pin",
    "as hash": "as hash",
    "as code": "as code",
}


def _tagbay_chest(label: str, inner: str, n: int, focus: bool = False, layout: str = "") -> str:
    cls = "tagbay-chest" + (" is-focus" if focus else "")
    bay = (label or "").strip().lower()
    if bay in ("as from", "as to", "as connector"):
        cls += " is-thread-rail"
    extra = (layout or "").strip()
    if extra:
        cls += " " + extra
    shown = _TAGBAY_CHEST_TITLE.get(bay, label)
    return (
        f'<section class="{cls}" data-bay="{html.escape(label, True)}">'
        '<header class="tagbay-chest-head">'
        f"<h2>{html.escape(shown)}</h2>"
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


def _tagbay_body(slug: str, here: str = "", role: str = "", compact: bool = False) -> str:
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
    code_hits = [h for h in hashes if str(h.get("kind") or "") == "code"]
    hash_hits = [h for h in hashes if str(h.get("kind") or "") != "code"]
    if (
        not pins
        and not as_from
        and not as_rel
        and not as_to
        and not hash_hits
        and not code_hits
    ):
        return _tagbay_article(
            slug,
            '<p class="tagbay-void">Charlie has not woven this word yet.</p>',
            role,
        )
    # as-pin / as-hash = citation refs (keep together).
    # Charlie threads = position-dependent bins, separate sheet.
    cite_chests: list[tuple[str, str, int]] = []
    thread_chests: list[tuple[str, str, int]] = []
    for label, hits, stance in (
        ("as from", as_from, "from"),
        ("as connector", as_rel, "rel"),
        ("as to", as_to, "to"),
    ):
        if hits:
            thread_chests.append(
                (
                    label,
                    _charlie_chain_items(hits, here, stance=stance, compact=compact),
                    len(hits),
                )
            )
    if pins:
        cite_chests.append(
            (
                "as pin",
                _tagbay_page_hits(pins, off_if_empty=True, here=here, compact=compact),
                len(pins),
            )
        )
    if hash_hits:
        cite_chests.append(
            (
                "as hash",
                _tagbay_page_hits(hash_hits, here=here, compact=compact),
                len(hash_hits),
            )
        )
    want = {"tag": "as pin", "hash": "as hash"}.get(role, "")
    parts: list[str] = []
    if cite_chests:
        cite_html = "".join(
            _tagbay_chest(label, inner, n, focus=(want == label))
            for label, inner, n in cite_chests
        )
        parts.append(f'<div class="tagbay-cites">{cite_html}</div>')
    if code_hits:
        parts.append(
            '<div class="tagbay-codes">'
            + _tagbay_chest(
                "as code",
                _tagbay_page_hits(code_hits, here=here, compact=compact),
                len(code_hits),
            )
            + "</div>"
        )
    if thread_chests:
        thread_html = "".join(
            _tagbay_chest(label, inner, n, focus=False)
            for label, inner, n in thread_chests
        )
        parts.append(f'<div class="tagbay-threads">{thread_html}</div>')
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
    hits: list[dict], here: str = "", stance: str = "from", compact: bool = False
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

    def object_bits(by_page: dict) -> list[str]:
        bits: list[str] = []
        seen_w: set[str] = set()
        for page in sorted(by_page.values(), key=page_sort_key):
            if stance == "from":
                bag = page["tos"]
            elif stance == "to":
                bag = page["froms"]
            else:
                bag = []
                for frm, to in page["pairs"]:
                    if frm:
                        bag.append(frm)
                    if to:
                        bag.append(to)
            for w in bag:
                slug = tag_slug(str(w or ""))
                if slug and slug not in seen_w:
                    seen_w.add(slug)
                    bits.append(_charlie_word_link(slug))
        return bits

    items: list[str] = []
    for rel, by_page in sorted(bins.items(), key=lambda kv: kv[0].lower()):
        claim_bits = object_bits(by_page)
        if compact:
            page_links: list[str] = []
            seen_href: set[str] = set()
            for page in sorted(by_page.values(), key=page_sort_key):
                href = str(page.get("href") or "")
                title = str(page.get("title") or page.get("pocket") or "")
                if not title or href in seen_href:
                    continue
                seen_href.add(href)
                shop = _pocket_shop(str(page.get("pocket") or ""))
                tip = str(page.get("crate") or "") or shop
                page_links.append(
                    f'<a class="thread-page" href="{html.escape(href, True)}"'
                    f' title="{html.escape(tip, True)}">'
                    f"{html.escape(title)}</a>"
                )
            if stance == "to":
                who = ", ".join(claim_bits)
                claim_html = (
                    f'<span class="thread-verb">{_charlie_word_link(rel, "cork-rel")}</span>'
                    + (f' <span class="thread-objects">{who}</span>' if who else "")
                )
                stance_cls = "is-in"
            elif stance == "rel":
                pair_src: dict[tuple[str, str], list[str]] = {}
                pair_order: list[tuple[str, str, str, str]] = []
                seen_pair_href: dict[tuple[str, str], set[str]] = {}
                for page in sorted(by_page.values(), key=page_sort_key):
                    href = str(page.get("href") or "")
                    title = str(page.get("title") or page.get("pocket") or "")
                    if not title:
                        continue
                    shop = _pocket_shop(str(page.get("pocket") or ""))
                    tip = str(page.get("crate") or "") or shop
                    link = (
                        f'<a class="thread-page" href="{html.escape(href, True)}"'
                        f' title="{html.escape(tip, True)}">'
                        f"{html.escape(title)}</a>"
                    )
                    for frm, to in page["pairs"]:
                        a, b = tag_slug(frm), tag_slug(to)
                        if not a and not b:
                            continue
                        key = (a, b)
                        if key not in pair_src:
                            pair_src[key] = []
                            seen_pair_href[key] = set()
                            pair_order.append((a, b, frm, to))
                        if href in seen_pair_href[key]:
                            continue
                        seen_pair_href[key].add(href)
                        pair_src[key].append(link)
                for a, b, frm, to in pair_order:
                    left = _charlie_word_link(frm) if a else ""
                    right = _charlie_word_link(to) if b else ""
                    claim_html = (
                        f'<span class="thread-pair">{left}'
                        f'<span class="thread-pair-sep"> to </span>'
                        f"{right}</span>"
                    )
                    src_links = pair_src.get((a, b), [])
                    sources = ""
                    if src_links:
                        sources = (
                            '<p class="thread-sources">'
                            '<span class="thread-sources-lab">sources:</span>'
                            f'<span class="thread-pages">{"".join(src_links)}</span>'
                            "</p>"
                        )
                    items.append(
                        '<li class="tagbay-hit thread-rail-item thread-sentence is-rel">'
                        f'<p class="thread-claim">{claim_html}</p>'
                        f"{sources}"
                        "</li>"
                    )
                continue
            else:
                objs = ", ".join(claim_bits)
                claim_html = (
                    f'<span class="thread-verb">{_charlie_word_link(rel, "cork-rel")}</span>'
                    + (f' <span class="thread-objects">{objs}</span>' if objs else "")
                )
                stance_cls = "is-out"
            sources = ""
            if page_links:
                sources = (
                    '<p class="thread-sources">'
                    '<span class="thread-sources-lab">sources:</span>'
                    f'<span class="thread-pages">{"".join(page_links)}</span>'
                    "</p>"
                )
            if not claim_bits and not page_links:
                continue
            items.append(
                f'<li class="tagbay-hit thread-rail-item thread-sentence {stance_cls}">'
                f'<p class="thread-claim">{claim_html}</p>'
                f"{sources}"
                "</li>"
            )
            continue

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
            crate = str(page.get("crate") or "").strip()
            pocket = str(page.get("pocket") or "").strip()
            cite_meta = _tagbay_meta(pocket, crate, off=False)
            cite = (
                f'<p class="charlie-bin-cite{here_cls}">'
                f'{_tagbay_note(page["href"], page["title"])}'
                f"{cite_meta}"
                "</p>"
            )
            page_blocks.append(
                f'<div class="charlie-bin-page{here_cls}">'
                f'<ul class="charlie-bin-words">{chips}</ul>'
                f"{cite}"
                "</div>"
            )
        if not page_blocks:
            continue
        claim_line = ""
        if claim_bits:
            claim_line = (
                '<p class="thread-claim">'
                f'<span class="thread-verb">{_charlie_word_link(rel, "cork-rel")}</span>'
                ' <span class="thread-sep" aria-hidden="true">→</span> '
                f'<span class="thread-objects">{" ".join(claim_bits)}</span>'
                "</p>"
            )
        items.append(
            '<li class="tagbay-hit tagbay-relbin thread-rail-item">'
            '<div class="charlie-bin">'
            f'<h3 class="charlie-bin-rel">{_charlie_word_link(rel, "cork-rel")}</h3>'
            f"{claim_line}"
            f'<div class="charlie-bin-pages">{"".join(page_blocks)}</div>'
            "</div>"
            "</li>"
        )
    return _tagbay_fold_lis(items)


def _tagbay_page_hits(
    hits: list[dict], off_if_empty: bool = False, here: str = "", compact: bool = False
) -> str:
    items = []
    for b in hits:
        pocket = str(b.get("pocket") or "").lstrip("/")
        title = str(b.get("title") or pocket)
        crate = str(b.get("crate") or "").strip()
        href = str(b.get("href") or href_from_pocket(str(b.get("pocket") or "")))
        here_cls = " is-here" if here and _pocket_same(pocket, here) else ""
        if compact:
            shop = _pocket_shop(pocket)
            tip = crate or pocket
            where = (
                f'<span class="tagbay-where">{html.escape(shop)}</span>' if shop else ""
            )
            items.append(
                f'<li class="tagbay-hit tagbay-hit-compact{here_cls}">'
                f'<a class="tagbay-note" href="{html.escape(href, True)}"'
                f' title="{html.escape(tip, True)}">{html.escape(title)}</a>'
                f"{where}"
                "</li>"
            )
            continue
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
    if mouth == "tps":
        return tps_hits(kind="title", value=value) if value else tps_hits()
    mouth = mouth_canon(mouth)
    if mouth not in ("librarian", "detective"):
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
            if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
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


def lore_search_notes(q: str) -> list[dict]:
    """Keyword look across every filed lore card."""
    needle = (q or "").strip().lower()
    if not needle:
        return []
    out: list[dict] = []
    seen: set[str] = set()
    hide = {n.lower() for n in (INDEX_NAME, INDEX_LEGACY, PAPER_NAME)}
    for mouth, spec in CATALOG.items():
        inbox = spec.get("inbox")
        if inbox is None or not inbox.is_dir():
            continue
        tray = spec.get("tray") or mouth
        for p in inbox.glob("*.md"):
            if p.name.lower() in hide:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            meta, body = parse_fm(text)
            if not is_card_note(meta):
                continue
            title = str(meta.get("title") or p.stem).strip() or p.stem
            klass = str(meta.get("class") or "").strip()
            line = str(meta.get("line") or "").strip()
            maker = str(meta.get("maker") or "").strip()
            house = str(meta.get("house") or spec.get("house") or "").strip()
            frm = str(meta.get("from") or "").strip()
            blob = " ".join(
                [title, klass, line, maker, house, frm, body or ""]
            ).lower()
            if needle not in blob:
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
                    "house": house,
                    "maker": maker,
                    "file": p.name,
                    "href": lore_href(tray, p.name),
                    "pop": card_pop_href(crate) if crate else "",
                    "crate": crate,
                    "line": line,
                    "from": frm,
                    "mouth": mouth,
                }
            )
    out.sort(key=lambda b: str(b.get("title") or "").lower())
    return out[:60]


def lore_search_form() -> str:
    q = html.escape(_LORE_Q.get() or "", True)
    return (
        '<form class="tag-search lore-search" method="get" action="/">'
        + '<input type="hidden" name="h" value="trays">'
        + '<input type="search" name="lore" value="'
        + q
        + '" placeholder="search the deck" '
        + 'autocomplete="off" spellcheck="false">'
        + '<button type="submit">look</button>'
        + "</form>"
    )


def lore_look_block() -> str:
    q = (_LORE_Q.get() or "").strip()
    if not q:
        return ""
    hits = lore_search_notes(q)
    if not hits:
        return (
            '<div class="lorelook taglook-empty">'
            "nothing in the deck matches "
            + html.escape(q)
            + "</div>"
        )
    items: list[str] = []
    for hit in hits:
        bits = [
            '<a class="lorelook-title" href="'
            + html.escape(str(hit.get("href") or ""), True)
            + '">'
            + html.escape(str(hit.get("title") or "card"))
            + "</a>"
        ]
        klass = str(hit.get("class") or "").strip()
        house = str(hit.get("house") or "").strip()
        meta = " · ".join(x for x in (klass, house) if x)
        if meta:
            bits.append(
                '<span class="lorelook-meta">' + html.escape(meta) + "</span>"
            )
        line = str(hit.get("line") or "").strip()
        if line:
            bits.append(
                '<span class="lorelook-line">' + html.escape(line) + "</span>"
            )
        items.append("<li>" + "".join(bits) + "</li>")
    return (
        '<div class="lorelook">'
        '<div class="lorelook-mark">in the deck</div>'
        "<ul>"
        + "".join(items)
        + "</ul></div>"
    )


def catalog_field_hits(mouth: str, label: str, value: str) -> list[dict]:
    """Pages whose catalog YAML has this label, and this value if given."""
    if mouth == "tps":
        return tps_hits(kind=label, value=value)
    mouth = mouth_canon(mouth)
    if mouth not in ("librarian", "detective"):
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
    "detective": {
        "who": "detective index",
        "brick": "mypi:hunt",
        "mark": "mypi:hunt",
        "accent": "#c4202a",
        "skin": "is-detectivebay",
        "cls": "is-hunt",
        "empty": "Detective has not indexed this field yet.",
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
    """The paper's YAML â€” the hidden cabinet. Crate ids and tags stay doors."""
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
            f'<a class="tps-crumb-x" href="{html.escape(tps_href(drop), True)}" title="drop {html.escape(k, True)}">Ã—</a>'
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
            mark = " â†“" if order == "desc" else " â†‘"
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
        env = str(r.get("environment") or "").strip() or "â€”"
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
    shown = html.escape(" Â· ".join(shown_bits) if shown_bits else "all dates")
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
    shown = " Â· ".join(shown_bits) if shown_bits else "tps"
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
        for p in walk_host_notes(host.root):
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
        shown = slug
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
        frm = str(t.get("from") or "").strip() or "â€”"
        rel = str(t.get("rel") or "").strip() or "â€”"
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
    fields_detective: list = []
    stamps: list = []
    pins: list[str] = []
    threads: list = []
    hashes: list[str] = []
    others: list[Path] = []
    linked: list[Path] = []
    touches: list[str] = []
    born = ""

    lore_all: list[dict] = []
    for mouth in ("librarian", "detective", "charlie"):
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
                    det_dest = shelf_file("detective", target)
                    tps_dest = shelf_file("tps", target)
                    cha_dest = shelf_file("charlie", target)
                    crate_on = bag_crate(shelf_anchor("librarian", target)) or crate
                    if lib_dest is not None:
                        fields_lib = catalog_payload(
                            "librarian", lib_dest, pocket, crate_on
                        ).get("fields") or []
                    if det_dest is not None:
                        fields_detective = catalog_payload(
                            "detective", det_dest, pocket, crate_on
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
    add_chest("detective", _crate_field_items("detective", fields_detective), len(fields_detective))
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
        f'<p class="tagbay-sub">{html.escape(" Â· ".join(sub_bits))}</p>'
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
    """Title + crate id — link goes to the living page door, not the old /?k= report."""
    c = norm_crate(crate)
    if not c:
        return html.escape(str(crate or ""))
    door = door_for_crate(c)
    href = str((door or {}).get("href") or "").strip() or crate_href(c)
    label = html.escape(str((door or {}).get("title") or c))
    esc_href = html.escape(href, True)
    esc_c = html.escape(c)
    return (
        f'<a class="card-meta-crate-link" href="{esc_href}">{label}</a>'
        f' <a class="card-meta-crate-id" href="{esc_href}"><code>{esc_c}</code></a>'
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


_LORE_SHELF_FACE_CACHE: dict[str, tuple[float, str]] = {}


def paint_lorecard_shelf_item(p: Path) -> str:
    """One traveler-dressed .lorecard for the cards cabinet shelf.

    Cached by path+mtime so deck shelf and Attach picker share the same face
    without re-painting sixty cards on every open.
    """
    try:
        key = str(p.resolve())
        mtime = p.stat().st_mtime
    except OSError:
        return ""
    hit = _LORE_SHELF_FACE_CACHE.get(key)
    if hit and hit[0] == mtime and hit[1]:
        return hit[1]
    html = _paint_lorecard_shelf_item(p)
    if html:
        _LORE_SHELF_FACE_CACHE[key] = (mtime, html)
    return html


def _paint_lorecard_shelf_item(p: Path) -> str:
    """Paint one traveler .lorecard (uncached)."""
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


def page_lore_crates(target: Path) -> list[str]:
    """Crates whose lore belongs on the Cards shelf: this page, then the shell."""
    out: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        c = norm_crate(str(raw or ""))
        if c and c not in seen:
            out.append(c)
            seen.add(c)

    add(bag_crate(target))
    folder = nearest_index_folder(target)
    if folder is not None:
        add(bag_crate(folder))
    return out


def cards_shelf_get(pocket_raw: str) -> tuple[int, dict | None, str]:
    """Shelf of lore cards on this page and its shell, from every cabinet."""
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        target = resolve_vault_page(pocket_raw)
        if target is None:
            return 400, None, "not a vault page"
        pocket = pocket_key(target)
        crate = bag_crate(target)
        crates = page_lore_crates(target)
        route = pocket_key(nearest_index_folder(target) or target)
        seen: set[str] = set()
        cards: list[dict] = []
        bits: list[str] = []
        for mouth in ("librarian", "detective", "charlie", "tps"):
            for want in crates:
                for card in lore_cards_for(mouth, want):
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



def cards_lore_list(*, faces: bool = False) -> tuple[int, dict | None, str]:
    """All lore cards across every catalog mouth — for the deck Attach picker.

    Metadata is always returned. When faces=True, each card also gets the same
    traveler paint as the Cards shelf (lorecard.css), cached by path+mtime.
    """
    seen: set[str] = set()
    cards: list[dict] = []
    for mouth in ("librarian", "detective", "charlie", "tps"):
        code, obj, err = catalog_lore_list(mouth)
        if code != 200 or not obj:
            continue
        house = str((obj or {}).get("house") or mouth).strip()
        spec = CATALOG.get(mouth) or {}
        inbox = spec.get("inbox")
        for card in obj.get("cards") or []:
            if not isinstance(card, dict):
                continue
            own = str(card.get("crate") or "").strip()
            key = own or f"{mouth}:{card.get('file')}"
            if not own or key in seen:
                continue
            seen.add(key)
            item = dict(card)
            item["mouth"] = mouth
            item["house"] = str(card.get("house") or house).strip() or house
            if faces:
                path = find_lore_file(mouth, own)
                if path is None and inbox is not None:
                    fname = str(card.get("file") or "").strip()
                    if fname:
                        cand = inbox / fname
                        if cand.is_file():
                            path = cand
                item["html"] = (
                    paint_lorecard_shelf_item(path) if path is not None else ""
                )
            cards.append(item)
    cards.sort(key=lambda c: (str(c.get("house") or "").lower(), str(c.get("title") or "").lower()))
    return 200, {"cards": cards, "house": "CARDS", "faces": bool(faces)}, ""


def cards_lore_attach(
    pocket_raw: str, card_crate: str, mouth: str = "", onto: str = ""
) -> tuple[int, dict | None, str]:
    """Attach a lore card (from any mouth) onto the open page; return the deck shelf."""
    mouth = mouth_canon(mouth)
    card_crate = norm_crate(card_crate)
    if not card_crate:
        return 400, None, "need a lore crate"
    if mouth not in CATALOG:
        # Resolve mouth from the crate if the client omitted it.
        for cand in ("librarian", "detective", "charlie", "tps"):
            if find_lore_file(cand, card_crate) is not None:
                mouth = cand
                break
    if mouth not in CATALOG:
        return 404, None, "no such lore"
    code, obj, err = catalog_lore_attach(mouth, pocket_raw, card_crate, onto)
    if code != 200 or obj is None:
        return code, None, err
    shelf_code, shelf, shelf_err = cards_shelf_get(pocket_raw)
    if shelf is None:
        return shelf_code, None, shelf_err
    shelf["attached"] = bool(obj.get("attached", True))
    shelf["file"] = str(obj.get("file") or "")
    shelf["mouth"] = mouth
    return 200, shelf, ""




def _resolve_lore_mouth(mouth: str, card_crate: str) -> str:
    mouth = mouth_canon(mouth)
    card_crate = norm_crate(card_crate)
    if mouth in CATALOG and card_crate and find_lore_file(mouth, card_crate) is not None:
        return mouth
    for cand in ("librarian", "detective", "charlie", "tps"):
        if card_crate and find_lore_file(cand, card_crate) is not None:
            return cand
    if mouth in CATALOG:
        return mouth
    return ""


def catalog_lore_detach(
    mouth: str, pocket_raw: str, card_crate: str, onto: str = ""
) -> tuple[int, dict | None, str]:
    """Remove a lore card edge from the open page (mirror of attach)."""
    mouth = _resolve_lore_mouth(mouth, card_crate)
    card_crate = norm_crate(card_crate)
    if not card_crate:
        return 400, None, "need a lore crate"
    if mouth not in CATALOG:
        return 404, None, "no such lore"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _catalog_lore_detach(mouth, pocket_raw, card_crate, onto)


def _catalog_lore_detach(
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
        # edges: field and born-on are separate; page {{cards}} uses both via lore_edge_crates
        edge_list = lore_edges_field(meta)
        born = norm_crate(str(meta.get("source_crate") or ""))
        had_edge = crate in edge_list
        had_born = born == crate
        had = had_edge or had_born
        if had:
            if had_edge:
                edge_list = [e for e in edge_list if e != crate]
                text = apply_lore_edges_fm(text, edge_list)
            if had_born:
                text = apply_lore_source_crate_fm(text, "")
            path.write_text(text, encoding="utf-8")
        try:
            page_text = target.read_text(encoding="utf-8")
        except OSError:
            page_text = ""
        page_meta, _page_body = parse_fm(page_text) if page_text else ({}, "")
        if is_card_note(page_meta) and card_crate:
            page_edges = lore_edge_crates(page_meta)
            if card_crate in page_edges:
                page_edges = [e for e in page_edges if e != card_crate]
                try:
                    target.write_text(
                        apply_lore_edges_fm(page_text, page_edges), encoding="utf-8"
                    )
                except OSError:
                    pass
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
    obj["detached"] = bool(had)
    return 200, obj, ""



def cards_lore_faces(items: list | None = None) -> tuple[int, dict | None, str]:
    """Paint traveler faces for a small set of crates (Attach picker lazy load)."""
    faces_map: dict[str, str] = {}
    cards_out: list[dict] = []
    for raw in items or []:
        if not isinstance(raw, dict):
            continue
        mouth = str(raw.get("mouth") or raw.get("house") or "").strip().lower()
        crate = norm_crate(str(raw.get("crate") or raw.get("card") or ""))
        if not crate:
            continue
        mouth = _resolve_lore_mouth(mouth, crate)
        if mouth not in CATALOG:
            continue
        path = find_lore_file(mouth, crate)
        if path is None:
            continue
        html = paint_lorecard_shelf_item(path)
        if not html:
            continue
        faces_map[crate] = html
        cards_out.append({"crate": crate, "mouth": mouth, "html": html})
    return 200, {"faces": faces_map, "cards": cards_out}, ""


def cards_lore_sync(
    pocket_raw: str,
    attach_list: list | None = None,
    detach_list: list | None = None,
    onto: str = "",
) -> tuple[int, dict | None, str]:
    """Attach and/or detach several lore cards, then return the deck shelf."""
    attached = 0
    detached = 0
    for raw in attach_list or []:
        if not isinstance(raw, dict):
            continue
        mouth = str(raw.get("mouth") or raw.get("house") or "")
        crate = str(raw.get("crate") or raw.get("card") or "")
        code, obj, err = catalog_lore_attach(mouth, pocket_raw, crate, onto)
        if code != 200 or obj is None:
            return code, None, err or "attach failed"
        if obj.get("attached"):
            attached += 1
    for raw in detach_list or []:
        if not isinstance(raw, dict):
            continue
        mouth = str(raw.get("mouth") or raw.get("house") or "")
        crate = str(raw.get("crate") or raw.get("card") or "")
        code, obj, err = catalog_lore_detach(mouth, pocket_raw, crate, onto)
        if code != 200 or obj is None:
            return code, None, err or "detach failed"
        if obj.get("detached"):
            detached += 1
    shelf_code, shelf, shelf_err = cards_shelf_get(pocket_raw)
    if shelf is None:
        return shelf_code, None, shelf_err
    shelf["attached_n"] = attached
    shelf["detached_n"] = detached
    return 200, shelf, ""


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
            mark = "as " + lab if not prefix else prefix + " Â· " + lab
            chests.append(_tagbay_chest(mark, "".join(items), len(bags)))

    add_field_chests(mouth, "")
    other = (
        "detective"
        if mouth == "librarian"
        else "librarian"
        if mouth == "detective"
        else ""
    )
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
    shown = (label + ((" Â· " + value) if value else "")).strip(" Â·") or value or mouth
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
    kind = mouth_canon(kind)
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


def normalize_media_name(name: str) -> str:
    """Strip wiki wrappers and legacy Obsidian vault prefixes from image paths."""
    raw = (name or "").strip().replace("\\", "/").strip("/")
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].strip().replace("\\", "/").strip("/")
    # Carl's AB migration left old Meta-System roots in banner paths.
    for prefix in ("XX. Meta-System/", "Meta-System/"):
        if raw.lower().startswith(prefix.lower()):
            raw = raw[len(prefix) :].lstrip("/")
            break
    return raw

def find_media_by_suffix(rel: str) -> Path | None:
    """Match Repo/Images/... under a nested Obsidian vault (e.g. AB/KDE-555/)."""
    rel = (rel or "").replace("\\", "/").strip("/")
    if not rel or ".." in Path(rel).parts:
        return None
    root = active_vault()
    if not root.is_dir() or is_lobby():
        return None
    needle = rel.lower()
    hits: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:
            continue
        try:
            parts = p.relative_to(root).parts
            pr = p.relative_to(root).as_posix()
        except ValueError:
            continue
        if any(part in SKIP for part in parts):
            continue
        pl = pr.lower()
        if pl == needle or pl.endswith("/" + needle):
            hits.append(p)
    if not hits:
        return None
    hits.sort(key=lambda x: x.as_posix().lower())
    return hits[0]

def find_media(name: str) -> Path | None:
    raw = normalize_media_name(name)
    if not raw or "://" in raw:
        return None
    found = find_mats_img(raw)
    if found is not None:
        return found
    if "/" in raw:
        target = safe_rel(raw)
        if target is not None and target.is_file() and target.suffix.lower() in IMAGE_EXT:
            return target
        nested = find_media_by_suffix(raw)
        if nested is not None:
            return nested
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
    img = (
        f'<img class="pic" src="{html.escape(src, True)}" '
        f'alt="{html.escape(label, True)}">'
    )
    # Click-through like jacket-zoom: in-pocket lightbox (www/librarian JS).
    return (
        f'<a class="pic-zoom" href="{html.escape(src, True)}" '
        f'title="open image">'
        f'{img}</a>'
    )


def cover_name(meta: dict | None) -> str:
    meta = meta or {}
    raw = str(
        meta.get("cover") or meta.get("jacket") or meta.get("banner") or ""
    ).strip()
    # Obsidian sometimes stores [[file|alt]] in front matter.
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].strip()
    return raw

def icon_name(meta: dict | None) -> str:
    """Host face / favicon filename. Not the jacket (cover:)."""
    meta = meta or {}
    raw = str(
        meta.get("icon")
        or meta.get("favicon")
        or meta.get("avatar")
        or meta.get("faveicon")
        or ""
    ).strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].strip()
    return raw


def face_letter(label: str) -> str:
    for ch in str(label or ""):
        if ch.isalnum():
            return ch.upper()
    return "*"


def door_face_html(label: str, meta: dict | None, yaml_icon: str = "") -> str:
    """Small avatar on a {{doors}} card. Picture if icon/cover resolves; else a letter tile."""
    name = icon_name(meta) or (yaml_icon or "").strip() or cover_name(meta)
    found = media_src(name) if name else None
    if found:
        src, _fname = found
        return (
            f'<img class="door-face" src="{html.escape(src, True)}" alt="" '
            f'aria-hidden="true">'
        )
    letter = face_letter(label)
    hue = ""
    color = str((meta or {}).get("color") or "").strip()
    if color.startswith("#") and len(color) in (4, 7):
        hue = color
    if not hue:
        n = sum(ord(c) for c in (label or "x"))
        hues = ("#1a1a2e", "#4a1c1c", "#1c3a1c", "#1c2a4a", "#3a2a12", "#3a1a3a")
        hue = hues[n % len(hues)]
    return (
        f'<span class="door-face is-letter" aria-hidden="true" '
        f'style="background:{html.escape(hue, True)}">{html.escape(letter)}</span>'
    )


def door_hue(meta: dict | None, label: str = "") -> str:
    """Lobby niche tint: YAML color/strip, else the room coat, else the letter hash."""
    got = css_hex(card_strip_color(meta, hop=False))
    if got:
        return got
    n = sum(ord(c) for c in (label or "x"))
    hues = ("#1a1a2e", "#4a1c1c", "#1c3a1c", "#1c2a4a", "#3a2a12", "#3a1a3a")
    return hues[n % len(hues)]


def letter_favicon_href(letter: str, fill: str = "#111111") -> str:
    ch = html.escape(face_letter(letter))
    fill = html.escape(fill if fill.startswith("#") else "#111111")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
        f'<rect width="16" height="16" fill="{fill}"/>'
        f'<text x="8" y="12.2" text-anchor="middle" font-size="11" '
        f'font-family="sans-serif" font-weight="700" fill="#fff">{ch}</text>'
        "</svg>"
    )
    return "data:image/svg+xml," + quote(svg)


def page_icon_link(here: Path | None) -> str:
    """<link rel=icon> for this host (start.md on the lobby)."""
    meta: dict = {}
    label = ""
    yaml_icon = ""
    try:
        if is_lobby():
            start = HOSTS_ROOT / START_NAME
            if start.is_file():
                meta = read_md_meta(start) or {}
                label = str(meta.get("title") or "start")
        else:
            root = active_vault()
            loaded = load_index(root)
            if loaded:
                meta = loaded[0] or {}
                label = str(meta.get("title") or root.name)
            else:
                label = active_host() or "go"
            slug = host_slug(active_host() or "")
            if slug:
                yaml_icon = host_icon_map().get(slug, "")
    except Exception:
        return ""
    name = icon_name(meta) or yaml_icon
    found = media_src(name) if name else None
    if found:
        href = found[0]
        return f'<link rel="icon" href="{html.escape(href, True)}">\n'
    return f'<link rel="icon" href="{letter_favicon_href(label)}">\n'


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
    """Cover on the page. Art if cover: resolves; else cloth + title.

    cover_fit: landscape | portrait. Name plaque sits under the art.
    Art links to the image for a bigger look (hover CSS zooms too).
    """
    meta = meta or {}
    title = str(meta.get("title") or "").strip()
    name_file = cover_name(meta)
    art = cover_art(meta, title)
    if not title and not art and not name_file:
        return ""
    hue = hue_name(meta)
    classes = ["jacket"]
    if art:
        classes.append("has-cover")
    if hue:
        classes.append(f"hue-{hue}")
    fit = str(meta.get("cover_fit") or meta.get("jacket_fit") or "").strip().lower()
    if fit in ("landscape", "wide", "horizontal"):
        classes.append("cover-landscape")
    label = html.escape(title or "untitled")
    if art:
        found = media_src(name_file) if name_file else None
        href = found[0] if found else ""
        if href:
            art = (
                f'<a class="jacket-zoom" href="{html.escape(href, True)}" '
                f'title="open cover">'
                f"{art}</a>"
            )
    return (
        f'<figure class="{" ".join(classes)}">'
        f"{art}"
        f'<figcaption class="name">{label}</figcaption>'
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



def chip_values_html(vals: list[str], mouth: str, label: str) -> str:
    """Join multi-value chip links with a visible separator (not smashed)."""
    parts: list[str] = []
    for i, value in enumerate(vals):
        if i:
            parts.append('<span class="chip-sep">, </span>')
        parts.append(
            '<a class="chip-value" href="'
            + html.escape(value_door_href(mouth, label, value), True)
            + '">'
            + html.escape(value)
            + "</a>"
        )
    return "".join(parts)



def slot_page(folder: Path, rel: str | None) -> Path:
    if rel:
        hit = safe_rel(rel)
        if hit is not None and hit.exists():
            return hit
    return folder


def tps_page_stamps(folder: Path, rel: str | None) -> list[dict]:
    """Decorated TPS stamps for this page's report shelf."""
    target = slot_page(folder, rel)
    dest = shelf_file("tps", target)
    if dest is None:
        return []
    pocket = pocket_key(target)
    obj = tps_read(dest, pocket)
    return tps_decorate_stamps(obj.get("stamps") or [])


def tps_meta_chips(folder: Path, rel: str | None) -> str:
    """Print this page's TPS stamps as chips (title → when), like Lib/Agent meta."""
    stamps = tps_page_stamps(folder, rel)
    if not stamps:
        return ""
    grouped: dict[str, list[tuple[str, str]]] = {}
    order: list[str] = []
    for s in stamps:
        title = str(s.get("title") or "").strip()
        when = str(s.get("when") or "").strip()
        if not title or not when:
            continue
        if title not in grouped:
            grouped[title] = []
            order.append(title)
        href = str(s.get("when_href") or s.get("title_href") or "").strip()
        pair = (when, href)
        if pair not in grouped[title]:
            grouped[title].append(pair)
    chips: list[str] = []
    for title in order:
        vals = grouped.get(title) or []
        if not vals:
            continue
        label_href = tps_href("title", title)
        bits: list[str] = []
        for when, href in vals:
            if href:
                bits.append(
                    '<a class="chip-value" href="'
                    + html.escape(href, True)
                    + '">'
                    + html.escape(when)
                    + "</a>"
                )
            else:
                bits.append(
                    '<span class="chip-value">' + html.escape(when) + "</span>"
                )
        values_html = "".join(
            (('<span class="chip-sep">, </span>' if i else "") + bit)
            for i, bit in enumerate(bits)
        )
        multi = " chip-group" if len(vals) > 1 else ""
        chips.append(
            f'<span class="chip{multi}">'
            '<a class="chip-label" href="'
            + html.escape(label_href, True)
            + '">'
            + html.escape(title)
            + '</a><span class="chip-values">'
            + values_html
            + "</span></span>"
        )
    if not chips:
        return ""
    return '<span class="chips chips-tps">' + "".join(chips) + "</span>"


def meta_chips(folder: Path, rel: str | None, mouth: str | None = None) -> str:
    """Print this page's catalog as clickable chips. Group identical field labels."""
    mouth = mouth_canon(mouth or "librarian")
    if mouth == "tps":
        return tps_meta_chips(folder, rel)
    if mouth not in ("librarian", "detective"):
        mouth = "librarian"
    target = slot_page(folder, rel)
    dest = shelf_file(mouth, target)
    if dest is None:
        return ""
    house = CATALOG[mouth]["house"]
    obj = catalog_read(dest, pocket_key(target), house)
    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for f in obj.get("fields") or []:
        if not isinstance(f, dict):
            continue
        label = str(f.get("label") or "").strip()
        if not label:
            continue
        if label not in grouped:
            grouped[label] = []
            order.append(label)
        for value in chip_values(f):
            v = str(value or "").strip()
            if v and v not in grouped[label]:
                grouped[label].append(v)
    chips: list[str] = []
    for label in order:
        vals = grouped.get(label) or []
        if not vals:
            continue
        bit = one_meta_chip_html(mouth, label, vals)
        if bit:
            chips.append(bit)
    if not chips:
        return ""
    return wrap_meta_chips(mouth, chips)


def one_meta_chip_html(mouth: str, label: str, vals: list[str]) -> str:
    """One label→value chip atom (shared by {{meta}} drops and {{chip:…}})."""
    label = (label or "").strip()
    vals = [str(v or "").strip() for v in (vals or []) if str(v or "").strip()]
    if not label or not vals:
        return ""
    mouth = mouth_canon(mouth or "librarian")
    if mouth == "tps":
        label_href = tps_href("title", label)
        values_html = "".join(
            (
                ('<span class="chip-sep">, </span>' if i else "")
                + (
                    '<a class="chip-value" href="'
                    + html.escape(tps_href("when", when), True)
                    + '">'
                    + html.escape(when)
                    + "</a>"
                    if when
                    else ""
                )
            )
            for i, when in enumerate(vals)
        )
    else:
        label_href = catalog_field_href(mouth, label)
        values_html = chip_values_html(vals, mouth, label)
    if not values_html:
        return ""
    multi = " chip-group" if len(vals) > 1 else ""
    return (
        f'<span class="chip{multi}">'
        '<a class="chip-label" href="'
        + html.escape(label_href, True)
        + '">'
        + html.escape(label)
        + '</a><span class="chip-values">'
        + values_html
        + "</span></span>"
    )


def wrap_meta_chips(mouth: str, chips: list[str], *, lone: bool = False) -> str:
    if not chips:
        return ""
    mouth = mouth_canon(mouth or "librarian")
    klass = "chips chips-" + html.escape(mouth, True)
    if lone:
        klass += " chips-lone"
    if mouth == "all" or mouth == "cabinets":
        klass = "chips chips-all"
        if lone:
            klass += " chips-lone"
    return '<span class="' + klass + '">' + "".join(chips) + "</span>"


def meta_slot_html(folder: Path, rel: str | None, who: str | None) -> str:
    """Resolve {{meta}} / {{meta:mouth}}. Bare meta/chips = every cabinet."""
    raw = (who or "").strip().lower()
    if not raw or raw in ("all", "cabinets", "every"):
        return meta_chips_all(folder, rel)
    if raw in ("lib", "librarian", "library"):
        return meta_chips(folder, rel, "librarian")
    if raw in ("det", "detective", "agent", "agt"):
        return meta_chips(folder, rel, "detective")
    if raw == "tps":
        return meta_chips(folder, rel, "tps")
    return meta_chips(folder, rel, raw)


def meta_chips_all(folder: Path, rel: str | None) -> str:
    """Every cabinet's chips in one quiet strip (lib, detective, tps)."""
    chips: list[str] = []
    for mouth in ("librarian", "detective", "tps"):
        block = meta_chips(folder, rel, mouth)
        if not block:
            continue
        # unwrap outer <span class="chips …">…</span> so all share one strip
        inner = block
        if inner.startswith("<span ") and inner.endswith("</span>"):
            gt = inner.find(">")
            if gt > 0:
                inner = inner[gt + 1 : -len("</span>")]
        if inner:
            chips.append(inner)
    if not chips:
        return ""
    return wrap_meta_chips("all", chips)


def catalog_chip_token(folder: Path, rel: str | None, mouth: str, label: str) -> str:
    """{{chip:lib:label}} — one tiny labeled chip. Missing → blank."""
    mouth = mouth_canon(mouth or "librarian")
    vals = catalog_field_values(folder, rel, mouth, label)
    bit = one_meta_chip_html(mouth, label, vals)
    if not bit:
        return ""
    return wrap_meta_chips(mouth, [bit], lone=True)


def pocket_bar(rel: str, is_dir: bool = False) -> str:
    host = active_host()
    p = (rel or "").replace("\\", "/").strip("/")
    if p.lower().endswith(".md"):
        p = p[:-3]
    if not host:
        stem = p.lower()
        if not stem or stem in ("start", "go"):
            return "go"
        if stem == "recent":
            return "recent"
        if stem == "roam":
            return "roam"
        bar = "go/" + p
        if is_dir:
            bar += "/"
        return bar
    if not p:
        return format_pocket(host)
    bar = format_pocket(host, p).rstrip("/")
    if is_dir:
        bar += "/"
    return bar


def parse_fm(text: str) -> tuple[dict, str]:
    raw = note_text(text)
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


def load_marks_map(text: str) -> dict[str, dict[str, str]]:
    """Optional ~hosts/_marks.yaml. Builtins still stamp with no file."""
    out: dict[str, dict[str, str]] = {}
    current = ""
    for line in (text or "").replace("\r\n", "\n").split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  ") and ":" in line and current:
            k, v = line.strip().split(":", 1)
            k = k.strip().lower()
            v = v.strip().strip('"').strip("'")
            if k in ("alias", "aliases"):
                k = "also"
            if k in ("label", "ink", "also") and v != "":
                out.setdefault(current, {})[k] = v
            continue
        if line[0] not in " \t" and ":" in line:
            k, v = line.split(":", 1)
            current = k.strip().lower()
            if not current:
                continue
            out.setdefault(current, {})
            rest = v.strip().strip('"').strip("'")
            if rest:
                out[current]["label"] = rest
    return out


def marks_registry() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """id -> {label, ink}, plus alias -> id. Builtins plus ~hosts/_marks.yaml."""
    defs: dict[str, dict[str, str]] = {k: dict(v) for k, v in MARK_BUILTINS.items()}
    aliases = dict(MARK_ALIASES)
    extra: dict[str, dict[str, str]] = {}
    if MARKS_FILE.is_file():
        try:
            extra = load_marks_map(MARKS_FILE.read_text(encoding="utf-8"))
        except OSError:
            extra = {}
    for name, meta in extra.items():
        slug = (name or "").strip().lower()
        if not slug:
            continue
        ink = str(meta.get("ink") or "").strip().lower()
        if ink not in MARK_INK:
            ink = defs.get(slug, {}).get("ink") or "dim"
        label = str(meta.get("label") or "").strip() or slug.upper()
        defs[slug] = {"label": label, "ink": ink}
        also = str(meta.get("also") or "").replace(",", " ")
        for word in also.split():
            w = word.strip().lower().strip(".")
            if w:
                aliases[w] = slug
    for slug in defs:
        aliases.setdefault(slug, slug)
    return defs, aliases


def parse_mark_words(meta: dict | None) -> list[str]:
    if not meta:
        return []
    raw = ""
    for key, val in meta.items():
        if str(key).strip().lower() in ("mark", "marks"):
            raw = str(val or "")
            break
    words: list[str] = []
    seen: set[str] = set()
    for part in raw.replace(";", ",").split(","):
        w = part.strip().lower()
        if not w or w in seen:
            continue
        seen.add(w)
        words.append(w)
    return words


def resolve_mark(
    word: str,
    defs: dict[str, dict[str, str]],
    aliases: dict[str, str],
) -> dict[str, str] | None:
    w = (word or "").strip().lower()
    if not w:
        return None
    canon = mouth_canon(w)
    slug = aliases.get(w) or aliases.get(canon) or (w if w in defs else "")
    if not slug or slug not in defs:
        return None
    spec = defs[slug]
    return {"id": slug, "label": spec["label"], "ink": spec["ink"]}


def _stamp_rot(word: str) -> int:
    h = 0
    for ch in word:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return int(h % 13) - 8


def page_marks_html(meta: dict | None) -> str:
    words = parse_mark_words(meta)
    if not words:
        return ""
    defs, aliases = marks_registry()
    stamps: list[dict[str, str]] = []
    seen: set[str] = set()
    for w in words:
        hit = resolve_mark(w, defs, aliases)
        if hit is None or hit["id"] in seen:
            continue
        seen.add(hit["id"])
        stamps.append(hit)
    if not stamps:
        return ""
    bits = ['<div class="go-marks" aria-hidden="true">']
    for i, st in enumerate(stamps):
        rot = _stamp_rot(st["id"] + str(i))
        bits.append(
            f'<span class="go-stamp ink-{html.escape(st["ink"], True)}" '
            f'style="--stamp-rot:{rot}deg">{html.escape(st["label"])}</span>'
        )
    bits.append("</div>")
    return "".join(bits)


def rewrite_tool_slots(body: str) -> str:
    """{{tool:codelook}} -> {{codelook}} so YAML {{word}} can stay local."""
    return TOOL_SLOT_RE.sub(lambda m: "{{" + m.group(1) + "}}", body or "")


def read_md_meta(p: Path) -> dict:
    if not p.is_file() or p.suffix.lower() != ".md":
        return {}
    try:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    return parse_fm(text)[0]


def md_list_label(p: Path) -> str:
    """List label: frontmatter title if present, else the filename without .md."""
    if p.suffix.lower() == ".chip":
        name = str(chip_peek(p).get("name") or "").strip()
        return name or p.stem
    if is_text_guest_path(p) or is_html_guest_path(p):
        return p.name
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


def coat_link_href(env: str | None) -> str:
    """Live coat sheet with mtime cache-bust so Keep restyles without a gray reload."""
    stem = env_name(env)
    if not stem:
        return ""
    ver = "0"
    try:
        path = STYLES / f"{stem}.css"
        if path.is_file():
            ver = str(int(path.stat().st_mtime))
    except OSError:
        pass
    return f"/styles/{html.escape(stem, True)}.css?v={ver}"


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



def iter_md_tables(body: str):
    """Yield (table_index, start_line, end_line_exclusive, lines) for pipe tables."""
    lines = (body or "").replace("\r\n", "\n").split("\n")
    fence = False
    i = 0
    n = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            fence = not fence
            i += 1
            continue
        if fence:
            i += 1
            continue
        if line.lstrip().startswith("|"):
            start = i
            chunk: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                chunk.append(lines[i])
                i += 1
            yield n, start, i, chunk
            n += 1
            continue
        i += 1


def serialize_md_table(rows: list[list[str]], aligns: list[str] | None = None) -> str:
    """Plain pipe Markdown from a cell grid."""
    if not rows:
        return ""
    width = max((len(r) for r in rows), default=0)
    if not width:
        return ""
    aligns = list(aligns or [])
    while len(aligns) < width:
        aligns.append("left")
    aligns = aligns[:width]

    def cell(s: str) -> str:
        return (s or "").replace("\n", " ").replace("|", "\\|").strip()

    def pad(row: list[str]) -> list[str]:
        row = list(row)
        if len(row) < width:
            row = row + [""] * (width - len(row))
        return row[:width]

    out: list[str] = []
    head = pad(rows[0])
    out.append("| " + " | ".join(cell(c) for c in head) + " |")
    sep = []
    for al in aligns:
        if al == "center":
            sep.append(":---:")
        elif al == "right":
            sep.append("---:")
        else:
            sep.append("---")
    out.append("| " + " | ".join(sep) + " |")
    for row in rows[1:]:
        out.append("| " + " | ".join(cell(c) for c in pad(row)) + " |")
    return "\n".join(out)


def replace_nth_md_table(body: str, index: int, table_md: str) -> tuple[str, bool]:
    lines = (body or "").replace("\r\n", "\n").split("\n")
    for n, start, end, _chunk in iter_md_tables(body):
        if n != index:
            continue
        fresh = (table_md or "").replace("\r\n", "\n").strip("\n").split("\n")
        if not fresh or not any(ln.lstrip().startswith("|") for ln in fresh):
            return body, False
        # keep only pipe lines
        fresh = [ln for ln in fresh if ln.lstrip().startswith("|")]
        new_lines = lines[:start] + fresh + lines[end:]
        return "\n".join(new_lines), True
    return body, False


def table_put(pocket_raw: str, index, table_md: str) -> tuple[int, dict | None, str]:
    try:
        n = int(index)
    except (TypeError, ValueError):
        return 400, None, "no such table"
    if n < 0:
        return 400, None, "no such table"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        return _table_put(pocket_raw, n, table_md)


def _table_put(pocket_raw: str, index: int, table_md: str) -> tuple[int, dict | None, str]:
    target = resolve_vault_page(pocket_raw)
    if target is None:
        return 400, None, "not a vault page"
    dest = page_note_file(target)
    if dest is None or not dest.is_file() or dest.suffix.lower() != ".md":
        return 400, None, "not a note"
    with LBR_LOCK:
        try:
            text = dest.read_text(encoding="utf-8-sig")
        except OSError:
            return 500, None, "could not read note"
        raw = note_text(text)
        head, body = "", raw
        if raw.startswith("---\n"):
            end = raw.find("\n---\n", 4)
            if end >= 0:
                head = raw[: end + 5]
                body = raw[end + 5 :]
        new_body, ok = replace_nth_md_table(body, index, table_md)
        if not ok:
            return 404, None, "no such table"
        out = head + new_body
        if not out.endswith("\n"):
            out += "\n"
        try:
            dest.write_text(out, encoding="utf-8")
        except OSError:
            return 500, None, "could not write note"
    return 200, {"ok": True, "i": index}, ""


def md_table_html(lines: list[str], inline, index: int | None = None) -> str:
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
            cls = f' class="is-{al}"' if al else ""
            bits.append(
                f"<{tag}{cls} data-md=\""
                + html.escape(text, True)
                + f"\">"
                + inline(text)
                + f"</{tag}>"
            )
        return "".join(bits)

    wrap_attr = ""
    if index is not None:
        wrap_attr = f' data-table-i="{index}" data-live="1"'
    parts = [f'<div class="md-table-wrap"{wrap_attr}><table class="md-table">']
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
            text = dest.read_text(encoding="utf-8-sig")
        except OSError:
            return 500, None, "could not read note"
        raw = note_text(text)
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
    # Final enters at EOF are editor noise — they mint trailing md-gap and
    # leave empty space under shell / paper designs. Leading blanks already skip.
    while lines and not str(lines[-1]).strip():
        lines.pop()
    out: list[str] = []
    buf: list[str] = []
    open_divs = 0
    open_spans = 0

    fence: list[str] | None = None
    fence_kind: str = ""
    table: list[str] | None = None
    table_i = 0
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
        # soft break: line ending in two spaces -> <br> (classic markdown)
        parts: list[str] = []
        for i, line in enumerate(buf):
            if i < len(buf) - 1 and line.endswith("  "):
                parts.append(line.rstrip() + "\x00BR\x00")
            else:
                parts.append(line)
        joined = "\n".join(parts)
        para, cls, eid = take_dress(joined)
        html_para = inline(para).replace("\x00BR\x00", "<br>\n")
        out.append(f"<p{html_attrs(cls, eid)}>" + html_para + "</p>")
        buf.clear()

    def flush_fence() -> None:
        nonlocal fence, fence_kind
        if fence is None:
            return
        body = html.escape("\n".join(fence))
        # bare ``` = code; ```ascii = art plate; ```card = mono slip (class mono-card — not .lorecard)
        kind = (fence_kind or "code").strip().lower()
        if kind in ("ascii", "art"):
            cls = "ascii"
        elif kind in ("card", "bizcard", "slip"):
            cls = "mono-card"
        else:
            cls = "code"
            if kind and kind not in ("code", "txt", "text", ""):
                # unknown language still code, keep tag as extra class if safe
                safe = re.sub(r"[^a-z0-9_-]+", "", kind)[:24]
                if safe and safe != "code":
                    cls = f"code lang-{safe}"
        out.append(f"<pre class='{cls}'><code>{body}</code></pre>")
        fence = None
        fence_kind = ""

    def flush_table() -> None:
        nonlocal table, table_i
        if table is None:
            return
        out.append(md_table_html(table, inline, table_i))
        table_i += 1
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
        s = ROM_TOKEN_RE.sub(
            lambda m: hold(rom_launch_html(m.group(1), m.group(2) or "")),
            s,
        )
        s = LINK_CRATE_RE.sub(
            lambda m: hold(print_link_token(m.group(1), m.group(2), m.group(3) or "")),  # POCKET_LINK_GO_HOST
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
        s = CHIP_CODE_RE.sub(lambda m: hold(chip_code_chip(m.group(1))), s)
        s = SPAN_RE.sub(
            lambda m: hold(f"<span{html_attrs(*parse_spec(m.group(1) or ''))}>")
            + m.group(2)
            + hold("</span>"),
            s,
        )
        s = DIV_INLINE_RE.sub(
            lambda m: hold(f"<div{html_attrs(*parse_spec(m.group(1)))}>")
            + m.group(2)
            + hold("</div>"),
            s,
        )
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(
            r"(?<![A-Za-z0-9*_])_([^_\n]+?)_(?![A-Za-z0-9*_])",
            r"<em>\1</em>",
            s,
        )
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
            # language tag on opening fence: ```ascii / ```card / ```python
            tag = line.strip()[3:].strip()
            fence_kind = tag.split()[0] if tag else ""
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
        if (
            FACE_CRATE_RE.fullmatch(raw)
            or LINK_CRATE_RE.fullmatch(raw)
            or DOORS_SLOT_RE.fullmatch(raw)
            or META_SLOT_RE.fullmatch(raw)
            or RECENT_SLOT_RE.fullmatch(raw)
            or TREE_SLOT_RE.fullmatch(raw)
            or raw
            in (
                "{{images}}",
                "{{slides}}",
                "{{files}}",
                "{{spines}}",
                "{{dir}}",
                "{{list}}",
                "{{dirtree}}",
                "{{tree}}",
                "{{faces}}",
                "{{cards}}",
                "{{shelf}}",
                "{{cover}}",
                "{{jacket}}",
                "{{edges}}",
                "{{headers}}",
            )
        ):
            end_list()
            flush()
            while out and "md-gap" in out[-1]:
                out.pop()
            out.append(raw)
            continue
        span_open = SPAN_LINE.match(raw)
        if span_open:
            end_list()
            flush()
            spec = span_open.group(1) or ""
            rest = span_open.group(2) or ""
            attrs = html_attrs(*parse_spec(spec))
            close_m = SPAN_CLOSE_INLINE.search(rest)
            if close_m:
                inner = rest[: close_m.start()]
                after = rest[close_m.end() :]
                out.append(f"<span{attrs}>" + inline(inner) + "</span>")
                if after.strip():
                    buf.append(after)
            elif rest.strip():
                out.append(f"<span{attrs}>" + inline(rest) + "</span>")
            else:
                out.append(f"<span{attrs}>")
                open_spans += 1
            continue
        if SPAN_CLOSE.match(raw):
            end_list()
            flush()
            if open_spans:
                out.append("</span>")
                open_spans -= 1
            continue
        opened = DIV_OPEN.match(raw)
        if opened:
            end_list()
            flush()
            spec = opened.group(1)
            rest = opened.group(2) or ""
            close_m = DIV_CLOSE_INLINE.search(rest)
            if close_m:
                inner = rest[: close_m.start()]
                after = rest[close_m.end() :]
                out.append(
                    f"<div{html_attrs(*parse_spec(spec))}>"
                    + inline(inner)
                    + "</div>"
                )
                if after.strip():
                    buf.append(after)
            else:
                out.append(f"<div{html_attrs(*parse_spec(spec))}>")
                open_divs += 1
                if rest.strip():
                    out.append(inline(rest))
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
            n = min(max(len(hm.group(1)), 1), 6)
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
            # Micro-doc letter spacing only at top level, between real content.
            # Inside {{div}} shells, blanks are readable structure only — an
            # md-gap there becomes a grid/flex child and collapses bay yards.
            # Leading blanks (before anything is emitted) also become a visible
            # top gap on Tags/Glen; skip those so coats can kiss the chrome.
            if open_divs == 0 and out:
                prev = out[-1]
                if prev.startswith("<p") and "md-gap" not in prev:
                    out.append('<p class="md-gap" aria-hidden="true"></p>')
        else:
            end_list()
            buf.append(line)
    flush()
    flush_fence()
    flush_table()
    end_quote()
    end_list()
    while open_spans:
        out.append("</span>")
        open_spans -= 1
    while open_divs:
        out.append("</div>")
        open_divs -= 1
    gap = '<p class="md-gap" aria-hidden="true"></p>'
    while out and out[-1] == gap:
        out.pop()
    return "\n".join(out)


def walk_host_notes(root: Path, *, chips: bool = True):
    """Yield .md (and guest .chip) under a host, skipping stash folders."""
    if not root.is_dir():
        return
    pats = ("*.md", "*.chip") if chips else ("*.md",)
    for pat in pats:
        for p in root.rglob(pat):
            try:
                rel_parts = p.relative_to(root).parts
            except ValueError:
                continue
            if any(part in SKIP or stash_name(part) for part in rel_parts):
                continue
            yield p


def iter_notes() -> list[Path]:
    root = active_vault()
    if not root.is_dir():
        return []
    out: list[Path] = []
    hide = {INDEX_NAME, INDEX_LEGACY, PAPER_NAME, START_NAME, RECENT_NAME, ROAM_NAME, "readme.md"}
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
    for p in walk_host_notes(root):
        if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
            continue
        out.append(p)
    return out


def iter_hash_notes() -> list[Path]:
    """Notes whose #hashes count, including hall papers (index.md).

    go.codes trunks/branches are papers, not named files. iter_notes hides those.
    """
    root = active_vault()
    if not root.is_dir():
        return []
    hide = {INDEX_NAME, INDEX_LEGACY, START_NAME, RECENT_NAME, ROAM_NAME, "readme.md"}
    out: list[Path] = []
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
    for p in walk_host_notes(root):
        if p.name.lower() in hide:
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
    """#slug in the paper; bare slug on the face (hash is the wire, not the label)."""
    slug = name.strip().lstrip("#")
    return (
        f'<a class="tag" href="{html.escape(tag_href(slug), True)}" '
        f'data-tag="{html.escape(slug, True)}" title="#{html.escape(slug, True)}">'
        f"{html.escape(slug)}</a>"
    )


def crate_cite_chip(raw: str) -> str:
    """^crate chip → living page door when known; else fall back to /?k= lookup."""
    c = norm_crate(raw)
    if not c:
        return html.escape("^" + str(raw or ""))
    door = door_for_crate(c)
    href = str((door or {}).get("href") or "").strip() or crate_href(c)
    return (
        f'<a class="cite" href="{html.escape(href, True)}" title="{html.escape(c, True)}">'
        f"^{html.escape(c)}</a>"
    )


def chip_code_is_trunk_wild(seg: str) -> bool:
    """Trunk slot not yet sealed: * or T* (optional three-slot form)."""
    s = (seg or "").strip().upper()
    return s in ("*", "T*")


def chip_code_is_trunk_seg(seg: str) -> bool:
    return bool(re.fullmatch(r"T\d+", seg or "", re.I)) or chip_code_is_trunk_wild(seg)


def chip_code_is_branch_seg(seg: str) -> bool:
    return bool(re.fullmatch(r"B\d+", seg or "", re.I))


def chip_code_parse(raw: str) -> dict | None:
    """One chain address: group-number, then trunk / branch / leaf.

    OT-008.T01.B002.L03 -> group OT, log 008, trunk T01, branch B002, leaf L03.
    OT-008.B002 -> bag + branch only (trunk omitted; preferred pre-timber cite).
    OT-008.*.B002 or OT-008.T*.B002 -> same idea with an explicit wild trunk slot.
    Groups are OT, NT, ONT, or any letter prefix. Dots are depth, not extra cites.
    """
    s = (raw or "").strip().lstrip("^").strip()
    if not s or not CHIP_CODE_BODY_RE.fullmatch(s):
        return None
    bits = [p.upper() for p in s.split(".") if p]
    head = bits[0]
    if "-" not in head:
        return None
    group, number = head.split("-", 1)
    if not group or not number:
        return None
    segs = bits[1:]
    trunk_wild = bool(segs) and chip_code_is_trunk_wild(segs[0])
    trunk_omit = bool(segs) and chip_code_is_branch_seg(segs[0])
    trunk_open = trunk_wild or trunk_omit
    code = head if not segs else head + "." + ".".join(segs)
    return {
        "group": group,
        "number": number,
        "segs": segs,
        "code": code,
        "display": [head] + segs,
        "bins": [group, number] + segs,
        "trunk_wild": trunk_wild,
        "trunk_omit": trunk_omit,
        "trunk_open": trunk_open,
    }


def chip_code_wild_rest(segs: list[str]) -> list[str]:
    """Segs under the bag after skipping a trunk slot (* / T* / T01).

    Bare BAG.B### has no trunk slot — the segs themselves are the rest.
    """
    if not segs:
        return []
    if chip_code_is_trunk_wild(segs[0]) or re.fullmatch(r"T\d+", segs[0] or "", re.I):
        return list(segs[1:])
    return list(segs)


def chip_codes_wild_match(a: str, b: str) -> bool:
    """Bag+rest match when either cite leaves the trunk open (* / T* / omit)."""
    pa, pb = chip_code_parse(a), chip_code_parse(b)
    if pa is None or pb is None:
        return False
    if pa["group"] != pb["group"] or pa["number"] != pb["number"]:
        return False
    if not (pa.get("trunk_open") or pb.get("trunk_open")):
        return False
    ra, rb = chip_code_wild_rest(pa["segs"]), chip_code_wild_rest(pb["segs"])
    if ra == rb:
        return True
    if not ra or not rb:
        return ra == rb
    sa, sb = ".".join(ra), ".".join(rb)
    return sa == sb or sa.startswith(sb + ".") or sb.startswith(sa + ".")


def chip_code_fill_wild(raw: str) -> str:
    """If trunk is open, pick the lowest real T## under the bag that holds the rest."""
    parsed = chip_code_parse(raw)
    if parsed is None or not parsed.get("trunk_open"):
        return chip_code_norm(raw)
    root = codes_host_root()
    if root is None:
        return parsed["code"]
    bag = root / parsed["group"] / parsed["number"]
    rest = chip_code_wild_rest(parsed["segs"])
    if not rest:
        return parsed["group"] + "-" + parsed["number"]
    if not bag.is_dir():
        return parsed["code"]
    hits: list[str] = []
    try:
        kids = sorted(bag.iterdir(), key=lambda p: p.name.upper())
    except OSError:
        return parsed["code"]
    for child in kids:
        if not child.is_dir() or not re.fullmatch(r"T\d+", child.name, re.I):
            continue
        cur = child
        ok = True
        for j, seg in enumerate(rest):
            last = j == len(rest) - 1
            try:
                if last and chip_code_is_line(seg):
                    if not (cur / (seg + ".md")).is_file():
                        ok = False
                        break
                else:
                    nxt = cur / seg
                    if not nxt.is_dir():
                        ok = False
                        break
                    cur = nxt
            except OSError:
                ok = False
                break
        if ok:
            hits.append(child.name.upper())
    if not hits:
        return parsed["code"]
    filled = parsed["group"] + "-" + parsed["number"] + "." + hits[0]
    if rest:
        filled += "." + ".".join(rest)
    return chip_code_norm(filled) or filled

def chip_code_norm(raw: str) -> str:
    parsed = chip_code_parse(raw)
    return parsed["code"] if parsed else ""


def chip_code_group(raw: str) -> str:
    s = (raw or "").strip().lstrip("^").strip().upper()
    if re.fullmatch(r"[A-Z]{1,12}", s):
        return s
    parsed = chip_code_parse(raw)
    return parsed["group"] if parsed else ""


def chip_code_parts(code: str) -> list[str]:
    parsed = chip_code_parse(code)
    return list(parsed["display"]) if parsed else []


def chip_code_chain(code: str) -> list[str]:
    parts = chip_code_parts(code)
    acc: list[str] = []
    out: list[str] = []
    for part in parts:
        acc.append(part)
        out.append(".".join(acc))
    return out


def chip_code_is_line(seg: str) -> bool:
    return bool(re.fullmatch(r"L\d+", seg or "", re.I))


def chip_code_at_bins(bins: list[str]) -> str:
    if not bins:
        return ""
    if len(bins) == 1:
        return bins[0]
    head = bins[0] + "-" + bins[1]
    if len(bins) == 2:
        return head
    return head + "." + ".".join(bins[2:])


def chip_code_rel(code: str) -> tuple[str, bool]:
    """Path under go.codes: GROUP/NUMBER/T../B../Lxx.md. Leaf is a file; else a hall.

    Open trunk (* / T* / bare BAG.B###): resolve to a real trunk when bag+rest
    exist; else the bag hall. Never returns a literal * or T* folder, and never
    parks a branch directly under the bag.
    """
    parsed = chip_code_parse(code)
    if parsed is None:
        group = chip_code_group(code)
        if group:
            return group, True
        return "", False
    if parsed.get("trunk_open"):
        filled = chip_code_fill_wild(parsed["code"])
        filled_p = chip_code_parse(filled)
        if filled_p is not None and not filled_p.get("trunk_open"):
            parsed = filled_p
        else:
            return parsed["group"] + "/" + parsed["number"], True
    bins = parsed["bins"]
    last = bins[-1]
    if parsed["segs"] and chip_code_is_line(last):
        return "/".join(bins[:-1] + [last + ".md"]), False
    return "/".join(bins), True

def chip_code_from_rel(rel: str) -> str:
    here = (rel or "").replace("\\", "/").strip("/")
    if here.lower().endswith(".md"):
        here = here[:-3]
    parts = [
        p
        for p in here.split("/")
        if p and p.lower() not in {"index", "_shell", "_index"}
    ]
    if not parts:
        return ""
    if len(parts) == 1 and re.fullmatch(r"[A-Za-z]{1,12}", parts[0]):
        return parts[0].upper()
    if re.fullmatch(r"[A-Za-z]{1,12}-\d{1,8}", parts[0], re.I):
        return chip_code_norm(".".join(parts))
    if (
        len(parts) >= 2
        and re.fullmatch(r"[A-Za-z]{1,12}", parts[0])
        and re.fullmatch(r"\d{1,8}", parts[1])
    ):
        return chip_code_norm(parts[0] + "-" + parts[1] + (
            ("." + ".".join(parts[2:])) if len(parts) > 2 else ""
        ))
    return ""


def codes_host_root() -> Path | None:
    host = codes_host()
    return host.root if host is not None else None


def codes_host_slug() -> str:
    host = codes_host()
    return host.name if host is not None else "codes"


def event_host() -> Host | None:
    found = discover_hosts()
    host = found.get(EVENT_HOST_SLUG)
    if host is not None:
        return host
    for host in found.values():
        if (host.kind or "go") == "roam":
            continue
        env = str(host.environment or "").strip().lower()
        if env == "event":
            return host
    return None


def event_host_slug() -> str:
    host = event_host()
    return host.name if host is not None else EVENT_HOST_SLUG


def people_host() -> Host | None:
    found = discover_hosts()
    host = found.get(PEOPLE_HOST_SLUG)
    if host is not None:
        return host
    for host in found.values():
        env = str(host.environment or "").strip().lower()
        if env == "people":
            return host
    return None


def people_host_slug() -> str:
    host = people_host()
    return host.name if host is not None else PEOPLE_HOST_SLUG


def people_root() -> Path | None:
    host = people_host()
    return host.root if host is not None else None


def on_people_pad(rel: str = "") -> bool:
    host = people_host()
    return host is not None and active_host() == host.name


def chip_code_href(code: str) -> str:
    rel, _is_dir = chip_code_rel(code)
    slug = codes_host_slug()
    if not rel:
        return "/?h=" + quote(slug)
    return "/?h=" + quote(slug) + "&p=" + quote(rel, safe="/")


def note_chip_code(meta: dict | None, rel: str = "", path: Path | None = None) -> str:
    """Full ZIP on a codes paper: YAML code:, else path OT/001/T01/B006."""
    meta = meta or {}
    code = chip_code_norm(str(meta.get("code") or ""))
    if code:
        return code
    if path is not None:
        try:
            rel = path.relative_to(active_vault()).as_posix()
        except ValueError:
            pass
    return chip_code_from_rel(rel or "")


def chip_code_chip(raw: str) -> str:
    """One cite, one link to that exact node. Dots are the address, not extra doors."""
    if is_event_cite(raw):
        return event_code_chip(raw)
    if is_people_cite(raw):
        return people_code_chip(raw)
    parsed = chip_code_parse(raw)
    if parsed is None:
        return html.escape("^" + str(raw or ""))
    code = parsed["code"]
    ensure_code_chain(code)
    href = chip_code_href(code)
    return (
        '<a class="chipcode" href="'
        + html.escape(href, True)
        + '" title="'
        + html.escape("^" + code, True)
        + '">^'
        + html.escape(code)
        + "</a>"
    )


def event_code_chip(raw: str) -> str:
    """^EV-001 is the event file on go.code.event, not a compost ZIP."""
    code = event_code_norm(raw)
    if not code:
        return html.escape("^" + str(raw or ""))
    dest = ensure_event_note(code)
    href = era_note_href(code + ".md") if dest is not None else era_note_href(code + ".md")
    return (
        '<a class="eventcode" href="'
        + html.escape(href, True)
        + '" title="'
        + html.escape("^" + code, True)
        + '">^'
        + html.escape(code)
        + "</a>"
    )


def ensure_event_note(code: str) -> Path | None:
    """Mint a flat EV-00n.md on go.code.event. Never a compost EV/ folder."""
    use = event_code_norm(code)
    if not use:
        return None
    root = events_root()
    if root is None:
        root = HOSTS_ROOT / EVENT_HOST_SLUG
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
    dest = root / (use + ".md")
    if dest.is_file():
        return dest
    ensure_events_index()
    own = mint_crate_id()
    era_write_note(dest, own=own, title=use, sit="", body="", code=use)
    return dest


def people_code_norm(raw: str) -> str:
    s = (raw or "").strip().upper().replace(" ", "").replace("_", "-")
    s = s.lstrip("^")
    if s.endswith(".MD"):
        s = s[:-3]
    s = s.split(".", 1)[0]
    if not s or not PEOPLE_CODE_RE.fullmatch(s):
        return ""
    group = s.split("-", 1)[0]
    if group in PEOPLE_SKIP_GROUPS:
        return ""
    return s


def is_people_cite(raw: str) -> bool:
    return bool(people_code_norm(raw))


def people_note_href(rel: str) -> str:
    slug = people_host_slug()
    path = (rel or "").replace("\\", "/").strip("/")
    if not path:
        return "/?h=" + quote(slug)
    return "/?h=" + quote(slug) + "&p=" + quote(path, safe="/")


def _meta_str_list(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        out = []
        for x in raw:
            s = str(x or "").strip()
            if s:
                out.append(s)
        return out
    s = str(raw or "").strip()
    if not s:
        return []
    s = s.strip("[]")
    return [p.strip().strip("'").strip('"') for p in s.split(",") if p.strip()]


def iter_people_notes() -> list[Path]:
    """KVEN slips live flat under go.code.people. Filename is the people code."""
    root = people_root()
    if root is None or not root.is_dir():
        return []
    hide = {n.lower() for n in RESERVED_NOTES}
    out: list[Path] = []
    try:
        kids = list(root.iterdir())
    except OSError:
        return []
    for p in kids:
        if not p.is_file() or p.suffix.lower() != ".md":
            continue
        if p.name.lower() in hide:
            continue
        if stash_name(p.name):
            continue
        meta = read_md_meta(p)
        kind = str(meta.get("kind") or "").strip().lower()
        code = people_code_norm(str(meta.get("kven") or meta.get("code") or p.stem))
        if not code and kind not in ("kven", "person", "people"):
            continue
        if not code:
            continue
        out.append(p)
    out.sort(key=lambda p: p.name.lower())
    return out


def people_record(path: Path) -> dict | None:
    root = people_root()
    if root is None:
        return None
    try:
        rel = path.relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = parse_fm(text)
    title = str(meta.get("title") or "").strip() or path.stem
    code = people_code_norm(str(meta.get("kven") or meta.get("code") or path.stem))
    own = norm_crate(str(meta.get("crate") or ""))
    return {
        "title": title,
        "code": code,
        "href": people_note_href(rel),
        "rel": rel,
        "crate": own,
        "type": str(meta.get("type") or "").strip(),
        "aliases": _meta_str_list(meta.get("aliases")),
        "matches": _meta_str_list(meta.get("matches")),
        "edges": [people_code_norm(x) for x in _meta_str_list(meta.get("edges")) if people_code_norm(x)],
        "note": str(meta.get("note") or "").strip(),
        "body": hunt_thought_body(body or ""),
    }


def people_search_notes(q: str) -> list[dict]:
    needle = (q or "").strip().lower()
    recs = []
    for p in iter_people_notes():
        rec = people_record(p)
        if not rec:
            continue
        if needle:
            blob = " ".join(
                [
                    str(rec.get("title") or ""),
                    str(rec.get("code") or ""),
                    str(rec.get("type") or ""),
                    str(rec.get("note") or ""),
                    str(rec.get("body") or ""),
                    " ".join(rec.get("aliases") or []),
                    " ".join(rec.get("matches") or []),
                ]
            ).lower()
            if needle not in blob:
                continue
        recs.append(rec)
    recs.sort(key=lambda r: str(r.get("title") or "").lower())
    return recs


def people_search_form() -> str:
    q = html.escape(_PEOPLE_Q.get() or "", True)
    slug = html.escape(people_host_slug(), True)
    return (
        '<form class="tag-search people-search" method="get" action="/">'
        + '<input type="hidden" name="h" value="'
        + slug
        + '">'
        + '<input type="search" name="people" value="'
        + q
        + '" placeholder="a person, a kven" '
        + 'autocomplete="off" spellcheck="false">'
        + '<button type="submit">look</button>'
        + "</form>"
    )


def people_card_html(rec: dict) -> str:
    href = html.escape(str(rec.get("href") or "#"), True)
    title = html.escape(str(rec.get("title") or "person"))
    code = str(rec.get("code") or "").strip()
    kind = str(rec.get("type") or "").strip()
    aka = rec.get("aliases") or []
    parts = [
        '<article class="people-card">',
        '<a class="people-card-title" href="',
        href,
        '">',
        title,
        "</a>",
    ]
    if code:
        parts.append('<p class="people-code">' + html.escape(code) + "</p>")
    if kind:
        parts.append('<p class="people-type">' + html.escape(kind) + "</p>")
    if aka:
        parts.append(
            '<p class="people-aka">' + html.escape(", ".join(aka[:6])) + "</p>"
        )
    parts.append("</article>")
    return "".join(parts)


def people_look_block(rel: str = "", meta: dict | None = None) -> str:
    if not on_people_pad(rel):
        return ""
    q = (_PEOPLE_Q.get() or "").strip()
    meta = meta or {}
    here = (rel or "").replace("\\", "/").strip("/")
    here_path: Path | None = None
    root = people_root()
    leaf = here.split("/")[-1] if here else ""
    if root is not None and leaf and leaf.lower() not in {n.lower() for n in RESERVED_NOTES}:
        cand = root / leaf
        if cand.is_file() and people_code_norm(cand.stem):
            here_path = cand
    if q:
        recs = people_search_notes(q)
        mark = "on the roll"
        if not recs:
            return (
                '<div class="peoplelook taglook-empty">'
                "nobody on this roll matches "
                + html.escape(q)
                + "</div>"
            )
        items = ["<li>" + people_card_html(rec) + "</li>" for rec in recs]
        return (
            '<div class="peoplelook people-roster">'
            '<div class="peoplelook-mark">'
            + html.escape(mark)
            + "</div>"
            "<ul>"
            + "".join(items)
            + "</ul></div>"
        )
    if here_path is not None:
        rec = people_record(here_path) or {}
        code = str(rec.get("code") or "")
        mine = str(rec.get("href") or "")
        cites = [
            h
            for h in (notes_with_chip(code) if code else [])
            if str(h.get("href") or "") != mine
        ]
        edges = rec.get("edges") or []
        bits = ['<div class="peoplelook">']
        if edges:
            bits.append('<div class="peoplelook-mark">linked kven</div><ul class="people-cites">')
            for edge in edges:
                dest = people_root()
                href = people_note_href(edge + ".md") if dest is not None else "#"
                bits.append(
                    '<li><a class="peoplecode" href="'
                    + html.escape(href, True)
                    + '">^'
                    + html.escape(edge)
                    + "</a></li>"
                )
            bits.append("</ul>")
        if cites:
            bits.append('<div class="peoplelook-mark">cited on</div><ul class="people-cites">')
            for hit in cites[:40]:
                href = html.escape(str(hit.get("href") or "#"), True)
                title = html.escape(str(hit.get("title") or hit.get("pocket") or "page"))
                bits.append('<li><a href="' + href + '">' + title + "</a></li>")
            bits.append("</ul>")
        if len(bits) == 1:
            return (
                '<div class="peoplelook taglook-empty">'
                "not cited yet"
                "</div>"
            )
        bits.append("</div>")
        return "".join(bits)
    recs = people_search_notes("")
    if not recs:
        return (
            '<div class="peoplelook taglook-empty">'
            "no people on the roll yet. cite a kven to mint a slip."
            "</div>"
        )
    items = ["<li>" + people_card_html(rec) + "</li>" for rec in recs]
    return (
        '<div class="peoplelook people-roster">'
        '<div class="peoplelook-mark">on the roll</div>'
        "<ul>"
        + "".join(items)
        + "</ul></div>"
    )


def people_write_note(dest: Path, *, own: str, title: str, code: str) -> None:
    lines = [
        "---",
        "crate: " + own,
        "title: " + yaml_scalar(title),
        "kven: " + code,
        "kind: kven",
        "type: person",
        "environment: people",
        "---",
        "",
        "# {{title}}",
        "",
    ]
    dest.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def people_code_chip(raw: str) -> str:
    """^MIS-777 is the person slip on go.code.people, not a compost ZIP."""
    code = people_code_norm(raw)
    if not code:
        return html.escape("^" + str(raw or ""))
    dest = ensure_people_note(code)
    href = people_note_href(code + ".md")
    return (
        '<a class="peoplecode" href="'
        + html.escape(href, True)
        + '" title="'
        + html.escape("^" + code, True)
        + '">^'
        + html.escape(code)
        + "</a>"
    )


def ensure_people_note(code: str) -> Path | None:
    """Mint a flat LLL-DDD.md on go.code.people. Never a compost MIS/ folder."""
    use = people_code_norm(code)
    if not use:
        return None
    root = people_root()
    if root is None:
        root = HOSTS_ROOT / PEOPLE_HOST_SLUG
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
    dest = root / (use + ".md")
    if dest.is_file():
        return dest
    own = mint_crate_id()
    people_write_note(dest, own=own, title=use, code=use)
    return dest


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

    Stem `index` / `_index` / `_shell` stays off — that would hit every hall.
    """
    if not needle or needle in {"index", "_index", "_shell"}:
        return []
    root = active_vault()
    if not root.is_dir() or is_lobby():
        return []
    hits: list[Path] = []
    seen: set[str] = set()

    def consider(hall: Path) -> None:
        names = {wiki_target(hall.name)}
        dest: Path | None = None
        for fname in (PAPER_NAME, INDEX_NAME, INDEX_LEGACY):
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
    if p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
        return str(read_md_meta(p).get("title") or "").strip() or p.parent.name
    return p.stem


def wiki_hit_rel(p: Path) -> str:
    if p.is_file() and p.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
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
    for p in iter_hash_notes():
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
                meta = read_md_meta(p)
                rel = p.relative_to(active_vault()).as_posix()
                code = note_chip_code(meta, rel, p)
                kind = str(meta.get("kind") or "").strip().lower()
                on_codes = is_codes_host(host)
                if code and (on_codes or kind in ("code", "chip", "chipcode")):
                    title = code
                    href = chip_code_href(code)
                else:
                    title = pocket_title(pocket) or p.stem
                    href = (
                        href_from_pocket(pocket)
                        if host.name
                        else page_href(rel)
                    )
                hits.append(
                    {
                        "pocket": pocket,
                        "title": title,
                        "href": href,
                        "crate": file_crate(p),
                        "kind": (
                            "code"
                            if code and (on_codes or kind in ("code", "chip", "chipcode"))
                            else "hash"
                        ),
                    }
                )
    return hits


def tags_host_root() -> Path | None:
    host = get_host(TAGS_HOST_SLUG)
    return host.root if host is not None else None


def ensure_tag_page(slug: str) -> Path | None:
    """On-touch mint: one markdown page per word under go.code.tags. Word node = crate."""
    word = tag_slug(slug)
    if not word:
        return None
    root = tags_host_root()
    if root is None or not root.is_dir():
        return None
    if "/" in word or "\\" in word:
        word = word.replace("/", "-").replace("\\", "-")
    dest = root / (word + ".md")
    if dest.is_file():
        return dest
    reserved = {n.lower() for n in RESERVED_NOTES}
    if dest.name.lower() in reserved:
        return None
    crate = mint_crate_id()
    nl = "\n"
    body = (
        "---" + nl
        + "crate: " + crate + nl
        + "title: " + yaml_scalar(word) + nl
        + "kind: tag" + nl
        + "tag: " + word + nl
        + "environment: tags" + nl
        + "---" + nl + nl
        + "# {{title}}" + nl + nl
        + "_insights on this word live here. Cabinets wear on this crate._" + nl
    )
    with LBR_LOCK:
        if dest.exists():
            return dest
        try:
            dest.write_text(body, encoding="utf-8")
        except OSError:
            return None
    return dest


def tag_page_href(slug: str) -> str:
    word = tag_slug(slug)
    if not word:
        return "/?h=" + TAGS_HOST_SLUG
    ensure_tag_page(word)
    return "/?h=" + TAGS_HOST_SLUG + "&p=" + quote(word + ".md", safe="/")


def tag_search_form() -> str:
    return (
        "<form class=\"tag-search\" method=\"get\" action=\"/\">"
        + "<input type=\"hidden\" name=\"h\" value=\"" + TAGS_HOST_SLUG + "\">"
        + "<input type=\"search\" name=\"touch\" placeholder=\"find or open a word\" "
        + "autocomplete=\"off\" spellcheck=\"false\">"
        + "<button type=\"submit\">open</button>"
        + "</form>"
    )


CODE_PAPER_BLURB = (
    "_group / trunk / branch / leaf. Cites of this node, and anything deeper, look through below._"
)
HASH_ONLY_LINE_RE = re.compile(
    r"^(?:\s*#[A-Za-z0-9][\w/-]*\s*)+$"
)


def _codes_tps_created(path: Path, code: str, *, minted: bool = False) -> None:
    """Slide compost message time into TPS created. New pages fall back to now."""
    at = _compost_when_unix(code)
    if at is None:
        if not minted:
            return
        at = int(time.time())
    host = codes_host()
    if host is None:
        return
    with using_host(host):
        tps_stamp_quiet(path, "created", at)


def _mint_code_node(path: Path, code: str, title: str) -> None:
    minted = False
    if not path.exists():
        crate = mint_crate_id()
        body = (
            "---\n"
            "crate: " + crate + "\n"
            "title: " + yaml_scalar(title) + "\n"
            "kind: code\n"
            "code: " + code + "\n"
            "environment: codes\n"
            "---\n\n"
            "# {{code}}\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        write_note(path, body)
        minted = True
    _codes_tps_created(path, code, minted=minted)


def ensure_code_chain(raw: str) -> Path | None:
    """Mint go.codes as GROUP / NUMBER / trunk / branch, leaf as a .md.

    Open trunk (* / T* / bare BAG.B###): mint only the bag hall; if a real trunk
    already holds the rest, mint/fill that concrete chain instead. Never create
    a * / T* folder, and never mint B### directly under the bag.
    """
    if is_event_cite(raw):
        return ensure_event_note(raw)
    if is_people_cite(raw):
        return ensure_people_note(raw)
    parsed = chip_code_parse(raw)
    if parsed is None:
        return None
    if parsed.get("trunk_open"):
        filled = chip_code_fill_wild(parsed["code"])
        filled_p = chip_code_parse(filled)
        if filled_p is not None and not filled_p.get("trunk_open"):
            return ensure_code_chain(filled)
        bag_code = parsed["group"] + "-" + parsed["number"]
        return ensure_code_chain(bag_code)
    root = codes_host_root()
    if root is None or not root.is_dir():
        return None
    bins = parsed["bins"]
    with LBR_LOCK:
        cur = root
        dest: Path | None = None
        for i, seg in enumerate(bins):
            if chip_code_is_trunk_wild(seg):
                break
            node = chip_code_at_bins(bins[: i + 1])
            last = i == len(bins) - 1
            as_file = last and chip_code_is_line(seg) and len(parsed["segs"]) > 0
            if i == 0:
                title = parsed["group"]
            elif i == 1:
                title = parsed["group"] + "-" + parsed["number"]
            else:
                title = seg
            if as_file:
                dest = cur / (seg + ".md")
                reserved = {n.lower() for n in RESERVED_NOTES}
                if dest.name.lower() in reserved:
                    return None
                _mint_code_node(dest, node, title)
            else:
                cur = cur / seg
                dest = cur / PAPER_NAME
                _mint_code_node(dest, node, title)
        return dest

def chip_codes_from_blob(blob: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        code = chip_code_norm(raw)
        if code and code not in seen:
            seen.add(code)
            found.append(code)

    for m in CHIP_CODE_RE.finditer(blob or ""):
        add(m.group(1))
    for piece in CHIP_SPLIT.split(blob or ""):
        add(piece)
    return found


def chip_codes_in_catalog(path: Path | None) -> list[str]:
    """Librarian / Detective field values count as cites, not only the page body."""
    found: list[str] = []
    seen: set[str] = set()
    if path is None:
        return found
    try:
        if not path.exists():
            return found
    except OSError:
        return found
    for mouth in ("librarian", "detective"):
        dest = shelf_file(mouth, path)
        if dest is None or not dest.is_file():
            continue
        house = str((CATALOG.get(mouth) or {}).get("house") or "LIBRARIAN")
        obj = catalog_read(dest, pocket_key(path), house)
        for f in obj.get("fields") or []:
            if not isinstance(f, dict):
                continue
            for value in chip_values(f):
                for code in chip_codes_from_blob(str(value or "")):
                    if code not in seen:
                        seen.add(code)
                        found.append(code)
    return found


def chip_codes_in_note(meta: dict, body: str, path: Path | None = None) -> list[str]:
    bag = meta or {}
    found: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        code = chip_code_norm(raw)
        if code and code not in seen:
            seen.add(code)
            found.append(code)

    blob = (body or "") + "\n" + str(bag.get("title") or "")
    for code in chip_codes_from_blob(blob):
        add(code)
    for key in ("code", "chips", "chip", "chipcode", "kven"):
        extra = str(bag.get(key) or "").strip()
        if not extra:
            continue
        add(extra)
        for piece in CHIP_SPLIT.split(extra):
            add(piece)
    for piece in _meta_str_list(bag.get("edges")):
        add(piece)
    for code in chip_codes_in_catalog(path):
        add(code)
    return found


def notes_with_chip(prefix: str) -> list[dict]:
    """Notes that cited this chain node, or a deeper address under it."""
    parsed = chip_code_parse(prefix)
    group = ""
    needle = ""
    if parsed is not None:
        needle = parsed["code"]
    else:
        group = chip_code_group(prefix)
        if not group:
            return []
    hits: list[dict] = []
    seen: set[str] = set()
    hosts = [lobby_host()] + list(discover_hosts().values())
    for host in hosts:
        if host is None:
            continue
        if is_codes_host(host):
            continue
        with using_host(host):
            # Hall papers (index.md) count as cites — same set as pocket_cited_codes.
            for p in iter_hash_notes():
                pocket = pocket_key(p)
                if not pocket or pocket in seen:
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                meta, body = parse_fm(text)
                codes = chip_codes_in_note(meta, body, p)
                if needle:
                    ok = any(c == needle or c.startswith(needle + ".") for c in codes)
                else:
                    ok = any(c.startswith(group + "-") for c in codes)
                if not ok:
                    continue
                seen.add(pocket)
                hits.append(
                    {
                        "pocket": pocket,
                        "title": str(meta.get("title") or "").strip()
                        or pocket_title(pocket)
                        or p.stem,
                        "href": href_from_pocket(pocket)
                        if host.name
                        else page_href(p.relative_to(active_vault()).as_posix()),
                        "crate": file_crate(p),
                    }
                )
    return hits


def pocket_cited_codes() -> set[str]:
    """Chip ZIPs cited in the pocket. go.codes papers do not count as cites of themselves."""
    found: set[str] = set()
    hosts = [lobby_host()] + list(discover_hosts().values())
    for host in hosts:
        if host is None:
            continue
        if is_codes_host(host):
            continue
        with using_host(host):
            for p in iter_hash_notes():
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                meta, body = parse_fm(text)
                for code in chip_codes_in_note(meta, body, p):
                    found.add(code)
    return found


def code_is_held(node: str, cited: set[str] | None = None) -> bool:
    """True if the pocket cites this ZIP, or a deeper address that still needs it."""
    if cited is None:
        cited = pocket_cited_codes()
    parsed = chip_code_parse(node)
    if parsed is None:
        group = chip_code_group(node)
        return bool(group) and any(chip_code_group(c) == group for c in cited)
    node_s = parsed["code"]
    for c in cited:
        if c == node_s or c.startswith(node_s + "."):
            return True
        if chip_codes_wild_match(node_s, c):
            return True
    if len(parsed["bins"]) <= 1:
        group = parsed["group"]
        return any(chip_code_group(c) == group for c in cited)
    return False


def _drop_code_paper(path: Path) -> None:
    """Unlink a codes paper, its cabinet twins, and empty parent folders."""
    page = path
    if path.is_file() and path.name.lower() == PAPER_NAME:
        page = path.parent
    for kind in SHELF_KIND:
        dest = shelf_file(kind, page)
        if dest is None or not dest.is_file():
            continue
        try:
            dest.unlink()
        except OSError:
            pass
    try:
        path.unlink()
    except OSError:
        return
    folder = path.parent
    root = codes_host_root()
    while root is not None and folder != root:
        try:
            next(folder.iterdir())
            break
        except StopIteration:
            try:
                folder.rmdir()
            except OSError:
                break
            folder = folder.parent
        except OSError:
            break


def gc_unreferenced_codes(keep: Path | None = None) -> list[str]:
    """Drop go.codes papers the pocket no longer cites."""
    host = codes_host()
    root = codes_host_root()
    if host is None or root is None or not root.is_dir():
        return []
    cited = pocket_cited_codes()
    keep_key = ""
    if keep is not None:
        try:
            keep_key = str(keep.resolve())
        except OSError:
            keep_key = str(keep)
    rows: list[tuple[Path, str]] = []
    with using_host(host):
        for p in root.rglob("*.md"):
            if p.name.lower() in {INDEX_NAME, INDEX_LEGACY}:
                continue
            try:
                raw = p.read_text(encoding="utf-8")
            except OSError:
                continue
            meta, _body = parse_fm(raw)
            kind = str(meta.get("kind") or "").strip().lower()
            if kind == "bay":
                continue
            if kind and kind not in ("code", "chip", "chipcode"):
                continue
            rel = p.relative_to(root).as_posix()
            code = note_chip_code(meta, rel, p)
            if not code or code_is_held(code, cited):
                continue
            if keep_key:
                try:
                    if str(p.resolve()) == keep_key:
                        continue
                except OSError:
                    pass
            rows.append((p, code))
        rows.sort(key=lambda row: row[1].count("."), reverse=True)
        dropped: list[str] = []
        with LBR_LOCK:
            for p, code in rows:
                if not p.is_file():
                    continue
                _drop_code_paper(p)
                dropped.append(code)
        return dropped


def code_search_form() -> str:
    return (
        "<form class=\"tag-search\" method=\"get\" action=\"/\">"
        + "<input type=\"hidden\" name=\"h\" value=\"codes\">"
        + "<input type=\"search\" name=\"touch\" placeholder=\"OT-008.T01.B002.L03\" "
        + "autocomplete=\"off\" spellcheck=\"false\">"
        + "<button type=\"submit\">open</button>"
        + "</form>"
    )


def code_look_block(rel: str, meta: dict | None) -> str:
    meta = meta or {}
    kind = str(meta.get("kind") or "").strip().lower()
    code = chip_code_norm(str(meta.get("code") or ""))
    if not code:
        code = chip_code_from_rel(rel or "")
    if not code:
        if on_codes_host():
            return (
                '<div class="codelook taglook-empty">'
                "open a cite to see what referenced this chain</div>"
            )
        return ""
    if kind and kind not in ("code", "chip", "chipcode"):
        if not on_codes_host():
            return ""
    hits = notes_with_chip(code)
    shown = chip_code_norm(code) or chip_code_group(code) or code
    if not hits:
        return (
            '<div class="codelook taglook-empty">'
            "nothing has cited this address yet</div>"
        )
    items = []
    for hit in hits:
        title = str(hit.get("title") or "").strip() or "note"
        href = str(hit.get("href") or "").strip()
        pocket = str(hit.get("pocket") or "").strip()
        items.append(
            "<li><a href=\""
            + html.escape(href, True)
            + "\">"
            + html.escape(title)
            + "</a>"
            + (
                '<span class="hit-path">' + html.escape(pocket) + "</span>"
                if pocket
                else ""
            )
            + "</li>"
        )
    return (
        '<div class="codelook"><p class="codelook-head">cited as ^'
        + html.escape(shown)
        + "</p><ul class=\"dir hits\">"
        + "".join(items)
        + "</ul></div>"
    )



def code_look_placeholder(rel: str, meta: dict | None) -> str:
    """Fast {{codelook}} slot: spinner + data attrs; cites load via /api/codelook."""
    meta = meta or {}
    kind = str(meta.get("kind") or "").strip().lower()
    code = chip_code_norm(str(meta.get("code") or ""))
    if not code:
        code = chip_code_from_rel(rel or "")
    if not code:
        if on_codes_host():
            return (
                '<div class="codelook taglook-empty">'
                "open a cite to see what referenced this chain</div>"
            )
        return ""
    if kind and kind not in ("code", "chip", "chipcode"):
        if not on_codes_host():
            return ""
    host = active_host() or ""
    return (
        '<div class="codelook is-loading" data-codelook="1"'
        ' data-h="'
        + html.escape(host, True)
        + '" data-p="'
        + html.escape(rel or "", True)
        + '" data-code="'
        + html.escape(code, True)
        + '">'
        '<span class="codelook-spin" aria-hidden="true"></span>'
        '<span class="codelook-wait">looking through cites...</span>'
        "</div>"
    )



_COMPOST_LOCK = threading.Lock()
_COMPOST_CONS: dict[str, sqlite3.Connection] = {}


def compost_yard_path() -> Path:
    return Path(os.environ.get("GLASS_COMPOST_YARD_DB") or str(COMPOST_YARD_DEFAULT))


def compost_bench_path() -> Path:
    return Path(os.environ.get("GLASS_COMPOST_BENCH_DB") or str(COMPOST_BENCH_DEFAULT))


def _compost_ro(path: Path) -> sqlite3.Connection | None:
    """Read-only handle. Chip cites are compost stamps; crate tags live in yard."""
    if not path.is_file():
        return None
    key = str(path.resolve())
    with _COMPOST_LOCK:
        con = _COMPOST_CONS.get(key)
        if con is None:
            con = sqlite3.connect(
                f"file:{path.as_posix()}?mode=ro",
                uri=True,
                check_same_thread=False,
            )
            con.row_factory = sqlite3.Row
            _COMPOST_CONS[key] = con
        return con


def _json_slugs(raw, *, skip_energy: bool = True) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        vals = list(raw)
    else:
        s = str(raw).strip()
        if not s or s in ("[]", "null"):
            return []
        try:
            vals = json.loads(s)
        except Exception:
            return []
        if not isinstance(vals, list):
            return []
    out: list[str] = []
    seen: set[str] = set()
    for v in vals:
        word = tag_slug(str(v or ""))
        if not word:
            continue
        if skip_energy and word.startswith("energy-"):
            continue
        if word in seen:
            continue
        seen.add(word)
        out.append(word)
    return out


def _compost_zip(code: str) -> dict | None:
    parsed = chip_code_parse(code)
    if parsed is None:
        return None
    try:
        serial = int(parsed["number"])
    except ValueError:
        return None
    trunk = branch = leaf = None
    for seg in parsed["segs"]:
        m = re.fullmatch(r"T(\d+)", seg, re.I)
        if m:
            trunk = int(m.group(1))
            continue
        m = re.fullmatch(r"B(\d+)", seg, re.I)
        if m:
            branch = int(m.group(1))
            continue
        m = re.fullmatch(r"L(\d+)", seg, re.I)
        if m:
            leaf = int(m.group(1))
    return {
        "group": parsed["group"],
        "serial": serial,
        "log": f"{parsed['group']}-{serial:03d}",
        "trunk": trunk,
        "branch": branch,
        "leaf": leaf,
        "code": parsed["code"],
    }


def _compost_face(y: sqlite3.Connection, group: str, serial: int):
    row = y.execute(
        """
        SELECT face_id, title, working_title, bag_code, tags_json, energy_json,
               testament, face_serial, msg_count, create_time, create_date_utc
        FROM faces
        WHERE face_serial = ? AND UPPER(COALESCE(testament, '')) = ?
        LIMIT 1
        """,
        (serial, group),
    ).fetchone()
    if row:
        return row
    return y.execute(
        """
        SELECT face_id, title, working_title, bag_code, tags_json, energy_json,
               testament, face_serial, msg_count, create_time, create_date_utc
        FROM faces
        WHERE bag_code LIKE ? OR bag_code = ?
        LIMIT 1
        """,
        (f"%-{group}-{serial:03d}", f"{group}-{serial:03d}"),
    ).fetchone()


def _compost_unix(raw) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        t = float(raw)
    except (TypeError, ValueError):
        return None
    if t > 1e12:
        t = t / 1000.0
    at = int(t)
    return at if at > 0 else None


def _msg_create_unix(y: sqlite3.Connection, face_id: str, seq: int) -> int | None:
    try:
        row = y.execute(
            "SELECT create_time FROM messages WHERE face_id=? AND seq=?",
            (face_id, seq),
        ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    return _compost_unix(row["create_time"])


def _local_stamp(at: int | None) -> datetime | None:
    if not at:
        return None
    try:
        return datetime.fromtimestamp(int(at))
    except (OSError, OverflowError, ValueError, TypeError):
        return None


def _local_day(at: int | None) -> str:
    d = _local_stamp(at)
    if d is None:
        return ""
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"


def _compost_span_label(
    y: sqlite3.Connection | None,
    face,
    face_id: str,
    start_seq: int | None = None,
    end_seq: int | None = None,
) -> str:
    """First-to-last sitting on this ZIP. Local clock, same as TPS."""
    first = last = None
    if y is not None:
        try:
            if start_seq is None:
                row = y.execute(
                    """
                    SELECT MIN(create_time) a, MAX(create_time) b
                    FROM messages WHERE face_id=?
                    """,
                    (face_id,),
                ).fetchone()
            else:
                en = end_seq if end_seq is not None else start_seq
                row = y.execute(
                    """
                    SELECT MIN(create_time) a, MAX(create_time) b
                    FROM messages WHERE face_id=? AND seq BETWEEN ? AND ?
                    """,
                    (face_id, start_seq, en),
                ).fetchone()
        except sqlite3.Error:
            row = None
        if row is not None:
            try:
                lo = row["a"]
                hi = row["b"]
            except (KeyError, IndexError, TypeError):
                lo = row[0] if len(row) else None
                hi = row[1] if len(row) > 1 else None
            first = _compost_unix(lo)
            last = _compost_unix(hi)
    a = _local_day(first)
    b = _local_day(last)
    sa = _local_stamp(first)
    sb = _local_stamp(last)
    ca = tps_clock(sa) if sa is not None else ""
    cb = tps_clock(sb) if sb is not None else ""
    if a and b and a != b:
        left = (a + " " + ca).strip()
        right = (b + " " + cb).strip()
        return left + " - " + right
    day = a or b
    if day and ca and cb and ca != cb:
        return day + " · " + ca + " - " + cb
    if day and (ca or cb):
        return day + " · " + (ca or cb)
    if day:
        return day
    if face is not None:
        try:
            day = str(face["create_date_utc"] or "").strip()
        except (KeyError, IndexError):
            day = ""
        if day:
            return day[:10]
        try:
            return _local_day(_compost_unix(face["create_time"]))
        except (KeyError, IndexError):
            return ""
    return ""


def _compost_when_unix(code: str) -> int | None:
    """Yard create_time for this ZIP: the message, or the first beat of the trunk/log."""
    z = _compost_zip(code)
    if z is None:
        return None
    y = _compost_ro(compost_yard_path())
    if y is None:
        return None
    try:
        face = _compost_face(y, z["group"], z["serial"])
    except sqlite3.Error:
        return None
    if face is None:
        return None
    face_id = str(face["face_id"])
    seq = z["branch"]
    if seq is not None:
        return _msg_create_unix(y, face_id, seq)
    if z["trunk"] is not None:
        b = _compost_ro(compost_bench_path())
        max_seq = int(face["msg_count"] or 0) - 1
        if max_seq < 0:
            max_seq = 0
        trunks = _bench_trunks(b, face_id, max_seq) if b is not None else []
        start = 0
        for t in trunks:
            if t.get("trunk_n") == z["trunk"]:
                start = int(t.get("start_seq") or 0)
                break
        return _msg_create_unix(y, face_id, start)
    at = _msg_create_unix(y, face_id, 0)
    if at:
        return at
    try:
        row = y.execute(
            "SELECT create_time FROM faces WHERE face_id=?",
            (face_id,),
        ).fetchone()
    except sqlite3.Error:
        row = None
    if row is None:
        return None
    keys = row.keys() if hasattr(row, "keys") else []
    if "create_time" not in keys:
        return None
    return _compost_unix(row["create_time"])


def _compost_message_text(code: str) -> str:
    """Yard message body at B, or the bench leaf slice at L. Empty above branch."""
    z = _compost_zip(code)
    if z is None or z.get("branch") is None:
        return ""
    y = _compost_ro(compost_yard_path())
    if y is None:
        return ""
    try:
        face = _compost_face(y, z["group"], z["serial"])
    except sqlite3.Error:
        return ""
    if face is None:
        return ""
    face_id = str(face["face_id"])
    seq = int(z["branch"])
    try:
        row = y.execute(
            "SELECT text FROM messages WHERE face_id=? AND seq=?",
            (face_id, seq),
        ).fetchone()
    except sqlite3.Error:
        return ""
    if row is None:
        return ""
    text = str(row["text"] or "")
    leaf_n = z.get("leaf")
    if leaf_n is not None:
        b = _compost_ro(compost_bench_path())
        lf = None
        if b is not None:
            try:
                lf = b.execute(
                    """
                    SELECT start_off, end_off FROM msg_leaves
                    WHERE face_id=? AND seq=? AND leaf_n=?
                    """,
                    (face_id, seq, int(leaf_n)),
                ).fetchone()
            except sqlite3.Error:
                lf = None
        if lf is not None:
            try:
                a = int(lf["start_off"] or 0)
                c = int(lf["end_off"] or 0)
            except (TypeError, ValueError):
                a = c = 0
            if c > a:
                text = text[a:c]
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def compost_message_html(meta: dict | None, rel: str = "") -> str:
    meta = meta or {}
    code = chip_code_norm(str(meta.get("code") or ""))
    if not code:
        code = chip_code_from_rel(rel or "")
    text = _compost_message_text(code)
    if not text:
        return ""
    return '<div class="compost-msg">' + html.escape(text) + "</div>"


COMPOST_MSG_CHUNK = re.compile(
    r'<div class="compost-msg">.*?</div>',
    re.I | re.S,
)


def settle_compost_message(html: str) -> str:
    """Drop the cited log printout below the bureau card, before look-through."""
    if not html:
        return html
    m = COMPOST_MSG_CHUNK.search(html)
    if not m:
        return html
    extra = m.group(0)
    html = html[: m.start()] + html[m.end() :]
    look = re.search(r'<div class="look-wrap"', html)
    if look:
        return html[: look.start()] + extra + html[look.start() :]
    return html + extra


def wear_compost_message(inner: str, meta: dict | None, rel: str = "") -> str:
    extra = compost_message_html(meta, rel)
    if not extra:
        return inner
    m = re.search(r"(?i)</h1>", inner or "")
    if m:
        return inner[: m.end()] + extra + inner[m.end() :]
    return extra + (inner or "")


def _bench_trunks(b: sqlite3.Connection, face_id: str, max_seq: int) -> list[dict]:
    try:
        cuts = list(
            b.execute(
                """
                SELECT start_seq, title, note, tags_json
                FROM hand_cuts WHERE face_id=? ORDER BY start_seq ASC
                """,
                (face_id,),
            )
        )
    except sqlite3.Error:
        return []
    starts = [int(c["start_seq"]) for c in cuts]
    if not starts or starts[0] != 0:
        starts = [0] + [s for s in starts if s != 0]
    meta = {int(c["start_seq"]): c for c in cuts}
    out: list[dict] = []
    for i, st in enumerate(starts):
        en = (starts[i + 1] - 1) if i + 1 < len(starts) else max_seq
        if en < st:
            en = st
        m = meta.get(st)
        out.append(
            {
                "trunk_n": i + 1,
                "start_seq": st,
                "end_seq": en,
                "title": str((m["title"] if m else "") or "").strip(),
                "note": str((m["note"] if m else "") or "").strip(),
                "tags": _json_slugs(m["tags_json"] if m else None),
            }
        )
    return out


def _bench_scenes(b: sqlite3.Connection | None, face_id: str) -> list[dict]:
    """Accepted Agent Eyes trunks. Proposed stays in compost until ori'el accepts."""
    if b is None:
        return []
    try:
        rows = list(
            b.execute(
                """
                SELECT start_seq, end_seq, title, shot, intensity, shift_note, status
                FROM scene_scenes WHERE face_id=? ORDER BY start_seq ASC
                """,
                (face_id,),
            )
        )
    except sqlite3.Error:
        return []
    out: list[dict] = []
    for r in rows:
        if str(r["status"] or "proposed").strip().lower() != "accepted":
            continue
        try:
            start = int(r["start_seq"] or 0)
            end = int(r["end_seq"] or start)
        except (TypeError, ValueError):
            continue
        out.append(
            {
                "start_seq": start,
                "end_seq": end if end >= start else start,
                "title": str(r["title"] or "").strip(),
                "shot": str(r["shot"] or "").strip(),
                "intensity": str(r["intensity"] or "").strip(),
                "shift": str(r["shift_note"] or "").strip(),
            }
        )
    return out


def _bench_log_shot(b: sqlite3.Connection | None, face_id: str) -> dict | None:
    if b is None:
        return None
    try:
        row = b.execute(
            """
            SELECT shot, intensity, status FROM scene_logs WHERE face_id=?
            """,
            (face_id,),
        ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    if str(row["status"] or "proposed").strip().lower() != "accepted":
        return None
    shot = str(row["shot"] or "").strip()
    if not shot:
        return None
    return {
        "shot": shot,
        "intensity": str(row["intensity"] or "").strip(),
    }


def _log_display_title(
    b: sqlite3.Connection | None, face, face_id: str, fallback: str
) -> str:
    """Prefer the name ori'el typed (working_title) over the glass ingest title."""
    work = ""
    if b is not None:
        try:
            row = b.execute(
                "SELECT working_title FROM log_marks WHERE face_id=?",
                (face_id,),
            ).fetchone()
        except sqlite3.Error:
            row = None
        if row is not None:
            work = str(row["working_title"] or "").strip()
    if not work:
        try:
            if face is not None and hasattr(face, "keys") and "working_title" in face.keys():
                work = str(face["working_title"] or "").strip()
        except (KeyError, IndexError):
            work = ""
    orig = ""
    try:
        if face is not None:
            orig = str(face["title"] or "").strip()
    except (KeyError, IndexError):
        orig = ""
    return work or orig or (fallback or "")


def _scene_at(scenes: list[dict], start_seq: int) -> dict | None:
    for sc in scenes:
        if sc["start_seq"] == start_seq:
            return sc
    for sc in scenes:
        if sc["start_seq"] <= start_seq <= sc["end_seq"]:
            return sc
    return None


def _hand_secondary(trunk: dict | None, scene: dict | None) -> str:
    if not trunk:
        return ""
    head = str(trunk.get("title") or "").strip()
    note = str(trunk.get("note") or "").strip()
    scene_title = str((scene or {}).get("title") or "").strip().lower()
    if head and scene_title and head.lower() == scene_title:
        head = ""
    bits = [p for p in (head, note) if p]
    return " — ".join(bits)


def _codes_note_from_rel(rel: str) -> Path | None:
    seat = safe_rel(rel or "")
    if seat is None:
        return None
    if seat.is_file() and seat.suffix.lower() == ".md":
        return seat
    if seat.is_dir():
        paper = seat / PAPER_NAME
        if paper.is_file():
            return paper
    return None


def _header_set_tags(headers: str, slugs: list[str], *, replace: bool = False) -> str:
    lines = (headers or "").split("\n") if headers else []
    have: list[str] = []
    out: list[str] = []
    for line in lines:
        if line.lower().startswith("tags:"):
            have.extend(split_tags(line.split(":", 1)[1]))
            continue
        out.append(line)
    seen: set[str] = set()
    merged: list[str] = []
    for raw in ([] if replace else have) + list(slugs):
        word = tag_slug(raw)
        if not word or word in seen:
            continue
        seen.add(word)
        merged.append(word)
    if merged:
        out.append("tags: " + ", ".join(merged))
    return "\n".join(out)


def _strip_code_paper_stock(markdown: str) -> tuple[str, list[str]]:
    """Drop the mint blurb and hash-only lines. Return leftover body + pulled slugs."""
    pulled: list[str] = []
    kept: list[str] = []
    for line in (markdown or "").split("\n"):
        stripped = line.strip()
        if stripped == CODE_PAPER_BLURB:
            continue
        if stripped and HASH_ONLY_LINE_RE.match(stripped):
            for m in TAG_RE.finditer(stripped):
                word = tag_slug(m.group(1))
                if word:
                    pulled.append(word)
            continue
        kept.append(line)
    body = "\n".join(kept).strip()
    if not body:
        body = "# {{code}}"
    return body + "\n", pulled


def _stamp_code_hashes(rel: str, slugs: list[str]) -> None:
    """Keep hashes in YAML tags: so go.code.tags can see them. Paper face stays just the code."""
    want: list[str] = []
    seen: set[str] = set()
    for raw in slugs:
        word = tag_slug(raw)
        if not word or word in seen:
            continue
        seen.add(word)
        want.append(word)
        ensure_tag_page(word)
    path = _codes_note_from_rel(rel)
    if path is None or not path.is_file():
        return
    with LBR_LOCK:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            return
        meta, _body = parse_fm(raw)
        kind = str(meta.get("kind") or "").strip().lower()
        if kind and kind not in ("code", "chip", "chipcode"):
            return
        headers, markdown = split_note(raw)
        new_md, pulled = _strip_code_paper_stock(markdown)
        headers2 = _header_set_tags(headers, want + pulled, replace=True)
        new_raw = join_note(headers2, new_md)
        if note_text(new_raw) == note_text(raw):
            return
        write_note(path, new_raw)


def _compost_chip_ids(
    y: sqlite3.Connection | None,
    face_id: str,
    start_seq: int | None = None,
    end_seq: int | None = None,
) -> list[str]:
    """Yard message chip_ids in this ZIP, seq order. One seq if start==end."""
    if y is None or not face_id:
        return []
    try:
        if start_seq is None:
            rows = y.execute(
                "SELECT chip_id FROM messages WHERE face_id=? ORDER BY seq",
                (face_id,),
            )
        else:
            en = end_seq if end_seq is not None else start_seq
            rows = y.execute(
                """
                SELECT chip_id FROM messages
                WHERE face_id=? AND seq BETWEEN ? AND ?
                ORDER BY seq
                """,
                (face_id, start_seq, en),
            )
    except sqlite3.Error:
        return []
    out: list[str] = []
    for row in rows:
        try:
            cid = str(row["chip_id"] or "").strip()
        except (KeyError, IndexError, TypeError):
            cid = str(row[0] or "").strip() if row else ""
        if cid:
            out.append(cid)
    return out


def _codes_cabinet_page(paper: Path) -> Path:
    """Cabinets hang on the folder for a hall paper, same as TPS."""
    page = paper
    if page.is_file() and (
        is_shell_name(page.name) or page.name.lower() == PAPER_NAME
    ):
        page = page.parent
    return page


CODES_LIB_OWNED = ("title", "messages", "references", "energy")


def _codes_into_cabinets(
    paper: Path,
    log_code: str,
    *,
    refs: list[str] | None = None,
    energy: list[str] | None = None,
    title: str = "",
    chip_ids: list[str] | None = None,
) -> None:
    """Compost-owned librarian fields rewrite on peek. Charlie only gets face refs/energy."""
    page = _codes_cabinet_page(paper)
    frm = tag_slug(log_code)
    ref_slugs = [tag_slug(t) for t in (refs or []) if tag_slug(t)]
    energy_slugs = [tag_slug(t) for t in (energy or []) if tag_slug(t)]
    title = str(title or "").strip()
    ids = [str(c).strip() for c in (chip_ids or []) if str(c).strip()]
    want: list[tuple[str, str]] = []
    if title:
        want.append(("title", title))
    if ids:
        want.append(("messages", ", ".join(ids)))
    if ref_slugs:
        want.append(("references", ", ".join(ref_slugs)))
    if energy_slugs:
        want.append(("energy", ", ".join(energy_slugs)))
    owned = set(CODES_LIB_OWNED)
    with LBR_LOCK:
        lib_dest = shelf_file("librarian", page)
        if lib_dest is not None:
            pocket = pocket_key(shelf_anchor("librarian", page))
            crate = bag_crate(shelf_anchor("librarian", page))
            obj = catalog_read(lib_dest, pocket, "LIBRARIAN")
            fields = [f for f in (obj.get("fields") or []) if isinstance(f, dict)]
            kept: list[dict] = []
            for f in fields:
                lab = str(f.get("label") or "").strip().lower()
                if lab in owned:
                    continue
                kept.append(f)
            for lab, val in want:
                kept.append({"type": "input", "label": lab, "value": val})
            obj["fields"] = kept
            obj["pocket"] = pocket
            obj["house"] = "LIBRARIAN"
            if crate:
                obj["crate"] = crate
            catalog_write(lib_dest, obj)
        if not frm or (not ref_slugs and not energy_slugs):
            return
        cha_dest = shelf_file("charlie", page)
        if cha_dest is not None:
            pocket = pocket_key(shelf_anchor("charlie", page))
            crate = bag_crate(shelf_anchor("charlie", page))
            blot = blot_read(cha_dest, pocket, "CHARLIE")
            charlie_normalize(blot)
            kept_th: list[dict] = []
            for t in blot.get("threads") or []:
                if not isinstance(t, dict):
                    continue
                if tag_slug(str(t.get("from") or "")) == frm and tag_slug(
                    str(t.get("rel") or "")
                ) in ("references", "energy"):
                    continue
                kept_th.append(t)
            blot["threads"] = kept_th
            if ref_slugs:
                charlie_weave(blot, frm, "references", ", ".join(ref_slugs))
            if energy_slugs:
                charlie_weave(blot, frm, "energy", ", ".join(energy_slugs))
            blot["pocket"] = pocket
            blot["house"] = "CHARLIE"
            if crate:
                blot["crate"] = crate
            blot_write(cha_dest, blot)


def _compost_tag_chip(slug: str) -> str:
    ensure_tag_page(slug)
    return tag_chip(slug)


def _compost_tag_row(slugs: list[str], klass: str = "compost-tags") -> str:
    chips = [_compost_tag_chip(s) for s in slugs if s]
    if not chips:
        return ""
    return '<p class="' + klass + '">' + " ".join(chips) + "</p>"


def compost_look_block(rel: str, meta: dict | None) -> str:
    """Headlines, cuts, and tags from compost/yard on this ZIP. Does not mint pages."""
    meta = meta or {}
    kind = str(meta.get("kind") or "").strip().lower()
    code = chip_code_norm(str(meta.get("code") or ""))
    if not code:
        code = chip_code_from_rel(rel or "")
    if not code:
        if on_codes_host():
            return (
                '<div class="compostlook taglook-empty">'
                "open a cite to see compost work at that chip</div>"
            )
        return ""
    if kind and kind not in ("code", "chip", "chipcode"):
        if not on_codes_host():
            return ""
        group_only = chip_code_group(code) == code or chip_code_parse(code) is None
        if group_only and kind == "bay":
            return (
                '<div class="compostlook taglook-empty">'
                "open a log chip to pull compost headlines</div>"
            )
    z = _compost_zip(code)
    if z is None:
        return (
            '<div class="compostlook taglook-empty">'
            "not a glass ZIP</div>"
        )
    y = _compost_ro(compost_yard_path())
    b = _compost_ro(compost_bench_path())
    if y is None and b is None:
        return (
            '<div class="compostlook taglook-empty">'
            "glass compost dbs not open</div>"
        )
    face = None
    if y is not None:
        try:
            face = _compost_face(y, z["group"], z["serial"])
        except sqlite3.Error:
            face = None
    if face is None:
        return (
            '<div class="compostlook taglook-empty">'
            "no yard face for "
            + html.escape(z["log"])
            + "</div>"
        )
    face_id = str(face["face_id"])
    max_seq = int(face["msg_count"] or 0) - 1
    if max_seq < 0:
        max_seq = 0
    trunks = _bench_trunks(b, face_id, max_seq) if b is not None else []
    scenes = _bench_scenes(b, face_id)
    log_shot = _bench_log_shot(b, face_id)
    seq = z["branch"]
    leaf_n = z["leaf"]
    trunk = None
    if seq is not None and trunks:
        for t in trunks:
            if t["start_seq"] <= seq <= t["end_seq"]:
                trunk = t
                break
    if trunk is None and z["trunk"] is not None and trunks:
        for t in trunks:
            if t["trunk_n"] == z["trunk"]:
                trunk = t
                break

    yard_tags: list[str] = []
    bench_tags: list[str] = []
    face_refs: list[str] = []
    face_energy: list[str] = []
    title = ""
    note = ""
    shot = ""
    shift = ""
    intensity = ""
    hand = ""
    kicker = ""
    kids: list[dict] = []

    if leaf_n is not None and seq is not None:
        kicker = "leaf"
        if b is not None:
            try:
                lf = b.execute(
                    """
                    SELECT title, note, tags_json FROM msg_leaves
                    WHERE face_id=? AND seq=? AND leaf_n=?
                    """,
                    (face_id, seq, leaf_n),
                ).fetchone()
            except sqlite3.Error:
                lf = None
            if lf:
                title = str(lf["title"] or "").strip()
                note = str(lf["note"] or "").strip()
                bench_tags = _json_slugs(lf["tags_json"])
        if y is not None:
            try:
                yl = y.execute(
                    """
                    SELECT tags_json FROM leaves
                    WHERE face_id=? AND ix=? AND parent_chip=?
                    """,
                    (face_id, leaf_n, f"{face_id}.{seq}"),
                ).fetchone()
            except sqlite3.Error:
                yl = None
            if yl:
                yard_tags = _json_slugs(yl["tags_json"])
    elif seq is not None:
        kicker = "branch"
        if trunk:
            title = trunk.get("title") or ""
            note = trunk.get("note") or ""
            bench_tags = list(trunk.get("tags") or [])
        if b is not None:
            try:
                mt = b.execute(
                    "SELECT tags_json FROM msg_tags WHERE face_id=? AND seq=?",
                    (face_id, seq),
                ).fetchone()
            except sqlite3.Error:
                mt = None
            if mt:
                for t in _json_slugs(mt["tags_json"]):
                    if t not in bench_tags:
                        bench_tags.append(t)
        if y is not None:
            try:
                ym = y.execute(
                    "SELECT tags_json FROM messages WHERE face_id=? AND seq=?",
                    (face_id, seq),
                ).fetchone()
            except sqlite3.Error:
                ym = None
            if ym:
                yard_tags = _json_slugs(ym["tags_json"])
    elif trunk is not None:
        kicker = "trunk"
        title = trunk.get("title") or ""
        note = trunk.get("note") or ""
        bench_tags = list(trunk.get("tags") or [])
        scene = _scene_at(scenes, trunk["start_seq"])
        if scene:
            title = scene.get("title") or title
            shot = scene.get("shot") or ""
            shift = scene.get("shift") or ""
            intensity = scene.get("intensity") or ""
            hand = _hand_secondary(trunk, scene)
            note = ""
        if y is not None:
            try:
                for row in y.execute(
                    """
                    SELECT seq, tags_json FROM messages
                    WHERE face_id=? AND seq BETWEEN ? AND ?
                    ORDER BY seq
                    """,
                    (face_id, trunk["start_seq"], trunk["end_seq"]),
                ):
                    for t in _json_slugs(row["tags_json"]):
                        if t not in yard_tags:
                            yard_tags.append(t)
            except sqlite3.Error:
                pass
    else:
        kicker = "log"
        title = _log_display_title(b, face, face_id, str(z["log"]))
        if log_shot:
            shot = log_shot.get("shot") or ""
            intensity = log_shot.get("intensity") or ""
        face_refs = _json_slugs(face["tags_json"], skip_energy=False)
        energy = None
        if hasattr(face, "keys") and "energy_json" in face.keys():
            energy = face["energy_json"]
        for t in _json_slugs(energy, skip_energy=False):
            if t not in face_energy:
                face_energy.append(t)
        if scenes:
            for i, sc in enumerate(scenes):
                tn = i + 1
                cut = None
                for t in trunks:
                    if t["start_seq"] == sc["start_seq"]:
                        cut = t
                        break
                kids.append(
                    {
                        "lab": f"T{tn:02d} · " + (sc.get("title") or f"T{tn:02d}"),
                        "href": chip_code_href(f"{z['log']}.T{tn:02d}"),
                        "shot": sc.get("shot") or "",
                        "intensity": sc.get("intensity") or "",
                        "hand": _hand_secondary(cut, sc),
                    }
                )
                if cut:
                    for tag in cut.get("tags") or []:
                        if tag not in bench_tags:
                            bench_tags.append(tag)
        else:
            for t in trunks:
                head = t.get("title") or f"T{t['trunk_n']:02d}"
                kids.append(
                    {
                        "lab": f"T{t['trunk_n']:02d} · " + head,
                        "href": chip_code_href(f"{z['log']}.T{t['trunk_n']:02d}"),
                        "note": t.get("note") or "",
                    }
                )
                for tag in t.get("tags") or []:
                    if tag not in bench_tags:
                        bench_tags.append(tag)

    when = ""
    if kicker in ("leaf", "branch") and seq is not None:
        when = _compost_span_label(y, face, face_id, seq, seq)
    elif kicker == "trunk" and trunk is not None:
        when = _compost_span_label(
            y, face, face_id, trunk["start_seq"], trunk["end_seq"]
        )
    elif kicker == "log":
        when = _compost_span_label(y, face, face_id)

    yard_only = [t for t in yard_tags if t not in bench_tags]
    stamp_tags = list(bench_tags)
    if kicker != "log":
        for t in yard_tags:
            if t not in stamp_tags:
                stamp_tags.append(t)
    _stamp_code_hashes(rel, stamp_tags)
    paper = _codes_note_from_rel(rel)
    if paper is not None:
        _codes_tps_created(paper, z["code"], minted=False)
        chip_ids: list[str] = []
        if kicker in ("leaf", "branch") and seq is not None:
            chip_ids = _compost_chip_ids(y, face_id, seq, seq)
        elif kicker == "trunk" and trunk is not None:
            chip_ids = _compost_chip_ids(
                y, face_id, trunk["start_seq"], trunk["end_seq"]
            )
        _codes_into_cabinets(
            paper,
            z["code"],
            refs=face_refs if kicker == "log" else [],
            energy=face_energy if kicker == "log" else [],
            title=title,
            chip_ids=chip_ids,
        )
    has = bool(title or note or shot or shift or when or bench_tags or yard_tags or kids)
    if not has:
        return (
            '<div class="compostlook taglook-empty">'
            "no compost headlines or tags at "
            + html.escape(z["code"])
            + " yet</div>"
        )
    bits = [
        '<div class="compostlook"><p class="compostlook-head">',
        html.escape(kicker),
        " · ^",
        html.escape(z["code"]),
        "</p>",
    ]
    if when:
        bits.append('<p class="compost-when">' + html.escape(when) + "</p>")
    if intensity:
        bits.append(
            '<p class="compost-intensity">' + html.escape(intensity) + "</p>"
        )
    if title:
        bits.append('<p class="compost-title">' + html.escape(title) + "</p>")
    if shot:
        bits.append('<p class="compost-shot">' + html.escape(shot) + "</p>")
    if shift:
        bits.append('<p class="compost-shift">' + html.escape(shift) + "</p>")
    if note:
        bits.append('<p class="compost-note">' + html.escape(note) + "</p>")
    if hand:
        bits.append('<p class="compost-hand">' + html.escape(hand) + "</p>")
    bits.append(_compost_tag_row(bench_tags, "compost-tags"))
    if kicker != "log" and yard_only:
        bits.append(_compost_tag_row(yard_only, "compost-tags yard"))
    if kids:
        bits.append('<ul class="compost-kids">')
        for kid in kids[:24]:
            if not isinstance(kid, dict):
                continue
            bits.append("<li>")
            lab = str(kid.get("lab") or "").strip()
            href = str(kid.get("href") or "").strip()
            if lab:
                if href:
                    bits.append(
                        '<a class="kid-lab" href="'
                        + html.escape(href, True)
                        + '">'
                        + html.escape(lab)
                        + "</a>"
                    )
                else:
                    bits.append('<span class="kid-lab">' + html.escape(lab) + "</span>")
            kid_int = str(kid.get("intensity") or "").strip()
            if kid_int:
                bits.append(
                    '<span class="kid-intensity">' + html.escape(kid_int) + "</span>"
                )
            kid_shot = str(kid.get("shot") or "").strip()
            if kid_shot:
                bits.append(
                    '<span class="kid-shot">' + html.escape(kid_shot) + "</span>"
                )
            kid_note = str(kid.get("note") or "").strip()
            if kid_note:
                bits.append(
                    '<span class="kid-note">' + html.escape(kid_note) + "</span>"
                )
            kid_hand = str(kid.get("hand") or "").strip()
            if kid_hand:
                bits.append(
                    '<span class="kid-hand">' + html.escape(kid_hand) + "</span>"
                )
            bits.append("</li>")
        bits.append("</ul>")
    bits.append("</div>")
    return "".join(bits)


def recent_limit(raw: str | None) -> int:
    n = RECENT_COUNT
    if raw is not None and str(raw).strip().isdigit():
        n = int(raw)
    return max(1, min(n, RECENT_CAP))


def iter_mtime_notes() -> list[Path]:
    """Notes and canvases across the lobby and every host, newest mtime first."""
    out: list[Path] = []
    seen: set[str] = set()
    hosts = [lobby_host()] + list(discover_hosts().values())
    for host in hosts:
        if host is None or not host.root.is_dir():
            continue
        root = host.root
        lobby = not str(getattr(host, "name", "") or "").strip()
        walk = root.iterdir() if lobby else root.rglob("*")
        for p in walk:
            if not p.is_file() or p.suffix.lower() not in {".md", ".canvas", ".chip"}:
                continue
            if p.name.lower() == RECENT_NAME:
                continue
            try:
                parts = p.relative_to(root).parts
            except ValueError:
                continue
            if any(part in SKIP or stash_name(part) for part in parts):
                continue
            seen_key = ""
            try:
                seen_key = str(p.resolve())
            except OSError:
                seen_key = str(p)
            if seen_key in seen:
                continue
            seen.add(seen_key)
            out.append(p)
    return out


def recent_hits(limit: int | str | None = None) -> list[dict]:
    n = recent_limit(str(limit) if limit is not None else None)
    ranked: list[tuple[float, Path]] = []
    for p in iter_mtime_notes():
        try:
            at = p.stat().st_mtime
        except OSError:
            continue
        ranked.append((at, p))
    ranked.sort(key=lambda t: t[0], reverse=True)
    hits: list[dict] = []
    for at, p in ranked[:n]:
        door = door_for_path(p)
        title = ""
        href = ""
        pocket = ""
        if door is not None:
            title = str(door.get("title") or "").strip()
            href = str(door.get("href") or "").strip()
            pocket = str(door.get("pocket") or "").strip()
        if not href:
            try:
                rel = p.relative_to(HOSTS_ROOT.resolve()).as_posix()
            except (OSError, ValueError):
                continue
            with using_host(lobby_host()):
                href = page_href(rel)
                title = md_list_label(p) if p.suffix.lower() == ".md" else p.stem
                if p.name.lower() == START_NAME:
                    pocket = "go"
                elif p.name.lower() == ROAM_NAME:
                    pocket = "roam"
                elif p.name.lower() == RECENT_NAME:
                    pocket = "recent"
                else:
                    pocket = "go/" + p.stem
        stamp = datetime.fromtimestamp(int(at)).strftime("%b %d %H:%M")
        hits.append(
            {
                "title": title or p.stem,
                "href": href or "/",
                "pocket": pocket,
                "when": stamp,
            }
        )
    return hits


def recent_block(limit: int | str | None = None) -> str:
    hits = recent_hits(limit)
    if not hits:
        return '<div class="recentlook taglook-empty">no notes have been kept yet</div>'
    items = []
    for hit in hits:
        path = str(hit.get("pocket") or "").strip()
        when = str(hit.get("when") or "").strip()
        bits = []
        if when:
            bits.append('<time class="hit-when">' + html.escape(when) + "</time>")
        bits.append(
            "<a href=\""
            + html.escape(str(hit.get("href") or "/"), True)
            + "\">"
            + html.escape(str(hit.get("title") or "note"))
            + "</a>"
        )
        if path:
            bits.append('<span class="hit-path">' + html.escape(path) + "</span>")
        items.append("<li>" + "".join(bits) + "</li>")
    return (
        '<div class="recentlook"><ul class="dir hits">'
        + "".join(items)
        + "</ul></div>"
    )


INJECTOR_RE = re.compile(
    r"(?:<p>\s*)?\{\{injector(?::([^}]*))?\}\}(?:\s*</p>)?"
    r"(.*?)"
    r"(?:<p>\s*)?\{\{/injector\}\}(?:\s*</p>)?",
    re.I | re.S,
)
INJECTOR_FIELD_RE = re.compile(
    r"\{\{(text|textarea):([A-Za-z][A-Za-z0-9_-]*)(?:\|([^}]+))?\}\}",
    re.I,
)
INJECTOR_HIDDEN_RE = re.compile(
    r"\{\{hidden:([A-Za-z][A-Za-z0-9_-]*)\}\}(.*?)\{\{/hidden\}\}",
    re.I | re.S,
)
INJECTOR_TIME_RE = re.compile(r"\{\{\s*time(?::([A-Za-z][A-Za-z0-9_-]*))?\s*\}\}", re.I)
INJECTOR_SLOT_RE = re.compile(r"\{\{\s*([A-Za-z][A-Za-z0-9_-]*)\s*\}\}", re.I)
INSERT_TITLE_KEYS = ("line", "name", "title")
INSERT_BODY_KEYS = (
    "message",
    "what-happened",
    "what_happened",
    "body",
    "entry",
    "log",
    "happened",
)
INSERT_YAML_MOUTHS = {"frontmatter", "fm", "yaml", "headers", "header"}
INSERT_META_SLOT = {
    "librarian": "{{meta:librarian}}",
    "detective": "{{meta:detective}}",
    "tps": "{{meta:tps}}",
}


def insert_strip_html(src: str) -> str:
    return re.sub(r"<[^>]+>", "\n", src or "")


def insert_mouth(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in INSERT_YAML_MOUTHS:
        return "yaml"
    return mouth_canon(s)


def parse_injector_fields(inner: str) -> list[tuple[str, str, str]]:
    text = insert_strip_html(inner)
    row_label: dict[str, str] = {}
    for line in text.split("\n"):
        line = line.strip()
        fm = INJECTOR_FIELD_RE.search(line)
        if not fm:
            continue
        name = fm.group(2).lower()
        prefix = line.split("{{", 1)[0]
        if ":" in prefix:
            lab = prefix.split(":", 1)[0].strip()
            if lab and not lab.startswith("{{"):
                row_label[name] = lab.replace("_", " ")
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for m in INJECTOR_FIELD_RE.finditer(text):
        kind = m.group(1).lower()
        name = m.group(2).lower()
        if name in seen:
            continue
        seen.add(name)
        label = (
            (m.group(3) or "").strip()
            or row_label.get(name)
            or name.replace("-", " ").replace("_", " ")
        )
        out.append((kind, name, label))
    return out or [("text", "line", "line")]


def injector_form_html(
    land: str,
    fields: list[tuple[str, str, str]],
    folder: Path,
    crumb_rel: str | None,
) -> str:
    # Standing = the page that owns the recipe. When the open crumb is a note,
    # that note (not its parent folder index) must supply insert_parse_recipe —
    # otherwise a hidden injector sheet's clay is ignored and only the title lands.
    # land:here still files into clay_folder(standing) = the note's parent hall.
    standing = ""
    try:
        if crumb_rel:
            here = (crumb_rel or "").replace("\\", "/").strip("/")
            seat = safe_rel(here) if here else None
            if seat is not None and seat.is_file():
                standing = pocket_key(seat)
            else:
                standing = pocket_key(folder_from_rel(crumb_rel, folder) or folder)
        else:
            standing = pocket_key(folder)
    except OSError:
        standing = pocket_key(folder)
    land = (land or "here").strip() or "here"
    bits = [
        '<form class="pg-injector" method="post" action="/api/insert">',
        '<input type="hidden" name="pocket" value="'
        + html.escape(standing, True)
        + '">',
        '<input type="hidden" name="land" value="' + html.escape(land, True) + '">',
    ]
    for kind, name, label in fields:
        shown = html.escape(label or name.replace("-", " "))
        fid = "inj-" + html.escape(name, True)
        bits.append('<label class="pg-injector-row" for="' + fid + '">')
        bits.append('<span class="pg-injector-label">' + shown + "</span>")
        if kind == "textarea":
            bits.append(
                '<textarea class="pg-injector-field" id="'
                + fid
                + '" name="f_'
                + html.escape(name, True)
                + '" rows="4" required></textarea>'
            )
        else:
            bits.append(
                '<input class="pg-injector-field" id="'
                + fid
                + '" type="text" name="f_'
                + html.escape(name, True)
                + '" autocomplete="off" spellcheck="false" required>'
            )
        bits.append("</label>")
    bits.append('<button type="submit">post</button>')
    bits.append("</form>")
    return "".join(bits)


def expand_injectors(body: str, folder: Path, crumb_rel: str | None) -> tuple[str, bool]:
    hit = False

    def repl(m: re.Match[str]) -> str:
        nonlocal hit
        hit = True
        land = (m.group(1) or "here").strip()
        fields = parse_injector_fields(m.group(2) or "")
        return injector_form_html(land, fields, folder, crumb_rel)

    return INJECTOR_RE.sub(repl, body), hit


def insert_title_from(
    fields: dict[str, str], prefer: list[str] | None = None
) -> str:
    keys = list(prefer or []) + [k for k in INSERT_TITLE_KEYS if k not in (prefer or [])]
    for key in keys:
        t = str(fields.get(key) or "").strip()
        if t:
            return t.split("\n", 1)[0].strip()[:80]
    for key in INSERT_BODY_KEYS:
        t = str(fields.get(key) or "").strip()
        if t:
            return t.split("\n", 1)[0].strip()[:80]
    for v in fields.values():
        t = str(v or "").strip()
        if t:
            return t.split("\n", 1)[0].strip()[:80]
    return ""


def insert_body_from(
    fields: dict[str, str], title: str, body_names: list[str] | None = None
) -> str:
    if body_names is not None:
        bits: list[str] = []
        for name in body_names:
            t = str(fields.get(name) or "").strip()
            if t:
                bits.append(t)
        if bits:
            return "\n\n".join(bits)
        return title
    for key in INSERT_BODY_KEYS:
        t = str(fields.get(key) or "").strip()
        if t:
            return t
    line = str(fields.get("line") or "").strip()
    if line:
        return line
    return title


def insert_dest(folder: Path, title: str) -> Path | None:
    fname = note_filename(title)
    if not fname:
        fname = note_filename(datetime.now().strftime("%Y-%m-%d-%H%M"))
    if not fname:
        return None
    dest = folder / fname
    if not dest.exists():
        return dest
    stem = dest.stem
    for i in range(2, 80):
        alt = folder / (stem + "-" + str(i) + ".md")
        if not alt.exists():
            return alt
    return None


def insert_land_folder(standing: Path, land: str) -> Path | None:
    land = (land or "here").strip()
    if not land or land.lower() in ("here", "this", "."):
        folder = clay_folder(standing) if standing.is_file() else standing
        return folder if folder is not None and folder.is_dir() else None
    raw = land
    if not GO_PREFIX.match(raw.replace("\\", "/").strip()):
        host = active_host()
        raw = format_pocket(host, land.strip("/")) if host else land
    target = resolve_vault_page(raw)
    if target is None:
        return None
    folder = clay_folder(target) if target.is_file() else target
    if folder is None or not folder.is_dir() or not _in_active_vault(folder):
        return None
    return folder


def insert_standing_src(standing: Path) -> tuple[dict, str]:
    if standing.is_file() and standing.suffix.lower() == ".md":
        try:
            meta, body = parse_fm(standing.read_text(encoding="utf-8-sig"))
            return meta, rewrite_tool_slots(body)
        except OSError:
            return {}, ""
    paper = load_paper(standing) if standing.is_dir() else None
    if paper:
        meta, body = paper
        return meta, rewrite_tool_slots(body)
    loaded = load_index(standing) if standing.is_dir() else None
    if loaded:
        meta, body = loaded
        return meta, rewrite_tool_slots(body)
    return {}, ""


def insert_resolve_value(
    spec: str, standing_meta: dict, now: datetime, fields: dict[str, str]
) -> str:
    text = str(spec or "")
    unix = str(int(now.timestamp()))
    when = now.strftime("%Y-%m-%d %H:%M")

    def field_token(m: re.Match[str]) -> str:
        return str(fields.get(m.group(2).lower()) or "").strip()

    text = INJECTOR_FIELD_RE.sub(field_token, text)

    def time_token(m: re.Match[str]) -> str:
        """{{time}} / {{time:now}} → now. {{time:when}} → field override (TPS-parseable), else now."""
        name = (m.group(1) or "now").strip().lower()
        if name in ("", "now"):
            return unix
        raw = str(fields.get(name) or "").strip()
        if not raw:
            return unix
        # Prefer unix seconds if user pasted epoch; else parse_tps_time / librarian time.
        if re.fullmatch(r"\d{9,12}", raw) or re.fullmatch(r"u:?\d{9,12}", raw, re.I):
            dig = re.sub(r"^u:?", "", raw, flags=re.I)
            return dig
        try:
            got = parse_tps_time(raw)
            if got is None:
                got = parse_librarian_time(raw)
            if got is None:
                return unix
            if isinstance(got, tuple) and got:
                return str(int(got[0]))
            if isinstance(got, (int, float)):
                return str(int(got))
            if isinstance(got, datetime):
                return str(int(got.timestamp()))
            return unix
        except Exception:
            return unix

    text = INJECTOR_TIME_RE.sub(time_token, text)

    def slot_token(m: re.Match[str]) -> str:
        key = m.group(1)
        low = key.lower()
        if low in ("when",):
            return when
        if low in ("date",):
            return now.strftime("%Y-%m-%d")
        got = str(fields.get(low) or "").strip()
        if got:
            return got
        for mk, mv in (standing_meta or {}).items():
            if str(mk).lower() == low:
                return str(mv or "").strip()
        return ""

    text = INJECTOR_SLOT_RE.sub(slot_token, text)
    return text.strip()


def insert_parse_recipe(src: str) -> dict:
    """Visible clay → page. hidden:mouth → that cabinet (or yaml)."""
    inners = [m.group(2) or "" for m in INJECTOR_RE.finditer(src or "")]
    raw = insert_strip_html("\n".join(inners) if inners else src)
    spans: list[tuple[int, int, str, str]] = []
    for m in INJECTOR_HIDDEN_RE.finditer(raw):
        spans.append((m.start(), m.end(), insert_mouth(m.group(1)), m.group(2) or ""))
    body_names: list[str] = []
    yaml_names: list[str] = []
    seen_body: set[str] = set()
    seen_yaml: set[str] = set()
    for m in INJECTOR_FIELD_RE.finditer(raw):
        name = m.group(2).lower()
        dest = "body"
        for start, end, mouth, _inner in spans:
            if start <= m.start() < end:
                dest = mouth
                break
        if dest == "yaml":
            if name not in seen_yaml:
                seen_yaml.add(name)
                yaml_names.append(name)
        elif dest == "body" and name not in seen_body:
            seen_body.add(name)
            body_names.append(name)
    cabinets: dict[str, list[tuple[str, str, str]]] = {}
    for _start, _end, mouth, inner in spans:
        if mouth == "yaml":
            continue
        inner = insert_strip_html(inner)
        rows: list[tuple[str, str, str]] = []
        for line in inner.split("\n"):
            line = line.strip()
            if not line:
                continue
            if INJECTOR_FIELD_RE.fullmatch(line):
                continue
            label = ""
            spec = ""
            prefix = line.split("{{", 1)[0]
            if ":" in prefix:
                label, spec = line.split(":", 1)
                label = label.strip()
                spec = spec.strip()
            elif INJECTOR_TIME_RE.search(line):
                tm = INJECTOR_TIME_RE.search(line)
                label = line[: tm.start()].strip() if tm else ""
                spec = tm.group(0) if tm else line
            else:
                continue
            if not label:
                continue
            kind = "time" if INJECTOR_TIME_RE.search(spec) else "input"
            rows.append((label, spec, kind))
        if rows:
            cabinets.setdefault(mouth, []).extend(rows)
    events: list[tuple[int, str, str]] = []
    for start, _end, mouth, _inner in spans:
        events.append((start, "hidden", mouth))
    for m in INJECTOR_FIELD_RE.finditer(raw):
        name = m.group(2).lower()
        inside = any(start <= m.start() < end for start, end, _mouth, _inner in spans)
        if not inside:
            events.append((m.start(), "field", name))
    events.sort(key=lambda e: e[0])
    face: list[tuple[str, str]] = []
    seen_meta: set[str] = set()
    heading_done = False
    for _start, kind, name in events:
        if kind == "hidden":
            if name == "yaml":
                if not heading_done:
                    face.append(("heading", ""))
                    heading_done = True
            elif name not in seen_meta and name in INSERT_META_SLOT:
                seen_meta.add(name)
                face.append(("meta", name))
        elif name in INSERT_TITLE_KEYS and not heading_done:
            face.append(("heading", ""))
            heading_done = True
        else:
            face.append(("body", name))
    if not heading_done:
        face.insert(0, ("heading", ""))
    return {
        "body_names": body_names,
        "yaml_names": yaml_names,
        "cabinets": cabinets,
        "has_tps": "tps" in {m for _s, _e, m, _i in spans},
        "face": face,
    }


def insert_face_parts(
    recipe: dict, fields: dict[str, str], title: str
) -> list[str]:
    """Minted page face, in injector clay order."""
    parts: list[str] = []
    seen_heading = False
    for kind, name in recipe.get("face") or []:
        if kind == "heading":
            parts.append("# {{title}}")
            seen_heading = True
            continue
        if kind == "meta":
            slot = INSERT_META_SLOT.get(name)
            if slot:
                parts.append(slot)
            continue
        t = str(fields.get(name) or "").strip()
        if not t:
            continue
        if seen_heading and t == title:
            continue
        # section-ish fields dress as ## so ingest can match daily-inventory shape
        if name in ("type", "section", "heading", "kind") and not t.lstrip().startswith("#"):
            t = "## " + t
        parts.append(t)
    if not seen_heading:
        parts.insert(0, "# {{title}}")
    if not parts:
        parts.append("# {{title}}")
    return parts


def insert_file_cabinets(
    dest: Path,
    standing: Path,
    standing_meta: dict,
    now: datetime,
    fields: dict | None = None,
    recipe: dict | None = None,
) -> list[str]:
    """Only hidden:mouth rows file cabinets. Visible fields stay on the page."""
    new_pocket = pocket_key(dest)
    _meta, src = insert_standing_src(standing)
    standing_meta = standing_meta or _meta or {}
    fields = fields or {}
    if recipe is None:
        recipe = insert_parse_recipe(src)
    printed: list[str] = []
    cabinets: dict[str, list[tuple[str, str, str]]] = recipe.get("cabinets") or {}
    tps_rows = cabinets.get("tps") or []
    if recipe.get("has_tps") or tps_rows:
        if not tps_rows:
            tps_stamp_add(new_pocket, "created", str(int(now.timestamp())))
        for label, spec, _kind in tps_rows:
            val = insert_resolve_value(spec, standing_meta, now, fields)
            tps_stamp_add(new_pocket, label, val or str(int(now.timestamp())))
        printed.append("tps")
    else:
        tps_stamp_add(new_pocket, "created", str(int(now.timestamp())))
    for mouth, items in cabinets.items():
        if mouth == "tps":
            continue
        if mouth not in CATALOG:
            continue
        for label, spec, kind in items:
            val = insert_resolve_value(spec, standing_meta, now, fields)
            if not val:
                continue
            use = kind if kind in FIELD_TYPES else "input"
            catalog_field_add(mouth, new_pocket, use, label, val)
        printed.append(mouth)
    return printed


def insert_post(data: dict) -> tuple[int, dict | None, str]:
    """Mint a crate'd note. Visible clay → body. hidden:mouth → that cabinet."""
    if not isinstance(data, dict):
        return 400, None, "bad body"
    pocket_raw = str(data.get("pocket") or data.get("from") or "").strip()
    land = str(data.get("land") or "here").strip()
    fields_in = data.get("fields")
    fields: dict[str, str] = {}
    if isinstance(fields_in, dict):
        for k, v in fields_in.items():
            key = str(k or "").strip().lower()
            if not re.match(r"^[a-z][a-z0-9_-]*$", key):
                continue
            fields[key] = str(v or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    else:
        for k, v in data.items():
            ks = str(k or "")
            if ks.startswith("f_"):
                key = ks[2:].strip().lower()
                if re.match(r"^[a-z][a-z0-9_-]*$", key):
                    fields[key] = str(v or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not any(fields.values()):
        return 400, None, "need a line"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        standing = resolve_vault_page(pocket_raw)
        if standing is None:
            return 400, None, "not a vault page"
        folder = insert_land_folder(standing, land)
        if folder is None:
            return 400, None, "bad landing"
        standing_meta, src = insert_standing_src(standing)
        recipe = insert_parse_recipe(src)
        title = insert_title_from(fields, recipe.get("yaml_names"))
        if not title:
            return 400, None, "need a line"
        dest = insert_dest(folder, title)
        if dest is None:
            return 409, None, "could not name the page"
        now = datetime.now()
        crate = mint_crate_id()
        env = (
            zone_page_env(standing)
            or zone_shell_env(standing)
            or zone_page_env(folder)
            or zone_shell_env(folder)
            or ""
        )
        lines = [
            "---",
            "crate: " + crate,
            "title: " + yaml_scalar(title),
        ]
        if env:
            lines.append("environment: " + yaml_scalar(env))
        skip_yaml = {"title", "crate", "environment"}
        for name in recipe.get("yaml_names") or []:
            if name in skip_yaml:
                continue
            extra = str(fields.get(name) or "").strip()
            if extra:
                lines.append(name + ": " + yaml_scalar(extra))
        lines.append("---")
        lines.append("")
        face_bits = insert_face_parts(recipe, fields, title)
        # Keep injector clay tight: one newline between parts (not a blank line
        # per field). Blank line only after the heading so md still breathes.
        if face_bits and face_bits[0].startswith("# "):
            lines.append(face_bits[0])
            rest = face_bits[1:]
            if rest:
                lines.append("")
                lines.append("\n".join(rest))
        else:
            lines.append("\n".join(face_bits))
        lines.append("")
        with LBR_LOCK:
            if dest.exists():
                return 409, None, "already a page by that name"
            try:
                write_note(dest, "\n".join(lines))
            except OSError:
                return 500, None, "could not write"
        insert_file_cabinets(dest, standing, standing_meta, now, fields, recipe)
        rel = dest.relative_to(active_vault()).as_posix()
        return 200, {
            "file": dest.name,
            "href": page_href(rel),
            "pocket": pocket_key(dest),
            "crate": crate,
            "title": title,
        }, ""


def page_card_shelf(rel: str, meta: dict | None) -> str:
    """Reverse-edged lorecards for this page's crate â€” same query as the cards cabinet shelf."""
    meta = meta or {}
    # Prefer the open page path. Shell dress keeps the bay's own crate in meta["crate"].
    crates: list[str] = []
    crate = ""
    if rel:
        try:
            target = active_vault() / rel
            if target.exists():
                crates = page_lore_crates(target)
                crate = crates[0] if crates else ""
        except Exception:
            crates = []
            crate = ""
    if not crates:
        crate = norm_crate(str(meta.get("crate") or ""))
        if crate:
            crates = [crate]
    bits: list[str] = []
    seen: set[str] = set()
    if crates:
        for mouth in ("librarian", "detective", "charlie", "tps"):
            for want in crates:
                for card in lore_cards_for(mouth, want):
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
                        cand = Path(inbox) / fname
                        if cand.is_file():
                            p = cand
                    if p is None and own:
                        p = find_file_by_crate(own)
                    painted = paint_lorecard_shelf_item(p) if p is not None else ""
                    if painted:
                        bits.append(painted)
    cls = "card-shelf yard-shelf"
    if not bits:
        cls += " is-empty"
    crate_attr = f' data-crate="{html.escape(crate, True)}"' if crate else ""
    return f'<div class="{cls}" data-shelf="lore"{crate_attr}>' + "".join(bits) + "</div>"


def tag_look_block(rel: str, meta: dict | None) -> str:
    """Look-through for a tag page: Charlie/tagbay body for this word."""
    meta = meta or {}
    kind = str(meta.get("kind") or "").strip().lower()
    word = str(meta.get("tag") or "").strip()
    if not word:
        here = (rel or "").replace("\\", "/").strip("/")
        if here.lower().endswith(".md") and kind == "tag":
            word = Path(here).stem
    word = tag_slug(word)
    if not word:
        if active_host() == TAGS_HOST_SLUG:
            return "<div class=\"taglook taglook-empty\">open a word to see what touches it</div>"
        return ""
    if kind and kind not in ("tag", "hash"):
        return ""
    role = kind if kind in ("tag", "hash") else "tag"
    try:
        here_pocket = ""
        if rel:
            try:
                here_pocket = pocket_key(active_vault() / rel)
            except Exception:
                here_pocket = ""
        inner = _tagbay_body(word, here=here_pocket, role=role, compact=True)
    except Exception:
        inner = ""
    if not inner:
        return "<div class=\"taglook taglook-empty\">nothing edged to this word yet</div>"
    return "<div class=\"taglook\">" + inner + "</div>"


def tag_page(slug: str) -> bytes:
    """Legacy ?t= entry — redirect into the tags pocket word page."""
    dest = tag_page_href(slug)
    esc = html.escape(dest, True)
    return (
        f"<!doctype html><meta http-equiv=\"refresh\" content=\"0;url={esc}\">"
        f"<a href=\"{esc}\">go.tags</a>"
    ).encode("utf-8")



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
    s = CHIP_CODE_RE.sub(lambda m: hold(chip_code_chip(m.group(1))), s)
    s = html.escape(s)
    return re.sub(r"\x00@(\d+)@\x00", lambda m: held[int(m.group(1))], s)


def fm_row(k: str, v: str) -> str:
    if k.lower() in ("tags", "tag"):
        chips = "".join(tag_chip(t) for t in split_tags(str(v)))
        dd = chips or html.escape(str(v))
    else:
        dd = fm_inline(str(v))
    return f"<div><dt>{html.escape(k)}</dt><dd>{dd}</dd></div>"



def catalog_field_values(folder: Path, rel: str | None, mouth: str, label: str) -> list[str]:
    """Values for one catalog label on this page's librarian/detective/tps shelf."""
    mouth = mouth_canon(mouth or "librarian")
    if mouth == "tps":
        want = (label or "").strip().lower()
        if not want:
            return []
        stamps = tps_page_stamps(folder, rel)
        out: list[str] = []
        if want in ("title", "titles"):
            for s in stamps:
                v = str(s.get("title") or "").strip()
                if v and v not in out:
                    out.append(v)
            return out
        if want in ("when", "date", "dates"):
            for s in stamps:
                v = str(s.get("when") or "").strip()
                if v and v not in out:
                    out.append(v)
            return out
        # {{tps:created}} → when(s) for stamps with that title
        for s in stamps:
            if str(s.get("title") or "").strip().lower() != want:
                continue
            v = str(s.get("when") or "").strip()
            if v and v not in out:
                out.append(v)
        return out
    if mouth not in ("librarian", "detective"):
        return []
    want = (label or "").strip().lower()
    if not want:
        return []
    target = slot_page(folder, rel)
    dest = shelf_file(mouth, target)
    if dest is None:
        return []
    house = CATALOG[mouth]["house"]
    obj = catalog_read(dest, pocket_key(target), house)
    out = []
    for f in obj.get("fields") or []:
        if not isinstance(f, dict):
            continue
        lab = str(f.get("label") or "").strip()
        if lab.lower() != want:
            continue
        for value in chip_values(f):
            v = str(value or "").strip()
            if v and v not in out:
                out.append(v)
    return out


def catalog_field_token(folder: Path, rel: str | None, mouth: str, label: str) -> str:
    """Print one cabinet field into clay. Missing → blank. Multi → comma-joined."""
    vals = catalog_field_values(folder, rel, mouth, label)
    if not vals:
        return ""
    if len(vals) == 1:
        return fm_inline(vals[0])
    return fm_inline(", ".join(vals))



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
    p = shell_path(folder)
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="replace")
    return parse_fm(text)


def nearest_index_folder(page: Path | None) -> Path | None:
    """Closest folder that has `_shell.md` (or leftover `_index.md`), walking up."""
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
        if has_shell(cur):
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
    """Closest `_shell.md` title walking up from this folder (the shell, not vault root)."""
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


def kid_order_num(p: Path) -> float:
    """Frontmatter order: for notes (and folder shells). Missing → +inf (after numbered)."""
    meta: dict = {}
    if p.is_dir():
        shell = shell_path(p)
        if shell.is_file():
            meta = read_md_meta(shell)
    elif p.suffix.lower() == ".md":
        meta = read_md_meta(p)
    raw = meta.get("order", meta.get("sort", ""))
    if raw is None or str(raw).strip() == "":
        return float("inf")
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return float("inf")


def kid_sort_key(p: Path) -> tuple:
    """Folders first; within group, frontmatter order: then title/name."""
    ord_n = kid_order_num(p)
    if p.is_dir():
        return (0, ord_n, p.name.lower(), p.name.lower())
    if p.suffix.lower() in {".md", ".chip"} or is_text_guest_path(p) or is_html_guest_path(p):
        return (1, ord_n, md_list_label(p).lower(), p.name.lower())
    return (1, ord_n, p.stem.lower(), p.name.lower())


def visible_kids(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    kids = []
    for p in folder.iterdir():
        if p.name in SKIP or stash_name(p.name):
            continue
        if p.name.lower() in {n.lower() for n in RESERVED_NOTES}:
            continue
        if p.is_file() and p.name.lower() in MACHINE_FILES:
            continue
        if is_lobby() and p.name.lower() in {START_NAME, RECENT_NAME, ROAM_NAME, "readme.md"}:
            continue
        if path_list_hidden(p):
            continue
        if (
            p.is_dir()
            or p.suffix.lower() in {".md", ".canvas", ".chip"}
            or is_text_guest_path(p)
            or is_html_guest_path(p)
        ):
            kids.append(p)
    kids.sort(key=kid_sort_key)
    return kids


def door_slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s if s and ENV_NAME.fullmatch(s) else ""


def _connected_lobby_door(
    host: Host,
    here_n: str,
    pins: dict[str, int],
    icons: dict[str, str],
    is_chips: bool,
    i: int,
    *,
    scheme: str,
) -> dict:
    """Start {{doors}} card for a yaml-connected host (roam.* or exterior go.*)."""
    slug = host.name
    scheme_n = (scheme or "go").strip().lower() or "go"
    n = 0
    if host.root.is_dir():
        n = sum(
            1
            for p in walk_host_notes(host.root)
            if p.name.lower() not in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}
        )
    classes = ["world", f"door-n{i}", f"door-{scheme_n}"]
    if is_chips:
        classes.append("door-chip")
    ds = door_slug(slug)
    if slug:
        classes.append(f"door-{ds or slug}")
    if here_n == slug or here_n.startswith(slug + "/"):
        classes.append("on")
    pin_rank = pins.get(slug)
    if pin_rank is not None:
        classes.append("door-pinned")
    # Same door face fields as go.*: shell frontmatter (_shell.md) via load_index.
    # host.title / environment still come from _hosts.yaml for the roam hook.
    meta: dict = {}
    loaded = load_index(host.root)
    if loaded:
        meta = loaded[0] or {}
    label = str(meta.get("title") or host.title or slug).strip() or slug
    section = str(meta.get("section") or meta.get("neighborhood") or "").strip()
    deck = ""
    if not is_chips:
        for key in ("deck", "blurb", "lede", "description", "summary"):
            raw = str(meta.get(key) or "").strip()
            if raw:
                deck = raw
                break
        if not deck:
            deck = scheme_n + "." + slug
    bits = [f"<strong>{html.escape(label)}</strong>"]
    if deck:
        bits.append(f"<span class='door-deck'>{html.escape(deck)}</span>")
        classes.append("has-deck")
    if not is_chips:
        bits.append(f"<span class='note-details'>{n}</span>")
    yaml_icon = icons.get(slug, "")
    face = door_face_html(label, meta, yaml_icon)
    classes.append("has-face")
    hue = door_hue(meta, label)
    href = "/?h=" + quote(slug)
    card = (
        f'<a class="{html.escape(" ".join(classes), True)}" '
        f'href="{html.escape(href, True)}" '
        f'data-door="{html.escape(slug, True)}"'
        + (f' data-section="{html.escape(section, True)}"' if section else "")
        + f' style="--door-hue:{html.escape(hue, True)}"'
        + ">"
        + face
        + "<span class='door-copy'>"
        + "".join(bits)
        + "</span>"
        + "</a>"
    )
    return {
        "card": card,
        "section": section,
        "pin": pin_rank,
        "name": slug.lower(),
        "label": label.lower(),
    }


def _roam_lobby_door(
    host: Host,
    here_n: str,
    pins: dict[str, int],
    icons: dict[str, str],
    is_chips: bool,
    i: int,
) -> dict:
    return _connected_lobby_door(
        host, here_n, pins, icons, is_chips, i, scheme="roam"
    )


def door_cards(folder: Path, here: str = "", mode: str = "cards", scope: str = "") -> str:
    """Folder doors. Title/deck/section from each child shell front matter.
    Lobby pins float via _hosts.yaml pin:. section: groups doors into neighborhoods.
    Lobby show: false in _hosts.yaml hides a host from go/roam {{doors}} only.
    mode: "cards" (fat lobby cards) or "chips" (thin host-nav door chips).
    scope: go (native ~hosts folders plus exterior kind: go + source:), roam, all.
    On the Go lobby, {{doors}} is go-only. Roam lobby uses {{doors:roam}}.
    kind: go + source: still counts as a go door (not roam).
    """
    mode_n = (mode or "cards").strip().lower()
    if mode_n not in ("cards", "chips"):
        mode_n = "cards"
    is_chips = mode_n == "chips"
    scope_n = (scope or "").strip().lower()
    if scope_n not in ("go", "roam", "all"):
        scope_n = "go" if is_lobby() else "all"
    include_go = (not is_lobby()) or scope_n in ("go", "all")
    include_roam = is_lobby() and scope_n in ("roam", "all")
    dirs = [w for w in visible_kids(folder) if w.is_dir()] if include_go else []
    pins = host_pin_map() if is_lobby() else {}
    show_map = host_show_map() if is_lobby() else {}
    icons = host_icon_map() if is_lobby() else {}
    folder_alias = _hosts_folder_alias_slugs() if is_lobby() else {}
    here_n = (here or "").replace("\\", "/").strip("/").lower()

    doors: list[dict] = []
    for i, w in enumerate(dirs, start=1):

        if is_lobby():
            own = host_slug(w.name) or ""
            alias = folder_alias.get(w.name.lower(), "")
            check = [s for s in (own, alias) if s]
            if any(show_map.get(s, True) is False for s in check):
                continue
            roam_slugs = {
                h.name for h in discover_hosts().values() if h.kind == "roam"
            }
            if own in roam_slugs or (alias and alias in roam_slugs):
                continue
        n = sum(
            1
            for _ in walk_host_notes(w)
            if _.name.lower() not in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}
        )
        slug = door_slug(w.name)
        classes = ["world", f"door-n{i}"]
        if is_chips:
            classes.append("door-chip")
        if slug:
            classes.append(f"door-{slug}")
        try:
            door_rel = (
                w.relative_to(active_vault())
                .as_posix()
                .replace("\\", "/")
                .strip("/")
                .lower()
            )
        except ValueError:
            door_rel = w.name.lower()
        if here_n and (here_n == door_rel or here_n.startswith(door_rel + "/")):
            classes.append("on")
        pin_slug = host_slug(w.name) or slug
        pin_rank = None
        if pin_slug and pin_slug in pins:
            classes.append("door-pinned")
            pin_rank = pins[pin_slug]
        meta: dict = {}
        loaded = load_index(w)
        if loaded:
            meta = loaded[0] or {}
        label = str(meta.get("title") or "").strip() or w.name
        section = str(meta.get("section") or meta.get("neighborhood") or "").strip()
        deck = ""
        if not is_chips:
            for key in ("deck", "blurb", "lede", "description", "summary"):
                raw = str(meta.get(key) or "").strip()
                if raw:
                    deck = raw
                    break
        bits = [f"<strong>{html.escape(label)}</strong>"]
        if deck:
            bits.append(f"<span class='door-deck'>{html.escape(deck)}</span>")
            classes.append("has-deck")
        if not is_chips:
            bits.append(f"<span class='note-details'>{n}</span>")
        yaml_icon = icons.get(pin_slug, "") if pin_slug else ""
        face = door_face_html(label, meta, yaml_icon)
        classes.append("has-face")
        cover_meta = meta
        if not cover_name(meta):
            papered = load_paper(w)
            if papered and cover_name(papered[0] or {}):
                cover_meta = papered[0] or {}
        found = media_src(cover_name(cover_meta)) if cover_name(cover_meta) else None
        art = ""
        if found:
            src, _fname = found
            classes.append("has-cover")
            art = (
                f'<img class="door-cover" src="{html.escape(src, True)}" alt="" '
                f'aria-hidden="true">'
            )
        hue = door_hue(meta, label)
        card = (
            f'<a class="{html.escape(" ".join(classes), True)}" '
            f'href="{html.escape(kid_href(w), True)}" '
            f'data-door="{html.escape(w.name, True)}"'
            + (f' data-section="{html.escape(section, True)}"' if section else "")
            + f' style="--door-hue:{html.escape(hue, True)}"'
            + ">"
            + art
            + ("<span class='door-scrim'></span>" if art else "")
            + face
            + "<span class='door-copy'>"
            + "".join(bits)
            + "</span>"
            + "</a>"
        )
        doors.append(
            {
                "card": card,
                "section": section,
                "pin": pin_rank,
                "name": w.name.lower(),
                "label": label.lower(),
            }
        )

    if include_go and is_lobby():
        seen_go = {d["name"] for d in doors}
        for slug, host in sorted(discover_hosts().items(), key=lambda kv: kv[0].lower()):
            if (host.kind or "go") == "roam":
                continue
            if not host_is_exterior(host):
                continue
            if not host_is_shown(slug):
                continue
            if slug.lower() in seen_go:
                continue
            doors.append(
                _connected_lobby_door(
                    host, here_n, pins, icons, is_chips, len(doors) + 1, scheme="go"
                )
            )
            seen_go.add(slug.lower())

    if include_roam:
        roam_map = {h.name: h for h in discover_hosts().values() if h.kind == "roam"}
        for slug, host in sorted(roam_map.items()):
            if not host_is_shown(slug):
                continue
            doors.append(
                _roam_lobby_door(host, here_n, pins, icons, is_chips, len(doors) + 1)
            )

    if not doors:
        if scope_n == "roam":
            return "<p>no roam libraries.</p>"
        return "<p>no folders here.</p>"

    def door_key(d: dict):
        # pinned first within its section; then name
        pinned = 0 if d["pin"] is not None else 1
        pin_n = d["pin"] if d["pin"] is not None else 0
        return (pinned, pin_n, d["name"])

    wrap_cls = "worlds is-chips" if is_chips else "worlds"
    any_section = any(d["section"] for d in doors)
    if not any_section:
        doors.sort(key=door_key)
        return f"<div class='{wrap_cls}'>" + "".join(d["card"] for d in doors) + "</div>"

    # group by section; unlabeled last
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for d in doors:
        key = d["section"] or ""
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(d)
    # stable: named sections alpha, empty last
    named = sorted([k for k in order if k], key=lambda s: s.lower())
    if "" in groups:
        named.append("")
    parts: list[str] = [f'<div class="{wrap_cls} is-sectioned">']
    for sec in named:
        items = sorted(groups[sec], key=door_key)
        slug = re.sub(r"[^a-z0-9]+", "-", sec.lower()).strip("-") if sec else "loose"
        if sec:
            parts.append(
                f'<section class="door-section" data-section="{html.escape(sec, True)}">'
                f'<h2 class="door-section-head">{html.escape(sec)}</h2>'
                f'<div class="door-section-doors">'
                + "".join(d["card"] for d in items)
                + "</div></section>"
            )
        else:
            parts.append(
                f'<section class="door-section is-loose" data-section="loose">'
                f'<div class="door-section-doors">'
                + "".join(d["card"] for d in items)
                + "</div></section>"
            )
    parts.append("</div>")
    return "".join(parts)



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


def _tag_use_badge(stem: str, tally: dict[str, dict[str, int]] | None) -> str:
    if not tally:
        return ""
    slug = tag_slug(stem)
    if not slug:
        return ""
    row = tally.get(slug) or {}
    n = int(row.get("n") or 0)
    if n < 1:
        return ""
    bits: list[str] = []
    for key, lab in (
        ("pin", "pin"),
        ("hash", "hash"),
        ("from", "out"),
        ("to", "in"),
        ("rel", "rel"),
    ):
        k = int(row.get(key) or 0)
        if k:
            bits.append(f"{k} {lab}")
    tip = " · ".join(bits) if bits else f"{n} uses"
    return (
        f'<span class="tag-n" title="{html.escape(tip, True)}">'
        f"{n}</span>"
    )


def navbar_links(folder: Path, here: str = "") -> str:
    """Lightweight auto folder nav for the current hall — not door cards."""
    here_n = (here or "").replace("\\", "/").strip("/").lower()
    bits: list[str] = ['<nav class="pg-navbar">']
    for p in visible_kids(folder):
        if not p.is_dir():
            continue
        try:
            rel = p.relative_to(active_vault()).as_posix()
        except ValueError:
            rel = p.name
        cls = (
            ' class="on"'
            if here_n and rel.replace("\\", "/").strip("/").lower() == here_n
            else ""
        )
        bits.append(
            '<a'
            + cls
            + ' href="'
            + html.escape(kid_href(p), True)
            + '">'
            + html.escape(p.name)
            + "</a>"
        )
    bits.append("</nav>")
    if len(bits) == 2:
        return '<nav class="pg-navbar"></nav>'
    return "".join(bits)



def navbar_files(folder: Path, here: str = "") -> str:
    """Same strip as navbar_links, but lists files in this hall — not folders."""
    here_n = (here or "").replace("\\", "/").strip("/").lower()
    bits: list[str] = ['<nav class="pg-navbar">']
    for p in visible_kids(folder):
        if p.is_dir():
            continue
        try:
            rel = p.relative_to(active_vault()).as_posix()
        except ValueError:
            rel = p.name
        cls = (
            ' class="on"'
            if here_n and rel.replace("\\", "/").strip("/").lower() == here_n
            else ""
        )
        label = md_list_label(p) if p.suffix.lower() in {".md", ".canvas", ".chip"} else p.name
        bits.append(
            '<a'
            + cls
            + ' href="'
            + html.escape(kid_href(p), True)
            + '">'
            + html.escape(label)
            + "</a>"
        )
    bits.append("</nav>")
    if len(bits) == 2:
        return '<nav class="pg-navbar"></nav>'
    return "".join(bits)

def file_list(
    folder: Path,
    kind: str = "files",
    extra: str = "",
    here: str = "",
    tally: dict[str, dict[str, int]] | None = None,
    sort: str = "",  # FILES_DATE_SORT: "" | "date" (mtime newest first)
) -> str:
    items = []
    face_up = extra != "spines"
    here_n = (here or "").replace("\\", "/").strip("/").lower()
    kids = list(visible_kids(folder))
    sort_n = (sort or "").strip().lower()
    if sort_n in ("date", "mtime", "newest", "new"):  # FILES_DATE_SORT
        def _mtime(p: Path) -> float:
            try:
                return p.stat().st_mtime
            except OSError:
                return 0.0
        # Newest first; folders still lead within the same kind filter.
        kids.sort(key=lambda p: (0 if p.is_dir() else 1, -_mtime(p), p.name.lower()))
    for p in kids:
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
            label = md_list_label(p)
            hue = hue_name(meta)
            if hue:
                classes.append(f"hue-{hue}")
            if p.suffix.lower() == ".chip":
                classes.append("is-chip-guest")
            elif is_html_guest_path(p):
                classes.append("is-html-guest")
            elif is_text_guest_path(p):
                classes.append("is-text-guest")
            if face_up and not is_text_guest_path(p) and not is_html_guest_path(p):
                art = cover_art(meta, label)
                if art:
                    classes.append("has-cover")
                fit = str(meta.get("cover_fit") or meta.get("jacket_fit") or "").strip().lower()
                if fit in ("landscape", "wide", "horizontal"):
                    classes.append("cover-landscape")
        cls_attr = f' class="{html.escape(" ".join(classes), True)}"' if classes else ""
        badge = "" if p.is_dir() else _tag_use_badge(p.stem, tally)
        items.append(
            f'<li><a{cls_attr} href="{html.escape(kid_href(p), True)}">'
            f"{art}"
            f'<span class="name">{html.escape(label)}{mark}</span>'
            f"{badge}</a></li>"
        )
    if not items:
        if kind == "files":
            return "<p>no notes here.</p>"
        if kind == "dirs":
            return "<p>no folders here.</p>"
        return "<p>empty.</p>"
    ul = "dir" + (f" {extra}" if extra else "")
    return f"<ul class='{html.escape(ul, True)}'>" + "".join(items) + "</ul>"


DIRTREE_DEPTH = 3


def _dirtree_rel(p: Path) -> str:
    try:
        rel = p.relative_to(active_vault()).as_posix()
    except ValueError:
        rel = p.name
    rel = rel.replace("\\", "/").strip("/").lower()
    if p.is_file() and rel.endswith(".md"):
        rel = rel[:-3]
    elif p.is_file() and rel.endswith(".chip"):
        rel = rel[:-5]
    return rel


def _dirtree_here(here: str) -> str:
    n = (here or "").replace("\\", "/").strip("/").lower()
    if n.endswith(".md"):
        n = n[:-3]
    elif n.endswith(".chip"):
        n = n[:-5]
    return n


def _dirtree_on(p: Path, here_n: str) -> bool:
    if not here_n:
        return False
    rel = _dirtree_rel(p)
    if not rel:
        return False
    if p.is_dir():
        return here_n == rel or here_n.startswith(rel + "/")
    return here_n == rel


def dir_tree_flat(folder: Path, here_n: str) -> str:
    """All notes under this folder as one flat list (no nested halls)."""
    hide = {n.lower() for n in RESERVED_NOTES}
    items: list[str] = []
    if not folder.is_dir():
        return ""
    for p in sorted(folder.rglob("*"), key=lambda x: x.as_posix().lower()):
        if not p.is_file() or p.suffix.lower() not in {".md", ".chip"}:
            continue
        parts = p.relative_to(folder).parts
        if any(part in SKIP or stash_name(part) for part in parts):
            continue
        if p.name.lower() in hide:
            continue
        classes: list[str] = []
        if _dirtree_on(p, here_n):
            classes.append("on")
        label = md_list_label(p)
        cls_attr = f' class="{html.escape(" ".join(classes), True)}"' if classes else ""
        items.append(
            f'<li><a{cls_attr} href="{html.escape(kid_href(p), True)}">'
            f'<span class="name">{html.escape(label)}</span></a></li>'
        )
    if not items:
        return ""
    return "<ul class='dir dirtree is-flat'>" + "".join(items) + "</ul>"


def dir_tree_list(
    folder: Path, here_n: str, depth: int, max_depth: int, mode: str = "all"
) -> str:
    """Nested {{dir}} from this folder. depth 1 is the first listed generation."""
    mode = (mode or "all").strip().lower()
    if mode not in ("all", "folders", "files", "flat"):
        mode = "all"
    kids = visible_kids(folder)
    if mode == "folders":
        kids = [p for p in kids if p.is_dir()]
    elif mode == "files":
        kids = [p for p in kids if p.is_file()]
    if not kids:
        return ""
    items: list[str] = []
    for p in kids:
        mark = "/" if p.is_dir() else ""
        classes: list[str] = []
        if _dirtree_on(p, here_n):
            classes.append("on")
        if p.is_dir():
            classes.append("is-dir")
            label = crumb_back_name(p)
        else:
            label = md_list_label(p)
        cls_attr = f' class="{html.escape(" ".join(classes), True)}"' if classes else ""
        head = (
            f'<a{cls_attr} href="{html.escape(kid_href(p), True)}">'
            f'<span class="name">{html.escape(label)}{mark}</span></a>'
        )
        nested = ""
        if mode != "files" and p.is_dir() and depth < max_depth:
            nested = dir_tree_list(p, here_n, depth + 1, max_depth, mode=mode)
        if nested:
            items.append(f"<li>{head}{nested}</li>")
        else:
            items.append(f"<li>{head}</li>")
    if not items:
        return ""
    ul = "dir dirtree" if depth == 1 else "dir"
    if mode == "folders" and depth == 1:
        ul += " is-folders"
    elif mode == "files" and depth == 1:
        ul += " is-files"
    return f"<ul class='{html.escape(ul, True)}'>" + "".join(items) + "</ul>"


def dir_tree(
    folder: Path, here: str = "", depth: int = DIRTREE_DEPTH, mode: str = "all"
) -> str:
    """Notes and subfolders from this page's folder, nested up to `depth` levels.

    mode: all | folders | files | flat
    """
    mode = (mode or "all").strip().lower()
    if mode not in ("all", "folders", "files", "flat"):
        mode = "all"
    if mode == "flat":
        tree = dir_tree_flat(folder, _dirtree_here(here))
        if not tree:
            return "<p>empty.</p>"
        return tree
    try:
        n = int(depth)
    except (TypeError, ValueError):
        n = DIRTREE_DEPTH
    if n < 1:
        n = 1
    if n > 8:
        n = 8
    tree = dir_tree_list(folder, _dirtree_here(here), 1, n, mode=mode)
    if not tree:
        return "<p>empty.</p>"
    return tree


TREE_DEPTH = 8


def file_tree_list(folder: Path, here_n: str, depth: int, max_depth: int) -> str:
    """Nested halls from a fixed root. Folders twist open; the open path stays open."""
    kids = visible_kids(folder)
    if not kids:
        return ""
    items: list[str] = []
    for p in kids:
        mark = "/" if p.is_dir() else ""
        classes: list[str] = []
        on = _dirtree_on(p, here_n)
        if on:
            classes.append("on")
        if p.is_dir():
            classes.append("is-dir")
            label = crumb_back_name(p)
        else:
            label = md_list_label(p)
        cls_attr = f' class="{html.escape(" ".join(classes), True)}"' if classes else ""
        head = (
            f'<a{cls_attr} href="{html.escape(kid_href(p), True)}">'
            f'<span class="name">{html.escape(label)}{mark}</span></a>'
        )
        nested = ""
        if p.is_dir() and depth < max_depth:
            nested = file_tree_list(p, here_n, depth + 1, max_depth)
        li_cls = f' class="{html.escape(" ".join(classes), True)}"' if classes else ""
        if nested:
            opened = " open" if on else ""
            items.append(
                f"<li{li_cls}><details{opened}><summary>{head}</summary>"
                f"{nested}</details></li>"
            )
        else:
            items.append(f"<li{li_cls}>{head}</li>")
    if not items:
        return ""
    ul = "dir tree" if depth == 1 else "dir"
    return f"<ul class='{html.escape(ul, True)}'>" + "".join(items) + "</ul>"


def file_tree(folder: Path, here: str = "", depth: int = TREE_DEPTH) -> str:
    """File tree rooted at this folder (the dress shell when the token is on `_shell.md`)."""
    try:
        n = int(depth)
    except (TypeError, ValueError):
        n = TREE_DEPTH
    if n < 1:
        n = 1
    if n > 12:
        n = 12
    tree = file_tree_list(folder, _dirtree_here(here), 1, n)
    if not tree:
        return "<p>empty.</p>"
    return tree


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
        for p in walk_host_notes(root):
            if norm_crate(file_crate(p)) == crate:
                return p
    return None


def crates_search(q: str, limit: int = 40, mode: str = "all") -> tuple[int, dict | None, str]:
    """BIOS Crates finder: match crate id / title / path / body across host notes."""
    q = str(q or "").strip()
    mode = str(mode or "all").strip().lower()
    if mode not in ("all", "title", "path", "body", "crate"):
        mode = "all"
    try:
        limit = int(limit or 40)
    except (TypeError, ValueError):
        limit = 40
    limit = max(1, min(limit, 200))
    if not q:
        return 200, {"q": "", "mode": mode, "items": []}, ""

    q_low = q.lower()
    # Hex mode only when the query (minus optional crate. prefix) is pure hex --
    # do not strip letters or "aidm"/"Andy" become "AD" and match every crate.
    hex_raw = q.strip()
    if hex_raw.lower().startswith("crate."):
        hex_raw = hex_raw[6:]
    hex_raw = hex_raw.strip()
    looks_hex = bool(hex_raw) and re.fullmatch(r"[A-Fa-f0-9]+", hex_raw) is not None
    hex_only = hex_raw.upper() if looks_hex else ""
    want_full = norm_crate(q)
    use_hex = mode in ("all", "crate")

    roots: list[tuple[str, Path]] = []
    for name, host in discover_hosts().items():
        if host.root.is_dir():
            roots.append((name, host.root))

    scored: list[tuple[int, str, dict]] = []
    seen: set[str] = set()
    body_max = 200 * 1024

    def note_body(p: Path) -> str:
        try:
            if p.stat().st_size > body_max:
                return ""
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        _meta, body = parse_fm(text)
        return str(body or "")

    def consider(p: Path) -> None:
        crate = norm_crate(file_crate(p))
        if not crate:
            return
        if crate in seen:
            return
        door = door_for_path(p)
        title = str((door or {}).get("title") or md_list_label(p) or "").strip()
        pocket = str((door or {}).get("pocket") or "").strip()
        href = str((door or {}).get("href") or "").strip()
        try:
            path_s = p.as_posix()
        except Exception:
            path_s = str(p)
        crate_hex = crate[6:] if crate.lower().startswith("crate.") else crate
        crate_hex = crate_hex.upper()

        score = None
        if use_hex and want_full and crate == want_full:
            score = 0
        elif use_hex and looks_hex and hex_only:
            if crate_hex == hex_only:
                score = 0
            elif crate_hex.startswith(hex_only):
                score = 1
            elif hex_only in crate_hex:
                score = 2
        if score is None:
            if mode == "title":
                if q_low in title.lower():
                    score = 4
                else:
                    return
            elif mode == "path":
                if (
                    q_low in pocket.lower()
                    or q_low in path_s.lower()
                    or q_low in p.name.lower()
                ):
                    score = 5
                else:
                    return
            elif mode == "crate":
                if q_low in crate.lower() or (hex_only and hex_only in crate_hex):
                    score = 3
                else:
                    return
            elif mode == "body":
                body = note_body(p)
                if q_low in body.lower():
                    score = 7
                else:
                    return
            else:
                hay = " ".join(
                    [
                        crate.lower(),
                        title.lower(),
                        pocket.lower(),
                        path_s.lower(),
                        p.name.lower(),
                    ]
                )
                if q_low in crate.lower():
                    score = 3
                elif q_low in title.lower():
                    score = 4
                elif (
                    q_low in pocket.lower()
                    or q_low in path_s.lower()
                    or q_low in p.name.lower()
                ):
                    score = 5
                elif q_low in hay:
                    score = 6
                else:
                    return

        seen.add(crate)
        item = {
            "crate": crate,
            "title": title or p.stem,
            "pocket": pocket,
            "href": href,
            "path": path_s,
        }
        scored.append((score, title.lower(), item))

    start = HOSTS_ROOT / START_NAME
    if start.is_file():
        consider(start)
    for _name, root in roots:
        if not root.is_dir():
            continue
        for p in walk_host_notes(root):
            consider(p)

    scored.sort(key=lambda t: (t[0], t[1], t[2].get("crate") or ""))
    items = [t[2] for t in scored[:limit]]
    return 200, {"q": q, "mode": mode, "items": items}, ""


def paint_face(path: Path, meta: dict | None = None, src: str | None = None) -> str:
    if meta is None or src is None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        meta, src = parse_fm(text)
    meta = dict(meta or {})
    meta["maker"] = card_maker(meta)
    inner = md_lite(src)
    try:
        rel = path.relative_to(active_vault()).as_posix()
    except ValueError:
        rel = path.name
    room = path.parent
    if META_SLOT_RE.search(inner):
        def _meta_slot(m: re.Match[str]) -> str:
            return meta_slot_html(room, rel, m.group(1))

        inner = META_SLOT_RE.sub(_meta_slot, inner)
    if CABINET_FIELD_RE.search(inner):
        def _cabinet_field(m: re.Match[str]) -> str:
            return catalog_field_token(room, rel, m.group(1), m.group(2))

        inner = CABINET_FIELD_RE.sub(_cabinet_field, inner)
    if CHIP_FIELD_RE.search(inner):
        def _chip_field(m: re.Match[str]) -> str:
            return catalog_chip_token(room, rel, m.group(1), m.group(2))

        inner = CHIP_FIELD_RE.sub(_chip_field, inner)
    inner = stamp_lorecard_strip(fill_fields(inner, meta), meta)
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
    """The label a card sorts under â€” class first, then untitled."""
    meta = meta or {}
    klass = str(meta.get("class") or "").strip()
    if klass:
        return klass
    if is_card_note(meta):
        return "unfiled"
    return ""


def face_list(folder: Path) -> str:
    """Print each note as a face. Hunt slips wear search-style blotter cards."""
    rows: list[tuple[str, str, str, Path, dict, str]] = []
    hunt_hits: list[dict] = []
    hide = {n.lower() for n in RESERVED_NOTES}
    for p in visible_kids(folder):
        if not p.is_file() or p.suffix.lower() not in {".md", ".chip"}:
            continue
        if p.name.lower() in hide:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = parse_fm(text)
        kind = str(meta.get("kind") or "").strip().lower()
        if is_blotter_note(meta):
            rec = hunt_record(p)
            if rec:
                hunt_hits.append(rec)
            continue
        painted = paint_face(p, meta, body)
        if not painted:
            continue
        deck = face_deck_key(meta)
        title = str(meta.get("title") or p.stem).strip() or p.stem
        if p.suffix.lower() == ".chip":
            title = str(chip_peek(p).get("name") or "").strip() or title
        rows.append((deck.lower(), title.lower(), p.name.lower(), p, meta, painted))
    chunks: list[str] = []
    if hunt_hits:
        hunt_hits.sort(key=lambda h: int(h.get("at") or 0), reverse=True)
        slips = [
            paint_hunt_slip(hit, n=(i % 3) + 1)
            for i, hit in enumerate(hunt_hits)
        ]
        chunks.append('<div class="hunt-faces">' + "".join(slips) + "</div>")
    if rows:
        rows.sort(key=lambda r: (r[0] == "", r[0], r[1], r[2]))
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
    if not chunks:
        return "<p>no notes here.</p>"
    return '<div class="faces">' + "".join(chunks) + "</div>"



TRAY_MOUTHS = ("librarian", "detective", "charlie", "tps")


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
    """Quiet index of sibling cards â€” class + title only, not mini pages."""
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
            f'<span class="tray-index-class">{html.escape(klass or "Â·")}</span>'
            f'<span class="tray-index-title">{html.escape(title)}</span>'
            f"</a>"
        )
    bits.append("</nav>")
    return "".join(bits)


def paint_tray_hinterland(meta: dict | None, current: Path | None = None) -> str:
    """Connected refs on the open tray stage: pages row, then card minis row."""
    meta = meta or {}
    cur_crate = norm_crate(str(meta.get("crate") or ""))
    crates = lore_edge_crates(meta)
    # Cabinet attach stamps the open page onto the *other* card; include reverse hits.
    for c in lore_reverse_edge_crates(cur_crate):
        if c not in crates:
            crates.append(c)
    if not crates:
        return ""
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

    pages: list[str] = []
    cards: list[str] = []
    for c in crates:
        if len(pages) + len(cards) >= 10:
            break
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
            m, body = parse_fm(text) if text else ({}, "")
            door = door_for_path(p)
            if is_card_note(m):
                face = paint_face(p, m, body)
                if face:
                    strip = css_hex(card_strip_color(m)) or ""
                    if "tray-mini" not in face:
                        face = face.replace('class="face"', 'class="face tray-mini"', 1)
                        face = face.replace("class='face'", "class='face tray-mini'", 1)
                    where = _where_for(p, door if isinstance(door, dict) else None)
                    style = f' style="--card-strip:{strip}"' if strip else ""
                    cards.append(
                        f'<div class="tray-mini-wrap"{style}>'
                        f'<span class="tray-mini-where">{html.escape(where)}</span>'
                        + face
                        + "</div>"
                    )
                    continue
            href = str((door or {}).get("href") or "").strip() or kid_href(p)
            title = str((m or {}).get("title") or (door or {}).get("title") or p.stem).strip()
            where = _where_for(p, door if isinstance(door, dict) else None)
            pages.append(
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
        pages.append(
            f'<a class="tray-slip" href="{href}">'
            f'<span class="tray-slip-where">{where}</span>'
            f'<span class="tray-slip-title">{title}</span>'
            f"</a>"
        )
    if not pages and not cards:
        return ""
    chunks = ['<aside class="tray-connected" aria-label="Also referenced on">']
    if pages:
        chunks.append('<div class="tray-connected-row is-pages">')
        chunks.append('<span class="tray-hinter-label">Also on pages</span>')
        chunks.append('<div class="tray-connected-list">' + "".join(pages) + "</div>")
        chunks.append("</div>")
    if cards:
        chunks.append('<div class="tray-connected-row is-cards">')
        chunks.append('<span class="tray-hinter-label">Also on cards</span>')
        chunks.append('<div class="tray-connected-list">' + "".join(cards) + "</div>")
        chunks.append("</div>")
    chunks.append("</aside>")
    return "".join(chunks)


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
        f'<div class="tray-stage">'
        f'<div class="tray-focus">{inner}</div>'
        f"{hinter}"
        f"</div>"
        f'<aside class="tray-rail" data-mouth="{mouth_e}">{rail}</aside>'
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
    painted = paint_face(p)
    if not painted:
        return ""
    if 'class="face"' in painted and "face-ref" not in painted:
        painted = painted.replace(
            'class="face"', 'class="face face-ref"', 1
        )
    return painted


def print_crate_link(raw_id: str, label: str | None = None) -> str:
    """Plain wiki-style door to a crate — title only, not the face/frame."""
    crate = norm_crate(raw_id)
    if not crate:
        return '<span class="pic-miss">[no crate]</span>'
    door = door_for_crate(crate)
    if door is None:
        return (
            f'<span class="pic-miss">[no crate: {html.escape(crate)}]</span>'
        )
    shown = (label or "").strip() or str(door.get("title") or crate)
    href = str(door.get("href") or crate_href(crate))
    return (
        f'<a class="wiki" href="{html.escape(href, True)}">'
        f"{html.escape(shown)}</a>"
    )



def print_pocket_link(raw: str, label: str | None = None) -> str:
    """Wiki door to a go.*/roam.* pocket path (or lobby /rel)."""
    s = (raw or "").strip().replace(chr(92), "/")
    if not s:
        return '<span class="pic-miss">[no link]</span>'
    low = s.lower()
    if "://" in s or low.startswith(
        ("javascript:", "data:", "vbscript:", "file:")
    ):
        return '<span class="pic-miss">[bad link]</span>'
    parts = [p for p in s.split("/") if p != ""]
    if any(p == ".." for p in parts):
        return '<span class="pic-miss">[bad link]</span>'
    if not (GO_PREFIX.match(s) or s.startswith("/")):
        return '<span class="pic-miss">[bad link]</span>'
    name, rel = split_pocket(s)
    if name:
        host = get_host(name)
        if host is None:
            return (
                f'<span class="pic-miss">[no host: {html.escape(name)}]</span>'
            )
        with using_host(host):
            href = page_href(rel)
    else:
        href = href_from_pocket(s)
    shown = (label or "").strip()
    if not shown:
        if rel:
            leaf = rel.rstrip("/").rsplit("/", 1)[-1]
            if leaf.lower().endswith(".md"):
                leaf = leaf[:-3]
            shown = leaf or name or "start"
        else:
            shown = name or "start"
    return (
        f'<a class="wiki pocket-link" href="{html.escape(href, True)}">'
        f"{html.escape(shown)}</a>"
    )


def print_link_token(
    kind: str, target: str, label: str | None = None
) -> str:
    """{{link:}} / {{crate:}} — crate hex stays crate; else pocket path."""
    raw = (target or "").strip()
    lab = (label or "").strip() or None
    kind_l = (kind or "link").strip().lower()
    looks_crate = bool(
        re.fullmatch(r"(?:crate\.)?[A-Fa-f0-9]{16}", raw, re.I)
    )
    if kind_l == "crate" or looks_crate:
        return print_crate_link(raw, lab)
    if kind_l != "link":
        return '<span class="pic-miss">[bad link]</span>'
    return print_pocket_link(raw, lab)

# POCKET_LINK_GO_HOST

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
        if key.lower() in SLOT_NAMES or key.lower() in ("span", "div", "block"):
            return m.group(0)
        if key.lower() in ("mark", "marks"):
            return ""
        raw = lookup(key)
        if raw is None:
            return ""
        text = str(raw or "").strip()
        painted = fm_inline(text) if text else ""
        rom = str(lookup(key + "_rom") or "").strip()
        if painted and rom:
            launched = rom_launch_html(rom, text)
            if launched:
                return launched
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


def folder_from_rel(rel: str | None, fallback: Path) -> Path:
    """Folder for 'here' lists: note parent, or the folder path itself."""
    here = (rel or "").replace("\\", "/").strip("/")
    if not here:
        return fallback
    seat = safe_rel(here)
    if seat is None:
        return fallback
    if seat.is_file():
        return seat.parent
    if seat.is_dir():
        return seat
    return fallback


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
    # When worn as a shell, folder is the shell root — so {{doors}} keeps
    # listing the room's root houses even deep inside. {{files}} / {{faces}}
    # follow the open hall, not the parent shell folder.
    here_folder = folder_from_rel(rel, folder)
    body = rewrite_tool_slots(body)
    body, had_inject = expand_injectors(body, here_folder, rel)
    had = had_inject
    doors = door_cards(folder, here=rel, mode="cards")
    doors_chips = None
    roam_doors = None
    tag_tally = charlie_word_use_tally() if active_host() == TAGS_HOST_SLUG else None
    notes = file_list(here_folder, "files", extra="files", here=rel, tally=tag_tally)
    spines = file_list(here_folder, "files", extra="spines", here=rel, tally=tag_tally)
    listing = file_list(here_folder, "all", here=rel, tally=tag_tally)
    if "{{doors:roam}}" in body or "{{roam}}" in body:
        roam_doors = door_cards(folder, here=rel, mode="cards", scope="roam")
        body = body.replace("{{doors:roam}}", roam_doors).replace("{{roam}}", roam_doors)
        had = True
    if "{{doors:chips}}" in body or "{{worlds:chips}}" in body:
        doors_chips = door_cards(folder, here=rel, mode="chips")
        body = body.replace("{{doors:chips}}", doors_chips).replace(
            "{{worlds:chips}}", doors_chips
        )
        had = True
    if "{{doors:cards}}" in body or "{{worlds:cards}}" in body:
        body = body.replace("{{doors:cards}}", doors).replace("{{worlds:cards}}", doors)
        had = True
    if "{{doors}}" in body or "{{worlds}}" in body:
        body = body.replace("{{doors}}", doors).replace("{{worlds}}", doors)
        had = True
    if "{{files:date}}" in body:  # FILES_DATE_SORT
        notes_date = file_list(
            here_folder, "files", extra="files", here=rel, tally=tag_tally, sort="date"
        )
        body = body.replace("{{files:date}}", notes_date)
        had = True
    if "{{files}}" in body:
        body = body.replace("{{files}}", notes)
        had = True
    if "{{spines}}" in body:
        body = body.replace("{{spines}}", spines)
        had = True
    if "{{tagsearch}}" in body:
        body = body.replace("{{tagsearch}}", tag_search_form())
        had = True
    if "{{taglook}}" in body:
        body = body.replace("{{taglook}}", tag_look_block(rel, meta))
        had = True
    if "{{codesearch}}" in body:
        body = body.replace("{{codesearch}}", code_search_form())
        had = True
    if "{{huntsearch}}" in body:
        body = body.replace("{{huntsearch}}", hunt_search_form("detective"))
        had = True
    if "{{huntlook}}" in body:
        body = body.replace("{{huntlook}}", hunt_look_block("detective"))
        had = True
    if "{{blotsearch}}" in body:
        body = body.replace("{{blotsearch}}", hunt_search_form("librarian"))
        had = True
    if "{{blotlook}}" in body:
        body = body.replace("{{blotlook}}", hunt_look_block("librarian"))
        had = True
    if "{{erasearch}}" in body or "{{eventsearch}}" in body:
        form = era_search_form()
        body = body.replace("{{erasearch}}", form).replace("{{eventsearch}}", form)
        had = True
    if "{{eralook}}" in body or "{{eventlook}}" in body:
        look = era_look_block(rel, meta)
        body = body.replace("{{eralook}}", look).replace("{{eventlook}}", look)
        had = True
    if "{{peoplesearch}}" in body or "{{kvensearch}}" in body:
        form = people_search_form()
        body = body.replace("{{peoplesearch}}", form).replace("{{kvensearch}}", form)
        had = True
    if "{{peoplelook}}" in body or "{{kvenlook}}" in body:
        look = people_look_block(rel, meta)
        body = body.replace("{{peoplelook}}", look).replace("{{kvenlook}}", look)
        had = True
    if "{{loresearch}}" in body or "{{cardsearch}}" in body:
        form = lore_search_form()
        body = body.replace("{{loresearch}}", form).replace("{{cardsearch}}", form)
        had = True
    if "{{lorelook}}" in body or "{{cardlook}}" in body:
        look = lore_look_block()
        body = body.replace("{{lorelook}}", look).replace("{{cardlook}}", look)
        had = True
    if "{{codelook}}" in body:
        body = body.replace("{{codelook}}", code_look_placeholder(rel, meta))
        had = True
    if "{{compost}}" in body:
        body = body.replace("{{compost}}", compost_look_block(rel, meta))
        had = True
    if RECENT_SLOT_RE.search(body):
        def _recent_slot(m: re.Match[str]) -> str:
            return recent_block(m.group(1))

        body = RECENT_SLOT_RE.sub(_recent_slot, body)
        had = True
    if "{{shelf}}" in body:
        body = body.replace("{{shelf}}", page_card_shelf(rel, meta))
        had = True
    if "{{navbar:files}}" in body or "{{nav:files}}" in body or "{{navfiles}}" in body:
        # Shell root (folder), not open hall — same anchor as {{doors}} so the strip
        # stays populated in leaf subfolders. here=rel still marks .on.
        navf = navbar_files(folder, here=rel)
        body = (
            body.replace("{{navbar:files}}", navf)
            .replace("{{nav:files}}", navf)
            .replace("{{navfiles}}", navf)
        )
        had = True
    if "{{navbar}}" in body or "{{nav}}" in body:
        nav = navbar_links(folder, here=rel)
        body = body.replace("{{navbar}}", nav).replace("{{nav}}", nav)
        had = True
    if "{{dir}}" in body or "{{list}}" in body:
        body = body.replace("{{dir}}", listing).replace("{{list}}", listing)
        had = True
    if DIRTREE_MODE_RE.search(body):
        def _dirtree_mode_slot(m: re.Match[str]) -> str:
            mode = (m.group(1) or "all").strip().lower()
            return dir_tree(here_folder, here=rel, mode=mode)

        body = DIRTREE_MODE_RE.sub(_dirtree_mode_slot, body)
        had = True
    if "{{navbar:dirtree}}" in body or "{{nav:dirtree}}" in body:
        # Shell-root folders tree — same anchor as {{navbar}} / {{navbar:files}}.
        nav_tree = (
            '<nav class="pg-navbar pg-navbar-tree">'
            + dir_tree(folder, here=rel, mode="folders")
            + "</nav>"
        )
        body = body.replace("{{navbar:dirtree}}", nav_tree).replace(
            "{{nav:dirtree}}", nav_tree
        )
        had = True
    if TREE_SLOT_RE.search(body):
        rooted = file_tree(folder, here=rel)
        body = TREE_SLOT_RE.sub(rooted, body)
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
            return meta_slot_html(folder, crumb_rel, m.group(1))

        body = META_SLOT_RE.sub(_meta_slot, body)
    if CABINET_FIELD_RE.search(body):
        def _cabinet_field(m: re.Match[str]) -> str:
            return catalog_field_token(folder, crumb_rel, m.group(1), m.group(2))

        body = CABINET_FIELD_RE.sub(_cabinet_field, body)
    if CHIP_FIELD_RE.search(body):
        def _chip_field(m: re.Match[str]) -> str:
            return catalog_chip_token(folder, crumb_rel, m.group(1), m.group(2))

        body = CHIP_FIELD_RE.sub(_chip_field, body)
    if "{{edges}}" in body:
        body = body.replace("{{edges}}", paint_lore_edges(meta or {}))
    if "{{headers}}" in body:
        body = body.replace("{{headers}}", headers_block(meta or {}))
    need_faces = "{{faces}}" in body or "{{cards}}" in body
    if need_faces:
        had = True
    body = fill_fields(body, meta)
    if need_faces:
        faces = face_list(here_folder)
        body = body.replace("{{faces}}", faces).replace("{{cards}}", faces)
    if FACE_CRATE_RE.search(body):
        body = FACE_CRATE_RE.sub(lambda m: print_crate_face(m.group(1)), body)
    if LINK_CRATE_RE.search(body):
        body = LINK_CRATE_RE.sub(
            lambda m: print_link_token(m.group(1), m.group(2), m.group(3) or ""),  # POCKET_LINK_GO_HOST
            body,
        )
    body = place_crumb(body, rel, folder, meta)
    if auto and not had:
        body = body + "\n" + (doors if is_vault_root(folder) else listing)
    return body



def meta_codeword(meta: dict | None) -> str:
    """Canonical key is codeword:; also accept password:/lock:/code:."""
    if not meta:
        return ""
    for key in CODEWORD_KEYS:
        raw = str(meta.get(key) or "").strip()
        if raw:
            return raw
    return ""


def find_codeword_lock(target: Path | None) -> tuple[str, str] | None:
    """Nearest `_shell.md` with a codeword, walking up from the page/folder.

    Child rooms inherit a parent lock unless they set their own codeword.
    Returns (shell_rel, codeword) where shell_rel is vault-relative ('' = host root).
    """
    if target is None:
        return None
    try:
        vault = active_vault().resolve()
        cur = target.resolve()
        if cur.is_file():
            cur = cur.parent
    except OSError:
        return None
    while True:
        loaded = load_index(cur)
        if loaded:
            cw = meta_codeword(loaded[0])
            if cw:
                try:
                    rel = "" if is_vault_root(cur) else cur.relative_to(vault).as_posix()
                except ValueError:
                    rel = ""
                return rel, cw
        if is_vault_root(cur):
            return None
        parent = cur.parent
        if parent == cur:
            return None
        try:
            parent.relative_to(vault)
        except ValueError:
            return None
        cur = parent


def cw_token(host: str, shell_rel: str, codeword: str) -> str:
    """Session flag: hash of host + locking shell path + codeword (no plaintext cookie)."""
    host_s = (host or "").strip().lower()
    path_s = (shell_rel or "").replace("\\", "/").strip("/")
    cw = (codeword or "").strip()
    raw = f"{host_s}|{path_s}|{cw}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def codeword_gate_body(*, wrong: bool = False, action: str = "") -> str:
    """Cute minimal lock form — wears the room coat via .go-shell vars; nothing secret in HTML."""
    hint = (
        '<p class="cw-gate-hint">hmm, not that one — try again?</p>'
        if wrong
        else '<p class="cw-gate-hint">a soft gate. ask whoever keeps this room.</p>'
    )
    act = html.escape(action or "", True)
    # Class-only markup so environment CSS (ineffable, mausoleum, …) can dress the gate.
    return f"""<style>
.cw-gate {{
  max-width: 22rem;
  margin: 2.5rem auto;
  padding: 1.25rem 1.4rem;
  border: 1px solid var(--line, rgba(128,128,128,.35));
  border-radius: 10px;
  background: color-mix(in srgb, var(--steel, var(--stone, var(--paper, #1a1a1a))) 88%, transparent);
  color: var(--ink, var(--text, inherit));
  font-family: inherit;
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--ink, #fff) 8%, transparent);
}}
.cw-gate-msg {{ margin: 0 0 .85rem; font-size: 1.15rem; letter-spacing: 0.04em; }}
.cw-gate-form {{ display: flex; flex-direction: column; gap: .65rem; }}
.cw-gate-form label {{ display: flex; flex-direction: column; gap: .3rem; font-size: .9rem; color: var(--mute, inherit); }}
.cw-gate-form input[type="password"] {{
  font: inherit;
  padding: .45rem .6rem;
  color: inherit;
  background: color-mix(in srgb, var(--void, var(--bg, #000)) 55%, transparent);
  border: 1px solid var(--line, rgba(128,128,128,.4));
  border-radius: 6px;
}}
.cw-gate-form button {{
  align-self: flex-start;
  font: inherit;
  padding: .35rem 1rem;
  border-radius: 999px;
  cursor: pointer;
  color: inherit;
  background: color-mix(in srgb, var(--seal, var(--accent, var(--brass, #c8a050))) 22%, transparent);
  border: 1px solid var(--line, rgba(128,128,128,.45));
}}
.cw-gate-form button:hover {{
  background: color-mix(in srgb, var(--seal, var(--accent, var(--brass, #c8a050))) 38%, transparent);
}}
.cw-gate-hint {{ margin: .85rem 0 0; font-size: .85rem; color: var(--mute, inherit); opacity: .9; }}
</style>
<section class="cw-gate">
  <p class="cw-gate-msg">this room is locked</p>
  <form method="post" action="{act}" class="cw-gate-form">
    <input type="hidden" name="cw_unlock" value="1">
    <label>
      <span>code word</span>
      <input type="password" name="codeword" autocomplete="off" autofocus>
    </label>
    <button type="submit">enter</button>
  </form>
  {hint}
</section>
"""


def codeword_gate_page(
    *,
    title: str = "locked",
    rel: str = "",
    wrong: bool = False,
    here: Path | None = None,
    shell_rel: str | None = None,
) -> bytes:
    is_dir = False
    folder: Path | None = None
    if here is not None:
        try:
            if here.is_dir():
                is_dir = True
                folder = here
            elif here.is_file():
                folder = here.parent
        except OSError:
            folder = None
    # Wear the locking shell's environment coat (ineffable, mausoleum, …).
    environment = None
    accent = "#6e6254"
    try:
        vault = active_vault()
        shell_folder = None
        if shell_rel is not None:
            s = str(shell_rel).replace("\\", "/").strip("/")
            shell_folder = vault if not s else (vault / s)
        elif folder is not None:
            shell_folder = folder
        if shell_folder is not None and shell_folder.is_dir():
            loaded = load_index(shell_folder)
            if loaded:
                meta = loaded[0]
                environment = str(meta.get("environment") or "").strip() or None
                title = str(meta.get("title") or "").strip() or title
                strip = env_css_strip(environment) if environment else ""
                if strip:
                    accent = strip
    except OSError:
        pass
    bar = pocket_bar(rel, is_dir)
    action = page_href(rel, is_dir=is_dir)
    body = codeword_gate_body(wrong=wrong, action=action)
    crumb = folder_crumbs(rel) if rel else ""
    vault_key = pocket_key(here) if here is not None else None
    return page(
        title,
        body,
        accent,
        crumb,
        bar,
        environment=environment,
        here=folder,
        vault=vault_key,
        librarian=True,
        body_class="is-cw-gate",
        mark="mypi:lock",
    )

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


def has_subshell_slot(src: str) -> bool:
    return "{{subshell}}" in src


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


def find_subshells(
    folder: Path, stop: Path | None
) -> list[tuple[Path, dict, str]]:
    """`_shell.md` files between here and the dress shell that nest via {{subshell}}.

    Innermost first. A {{paper}} shell is the dress room, not a subshell.
    """
    out: list[tuple[Path, dict, str]] = []
    try:
        cur = folder.resolve()
        stop_r = stop.resolve() if stop is not None else None
    except OSError:
        return out
    while True:
        if stop_r is not None and cur == stop_r:
            break
        loaded = load_index(cur)
        if loaded:
            meta, src = loaded
            if (
                not paper_off(meta)
                and has_subshell_slot(src)
                and not has_paper_slot(src)
            ):
                out.append((cur, meta, src))
        if is_vault_root(cur):
            break
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return out


def place_hole(shell_html: str, inner: str, hole: re.Pattern[str]) -> str:
    if not hole.search(shell_html):
        return shell_html
    return hole.sub(lambda _m: inner, shell_html, count=1)


def place_paper(shell_html: str, inner: str) -> str:
    return place_hole(shell_html, inner, PAPER_HOLE)


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
    hole: re.Pattern[str] | None = None,
) -> str:
    dressed = fill_slots(
        md_lite(shell_src),
        shell_folder,
        auto=False,
        crumb_rel=page_rel,
        meta=shell_dress(shell_meta, page_meta),
    )
    return settle_compost_message(place_hole(dressed, inner, hole or PAPER_HOLE))


def wrap_in_shell(folder: Path, inner: str, page_rel: str, meta: dict | None = None) -> tuple[str, dict | None]:
    if meta and paper_off(meta):
        return inner, None
    if is_card_note(meta):
        return inner, None
    found = find_shell(folder)
    stop = found[0] if found else None
    last_sub: dict | None = None
    for sub_folder, sub_meta, sub_src in find_subshells(folder, stop):
        inner = wear_shell(
            sub_src,
            sub_folder,
            inner,
            page_rel,
            sub_meta,
            meta,
            SUBSHELL_HOLE,
        )
        last_sub = sub_meta
    if not found:
        return inner, last_sub
    shell_folder, shell_meta, shell_src = found
    return wear_shell(shell_src, shell_folder, inner, page_rel, shell_meta, meta), shell_meta


def sight_stage(here: Path) -> None:
    """Mint a crate on every vault page on stage (.md / .canvas / guest .chip). Shell and paper stay distinct."""
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
        one(shell_path(folder))
        one(folder / PAPER_NAME)
        one(lobby_start(folder))
    found = find_shell(folder)
    if found:
        one(shell_path(found[0]))
    if here.is_file() and here.suffix.lower() == ".md" and not on_codes_host():
        try:
            text = here.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        meta, body = parse_fm(text)
        for c in chip_codes_in_note(meta, body, here):
            ensure_code_chain(c)
    if on_codes_host():
        gc_unreferenced_codes(keep=here)


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
    low = part.lower()
    if low.endswith(".md"):
        return part[:-3]
    if low.endswith(".chip"):
        return part[:-5]
    return part


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
    """Trail from the nearest paper-shell folder to here. No shell â†’ full {{crumb}} trail."""
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
    for loaded in (load_paper(folder), load_index(folder)):
        if not loaded:
            continue
        title = str(loaded[0].get("title", "")).strip()
        if title:
            return title
    if is_vault_root(folder):
        return "home"
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
    """Door to the nearest `_shell.md` walking up. Vault root if none."""
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
    if not folder.exists():
        return page("gone", "<p>this chip is not cited in the pocket anymore.</p>", "#6e6254", "", pocket_bar(""), librarian=False)
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
            inner = wear_compost_message(inner, inner_meta, rel)
        title = (
            str(inner_meta.get("title") or "").strip()
            or str(shell_meta.get("title") or "").strip()
            or (folder.name if rel else "root")
        )
        env = dress_environment(folder, inner_meta, shell_meta)
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
            stamps=page_marks_html(inner_meta),
        )

    meta: dict = {}
    if paper:
        meta, src = paper
        title = meta.get("title") or (folder.name if rel else "root")
        body = fill_slots(md_lite(src), folder, auto=False, crumb_rel=rel, meta=meta)
        body = wear_compost_message(body, meta, rel)
        env = meta.get("environment")
    elif loaded and not has_subshell_slot(loaded[1]):
        meta, src = loaded
        title = meta.get("title") or (folder.name if rel else "root")
        body = fill_slots(md_lite(src), folder, meta=meta)
        env = meta.get("environment")
    elif not rel:
        spec = _CURRENT_HOST.get()
        title = (spec.title if spec else "") or active_host()
        if is_lobby():
            body = f"<h1>{html.escape(title)}</h1>" + door_cards(folder)
            env = None
        else:
            env = (spec.environment if spec else None) or None
            listing = file_list(folder, "all")
            body = f"<h1>{html.escape(title)}</h1>" + listing
    else:
        title = folder.name
        env = dress_environment(folder)
        hunt_hall = env_name(env) in ("hunt", "era") or active_host() in (
            "detective",
            "era",
        )
        listing = face_list(folder) if hunt_hall else file_list(folder, "all")
        body = f"<h1>{html.escape(folder.name)}</h1>" + listing
        env = env or None

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
        stamps=page_marks_html(meta),
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
    stamps: str = "",
) -> bytes:
    shown = (chrome or "").strip() or header_label(nearest_index_title(here), title)
    skin = env_name(environment)
    extra = ""
    extra += '<link rel="stylesheet" href="/styles/fonts.css">\n'
    # lorecard traveler preloads like fonts — planted crate faces dress on any host
    extra += '<link rel="stylesheet" href="/styles/lorecard.css?v=20260914210700">\n'
    if skin:
        extra += f'<link rel="stylesheet" href="{coat_link_href(skin)}">\n'
    extra += '<link rel="stylesheet" href="/librarian.css?v=20260922115800">\n'
    for href in extra_css or []:
        extra += f'<link rel="stylesheet" href="{html.escape(href, True)}">\n'
    html_attrs = f'data-pocket="{html.escape(bar, True)}"'
    # cute pin mark in www chrome URL bar when this go.* is pinned on start
    try:
        _pin_host = active_host()
        if _pin_host and _pin_host in host_pin_map():
            html_attrs += ' data-pinned="1"'
    except Exception:
        pass
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
    nicks_js = json.dumps(bar_nicks(), separators=(",", ":"), ensure_ascii=True).replace(
        "<", "\\u003c"
    )
    schemes_js = json.dumps(
        host_scheme_map(), separators=(",", ":"), ensure_ascii=True
    ).replace("<", "\\u003c")
    extra_scripts = (
        "<script>window.pocketBarNicks="
        + nicks_js
        + ";window.pocketHostSchemes="
        + schemes_js
        + ";</script>\n"
        + extra_scripts
    )
    root = f"--note-accent: {accent};"
    hue = css_hex(strip or "")
    hue_css = f"<style>:root {{ --card-strip: {hue}; }}</style>\n" if hue else ""
    html_out = f"""<!doctype html>
<html lang="en" {html_attrs}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(shown)}</title>
{page_icon_link(here)}<link rel="stylesheet" href="/www.css?v=20260920203200">
<link rel="stylesheet" href="/dress.css?v=20260923200000">
<style>:root {{ {root} }}</style>
{extra}{hue_css}</head>
<body{body_attr}>
<header class="wwwExplorer_chrome" data-deck-chrome data-deck-controls="deep,min,max,close">
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
            title="Refresh Â· Shift/Ctrl+click = hard refresh" aria-label="Refresh">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 8a5 5 0 1 1-1.4-3.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/><polygon points="13.5,1.5 13.8,6.2 9.2,5.2"/></svg>
    </button>
        <button type="button" id="jumpPin" data-webbar="pin" title="Pin this page to jump bar" aria-label="Pin page" aria-pressed="false">
      <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.5 L9.2 5.8 L13.5 6.2 L10.2 9.1 L11.2 13.5 L8 11.2 L4.8 13.5 L5.8 9.1 L2.5 6.2 L6.8 5.8 Z" fill="currentColor"/></svg>
    </button>
<span id="wwwBar" class="linkSlug" tabindex="0" role="textbox" spellcheck="false" title="click to type · Enter or GO">{html.escape(bar)}</span>
    <button type="button" id="GO" data-webbar="go">GO!</button>
  </div>
  <div id="jumpBar" class="wwwJumpBar" hidden aria-label="Jump bookmarks"></div>
  <div id="workTabs" class="wwwWorkTabs" hidden aria-label="Working tabs"></div>
</header>
<div class="wwwExplorer_stage">
<div class="go-shell">
  {stamps}<main id="browserWindow">
{body}
  </main>
</div>
</div>
<footer class="wwwExplorer_status"><span id="wwwStatus">Done</span></footer>
<script src="/www.js?v=20260923200000"></script>
<script src="/librarian.js?v=20260922115800"></script>
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
    # Embed as text inside script â€” escape </script> breakouts
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
        '<span style="opacity:.6;margin-left:auto">pan Â· wheel zoom Â· read-only</span>'
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
<link rel="stylesheet" href="/www.css?v=20260920203200">
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
<script src="/librarian.js?v=20260922115800"></script>
</body></html>"""
    return html_out.encode("utf-8")


def missing_host_page(name: str) -> bytes:
    slug = host_slug(name) or (name or "???").strip()
    shown = format_pocket(slug).rstrip("/") if discover_hosts().get(slug) else "go." + slug
    body = (
        f"<h1>{html.escape(shown)}</h1>"
        "<p>that room isn't in the pocket yet!! "
        "a folder under ~hosts with that name makes a go.* door. "
        "kind: roam and source: in _hosts.yaml connects an exterior folder as roam.{slug}. "
        "it isn't missing forever. it just isn't here <em>now</em>.</p>"
    )
    return page(shown, body, "#6e6254", shown, shown + "/", "www", librarian=False)


HELP_MAX = 200_000


def help_list_pages() -> list[dict]:
    """Editable field-manual pages under ~help/."""
    root = HELP_ROOT
    root.mkdir(parents=True, exist_ok=True)
    pages: list[dict] = []
    try:
        files = sorted(root.glob("*.md"), key=lambda p: (p.name.lower() != "_index.md", p.name.lower()))
    except OSError:
        files = []
    for p in files:
        slug = p.stem
        title = slug if slug != "_index" else "help"
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            meta, _ = parse_fm(text)
            t = str(meta.get("title") or "").strip()
            if t:
                title = t
        except OSError:
            pass
        pages.append({"slug": slug, "title": title, "file": p.name})
    return pages


def help_path(slug: str) -> Path | None:
    s = env_name(slug) or ""
    if not s:
        return None
    # allow _index
    if slug.strip().lower() in ("_index", "index", "help"):
        s = "_index"
    path = (HELP_ROOT / f"{s}.md").resolve()
    try:
        path.relative_to(HELP_ROOT.resolve())
    except ValueError:
        return None
    return path



def _hosts_path_hint(path: Path, root: Path, prefix: str) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
        return prefix.rstrip("/") + "/" + rel
    except (ValueError, OSError):
        return prefix.rstrip("/") + "/" + path.name


def host_is_exterior(host: Host) -> bool:
    try:
        host.root.resolve().relative_to(HOSTS_ROOT.resolve())
        return False
    except (ValueError, OSError):
        return True


def hosts_list_entries() -> list[dict]:
    out: list[dict] = []
    pins = host_pin_map()
    shows = host_show_map()
    for slug, host in sorted(discover_hosts().items(), key=lambda kv: kv[0].lower()):
        shell = shell_path(host.root)
        meta = read_md_meta(shell) if shell.is_file() else {}
        title = str(meta.get("title") or host.title or slug).strip() or slug
        section = str(meta.get("section") or meta.get("neighborhood") or "").strip()
        out.append({
            "slug": slug,
            "title": title,
            "section": section,
            "kind": host.kind or "go",
            "scheme": host_scheme_of(host),
            "source": str(host.root) if ((host.kind or "go") == "roam" or host_is_exterior(host)) else "",
            "environment": host.environment or "",
            "show": bool(shows.get(slug, True)),
            "pin": pins.get(slug),
        })
    return out


def hosts_get(host_raw: str = "") -> tuple[int, dict | None, str]:
    hosts = hosts_list_entries()
    empty = {
        "house": "HOSTS",
        "hosts": hosts,
        "host": "",
        "shell_headers": "",
        "shell_markdown": "",
        "letter_body": "",
        "letter_html": "",
        "letter_path": "",
        "shell_path": "",
    }
    if not hosts:
        return 200, empty, ""
    raw = (host_raw or "").strip()
    if raw:
        want = host_slug(raw)
        if not want:
            return 400, None, "bad host"
        if want not in {h["slug"] for h in hosts}:
            return 400, None, "no such host"
    else:
        go_slugs = [
            h["slug"] for h in hosts if (h.get("kind") or "go") != "roam"
        ]
        want = go_slugs[0] if go_slugs else hosts[0]["slug"]
    found_map = discover_hosts()
    host = found_map.get(want)
    if host is None:
        return 400, None, "no such host"
    shell_file = shell_path(host.root)
    shell_headers, shell_markdown = "", ""
    if shell_file.is_file():
        try:
            text = shell_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 500, None, "could not read shell"
        shell_headers, shell_markdown = split_note(text)
    letter_dest = readme_dest_for_folder(host.root)
    if letter_dest is None:
        resolved = readme_resolve(host.root)
        if resolved is not None:
            letter_dest = resolved[1]
    letter_body = ""
    if letter_dest is not None and letter_dest.is_file():
        try:
            letter_body = letter_dest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 500, None, "could not read letter"
    meta, src = parse_fm(letter_body or "")
    letter_html = md_lite(src if meta else (letter_body or ""))
    if letter_dest is not None:
        letter_path = _hosts_path_hint(letter_dest, README_ROOT, "~readme")
    else:
        letter_path = "~readme/" + want + "/README.md"
    if host.kind == "roam" or host_is_exterior(host):
        shell_hint = str(host.root)
    else:
        shell_hint = _hosts_path_hint(shell_file, HOSTS_ROOT, "~hosts")
    pin_n = host_pin_map().get(want)
    show_b = host_is_shown(want)
    obj = {
        "house": "HOSTS",
        "hosts": hosts,
        "host": want,
        "kind": host.kind or "go",
        "title": str(host.title or "").strip() or want,
        "source": str(host.root) if ((host.kind or "go") == "roam" or host_is_exterior(host)) else "",
        "environment": host.environment or "",
        "show": show_b,
        "pin": pin_n,
        "shell_headers": shell_headers,
        "shell_markdown": shell_markdown,
        "letter_body": letter_body,
        "letter_html": letter_html,
        "letter_path": letter_path,
        "shell_path": shell_hint,
    }
    return 200, obj, ""



def hosts_yaml_update(
    slug: str,
    *,
    show=None,
    pin="__omit__",
    set_keys: dict | None = None,
    drop_block: bool = False,
) -> tuple[bool, str]:
    """Safely edit ~hosts/_hosts.yaml show:/pin: under a top-level slug block.

    show=True removes show: (default on). show=False writes show: false.
    pin="__omit__" leaves pin alone; pin=None removes pin:; pin=int writes pin: N.
    set_keys writes or removes extra keys (kind/source/title/environment).
    drop_block removes the whole slug: block (disconnect roam; does not delete the folder).
    Creates the slug: block at end if missing (unless drop_block). Preserves comments/other keys.
    """
    s = host_slug(slug)
    if not s:
        return False, "bad host"
    HOSTS_ROOT.mkdir(parents=True, exist_ok=True)
    path = HOSTS_FILE
    try:
        raw = path.read_text(encoding="utf-8") if path.is_file() else ""
    except OSError:
        return False, "could not read _hosts.yaml"
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")

    start = -1
    for i, line in enumerate(lines):
        if not line or line[0] in " \t":
            continue
        if line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key = line.split(":", 1)[0].strip()
        if host_slug(key) == s or key.strip().lower() == s:
            start = i
            break
    if start < 0:
        if drop_block:
            return False, "no yaml block"
        while lines and lines[-1] == "":
            lines.pop()
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(s + ":")
        start = len(lines) - 1

    end = len(lines)
    for j in range(start + 1, len(lines)):
        line = lines[j]
        if not line.strip():
            continue
        if line[0] not in " \t" and not line.lstrip().startswith("#") and ":" in line:
            end = j
            break

    if drop_block:
        new_lines = lines[:start] + lines[end:]
        while new_lines and new_lines[-1] == "":
            new_lines.pop()
        out = "\n".join(new_lines)
        if out and not out.endswith("\n"):
            out += "\n"
        try:
            path.write_text(out, encoding="utf-8")
        except OSError:
            return False, "could not write _hosts.yaml"
        return True, ""

    def is_key_line(line: str, keys: tuple[str, ...]) -> bool:
        if not line.startswith("  "):
            return False
        stripped = line.lstrip()
        if stripped.startswith("#") or ":" not in stripped:
            return False
        k = stripped.split(":", 1)[0].strip().lower()
        return k in keys

    body = lines[start + 1 : end]
    if show is not None:
        body = [ln for ln in body if not is_key_line(ln, ("show", "active", "visible"))]
        if show is False:
            body.insert(0, "  show: false")
    if pin != "__omit__":
        body = [ln for ln in body if not is_key_line(ln, ("pin",))]
        if pin is not None:
            try:
                n = int(pin)
            except (TypeError, ValueError):
                return False, "bad pin"
            body.insert(0, "  pin: " + str(n))
    if set_keys:
        wanted: dict = {}
        for key, val in set_keys.items():
            kn = str(key or "").strip().lower()
            if kn:
                wanted[kn] = val
        prefer = ("kind", "source", "title", "environment")
        for kn in wanted:
            body = [ln for ln in body if not is_key_line(ln, (kn,))]
        for kn in reversed(prefer):
            if kn not in wanted:
                continue
            val = wanted[kn]
            if val is None:
                continue
            body.insert(0, "  " + kn + ": " + str(val))
        for kn, val in wanted.items():
            if kn in prefer or val is None:
                continue
            body.append("  " + kn + ": " + str(val))

    new_lines = lines[: start + 1] + body + lines[end:]
    out = "\n".join(new_lines)
    if not out.endswith("\n"):
        out += "\n"
    try:
        path.write_text(out, encoding="utf-8")
    except OSError:
        return False, "could not write _hosts.yaml"
    return True, ""


def hosts_put(data: dict) -> tuple[int, dict | None, str]:
    if not isinstance(data, dict):
        return 400, None, "bad body"
    slug = host_slug(str(data.get("host") or ""))
    if not slug:
        return 400, None, "bad host"
    host = discover_hosts().get(slug)
    if host is None:
        return 400, None, "no such host"
    what = str(data.get("what") or "shell").strip().lower() or "shell"
    if what in ("meta", "yaml"):
        show_arg = None
        pin_arg = "__omit__"
        if "show" in data:
            raw_show = data.get("show")
            if isinstance(raw_show, bool):
                show_arg = raw_show
            else:
                parsed = _parse_show_flag(str(raw_show))
                if parsed is None:
                    return 400, None, "bad show"
                show_arg = parsed
        if "pin" in data:
            raw_pin = data.get("pin")
            if raw_pin is None or raw_pin is False:
                pin_arg = None
            elif isinstance(raw_pin, bool) and raw_pin is True:
                pins_now = host_pin_map()
                pin_arg = (max(pins_now.values()) + 1) if pins_now else 1
            else:
                try:
                    pin_arg = int(raw_pin)
                except (TypeError, ValueError):
                    return 400, None, "bad pin"
        if show_arg is None and pin_arg == "__omit__":
            return 400, None, "need show or pin"
        with LBR_LOCK:
            ok, err = hosts_yaml_update(slug, show=show_arg, pin=pin_arg)
        if not ok:
            return 500, None, err or "yaml update failed"
        return hosts_get(slug)
    if what in ("disconnect", "unhook"):
        if (host.kind or "go") != "roam":
            return 400, None, "not a roam host"
        with LBR_LOCK:
            ok, err = hosts_yaml_update(slug, drop_block=True)
        if not ok:
            return 500, None, err or "disconnect failed"
        return hosts_get("")
    if what in ("roam", "source"):
        if (host.kind or "go") != "roam":
            return 400, None, "not a roam host"
        keys: dict = {"kind": "roam"}
        touched = False
        if "source" in data or "path" in data or "folder" in data:
            source_raw = str(
                data.get("source") or data.get("path") or data.get("folder") or ""
            )
            root = roam_source_path(source_raw)
            if root is None:
                return 400, None, "need a source folder"
            keys["source"] = yaml_source_scalar(str(root))
            touched = True
        if "title" in data:
            title = str(data.get("title") or "").strip()
            keys["title"] = yaml_scalar(title) if title else yaml_scalar(slug)
            touched = True
        env_raw = None
        if "environment" in data:
            env_raw = data.get("environment")
        elif "env" in data:
            env_raw = data.get("env")
        elif "coat" in data:
            env_raw = data.get("coat")
        if env_raw is not None:
            env = env_name(str(env_raw or "")) or ""
            keys["environment"] = env if env else None
            touched = True
        if not touched:
            return 400, None, "need source, title, or environment"
        with LBR_LOCK:
            ok, err = hosts_yaml_update(slug, set_keys=keys)
        if not ok:
            return 500, None, err or "yaml update failed"
        return hosts_get(slug)
    if what == "letter":
        body = str(data.get("body") if data.get("body") is not None else "")
        body = body.replace("\r\n", "\n").replace("\r", "\n")
        if len(body) > README_MAX:
            return 413, None, "room letter too long"
        dest = readme_dest_for_folder(host.root)
        if dest is None:
            return 400, None, "no letter path"
        with LBR_LOCK:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
        return hosts_get(slug)
    if what != "shell":
        return 400, None, "bad what"
    headers = str(data.get("headers") if data.get("headers") is not None else "")
    headers = headers.replace("\r\n", "\n").replace("\r", "\n")
    shell = shell_path(host.root)
    with LBR_LOCK:
        try:
            old = shell.read_text(encoding="utf-8") if shell.is_file() else ""
        except OSError:
            old = ""
        _old_h, old_body = split_note(old)
        if data.get("markdown") is None:
            markdown = old_body
        else:
            markdown = str(data.get("markdown") or "")
        markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
        if len(headers) + len(markdown) > README_MAX:
            return 413, None, "shell too long"
        live = file_crate(shell) if shell.is_file() else ""
        if not live:
            live = str(parse_fm(old)[0].get("crate") or "").strip()
        text = join_note(headers, markdown)
        if live:
            text = force_crate_line(text, live)
        shell.parent.mkdir(parents=True, exist_ok=True)
        write_note(shell, text)
        mint = not live
    if mint:
        ensure_crate(shell)
    return hosts_get(slug)


def hosts_create(title_raw: str = "", slug_raw: str = "", template_raw: str = "") -> tuple[int, dict | None, str]:
    """Mint a new go.* host under ~hosts with shell + room letter."""
    title = (title_raw or "").strip()
    raw_slug = (slug_raw or "").strip()
    if not raw_slug and title:
        rough = re.sub(r"[^A-Za-z0-9_-]+", "-", title.lower()).strip("-_")
        raw_slug = rough
    slug = host_slug(raw_slug)
    if not slug:
        return 400, None, "need a go name (letters, numbers, dot, - _)"
    if slug in RESERVED_HOST_SLUGS:
        return 400, None, "reserved host name"
    if discover_hosts().get(slug) is not None:
        return 409, None, "go." + slug + " already exists"
    root = (HOSTS_ROOT / slug).resolve()
    try:
        root.relative_to(HOSTS_ROOT.resolve())
    except ValueError:
        return 400, None, "bad host path"
    if root.exists():
        return 409, None, "go." + slug + " already exists"
    if not title:
        title = slug
    crate = mint_crate_id()
    index_text = (
        "---\n"
        "crate: " + crate + "\n"
        "title: " + yaml_scalar(title) + "\n"
        "---\n\n"
        "{{.mast}}" + title + "\n\n"
        "{{doors}}\n"
    )
    with LBR_LOCK:
        try:
            root.mkdir(parents=True, exist_ok=False)
            (root / INDEX_NAME).write_text(index_text, encoding="utf-8")
        except FileExistsError:
            return 409, None, "go." + slug + " already exists"
        except OSError:
            return 500, None, "could not create host"
    try:
        mint_zone_room_letter(root, title=title, env=slug)
    except Exception:
        pass
    tid = (template_raw or "").strip().lower()
    if tid in TEMPLATE_IDS:
        templates_apply("go." + slug, tid, mode="new", env_raw=slug, title_raw=title)
    return hosts_get(slug)


def hosts_roam_connect(
    slug_raw: str = "",
    source_raw: str = "",
    title_raw: str = "",
    env_raw: str = "",
) -> tuple[int, dict | None, str]:
    """Connect an exterior folder as roam.{slug}. Does not mint ~hosts/{slug}."""
    title = (title_raw or "").strip()
    raw_slug = (slug_raw or "").strip()
    if not raw_slug and title:
        rough = re.sub(r"[^A-Za-z0-9_-]+", "-", title.lower()).strip("-_")
        raw_slug = rough
    slug = host_slug(raw_slug)
    if not slug:
        return 400, None, "need a roam name (letters, numbers, dot, - _)"
    if slug in RESERVED_HOST_SLUGS:
        return 400, None, "reserved host name"
    existing = discover_hosts().get(slug)
    if existing is not None:
        if existing.kind == "roam":
            return 409, None, "roam." + slug + " already exists"
        return 409, None, "go." + slug + " already exists"
    native = HOSTS_ROOT / slug
    if native.is_dir():
        return 409, None, "go." + slug + " already exists"
    root = roam_source_path(source_raw)
    if root is None:
        return 400, None, "need a source folder"
    if not title:
        title = slug
    env = env_name(str(env_raw or "")) or ""
    keys = {
        "kind": "roam",
        "source": yaml_source_scalar(str(root)),
        "title": yaml_scalar(title),
    }
    if env:
        keys["environment"] = env
    with LBR_LOCK:
        ok, err = hosts_yaml_update(slug, set_keys=keys)
    if not ok:
        return 500, None, err or "could not connect roam"
    return hosts_get(slug)



TEMPLATES_ROOT = ROOT / "mats" / "templates"
TEMPLATE_IDS = ("blank", "stack", "rail-left", "rail-right")


def templates_list() -> list[dict]:
    out: list[dict] = []
    for tid in TEMPLATE_IDS:
        meta_path = TEMPLATES_ROOT / tid / "meta.json"
        title, desc = tid, ""
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                title = str(meta.get("title") or tid)
                desc = str(meta.get("description") or "")
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        out.append({"id": tid, "title": title, "description": desc})
    return out


def template_shell_src(tid: str) -> Path | None:
    tid = (tid or "").strip().lower()
    if tid not in TEMPLATE_IDS:
        return None
    p = TEMPLATES_ROOT / tid / "_shell.md"
    return p if p.is_file() else None


def template_css_src(tid: str) -> Path | None:
    tid = (tid or "").strip().lower()
    if tid not in TEMPLATE_IDS:
        return None
    p = TEMPLATES_ROOT / tid / "base.css"
    return p if p.is_file() else None


def templates_apply(
    pocket_raw: str,
    template_id: str,
    mode: str = "overwrite",
    env_raw: str = "",
    title_raw: str = "",
) -> tuple[int, dict | None, str]:
    """Write template shell + coat CSS into a pocket. mode: overwrite|fork|new."""
    tid = (template_id or "").strip().lower()
    if tid not in TEMPLATE_IDS:
        return 400, None, "unknown template"
    mode_n = (mode or "overwrite").strip().lower()
    if mode_n not in ("overwrite", "fork", "new"):
        return 400, None, "bad mode"
    shell_src = template_shell_src(tid)
    css_src = template_css_src(tid)
    if shell_src is None or css_src is None:
        return 404, None, "template files missing"
    with using_pocket(pocket_raw) as host:
        if host is None:
            return 400, None, "no such host"
        standing = resolve_vault_page(pocket_raw)
        if standing is None:
            return 400, None, "not a vault page"
        folder = clay_folder(standing) if standing.is_file() else standing
        if folder is None or not folder.is_dir():
            return 400, None, "bad landing"
        env = env_name(env_raw) or env_name(getattr(host, "environment", "") or "") or env_name(host.name) or "coat"
        if mode_n == "fork":
            base = env
            n = 2
            while True:
                cand = env_name(f"{base}-{tid}") if n == 2 else env_name(f"{base}-{tid}-{n}")
                if not cand:
                    cand = env_name(f"{base}{n}")
                path = STYLES / f"{cand}.css"
                if not path.is_file():
                    env = cand
                    break
                n += 1
                if n > 40:
                    return 409, None, "could not fork coat name"
        title = (title_raw or "").strip() or str(getattr(host, "title", "") or host.name or env)
        try:
            raw_shell = shell_src.read_text(encoding="utf-8")
            raw_css = css_src.read_text(encoding="utf-8")
        except OSError:
            return 500, None, "could not read template"
        raw_shell = raw_shell.replace("{{TITLE}}", title).replace("{{ENV}}", env)
        shell_path = folder / INDEX_NAME
        with LBR_LOCK:
            try:
                STYLES.mkdir(parents=True, exist_ok=True)
                (STYLES / f"{env}.css").write_text(raw_css, encoding="utf-8")
                live = file_crate(shell_path) if shell_path.is_file() else ""
                if live:
                    raw_shell = force_crate_line(raw_shell, live)
                write_note(shell_path, raw_shell)
                if not live:
                    ensure_crate(shell_path)
                try:
                    dest = readme_dest_for_folder(folder)
                    if dest is not None:
                        stamp_room_environment(dest, env)
                except Exception:
                    pass
            except OSError:
                return 500, None, "could not write template"
        return 200, {
            "ok": True,
            "template": tid,
            "mode": mode_n,
            "env": env,
            "shell": pocket_key(shell_path),
            "css": f"{env}.css",
        }, ""


def help_get(page_raw: str = "") -> tuple[int, dict | None, str]:
    HELP_ROOT.mkdir(parents=True, exist_ok=True)
    pages = help_list_pages()
    if not pages:
        return 200, {"house": "HELP", "pages": [], "slug": "", "title": "", "body": "", "body_html": ""}, ""
    want = (page_raw or "").strip()
    if not want:
        want = pages[0]["slug"]
    path = help_path(want)
    if path is None:
        return 400, None, "bad help page"
    if not path.is_file():
        # fall back to first
        want = pages[0]["slug"]
        path = help_path(want)
        if path is None or not path.is_file():
            return 200, {"house": "HELP", "pages": pages, "slug": "", "title": "", "body": "", "body_html": ""}, ""
    try:
        body = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 500, None, "could not read help"
    meta, src = parse_fm(body)
    title = str(meta.get("title") or path.stem).strip()
    obj = {
        "house": "HELP",
        "pages": pages,
        "slug": path.stem,
        "title": title,
        "body": body,
        "body_html": md_lite(src if meta else body),
    }
    return 200, obj, ""


def help_put(page_raw: str, body: str) -> tuple[int, dict | None, str]:
    body = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    if len(body) > HELP_MAX:
        return 413, None, "help page too long"
    path = help_path(page_raw)
    if path is None:
        return 400, None, "bad help page"
    HELP_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(body, encoding="utf-8")
    except OSError:
        return 500, None, "could not write help"
    return help_get(path.stem)



SIDECAR_HOUSES = {
    "readme": ("BIOS", "#0000aa", "mypi:bios"),
    "librarian": ("LIBRARIAN", "#2a3f3d", "mypi:lib"),
    "charlie": ("CHARLIE", "#1a1204", "mypi:bay"),
    "detective": ("DETECTIVE", "#140808", "mypi:hunt"),
    "tps": ("TPS", "#2a2c28", "mypi:tps"),
    "cards": ("CARDS", "#3a3226", "mypi:deck"),
}


def sidecar_page(house: str) -> bytes:
    """Second window for one blotter. Follows the deck's vault path."""
    title, accent, brick = SIDECAR_HOUSES[house]
    card_css = (
        '''<link rel="stylesheet" href="/dress.css">\n'''
        '''<link rel="stylesheet" href="/styles/lorecard.css?v=20260914210700">\n'''
        if house == "cards"
        else ""
    )
    grip = ""
    html_out = f"""<!doctype html>
<html lang="en" data-sidecar="{html.escape(house, True)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="/www.css?v=20260920203200">
<link rel="stylesheet" href="/styles/fonts.css">
<style>:root {{ --note-accent: {accent}; }}</style>
<link rel="stylesheet" href="/librarian.css?v=20260922115800">
{card_css}</head>
<body class="is-sidecar">
<header class="wwwExplorer_chrome" data-deck-chrome data-deck-controls="min,close">
  <div class="wwwExplorer_windowTitleBar" data-deck-drag>
    <button type="button" class="wwwExplorer_mark" data-deck-menu title="Menu">{html.escape(brick)}</button>
    <span class="wwwExplorer_title" id="sidecarTitle" data-deck-drag>/</span>
    <div class="wwwExplorer_win" data-deck-window-controls aria-label="Window"></div>
  </div>
</header>
<div class="wwwExplorer_stage"></div>
{grip}<script src="/librarian.js?v=20260922115800"></script>
</body></html>"""
    return html_out.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[pocket-go]", args[0] if args else fmt)

    def send_html(
        self,
        blob: bytes,
        code: int = 200,
        *,
        set_cookies: list[str] | None = None,
    ) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        for raw in set_cookies or []:
            if raw:
                self.send_header("Set-Cookie", raw)
        self.end_headers()
        self.wfile.write(blob)

    def cw_unlocked_tokens(self) -> set[str]:
        jar = SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", "") or "")
        except Exception:
            return set()
        morsel = jar.get(CW_COOKIE)
        if not morsel:
            return set()
        return {t for t in str(morsel.value or "").split(".") if t and t.isalnum()}

    def cw_cookie_header(self, tokens: set[str], *, clear: bool = False) -> str:
        if clear or not tokens:
            return f"{CW_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
        # stable order, cap length
        joined = ".".join(sorted(tokens)[-24:])
        return (
            f"{CW_COOKIE}={joined}; Path=/; Max-Age={CW_COOKIE_MAX_AGE}; "
            "HttpOnly; SameSite=Lax"
        )

    def send_redirect(self, location: str, *, set_cookies: list[str] | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        for raw in set_cookies or []:
            if raw:
                self.send_header("Set-Cookie", raw)
        self.end_headers()

    def maybe_send_codeword_gate(self, target: Path, rel: str) -> bool:
        """If this place is locked and cookie lacks the unlock, send gate HTML. True = gated."""
        lock = find_codeword_lock(target)
        if not lock:
            return False
        shell_rel, codeword = lock
        host = active_host()
        token = cw_token(host, shell_rel, codeword)
        if token in self.cw_unlocked_tokens():
            return False
        title = "locked"
        self.send_html(
            codeword_gate_page(
                title=title, rel=rel, wrong=False, here=target, shell_rel=shell_rel
            )
        )
        return True

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
        name = name.replace("\\", "/").lstrip("/")
        if ".." in name.split("/"):
            self.send_error(404)
            return
        # local font files: /styles/fonts/Name.ttf
        if name.lower().startswith("fonts/"):
            font_name = name.split("/", 1)[1]
            if "/" in font_name or "\\" in font_name:
                self.send_error(404)
                return
            ext = Path(font_name).suffix.lower()
            mime = {
                ".ttf": "font/ttf",
                ".otf": "font/otf",
                ".woff": "font/woff",
                ".woff2": "font/woff2",
            }.get(ext)
            if not mime:
                self.send_error(404)
                return
            target = (STYLES / "fonts" / font_name).resolve()
            try:
                target.relative_to((STYLES / "fonts").resolve())
            except ValueError:
                self.send_error(404)
                return
            if not target.is_file():
                self.send_error(404)
                return
            self.send_bytes(target.read_bytes(), mime)
            return
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

        if u.path == "/api/codelook":
            qs = parse_qs(u.query)
            host_name, rel = parse_request_pocket(qs)
            code_q = unquote((qs.get("code") or [""])[0]).strip()
            host = get_host(host_name) if host_name else None
            if host is None and not host_name:
                host = codes_host()
            if host is None:
                self.send_bytes(
                    b'<div class="codelook taglook-empty">unknown host</div>',
                    "text/html; charset=utf-8",
                    404,
                )
                return
            with using_host(host):
                target = safe_rel(rel) if rel else None
                meta: dict = {}
                if target is not None and target.is_file():
                    try:
                        raw = target.read_text(encoding="utf-8", errors="replace")
                        meta, _body = parse_fm(raw)
                    except OSError:
                        meta = {}
                elif target is not None and target.is_dir():
                    shell = shell_path(target)
                    if shell.is_file():
                        try:
                            raw = shell.read_text(encoding="utf-8", errors="replace")
                            meta, _body = parse_fm(raw)
                        except OSError:
                            meta = {}
                gate_target = target if target is not None else active_vault()
                lock = find_codeword_lock(gate_target)
                if lock:
                    shell_rel, codeword = lock
                    token = cw_token(active_host(), shell_rel, codeword)
                    if token not in self.cw_unlocked_tokens():
                        self.send_bytes(
                            b'<div class="codelook taglook-empty">locked</div>',
                            "text/html; charset=utf-8",
                            403,
                        )
                        return
                if code_q:
                    meta = dict(meta or {})
                    meta["code"] = code_q
                    if not str(meta.get("kind") or "").strip():
                        meta["kind"] = "code"
                html_out = code_look_block(rel or "", meta)
                if not html_out:
                    html_out = (
                        '<div class="codelook taglook-empty">'
                        "nothing has cited this address yet</div>"
                    )
                self.send_bytes(
                    html_out.encode("utf-8"),
                    "text/html; charset=utf-8",
                )
            return

        if u.path == "/api/been":
            self.send_bytes(
                json.dumps({"been": been_load()}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/jumps":
            disk, jumps = jumps_load()
            self.send_bytes(
                json.dumps({"jumps": jumps, "disk": disk}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/last":
            self.send_bytes(
                json.dumps({"href": last_load()}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/hosts":
            qs = parse_qs(u.query)
            host = unquote((qs.get("host") or qs.get("h") or [""])[0])
            code, obj, err = hosts_get(host)
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
            return
        if u.path == "/api/crates/search":
            qs = parse_qs(u.query)
            q = unquote((qs.get("q") or qs.get("query") or [""])[0])
            mode = unquote((qs.get("mode") or ["all"])[0])
            lim_raw = (qs.get("limit") or qs.get("n") or ["40"])[0]
            try:
                lim = int(lim_raw or 40)
            except (TypeError, ValueError):
                lim = 40
            code, obj, err = crates_search(q, lim, mode)
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
            return
        if u.path == "/api/templates":
            self.send_bytes(
                json.dumps({"templates": templates_list()}).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return
        if u.path == "/api/help":
            qs = parse_qs(u.query)
            page = unquote((qs.get("page") or qs.get("p") or [""])[0])
            code, obj, err = help_get(page)
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
        if u.path in ("/api/librarian/lore", "/api/detective/lore", "/api/agent/lore", "/api/charlie/lore", "/api/tps/lore"):
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
        if u.path in ("/api/librarian/suggest", "/api/detective/suggest", "/api/agent/suggest", "/api/charlie/suggest"):
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
        if u.path == "/api/cards/lore":
            qs = parse_qs(u.query)
            faces_raw = (qs.get("faces") or qs.get("face") or ["0"])[0]
            faces = str(faces_raw).strip().lower() in ("1", "true", "yes", "on")
            code, obj, err = cards_lore_list(faces=faces)
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
        if u.path == "/api/cards/search":
            qs = parse_qs(u.query)
            q = unquote((qs.get("q") or qs.get("lore") or qs.get("query") or [""])[0])
            hits = lore_search_notes(q)
            self.send_bytes(
                json.dumps({"q": q, "hits": hits, "n": len(hits)}).encode("utf-8"),
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
        if u.path.startswith("/h/"):
            raw = unquote(u.path[len("/h/") :]).strip("/")
            name, path = split_pocket(raw)
            html_host = get_host(name)
            if html_host is None:
                self.send_error(404)
                return
            with using_host(html_host):
                target = safe_rel(path)
                suf = target.suffix.lower() if target is not None else ""
                if (
                    target is None
                    or not target.is_file()
                    or suf not in HTML_ASSET_TYPE
                ):
                    self.send_error(404)
                    return
                if self.maybe_send_codeword_gate(target, path):
                    return
                try:
                    n = target.stat().st_size
                except OSError:
                    self.send_error(404)
                    return
                if n > HTML_ASSET_MAX:
                    self.send_error(413)
                    return
                ctype = HTML_ASSET_TYPE[suf]
                blob = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(blob)
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
            house = mouth_canon(house) if house in MOUTH_CANON else house
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
            # Hash/tag wiki jumps -> go.tags/{word} (not Charlie report).
            if "h" not in qs and "p" not in qs:
                dest = tag_page_href(word)
                self.send_response(302)
                self.send_header("Location", dest)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
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
            hunt_tok = None
            lore_tok = None
            era_tok = None
            people_tok = None
            if host.name == "detective":
                q = unquote((qs.get("hunt") or qs.get("q") or [""])[0]).strip()
                hunt_tok = _HUNT_Q.set(q)
            elif host.name == "librarian":
                q = unquote((qs.get("blot") or qs.get("q") or [""])[0]).strip()
                hunt_tok = _HUNT_Q.set(q)
            if host.name == "era" or host.name == EVENT_HOST_SLUG:
                eq = unquote(
                    (qs.get("event") or qs.get("era") or qs.get("q") or [""])[0]
                ).strip()
                era_tok = _ERA_Q.set(eq)
            if host.name == PEOPLE_HOST_SLUG:
                pq = unquote(
                    (qs.get("people") or qs.get("kven") or qs.get("person") or qs.get("q") or [""])[0]
                ).strip()
                people_tok = _PEOPLE_Q.set(pq)
            lq = unquote((qs.get("lore") or [""])[0]).strip()
            if lq:
                lore_tok = _LORE_Q.set(lq)
            try:
                self.serve_vault(qs, rel)
            finally:
                if hunt_tok is not None:
                    _HUNT_Q.reset(hunt_tok)
                if era_tok is not None:
                    _ERA_Q.reset(era_tok)
                if people_tok is not None:
                    _PEOPLE_Q.reset(people_tok)
                if lore_tok is not None:
                    _LORE_Q.reset(lore_tok)

    def serve_vault(self, qs: dict, rel: str) -> None:
        # Soft clear: /?h=…&p=…&cw=clear drops unlock cookie for this browser.
        cw_q = str((qs.get("cw") or qs.get("codeword") or [""])[0]).strip().lower()
        if cw_q in ("clear", "lock", "reset", "forget"):
            loc = page_href(rel)
            # rebuild without cw=
            pairs = [(k, v) for k, vs in qs.items() for v in vs if k not in ("cw", "codeword")]
            # page_href already encodes host+path; just redirect clean
            self.send_redirect(loc, set_cookies=[self.cw_cookie_header(set(), clear=True)])
            return
        if active_host() == TAGS_HOST_SLUG:
            touch = (qs.get("touch") or [""])[0].strip()
            if touch:
                dest = ensure_tag_page(touch)
                if dest is not None:
                    self.send_response(302)
                    self.send_header("Location", tag_page_href(touch))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    return
            rel_n = (rel or "").replace(chr(92), "/").strip("/")
            if rel_n.lower().endswith(".md") and "/" not in rel_n:
                target = active_vault() / rel_n
                if not target.is_file():
                    ensure_tag_page(Path(rel_n).stem)
        if on_codes_host():
            touch = (qs.get("touch") or [""])[0].strip()
            if touch:
                dest = ensure_code_chain(touch)
                if dest is not None:
                    self.send_response(302)
                    self.send_header("Location", chip_code_href(touch))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    return
            rel_n = (rel or "").replace(chr(92), "/").strip("/")
            code = chip_code_from_rel(rel_n)
            if code and code_is_held(code):
                ensure_code_chain(code)
                want, _is_dir = chip_code_rel(code)
                got = rel_n.replace("\\", "/").strip("/")
                if want and got != want:
                    self.send_response(302)
                    self.send_header("Location", chip_code_href(code))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    return
        if "q" in qs and "hunt" not in qs and "lore" not in qs and "era" not in qs:
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
                root = active_vault()
                if self.maybe_send_codeword_gate(root, ""):
                    return
                self.send_html(self.index())
                self.remember_desk()
                return
        else:
            target = safe_rel(rel)
            rel_l = rel.lower()
            if (target is None or not target.exists()) and not rel_l.endswith(".md"):
                alt = safe_rel(rel + ".md")
                if alt is not None and alt.exists():
                    target = alt
                    rel = rel + ".md"
            if (target is None or not target.exists()) and not rel_l.endswith((".md", ".chip")):
                alt = safe_rel(rel + ".chip")
                if alt is not None and alt.exists():
                    target = alt
                    rel = rel + ".chip"
        if target is None or not target.exists():
            self.send_html(page("missing", "<p>gone.</p>", "#6e6254", rel, pocket_bar(rel), librarian=False), 404)
            return
        if target.is_file() and target.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
            parent = target.parent
            if self.maybe_send_codeword_gate(parent, "" if is_vault_root(parent) else parent.relative_to(active_vault()).as_posix()):
                return
            self.send_html(self.index() if is_vault_root(parent) else self.listing(parent))
            self.remember_desk()
            return
        if target.is_dir():
            if self.maybe_send_codeword_gate(target, rel):
                return
            self.send_html(self.listing(target))
            self.remember_desk()
            return
        if target.suffix.lower() in {".md", ".chip"}:
            is_chip = target.suffix.lower() == ".chip"
            if self.maybe_send_codeword_gate(target, rel):
                return
            sight_stage(target)
            if not target.is_file():
                self.send_html(page("gone", "<p>this chip is not cited in the pocket anymore.</p>", "#6e6254", rel, pocket_bar(rel), librarian=False), 404)
                return
            text = target.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_fm(text)
            accent = accent_for(rel, meta)
            inner = fill_slots(
                md_lite(body), target.parent, auto=False, crumb_rel=rel, meta=meta
            )
            inner = wear_compost_message(inner, meta, rel)
            inner = fill_uses(inner, target.stem, target)
            if str(meta.get("kind") or "").strip().lower() in ("hunt", "blot"):
                rec = hunt_record(target)
                if rec:
                    inner = wrap_hunt_open_page(inner, rec)
            # Picture-led Obsidian notes (banner:/cover:) still show art when the
            # shell has no {{cover}} slot â€” common under ~hosts/terminals/AB.
            if (
                not is_chip
                and cover_name(meta)
                and "{{cover}}" not in body
                and "{{jacket}}" not in body
                and "jacket-art" not in inner
                and 'class="jacket"' not in inner
            ):
                lead = jacket_block(meta)
                if lead:
                    inner = lead + inner
            wrapped, shell_meta = wrap_in_shell(target.parent, inner, rel, meta)
            env = dress_environment(target, meta, shell_meta)
            extras = None
            if shell_meta:
                extras = ["/index.css"] if (SYS / "index.css").is_file() else None
            crumb = folder_crumbs(rel)
            card = False if is_chip else is_card_note(meta)
            if card:
                env = env or "lorecard"
            strip = css_hex(card_strip_color(meta)) if card else ""
            if card:
                wrapped = stamp_lorecard_strip(wrapped, meta)
                wrapped = wrap_tray_room(wrapped, target, meta)
            tray_room = card and tray_mouth_of(target)
            body_class = "is-lorecard" if card else ""
            if is_chip:
                body_class = (body_class + " is-chip-guest").strip()
            if tray_room:
                body_class = (body_class + " is-tray-room").strip()
            mark = "mypi:card" if card else "mypi:go"
            if is_lobby() and target.name.lower() == START_NAME:
                body_class = (body_class + " is-start").strip()
                mark = "mypi:start"
            elif is_lobby() and target.name.lower() == RECENT_NAME:
                body_class = (body_class + " is-recent").strip()
                mark = "mypi:recent"
            elif is_lobby() and target.name.lower() == ROAM_NAME:
                body_class = (body_class + " is-start is-roam").strip()
                mark = "mypi:roam"
            title = str(meta.get("title") or target.stem)
            if is_chip:
                title = str(chip_peek(target).get("name") or "").strip() or title
            self.send_html(
                page(
                    title,
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
                    stamps=page_marks_html(meta),
                )
            )
            self.remember_desk()
            return
        if is_html_guest_path(target):
            if self.maybe_send_codeword_gate(target, rel):
                return
            sight_stage(target)
            inner = html_guest_inner(rel, target.name)
            wrapped, shell_meta = wrap_in_shell(target.parent, inner, rel, {})
            env = dress_environment(target, {}, shell_meta)
            extras = None
            if shell_meta:
                extras = ["/index.css"] if (SYS / "index.css").is_file() else None
            crumb = folder_crumbs(rel)
            self.send_html(
                page(
                    target.name,
                    wrapped,
                    accent_for(rel, {}),
                    crumb,
                    pocket_bar(rel),
                    env,
                    extras,
                    here=target.parent,
                    vault=pocket_key(target),
                    body_class="is-chip-guest is-html-guest",
                    mark="mypi:go",
                )
            )
            self.remember_desk()
            return
        if is_text_guest_path(target):
            if self.maybe_send_codeword_gate(target, rel):
                return
            sight_stage(target)
            inner = text_guest_inner(target)
            wrapped, shell_meta = wrap_in_shell(target.parent, inner, rel, {})
            env = dress_environment(target, {}, shell_meta)
            extras = None
            if shell_meta:
                extras = ["/index.css"] if (SYS / "index.css").is_file() else None
            crumb = folder_crumbs(rel)
            self.send_html(
                page(
                    target.name,
                    wrapped,
                    accent_for(rel, {}),
                    crumb,
                    pocket_bar(rel),
                    env,
                    extras,
                    here=target.parent,
                    vault=pocket_key(target),
                    body_class="is-chip-guest is-text-guest",
                    mark="mypi:go",
                )
            )
            self.remember_desk()
            return
        if target.suffix.lower() == ".canvas":
            if self.maybe_send_codeword_gate(target, rel):
                return
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
        # Soft codeword unlock — form POST back to the pocket URL (not /api).
        if u.path in ("/", ""):
            qs = parse_qs(u.query)
            try:
                n = int(self.headers.get("Content-Length", "0") or 0)
            except ValueError:
                n = 0
            if 0 < n <= 8_000:
                raw = self.rfile.read(n)
                ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                form: dict = {}
                if ctype in ("", "application/x-www-form-urlencoded"):
                    try:
                        form = parse_qs(raw.decode("utf-8", errors="replace"))
                    except Exception:
                        form = {}
                if form.get("cw_unlock") or "codeword" in form:
                    host_name, rel = parse_request_pocket(qs)
                    host = get_host(host_name)
                    if host is None:
                        self.send_html(missing_host_page(host_name), 404)
                        return
                    guess = unquote((form.get("codeword") or form.get("password") or form.get("lock") or form.get("code") or [""])[0]).strip()
                    with using_host(host):
                        if not rel:
                            target = active_vault()
                        else:
                            target = safe_rel(rel)
                            if target is None:
                                self.send_html(
                                    page("missing", "<p>gone.</p>", "#6e6254", rel, pocket_bar(rel), librarian=False),
                                    404,
                                )
                                return
                            if target.is_file() and target.name.lower() in {INDEX_NAME, INDEX_LEGACY, PAPER_NAME}:
                                target = target.parent
                        lock = find_codeword_lock(target)
                        if not lock:
                            self.send_redirect(page_href(rel, is_dir=target.is_dir() if target else False))
                            return
                        shell_rel, codeword = lock
                        if guess == codeword:
                            tokens = self.cw_unlocked_tokens()
                            tokens.add(cw_token(active_host(), shell_rel, codeword))
                            loc = page_href(
                                rel,
                                is_dir=bool(target and target.is_dir()),
                            )
                            self.send_redirect(
                                loc,
                                set_cookies=[self.cw_cookie_header(tokens)],
                            )
                            return
                        self.send_html(
                            codeword_gate_page(
                                title="locked",
                                rel=rel,
                                wrong=True,
                                here=target,
                                shell_rel=shell_rel,
                            )
                        )
                        return
        if u.path == "/api/insert":
            ctype = (self.headers.get("Content-Type") or "").lower()
            if "json" in ctype:
                data, status = self.read_json_body({})
            else:
                try:
                    n = int(self.headers.get("Content-Length", "0") or 0)
                except ValueError:
                    n = 0
                if n < 0 or n > 200_000:
                    self.send_error(413)
                    return
                raw = self.rfile.read(n).decode("utf-8", "replace") if n else ""
                parsed = parse_qs(raw)
                data = {}
                fields = {}
                for k, vs in parsed.items():
                    v = vs[-1] if vs else ""
                    if k.startswith("f_"):
                        fields[k[2:]] = v
                    else:
                        data[k] = v
                data["fields"] = fields
                status = 200
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = insert_post(data)
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
            return
        if u.path == "/api/rom-launch":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            result = launch_rom(str(data.get("id") or data.get("rom") or ""))
            self.send_bytes(
                json.dumps(result).encode("utf-8"),
                "application/json; charset=utf-8",
                200 if result.get("ok") else 400,
            )
            return
        if u.path == "/api/templates/apply":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                data = {}
            if not isinstance(data, dict):
                data = {}
            code, obj, err = templates_apply(
                str(data.get("pocket") or data.get("p") or ""),
                str(data.get("template") or data.get("id") or ""),
                str(data.get("mode") or "overwrite"),
                str(data.get("env") or data.get("environment") or ""),
                str(data.get("title") or ""),
            )
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
            return
        if u.path == "/api/hosts":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            title = str(data.get("title") or data.get("name") or "").strip()
            slug = str(data.get("slug") or data.get("host") or data.get("go") or "").strip()
            kind = str(data.get("kind") or "go").strip().lower()
            if kind == "roam":
                code, obj, err = hosts_roam_connect(
                    slug,
                    str(data.get("source") or data.get("path") or data.get("folder") or ""),
                    title,
                    str(data.get("environment") or data.get("env") or ""),
                )
            else:
                code, obj, err = hosts_create(title, slug, str(data.get("template") or data.get("layout") or ""))
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
            return
        if u.path in ("/api/readme", "/api/rules"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            what = str(data.get("what") or "").strip().lower()
            if what == "rename":
                code, obj, err = readme_note_rename(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or data.get("name") or data.get("leaf") or ""),
                    str(data.get("which") or data.get("kind") or ""),
                )
            elif what == "folder":
                code, obj, err = readme_folder_add(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or data.get("name") or data.get("leaf") or ""),
                )
            elif what in ("folder-rename", "rename-folder", "rename_folder"):
                code, obj, err = readme_folder_rename(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or data.get("name") or data.get("leaf") or ""),
                )
            elif what == "shell":
                code, obj, err = readme_shell_add(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or data.get("name") or data.get("leaf") or ""),
                )
            elif what in ("letter", "readme"):
                code, obj, err = readme_letter_add(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or data.get("name") or data.get("leaf") or ""),
                )
            else:
                code, obj, err = readme_note_add(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or data.get("name") or data.get("leaf") or ""),
                )
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/cards/lore/faces":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            items = data.get("crates") or data.get("cards") or data.get("items") or []
            if not isinstance(items, list):
                items = []
            code, obj, err = cards_lore_faces(items)
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/cards/lore/attach":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = cards_lore_attach(
                str(data.get("pocket") or ""),
                str(data.get("crate") or data.get("card") or ""),
                str(data.get("mouth") or data.get("house") or ""),
                str(data.get("onto") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/cards/lore/sync":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            attach_list = data.get("attach") or data.get("add") or []
            detach_list = data.get("detach") or data.get("remove") or []
            if not isinstance(attach_list, list):
                attach_list = []
            if not isinstance(detach_list, list):
                detach_list = []
            code, obj, err = cards_lore_sync(
                str(data.get("pocket") or ""),
                attach_list,
                detach_list,
                str(data.get("onto") or ""),
            )
            self.send_blot(code, obj, err)
            return
        if u.path in (
            "/api/librarian/lore/attach",
            "/api/detective/lore/attach",
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
        if u.path in ("/api/librarian/lore", "/api/detective/lore", "/api/agent/lore", "/api/charlie/lore", "/api/tps/lore"):
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
        if u.path in ("/api/detective/hunt", "/api/librarian/blot"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            bank = "librarian" if u.path.endswith("/blot") else "detective"
            crate = str(data.get("crate") or data.get("slip") or "")
            if crate.strip():
                code, obj, err = hunt_save(
                    str(data.get("pocket") or ""),
                    crate,
                    str(data.get("title") or ""),
                    str(data.get("body") or data.get("thought") or ""),
                    str(data.get("mindset") or data.get("mind") or ""),
                    bank,
                )
            else:
                code, obj, err = hunt_add(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or ""),
                    str(data.get("body") or data.get("thought") or ""),
                    str(data.get("mindset") or data.get("mind") or ""),
                    bank,
                )
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/tps/era" or u.path == "/api/tps/event":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            crate = str(data.get("crate") or data.get("slip") or "")
            sit = str(
                data.get("perspective")
                or data.get("sit")
                or data.get("era")
                or ""
            )
            code = str(data.get("code") or data.get("event") or "")
            if crate.strip():
                code_n, obj, err = era_save(
                    str(data.get("pocket") or ""),
                    crate,
                    str(data.get("title") or ""),
                    str(data.get("body") or data.get("thought") or ""),
                    sit,
                    code,
                )
            else:
                code_n, obj, err = era_add(
                    str(data.get("pocket") or ""),
                    str(data.get("title") or ""),
                    str(data.get("body") or data.get("thought") or ""),
                    sit,
                    code,
                )
            self.send_blot(code_n, obj, err)
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
        if u.path == "/api/table":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            idx = data.get("i") if data.get("i") is not None else data.get("index")
            code, obj, err = table_put(
                str(data.get("pocket") or ""),
                idx,
                str(data.get("markdown") or data.get("table") or data.get("md") or ""),
            )
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
        if u.path == "/api/jumps":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            saved = jumps_save(data)
            self.send_bytes(
                json.dumps({"jumps": saved, "disk": True}).encode("utf-8"),
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
        if u.path in ("/api/detective/hunt", "/api/librarian/blot"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            bank = "librarian" if u.path.endswith("/blot") else "detective"
            code, obj, err = hunt_save(
                str(data.get("pocket") or ""),
                str(data.get("crate") or data.get("slip") or ""),
                str(data.get("title") or ""),
                str(data.get("body") or data.get("thought") or ""),
                str(data.get("mindset") or data.get("mind") or ""),
                bank,
            )
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/tps/era" or u.path == "/api/tps/event":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            sit = str(
                data.get("perspective")
                or data.get("sit")
                or data.get("era")
                or ""
            )
            code = str(data.get("code") or data.get("event") or "")
            code_n, obj, err = era_save(
                str(data.get("pocket") or ""),
                str(data.get("crate") or data.get("slip") or ""),
                str(data.get("title") or ""),
                str(data.get("body") or data.get("thought") or ""),
                sit,
                code,
            )
            self.send_blot(code_n, obj, err)
            return
        if u.path == "/api/hosts":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = hosts_put(data)
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
            return
        if u.path == "/api/help":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            page = str(data.get("page") or data.get("slug") or "").strip()
            body = str(data.get("body") or "")
            code, obj, err = help_put(page, body)
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
            return
        if u.path in ("/api/readme", "/api/rules"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            what = str(data.get("what") or data.get("face") or "room").strip().lower()
            if what == "coat":
                css_body = data.get("css")
                if css_body is None:
                    css_body = data.get("body")
                if css_body is None:
                    css_body = data.get("leaf") or ""
                code, obj, err = readme_coat_put(
                    str(data.get("pocket") or ""),
                    str(css_body),
                    str(data.get("which") or data.get("source") or ""),
                )
            elif what == "page":
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
        if u.path in ("/api/librarian/lore", "/api/detective/lore", "/api/agent/lore", "/api/charlie/lore", "/api/tps/lore"):
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
        if u.path in ("/api/detective/hunt", "/api/librarian/blot"):
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            bank = "librarian" if u.path.endswith("/blot") else "detective"
            code, obj, err = hunt_drop(
                str(data.get("pocket") or ""),
                str(data.get("crate") or data.get("slip") or ""),
                bank,
            )
            self.send_blot(code, obj, err)
            return
        if u.path == "/api/tps/era" or u.path == "/api/tps/event":
            data, status = self.read_json_body({})
            if status != 200:
                self.send_error(status)
                return
            if not isinstance(data, dict):
                self.send_error(400)
                return
            code, obj, err = era_drop(
                str(data.get("pocket") or ""),
                str(data.get("crate") or data.get("slip") or ""),
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
