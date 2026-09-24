# -*- coding: utf-8 -*-
import pathlib, shutil, time, urllib.request

root = pathlib.Path(r"C:/ALICE_BOX/my-pocket-things/pocket-go/prod/www_sys")
js_path = root / "librarian.js"
css_path = root / "librarian.css"
ts = time.strftime("%Y%m%d-%H%M%S")

for p in (js_path, css_path):
    bak = p.with_name(p.name + f".bak-quire-seal-{ts}")
    shutil.copy2(p, bak)
    print("bak", bak.name)

js = js_path.read_text(encoding="utf-8")
old = (
    "          : '<div class=\"librarian-head\">' +\n"
    "            '<div class=\"librarian-mast\">' +\n"
    "            \"<strong>\" +\n"
    "            escapeHtml(cfg.title) +\n"
    "            \"</strong>\" +\n"
    "            \"</div>\" +"
)
new = (
    "          : '<div class=\"librarian-head\">' +\n"
    "            '<div class=\"librarian-mast\">' +\n"
    "            (cfg.id === \"librarian\"\n"
    "              ? '<img class=\"librarian-seal\" src=\"/i/quire-librarian-seal.png\" alt=\"\" width=\"40\" height=\"40\">'\n"
    "              : \"\") +\n"
    "            \"<strong>\" +\n"
    "            escapeHtml(cfg.title) +\n"
    "            \"</strong>\" +\n"
    "            \"</div>\" +"
)
if old not in js:
    # try softer find
    needle = "'<div class=\"librarian-mast\">'"
    if needle not in js:
        raise SystemExit("mast not found")
    print("exact old miss — using index splice")
    i = js.find(
        "          : '<div class=\"librarian-head\">' +\n"
        "            '<div class=\"librarian-mast\">' +\n"
        "            \"<strong>\" +"
    )
    if i < 0:
        raise SystemExit("splice anchor miss")
    # insert seal line after mast open
    insert_at = js.find("'<div class=\"librarian-mast\">' +", i)
    insert_at = js.find("\n", insert_at) + 1
    seal_lines = (
        "            (cfg.id === \"librarian\"\n"
        "              ? '<img class=\"librarian-seal\" src=\"/i/quire-librarian-seal.png\" alt=\"\" width=\"40\" height=\"40\">'\n"
        "              : \"\") +\n"
    )
    js = js[:insert_at] + seal_lines + js[insert_at:]
else:
    js = js.replace(old, new, 1)
    print("exact replace ok")

js_path.write_text(js, encoding="utf-8")
print("js", js_path.stat().st_size, "seal" , "librarian-seal" in js)

css = css_path.read_text(encoding="utf-8")
marker = "/* —— Quire librarian seal sticker —— */"
if marker in css:
    css = css.split(marker)[0].rstrip() + "\n"

extra = marker + """
.librarian.is-librarian .librarian-seal {
  flex: 0 0 auto;
  width: 2.4rem;
  height: 2.4rem;
  object-fit: contain;
  border-radius: 50%;
  border: 1px solid rgba(196, 165, 116, 0.5);
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.3),
    0 2px 5px rgba(0, 0, 0, 0.35);
  background: #152018;
  transform: rotate(-6deg);
}
.librarian.is-librarian .librarian-mast {
  align-items: center;
  gap: 0.55rem;
}
"""
css_path.write_text(css.rstrip() + "\n\n" + extra + "\n", encoding="utf-8")
print("css", css_path.stat().st_size)
r = urllib.request.urlopen("http://127.0.0.1:43210/i/quire-librarian-seal.png", timeout=5)
print("asset", r.status)
print("DONE", ts)
