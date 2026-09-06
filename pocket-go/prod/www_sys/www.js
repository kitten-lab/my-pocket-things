/**
 * Pocket Go webBAR — back / forward / refresh / GO.
 * Address bar shows go.{host}/… for any live host. Folders in ~hosts become doors.
 */
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
    if (el === document.activeElement && el.getAttribute("contenteditable") === "true") {
      el.textContent = shown;
      return;
    }
    el.removeAttribute("contenteditable");
    el.textContent = shown;
  }

  function editBar() {
    var el = barEl();
    if (!el) return;
    var raw = el.getAttribute("data-raw") || pocketPath();
    el.setAttribute("contenteditable", "true");
    el.textContent = raw;
    el.focus();
    try {
      var range = document.createRange();
      range.selectNodeContents(el);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
    } catch (e) {}
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
    var hm = raw.match(/^go\.([A-Za-z0-9_-]+)(\/.*)?$/i);
    if (hm) {
      host = hm[1].toLowerCase();
      path = hm[2] || "/";
    } else if (/^(start\.md|start\/?)?$/i.test(raw) || raw === "/") {
      window.location.assign("/?home=1");
      return;
    } else if (raw.charAt(0) !== "/") {
      path = "/" + raw;
    }

    if (!host) {
      if (path === "/" || path === "" || /^\/?start(\.md)?\/?$/i.test(path)) {
        window.location.assign("/?home=1");
        return;
      }
      window.location.assign("/?p=" + encodeURI(path.replace(/^\/+/, "")));
      return;
    }
    var dest = "/?h=" + encodeURIComponent(host);
    if (path && path !== "/") {
      dest += "&p=" + encodeURI(path.replace(/^\/+/, ""));
    }
    window.location.assign(dest);
  };

  var el = barEl();
  if (!el) {
    console.warn("webBAR: #wwwBar missing");
    return;
  }

  paintBar();
  window.addEventListener("pageshow", paintBar);

  el.addEventListener("click", function (e) {
    e.preventDefault();
    editBar();
  });
  el.addEventListener("keydown", function (event) {
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
    var shell = document.querySelector(".wwwExplorer_innerShell");
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
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a || !a.closest(".wwwExplorer_innerShell")) return;
      var href = a.getAttribute("href") || "";
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
    var host = u.searchParams.get("h");
    var go = host ? "go." + host : "start";
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
      var who = m === "agent" ? "agent index" : "librarian catalog";
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
      var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
      if (!a) return;
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
    if (!li || !li.closest(".wwwExplorer_innerShell")) return null;
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

  function faceDoor(from) {
    var art = from && from.closest ? from.closest("article.face[data-href]") : null;
    if (!art || !art.closest(".wwwExplorer_innerShell")) return null;
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
    if (!li.closest(".wwwExplorer_innerShell")) return;
    e.preventDefault();
    markBullet(li);
  });
})();
