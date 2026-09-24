/**
 * Pocket Go webBAR — back / forward / refresh / GO.
 * Address bar shows go.{host}/… for any live host. Folders in ~hosts become doors.
 */

/* soft-nav */
(function () {
  // Soft nav parked 2026-09-13 — FOUC / thrash; back to full page loads.
  // Keep pocketSoftGo so LetsGO + jump chips still navigate (hard assign).
  window.pocketSoftGo = function (href) {
    href = String(href || "").trim();
    if (!href) return;
    window.location.assign(href);
  };
})();
/* /soft-nav */


(function () {
  function barEl() {
    return document.getElementById("wwwBar");
  }

  function pocketPath() {
    var html = document.documentElement;
    var fromDom = (html.getAttribute("data-pocket") || "").trim();
    if (fromDom) return fromDom;
    var q = new URLSearchParams(window.location.search).get("p");
    if (!q) return "/";
    var p = "/" + q.replace(/\\/g, "/").replace(/^\/+/, "");
    return p;
  }

  function displayPath(raw) {
    return String(raw || "").replace(/\.md(\/?)$/i, "$1");
  }

  function paintBar() {
    var el = barEl();
    if (!el) return;
    var raw = pocketPath();
    var shown = displayPath(raw);
    el.setAttribute("data-raw", shown);
    /* never rewrite text while editing — that kills caret/selection */
    if (el.getAttribute("contenteditable") === "true" && document.activeElement === el) {
      return;
    }
    el.removeAttribute("contenteditable");
    el.textContent = shown;
  }

  window.paintBar = paintBar;

  function editBar(opts) {
    var el = barEl();
    if (!el) return;
    opts = opts || {};
    var raw = el.getAttribute("data-raw") || pocketPath();
    var already = el.getAttribute("contenteditable") === "true";
    el.setAttribute("contenteditable", "true");
    if (!already) {
      el.textContent = raw;
    }
    if (opts.focus !== false) {
      try {
        el.focus({ preventScroll: true });
      } catch (e0) {
        el.focus();
      }
    }
    /* select-all only when asked (e.g. keyboard focus) — never on every click */
    if (opts.selectAll) {
      try {
        var range = document.createRange();
        range.selectNodeContents(el);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      } catch (e) {}
    }
  }

  window.WWWBack = function WWWBack() {
    if (window.history.length > 1) {
      window.history.go(-1);
    } else {
      window.history.back();
    }
  };

  window.WWWForward = function WWWForward() {
    window.history.go(1);
  };

  window.WWWHome = function WWWHome() {
    window.location.assign("/?home=1");
  };

  window.WWWRefresh = function WWWRefresh() {
    try {
      window.location.reload();
    } catch (e) {
      window.location.href = window.location.href;
    }
  };

  window.WWWReload = window.WWWRefresh;

  function openOutside(href) {
    href = String(href || "").trim();
    if (!/^https?:\/\//i.test(href)) return false;
    var api = window.pywebview && window.pywebview.api;
    if (api && api.open_external) {
      try {
        var ret = api.open_external(href);
        if (ret && typeof ret.then === "function") {
          ret.catch(function () {
            window.open(href, "_blank", "noopener");
          });
        }
      } catch (e) {
        window.open(href, "_blank", "noopener");
      }
      return true;
    }
    window.open(href, "_blank", "noopener");
    return true;
  }

  function launchRom(id, a) {
    id = String(id || "").trim();
    if (!id) return false;
    paintStatus("launching " + id + " in Deck Host");
    if (a) a.classList.add("is-launching");
    fetch("/api/rom-launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: id }),
    })
      .then(function (res) {
        return res.text().then(function (text) {
          var data = {};
          try {
            data = text ? JSON.parse(text) : {};
          } catch (err) {
            data = { error: text || res.statusText };
          }
          return { ok: res.ok && data.ok, data: data };
        });
      })
      .then(function (r) {
        if (a) a.classList.remove("is-launching");
        if (!r.ok) {
          paintStatus((r.data && (r.data.error || r.data.message)) || "launch failed");
          return;
        }
        paintStatus(r.data.message || "opened in Deck Host");
      })
      .catch(function () {
        if (a) a.classList.remove("is-launching");
        paintStatus("launch failed");
      });
    return true;
  }

  window.WWWHardRefresh = function WWWHardRefresh() {
    try {
      var dest = new URL(window.location.href);
      dest.searchParams.set("_cb", String(Date.now()));
      window.location.replace(dest.toString());
    } catch (e) {
      window.location.reload();
    }
  };

  window.LetsGO = function LetsGO() {
    var el = barEl();
    if (!el) return;
    var raw = (el.textContent || el.innerText || "").trim();
    raw = raw.replace(/\u200b/g, "").replace(/\s+/g, " ").trim();
    if (!raw) return;

    if (/^https?:\/\//i.test(raw)) {
      openOutside(raw);
      return;
    }

    var host = "";
    var path = raw;
    var hm = raw.match(/^(?:go|roam)\.([A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?)(\/.*)?$/i);
    if (hm) {
      host = hm[1].toLowerCase();
      path = hm[2] || "/";
      if (host === "roam") {
        window.pocketSoftGo("/?p=roam");
        return;
      }
      if (host === "recent") {
        window.pocketSoftGo("/?p=recent");
        return;
      }
      if (host === "start" || host === "go") {
        window.pocketSoftGo("/?home=1");
        return;
      }
    } else {
      var nicks = window.pocketBarNicks || {};
      var word = raw.replace(/\.md$/i, "").replace(/\/+$/, "").toLowerCase();
      if (raw.indexOf("/") < 0 && nicks[word]) {
        var go = nicks[word];
        if (go === "start" || go === "go") {
          window.pocketSoftGo("/?home=1");
          return;
        }
        if (go === "recent") {
          window.pocketSoftGo("/?p=recent");
          return;
        }
        if (go === "roam") {
          window.pocketSoftGo("/?p=roam");
          return;
        }
        window.pocketSoftGo("/?h=" + encodeURIComponent(go));
        return;
      }
      if (raw.charAt(0) !== "/") {
        path = "/" + raw;
      }
    }

    if (!host) {
      if (path === "/" || path === "" || /^\/?(start|go)(\.md)?\/?$/i.test(path)) {
        window.pocketSoftGo("/?home=1");
        return;
      }
      if (/^\/?roam(\.md)?\/?$/i.test(path)) {
        window.pocketSoftGo("/?p=roam");
        return;
      }
      if (/^\/?recent(\.md)?\/?$/i.test(path)) {
        window.pocketSoftGo("/?p=recent");
        return;
      }
      window.pocketSoftGo("/?p=" + encodeURI(path.replace(/^\/+/, "")));
      return;
    }
    var dest = "/?h=" + encodeURIComponent(host);
    if (path && path !== "/") {
      dest += "&p=" + encodeURI(path.replace(/^\/+/, ""));
    }
    window.pocketSoftGo(dest);
  };

  var el = barEl();
  if (!el) {
    console.warn("webBAR: #wwwBar missing");
    return;
  }

  paintBar();
  window.addEventListener("pageshow", paintBar);

  /* Enable editing on mousedown BEFORE the click so the browser can place the caret
     (or start a drag-select) instead of us select-all'ing the whole URL. */
  el.addEventListener("mousedown", function (e) {
    if (e.button != null && e.button !== 0) return;
    if (el.getAttribute("contenteditable") === "true") return;
    var raw = el.getAttribute("data-raw") || pocketPath();
    el.setAttribute("contenteditable", "true");
    el.textContent = raw;
  });
  el.addEventListener("click", function (e) {
    /* already editable: let native caret / selection stand */
    if (el.getAttribute("contenteditable") === "true") return;
    editBar({ selectAll: false });
  });
  el.addEventListener("focus", function () {
    if (el.getAttribute("contenteditable") === "true") return;
    /* tab-in: edit and select all (keyboard-friendly) */
    editBar({ selectAll: true, focus: false });
  });
  el.addEventListener("keydown", function (event) {
    if (el.getAttribute("contenteditable") !== "true") {
      editBar({ selectAll: false });
    }
    if (event.key === "Enter") {
      event.preventDefault();
      window.LetsGO();
    }
    if (event.key === "Escape") {
      event.preventDefault();
      paintBar();
      el.blur();
    }
  });
  el.addEventListener("blur", function () {
    if (el.getAttribute("contenteditable") === "true") paintBar();
  });

  if (!window.__webbarKeysBound) {
    window.__webbarKeysBound = true;
    window.addEventListener(
      "keydown",
      function (e) {
        var key = e.key || "";
        if (key === "F5" && (e.ctrlKey || e.shiftKey)) {
          e.preventDefault();
          window.WWWHardRefresh();
          return;
        }
        if (key === "F5") {
          e.preventDefault();
          window.WWWRefresh();
          return;
        }
        if ((key === "r" || key === "R") && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          if (e.shiftKey) window.WWWHardRefresh();
          else window.WWWRefresh();
        }
      },
      true
    );
  }

  document.querySelectorAll("[data-webbar]").forEach(function (node) {
    if (node.__webbarDataBound) return;
    node.__webbarDataBound = true;
    var act = (node.getAttribute("data-webbar") || "").toLowerCase();
    node.addEventListener("click", function (e) {
      e.preventDefault();
      if (act === "back") window.WWWBack();
      else if (act === "forward") window.WWWForward();
      else if (act === "home") window.WWWHome();
      else if (act === "hard-refresh" || act === "hardrefresh") window.WWWHardRefresh();
      else if (act === "refresh" || act === "reload") {
        if (e.shiftKey || e.altKey || e.ctrlKey || e.metaKey) window.WWWHardRefresh();
        else window.WWWRefresh();
      } else if (act === "go") window.LetsGO();
    });
  });

  var BEEN_KEY = "pocket-go-been";
  var beenMem = [];
  var beenLoaded = false;

  function beenList() {
    if (beenLoaded) return beenMem;
    try {
      var raw = localStorage.getItem(BEEN_KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function beenSave(arr) {
    if (arr.length > 2000) arr = arr.slice(arr.length - 2000);
    beenMem = arr;
    try {
      localStorage.setItem(BEEN_KEY, JSON.stringify(arr));
    } catch (e) {}
  }

  function beenPush(arr) {
    beenSave(arr);
    if (!beenLoaded) return;
    try {
      var req = new XMLHttpRequest();
      req.open("POST", "/api/been");
      req.setRequestHeader("Content-Type", "application/json");
      req.send(JSON.stringify({ been: arr }));
    } catch (e) {}
  }

  function beenKey(href) {
    try {
      var u = new URL(href, window.location.href);
      u.searchParams.delete("_cb");
      u.hash = "";
      return u.pathname + u.search;
    } catch (e) {
      return href;
    }
  }

  function beenRemember(href) {
    var keys = [beenKey(href)];
    try {
      var u = new URL(href, window.location.href);
      var p = u.searchParams.get("p");
      if (p) {
        var stem = p.replace(/\\/g, "/").split("/").pop().replace(/\.md$/i, "");
        if (stem) keys.push("/?q=" + stem);
      }
    } catch (e) {}
    var arr = beenList().slice();
    var changed = false;
    keys.forEach(function (k) {
      if (k && arr.indexOf(k) < 0) {
        arr.push(k);
        changed = true;
      }
    });
    if (changed) beenPush(arr);
    else beenSave(arr);
    return arr;
  }

  function beenPaint(arr) {
    arr = arr || beenList();
    var shell = document.querySelector(".go-shell");
    if (!shell) return;
    shell.querySelectorAll("a[href]").forEach(function (a) {
      if (arr.indexOf(beenKey(a.href)) >= 0) a.classList.add("been");
    });
  }

  function beenHydrate() {
    var req = new XMLHttpRequest();
    req.open("GET", "/api/been");
    req.onload = function () {
      var disk = [];
      try {
        var data = JSON.parse(req.responseText);
        disk = data.been || [];
      } catch (e) {}
      if (!Array.isArray(disk)) disk = [];
      var local = beenList();
      var merged = disk.slice();
      local.forEach(function (k) {
        if (k && merged.indexOf(k) < 0) merged.push(k);
      });
      beenLoaded = true;
      beenSave(merged);
      beenRemember(window.location.href);
      beenPaint();
      beenPush(beenList());
    };
    req.onerror = function () {
      beenLoaded = true;
      beenRemember(window.location.href);
      beenPaint();
    };
    req.send();
  }

  beenHydrate();
  document.addEventListener(
    "click",
    function (e) {
      var a = e.target && e.target.closest ? e.target.closest("a[href], a[data-rom]") : null;
      if (!a || !a.closest(".go-shell")) return;
      var rom = (a.getAttribute("data-rom") || "").trim();
      if (rom) {
        e.preventDefault();
        launchRom(rom, a);
        return;
      }
      var href = a.getAttribute("href") || "";
      var pic =
        a.classList.contains("pic-zoom") ||
        a.classList.contains("jacket-zoom") ||
        /\/i\//.test(href);
      if (!pic) {
        try {
          var path = new URL(href, window.location.href).pathname;
          pic = /\.(gif|png|jpe?g|webp|svg|bmp|ico)$/i.test(path);
        } catch (err) {
          pic = false;
        }
      }
      if (pic) {
        e.preventDefault();
        if (typeof window.openPocketPic === "function") {
          window.openPocketPic(a.href);
        }
        return;
      }
      var outside =
        a.hasAttribute("data-outlink") ||
        a.classList.contains("outlink") ||
        /^https?:\/\//i.test(href);
      if (outside) {
        e.preventDefault();
        openOutside(href);
        return;
      }
      beenRemember(a.href);
      a.classList.add("been");
    },
    true
  );

  var statusEl = document.getElementById("wwwStatus");
  var STATUS_IDLE = "Done";

  function pocketSpeak(href) {
    try {
      var u = new URL(href, window.location.href);
    } catch (e) {
      return "";
    }
    if (u.pathname.indexOf("/i/") === 0) {
      var pic = decodeURIComponent(u.pathname.split("/").pop() || "");
      return pic ? "picture: " + pic : "picture";
    }
    if (u.pathname.indexOf("/h/") === 0) {
      var page = decodeURIComponent(u.pathname.split("/").pop() || "");
      return page ? "html: " + page : "html";
    }
    var host = u.searchParams.get("h");
    var schemes = window.pocketHostSchemes || {};
    var scheme = host && schemes[host] === "roam" ? "roam" : "go";
    var p = (u.searchParams.get("p") || "").replace(/\.md$/i, "").replace(/\/+$/, "").toLowerCase();
    var go = host ? scheme + "." + host : "go";
    if (!host) {
      if (p === "roam") go = "roam";
      else if (p === "recent") go = "recent";
      else if (p && p !== "start" && p !== "go") go = p;
    }
    var q = u.searchParams.get("q");
    if (q) return go + "  [[" + q + "]]";
    var k = u.searchParams.get("k") || u.searchParams.get("crate");
    if (k) return "crate report  " + k;
    var c = u.searchParams.get("c") || u.searchParams.get("t");
    if (c) return "charlie lookup  #" + c;
    var m = (u.searchParams.get("m") || "").toLowerCase();
    if (m === "tps") {
      var keys = ["title", "month", "day", "year", "hour", "clock", "unix"];
      var bits = [];
      keys.forEach(function (k) {
        var val = u.searchParams.get(k);
        if (!val && k === (u.searchParams.get("f") || "")) val = u.searchParams.get("v");
        if (val) bits.push(k + " · " + val);
      });
      return "tps report  " + (bits.join(" / ") || "dates");
    }
    var f = u.searchParams.get("f");
    if (f) {
      var who =
        m === "agent" || m === "detective" ? "detective index" : "librarian catalog";
      var v = u.searchParams.get("v");
      return who + "  " + f + (v ? " · " + v : "");
    }
    var p = u.searchParams.get("p");
    if (p) {
      p = p.replace(/\\/g, "/").replace(/^\/+/, "");
      if (!/\.md$/i.test(p) && p.slice(-1) !== "/") p += "/";
      return go + "/" + p;
    }
    if (u.pathname === "/" || u.pathname === "") return go + "/";
    return go;
  }

  function paintStatus(text) {
    if (!statusEl) return;
    statusEl.textContent = text || STATUS_IDLE;
  }

  document.addEventListener(
    "mouseover",
    function (e) {
      var a = e.target && e.target.closest ? e.target.closest("a[href], a[data-rom]") : null;
      if (!a) return;
      var rom = (a.getAttribute("data-rom") || "").trim();
      if (rom) {
        paintStatus("Deck Host · " + rom);
        return;
      }
      paintStatus(pocketSpeak(a.href));
    },
    true
  );
  document.addEventListener(
    "mouseout",
    function (e) {
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a) return;
      var next = e.relatedTarget;
      if (next && a.contains(next)) return;
      paintStatus(STATUS_IDLE);
    },
    true
  );

  function bindSlides() {
    document.querySelectorAll("[data-slides]").forEach(function (root) {
      var pic = root.querySelector(".slides-pic");
      var cap = root.querySelector(".slides-cap");
      var num = root.querySelector(".slides-n");
      var thumbs = Array.prototype.slice.call(
        root.querySelectorAll(".slides-thumb[data-src]")
      );
      if (!pic || thumbs.length < 2) return;
      var i = 0;
      var n = thumbs.length;

      function show(next) {
        i = (next + n) % n;
        var t = thumbs[i];
        var src = t.getAttribute("data-src") || "";
        var name = t.getAttribute("data-name") || "";
        pic.src = src;
        pic.alt = name;
        if (cap) cap.textContent = name;
        if (num) num.textContent = i + 1 + " / " + n;
        thumbs.forEach(function (btn, k) {
          if (k === i) btn.classList.add("on");
          else btn.classList.remove("on");
        });
        if (t.scrollIntoView) {
          t.scrollIntoView({ block: "nearest", inline: "nearest" });
        }
      }

      var prev = root.querySelector(".slides-prev");
      var nxt = root.querySelector(".slides-next");
      if (prev) prev.addEventListener("click", function () { show(i - 1); });
      if (nxt) nxt.addEventListener("click", function () { show(i + 1); });
      thumbs.forEach(function (btn, k) {
        btn.addEventListener("click", function () { show(k); });
      });
      root.addEventListener("keydown", function (e) {
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          show(i - 1);
        } else if (e.key === "ArrowRight") {
          e.preventDefault();
          show(i + 1);
        }
      });
    });
  }
  bindSlides();

  function portsSkin() {
    return !!document.querySelector('link[href*="/styles/ports.css"]');
  }

  function flapify(el) {
    if (!el || el.getAttribute("data-flaps") === "1") return;
    var text = el.textContent || "";
    if (!text) return;
    el.setAttribute("data-flaps", "1");
    el.textContent = "";
    for (var i = 0; i < text.length; i++) {
      var ch = text.charAt(i);
      var s = document.createElement("span");
      s.className = "flap";
      s.textContent = ch === " " ? "\u00a0" : ch.toUpperCase();
      el.appendChild(s);
    }
  }

  function bindPorts() {
    if (!portsSkin()) return;
    var nodes = document.querySelectorAll(
      ".content ul.dir a .name, .content > li a.wiki, .content > ul:not(.hits) > li a.wiki"
    );
    Array.prototype.forEach.call(nodes, flapify);
  }
  bindPorts();

  var LAST_KEY = "pocket-go-last";

  function isDeskPage() {
    var html = document.documentElement;
    if (html.getAttribute("data-librarian") === "off") return false;
    if (html.hasAttribute("data-sheet")) return false;
    if (html.getAttribute("data-sidecar")) return false;
    return html.hasAttribute("data-vault") || html.hasAttribute("data-pocket");
  }

  function deskHrefNow() {
    try {
      var u = new URL(window.location.href);
      u.searchParams.delete("_cb");
      u.searchParams.delete("home");
      u.hash = "";
      return u.pathname + u.search;
    } catch (e) {
      return window.location.pathname + window.location.search;
    }
  }

  function isDeskHref(href) {
    href = String(href || "").trim();
    if (!href || href.charAt(0) !== "/") return false;
    if (href.charAt(1) === "/") return false;
    try {
      var u = new URL(href, window.location.href);
      if (u.pathname !== "/") return false;
      var q = u.searchParams;
      if (
        q.has("sidecar") ||
        q.has("k") ||
        q.has("crate") ||
        q.has("card") ||
        q.has("c") ||
        q.has("t") ||
        q.has("m") ||
        q.has("f") ||
        q.has("bay")
      ) {
        return false;
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  function rememberDesk() {
    if (!isDeskPage()) return;
    var href = deskHrefNow();
    if (!isDeskHref(href)) return;
    try {
      localStorage.setItem(LAST_KEY, href);
    } catch (e) {}
    try {
      var req = new XMLHttpRequest();
      req.open("POST", "/api/last");
      req.setRequestHeader("Content-Type", "application/json");
      req.send(JSON.stringify({ href: href }));
    } catch (e) {}
  }

  rememberDesk();
  window.addEventListener("pageshow", rememberDesk);
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) rememberDesk();
  });
  window.addEventListener("pagehide", rememberDesk);

  function bulletPocket() {
    return (document.documentElement.getAttribute("data-pocket") || "").trim();
  }

  function bulletNode(from) {
    var li = from && from.closest ? from.closest("li.bullet[data-i]") : null;
    if (!li || !li.closest(".go-shell")) return null;
    return li;
  }

  function markBullet(li) {
    if (!li || li.getAttribute("data-busy")) return;
    var pocket = bulletPocket();
    var i = li.getAttribute("data-i");
    if (!pocket || i == null) return;
    li.setAttribute("data-busy", "1");
    var req = new XMLHttpRequest();
    req.open("POST", "/api/bullet");
    req.setRequestHeader("Content-Type", "application/json");
    req.onload = function () {
      if (req.status >= 200 && req.status < 300) {
        window.location.reload();
        return;
      }
      li.removeAttribute("data-busy");
      paintStatus("could not mark");
    };
    req.onerror = function () {
      li.removeAttribute("data-busy");
      paintStatus("could not mark");
    };
    req.send(JSON.stringify({ pocket: pocket, i: Number(i) }));
  }


  /* —— Obsidian-style live Markdown tables —— */
  var mdTableSaveTimer = 0;
  var mdTableActive = null;

  function mdTablePocket() {
    return bulletPocket();
  }

  function mdTableWrap(from) {
    var w = from && from.closest ? from.closest(".md-table-wrap[data-table-i]") : null;
    if (!w || !w.closest(".go-shell")) return null;
    return w;
  }

  function mdTableCellText(cell) {
    if (!cell) return "";
    var raw = cell.getAttribute("data-md");
    if (raw != null) return raw;
    return (cell.textContent || "").replace(/\s+/g, " ").trim();
  }

  function mdTableReadGrid(wrap) {
    var table = wrap.querySelector("table.md-table");
    if (!table) return { rows: [], aligns: [] };
    var aligns = [];
    var rows = [];
    var ths = table.querySelectorAll("thead th");
    if (ths.length) {
      var head = [];
      for (var i = 0; i < ths.length; i++) {
        head.push(mdTableCellText(ths[i]));
        if (ths[i].classList.contains("is-center")) aligns[i] = "center";
        else if (ths[i].classList.contains("is-right")) aligns[i] = "right";
        else aligns[i] = "left";
      }
      rows.push(head);
    }
    var trs = table.querySelectorAll("tbody tr");
    for (var r = 0; r < trs.length; r++) {
      var cells = trs[r].querySelectorAll("td");
      var row = [];
      for (var c = 0; c < cells.length; c++) {
        row.push(mdTableCellText(cells[c]));
        if (!ths.length) {
          if (cells[c].classList.contains("is-center")) aligns[c] = "center";
          else if (cells[c].classList.contains("is-right")) aligns[c] = "right";
          else if (!aligns[c]) aligns[c] = "left";
        }
      }
      rows.push(row);
    }
    if (!rows.length) {
      /* no thead — all body already collected; if only thead missing */
      var all = table.querySelectorAll("tr");
      for (var a = 0; a < all.length; a++) {
        var cs = all[a].querySelectorAll("th,td");
        var rr = [];
        for (var b = 0; b < cs.length; b++) rr.push(mdTableCellText(cs[b]));
        rows.push(rr);
      }
    }
    return { rows: rows, aligns: aligns };
  }

  function mdTableSerialize(rows, aligns) {
    if (!rows || !rows.length) return "";
    var width = 0;
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].length > width) width = rows[i].length;
    }
    if (!width) return "";
    aligns = aligns || [];
    function cell(s) {
      return String(s || "")
        .replace(/\n/g, " ")
        .replace(/\|/g, "\\|")
        .trim();
    }
    function pad(row) {
      var out = row.slice();
      while (out.length < width) out.push("");
      return out.slice(0, width);
    }
    var lines = [];
    lines.push("| " + pad(rows[0]).map(cell).join(" | ") + " |");
    var sep = [];
    for (var c = 0; c < width; c++) {
      var al = aligns[c] || "left";
      if (al === "center") sep.push(":---:");
      else if (al === "right") sep.push("---:");
      else sep.push("---");
    }
    lines.push("| " + sep.join(" | ") + " |");
    for (var r = 1; r < rows.length; r++) {
      lines.push("| " + pad(rows[r]).map(cell).join(" | ") + " |");
    }
    return lines.join("\n");
  }

  function mdTableRebuild(wrap, rows, aligns) {
    var table = wrap.querySelector("table.md-table");
    if (!table) return;
    var width = 0;
    for (var i = 0; i < rows.length; i++) {
      if (rows[i].length > width) width = rows[i].length;
    }
    function pad(row) {
      var out = row.slice();
      while (out.length < width) out.push("");
      return out.slice(0, width);
    }
    var html = "";
    if (rows.length) {
      html += "<thead><tr>";
      var head = pad(rows[0]);
      for (var h = 0; h < head.length; h++) {
        var al = (aligns && aligns[h]) || "left";
        html +=
          '<th class="is-' +
          al +
          '" data-md="' +
          escapeAttr(head[h]) +
          '" contenteditable="true">' +
          escapeHtml(head[h]) +
          "</th>";
      }
      html += "</tr></thead><tbody>";
      for (var r = 1; r < rows.length; r++) {
        html += "<tr>";
        var row = pad(rows[r]);
        for (var c = 0; c < row.length; c++) {
          var al2 = (aligns && aligns[c]) || "left";
          html +=
            '<td class="is-' +
            al2 +
            '" data-md="' +
            escapeAttr(row[c]) +
            '" contenteditable="true">' +
            escapeHtml(row[c]) +
            "</td>";
        }
        html += "</tr>";
      }
      html += "</tbody>";
    }
    table.innerHTML = html;
    mdTableEnsureChrome(wrap);
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/"/g, "&quot;");
  }

  function mdTableEnsureChrome(wrap) {
    if (wrap.querySelector(".md-table-chrome")) return;
    var chrome = document.createElement("div");
    chrome.className = "md-table-chrome";
    chrome.innerHTML =
      '<button type="button" class="md-table-btn" data-table-add-row title="Add row">+ row</button>' +
      '<button type="button" class="md-table-btn" data-table-add-col title="Add column">+ col</button>' +
      '<button type="button" class="md-table-btn" data-table-del-row title="Delete last row">− row</button>' +
      '<button type="button" class="md-table-btn" data-table-del-col title="Delete last column">− col</button>' +
      '<button type="button" class="md-table-btn" data-table-done title="Done">done</button>';
    wrap.appendChild(chrome);
  }

  function mdTableEnter(wrap) {
    if (!wrap || wrap.classList.contains("is-editing")) return;
    if (mdTableActive && mdTableActive !== wrap) mdTableExit(mdTableActive, true);
    mdTableActive = wrap;
    wrap.classList.add("is-editing");
    mdTableEnsureChrome(wrap);
    var cells = wrap.querySelectorAll("th,td");
    for (var i = 0; i < cells.length; i++) {
      cells[i].setAttribute("contenteditable", "true");
    }
    if (cells[0]) {
      cells[0].focus();
      try {
        var range = document.createRange();
        range.selectNodeContents(cells[0]);
        range.collapse(false);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      } catch (e) {}
    }
  }

  function mdTableCollect(wrap) {
    var table = wrap.querySelector("table.md-table");
    var aligns = [];
    var rows = [];
    var headCells = table.querySelectorAll("thead th");
    if (headCells.length) {
      var head = [];
      for (var i = 0; i < headCells.length; i++) {
        var t = (headCells[i].textContent || "").replace(/\n/g, " ");
        headCells[i].setAttribute("data-md", t);
        head.push(t);
        if (headCells[i].classList.contains("is-center")) aligns[i] = "center";
        else if (headCells[i].classList.contains("is-right")) aligns[i] = "right";
        else aligns[i] = "left";
      }
      rows.push(head);
    }
    var bodyRows = table.querySelectorAll("tbody tr");
    for (var r = 0; r < bodyRows.length; r++) {
      var tds = bodyRows[r].querySelectorAll("td");
      var row = [];
      for (var c = 0; c < tds.length; c++) {
        var t2 = (tds[c].textContent || "").replace(/\n/g, " ");
        tds[c].setAttribute("data-md", t2);
        row.push(t2);
      }
      rows.push(row);
    }
    return { rows: rows, aligns: aligns };
  }

  function mdTableSave(wrap, thenReload) {
    if (!wrap || wrap.getAttribute("data-busy")) return;
    var pocket = mdTablePocket();
    var idx = wrap.getAttribute("data-table-i");
    if (!pocket || idx == null) return;
    var grid = mdTableCollect(wrap);
    var md = mdTableSerialize(grid.rows, grid.aligns);
    wrap.setAttribute("data-busy", "1");
    var req = new XMLHttpRequest();
    req.open("POST", "/api/table");
    req.setRequestHeader("Content-Type", "application/json");
    req.onload = function () {
      wrap.removeAttribute("data-busy");
      if (req.status >= 200 && req.status < 300) {
        if (thenReload) window.location.reload();
        else paintStatus("table saved");
        return;
      }
      paintStatus("could not save table");
    };
    req.onerror = function () {
      wrap.removeAttribute("data-busy");
      paintStatus("could not save table");
    };
    req.send(JSON.stringify({ pocket: pocket, i: Number(idx), markdown: md }));
  }

  function mdTableExit(wrap, save) {
    if (!wrap) return;
    wrap.classList.remove("is-editing");
    var cells = wrap.querySelectorAll("th,td");
    for (var i = 0; i < cells.length; i++) {
      cells[i].removeAttribute("contenteditable");
    }
    if (mdTableActive === wrap) mdTableActive = null;
    if (save) mdTableSave(wrap, true);
  }

  function mdTableFocusIndex(wrap, index) {
    var cells = wrap.querySelectorAll("th,td");
    if (!cells.length) return;
    if (index < 0) index = 0;
    if (index >= cells.length) index = cells.length - 1;
    cells[index].focus();
  }

  function mdTableCellIndex(wrap, cell) {
    var cells = wrap.querySelectorAll("th,td");
    for (var i = 0; i < cells.length; i++) {
      if (cells[i] === cell) return i;
    }
    return 0;
  }

  function mdTableColCount(wrap) {
    var th = wrap.querySelectorAll("thead th");
    if (th.length) return th.length;
    var td = wrap.querySelector("tbody tr");
    return td ? td.querySelectorAll("td").length : 0;
  }

  function bindMdTables() {
    if (document.documentElement._mdTablesBound) return;
    document.documentElement._mdTablesBound = true;

    document.addEventListener("click", function (e) {
      var addRow = e.target && e.target.closest ? e.target.closest("[data-table-add-row]") : null;
      var addCol = e.target && e.target.closest ? e.target.closest("[data-table-add-col]") : null;
      var delRow = e.target && e.target.closest ? e.target.closest("[data-table-del-row]") : null;
      var delCol = e.target && e.target.closest ? e.target.closest("[data-table-del-col]") : null;
      var done = e.target && e.target.closest ? e.target.closest("[data-table-done]") : null;
      var wrapBtn = addRow || addCol || delRow || delCol || done;
      if (wrapBtn) {
        e.preventDefault();
        e.stopPropagation();
        var wrap = wrapBtn.closest(".md-table-wrap");
        if (!wrap) return;
        var grid = mdTableCollect(wrap);
        var rows = grid.rows;
        var aligns = grid.aligns;
        var cols = mdTableColCount(wrap) || 1;
        if (addRow) {
          var blank = [];
          for (var i = 0; i < cols; i++) blank.push("");
          if (!rows.length) rows = [blank.slice(), blank.slice()];
          else rows.push(blank);
        } else if (addCol) {
          for (var r = 0; r < rows.length; r++) rows[r].push("");
          aligns.push("left");
        } else if (delRow) {
          if (rows.length > 2) rows.pop();
        } else if (delCol) {
          if (cols > 1) {
            for (var r2 = 0; r2 < rows.length; r2++) rows[r2].pop();
            aligns.pop();
          }
        } else if (done) {
          mdTableExit(wrap, true);
          return;
        }
        mdTableRebuild(wrap, rows, aligns);
        mdTableEnter(wrap);
        return;
      }

      var wrap = mdTableWrap(e.target);
      if (wrap && !wrap.classList.contains("is-editing")) {
        /* don't steal link clicks inside cells before edit */
        if (e.target.closest && e.target.closest("a")) return;
        e.preventDefault();
        mdTableEnter(wrap);
        return;
      }
      if (mdTableActive && (!wrap || wrap !== mdTableActive)) {
        if (e.target.closest && e.target.closest(".md-table-chrome")) return;
        mdTableExit(mdTableActive, true);
      }
    });

    document.addEventListener(
      "keydown",
      function (e) {
        if (!mdTableActive) return;
        var cell = e.target && e.target.closest ? e.target.closest("th,td") : null;
        if (!cell || !mdTableActive.contains(cell)) return;
        var wrap = mdTableActive;
        var cols = mdTableColCount(wrap) || 1;
        var idx = mdTableCellIndex(wrap, cell);
        if (e.key === "Tab") {
          e.preventDefault();
          mdTableFocusIndex(wrap, e.shiftKey ? idx - 1 : idx + 1);
          return;
        }
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          var grid = mdTableCollect(wrap);
          var blank = [];
          for (var i = 0; i < cols; i++) blank.push("");
          grid.rows.push(blank);
          var row = Math.floor(idx / cols);
          mdTableRebuild(wrap, grid.rows, grid.aligns);
          mdTableEnter(wrap);
          mdTableFocusIndex(wrap, (row + 1) * cols);
          return;
        }
        if (e.key === "Escape") {
          e.preventDefault();
          mdTableExit(wrap, true);
        }
      },
      true
    );

    /* light column resize */
    document.addEventListener("mousedown", function (e) {
      if (!mdTableActive) return;
      var cell = e.target && e.target.closest ? e.target.closest("th,td") : null;
      if (!cell || !mdTableActive.contains(cell)) return;
      var rect = cell.getBoundingClientRect();
      if (rect.right - e.clientX > 6) return;
      e.preventDefault();
      var startX = e.clientX;
      var startW = cell.offsetWidth;
      function move(ev) {
        var w = Math.max(48, startW + (ev.clientX - startX));
        cell.style.width = w + "px";
        cell.style.minWidth = w + "px";
      }
      function up() {
        document.removeEventListener("mousemove", move);
        document.removeEventListener("mouseup", up);
      }
      document.addEventListener("mousemove", move);
      document.addEventListener("mouseup", up);
    });
  }

  bindMdTables();

  function faceDoor(from) {
    var art = from && from.closest ? from.closest("article.face[data-href]") : null;
    if (!art || !art.closest(".go-shell")) return null;
    var href = (art.getAttribute("data-href") || "").trim();
    return href ? { art: art, href: href } : null;
  }

  function openFace(href) {
    if (!href) return;
    if (document.documentElement.hasAttribute("data-sheet")) {
      if (typeof window.nudgeDesk === "function") window.nudgeDesk(href);
      return;
    }
    window.location.assign(href);
  }

  document.addEventListener("click", function (e) {
    if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
      return;
    }
    if (e.target.closest && e.target.closest("a, button, input, textarea, label")) {
      return;
    }
    var door = faceDoor(e.target);
    if (door) {
      e.preventDefault();
      openFace(door.href);
      return;
    }
    var li = bulletNode(e.target);
    if (!li) return;
    e.preventDefault();
    markBullet(li);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== " " && e.key !== "Enter") return;
    var door = faceDoor(e.target);
    if (door && e.target === door.art) {
      e.preventDefault();
      openFace(door.href);
      return;
    }
    var li = e.target;
    if (!li || !li.matches || !li.matches("li.bullet[data-i]")) return;
    if (!li.closest(".go-shell")) return;
    e.preventDefault();
    markBullet(li);
  });

/* eden-ascent */
(function () {
  var pocket = (document.documentElement.getAttribute("data-pocket") || "");
  if (pocket.indexOf("go.eden") !== 0) return;
  var content = document.querySelector("#browserWindow .content");
  if (!content || content.getAttribute("data-eden-climb") === "1") return;
  content.setAttribute("data-eden-climb", "1");
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "eden-climb";
  btn.setAttribute("data-eden-ascent", "0");
  btn.textContent = "climb from the root";
  var h1 = content.querySelector(":scope > h1");
  if (h1) h1.insertAdjacentElement("afterend", btn);
  else content.insertBefore(btn, content.firstChild);
  btn.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    var on = btn.getAttribute("data-eden-ascent") === "1";
    var blocks = [];
    Array.prototype.forEach.call(content.children, function (el) {
      if (el === btn || (el.tagName && el.tagName.toLowerCase() === "h1")) return;
      blocks.push(el);
    });
    blocks.reverse().forEach(function (el) { content.appendChild(el); });
    btn.setAttribute("data-eden-ascent", on ? "0" : "1");
    btn.textContent = on ? "climb from the root" : "descend to the crown";
    btn.classList.toggle("on", !on);
    content.classList.toggle("is-ascent", !on);
  });
})();
/* /eden-ascent */

/* typewriter-keys */
(function () {
  var pocket = (document.documentElement.getAttribute("data-pocket") || "");
  if (pocket.indexOf("go.typewriter") !== 0) return;
  var chassis = document.querySelector("#browserWindow .chassis");
  if (!chassis || chassis.getAttribute("data-keys") === "1") return;
  chassis.setAttribute("data-keys", "1");
  chassis.innerHTML = "";
  var badge = document.createElement("div");
  badge.className = "badge";
  badge.innerHTML = "<strong>TYPEWRITER</strong><span>platen feed</span>";
  chassis.appendChild(badge);
  var row = document.createElement("div");
  row.className = "keys";
  var labels = ["Q","W","E","R","T","Y","U","I","O","P","A","S","D","F","G","H","J","K","L",";","Z","X","C","V","B","N","M",",",".","/","SHIFT","TAB","SPACE","RETURN","RIBBON"];
  labels.forEach(function (lab) {
    var k = document.createElement("span");
    k.textContent = lab;
    if (lab === "SPACE") k.className = "space";
    else if (lab === "SHIFT" || lab === "TAB" || lab === "RETURN") k.className = "wide";
    else if (lab === "RIBBON") k.className = "wide red";
    row.appendChild(k);
  });
  chassis.appendChild(row);
})();
/* /typewriter-keys */
﻿/* tags-yard-drawer */
(function () {
  var pocket = (document.documentElement.getAttribute("data-pocket") || "");
  if (pocket.indexOf("go.tags") !== 0) return;
  var yard = document.querySelector("#browserWindow .yard");
  if (!yard || yard.getAttribute("data-yard") === "1") return;
  yard.setAttribute("data-yard", "1");

  var scrim = document.createElement("div");
  scrim.className = "yard-scrim";
  yard.appendChild(scrim);

  var pull = document.createElement("button");
  pull.type = "button";
  pull.className = "crate-pull";
  pull.setAttribute("aria-label", "Open crate faces");
  pull.textContent = "CRATES";
  yard.appendChild(pull);

  function setOpen(on) {
    yard.classList.toggle("is-drawer-open", !!on);
    pull.textContent = on ? "STOW" : "CRATES";
    pull.setAttribute("aria-expanded", on ? "true" : "false");
  }
  pull.addEventListener("click", function () {
    setOpen(!yard.classList.contains("is-drawer-open"));
  });
  scrim.addEventListener("click", function () { setOpen(false); });

  var form = yard.querySelector(".tag-search");
  if (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector("button");
      if (!btn) return;
      btn.classList.remove("is-stamp");
      void btn.offsetWidth;
      btn.classList.add("is-stamp");
    });
  }

  var input = yard.querySelector('.tag-search input[type="search"]');
  if (input && !input.getAttribute("placeholder")) {
    input.setAttribute("placeholder", "scan a word");
  } else if (input) {
    input.setAttribute("placeholder", "scan · find or open a word");
  }

  /* stamp lids: meta + hung lore collapsible (expanded by default) */
  function stampLid(el, label, open, extra) {
    if (!el || el.closest('details.stamp-lid')) return;
    var parent = el.parentNode;
    if (!parent) return;
    var d = document.createElement('details');
    var kind = el.classList.contains('yard-shelf-wrap') ? ' is-lore' : ' is-meta';
    if (extra) kind = ' ' + extra;
    d.className = 'stamp-lid' + kind;
    if (open !== false) d.open = true;
    var s = document.createElement('summary');
    s.className = 'stamp-lid-head';
    s.textContent = label;
    parent.insertBefore(d, el);
    d.appendChild(s);
    d.appendChild(el);
  }
  var meta = yard.querySelector('.top-stamp .meta');
  if (meta && meta.querySelector('.chips')) {
    stampLid(meta, 'META \u00b7 STAMP SLIP', true);
  }
  var lore = yard.querySelector('.top-stamp .yard-shelf-wrap');
  if (lore) {
    stampLid(lore, 'HUNG LORE \u00b7 edged to this crate', true);
  }
  var cites = yard.querySelector('.taglook .tagbay-cites');
  var codes = yard.querySelector('.taglook .tagbay-codes');
  if (cites) {
    stampLid(cites, 'LOOK-THROUGH', true, 'is-look');
    if (codes) {
      var look = cites.closest('details.stamp-lid');
      if (look) look.appendChild(codes);
    }
  } else if (codes) {
    stampLid(codes, 'LOOK-THROUGH', true, 'is-look');
  }
  yard.querySelectorAll('.taglook .tagbay-chest.is-thread-rail').forEach(function (el) {
    var h = el.querySelector('h2');
    var n = el.querySelector('.tagbay-n');
    var label = (h && h.textContent ? h.textContent.trim() : 'threads');
    if (n && n.textContent) label += '  ' + n.textContent.trim();
    stampLid(el, label, false, 'is-thread');
  });
})();
/* /tags-yard-drawer */
/* media-tower-panes */
(function () {
  var pocket = (document.documentElement.getAttribute("data-pocket") || "");
  if (pocket.indexOf("go.media") !== 0) return;
  var store = document.querySelector("#browserWindow .store");
  if (!store || store.getAttribute("data-tower") === "1") return;
  store.setAttribute("data-tower", "1");

  /* lobby: snap department panes when the door row is wide enough to scroll */
  var doors = store.querySelector(".aisle-doors .worlds") || store.querySelector(".aisle-doors");
  if (doors && store.querySelector(".entrance")) {
    store.classList.add("is-paned");
  }

  /* aisle: sliding bin drawer on narrow stages */
  var aisle = store.querySelector(".aisle");
  var bin = store.querySelector(".bin");
  if (aisle && bin) {
    var scrim = document.createElement("div");
    scrim.className = "aisle-scrim";
    store.appendChild(scrim);

    var pull = document.createElement("button");
    pull.type = "button";
    pull.className = "aisle-pull";
    pull.setAttribute("aria-label", "Open aisle bin");
    pull.textContent = "BINS";
    store.appendChild(pull);

    function setOpen(on) {
      store.classList.toggle("is-bin-open", !!on);
      pull.textContent = on ? "STOW" : "BINS";
      pull.setAttribute("aria-expanded", on ? "true" : "false");
    }
    pull.addEventListener("click", function () {
      setOpen(!store.classList.contains("is-bin-open"));
    });
    scrim.addEventListener("click", function () { setOpen(false); });
  }
})();
/* /media-tower-panes */



/* mausoleum-tombs-drawer */
(function () {
  var pocket = document.documentElement.getAttribute("data-pocket") || "";
  if (pocket.indexOf("go.mausoleum") !== 0) return;
  var page = document.querySelector("#browserWindow .page") || document.querySelector(".go-shell .page");
  if (!page || page.getAttribute("data-tombs") === "1") return;
  var body = page.querySelector(".body");
  var sidebar = page.querySelector(".sidebar");
  if (!body || !sidebar) return;
  page.setAttribute("data-tombs", "1");

  // Scrim + pull live in .body so z-index can sit under the rail (not over the links).
  var scrim = document.createElement("div");
  scrim.className = "tombs-scrim";
  body.appendChild(scrim);

  var pull = document.createElement("button");
  pull.type = "button";
  pull.className = "tombs-pull";
  pull.setAttribute("aria-label", "Open tombs");
  pull.setAttribute("aria-expanded", "false");
  pull.textContent = "TOMBS";
  body.appendChild(pull);

  function setOpen(on) {
    page.classList.toggle("is-tombs-open", !!on);
    body.classList.toggle("is-tombs-open", !!on);
    pull.textContent = on ? "STOW" : "TOMBS";
    pull.setAttribute("aria-expanded", on ? "true" : "false");
  }
  pull.addEventListener("click", function () {
    setOpen(!page.classList.contains("is-tombs-open"));
  });
  scrim.addEventListener("click", function () {
    setOpen(false);
  });
})();
/* /mausoleum-tombs-drawer */

})();


/* pocket-jump-bar */
(function () {
  var KEY = "pocket-go-jumps-v1";
  var DEFAULTS = [
    { label: "go", href: "/?home=1" }
  ];
  /* Always-on chips (not user bookmarks) — before cabinet jumps, with a divider. */
  var PINNED = [
    { label: "help", href: "/?h=help" }
  ];
  var dragFrom = -1;
  var jumpsReady = false;

  function bar() {
    return document.getElementById("jumpBar");
  }
  function pinBtn() {
    return document.getElementById("jumpPin");
  }
  function cleanList(list) {
    if (!Array.isArray(list)) return [];
    return list.filter(function (x) {
      return x && x.href && x.label;
    });
  }
  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return [];
      return cleanList(JSON.parse(raw));
    } catch (e) {
      return [];
    }
  }
  function save(list, push) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
    } catch (e) {}
    if (!push || !jumpsReady) return;
    try {
      var req = new XMLHttpRequest();
      req.open("POST", "/api/jumps");
      req.setRequestHeader("Content-Type", "application/json");
      req.send(JSON.stringify({ jumps: list }));
    } catch (e) {}
  }
  function hydrate() {
    var req = new XMLHttpRequest();
    req.open("GET", "/api/jumps");
    req.onload = function () {
      var data = {};
      try {
        data = JSON.parse(req.responseText || "{}");
      } catch (e) {}
      var disk = data.disk === true;
      var fromDisk = cleanList(data.jumps);
      if (disk) {
        jumpsReady = true;
        save(fromDisk, false);
        paintBar();
        return;
      }
      var local = load();
      if (!local.length) local = DEFAULTS.slice();
      jumpsReady = true;
      save(local, true);
      paintBar();
    };
    req.onerror = function () {
      jumpsReady = true;
      if (!load().length) save(DEFAULTS.slice(), false);
      paintBar();
    };
    req.send();
  }
  function currentHref() {
    return window.location.pathname + window.location.search;
  }
  function currentLabel() {
    var title = document.querySelector(".wwwExplorer_title");
    var t = title ? (title.textContent || "").trim() : "";
    if (t) return t.slice(0, 28);
    var pocket = (document.documentElement.getAttribute("data-pocket") || "").trim();
    if (pocket) {
      var parts = pocket.replace(/\/+$/, "").split("/");
      return (parts[parts.length - 1] || parts[0] || "page").slice(0, 28);
    }
    return "page";
  }
  function normHref(h) {
    try {
      var u = new URL(h, window.location.href);
      return u.pathname + u.search;
    } catch (e) {
      return String(h || "");
    }
  }
  function goPath(href) {
    try {
      var u = new URL(href, window.location.href);
      var host = (u.searchParams.get("h") || "").trim();
      var p = (u.searchParams.get("p") || "").trim().replace(/^\/+/, "");
      if (u.searchParams.get("home") === "1" || (!host && !p && (u.pathname === "/" || u.pathname === ""))) {
        return "go.start";
      }
      if (!host) {
        var stem = p.replace(/\.md$/i, "").replace(/\/+$/, "").toLowerCase();
        if (stem === "roam") return "roam";
        if (stem === "recent") return "recent";
        return p ? "go./" + p : "go.start";
      }
      var schemes = window.pocketHostSchemes || {};
      var scheme = schemes[host] === "roam" ? "roam" : "go";
      return p ? scheme + "." + host + "/" + p : scheme + "." + host;
    } catch (e) {
      return String(href || "");
    }
  }
  function isHere(href) {
    return normHref(href) === normHref(currentHref());
  }
  function reorder(from, to) {
    if (from === to || from < 0 || to < 0) return;
    var list = load();
    if (from >= list.length || to >= list.length) return;
    var item = list.splice(from, 1)[0];
    list.splice(to, 0, item);
    save(list, true);
    paintBar();
  }
  function paintPin() {
    var btn = pinBtn();
    if (!btn) return;
    var list = load();
    var here = normHref(currentHref());
    var on = list.some(function (x) {
      return normHref(x.href) === here;
    });
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    var tip = on ? "Unpin " + goPath(here) : "Pin " + goPath(here);
    btn.title = tip;
    btn.setAttribute("aria-label", on ? "Unpin page" : "Pin page");
  }
  function paintBar() {
    var el = bar();
    if (!el) return;
    var list = load();
    el.innerHTML = "";
    if (!PINNED.length && !list.length) {
      el.hidden = true;
      paintPin();
      return;
    }
    el.hidden = false;
    function appendJumpChip(item, idx, permanent) {
      var a = document.createElement("a");
      a.className =
        "jumpChip" +
        (isHere(item.href) ? " is-here" : "") +
        (permanent ? " is-permanent" : "");
      a.href = item.href;
      a.title = permanent
        ? goPath(item.href) + " · go.help"
        : goPath(item.href) + " · drag to reorder · Ctrl-click for a working tab";
      var name = document.createElement("span");
      name.className = "jumpChip-name";
      name.textContent = item.label;
      a.appendChild(name);
      if (permanent) {
        a.draggable = false;
        a.setAttribute("data-permanent", "1");
      } else {
        a.draggable = true;
        a.dataset.idx = String(idx);
      }
      function goJump(e) {
        if (a.classList.contains("is-dragging")) {
          e.preventDefault();
          return;
        }
        e.preventDefault();
        if (e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1) {
          if (window.pocketOpenWorkTab) window.pocketOpenWorkTab(item.href);
          else if (window.pocketSoftGo) window.pocketSoftGo(item.href);
          else window.location.assign(item.href);
          return;
        }
        if (window.pocketSoftGo) window.pocketSoftGo(item.href);
        else window.location.assign(item.href);
      }
      a.addEventListener("click", goJump);
      a.addEventListener("auxclick", function (e) {
        if (e.button === 1) goJump(e);
      });
      if (permanent) {
        el.appendChild(a);
        return;
      }
      /* user chip: drag + remove wired below */
      return { a: a, goJump: goJump };
    }
    PINNED.forEach(function (item) {
      appendJumpChip(item, -1, true);
    });
    if (PINNED.length && list.length) {
      var sep = document.createElement("span");
      sep.className = "jumpSep";
      sep.setAttribute("aria-hidden", "true");
      el.appendChild(sep);
    }
    list.forEach(function (item, idx) {
      var built = appendJumpChip(item, idx, false);
      var a = built.a;
      a.addEventListener("dragstart", function (e) {
        dragFrom = idx;
        a.classList.add("is-dragging");
        try {
          e.dataTransfer.effectAllowed = "move";
          e.dataTransfer.setData("text/plain", String(idx));
        } catch (err) {}
      });
      a.addEventListener("dragend", function () {
        dragFrom = -1;
        a.classList.remove("is-dragging");
        el.querySelectorAll(".is-drag-over").forEach(function (n) {
          n.classList.remove("is-drag-over");
        });
      });
      a.addEventListener("dragover", function (e) {
        e.preventDefault();
        try {
          e.dataTransfer.dropEffect = "move";
        } catch (err) {}
        a.classList.add("is-drag-over");
      });
      a.addEventListener("dragleave", function () {
        a.classList.remove("is-drag-over");
      });
      a.addEventListener("drop", function (e) {
        e.preventDefault();
        a.classList.remove("is-drag-over");
        var from = dragFrom;
        if (from < 0) {
          try {
            from = parseInt(e.dataTransfer.getData("text/plain"), 10);
          } catch (err) {
            from = -1;
          }
        }
        reorder(from, idx);
      });
      var x = document.createElement("button");
      x.type = "button";
      x.className = "jumpX";
      x.draggable = false;
      x.title = "Remove " + goPath(item.href);
      x.setAttribute("aria-label", "Remove " + item.label);
      x.textContent = "×";
      x.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var next = load().filter(function (_, i) {
          return i !== idx;
        });
        save(next, true);
        paintBar();
      });
      a.appendChild(x);
      el.appendChild(a);
    });
    paintPin();
  }
  function togglePin() {
    var list = load();
    var here = normHref(currentHref());
    var found = -1;
    for (var i = 0; i < list.length; i++) {
      if (normHref(list[i].href) === here) {
        found = i;
        break;
      }
    }
    if (found >= 0) {
      list.splice(found, 1);
    } else {
      list.push({ label: currentLabel(), href: here });
    }
    save(list, true);
    paintBar();
  }

  function boot() {
    paintBar();
    hydrate();
    var btn = pinBtn();
    if (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        togglePin();
      });
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  window.addEventListener("pageshow", paintBar);
})();
/* /pocket-jump-bar */

/* pocket-work-tabs — session papers in this window; cabinets stay on this desk */
(function () {
  var KEY = "pocket-go-work-tabs-v1";
  var SWITCH = "pocket-go-tab-switch";
  var MAX = 12;

  function deskOk() {
    var html = document.documentElement;
    if (html.getAttribute("data-librarian") === "off") return false;
    if (html.hasAttribute("data-sheet")) return false;
    if (html.getAttribute("data-sidecar")) return false;
    return html.hasAttribute("data-vault") || html.hasAttribute("data-pocket");
  }

  function strip() {
    return document.getElementById("workTabs");
  }

  function nowHref() {
    try {
      var u = new URL(window.location.href);
      u.searchParams.delete("_cb");
      u.hash = "";
      return u.pathname + u.search;
    } catch (e) {
      return window.location.pathname + window.location.search;
    }
  }

  function nowLabel() {
    var title = document.querySelector(".wwwExplorer_title");
    var t = title ? (title.textContent || "").trim() : "";
    if (t) return t.slice(0, 32);
    return "page";
  }

  function goPath(href) {
    try {
      var u = new URL(href, window.location.href);
      var host = (u.searchParams.get("h") || "").trim();
      var p = (u.searchParams.get("p") || "").trim().replace(/^\/+/, "");
      if (u.searchParams.get("home") === "1" || (!host && !p && (u.pathname === "/" || u.pathname === ""))) {
        return "go.start";
      }
      if (!host) {
        var stem = p.replace(/\.md$/i, "").replace(/\/+$/, "").toLowerCase();
        if (stem === "roam") return "roam";
        if (stem === "recent") return "recent";
        return p ? "go./" + p : "go.start";
      }
      var schemes = window.pocketHostSchemes || {};
      var scheme = schemes[host] === "roam" ? "roam" : "go";
      return p ? scheme + "." + host + "/" + p : scheme + "." + host;
    } catch (e) {
      return String(href || "");
    }
  }

  function isDeskHref(href) {
    href = String(href || "").trim();
    if (!href || href.charAt(0) === "#") return false;
    try {
      var u = new URL(href, window.location.href);
      if (u.origin !== window.location.origin) return false;
      if (u.pathname !== "/") return false;
      var q = u.searchParams;
      if (
        q.has("sidecar") ||
        q.has("k") ||
        q.has("crate") ||
        q.has("card") ||
        q.has("c") ||
        q.has("t") ||
        q.has("m") ||
        q.has("f") ||
        q.has("bay")
      ) {
        return false;
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  function blankState() {
    return { tabs: [], active: "" };
  }

  function load() {
    try {
      var raw = sessionStorage.getItem(KEY);
      if (!raw) return blankState();
      var data = JSON.parse(raw);
      if (!data || !Array.isArray(data.tabs)) return blankState();
      data.tabs = data.tabs
        .filter(function (t) {
          return t && t.id && t.href;
        })
        .map(function (t) {
          return {
            id: String(t.id),
            href: String(t.href),
            label: String(t.label || "page").slice(0, 32),
            back: Array.isArray(t.back) ? t.back.filter(Boolean).slice(-40) : [],
            fwd: Array.isArray(t.fwd) ? t.fwd.filter(Boolean).slice(-40) : [],
          };
        });
      if (data.tabs.length && !data.tabs.some(function (t) { return t.id === data.active; })) {
        data.active = data.tabs[0].id;
      }
      return data;
    } catch (e) {
      return blankState();
    }
  }

  function save(state) {
    try {
      sessionStorage.setItem(KEY, JSON.stringify(state));
    } catch (e) {}
  }

  function mintId() {
    return "w" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  }

  var DRAFT_KEY = "pocket-go-work-tab-drafts-v1";

  function loadDrafts() {
    try {
      var raw = sessionStorage.getItem(DRAFT_KEY);
      if (!raw) return {};
      var data = JSON.parse(raw);
      return data && typeof data === "object" ? data : {};
    } catch (e) {
      return {};
    }
  }

  function saveDrafts(map) {
    try {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(map || {}));
    } catch (e) {}
  }

  function draftRoot() {
    return (
      document.getElementById("browserWindow") ||
      document.querySelector(".go-shell") ||
      document.body
    );
  }

  function nodeKey(el, i) {
    if (el.name) return "n:" + el.name;
    if (el.id) return "i:" + el.id;
    return "x:" + i + ":" + (el.tagName || "").toLowerCase();
  }

  function escAttr(s) {
    return String(s || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  }

  function captureDraftFor(tabId) {
    if (!tabId) return;
    var root = draftRoot();
    if (!root) return;
    var nodes = [];
    var list = root.querySelectorAll("input, textarea, select");
    for (var i = 0; i < list.length; i++) {
      var el = list[i];
      var typ = (el.type || "").toLowerCase();
      if (
        typ === "password" ||
        typ === "file" ||
        typ === "button" ||
        typ === "submit" ||
        typ === "reset" ||
        typ === "image" ||
        typ === "hidden"
      ) {
        // Hidden inputs are server plumbing (injector pocket/land, etc.).
        // Never stash or replay them — a stale pocket key after a server fix
        // would keep minting title-only notes.
        continue;
      }
      if (el._cm) {
        try {
          el._cm.save();
        } catch (e) {}
      }
      var val = el.value;
      if (el._cm) {
        try {
          val = el._cm.getValue();
        } catch (e2) {}
      }
      nodes.push({
        key: nodeKey(el, i),
        name: el.name || "",
        id: el.id || "",
        tag: (el.tagName || "").toLowerCase(),
        type: typ,
        value: val,
        checked: !!el.checked,
      });
    }
    var edits = root.querySelectorAll(
      '[contenteditable=""], [contenteditable=true], [contenteditable=plaintext-only]'
    );
    for (var j = 0; j < edits.length; j++) {
      var ce = edits[j];
      nodes.push({
        key: "c:" + (ce.id || j),
        name: "",
        id: ce.id || "",
        tag: "contenteditable",
        type: "contenteditable",
        value: ce.innerHTML || "",
        checked: false,
      });
    }
    if (!nodes.length) return;
    var map = loadDrafts();
    map[tabId] = { href: nowHref(), at: Date.now(), nodes: nodes };
    saveDrafts(map);
  }

  function findDraftNode(root, spec) {
    if (spec.name) {
      var byName = root.querySelectorAll('[name="' + escAttr(spec.name) + '"]');
      if (byName.length === 1) return byName[0];
      if (byName.length > 1 && spec.type) {
        for (var a = 0; a < byName.length; a++) {
          if ((byName[a].type || "").toLowerCase() === spec.type) return byName[a];
        }
      }
      if (byName.length) return byName[0];
    }
    if (spec.id) {
      var byId = document.getElementById(spec.id);
      if (byId) return byId;
    }
    return null;
  }

  function restoreDraftFor(tabId) {
    if (!tabId) return;
    var map = loadDrafts();
    var bag = map[tabId];
    if (!bag || !bag.nodes || !bag.nodes.length) return;
    if (bag.href && bag.href !== nowHref()) return;
    var root = draftRoot();
    if (!root) return;
    for (var i = 0; i < bag.nodes.length; i++) {
      var spec = bag.nodes[i];
      if (spec.tag === "contenteditable") {
        var ce = findDraftNode(root, spec);
        if (ce && ce.isContentEditable) {
          try {
            ce.innerHTML = spec.value || "";
          } catch (e) {}
        }
        continue;
      }
      var el = findDraftNode(root, spec);
      if (!el) continue;
      var elTyp = (el.type || spec.type || "").toLowerCase();
      if (elTyp === "hidden" || spec.type === "hidden") continue;
      if (spec.name === "pocket" || spec.name === "land") continue;
      if (spec.type === "checkbox" || spec.type === "radio") {
        el.checked = !!spec.checked;
        try {
          el.dispatchEvent(new Event("change", { bubbles: true }));
        } catch (e2) {}
        continue;
      }
      if (el._cm) {
        try {
          el._cm.setValue(spec.value || "");
          el._cm.save();
        } catch (e3) {
          el.value = spec.value || "";
        }
      } else {
        el.value = spec.value || "";
      }
      try {
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
      } catch (e4) {}
    }
  }

  function dropDraftFor(tabId) {
    if (!tabId) return;
    var map = loadDrafts();
    if (map[tabId]) {
      delete map[tabId];
      saveDrafts(map);
    }
  }

  function captureActiveDraft() {
    var state = load();
    if (state.active) captureDraftFor(state.active);
  }


  function find(state, id) {
    for (var i = 0; i < state.tabs.length; i++) {
      if (state.tabs[i].id === id) return state.tabs[i];
    }
    return null;
  }

  function go(href) {
    href = String(href || "").trim();
    if (!href) return;
    if (window.pocketSoftGo) window.pocketSoftGo(href);
    else window.location.assign(href);
  }

  function markSwitch() {
    try {
      sessionStorage.setItem(SWITCH, "1");
    } catch (e) {}
  }

  function takeSwitch() {
    try {
      var on = sessionStorage.getItem(SWITCH) === "1";
      sessionStorage.removeItem(SWITCH);
      return on;
    } catch (e) {
      return false;
    }
  }

  function syncHere() {
    var state = load();
    var href = nowHref();
    var label = nowLabel();
    if (!state.tabs.length) {
      var id = mintId();
      state.tabs.push({ id: id, href: href, label: label, back: [], fwd: [] });
      state.active = id;
      save(state);
      return state;
    }
    var tab = find(state, state.active) || state.tabs[0];
    state.active = tab.id;
    var switching = takeSwitch();
    if (!switching && tab.href !== href) {
      tab.back.push(tab.href);
      if (tab.back.length > 40) tab.back = tab.back.slice(-40);
      tab.fwd = [];
    }
    tab.href = href;
    tab.label = label;
    save(state);
    return state;
  }

  function paint() {
    var el = strip();
    if (!el) return;
    if (!deskOk()) {
      el.hidden = true;
      return;
    }
    var state = load();
    el.innerHTML = "";
    el.hidden = false;
    state.tabs.forEach(function (tab) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "workTab" + (tab.id === state.active ? " is-active" : "");
      b.title = goPath(tab.href);
      if (tab.id === state.active) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
      var name = document.createElement("span");
      name.className = "workTab-name";
      name.textContent = tab.label || "page";
      b.appendChild(name);
      var x = document.createElement("span");
      x.className = "workTab-x";
      x.setAttribute("aria-label", "Close " + (tab.label || "tab"));
      x.textContent = "×";
      x.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        closeTab(tab.id);
      });
      b.appendChild(x);
      b.addEventListener("click", function () {
        switchTab(tab.id);
      });
      el.appendChild(b);
    });
    var plus = document.createElement("button");
    plus.type = "button";
    plus.className = "workNew";
    plus.title = "New working tab (Ctrl+T)";
    plus.setAttribute("aria-label", "New working tab");
    plus.textContent = "+";
    plus.addEventListener("click", function () {
      openTab("/?home=1", { force: true });
    });
    el.appendChild(plus);
  }

  function switchTab(id) {
    var state = load();
    var tab = find(state, id);
    if (!tab) return;
    if (tab.id === state.active) return;
    captureDraftFor(state.active);
    state.active = id;
    save(state);
    markSwitch();
    go(tab.href);
  }

  function closeTab(id) {
    var state = load();
    if (state.tabs.length < 2) return;
    var idx = -1;
    for (var i = 0; i < state.tabs.length; i++) {
      if (state.tabs[i].id === id) {
        idx = i;
        break;
      }
    }
    if (idx < 0) return;
    var was = state.active === id;
    if (was) captureDraftFor(state.active);
    dropDraftFor(id);
    state.tabs.splice(idx, 1);
    if (was) {
      var next = state.tabs[Math.min(idx, state.tabs.length - 1)];
      state.active = next.id;
      save(state);
      markSwitch();
      go(next.href);
      return;
    }
    save(state);
    paint();
  }

  function openTab(href, opts) {
    href = String(href || "").trim();
    if (!href) return;
    try {
      var u = new URL(href, window.location.href);
      href = u.pathname + u.search;
    } catch (e) {}
    opts = opts || {};
    var state = load();
    if (!opts.force) {
      for (var i = 0; i < state.tabs.length; i++) {
        if (state.tabs[i].href === href) {
          switchTab(state.tabs[i].id);
          return;
        }
      }
    }
    if (state.tabs.length >= MAX) return;
    captureDraftFor(state.active);
    var id = mintId();
    state.tabs.push({
      id: id,
      href: href,
      label: opts.label || "page",
      back: [],
      fwd: [],
    });
    state.active = id;
    save(state);
    markSwitch();
    go(href);
  }

  function tabBack() {
    var state = load();
    var tab = find(state, state.active);
    if (!tab || !tab.back.length) return false;
    captureDraftFor(state.active);
    tab.fwd.push(tab.href);
    var dest = tab.back.pop();
    save(state);
    markSwitch();
    go(dest);
    return true;
  }

  function tabFwd() {
    var state = load();
    var tab = find(state, state.active);
    if (!tab || !tab.fwd.length) return false;
    captureDraftFor(state.active);
    tab.back.push(tab.href);
    var dest = tab.fwd.pop();
    save(state);
    markSwitch();
    go(dest);
    return true;
  }

  window.pocketOpenWorkTab = function (href) {
    if (!deskOk()) {
      go(href);
      return;
    }
    openTab(href, {});
  };

  var prevBack = window.WWWBack;
  window.WWWBack = function () {
    if (deskOk() && tabBack()) return;
    if (typeof prevBack === "function") prevBack();
  };
  var prevFwd = window.WWWForward;
  window.WWWForward = function () {
    if (deskOk() && tabFwd()) return;
    if (typeof prevFwd === "function") prevFwd();
  };

  function hrefFromAnchor(a) {
    var href = a.getAttribute("href") || "";
    if (!isDeskHref(href)) return "";
    try {
      var u = new URL(href, window.location.href);
      return u.pathname + u.search;
    } catch (e) {
      return "";
    }
  }

  document.addEventListener(
    "click",
    function (e) {
      if (!deskOk()) return;
      if (e.button !== 0 || !(e.ctrlKey || e.metaKey)) return;
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a || a.closest("#jumpBar") || a.closest("#workTabs")) return;
      if (!a.closest(".go-shell")) return;
      var href = hrefFromAnchor(a);
      if (!href) return;
      e.preventDefault();
      e.stopPropagation();
      openTab(href, {});
    },
    true
  );

  document.addEventListener(
    "auxclick",
    function (e) {
      if (!deskOk() || e.button !== 1) return;
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a || a.closest("#jumpBar") || a.closest("#workTabs")) return;
      if (!a.closest(".go-shell")) return;
      var href = hrefFromAnchor(a);
      if (!href) return;
      e.preventDefault();
      openTab(href, {});
    },
    true
  );

  document.addEventListener(
    "keydown",
    function (e) {
      if (!deskOk()) return;
      var key = e.key || "";
      var mod = e.ctrlKey || e.metaKey;
      if (mod && (key === "t" || key === "T") && !e.shiftKey) {
        e.preventDefault();
        openTab("/?home=1", { force: true });
        return;
      }
      if (mod && (key === "w" || key === "W") && !e.altKey) {
        e.preventDefault();
        var state = load();
        if (state.active) closeTab(state.active);
        return;
      }
      if (mod && key === "Tab") {
        e.preventDefault();
        var st = load();
        if (st.tabs.length < 2) return;
        var ix = 0;
        for (var i = 0; i < st.tabs.length; i++) {
          if (st.tabs[i].id === st.active) {
            ix = i;
            break;
          }
        }
        ix = e.shiftKey
          ? (ix - 1 + st.tabs.length) % st.tabs.length
          : (ix + 1) % st.tabs.length;
        switchTab(st.tabs[ix].id);
      }
    },
    true
  );

  if (!deskOk()) return;
  syncHere();
  paint();
  function restoreSoon() {
    var st = load();
    restoreDraftFor(st.active);
    setTimeout(function () {
      restoreDraftFor(st.active);
    }, 50);
    setTimeout(function () {
      restoreDraftFor(st.active);
    }, 250);
  }
  restoreSoon();
  window.addEventListener("pageshow", function () {
    if (!deskOk()) return;
    syncHere();
    paint();
    restoreSoon();
  });
  window.addEventListener("pagehide", function () {
    if (!deskOk()) return;
    captureActiveDraft();
  });
  document.addEventListener(
    "submit",
    function () {
      var st = load();
      dropDraftFor(st.active);
    },
    true
  );
})();
/* /pocket-work-tabs */

(function () {
  function bootInjector() {
    document.addEventListener("submit", function (e) {
      var form = e.target && e.target.closest ? e.target.closest("form.pg-injector") : null;
      if (!form) return;
      e.preventDefault();
      var fields = {};
      var pocket = "";
      var land = "here";
      var els = form.querySelectorAll("[name]");
      for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var name = el.getAttribute("name") || "";
        var val = el.value != null ? String(el.value) : "";
        if (name === "pocket") pocket = val;
        else if (name === "land") land = val;
        else if (name.indexOf("f_") === 0) fields[name.slice(2)] = val;
      }
      var btn = form.querySelector("button");
      if (btn) btn.disabled = true;
      fetch("/api/insert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pocket: pocket, land: land, fields: fields }),
      })
        .then(function (r) {
          return r.json().then(function (data) {
            if (!r.ok) throw new Error((data && data.error) || "insert failed");
            return data;
          });
        })
        .then(function (data) {
          if (data && data.href) window.location.assign(data.href);
          else window.location.reload();
        })
        .catch(function (err) {
          if (btn) btn.disabled = false;
          window.alert((err && err.message) || "insert failed");
        });
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootInjector);
  } else {
    bootInjector();
  }
})();






/* codelook-async — load {{codelook}} cites without blocking first paint */
(function () {
  function fail(el, msg) {
    el.classList.remove("is-loading");
    el.classList.add("taglook-empty");
    el.removeAttribute("data-codelook");
    el.innerHTML = msg || "cites could not load";
  }

  function fill(el, html) {
    var wrap = document.createElement("div");
    wrap.innerHTML = String(html || "").trim();
    var node = wrap.firstElementChild;
    if (!node) {
      fail(el, "cites could not load");
      return;
    }
    el.replaceWith(node);
  }

  function loadOne(el) {
    var h = el.getAttribute("data-h") || "";
    var p = el.getAttribute("data-p") || "";
    var code = el.getAttribute("data-code") || "";
    var url = "/api/codelook?";
    var bits = [];
    if (h) bits.push("h=" + encodeURIComponent(h));
    if (p) bits.push("p=" + encodeURIComponent(p));
    if (code) bits.push("code=" + encodeURIComponent(code));
    if (!bits.length) {
      fail(el, "cites could not load");
      return;
    }
    url += bits.join("&");
    fetch(url, { credentials: "same-origin", cache: "no-store" })
      .then(function (r) {
        return r.text().then(function (text) {
          if (!r.ok) throw new Error(text || ("HTTP " + r.status));
          return text;
        });
      })
      .then(function (html) {
        fill(el, html);
      })
      .catch(function () {
        fail(el, "cites could not load");
      });
  }

  function bootCodelook() {
    var nodes = document.querySelectorAll(".codelook.is-loading[data-codelook]");
    for (var i = 0; i < nodes.length; i++) {
      loadOne(nodes[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootCodelook);
  } else {
    bootCodelook();
  }
})();

