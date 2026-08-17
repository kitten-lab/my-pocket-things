/**
 * Pocket Go webBAR — back / forward / refresh / GO.
 * Address bar shows go.library/… (vault). Other go.{{name}} hosts are later doors.
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

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function paintBar() {
    var el = barEl();
    if (!el) return;
    var raw = pocketPath();
    el.setAttribute("data-raw", raw);
    if (el === document.activeElement && el.getAttribute("contenteditable") === "true") {
      el.textContent = raw;
      return;
    }
    var hm = raw.match(/^go\.([A-Za-z0-9_-]+)(\/.*)?$/i);
    if (!hm) {
      el.textContent = raw;
      return;
    }
    var bits = ['<a href="/">go.' + esc(hm[1]) + "</a>"];
    var rest = (hm[2] || "").replace(/^\/+/, "").replace(/\/+$/, "");
    var trailing = /\/\s*$/.test(hm[2] || "/");
    if (rest) {
      var parts = rest.split("/");
      var acc = [];
      parts.forEach(function (part) {
        acc.push(part);
        bits.push("/");
        bits.push('<a href="/?p=' + encodeURI(acc.join("/")) + '">' + esc(part) + "</a>");
      });
    }
    if (trailing) bits.push("/");
    el.removeAttribute("contenteditable");
    el.innerHTML = bits.join("");
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

  window.WWWRefresh = function WWWRefresh() {
    try {
      window.location.reload();
    } catch (e) {
      window.location.href = window.location.href;
    }
  };

  window.WWWReload = window.WWWRefresh;

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
      window.location.assign(raw);
      return;
    }

    var host = "library";
    var path = raw;
    var hm = raw.match(/^go\.([A-Za-z0-9_-]+)(\/.*)?$/i);
    if (hm) {
      host = hm[1].toLowerCase();
      path = hm[2] || "/";
    } else if (raw.charAt(0) !== "/") {
      path = "/" + raw;
    }

    if (host !== "library") {
      console.warn("pocket door later — not this cut:", "go." + host);
      return;
    }
    if (path === "/" || path === "") {
      window.location.assign("/");
      return;
    }
    var p = path.replace(/^\/+/, "");
    window.location.assign("/?p=" + encodeURI(p));
  };

  var el = barEl();
  if (!el) {
    console.warn("webBAR: #wwwBar missing");
    return;
  }

  paintBar();
  window.addEventListener("pageshow", paintBar);

  el.addEventListener("dblclick", function (e) {
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
    var q = u.searchParams.get("q");
    if (q) return "go.library  [[" + q + "]]";
    var t = u.searchParams.get("t");
    if (t) return "go.library  #" + t;
    var p = u.searchParams.get("p");
    if (p) {
      p = p.replace(/\\/g, "/").replace(/^\/+/, "");
      if (!/\.md$/i.test(p) && p.slice(-1) !== "/") p += "/";
      return "go.library/" + p;
    }
    if (u.pathname === "/" || u.pathname === "") return "go.library/";
    return "go.library";
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
})();
