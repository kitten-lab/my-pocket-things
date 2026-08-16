/**
 * Pocket Library webBAR — back / forward / refresh / GO.
 * Address bar shows a pocket path (/world/note.md), not ?p=.
 * Paths that are not vault paths are later pocket doors (my-pocket-internet).
 */
(function () {
  var FUTURE = ["mythleak", "chesters-imports", "star-lux", "starlux"];

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

  function paintBar() {
    var el = barEl();
    if (!el) return;
    el.textContent = pocketPath();
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

  function isFutureDoor(raw) {
    var slug = raw.replace(/^\/+/, "").split("/")[0].toLowerCase();
    return FUTURE.indexOf(slug) !== -1;
  }

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
    if (raw.charAt(0) !== "/") {
      raw = "/" + raw;
    }
    if (raw === "/") {
      window.location.assign("/");
      return;
    }
    // later: my-pocket-internet rooms (mythleak, star-lux, …)
    if (isFutureDoor(raw)) {
      console.warn("pocket door later — not this cut:", raw);
      return;
    }
    var p = raw.replace(/^\/+/, "");
    window.location.assign("/?p=" + encodeURI(p));
  };

  var el = barEl();
  if (!el) {
    console.warn("webBAR: #wwwBar missing");
    return;
  }

  paintBar();
  window.addEventListener("pageshow", paintBar);

  el.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      event.preventDefault();
      window.LetsGO();
    }
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
})();
