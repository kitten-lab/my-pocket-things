#!/usr/bin/env python3
"""My Pocket Go — early internet in WWW chrome. Edit in Obsidian, refresh here."""

from __future__ import annotations

import html
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

SYS = Path(__file__).resolve().parent
ROOT = SYS.parents[1]  # pocket-go/
STYLES = SYS / "styles"
HOST = "127.0.0.1"
PORT = int(os.environ.get("GO_PORT", os.environ.get("LIBRARY_PORT", "43210")))
SKU = "CO.MYPT-004-GO"
SKIP = {".obsidian", ".agents", ".claude", ".opencode", ".git", "~reader"}
ENV_NAME = re.compile(r"^[A-Za-z0-9_-]+$")

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
}


def worlds() -> list[Path]:
    if not VAULT.is_dir():
        return []
    out = []
    for p in sorted(VAULT.iterdir(), key=lambda x: x.name.lower()):
        if p.is_dir() and p.name not in SKIP and not p.name.startswith("."):
            out.append(p)
    return out


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


def pocket_bar(rel: str, is_dir: bool = False) -> str:
    if not rel:
        return "/"
    p = "/" + rel.replace("\\", "/").strip("/")
    if is_dir:
        p += "/"
    return p


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


def md_lite(src: str) -> str:
    lines = src.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        para = " ".join(buf)
        out.append("<p>" + inline(para) + "</p>")
        buf.clear()

    def inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(
            r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
            lambda m: f'<a class="wiki" href="/?q={html.escape(m.group(1), True)}">{html.escape(m.group(2) or m.group(1))}</a>',
            s,
        )
        return s

    for line in lines:
        if line.startswith("#"):
            flush()
            n = len(line) - len(line.lstrip("#"))
            n = min(max(n, 1), 5)
            out.append(f"<h{n}>" + inline(line[n:].strip()) + f"</h{n}>")
        elif line.strip() == "---":
            flush()
            out.append("<hr>")
        elif line.startswith("|"):
            flush()
            out.append("<pre class='tbl'>" + html.escape(line) + "</pre>")
        elif re.match(r"^[-*]\s+", line):
            flush()
            out.append("<li>" + inline(re.sub(r"^[-*]\s+", "", line)) + "</li>")
        elif not line.strip():
            flush()
        else:
            buf.append(line)
    flush()
    return "\n".join(out)


def find_note(title: str) -> str | None:
    if not VAULT.is_dir():
        return None
    needle = title.strip().lower()
    hits: list[Path] = []
    for p in VAULT.rglob("*.md"):
        if any(part in SKIP for part in p.relative_to(VAULT).parts):
            continue
        if p.stem.lower() == needle or p.stem.lower().startswith(needle):
            hits.append(p)
    if not hits:
        return None
    rel = hits[0].relative_to(VAULT).as_posix()
    return "/?p=" + rel


def page(
    title: str,
    body: str,
    accent: str,
    crumb: str,
    bar: str = "/",
    environment: str | None = None,
) -> bytes:
    skin = env_name(environment)
    extra = ""
    if skin:
        extra = f'<link rel="stylesheet" href="/styles/{html.escape(skin, True)}.css">\n'
    html_out = f"""<!doctype html>
<html lang="en" data-pocket="{html.escape(bar, True)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · pocket-go</title>
<link rel="stylesheet" href="/www.css">
<link rel="stylesheet" href="/dress.css">
<style>:root {{ --accent: {accent}; }}</style>
{extra}</head>
<body>
<header class="wwwExplorer_chrome" data-deck-chrome>
  <div class="wwwExplorer_windowTitleBar" data-deck-drag>
    <span class="wwwExplorer_mark" data-deck-menu title="Menu">&gt;| WWW</span>
    <span class="wwwExplorer_title">{html.escape(title)}</span>
    <div class="wwwExplorer_win" data-deck-window-controls aria-label="Window"></div>
  </div>
  <div class="wwwExplorer_linkBar">
    <button type="button" data-webbar="back">back</button>
    <button type="button" data-webbar="forward">forward</button>
    <button type="button" id="REFRESH" data-webbar="refresh"
            title="Shift/Ctrl+click = hard refresh">refresh</button>
    <span id="wwwBar" class="linkSlug" contenteditable="true" spellcheck="false">{html.escape(bar)}</span>
    <button type="button" id="GO" data-webbar="go">GO!</button>
  </div>
</header>
<div class="wwwExplorer_innerShell">
  <nav class="crumb">{crumb}</nav>
  <main id="browserWindow">
{body}
  </main>
</div>
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
            dest = find_note(qs["q"][0])
            self.send_response(302)
            self.send_header("Location", dest or "/")
            self.end_headers()
            return
        rel = unquote(qs.get("p", [""])[0]).strip("/")
        if not rel:
            self.send_html(self.index())
            return
        target = safe_rel(rel)
        if target is None or not target.exists():
            self.send_html(page("missing", "<p>gone.</p>", "#6e6254", rel, pocket_bar(rel)), 404)
            return
        if target.is_dir():
            self.send_html(self.listing(target))
            return
        if target.suffix.lower() == ".md":
            text = target.read_text(encoding="utf-8", errors="replace")
            meta, body = parse_fm(text)
            accent = accent_for(rel, meta)
            bits = []
            if meta:
                rows = "".join(
                    f"<div><dt>{html.escape(k)}</dt><dd>{html.escape(str(v))}</dd></div>"
                    for k, v in meta.items()
                )
                bits.append(f"<dl class='fm'>{rows}</dl>")
            bits.append(md_lite(body))
            crumb = " / ".join(
                f'<a href="/?p={html.escape("/".join(Path(rel).parts[: i + 1]), True)}">{html.escape(part)}</a>'
                for i, part in enumerate(Path(rel).parts)
            )
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

    def index(self) -> bytes:
        cards = []
        for w in worlds():
            n = sum(1 for _ in w.rglob("*.md") if "~reader" not in _.parts)
            accent = accent_for(w.name, {})
            cards.append(
                f'<a class="world" href="/?p={html.escape(w.name, True)}" style="--accent:{accent}">'
                f"<strong>{html.escape(w.name)}</strong><span>{n} notes</span></a>"
            )
        body = "<h1>worlds</h1><div class='worlds'>" + "".join(cards) + "</div>"
        if not cards:
            body = "<h1>worlds</h1><p>vault is empty — drop notes in ~library.</p>"
        return page("worlds", body, "#6e6254", "home", "/")

    def listing(self, folder: Path) -> bytes:
        rel = folder.relative_to(VAULT).as_posix()
        items = []
        for p in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if p.name in SKIP or p.name.startswith("."):
                continue
            if p.is_dir() or p.suffix.lower() == ".md":
                r = p.relative_to(VAULT).as_posix()
                mark = "/" if p.is_dir() else ""
                items.append(
                    f'<li><a href="/?p={html.escape(r, True)}">{html.escape(p.name)}{mark}</a></li>'
                )
        crumb = " / ".join(
            f'<a href="/?p={html.escape("/".join(Path(rel).parts[: i + 1]), True)}">{html.escape(part)}</a>'
            for i, part in enumerate(Path(rel).parts)
        )
        body = f"<h1>{html.escape(folder.name)}</h1><ul class='dir'>{''.join(items)}</ul>"
        return page(folder.name, body, accent_for(rel, {}), crumb, pocket_bar(rel, True))


if __name__ == "__main__":
    print(f"pocket-go  http://{HOST}:{PORT}/   vault={VAULT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
