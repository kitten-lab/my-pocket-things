/**
 * Pocket Go shelves — README, Librarian, Charlie (weaver), Detective, TPS.
 * Independent drawers. README is one letter, not slips.
 * Ctrl+Shift+B bios · Ctrl+Shift+L librarian · Ctrl+Shift+C charlie · Ctrl+Shift+A detective · Ctrl+Shift+T tps · Ctrl+Shift+D cards.
 * Ctrl+Shift+O opens all cabinets as windows.
 * Gem: Cabinets → mouth → Window or Dock. Dock again puts the overlay away.
 * Window / hotkey opens a sidecar that follows the desk's page.
 * Charlie / Librarian / Detective / TPS / crate lookup opens a Pocket Go window.
 * Lookup windows are not a here — cabinets stay on the desk.
 */
(function () {
  var SIGIL = /(^|[^A-Za-z0-9._:/-])([#$^@])([A-Za-z0-9._:/-]+)/g;
  function mouthCanon(raw) {
    var s = String(raw || "").trim().toLowerCase();
    if (s === "agt" || s === "agent" || s === "det") return "detective";
    if (s === "lib") return "librarian";
    if (s === "cha") return "charlie";
    return s;
  }

  function crateIdOf(raw) {
    var s = String(raw || "").trim();
    var m = s.match(/^(?:crate\.)?([A-Fa-f0-9]{16})$/i);
    return m ? "crate." + m[1].toUpperCase() : "";
  }

  var HOUSES = [
    {
      id: "readme",
      api: "/api/readme",
      openKey: "pocket-go-readme-open",
      openKeyLegacy: "pocket-go-rules-open",
      bodyClass: "readme-open",
      menu: "BIOS",
      title: "BIOS",
      kicker: "THIS ROOM",
      placeholder: "how we use this space.",
      empty: "Nothing in the letter yet.",
      issue: "Keep",
      slips: ["letter", "letter"],
      hotkey: { key: "b", shift: true },
      skin: "is-readme",
      kind: "letter",
      pop: { w: 920, h: 640 },
    },
    {
      id: "librarian",
      api: "/api/librarian",
      openKey: "pocket-go-librarian-open",
      bodyClass: "librarian-open",
      menu: "Librarian",
      title: "Librarian",
      kicker: "Catalog",
      placeholder: "",
      empty: "No fields on this bag yet. Add meta data or lore.",
      issue: "Confirm",
      slips: ["field", "fields"],
      hotkey: { key: "l", shift: true },
      skin: "is-catalog is-librarian",
      kind: "catalog",
      pop: { w: 440, h: 760 },
      metaHint: "e.g. author",
    },
    {
      id: "charlie",
      api: "/api/charlie",
      openKey: "pocket-go-charlie-open",
      bodyClass: "charlie-open",
      menu: "Charlie",
      title: "CHARLIE",
      kicker: "WEAVE",
      placeholder: "a tag",
      empty: "Nothing on this page yet. A thread, a tag, a hash, or lore.",
      issue: "write",
      slips: ["tag", "tags"],
      hotkey: { key: "c", shift: true },
      skin: "is-charlie",
      kind: "tags",
      pop: { w: 440, h: 760 },
      lore: true,
      loreClassHint: "e.g. thread",
    },
    {
      id: "detective",
      api: "/api/detective",
      openKey: "pocket-go-detective-open",
      openKeyLegacy: "pocket-go-agent-open",
      bodyClass: "detective-open",
      menu: "Detective",
      title: "DETECTIVE",
      kicker: "BLOTTER",
      placeholder: "",
      empty: "No slips on this bag yet. Pin a thought, or add lore.",
      issue: "Confirm",
      slips: ["slip", "slips"],
      hotkey: { key: "a", shift: true },
      skin: "is-catalog is-detective is-agent",
      kind: "catalog",
      pop: { w: 440, h: 760 },
      metaHint: "e.g. faction",
    },
    {
      id: "tps",
      api: "/api/tps",
      openKey: "pocket-go-tps-open",
      bodyClass: "tps-open",
      menu: "TPS",
      title: "TPS",
      kicker: "COVER SHEET",
      placeholder: "",
          empty: "No cover sheet on this worldline yet. Stamp a when, pin an event, or it won't know where to go.",
      issue: "Stamp",
      slips: ["date", "dates"],
      hotkey: { key: "t", shift: true },
      skin: "is-tps",
      kind: "tps",
      pop: { w: 440, h: 760 },
      lore: true,
      loreClassHint: "e.g. event",
      defaultMaker: "TPS event",
    },
    {
      id: "cards",
      api: "/api/cards",
      openKey: "pocket-go-cards-open",
      bodyClass: "cards-open",
      menu: "Cards",
      title: "CARDS",
      kicker: "DECK",
      placeholder: "",
      empty: "No lore cards on this page or its shell yet.",
      issue: "View",
      slips: ["card", "cards"],
      hotkey: { key: "d", shift: true },
      skin: "is-cards",
      kind: "cards",
      pop: { w: 520, h: 760 },
    },
  ];

  function htmlRoot() {
    return document.documentElement;
  }

  var SIDECAR = (function () {
    var q = "";
    try {
      q = new URLSearchParams(window.location.search).get("sidecar") || "";
    } catch (e) {
      q = "";
    }
    q = mouthCanon(String(q).toLowerCase());
    for (var i = 0; i < HOUSES.length; i++) {
      if (HOUSES[i].id === q) return q;
    }
    return "";
  })();

  var HERE_KEY = "pocket-go-here";
  var GO_KEY = "pocket-go-go";
  var SOFT_KEY = "pocket-go-soft";
  var DESK_KEY = "pocket-go-desk";
  var POP_KEY = "pocket-go-pop";
  var WINDOW_KEY = "pocket-go-window";
  var KEEP_FACE_KEY = "pocket-go-readme-keep";
  var here = { vault: "", off: true };
  var followFns = [];
  var followTimer = 0;
  var hereChannel = null;
  var hereWait = [];
  var DOCK_KEY = "pocket-go-dock";
  var shelves = {};

  function dockRemember(id) {
    try {
      if (id) sessionStorage.setItem(DOCK_KEY, id);
      else sessionStorage.removeItem(DOCK_KEY);
    } catch (e) {}
  }

  function dockWanted() {
    try {
      var id = sessionStorage.getItem(DOCK_KEY) || "";
      if (id === "agent") id = "detective";
      if (id) return id;
      for (var i = 0; i < HOUSES.length; i++) {
        var cfg = HOUSES[i];
        if (sessionStorage.getItem(cfg.openKey) === "1") return cfg.id;
        if (cfg.openKeyLegacy && sessionStorage.getItem(cfg.openKeyLegacy) === "1") {
          return cfg.id;
        }
      }
    } catch (e) {}
    return "";
  }

  function paintDockRoom(mode) {
    if (SIDECAR || htmlRoot().hasAttribute("data-sheet")) return;
    var roomy = mode === "expanded" || mode === "maximized";
    htmlRoot().classList.toggle("deck-dock-roomy", !!roomy);
  }

  function askWindowMode() {
    var a = window.pywebview && window.pywebview.api;
    if (!a || !a.get_window_mode) return false;
    try {
      var r = a.get_window_mode();
      if (r && typeof r.then === "function") {
        r.then(function (info) {
          paintDockRoom(info && info.mode);
        }).catch(function () {});
      } else if (r && r.mode) {
        paintDockRoom(r.mode);
      }
      return true;
    } catch (e) {
      return false;
    }
  }

  function bindDockRoom() {
    var prev = window.DECK_ON_WINDOW_MODE;
    window.DECK_ON_WINDOW_MODE = function (mode, size) {
      paintDockRoom(mode);
      if (typeof prev === "function") prev(mode, size);
    };
    if (!askWindowMode()) {
      window.addEventListener("pywebviewready", function () {
        askWindowMode();
      });
    }
  }

  function dockOnly(id) {
    /* Allow BIOS (readme) + one catalog rail together.
       Opening BIOS must not kick Charlie; opening Charlie must not kick BIOS.
       Catalogs still displace each other. */
    if (id === "readme") return;
    Object.keys(shelves).forEach(function (sid) {
      if (sid === id) return;
      if (sid === "readme") return;
      var other = shelves[sid];
      if (other && other.isOpen && other.isOpen() && other.applyOpen) {
        other.applyOpen(false);
      }
    });
  }

  function isDesk() {
    return !SIDECAR && htmlRoot().getAttribute("data-librarian") !== "off";
  }

  function vaultFromDom() {
    if (htmlRoot().getAttribute("data-librarian") === "off") return "";
    if (!htmlRoot().hasAttribute("data-vault")) return "";
    var v = (htmlRoot().getAttribute("data-vault") || "").replace(/\\/g, "/");
    if (!v || v === "/") return "/";
    return v.replace(/^\/+/, "");
  }

  function offFromDom() {
    return htmlRoot().getAttribute("data-librarian") === "off";
  }

  function vaultPath() {
    if (SIDECAR) return here.vault || (here.off ? "" : "/");
    return vaultFromDom();
  }

  function librarianOff() {
    if (SIDECAR) return !!here.off;
    return offFromDom();
  }

  function pinDesk() {
    if (SIDECAR || offFromDom()) return;
    try {
      sessionStorage.setItem(
        DESK_KEY,
        JSON.stringify({
          href: window.location.pathname + window.location.search,
          vault: vaultFromDom(),
          t: Date.now(),
        })
      );
    } catch (e) {}
  }

  function nudgeDesk(href) {
    href = String(href || "").trim();
    if (!href || href.charAt(0) === "#") return;
    // Fan out: pywebview sidecars often lack opener; BroadcastChannel can miss
    // a desk — localStorage wakes every other same-origin window.
    try {
      localStorage.setItem(
        GO_KEY,
        JSON.stringify({ href: href, t: Date.now() })
      );
    } catch (e) {}
    if (window.opener && !window.opener.closed) {
      try {
        window.opener.location.href = href;
      } catch (e) {}
    }
    if (hereChannel) {
      try {
        hereChannel.postMessage({ type: "go", href: href });
      } catch (e) {}
    }
  }
  window.nudgeDesk = nudgeDesk;

  function takeGoIntent(raw) {
    if (SIDECAR || !isDesk()) return;
    try {
      var msg = typeof raw === "string" ? JSON.parse(raw) : raw;
      var href = msg && msg.href ? String(msg.href).trim() : "";
      if (!href || href.charAt(0) === "#") return;
      var hereNow = window.location.pathname + window.location.search;
      if (hereNow === href) return;
      window.location.assign(href);
    } catch (e) {}
  }

  function bootGoDesk() {
    if (SIDECAR) return;
    window.addEventListener("storage", function (e) {
      if (e.key === GO_KEY && e.newValue) takeGoIntent(e.newValue);
      if (e.key === SOFT_KEY && e.newValue) takeSoftReload();
    });
  }

  function sheetPath(href) {
    return String(href || "").split("?")[0];
  }

  function chromeSheet(href) {
    var n = sheetPath(href);
    return (
      n === "/www.css" ||
      n === "/dress.css" ||
      n === "/styles/fonts.css" ||
      n.indexOf("/styles/lorecard") === 0 ||
      n.indexOf("/librarian.css") === 0
    );
  }

  function coatSheet(href) {
    var n = sheetPath(href);
    return n.indexOf("/styles/") === 0 && n.slice(-4) === ".css" && !chromeSheet(href);
  }

  function bustSheetLink(oldLink, href) {
    var path = sheetPath(href);
    if (!path) return;
    var add = document.createElement("link");
    add.rel = "stylesheet";
    add.href = path + "?_live=" + Date.now();
    if (oldLink && oldLink.parentNode) {
      oldLink.parentNode.insertBefore(add, oldLink.nextSibling);
      oldLink.parentNode.removeChild(oldLink);
    } else {
      document.head.appendChild(add);
    }
  }

  function syncLiveHead(doc) {
    function copyVarStyle(token) {
      var from = null;
      var styles = doc.querySelectorAll("head style");
      var i;
      for (i = 0; i < styles.length; i++) {
        var text = styles[i].textContent || "";
        if (text.indexOf(token) >= 0 && text.indexOf(":root") >= 0) {
          from = styles[i];
          break;
        }
      }
      if (!from) return;
      var live = document.querySelectorAll("head style");
      for (i = 0; i < live.length; i++) {
        var liveText = live[i].textContent || "";
        if (live[i].getAttribute("data-cm")) continue;
        if (liveText.indexOf(token) >= 0 && liveText.indexOf(":root") >= 0) {
          live[i].textContent = from.textContent;
          return;
        }
      }
    }
    copyVarStyle("--note-accent");
    copyVarStyle("--card-strip");
    var wanted = {};
    var links = doc.querySelectorAll('head link[rel="stylesheet"]');
    var i;
    for (i = 0; i < links.length; i++) {
      var href = links[i].getAttribute("href") || "";
      if (!href || chromeSheet(href)) continue;
      wanted[sheetPath(href)] = href;
    }
    var liveLinks = Array.prototype.slice.call(
      document.querySelectorAll('head link[rel="stylesheet"]')
    );
    var seen = {};
    for (i = 0; i < liveLinks.length; i++) {
      var liveHref = liveLinks[i].getAttribute("href") || "";
      if (chromeSheet(liveHref)) continue;
      var path = sheetPath(liveHref);
      if (wanted[path]) {
        if (seen[path]) {
          if (liveLinks[i].parentNode) liveLinks[i].parentNode.removeChild(liveLinks[i]);
          continue;
        }
        seen[path] = true;
        bustSheetLink(liveLinks[i], wanted[path]);
        delete wanted[path];
      } else if (coatSheet(liveHref)) {
        if (liveLinks[i].parentNode) liveLinks[i].parentNode.removeChild(liveLinks[i]);
      }
    }
    Object.keys(wanted).forEach(function (path) {
      bustSheetLink(null, wanted[path]);
    });
  }

  function refreshLivePage() {
    var url = window.location.pathname + window.location.search;
    var sep = url.indexOf("?") >= 0 ? "&" : "?";
    return fetch(url + sep + "_cb=" + Date.now(), {
      cache: "no-store",
      credentials: "same-origin",
    })
      .then(function (r) {
        if (!r.ok) throw new Error("live refresh");
        return r.text();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        var next = doc.getElementById("browserWindow");
        var cur = document.getElementById("browserWindow");
        if (next && cur) {
          var y = cur.scrollTop;
          cur.innerHTML = next.innerHTML;
          cur.scrollTop = y;
        }
        var src = doc.documentElement;
        var dst = document.documentElement;
        ["data-pocket", "data-vault", "data-route", "data-pinned"].forEach(function (a) {
          if (src.hasAttribute(a)) dst.setAttribute(a, src.getAttribute(a));
          else if (a !== "data-pocket") dst.removeAttribute(a);
        });
        if (doc.title) document.title = doc.title;
        var nt = doc.querySelector(".wwwExplorer_title");
        var ct = document.querySelector(".wwwExplorer_title");
        if (nt && ct) ct.textContent = nt.textContent;
        if (typeof window.paintBar === "function") window.paintBar();
        syncLiveHead(doc);
      });
  }
  window.refreshLivePage = refreshLivePage;

  var softTimer = 0;
  function takeSoftReload() {
    if (SIDECAR || !isDesk()) return;
    if (softTimer) window.clearTimeout(softTimer);
    softTimer = window.setTimeout(function () {
      softTimer = 0;
      refreshLivePage().catch(function () {});
    }, 40);
  }
  window.takeSoftReload = takeSoftReload;

  function refreshDesk() {
    // BIOS Keep: soft-load the desk so the page picks up the save without
    // a gray full reload. Pop-out: fan out like GO (localStorage + opener +
    // BroadcastChannel) — Epiphany/LAN sidecars often lack opener, and BC
    // can miss a desk.
    try {
      localStorage.setItem(SOFT_KEY, JSON.stringify({ t: Date.now() }));
    } catch (e) {}
    if (window.opener && !window.opener.closed) {
      try {
        if (typeof window.opener.takeSoftReload === "function") {
          window.opener.takeSoftReload();
        }
      } catch (e) {}
    }
    if (hereChannel) {
      try {
        hereChannel.postMessage({ type: "reload" });
      } catch (e) {}
    }
    if (!SIDECAR && isDesk()) {
      return refreshLivePage().catch(function () {
        return null;
      });
    }
    return Promise.resolve();
  }
  window.refreshDesk = refreshDesk;

  function readDeskPin() {
    try {
      var pin = JSON.parse(sessionStorage.getItem(DESK_KEY) || "null");
      if (!pin || typeof pin !== "object") return null;
      return pin;
    } catch (e) {
      return null;
    }
  }

  function lookupFromHref(href) {
    href = String(href || "").trim();
    if (!href) return null;
    try {
      var u = new URL(href, window.location.href);
      if (u.origin && u.origin !== window.location.origin) return null;
      var card = String(u.searchParams.get("card") || "").trim();
      if (card) {
        var cardId = crateIdOf(card) || card;
        return {
          kind: "card",
          key: "card:" + cardId,
          title: cardId,
          hash: "#card=" + encodeURIComponent(cardId),
          href: "/?card=" + encodeURIComponent(cardId),
        };
      }
      var k = String(u.searchParams.get("k") || u.searchParams.get("crate") || "").trim();
      if (k) {
        return {
          kind: "crate",
          key: "crate:" + k,
          title: k,
          hash: "#k=" + encodeURIComponent(k),
          fetch: "/?k=" + encodeURIComponent(k) + "&bay=1",
          href: "/?k=" + encodeURIComponent(k),
        };
      }
      var c = String(u.searchParams.get("c") || u.searchParams.get("t") || "")
        .replace(/^#/, "")
        .trim();
      var asCrate = crateIdOf(c);
      if (asCrate) {
        return {
          kind: "crate",
          key: "crate:" + asCrate,
          title: asCrate,
          hash: "#k=" + encodeURIComponent(asCrate),
          fetch: "/?k=" + encodeURIComponent(asCrate) + "&bay=1",
          href: "/?k=" + encodeURIComponent(asCrate),
        };
      }
      if (c) {
        var asRole = String(u.searchParams.get("as") || "")
          .trim()
          .toLowerCase();
        if (asRole === "pin") asRole = "tag";
        if (asRole !== "tag" && asRole !== "hash") asRole = "";
        var extra = asRole ? "&as=" + encodeURIComponent(asRole) : "";
        return {
          kind: "charlie",
          key: "charlie:" + c + ":" + (asRole || "all"),
          title: asRole === "hash" ? "#" + c : c,
          hash: "#c=" + encodeURIComponent(c) + extra,
          fetch: "/?h=code.tags&p=" + encodeURIComponent(String(c).replace(/^#/, "").toLowerCase().replace(/\s+/g, "-") + ".md"),
          href: "/?h=code.tags&p=" + encodeURIComponent(String(c).replace(/^#/, "").toLowerCase().replace(/\s+/g, "-") + ".md"),
        };
      }
      var m = mouthCanon(String(u.searchParams.get("m") || "librarian"));
      if (m === "tps") {
        var keys = ["title", "month", "day", "year", "hour", "clock", "unix"];
        var f = String(u.searchParams.get("f") || "").trim().toLowerCase();
        var v = String(u.searchParams.get("v") || "").trim();
        var parts = ["m=tps"];
        var bits = [];
        keys.forEach(function (k) {
          var val = String(u.searchParams.get(k) || "").trim();
          if (!val && k === f) val = v;
          if (!val) return;
          parts.push(k + "=" + encodeURIComponent(val));
          bits.push(k + " · " + val);
        });
        var sort = String(u.searchParams.get("sort") || "").trim();
        var dir = String(u.searchParams.get("dir") || "").trim();
        if (sort) parts.push("sort=" + encodeURIComponent(sort));
        if (dir) parts.push("dir=" + encodeURIComponent(dir));
        if (!bits.length && !f) return null;
        var q = parts.join("&");
        return {
          kind: "tps",
          key: "tps:" + q,
          title: bits.join(" / ") || "tps",
          hash: "#" + q,
          fetch: "/?" + q + "&bay=1",
          href: "/?" + q,
        };
      }
      var f = String(u.searchParams.get("f") || "").trim();
      var v = String(u.searchParams.get("v") || "").trim();
      if (m !== "librarian" && m !== "detective") return null;
      if (!f && !v) return null;
      var bin = String(u.searchParams.get("bin") || "").trim().toLowerCase();
      if (bin !== "host" && bin !== "value") bin = "";
      var q =
        "m=" +
        encodeURIComponent(m) +
        (f ? "&f=" + encodeURIComponent(f) : "") +
        (v ? "&v=" + encodeURIComponent(v) : "") +
        (bin ? "&bin=" + encodeURIComponent(bin) : "");
      return {
        kind: m,
        key: m + ":" + f + ":" + v + ":" + bin,
        title: v ? (f ? f + " · " + v : v) : f,
        hash: "#" + q,
        fetch: "/?" + q + "&bay=1",
        href: "/?" + q,
      };
    } catch (e) {
      return null;
    }
  }

  function baySlugFromHref(href) {
    var look = lookupFromHref(href);
    return look && look.kind === "charlie" ? look.title.replace(/^#/, "") : "";
  }

  function snapshotHere() {
    if (offFromDom()) {
      var pin = readDeskPin();
      if (pin && pin.vault) {
        return {
          type: "here",
          vault: String(pin.vault || "").replace(/\\/g, "/"),
          off: false,
          t: Date.now(),
        };
      }
    }
    return {
      type: "here",
      vault: vaultFromDom(),
      off: offFromDom(),
      t: Date.now(),
    };
  }

  function paintSidecarTitle() {
    if (!SIDECAR) return;
    var house = null;
    for (var i = 0; i < HOUSES.length; i++) {
      if (HOUSES[i].id === SIDECAR) house = HOUSES[i];
    }
    var label = house ? house.title : SIDECAR;
    var path = here.off ? "…" : here.vault && here.vault !== "/" ? "/" + here.vault.replace(/^\//, "") : "/";
    var el = $("sidecarTitle");
    // readme title bar is owned by the letter face (room letter / shell / paper / css)
    if (SIDECAR === "readme") {
      document.title = label + " · " + path;
      return;
    }
    if (SIDECAR === "charlie" || SIDECAR === "tps") {
      var short = String(path || "/").replace(/\/$/, "").split("/").pop() || (SIDECAR === "tps" ? "report" : "loom");
      short = short.replace(/^go\./, "");
      if (el) el.textContent = short;
      document.title = (SIDECAR === "tps" ? "TPS" : "CHARLIE") + " · " + short;
      return;
    }
    if (el) el.textContent = path;
    document.title = label + " · " + path;
  }

  function notifyHereWait() {
    var fns = hereWait.slice();
    hereWait = [];
    fns.forEach(function (fn) {
      try {
        fn();
      } catch (e) {}
    });
  }

  function applyHere(msg) {
    if (!msg || typeof msg !== "object") return;
    var vault = String(msg.vault || "").replace(/\\/g, "/");
    if (!vault || vault === "/") vault = "/";
    var off = !!msg.off;
    var same = here.vault === vault && here.off === off;
    here.vault = vault;
    here.off = off;
    paintSidecarTitle();
    notifyHereWait();
    if (same) return;
    if (followTimer) window.clearTimeout(followTimer);
    followTimer = window.setTimeout(function () {
      followFns.forEach(function (fn) {
        try {
          fn();
        } catch (e) {}
      });
    }, 30);
  }

  function pingDeck() {
    if (!SIDECAR || !hereChannel) return;
    try {
      hereChannel.postMessage({ type: "ping" });
    } catch (e) {}
  }

  function withFreshVault(fn) {
    if (!SIDECAR || !hereChannel) {
      fn(vaultPath());
      return;
    }
    var settled = false;
    function done() {
      if (settled) return;
      settled = true;
      fn(vaultPath());
    }
    hereWait.push(done);
    pingDeck();
    window.setTimeout(done, 220);
  }

  function ontoName(pocket) {
    var p = String(pocket || "").replace(/\\/g, "/");
    var name = p.split("/").filter(Boolean).pop() || p || "this page";
    return name.replace(/\.md$/i, "");
  }

  function publishHere() {
    if (!isDesk()) return;
    pinDesk();
    var msg = snapshotHere();
    try {
      localStorage.setItem(HERE_KEY, JSON.stringify(msg));
    } catch (e) {}
    if (hereChannel) {
      try {
        hereChannel.postMessage(msg);
      } catch (e) {}
    }
  }

  function seedHere() {
    if (!SIDECAR) {
      here.vault = vaultFromDom();
      here.off = offFromDom();
      return;
    }
    try {
      var raw = localStorage.getItem(HERE_KEY);
      if (!raw) return;
      var msg = JSON.parse(raw);
      here.vault = String(msg.vault || "").replace(/\\/g, "/");
      if (!here.vault || here.vault === "/") here.vault = "/";
      here.off = !!msg.off;
    } catch (e) {}
  }

  function bootHere() {
    try {
      hereChannel = new BroadcastChannel("pocket-go-here");
    } catch (e) {
      hereChannel = null;
    }
    function sendLookup(look) {
      if (!look || !look.key) return false;
      if (window.opener && !window.opener.closed) {
        try {
          if (typeof window.opener.openLookup === "function") {
            window.opener.openLookup(look);
            return true;
          }
          if (look.kind === "charlie" && typeof window.opener.openTagbay === "function") {
            window.opener.openTagbay(look.title.replace(/^#/, ""));
            return true;
          }
        } catch (e) {}
      }
      if (hereChannel) {
        try {
          hereChannel.postMessage({ type: "lookup", look: look });
          return true;
        } catch (e) {}
      }
      return false;
    }

    function sendDeck(href) {
      href = String(href || "").trim();
      if (!href || href.charAt(0) === "#") return;
      var look = lookupFromHref(href);
      if (look) {
        if (launchLookup(look)) return;
        if (sendLookup(look)) return;
      }
      nudgeDesk(href);
    }

    if (hereChannel) {
      hereChannel.onmessage = function (ev) {
        var msg = ev.data || {};
        if (!SIDECAR) {
          if (!isDesk()) return;
          if (msg.type === "ping") {
            try {
              hereChannel.postMessage(snapshotHere());
            } catch (e) {}
          }
          if (msg.type === "lookup" && msg.look) {
            if (launchLookup(msg.look)) return;
            if (typeof window.openLookup === "function") {
              window.openLookup(msg.look);
            }
            return;
          }
          if (msg.type === "bay" && msg.slug) {
            if (typeof window.openTagbay === "function") {
              window.openTagbay(msg.slug);
            }
            return;
          }
          if (msg.type === "go" && msg.href) {
            try {
              window.location.href = msg.href;
            } catch (e) {}
          }
          if (msg.type === "reload") {
            takeSoftReload();
          }
          return;
        }
        if (msg.type === "here" || msg.type === "pong" || msg.type === undefined) {
          applyHere(msg);
        }
      };
    }
    if (SIDECAR) {
      window.addEventListener("storage", function (e) {
        if (e.key !== HERE_KEY || !e.newValue) return;
        try {
          applyHere(JSON.parse(e.newValue));
        } catch (err) {}
      });
      document.addEventListener(
        "click",
        function (e) {
          var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
          if (!a) return;
          var href = a.getAttribute("href") || "";
          if (!href || href.charAt(0) === "#") return;
          if (a.getAttribute("target") === "_blank") return;
          e.preventDefault();
          sendDeck(href);
        },
        true
      );
      if (hereChannel) {
        try {
          hereChannel.postMessage({ type: "ping" });
        } catch (e) {}
      }
      paintSidecarTitle();
      window.addEventListener("focus", pingDeck);
      window.setInterval(pingDeck, 2000);
    } else if (isDesk()) {
      publishHere();
      window.addEventListener("pageshow", publishHere);
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) publishHere();
      });
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function charlieEndHtml(word, slot, cls, asRole) {
    var name = String(word || "").trim();
    if (!name) {
      return '<span class="cork-gap" data-slot="' + slot + '">·</span>';
    }
    var crate = crateIdOf(name);
    var href = crate
      ? "/?k=" + encodeURIComponent(crate)
      : "/?c=" + encodeURIComponent(name);
    if (!crate && asRole) href += "&as=" + encodeURIComponent(asRole);
    return (
      '<a class="' +
      (cls || "cork-name") +
      '" data-slot="' +
      slot +
      '" href="' +
      href +
      '">' +
      escapeHtml(name) +
      "</a>"
    );
  }

  function paintLeaf(leaf) {
    var s = String(leaf || "");
    var out = "";
    var last = 0;
    var m;
    SIGIL.lastIndex = 0;
    while ((m = SIGIL.exec(s))) {
      var start = m.index + m[1].length;
      out += escapeHtml(s.slice(last, start));
      var kind = CHIP[m[2]] || "tag";
      var mark = m[2] + m[3];
      var crate = kind === "cite" ? crateIdOf(m[3]) : "";
      if (crate) {
        out +=
          '<a class="lbr-chip lbr-cite" href="/?k=' +
          encodeURIComponent(crate) +
          '">' +
          escapeHtml(mark) +
          "</a>";
      } else {
        out +=
          '<span class="lbr-chip lbr-' +
          kind +
          '">' +
          escapeHtml(mark) +
          "</span>";
      }
      last = start + m[2].length + m[3].length;
    }
    out += escapeHtml(s.slice(last));
    return out;
  }

  function fmtWhen(unix) {
    if (!unix) return "";
    var d = new Date(unix * 1000);
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function $(id) {
    return document.getElementById(id);
  }

  function api(method, path, body) {
    var opts = { method: method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    return fetch(path, opts).then(function (res) {
      return res.text().then(function (text) {
        var data = {};
        try {
          data = text ? JSON.parse(text) : {};
        } catch (e) {
          data = { error: text || res.statusText };
        }
        if (!res.ok) {
          throw new Error(data.error || res.statusText || "request failed");
        }
        return data;
      });
    });
  }

  function openGoWindow(dest, wdt, hgt, title, winId, onStatus) {
    function tell(msg, bad) {
      if (typeof onStatus === "function") onStatus(msg, bad);
    }
    dest = String(dest || "/");
    wdt = wdt || 720;
    hgt = hgt || 780;
    title = title || "lookup";
    winId = String(winId || "lookup").replace(/[^A-Za-z0-9_-]+/g, "-").slice(0, 48) || "lookup";
    var a = window.pywebview && window.pywebview.api;
    if (a && a.new_window) {
      var ret;
      try {
        ret = a.new_window(dest, wdt, hgt, 300, 420, title, winId);
      } catch (e) {
        if (dest.indexOf("sidecar=") < 0) {
          tell("could not open window", true);
          return false;
        }
        try {
          ret = a.new_window();
        } catch (e2) {
          tell("could not open window", true);
          return false;
        }
      }
      Promise.resolve(ret).then(
        function (ok) {
          if (ok && String(ok).indexOf("err:") === 0) {
            tell(String(ok), true);
          }
        },
        function () {
          tell("could not open window", true);
        }
      );
      return true;
    }
    try {
      var w = window.open(
        dest,
        "pocket-go-" + winId,
        "width=" +
          wdt +
          ",height=" +
          hgt +
          ",menubar=no,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes"
      );
      if (!w) {
        tell("pop-up blocked — allow this host", true);
        return false;
      }
      w.focus();
    } catch (e) {
      tell("could not open window", true);
      return false;
    }
    return true;
  }

  function launchLookup(look, onStatus) {
    if (!look || !look.href) return false;
    var card = look.kind === "card";
    var wide = look.kind === "crate" || look.kind === "tps";
    return openGoWindow(
      look.href,
      card ? 440 : wide ? 860 : 640,
      card ? 680 : 820,
      look.title || "lookup",
      "look-" + String(look.key || look.kind || "x"),
      onStatus
    );
  }

  function openRail(cfg, onStatus) {
    var pop = cfg.pop || {};
    var wdt = pop.w || 440;
    var hgt = pop.h || 760;
    try {
      localStorage.setItem(
        POP_KEY,
        JSON.stringify({ house: cfg.id, t: Date.now() })
      );
    } catch (e) {}
    var dest = "/?sidecar=" + encodeURIComponent(cfg.id);
    if (openGoWindow(dest, wdt, hgt, cfg.title, cfg.id, onStatus)) return;
    try {
      localStorage.removeItem(POP_KEY);
    } catch (e) {}
  }

  function makeShelf(cfg) {
    var blot =
      cfg.kind === "letter"
        ? { body: "", pocket: "/", crate: "", route: "" }
        : cfg.kind === "catalog"
        ? { fields: [], lore: [], pocket: "/", crate: "" }
        : cfg.kind === "tps"
        ? { stamps: [], slices: {}, pocket: "/", crate: "" }
        : cfg.kind === "cards"
        ? { cards: [], html: "", pocket: "/", crate: "" }
        : { thoughts: [], pocket: "/", next: 1, crate: "" };
    var deckHits = null;
    var open = false;
    var suggest = { time: [], bool: [], input: [], textbox: [], class: [] };
    var modalMode = "";
    var editIndex = -1;
    var editLoreCrate = "";
    var attachMetaCache = null;
    var attachFaceCache = {};
    var ids = {
      drawer: cfg.id,
      count: cfg.id + "Count",
      path: cfg.id + "Path",
      composer: cfg.id + "Composer",
      leaf: cfg.id + "Leaf",
      status: cfg.id + "Status",
      stack: cfg.id + "Stack",
      crate: cfg.id + "Crate",
      rel: cfg.id + "Rel",
      to: cfg.id + "To",
      modal: cfg.id + "Modal",
      modalTitle: cfg.id + "ModalTitle",
      modalBody: cfg.id + "ModalBody",
      headers: cfg.id + "Headers",
      markdown: cfg.id + "Markdown",
      coat: cfg.id + "Coat",
    };
    var letterFace = "room";
    var letterEditMode = false;
    var helpSlug = "_index";
    var helpBlot = { pages: [], slug: "", title: "", body: "", body_html: "" };
    var helpEditMode = false;
    var helpReturnFace = "room";
    var helpOpen = false;
    var helpReturnEdit = false;
    var hostsBlot = {
      hosts: [],
      host: "",
      shell_headers: "",
      shell_markdown: "",
      letter_body: "",
      letter_html: "",
      letter_path: "",
      shell_path: "",
    };
    var hostsSlug = "";
    var hostsEditMode = false;
    var hostsReturnFace = "room";
    var hostsReturnEdit = false;
    var cratesReturnFace = "room";
    var cratesReturnEdit = false;
    var cratesQuery = "";
    var cratesTimer = null;
    var cratesSearchGen = 0;
    var cratesMode = "all";
    var letterWhich = "";
    var cmPullFromTextareas = function () {};
    var catalogOnto = "page";
    var pendingKeep = null;
    if (cfg.kind === "letter" && !SIDECAR) {
      try {
        pendingKeep = JSON.parse(sessionStorage.getItem(KEEP_FACE_KEY) || "null");
        sessionStorage.removeItem(KEEP_FACE_KEY);
        if (pendingKeep && Date.now() - Number(pendingKeep.t || 0) > 15000) pendingKeep = null;
      } catch (e) {
        pendingKeep = null;
      }
      if (pendingKeep) {
        letterFace = pendingKeep.face || "room";
        letterWhich = pendingKeep.which || "";
        letterEditMode = !!pendingKeep.edit;
      }
    }

    function snapshotEditorCaret() {
      var snap = { focused: "markdown", cursor: null, scroll: null };
      var head = $(ids.headers);
      var md = $(ids.markdown);
      var coat = $(ids.coat);
      var leaf = $(ids.leaf);
      var cm = null;
      if (letterFace === "page" && head && head._cm && head._cm.hasFocus()) {
        cm = head._cm;
        snap.focused = "headers";
      } else if (letterFace === "page" && md && md._cm) {
        cm = md._cm;
        snap.focused = "markdown";
      } else if (letterFace === "coat" && coat && coat._cm) {
        cm = coat._cm;
        snap.focused = "coat";
      } else if (leaf && leaf._cm) {
        cm = leaf._cm;
        snap.focused = "room";
      }
      if (cm) {
        try {
          snap.cursor = cm.getCursor();
          var sc = cm.getScrollInfo();
          snap.scroll = { left: sc.left, top: sc.top };
        } catch (e) {}
      }
      return snap;
    }

    function restoreEditorCaret(snap) {
      if (!snap || !snap.cursor) return false;
      var el =
        snap.focused === "headers"
          ? $(ids.headers)
          : snap.focused === "coat"
          ? $(ids.coat)
          : snap.focused === "room"
          ? $(ids.leaf)
          : $(ids.markdown);
      var cm = el && el._cm;
      if (!cm) return false;
      try {
        cm.setCursor(snap.cursor);
        if (snap.scroll) cm.scrollTo(snap.scroll.left, snap.scroll.top);
        cm.focus();
        return true;
      } catch (e) {
        return false;
      }
    }

    function rememberLetterKeep() {
      if (SIDECAR || cfg.kind !== "letter") return;
      var snap = snapshotEditorCaret();
      snap.face = letterFace;
      snap.which = letterWhich;
      snap.edit = !!letterEditMode;
      snap.t = Date.now();
      try {
        sessionStorage.setItem(KEEP_FACE_KEY, JSON.stringify(snap));
      } catch (e) {}
    }

    function restoreKeepCursor() {
      if (!pendingKeep) return;
      if (restoreEditorCaret(pendingKeep)) pendingKeep = null;
      else if (!pendingKeep.cursor) pendingKeep = null;
    }

    function refreshDeskStay() {
      if (SIDECAR) return Promise.resolve(refreshDesk());
      return refreshLivePage().catch(function () {
        rememberLetterKeep();
        window.location.reload();
      });
    }

    function isChipGuest() {
      return !!(blot && blot.chip_guest);
    }

    function clayPages() {
      var pages;
      if (blot.page && blot.page.pages && blot.page.pages.length) pages = blot.page.pages.slice();
      else pages = blot.page ? [blot.page] : [];
      if (isChipGuest()) {
        pages = pages.filter(function (p) {
          return p && p.kind !== "note";
        });
      }
      return pages;
    }

    function currentClay() {
      var pages = clayPages();
      if (!pages.length) return blot.page || null;
      var i;
      if (letterWhich) {
        for (i = 0; i < pages.length; i++) {
          if (pages[i].kind === letterWhich) return pages[i];
        }
      }
      return pages[0];
    }

    function hereIsShell() {
      return String((blot && blot.here) || "") === "shell";
    }

    function canOntoShell() {
      return !!(blot && (blot.shell || hereIsShell()));
    }

    function shellName() {
      return String((blot && blot.shell_name) || "").trim();
    }

    function ontoLabel() {
      if ((catalogOnto === "shell" && canOntoShell()) || hereIsShell()) {
        var name = shellName();
        return name ? "the " + name + " shell" : "the shell";
      }
      return "this page";
    }

    function ontoCrate() {
      if ((catalogOnto === "shell" && canOntoShell()) || hereIsShell()) {
        if (blot.shell) return blot.shell.crate || "";
        return blot.crate || "";
      }
      return blot.crate || "";
    }

    function readmePaneBars() {
      var which = letterWhich || (currentClay() && currentClay().kind) || "";
      var suffix = which ? " · " + which : "";
      var roomBar = document.querySelector("#readmeRoom .readme-pane-bar");
      if (roomBar) roomBar.textContent = "room letter";
      var page = document.getElementById("readmePage");
      if (page) {
        var bars = page.querySelectorAll(".readme-pane-bar");
        for (var i = 0; i < bars.length; i++) {
          var t = (bars[i].textContent || "").toLowerCase();
          if (t.indexOf("header") === 0 || bars[i].parentElement.classList.contains("is-yaml")) {
            bars[i].textContent = "headers" + suffix;
          } else if (t.indexOf("markdown") === 0 || bars[i].parentElement.classList.contains("is-md")) {
            bars[i].textContent = "markdown" + suffix;
          }
        }
      }
    }

    function tearDownCoatCm() {
      var el = $(ids.coat);
      if (!el || !el._cm) return;
      try {
        el._cm.save();
        var w = el._cm.getWrapperElement();
        if (w && w.parentNode) w.parentNode.removeChild(w);
        el._cm.toTextArea();
      } catch (e) {
        try {
          el._cm.toTextArea();
        } catch (e2) {}
      }
      el._cm = null;
      el.style.display = "";
      if (el._cmFitObs) {
        try {
          el._cmFitObs.disconnect();
        } catch (e3) {}
        el._cmFitObs = null;
      }
      // drop from readmeCms
      if (typeof readmeCms !== "undefined" && readmeCms && readmeCms.length) {
        readmeCms = readmeCms.filter(function (cm) {
          return cm && cm.getTextArea && cm.getTextArea() !== el;
        });
      }
    }
    


    function clamp01(n) {
      n = Number(n);
      if (isNaN(n)) return 1;
      if (n < 0) return 0;
      if (n > 1) return 1;
      return n;
    }

    function hexToPickerValue(hex) {
      var h = String(hex || "").replace(/^#/, "");
      if (h.length === 3 || h.length === 4) {
        h =
          h.charAt(0) +
          h.charAt(0) +
          h.charAt(1) +
          h.charAt(1) +
          h.charAt(2) +
          h.charAt(2);
      }
      if (h.length === 8) h = h.slice(0, 6);
      if (h.length !== 6 || /[^0-9a-fA-F]/.test(h)) return "";
      return "#" + h.toLowerCase();
    }

    function hexAlphaPair(hex) {
      var h = String(hex || "").replace(/^#/, "");
      if (h.length === 4) {
        var a = h.charAt(3);
        return clamp01(parseInt(a + a, 16) / 255);
      }
      if (h.length === 8) return clamp01(parseInt(h.slice(6, 8), 16) / 255);
      return 1;
    }

    function parseRgbChannels(val) {
      var s = String(val || "").trim();
      var m = s.match(
        /^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*([0-9.]+))?\s*\)$/i
      );
      if (!m) return null;
      return {
        r: Math.max(0, Math.min(255, Math.round(Number(m[1])))),
        g: Math.max(0, Math.min(255, Math.round(Number(m[2])))),
        b: Math.max(0, Math.min(255, Math.round(Number(m[3])))),
        a: m[4] != null && m[4] !== "" ? clamp01(Number(m[4])) : 1,
      };
    }

    function rgbToHex(r, g, b) {
      function byte(n) {
        var s = Math.max(0, Math.min(255, n | 0)).toString(16);
        return s.length === 1 ? "0" + s : s;
      }
      return "#" + byte(r) + byte(g) + byte(b);
    }

    function hexToRgb(hex) {
      var h = hexToPickerValue(hex).replace(/^#/, "");
      if (!h) return { r: 0, g: 0, b: 0 };
      return {
        r: parseInt(h.slice(0, 2), 16),
        g: parseInt(h.slice(2, 4), 16),
        b: parseInt(h.slice(4, 6), 16),
      };
    }

    function alphaToHexByte(a) {
      var n = Math.round(clamp01(a) * 255);
      var s = n.toString(16);
      return s.length === 1 ? "0" + s : s;
    }

    function parseRootColorValue(val) {
      var s = String(val || "").trim();
      var rgb = parseRgbChannels(s);
      if (rgb) {
        return {
          kind: s.toLowerCase().indexOf("rgba") === 0 ? "rgba" : "rgb",
          hex: rgbToHex(rgb.r, rgb.g, rgb.b),
          alpha: rgb.a,
          display: s,
        };
      }
      var m = s.match(/#([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/);
      if (!m) return null;
      var raw = m[0];
      var kind = "hex";
      if (raw.length === 5 || raw.length === 9) kind = "hex8";
      return {
        kind: kind,
        hex: hexToPickerValue(raw),
        alpha: hexAlphaPair(raw),
        display: raw.toLowerCase(),
      };
    }

    function formatRootColor(kind, hex, alpha) {
      alpha = clamp01(alpha);
      var rgb = hexToRgb(hex);
      if (kind === "rgba" || (kind === "rgb" && alpha < 1)) {
        var a =
          Math.round(alpha * 1000) / 1000;
        if (a === 1 && kind === "rgb") {
          return "rgb(" + rgb.r + ", " + rgb.g + ", " + rgb.b + ")";
        }
        return "rgba(" + rgb.r + ", " + rgb.g + ", " + rgb.b + ", " + a + ")";
      }
      if (kind === "rgb") {
        return "rgb(" + rgb.r + ", " + rgb.g + ", " + rgb.b + ")";
      }
      if (kind === "hex8" || (kind === "hex" && alpha < 1)) {
        return hexToPickerValue(hex) + alphaToHexByte(alpha);
      }
      return hexToPickerValue(hex);
    }

    function coatCssText() {
      var el = $(ids.coat);
      if (!el) return "";
      if (el._cm) {
        try {
          return el._cm.getValue();
        } catch (e) {}
      }
      return el.value || "";
    }

    function setCoatCssText(text) {
      var el = $(ids.coat);
      if (!el) return;
      el.value = text;
      if (el._cm) {
        try {
          var cur = el._cm.getCursor();
          el._cm.setValue(text);
          el._cm.setCursor(cur);
          el._cm.save();
        } catch (e) {
          try {
            el._cm.setValue(text);
            el._cm.save();
          } catch (e2) {}
        }
      }
    }

    function parseRootColorVars(cssText) {
      var text = String(cssText || "");
      var rootRe = /:root\s*\{/i;
      var m = rootRe.exec(text);
      if (!m) return [];
      var i = m.index + m[0].length;
      var depth = 1;
      var start = i;
      while (i < text.length && depth > 0) {
        var ch = text.charAt(i);
        if (ch === "{") depth++;
        else if (ch === "}") depth--;
        i++;
      }
      if (depth !== 0) return [];
      var body = text.slice(start, i - 1);
      var out = [];
      var seen = {};
      var re = /(--[A-Za-z0-9-_]+)\s*:\s*([^;]+);/g;
      var hit;
      while ((hit = re.exec(body))) {
        var name = hit[1];
        var val = String(hit[2] || "").trim();
        var parsed = parseRootColorValue(val);
        if (!parsed || !parsed.hex) continue;
        if (seen[name]) continue;
        seen[name] = true;
        out.push({
          name: name,
          value: val,
          kind: parsed.kind,
          hex: parsed.hex,
          alpha: parsed.alpha,
          display: parsed.display,
        });
      }
      return out;
    }


    /* Autocomplete from mats/styles/fonts.css — narrow strip, not a searchable picker. */
    var COAT_FONT_SUGGESTIONS = ["var(--font-arcade)", "var(--font-glass)", "var(--font-px437)", "var(--font-px437-exec)", "var(--font-mono)", "var(--font-sans)", "var(--font-sans-cond)", "var(--font-serif)", "var(--font-body)", "var(--font-display)", "var(--font-hand)", "var(--font-script)", "var(--font-elite)", "var(--font-glitch)", "var(--font-ops)", "var(--font-garamond)", "var(--font-cormorant)", "var(--font-playfair)", "var(--font-baskerville)", "var(--font-franklin)", "var(--font-source-serif)", "var(--font-news)", "var(--font-fraunces)", "var(--font-cinzel)", "var(--font-patrick)", "var(--font-oswald)", "var(--font-anton)", "var(--font-barlow)", "var(--font-roboto-cond)", "var(--font-courier-prime)", "var(--font-redacted)", "var(--font-infant)", "var(--font-kalam)", "var(--font-indie)", "var(--font-shadows)", "var(--font-gloria)", "var(--font-apple)", "var(--font-rocksalt)", "var(--font-grace)", "var(--font-reenie)", "var(--font-nothing)", "var(--font-dancing)", "var(--font-vibes)", "var(--font-pacifico)", "var(--font-note)", "var(--font-diary)", "var(--font-marker)", "var(--font-press-start)", "var(--font-silkscreen)", "var(--font-pixelify)", "var(--font-orbitron)", "var(--font-chakra)", "var(--font-dos)", "var(--font-terminal)", "var(--font-fraktur)", "var(--font-fraktur-cook)", "var(--font-medieval)", "var(--font-blackletter)", "var(--font-zilla)", "var(--font-roboto-slab)", "var(--font-bitter)", "var(--font-caslon)", "var(--font-notebook)", "var(--font-slab)", "var(--font-creepster)", "var(--font-eater)", "var(--font-nosifer)", "var(--font-butcher)", "var(--font-faster)", "var(--font-monoton)", "var(--font-bungee-shade)", "var(--font-bungee)", "var(--font-righteous)", "var(--font-audiowide)", "var(--font-wallpoet)", "var(--font-fredericka)", "var(--font-lacquer)", "var(--font-warnes)", "var(--font-chaos)", "var(--font-distress)"];

    function ensureCoatFontDatalist() {
      var id = "coat-font-suggestions";
      var dl = document.getElementById(id);
      if (!dl) {
        dl = document.createElement("datalist");
        dl.id = id;
        document.body.appendChild(dl);
      }
      if (dl.getAttribute("data-filled") === "1") return id;
      dl.innerHTML = "";
      for (var i = 0; i < COAT_FONT_SUGGESTIONS.length; i++) {
        var opt = document.createElement("option");
        opt.value = COAT_FONT_SUGGESTIONS[i];
        dl.appendChild(opt);
      }
      dl.setAttribute("data-filled", "1");
      return id;
    }

    function classifyRootVar(name, val) {
      var n = String(name || "").toLowerCase();
      var v = String(val || "").trim();
      var parsed = parseRootColorValue(v);
      if (parsed && parsed.hex) return "color";
      if (
        /font|typeface|family/.test(n) ||
        /^var\(\s*--font/i.test(v) ||
        (/["'][^"']+["']\s*,/.test(v) || (/,/.test(v) && /serif|sans|mono|cursive|system-ui/i.test(v)))
      ) {
        return "font";
      }
      if (
        /size|pad|gap|width|indent|radius|tracking|leading|height|weight|max|side-w|line-height/.test(n) ||
        /^-?[\d.]+(px|em|rem|%|vh|vw)?$/i.test(v) ||
        /^\d+(\.\d+)?$/.test(v)
      ) {
        return "measure";
      }
      return "text";
    }

    function parseRootAllVars(cssText) {
      var text = String(cssText || "");
      var rootRe = /:root\s*\{/i;
      var m = rootRe.exec(text);
      if (!m) return [];
      var i = m.index + m[0].length;
      var depth = 1;
      var start = i;
      while (i < text.length && depth > 0) {
        var ch = text.charAt(i);
        if (ch === "{") depth++;
        else if (ch === "}") depth--;
        i++;
      }
      if (depth !== 0) return [];
      var body = text.slice(start, i - 1);
      var out = [];
      var seen = {};
      var re = /(--[A-Za-z0-9-_]+)\s*:\s*([^;]+);/g;
      var hit;
      while ((hit = re.exec(body))) {
        var name = hit[1];
        var val = String(hit[2] || "").trim();
        if (seen[name]) continue;
        seen[name] = true;
        var kind = classifyRootVar(name, val);
        var entry = { name: name, value: val, kind: kind };
        if (kind === "color") {
          var parsed = parseRootColorValue(val);
          if (parsed && parsed.hex) {
            entry.colorKind = parsed.kind;
            entry.hex = parsed.hex;
            entry.alpha = parsed.alpha;
            entry.display = parsed.display;
          } else {
            entry.kind = "text";
          }
        }
        out.push(entry);
      }
      return out;
    }

    function applyCoatVarText(row) {
      if (!row) return;
      var varName = row.getAttribute("data-coat-var");
      if (!varName) return;
      var input = row.querySelector("[data-coat-text]");
      if (!input) return;
      var next = String(input.value || "").trim();
      if (!next) return;
      setCoatCssText(rewriteRootVar(coatCssText(), varName, next));
    }


    function rewriteRootVar(cssText, varName, newValue) {
      var text = String(cssText || "");
      var rootRe = /:root\s*\{/i;
      var m = rootRe.exec(text);
      if (!m) {
        return ":root {\n  " + varName + ": " + newValue + ";\n}\n\n" + text;
      }
      var openEnd = m.index + m[0].length;
      var i = openEnd;
      var depth = 1;
      while (i < text.length && depth > 0) {
        var ch = text.charAt(i);
        if (ch === "{") depth++;
        else if (ch === "}") depth--;
        i++;
      }
      var closeAt = i - 1;
      var body = text.slice(openEnd, closeAt);
      var re = new RegExp(
        "(" +
          varName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") +
          "\\s*:\\s*)([^;]+)(;)",
        "i"
      );
      if (re.test(body)) {
        body = body.replace(re, "$1" + newValue + "$3");
      } else {
        body = body.replace(/\s*$/, "") + "\n  " + varName + ": " + newValue + ";\n";
      }
      return text.slice(0, openEnd) + body + text.slice(closeAt);
    }

    function applyCoatVarColor(row) {
      if (!row) return;
      var varName = row.getAttribute("data-coat-var");
      var kind = row.getAttribute("data-coat-kind") || "hex";
      if (!varName) return;
      var colorEl = row.querySelector('input[type="color"]');
      var alphaEl = row.querySelector('input[type="range"]');
      if (!colorEl) return;
      var hex = colorEl.value;
      var alpha = alphaEl ? Number(alphaEl.value) / 100 : 1;
      var next = formatRootColor(kind, hex, alpha);
      setCoatCssText(rewriteRootVar(coatCssText(), varName, next));
      var out = row.querySelector(".readme-coat-swatch-hex");
      if (out) out.textContent = next;
      if (alphaEl) {
        var lab = row.querySelector(".readme-coat-swatch-alpha");
        if (lab) lab.textContent = Math.round(alpha * 100) + "%";
      }
    }

    var coatPaletteTimer = 0;
    function scheduleCoatPalette() {
      if (coatPaletteTimer) window.clearTimeout(coatPaletteTimer);
      coatPaletteTimer = window.setTimeout(function () {
        coatPaletteTimer = 0;
        renderCoatPalette();
      }, 280);
    }

    function renderCoatPalette() {
      var host = $("readmeCoatPalette");
      if (!host) return;
      if (letterFace !== "coat") {
        host.hidden = true;
        return;
      }
      var all = parseRootAllVars(coatCssText());
      var colors = [];
      var fonts = [];
      var measures = [];
      var texts = [];
      for (var i = 0; i < all.length; i++) {
        var v = all[i];
        if (v.kind === "color") colors.push(v);
        else if (v.kind === "font") fonts.push(v);
        else if (v.kind === "measure") measures.push(v);
        else texts.push(v);
      }
      if (!all.length) {
        host.hidden = false;
        host.innerHTML =
          '<div class="readme-coat-palette-empty">No <code>:root</code> variables yet. Colors use <code>#hex</code> / <code>rgba()</code>; type uses <code>--font: var(--font-sans);</code> etc.</div>' +
          '<button type="button" class="readme-coat-palette-add" data-coat-add-root>+ seed :root palette</button>';
        return;
      }
      host.hidden = false;
      var html = "";
      function rowColor(v) {
        var aPct = Math.round(clamp01(v.alpha) * 100);
        return (
          '<div class="readme-coat-swatch" data-coat-var="' +
          escapeHtml(v.name) +
          '" data-coat-kind="' +
          escapeHtml(v.colorKind || "hex") +
          '" data-coat-role="color" title="' +
          escapeHtml(v.name + ": " + v.value) +
          '">' +
          '<input type="color" value="' +
          escapeHtml(v.hex) +
          '">' +
          '<span class="readme-coat-swatch-name">' +
          escapeHtml(v.name) +
          "</span>" +
          '<input type="range" min="0" max="100" step="1" value="' +
          aPct +
          '" aria-label="opacity">' +
          '<span class="readme-coat-swatch-alpha">' +
          aPct +
          "%</span>" +
          '<span class="readme-coat-swatch-hex">' +
          escapeHtml(v.display || v.value) +
          "</span>" +
          "</div>"
        );
      }
      function rowFont(v) {
        var listId = ensureCoatFontDatalist();
        return (
          '<div class="readme-coat-swatch readme-coat-type" data-coat-var="' +
          escapeHtml(v.name) +
          '" data-coat-role="font" title="' +
          escapeHtml(v.name + ": " + v.value) +
          '">' +
          '<span class="readme-coat-swatch-name">' +
          escapeHtml(v.name) +
          "</span>" +
          '<input type="text" class="readme-coat-type-input" data-coat-text list="' +
          listId +
          '" value="' +
          escapeHtml(v.value) +
          '" spellcheck="false" placeholder="var(--font-sans) — from fonts.css" autocomplete="off">' +
          "</div>"
        );
      }
      function rowText(v, role) {
        return (
          '<div class="readme-coat-swatch readme-coat-type" data-coat-var="' +
          escapeHtml(v.name) +
          '" data-coat-role="' +
          escapeHtml(role || "text") +
          '" title="' +
          escapeHtml(v.name + ": " + v.value) +
          '">' +
          '<span class="readme-coat-swatch-name">' +
          escapeHtml(v.name) +
          "</span>" +
          '<input type="text" class="readme-coat-type-input" data-coat-text value="' +
          escapeHtml(v.value) +
          '" spellcheck="false">' +
          "</div>"
        );
      }
      if (colors.length) {
        html +=
          '<div class="readme-coat-palette-label">root colors</div><div class="readme-coat-palette-rows">';
        for (var c = 0; c < colors.length; c++) html += rowColor(colors[c]);
        html += "</div>";
      }
      if (fonts.length) {
        html +=
          '<div class="readme-coat-palette-label">type / fonts</div><div class="readme-coat-palette-rows">';
        for (var f = 0; f < fonts.length; f++) html += rowFont(fonts[f]);
        html += "</div>";
      }
      if (measures.length) {
        html +=
          '<div class="readme-coat-palette-label">size / space</div><div class="readme-coat-palette-rows">';
        for (var m = 0; m < measures.length; m++) html += rowText(measures[m], "measure");
        html += "</div>";
      }
      if (texts.length) {
        html +=
          '<div class="readme-coat-palette-label">other vars</div><div class="readme-coat-palette-rows">';
        for (var t = 0; t < texts.length; t++) html += rowText(texts[t], "text");
        html += "</div>";
      }
      html +=
        '<div class="readme-coat-palette-actions">' +
        '<button type="button" class="readme-coat-palette-add" data-coat-add-var>+ color</button>' +
        '<button type="button" class="readme-coat-palette-add" data-coat-add-type>+ type var</button>' +
        "</div>";
      host.innerHTML = html;
    }


    function seedRootPalette() {
      var text = coatCssText();
      if (/:root\s*\{/i.test(text)) {
        setStatus(":root already present — add --name: #hex; or rgba() inside it");
        renderCoatPalette();
        return;
      }
      var seed =
        ":root {\n" +
        "  --bg: #0b1020;\n" +
        "  --ink: #e8ecf4;\n" +
        "  --accent: #55ffff;\n" +
        "  --accent-2: #ffff55;\n" +
        "  --lamp: rgba(255, 220, 150, 0.35);\n" +
        "  --font: var(--font-sans, system-ui, sans-serif);\n" +
        "  --font-head: var(--font-display, system-ui, sans-serif);\n" +
        "  --font-mono: var(--font-mono, ui-monospace, monospace);\n" +
        "  --font-size: 15px;\n" +
        "  --line-height: 1.45;\n" +
        "}\n\n";
      setCoatCssText(seed + text);
      renderCoatPalette();
      setStatus("seeded :root palette — Keep to save");
    }

    function addRootColorVar() {
      var name = window.prompt("variable name (without --)", "accent");
      if (name == null) return;
      name = String(name).trim().replace(/^--+/, "");
      if (!name) return;
      name = "--" + name.replace(/[^A-Za-z0-9-_]/g, "-");
      var text = rewriteRootVar(coatCssText(), name, "#808080");
      setCoatCssText(text);
      renderCoatPalette();
      setStatus("added " + name + " — Keep to save");
    }

    
    function coatSplitCollapsed() {
      try {
        return window.localStorage.getItem("pocketgo.coat.palette") === "off";
      } catch (e) {
        return false;
      }
    }

    function applyCoatSplitState() {
      var split = $("readmeCoatSplit");
      var btn = $("readmeCoatSplitToggle");
      var off = coatSplitCollapsed();
      if (split) {
        if (off) split.classList.add("is-palette-off");
        else split.classList.remove("is-palette-off");
      }
      if (btn) {
        btn.textContent = off ? "colors" : "colors ✓";
        btn.setAttribute("aria-pressed", off ? "false" : "true");
      }
      var el = $(ids.coat);
      if (el && el._cm) {
        try {
          el._cm.refresh();
        } catch (e) {}
      }
    }

    function bindCoatSplitToggle() {
      var btn = $("readmeCoatSplitToggle");
      if (!btn || btn._bound) return;
      btn._bound = true;
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var off = !coatSplitCollapsed();
        try {
          window.localStorage.setItem("pocketgo.coat.palette", off ? "off" : "on");
        } catch (err) {}
        applyCoatSplitState();
      });
      applyCoatSplitState();
    }


    function addRootTypeVar() {
      var name = window.prompt("type variable name (without --)", "font");
      if (name == null) return;
      name = String(name).trim().replace(/^--+/, "");
      if (!name) return;
      name = "--" + name.replace(/[^A-Za-z0-9-_]/g, "-");
      var def =
        /font/i.test(name) && !/size|weight|height|tracking/i.test(name)
          ? "var(--font-sans, system-ui, sans-serif)"
          : /size|pad|gap|width|indent|radius/i.test(name)
            ? "1em"
            : "inherit";
      var text = rewriteRootVar(coatCssText(), name, def);
      setCoatCssText(text);
      renderCoatPalette();
      setStatus("added " + name + " — Keep to save");
    }

    function bindCoatPalette() {
      var host = $("readmeCoatPalette");
      if (!host || host._coatPaletteBound) return;
      host._coatPaletteBound = true;
      host.addEventListener("input", function (e) {
        var t = e.target;
        if (!t) return;
        var row = t.closest ? t.closest(".readme-coat-swatch") : null;
        if (!row) return;
        if (t.getAttribute("type") === "color" || t.getAttribute("type") === "range") {
          applyCoatVarColor(row);
          return;
        }
        if (t.getAttribute("data-coat-text") != null) {
          applyCoatVarText(row);
        }
      });
      host.addEventListener("change", function (e) {
        var t = e.target;
        if (!t) return;
        var row = t.closest ? t.closest(".readme-coat-swatch") : null;
        if (!row) return;
        if (t.getAttribute("data-coat-text") != null) {
          applyCoatVarText(row);
        }
      });
      host.addEventListener("click", function (e) {
        var addRoot = e.target && e.target.closest ? e.target.closest("[data-coat-add-root]") : null;
        if (addRoot) {
          e.preventDefault();
          seedRootPalette();
          return;
        }
        var addType = e.target && e.target.closest ? e.target.closest("[data-coat-add-type]") : null;
        if (addType) {
          e.preventDefault();
          addRootTypeVar();
          return;
        }
        var addVar = e.target && e.target.closest ? e.target.closest("[data-coat-add-var]") : null;
        if (addVar) {
          e.preventDefault();
          addRootColorVar();
        }
      });
    }

function ensureCoatCm() {
      var el = $(ids.coat);
      if (!el) return;
      if (el._cm) {
        try {
          var w = el._cm.getWrapperElement();
          if (w) w.style.display = "";
          el._cm.refresh();
          bindCoatSplitToggle(); bindCoatPalette(); renderCoatPalette(); applyCoatSplitState();
        } catch (e) {}
        return;
      }
      if (!window.CodeMirror) return;
      try {
        var cm = window.CodeMirror.fromTextArea(el, {
          mode: "css",
          theme: "material-darker",
          lineNumbers: true,
          gutters: ["CodeMirror-linenumbers"],
          fixedGutter: true,
          lineWrapping: true,
          tabSize: 2,
          indentWithTabs: false,
          viewportMargin: Infinity,
          extraKeys: {
            "Ctrl-S": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Cmd-S": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Ctrl-K": function (cm) {
              if (cm && cm.getOption) { /* claim over any kill-line default */ }
              cmSaveAll();
              storeThought();
              return false;
            },
            "Cmd-K": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Ctrl-Enter": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Cmd-Enter": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Ctrl-E": function () {
              letterFace = "room";
              letterEditMode = true;
              render();
              syncRoomLetterView();
            },
            "Cmd-E": function () {
              letterFace = "room";
              letterEditMode = true;
              render();
              syncRoomLetterView();
            },
            Tab: function (c) {
              c.replaceSelection("  ", "end");
            },
          },
        });
        el._cm = cm;
        cm.setValue(el.value || "");
        cm.on("changes", function () {
          cm.save();
          scheduleCoatPalette();
        });
        bindCoatSplitToggle(); bindCoatPalette(); renderCoatPalette(); applyCoatSplitState();
        if (typeof cmObservePane === "function") cmObservePane(el);
        if (typeof readmeCms !== "undefined" && readmeCms) readmeCms.push(cm);
        window.requestAnimationFrame(function () {
          if (typeof cmFitEl === "function") cmFitEl(el);
        });
      } catch (e) {}
    }


    
    
    function syncHelpFab() {
      var fab = $("readmeHelpFab");
      if (!fab) return;
      var on = letterFace === "help";
      fab.classList.toggle("is-on", on);
      fab.setAttribute("aria-pressed", on ? "true" : "false");
      fab.title = on
        ? "back to editor (draft kept in memory until Keep)"
        : "field manual — tokens, type, notes";
    }

    function syncRenameBtn() {
      // Only paper pages are renameable — not room letter, shell, css, or guest chips.
      var btn = document.querySelector("[data-rename-note]");
      if (!btn) return;
      if (isChipGuest()) {
        btn.setAttribute("hidden", "");
        return;
      }
      var clay = letterFace === "page" ? currentClay() : null;
      var kind = clay && clay.kind ? clay.kind : letterWhich;
      var show = letterFace === "page" && kind && kind !== "shell";
      if (show) btn.removeAttribute("hidden");
      else btn.setAttribute("hidden", "");
    }

    function loadHelp(slug) {
      helpSlug = slug || helpSlug || "_index";
      api("GET", "/api/help?page=" + encodeURIComponent(helpSlug))
        .then(function (data) {
          helpBlot = data || helpBlot;
          if (helpBlot.slug) helpSlug = helpBlot.slug;
          helpEditMode = false;
          fillHelp();
          syncHelpLetterView();
          renderHelpPages();
          syncHelpFab();
        })
        .catch(function (err) {
          setStatus(err.message || "help load failed", true);
        });
    }

    function fillHelp() {
      var el = $("readmeHelpLeaf");
      var body = (helpBlot && helpBlot.body) || "";
      if (el) {
        el.value = body;
        if (el._cm) {
          try {
            if (el._cm.getValue() !== body) el._cm.setValue(body);
          } catch (e) {}
        }
      }
      var bar = $("readmeHelpBar");
      var label = (helpBlot && helpBlot.title) || helpSlug || "help";
      var lab = bar && bar.querySelector(".readme-letter-label");
      if (lab) lab.textContent = label;
    }

    function renderHelpPages() {
      var host = $("readmeHelpPages");
      if (!host) return;
      var pages = (helpBlot && helpBlot.pages) || [];
      var html = "";
      for (var i = 0; i < pages.length; i++) {
        var p = pages[i];
        html +=
          '<button type="button" class="readme-help-page' +
          (p.slug === helpSlug ? " is-on" : "") +
          '" data-help-page="' +
          escapeHtml(p.slug) +
          '">' +
          escapeHtml(p.title || p.slug) +
          "</button>";
      }
      host.innerHTML = html;
    }

    function syncHelpLetterView() {
      var view = $("readmeHelpView");
      var editBtn = document.querySelector("[data-help-edit]");
      var cancelBtn = document.querySelector("[data-help-cancel]");
      var leaf = $("readmeHelpLeaf");
      var pane = view && view.closest ? view.closest(".readme-pane") : null;
      if (!view || !leaf) return;
      if (letterFace !== "help") {
        view.hidden = true;
        if (editBtn) editBtn.setAttribute("hidden", "");
        if (cancelBtn) cancelBtn.setAttribute("hidden", "");
        if (pane) pane.classList.remove("is-printout", "is-editing");
        if (leaf._cm) {
          try {
            var w = leaf._cm.getWrapperElement();
            if (w) w.style.display = "none";
          } catch (e) {}
        }
        leaf.setAttribute("hidden", "");
        return;
      }
      var has = !!(helpBlot.body && String(helpBlot.body).trim());
      var editing = helpEditMode || !has;
      if (pane) {
        pane.classList.toggle("is-printout", !editing);
        pane.classList.toggle("is-editing", editing);
      }
      function showHelpCm(on) {
        if (!leaf._cm) return;
        try {
          var w = leaf._cm.getWrapperElement();
          if (w) w.style.display = on ? "" : "none";
          if (on) leaf._cm.refresh();
        } catch (e) {}
      }
      if (editing) {
        view.hidden = true;
        leaf.removeAttribute("hidden");
        // keep textarea hidden when CM exists (same as room letter)
        if (leaf._cm) {
          leaf.style.display = "none";
          showHelpCm(true);
        } else {
          leaf.style.display = "";
          ensureHelpCm();
        }
        if (editBtn) editBtn.setAttribute("hidden", "");
        if (cancelBtn) {
          if (has) cancelBtn.removeAttribute("hidden");
          else cancelBtn.setAttribute("hidden", "");
        }
      } else {
        view.hidden = false;
        view.innerHTML =
          (helpBlot.body_html && String(helpBlot.body_html).trim()) ||
          '<p class="readme-letter-empty">(empty help — hit Edit)</p>';
        leaf.setAttribute("hidden", "");
        leaf.style.display = "none";
        showHelpCm(false);
        if (editBtn) editBtn.removeAttribute("hidden");
        if (cancelBtn) cancelBtn.setAttribute("hidden", "");
      }
    }

    /* ---- BIOS source-pane pipe tables (Obsidian-style grid over CodeMirror) ---- */
    function biosEscapeHtml(s) {
      return String(s || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    }
    function biosEscapeAttr(s) {
      return biosEscapeHtml(s).replace(/"/g, "&quot;");
    }
    function biosSplitPipeRow(line) {
      var raw = String(line || "").trim();
      if (raw.charAt(0) === "|") raw = raw.slice(1);
      if (raw.charAt(raw.length - 1) === "|") raw = raw.slice(0, -1);
      var parts = [];
      var buf = "";
      var esc = false;
      for (var i = 0; i < raw.length; i++) {
        var ch = raw.charAt(i);
        if (esc) {
          buf += ch;
          esc = false;
          continue;
        }
        if (ch === "\\") {
          esc = true;
          continue;
        }
        if (ch === "|") {
          parts.push(buf.trim());
          buf = "";
          continue;
        }
        buf += ch;
      }
      parts.push(buf.trim());
      return parts;
    }
    function biosIsSepRow(line) {
      var cells = biosSplitPipeRow(line);
      if (!cells.length) return false;
      for (var i = 0; i < cells.length; i++) {
        if (!/^:?-+:?$/.test(cells[i].replace(/\s+/g, ""))) return false;
      }
      return true;
    }
    function biosAlignFromSep(cell) {
      var s = String(cell || "").replace(/\s+/g, "");
      var left = s.charAt(0) === ":";
      var right = s.charAt(s.length - 1) === ":";
      if (left && right) return "center";
      if (right) return "right";
      return "left";
    }
    function biosParsePipeTables(text) {
      var lines = String(text || "").split("\n");
      var out = [];
      var i = 0;
      while (i < lines.length - 1) {
        if (!/^\s*\|/.test(lines[i]) || !biosIsSepRow(lines[i + 1])) {
          i++;
          continue;
        }
        var from = i;
        var head = biosSplitPipeRow(lines[i]);
        var sep = biosSplitPipeRow(lines[i + 1]);
        var aligns = [];
        var width = Math.max(head.length, sep.length);
        for (var c = 0; c < width; c++) {
          aligns.push(biosAlignFromSep(sep[c] || "---"));
        }
        while (head.length < width) head.push("");
        var rows = [head.slice(0, width)];
        i += 2;
        while (i < lines.length && /^\s*\|/.test(lines[i]) && !biosIsSepRow(lines[i])) {
          var row = biosSplitPipeRow(lines[i]);
          while (row.length < width) row.push("");
          rows.push(row.slice(0, width));
          i++;
        }
        out.push({ from: from, to: i - 1, rows: rows, aligns: aligns });
      }
      return out;
    }
    function biosSerializePipeTable(rows, aligns) {
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
    function biosTableCollect(wrap) {
      var table = wrap.querySelector("table.bios-md-table");
      var aligns = [];
      var rows = [];
      var headCells = table.querySelectorAll("thead th");
      if (headCells.length) {
        var head = [];
        for (var i = 0; i < headCells.length; i++) {
          var t = (headCells[i].textContent || "").replace(/\n/g, " ");
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
          row.push((tds[c].textContent || "").replace(/\n/g, " "));
        }
        rows.push(row);
      }
      return { rows: rows, aligns: aligns };
    }
    function biosTableFill(wrap, rows, aligns) {
      var table = wrap.querySelector("table.bios-md-table");
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
            '" contenteditable="true">' +
            biosEscapeHtml(head[h]) +
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
              '" contenteditable="true">' +
              biosEscapeHtml(row[c]) +
              "</td>";
          }
          html += "</tr>";
        }
        html += "</tbody>";
      }
      table.innerHTML = html;
    }
    function biosTableEnsureChrome(wrap) {
      if (wrap.querySelector(".bios-md-table-chrome")) return;
      var chrome = document.createElement("div");
      chrome.className = "bios-md-table-chrome";
      chrome.innerHTML =
        '<button type="button" class="bios-md-table-btn" data-bios-table-add-row title="Add row">+ row</button>' +
        '<button type="button" class="bios-md-table-btn" data-bios-table-add-col title="Add column">+ col</button>' +
        '<button type="button" class="bios-md-table-btn" data-bios-table-del-row title="Delete last row">− row</button>' +
        '<button type="button" class="bios-md-table-btn" data-bios-table-del-col title="Delete last column">− col</button>' +
        '<button type="button" class="bios-md-table-btn" data-bios-table-raw title="Show raw Markdown">raw</button>' +
        '<button type="button" class="bios-md-table-btn" data-bios-table-done title="Done">done</button>';
      wrap.appendChild(chrome);
    }
    function biosTableSyncToCm(wrap) {
      var cm = wrap._cm;
      var mark = wrap._mark;
      if (!cm || !mark) return;
      var found = mark.find();
      if (!found) return;
      var grid = biosTableCollect(wrap);
      var md = biosSerializePipeTable(grid.rows, grid.aligns);
      cm._biosTableLock = true;
      try {
        cm.replaceRange(md, found.from, found.to);
        mark.clear();
        var newLines = md.split("\n");
        var fromLine = found.from.line;
        var toLine = fromLine + newLines.length - 1;
        var endCh = (cm.getLine(toLine) || "").length;
        var fresh = cm.markText(
          { line: fromLine, ch: 0 },
          { line: toLine, ch: endCh },
          {
            replacedWith: wrap,
            clearOnEnter: false,
            handleMouseEvents: true,
            atomic: false,
          }
        );
        wrap._mark = fresh;
        if (!cm._biosTableMarks) cm._biosTableMarks = [];
        cm._biosTableMarks = cm._biosTableMarks.filter(function (m) {
          return m !== mark;
        });
        cm._biosTableMarks.push(fresh);
        cm.save();
      } catch (e) {}
      cm._biosTableLock = false;
    }
    function biosTableFocusIndex(wrap, index) {
      var cells = wrap.querySelectorAll("th,td");
      if (!cells.length) return;
      if (index < 0) index = 0;
      if (index >= cells.length) index = cells.length - 1;
      cells[index].focus();
    }
    function biosTableCellIndex(wrap, cell) {
      var cells = wrap.querySelectorAll("th,td");
      for (var i = 0; i < cells.length; i++) {
        if (cells[i] === cell) return i;
      }
      return 0;
    }
    function biosTableColCount(wrap) {
      var th = wrap.querySelectorAll("thead th");
      if (th.length) return th.length;
      var tr = wrap.querySelector("tbody tr");
      return tr ? tr.querySelectorAll("td").length : 0;
    }
    function biosBuildTableWidget(cm, tableMeta) {
      var wrap = document.createElement("div");
      wrap.className = "bios-md-table-wrap is-editing";
      wrap._cm = cm;
      wrap.setAttribute("contenteditable", "false");
      var table = document.createElement("table");
      table.className = "bios-md-table";
      wrap.appendChild(table);
      biosTableEnsureChrome(wrap);
      biosTableFill(wrap, tableMeta.rows, tableMeta.aligns);

      /* CodeMirror steals mousedown unless marked ignore — otherwise cells never focus */
      function ignoreCm(e) {
        e.codemirrorIgnore = true;
      }
      wrap.addEventListener("mousedown", ignoreCm, true);
      wrap.addEventListener("mouseup", ignoreCm, true);
      wrap.addEventListener("click", function (e) {
        e.codemirrorIgnore = true;
        var cell = e.target && e.target.closest ? e.target.closest("th, td") : null;
        if (!cell || !wrap.contains(cell)) return;
        e.preventDefault();
        e.stopPropagation();
        if (!cell.hasAttribute("contenteditable")) cell.setAttribute("contenteditable", "true");
        cell.focus();
        try {
          var range = document.createRange();
          range.selectNodeContents(cell);
          range.collapse(false);
          var sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(range);
        } catch (err) {}
      }, true);

      wrap.addEventListener("keydown", function (e) {
        e.codemirrorIgnore = true;
        var cell = e.target && e.target.closest ? e.target.closest("th,td") : null;
        if (!cell || !wrap.contains(cell)) return;
        var cols = biosTableColCount(wrap) || 1;
        var idx = biosTableCellIndex(wrap, cell);
        if (e.key === "Tab") {
          e.preventDefault();
          e.stopPropagation();
          biosTableFocusIndex(wrap, e.shiftKey ? idx - 1 : idx + 1);
          return;
        }
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          e.stopPropagation();
          var grid = biosTableCollect(wrap);
          var blank = [];
          for (var i = 0; i < cols; i++) blank.push("");
          grid.rows.push(blank);
          biosTableFill(wrap, grid.rows, grid.aligns);
          biosTableSyncToCm(wrap);
          biosTableFocusIndex(wrap, grid.rows.length * cols - cols);
          return;
        }
      });
      wrap.addEventListener("input", function (e) {
        if (!e.target || !e.target.closest) return;
        if (!e.target.closest("th,td")) return;
        clearTimeout(wrap._syncTimer);
        wrap._syncTimer = setTimeout(function () {
          biosTableSyncToCm(wrap);
        }, 180);
      });
      wrap.addEventListener("click", function (e) {
        var btn = e.target && e.target.closest ? e.target.closest("[data-bios-table-add-row], [data-bios-table-add-col], [data-bios-table-del-row], [data-bios-table-del-col], [data-bios-table-done], [data-bios-table-raw]") : null;
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();
        var grid = biosTableCollect(wrap);
        var cols = biosTableColCount(wrap) || 1;
        if (btn.hasAttribute("data-bios-table-add-row")) {
          var blank = [];
          for (var i = 0; i < cols; i++) blank.push("");
          grid.rows.push(blank);
          biosTableFill(wrap, grid.rows, grid.aligns);
          biosTableSyncToCm(wrap);
        } else if (btn.hasAttribute("data-bios-table-add-col")) {
          for (var r = 0; r < grid.rows.length; r++) grid.rows[r].push("");
          grid.aligns.push("left");
          biosTableFill(wrap, grid.rows, grid.aligns);
          biosTableSyncToCm(wrap);
        } else if (btn.hasAttribute("data-bios-table-del-row")) {
          if (grid.rows.length > 2) {
            grid.rows.pop();
            biosTableFill(wrap, grid.rows, grid.aligns);
            biosTableSyncToCm(wrap);
          }
        } else if (btn.hasAttribute("data-bios-table-del-col")) {
          if (cols > 1) {
            for (var r2 = 0; r2 < grid.rows.length; r2++) grid.rows[r2].pop();
            grid.aligns.pop();
            biosTableFill(wrap, grid.rows, grid.aligns);
            biosTableSyncToCm(wrap);
          }
        } else if (btn.hasAttribute("data-bios-table-raw") || btn.hasAttribute("data-bios-table-done")) {
          biosTableSyncToCm(wrap);
          cm._biosTableSkipUntil = Date.now() + (btn.hasAttribute("data-bios-table-raw") ? 8000 : 400);
          try {
            if (wrap._mark) wrap._mark.clear();
          } catch (err) {}
          cm._biosTableMarks = (cm._biosTableMarks || []).filter(function (m) {
            return m !== wrap._mark;
          });
          if (btn.hasAttribute("data-bios-table-raw")) {
            /* leave raw pipe source visible briefly */
          } else {
            setTimeout(function () {
              biosTableRefreshMarks(cm);
            }, 50);
          }
        }
      });
      return wrap;
    }
    function biosTableClearMarks(cm) {
      var marks = cm._biosTableMarks || [];
      for (var i = 0; i < marks.length; i++) {
        try {
          marks[i].clear();
        } catch (e) {}
      }
      cm._biosTableMarks = [];
    }
    function biosTableRefreshMarks(cm) {
      if (!cm || cm._biosTableLock) return;
      if (cm._biosTableSkipUntil && Date.now() < cm._biosTableSkipUntil) return;
      biosTableClearMarks(cm);
      var tables = biosParsePipeTables(cm.getValue());
      for (var t = 0; t < tables.length; t++) {
        var meta = tables[t];
        var wrap = biosBuildTableWidget(cm, meta);
        var endCh = (cm.getLine(meta.to) || "").length;
        var mark = cm.markText(
          { line: meta.from, ch: 0 },
          { line: meta.to, ch: endCh },
          {
            replacedWith: wrap,
            clearOnEnter: false,
            handleMouseEvents: true,
            atomic: false,
          }
        );
        wrap._mark = mark;
        cm._biosTableMarks.push(mark);
      }
    }
    function biosTableBind(cm) {
      if (!cm || cm._biosTablesBound) return;
      cm._biosTablesBound = true;
      cm._biosTableMarks = [];
      var timer = null;
      cm.on("changes", function () {
        if (cm._biosTableLock) return;
        clearTimeout(timer);
        timer = setTimeout(function () {
          biosTableRefreshMarks(cm);
        }, 160);
      });
      window.requestAnimationFrame(function () {
        biosTableRefreshMarks(cm);
      });
    }



    /* ---- BIOS custom dropdown (Epiphany/WebKitGTK cannot theme native select popups) ---- */
    function biosDdCloseAll(except) {
      var opens = document.querySelectorAll(".bios-dd.is-open");
      for (var i = 0; i < opens.length; i++) {
        if (except && opens[i] === except) continue;
        opens[i].classList.remove("is-open");
        var list = opens[i].querySelector(".bios-dd-list");
        if (list) list.hidden = true;
        var btn = opens[i].querySelector(".bios-dd-btn");
        if (btn) btn.setAttribute("aria-expanded", "false");
      }
    }
    function biosDdLabelFor(sel) {
      if (!sel || sel.selectedIndex < 0) return "";
      var opt = sel.options[sel.selectedIndex];
      return opt ? (opt.textContent || opt.value || "") : "";
    }
    function biosDdSync(sel) {
      if (!sel || !sel._biosDd) return;
      var wrap = sel._biosDd;
      var btn = wrap.querySelector(".bios-dd-btn");
      var list = wrap.querySelector(".bios-dd-list");
      if (!btn || !list) return;
      btn.textContent = biosDdLabelFor(sel) || (sel.getAttribute("title") || "choose…");
      btn.title = sel.title || btn.textContent;
      if (sel.classList.contains("is-host-off")) wrap.classList.add("is-host-off");
      else wrap.classList.remove("is-host-off");
      var html = "";
      for (var i = 0; i < sel.options.length; i++) {
        var o = sel.options[i];
        var cls = "bios-dd-opt";
        if (o.disabled) cls += " is-disabled";
        if (o.selected) cls += " is-selected";
        if (o.classList.contains("is-host-off")) cls += " is-host-off";
        html +=
          '<li class="' +
          cls +
          '" role="option" data-idx="' +
          i +
          '" aria-selected="' +
          (o.selected ? "true" : "false") +
          '">' +
          biosEscapeHtml(o.textContent || o.value || "") +
          "</li>";
      }
      list.innerHTML = html;
    }
    function biosDdPick(sel, idx) {
      if (!sel || idx < 0 || idx >= sel.options.length) return;
      var o = sel.options[idx];
      if (o.disabled) return;
      sel.selectedIndex = idx;
      sel.value = o.value;
      biosDdSync(sel);
      biosDdCloseAll();
      try {
        sel.dispatchEvent(new Event("change", { bubbles: true }));
        sel.dispatchEvent(new Event("input", { bubbles: true }));
      } catch (e) {
        var ev = document.createEvent("HTMLEvents");
        ev.initEvent("change", true, false);
        sel.dispatchEvent(ev);
      }
    }
    function biosDdEnhance(sel) {
      if (!sel || sel.tagName !== "SELECT" || sel._biosDd) return;
      var parent = sel.parentNode;
      if (!parent) return;
      var wrap = document.createElement("div");
      wrap.className = "bios-dd";
      if (sel.className) wrap.className += " " + sel.className.replace(/\breadme-hosts-select\b|\breadme-crates-mode\b|\blibrarian-leaf\b|\btagbay-input\b/g, "").replace(/\s+/g, " ").trim();
      wrap.classList.add("bios-dd");
      parent.insertBefore(wrap, sel);
      wrap.appendChild(sel);
      sel.classList.add("bios-dd-native");
      sel.setAttribute("tabindex", "-1");
      sel.setAttribute("aria-hidden", "true");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "bios-dd-btn";
      btn.setAttribute("aria-haspopup", "listbox");
      btn.setAttribute("aria-expanded", "false");
      var list = document.createElement("ul");
      list.className = "bios-dd-list";
      list.setAttribute("role", "listbox");
      list.hidden = true;
      wrap.appendChild(btn);
      wrap.appendChild(list);
      sel._biosDd = wrap;
      wrap._biosSel = sel;
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var open = !wrap.classList.contains("is-open");
        biosDdCloseAll(open ? wrap : null);
        if (open) {
          biosDdSync(sel);
          wrap.classList.add("is-open");
          list.hidden = false;
          btn.setAttribute("aria-expanded", "true");
        } else {
          wrap.classList.remove("is-open");
          list.hidden = true;
          btn.setAttribute("aria-expanded", "false");
        }
      });
      list.addEventListener("click", function (e) {
        var li = e.target && e.target.closest ? e.target.closest(".bios-dd-opt") : null;
        if (!li || li.classList.contains("is-disabled")) return;
        e.preventDefault();
        e.stopPropagation();
        biosDdPick(sel, Number(li.getAttribute("data-idx")));
      });
      btn.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (!wrap.classList.contains("is-open")) btn.click();
        } else if (e.key === "Escape") {
          biosDdCloseAll();
        }
      });
      var mo = new MutationObserver(function () {
        biosDdSync(sel);
      });
      mo.observe(sel, { childList: true, subtree: true, attributes: true, attributeFilter: ["class", "disabled"] });
      sel._biosDdMo = mo;
      biosDdSync(sel);
    }
    function biosDdEnhanceAll(root) {
      root = root || document;
      var scope = root.querySelectorAll
        ? root.querySelectorAll("select")
        : [];
      /* only BIOS / modal selects */
      var nodes = [];
      if (root.matches && root.matches("select")) nodes.push(root);
      for (var i = 0; i < scope.length; i++) nodes.push(scope[i]);
      for (var j = 0; j < nodes.length; j++) {
        var sel = nodes[j];
        if (!sel || sel.tagName !== "SELECT") continue;
        var inBios =
          sel.closest &&
          (sel.closest(".librarian.is-readme") ||
            sel.closest(".librarian-modal-card") ||
            sel.closest("#readmeRoom") ||
            sel.id === "readmeHostsSelect" ||
            sel.id === "readmeCratesMode");
        if (!inBios) continue;
        biosDdEnhance(sel);
        biosDdSync(sel);
      }
    }
    function biosDdBoot() {
      if (document._biosDdBooted) {
        biosDdEnhanceAll(document);
        return;
      }
      document._biosDdBooted = true;
      biosDdEnhanceAll(document);
      document.addEventListener(
        "click",
        function (e) {
          if (e.target && e.target.closest && e.target.closest(".bios-dd")) return;
          biosDdCloseAll();
        },
        true
      );
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") biosDdCloseAll();
      });
      try {
        var obs = new MutationObserver(function (muts) {
          var need = false;
          for (var i = 0; i < muts.length; i++) {
            var m = muts[i];
            if (m.type === "childList") {
              for (var a = 0; a < m.addedNodes.length; a++) {
                var n = m.addedNodes[a];
                if (n.nodeType !== 1) continue;
                if (n.tagName === "SELECT" || (n.querySelector && n.querySelector("select"))) {
                  need = true;
                  break;
                }
              }
            }
            if (m.type === "attributes" && m.attributeName === "hidden" && m.target && !m.target.hidden) {
              if (m.target.querySelector && m.target.querySelector("select")) need = true;
            }
            if (need) break;
          }
          if (need) {
            clearTimeout(document._biosDdEnhanceT);
            document._biosDdEnhanceT = setTimeout(function () {
              biosDdEnhanceAll(document);
            }, 30);
          }
        });
        obs.observe(document.documentElement, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ["hidden"],
        });
      } catch (eObs) {}
    }

    function ensureHelpCm() {
      var el = $("readmeHelpLeaf");
      if (!el || el._cm || !window.CodeMirror) return;
      try {
        var cm = window.CodeMirror.fromTextArea(el, {
          mode: "markdown",
          theme: "material-darker",
          lineNumbers: true,
          lineWrapping: true,
          tabSize: 2,
          viewportMargin: Infinity,
          extraKeys: {
            "Ctrl-S": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Cmd-S": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Ctrl-K": function (cm) {
              if (cm && cm.getOption) { /* claim over any kill-line default */ }
              cmSaveAll();
              storeThought();
              return false;
            },
            "Cmd-K": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Ctrl-Enter": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Cmd-Enter": function () {
              cmSaveAll();
              storeThought();
              return false;
            },
            "Ctrl-E": function () {
              letterFace = "room";
              letterEditMode = true;
              render();
              syncRoomLetterView();
            },
            "Cmd-E": function () {
              letterFace = "room";
              letterEditMode = true;
              render();
              syncRoomLetterView();
            },
          },
        });
        el._cm = cm;
      try { biosTableBind(cm); } catch (eH) {}
        if (typeof readmeCms !== "undefined" && readmeCms) readmeCms.push(cm);
      } catch (e) {}
    }

    function syncRoomLetterView() {
      var view = $("readmeRoomView");
      var editBtn = document.querySelector("[data-letter-edit]");
      var cancelBtn = document.querySelector("[data-letter-cancel]");
      var leaf = $(ids.leaf);
      var pane = view && view.closest ? view.closest(".readme-pane") : null;
      if (!view || !leaf) return;
      if (letterFace !== "room") {
        view.hidden = true;
        if (editBtn) editBtn.setAttribute("hidden", "");
        if (cancelBtn) cancelBtn.setAttribute("hidden", "");
        if (pane) pane.classList.remove("is-printout", "is-editing");
        return;
      }
      var has = !!(blot.body && String(blot.body).trim());
      var editing = letterEditMode || !has;
      if (pane) {
        pane.classList.toggle("is-printout", !editing);
        pane.classList.toggle("is-editing", editing);
      }
      function showCm(on) {
        if (leaf._cm) {
          /* CM owns the surface — never un-hide the raw textarea or you get two editors */
          leaf.style.display = "none";
          try {
            var w = leaf._cm.getWrapperElement();
            if (w) {
              w.style.display = on ? "" : "none";
              if (on) w.removeAttribute("hidden");
              else w.setAttribute("hidden", "");
            }
            if (on) leaf._cm.refresh();
          } catch (e) {}
        } else {
          leaf.style.display = on ? "" : "none";
        }
      }
      if (editing) {
        view.innerHTML = "";
        view.setAttribute("hidden", "");
        showCm(true);
        if (editBtn) editBtn.setAttribute("hidden", "");
        if (cancelBtn) {
          if (has) cancelBtn.removeAttribute("hidden");
          else cancelBtn.setAttribute("hidden", "");
        }
      } else {
        var html = blot.body_html;
        if (!html) {
          var raw = blot.body || "";
          html = raw.trim()
            ? '<pre class="readme-letter-fallback">' + escapeHtml(raw) + "</pre>"
            : '<p class="readme-letter-empty">(empty letter — hit Edit)</p>';
        }
        view.innerHTML = html;
        view.removeAttribute("hidden");
        showCm(false);
        if (editBtn) editBtn.removeAttribute("hidden");
        if (cancelBtn) cancelBtn.setAttribute("hidden", "");
      }
    }

    function coatWhich() {
      return letterFace === "coat" && letterWhich === "page" ? "page" : "shell";
    }

    function biosFaceLabel() {
      // Title: ROOM — DOOR (caps). Second rail: BIOS + edit path.
      var clay;
      var kind;
      var file;
      var loc;
      var room = String(vaultPath() || (blot && blot.pocket) || "").replace(/^\/+|\/+$/g, "");
      if (!room || room === ".") room = "root";
      // leaf folder name if nested
      if (room.indexOf("/") >= 0) room = room.replace(/^.*\//, "");

      function pack(door, editLoc) {
        return {
          door: door,
          loc: editLoc,
          title: room + " — " + String(door).toUpperCase(),
        };
      }

      if (letterFace === "help") {
        loc = helpSlug ? "~help/" + helpSlug : "~help/_index";
        return pack("help", loc);
      }

      if (letterFace === "hosts") {
        loc =
          (hostsBlot && (hostsBlot.shell_path || hostsBlot.letter_path)) ||
          (hostsSlug ? "~hosts/" + hostsSlug + "/_shell.md" : "~hosts");
        return pack("hosts", loc);
      }

      if (letterFace === "crates") {
        return pack("crate", "~bios/crates");
      }

      if (letterFace === "coat") {
        var which = coatWhich();
        var coat = blot.coat || null;
        if (which === "page" && coat && coat.page_override) {
          file = coat.page_override.file || "page.css";
          return pack("css", "mats/styles/" + file);
        }
        file = (coat && (coat.file || ((coat.env || "") + ".css"))) || "coat.css";
        return pack("css", "mats/styles/" + file);
      }
              if (letterFace === "page") {
        clay = currentClay();
        kind = (clay && clay.kind) || letterWhich || "page";
        if (kind === "shell") {
          // Prefer pocket/dir — bare _shell.md hides whether this is an ancestor zone.
          loc =
            (clay && (clay.pocket || (clay.dir ? clay.dir + "/_shell.md" : "") || clay.file)) ||
            "_shell.md";
          loc = String(loc);
          if (clay && clay.dir) {
            var zone = String(clay.dir).replace(/^.*\//, "") || String(clay.dir);
            if (zone) room = zone;
          }
          var door = clay && clay.here === false ? "shell↑" : "shell";
          return {
            door: door,
            loc: loc,
            title: room + " — " + String(door).toUpperCase(),
          };
        }
        loc =
          (clay && (clay.pocket || clay.file || clay.path || clay.title)) ||
          String(kind);
        loc = String(loc);
        return pack(kind === "note" ? "paper" : "paper", loc);
      }
      loc = String((blot && blot.pocket) || "");
      if (!loc || loc === "/") loc = String(vaultPath() || "");
      if (loc && !/readme\.md$/i.test(loc)) {
        loc = loc.replace(/\/?$/, "/") + "README.md";
      }
      if (!loc) loc = "README.md";
      return pack("room letter", loc);
    }

    function paintBiosSidecarTitle(label) {
      if (!SIDECAR) return;
      var el = $("sidecarTitle");
      if (el) el.textContent = label || "room — ROOM LETTER";
      if (label) document.title = "BIOS · " + label;
    }

    function captureEditorIntoBlot() {
      // Persist unsaved CM text into blot before leaving a face (e.g. open Help).
      function saveEl(el) {
        if (!el) return "";
        if (el._cm) {
          try {
            el._cm.save();
          } catch (e) {}
        }
        return el.value || "";
      }
      if (letterFace === "room") {
        blot.body = saveEl($(ids.leaf));
        return;
      }
      if (letterFace === "page") {
        var clay = currentClay();
        if (!clay) return;
        clay.headers = saveEl($(ids.headers));
        clay.body = saveEl($(ids.markdown));
        return;
      }
      if (letterFace === "coat" && blot.coat) {
        var which = coatWhich();
        var cssText = saveEl($(ids.coat));
        if (which === "page" && blot.coat.page_override) blot.coat.page_override_css = cssText;
        else blot.coat.css = cssText;
      }
    }


    var templateChoices = [];
    function loadTemplatesList() {
      return api("GET", "/api/templates")
        .then(function (data) {
          templateChoices = (data && data.templates) || [];
          return templateChoices;
        })
        .catch(function () {
          templateChoices = [
            { id: "blank", title: "Blank", description: "Just paper" },
            { id: "stack", title: "Header + nav", description: "Header, navbar, body, footer" },
            { id: "rail-left", title: "Sidebar left", description: "Left rail navbar" },
            { id: "rail-right", title: "Sidebar right", description: "Right rail navbar" },
          ];
          return templateChoices;
        });
    }

    function templateSelectHtml(selected) {
      selected = selected || "stack";
      var opts =
        '<option value="">doors (default)</option>' +
        '<option value="blank"' +
        (selected === "blank" ? " selected" : "") +
        ">Blank</option>" +
        '<option value="stack"' +
        (selected === "stack" ? " selected" : "") +
        ">Header + nav</option>" +
        '<option value="rail-left"' +
        (selected === "rail-left" ? " selected" : "") +
        ">Sidebar left</option>" +
        '<option value="rail-right"' +
        (selected === "rail-right" ? " selected" : "") +
        ">Sidebar right</option>";
      return (
        "<label>template</label>" +
        '<select data-field="template" class="librarian-leaf tagbay-input">' +
        opts +
        "</select>"
      );
    }

    function openApplyTemplateModal() {
      if (librarianOff()) return;
      var slug = hostsSlug || (hostsBlot && hostsBlot.host) || currentPocketHost() || "";
      if (!slug) {
        setStatus("open a host first", true);
        return;
      }
      modalMode = "apply-template";
      var titleEl = $(ids.modalTitle);
      var body = $(ids.modalBody);
      var modal = $(ids.modal);
      if (!titleEl || !body || !modal) return;
      titleEl.textContent = "Apply template";
      body.innerHTML =
        '<p class="librarian-onto">overwrite shell + coat, or fork a new coat name for go.' +
        String(slug) +
        "</p>" +
        templateSelectHtml("stack") +
        "<label>mode</label>" +
        '<select data-field="mode" class="librarian-leaf tagbay-input">' +
        '<option value="overwrite" selected>overwrite shell + CSS</option>' +
        '<option value="fork">fork new CSS name</option>' +
        "</select>";
      modal.removeAttribute("hidden");
    }

    function openHelpFace() {
      captureEditorIntoBlot();
      if (letterFace !== "help") {
        helpReturnFace = letterFace;
        helpReturnEdit = letterEditMode;
      }
      letterFace = "help";
      helpOpen = false;
      helpEditMode = false;
      loadHelp(helpSlug || "_index");
      render();
      syncHelpFab();
    }

    function closeHelpFace() {
      letterFace = helpReturnFace || "room";
      letterEditMode = !!helpReturnEdit;
      helpOpen = false;
      helpEditMode = false;
      render();
      syncHelpFab();
    }

    

    function syncHostsFab() {
      var fab = $("readmeHostsFab");
      if (fab) {
        fab.removeAttribute("hidden");
        var on = letterFace === "hosts";
        fab.classList.toggle("is-on", on);
        fab.setAttribute("aria-pressed", on ? "true" : "false");
        fab.title = on
          ? "back to editor (draft kept in memory until Keep)"
          : "go / roam registry — connect libraries, edit any host shell/letter";
      }
      var hostBtn = document.querySelector("[data-new-host]");
      if (hostBtn) {
        if (letterFace === "hosts") hostBtn.removeAttribute("hidden");
        else hostBtn.setAttribute("hidden", "");
      }
      var roamBtn = document.querySelector("[data-new-roam]");
      if (roamBtn) {
        if (letterFace === "hosts") roamBtn.removeAttribute("hidden");
        else roamBtn.setAttribute("hidden", "");
      }
    }


    function hostSlugFromGoPath(s) {
      s = String(s || "").replace(/\\/g, "/").trim();
      if (!s || s === "/" || s === "start" || s === "go" || s === "roam" || s === "recent") return "";
      var m = s.match(/(?:^|\/)(?:go|roam)\.([^\/\s?#]+)/i);
      if (m) return String(m[1] || "").toLowerCase();
      return "";
    }

    function currentPocketHost() {
      /* Prefer the pocket you are standing in — not the last Hosts dropdown pick. */
      function fromHref(href) {
        try {
          var u = new URL(String(href || ""), window.location.href);
          return String(u.searchParams.get("h") || "").trim().toLowerCase();
        } catch (e) {
          return "";
        }
      }
      var h = fromHref(window.location.href);
      if (h) return h;
      try {
        if (window.opener && !window.opener.closed) {
          h = fromHref(window.opener.location.href);
          if (h) return h;
          var od = window.opener.document;
          h =
            hostSlugFromGoPath(od.documentElement.getAttribute("data-pocket")) ||
            hostSlugFromGoPath(od.documentElement.getAttribute("data-vault")) ||
            hostSlugFromGoPath(od.documentElement.getAttribute("data-route"));
          if (h) return h;
        }
      } catch (e2) {}
      try {
        h =
          hostSlugFromGoPath(htmlRoot().getAttribute("data-pocket")) ||
          hostSlugFromGoPath(htmlRoot().getAttribute("data-vault")) ||
          hostSlugFromGoPath(htmlRoot().getAttribute("data-route"));
        if (h) return h;
      } catch (e3) {}
      try {
        if (typeof here !== "undefined" && here && here.vault) {
          h = hostSlugFromGoPath(here.vault);
          if (h) return h;
        }
      } catch (e4) {}
      try {
        var pin = readDeskPin();
        if (pin && pin.href) {
          h = fromHref(pin.href);
          if (h) return h;
        }
        if (pin && pin.vault) {
          h = hostSlugFromGoPath(pin.vault);
          if (h) return h;
        }
      } catch (e5) {}
      try {
        h = fromHref(vaultPath());
        if (h) return h;
        h = hostSlugFromGoPath(vaultPath());
        if (h) return h;
      } catch (e6) {}
      return "";
    }

    function openHostsFace() {
      captureEditorIntoBlot();
      if (letterFace !== "hosts") {
        hostsReturnFace = letterFace;
        hostsReturnEdit = letterEditMode;
      }
      letterFace = "hosts";
      hostsEditMode = false;
      /* Help-style chrome window: open/close via Hosts FAB.
         Prefer the pocket underfoot, then the last dropdown pick. */
      loadHosts(hostsSlug || currentPocketHost() || "");
      render();
      syncHostsFab();
    }


    function closeHostsFace() {
      letterFace = hostsReturnFace || "room";
      letterEditMode = !!hostsReturnEdit;
      hostsEditMode = false;
      render();
      syncHostsFab();
    }

    function syncCratesFab() {
      var fab = $("readmeCratesFab");
      if (!fab) return;
      fab.removeAttribute("hidden");
      var on = letterFace === "crates";
      fab.classList.toggle("is-on", on);
      fab.setAttribute("aria-pressed", on ? "true" : "false");
      fab.title = on
        ? "back to editor"
        : "crate finder — copy crate.HEX or {{link:crate.HEX}}";
    }

    function openCratesFace() {
      captureEditorIntoBlot();
      if (letterFace !== "crates") {
        cratesReturnFace = letterFace;
        cratesReturnEdit = letterEditMode;
      }
      letterFace = "crates";
      render();
      syncCratesFab();
      var modeEl = $("readmeCratesMode");
      if (modeEl && cratesMode) {
        try {
          modeEl.value = cratesMode;
        } catch (e0) {}
      }
      var qEl = $("readmeCratesQ");
      if (qEl) {
        if (cratesQuery) qEl.value = cratesQuery;
        window.setTimeout(function () {
          try {
            qEl.focus();
            if (!String(qEl.value || "").trim()) qEl.select();
          } catch (e) {}
        }, 30);
      }
      if (cratesQuery) runCratesSearch(cratesQuery);
    }
    function closeCratesFace() {
      letterFace = cratesReturnFace || "room";
      letterEditMode = !!cratesReturnEdit;
      render();
      syncCratesFab();
    }

    function renderCratesResults(items, q) {
      var host = $("readmeCratesResults");
      if (!host) return;
      items = items || [];
      if (!q) {
        host.innerHTML =
          '<p class="readme-crates-empty">type a title, path, or crate hex</p>';
        return;
      }
      if (!items.length) {
        host.innerHTML =
          '<p class="readme-crates-empty">no crates for "' +
          escapeHtml(q) +
          '"</p>';
        return;
      }
      var html = "";
      for (var i = 0; i < items.length; i++) {
        var it = items[i] || {};
        var crate = String(it.crate || "");
        var title = String(it.title || "");
        var pocket = String(it.pocket || it.path || "");
        html +=
          '<div class="readme-crates-row" data-crate="' +
          escapeHtml(crate) +
          '">' +
          '<div class="readme-crates-meta">' +
          '<div class="readme-crates-title">' +
          escapeHtml(title) +
          "</div>" +
          '<div class="readme-crates-pocket">' +
          escapeHtml(pocket) +
          "</div>" +
          '<div class="readme-crates-id">' +
          escapeHtml(crate) +
          "</div>" +
          "</div>" +
          '<div class="readme-crates-acts">' +
          '<button type="button" class="readme-crates-btn" data-crates-copy="' +
          escapeHtml(crate) +
          '" title="copy crate id">copy</button>' +
          '<button type="button" class="readme-crates-btn" data-crates-link="' +
          escapeHtml(crate) +
          '" title="copy {{link:crate}}">link</button>' +
          '<button type="button" class="readme-crates-btn" data-crates-face="' +
          escapeHtml(crate) +
          '" title="copy {{face:crate}}">face</button>' +
          "</div>" +
          "</div>";
      }
      host.innerHTML = html;
    }
    function cratesSearchMode() {
      var modeEl = $("readmeCratesMode");
      var mode = modeEl
        ? String(modeEl.value || "").trim().toLowerCase()
        : cratesMode;
      if (
        ["all", "title", "path", "body", "crate"].indexOf(mode) < 0
      ) {
        mode = "all";
      }
      cratesMode = mode;
      return mode;
    }

    function cratesSearchQuery() {
      var qEl = $("readmeCratesQ");
      return String(qEl ? qEl.value : cratesQuery || "").trim();
    }

    function runCratesSearch(q) {
      var mode = cratesSearchMode();
      cratesQuery = String(
        q != null && q !== undefined ? q : cratesSearchQuery()
      ).trim();
      if (!cratesQuery) {
        cratesSearchGen += 1;
        renderCratesResults([], "");
        return;
      }
      var gen = (cratesSearchGen += 1);
      var host = $("readmeCratesResults");
      if (host) {
        host.innerHTML =
          '<p class="readme-crates-empty">searching...</p>';
      }
      api(
        "GET",
        "/api/crates/search?q=" +
          encodeURIComponent(cratesQuery) +
          "&mode=" +
          encodeURIComponent(mode)
      )
        .then(function (data) {
          if (gen !== cratesSearchGen) return;
          renderCratesResults((data && data.items) || [], cratesQuery);
        })
        .catch(function (err) {
          if (gen !== cratesSearchGen) return;
          setStatus(err.message || "crates search failed", true);
        });
    }
    function scheduleCratesSearch() {
      if (cratesTimer) window.clearTimeout(cratesTimer);
      cratesTimer = window.setTimeout(function () {
        cratesTimer = null;
        runCratesSearch(cratesSearchQuery());
      }, 350);
    }
    function copyCratesText(text, okMsg) {
      text = String(text || "");
      if (!text) {
        setStatus("no crate", true);
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () {
            setStatus(okMsg || ("copied " + text));
          },
          function () {
            setStatus("could not copy", true);
          }
        );
      } else {
        setStatus(text);
      }
    }

    /* Help + Hosts + Crates are chrome windows for this spot — drop them when the live page moves. */
    var chromeVaultKey = null;
    function dismissChromeWindows() {
      if (letterFace === "help") closeHelpFace();
      else if (letterFace === "hosts") closeHostsFace();
      else if (letterFace === "crates") closeCratesFace();
    }
    function dismissChromeWindowsIfVaultMoved() {
      var key =
        String(vaultPath() || "") +
        "\0" +
        (librarianOff() ? "1" : "0");
      if (chromeVaultKey === null) {
        chromeVaultKey = key;
        return;
      }
      if (key === chromeVaultKey) return;
      chromeVaultKey = key;
      dismissChromeWindows();
    }

    function loadHosts(slug) {
      var q = slug ? "?host=" + encodeURIComponent(slug) : "";
      api("GET", "/api/hosts" + q)
        .then(function (data) {
          hostsBlot = data || hostsBlot;
          if (hostsBlot.host) hostsSlug = hostsBlot.host;
          var hasLetter = !!(hostsBlot.letter_body && String(hostsBlot.letter_body).trim());
          hostsEditMode = !hasLetter;
          fillHosts();
          syncHostsLetterView();
          syncHostsFab();
        })
        .catch(function (err) {
          setStatus(err.message || "hosts load failed", true);
        });
    }


    function hostYamlScalar(s) {
      s = String(s == null ? "" : s);
      if (s === "") return '""';
      if (s.trim() !== s || /[:#{}[\]&*!|>%@`'",\n]/.test(s)) {
        return JSON.stringify(s);
      }
      return s;
    }

    function roamFrontMatter(blot) {
      var src = (blot && blot.source) || "";
      var title = (blot && blot.title) || (blot && blot.host) || "";
      var env = (blot && blot.environment) || "";
      return [
        "kind: roam",
        "source: " + src,
        "title: " + (title ? hostYamlScalar(title) : '""'),
        "environment: " + (env ? hostYamlScalar(env) : ""),
      ].join("\n");
    }

    function parseHostHeaders(text) {
      var out = {};
      var raw = String(text || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
      if (raw.indexOf("---\n") === 0) {
        var end = raw.indexOf("\n---", 4);
        raw = end >= 0 ? raw.slice(4, end) : raw.slice(4);
      }
      var lines = raw.split("\n");
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        if (!line || /^\s*#/.test(line)) continue;
        var cut = line.indexOf(":");
        if (cut < 1) continue;
        var key = line.slice(0, cut).trim().toLowerCase();
        if (!/^[a-z0-9_-]+$/.test(key)) continue;
        var val = line.slice(cut + 1).replace(/^\s+/, "");
        if (
          val.length >= 2 &&
          ((val.charAt(0) === '"' && val.charAt(val.length - 1) === '"') ||
            (val.charAt(0) === "'" && val.charAt(val.length - 1) === "'"))
        ) {
          try {
            val =
              val.charAt(0) === '"'
                ? JSON.parse(val)
                : val.slice(1, -1);
          } catch (e) {
            val = val.slice(1, -1);
          }
        }
        if (key === "path" || key === "folder") key = "source";
        if (key === "env" || key === "coat") key = "environment";
        out[key] = val;
      }
      return out;
    }

    function fillHosts() {
      var sel = $("readmeHostsSelect");
      var list = (hostsBlot && hostsBlot.hosts) || [];
      /* Start-registry pane: never re-lock to the pocket underfoot —
         the dropdown pick is the editing target and must stick. */
      if (sel) {
        var html = "";
        for (var i = 0; i < list.length; i++) {
          var h = list[i];
          var scheme = h.kind === "roam" || h.scheme === "roam" ? "roam." : "";
          var label = scheme + (h.slug || "");
          if (h.title && String(h.title).toLowerCase() !== String(h.slug || "").toLowerCase()) {
            label += " — " + h.title;
          }
          if (h.section) label += " · " + h.section;
          if (h.show === false) label += " · off";
          html +=
            '<option value="' +
            escapeHtml(h.slug) +
            '"' +
            (h.slug === hostsSlug ? " selected" : "") +
            (h.show === false ? ' class="is-host-off"' : "") +
            ">" +
            escapeHtml(label) +
            "</option>";
        }
        sel.innerHTML = html;
        if (hostsSlug) sel.value = hostsSlug;
        if (hostsBlot && hostsBlot.show === false) sel.classList.add("is-host-off");
        else sel.classList.remove("is-host-off");
        try {
          biosDdEnhance(sel);
          biosDdSync(sel);
        } catch (eDd) {}
      }
      var showBtn = document.querySelector("[data-hosts-show]");
      var isRoam = !!(hostsBlot && hostsBlot.kind === "roam");
      var doorsName = isRoam ? "roam doors" : "go doors";
      if (showBtn) {
        var shown = !(hostsBlot && hostsBlot.show === false);
        showBtn.textContent = shown ? "Hide" : "Show";
        showBtn.setAttribute("aria-pressed", shown ? "true" : "false");
        showBtn.title = shown ? "hide from " + doorsName : "show on " + doorsName;
      }
      var pinBtn = document.querySelector("[data-hosts-pin]");
      if (pinBtn) {
        var pinned = hostsBlot && hostsBlot.pin != null && hostsBlot.pin !== "";
        pinBtn.textContent = pinned ? "Unpin" : "Pin";
        pinBtn.setAttribute("aria-pressed", pinned ? "true" : "false");
        pinBtn.title = pinned ? "unpin from " + doorsName : "pin on " + doorsName;
      }
      var roamPane = $("readmeHostsRoam");
      if (roamPane) roamPane.hidden = !isRoam;
      var shellPane = document.querySelector("#readmeHostsPane .is-hosts-shell");
      // BAY-003-BUG03: roam uses the same shell frontmatter editor as go.*
      if (shellPane) shellPane.hidden = false;
      var shellBar = shellPane && shellPane.querySelector(".readme-pane-bar");
      if (shellBar) shellBar.textContent = isRoam ? "roam frontmatter" : "shell frontmatter";
      var schemeLab = $("readmeHostsScheme");
      if (schemeLab) {
        var slugNow = (hostsBlot && hostsBlot.host) || hostsSlug || "";
        schemeLab.textContent = isRoam ? "roam." + slugNow : slugNow ? "go." + slugNow : "";
      }
      var head = $("readmeHostsHeaders");
      // Roam: prefer real shell frontmatter (same as go doors); else seed from yaml.
      var headers = (hostsBlot && hostsBlot.shell_headers) || "";
      if (isRoam && !String(headers).trim()) {
        headers = roamFrontMatter(hostsBlot);
      }
      if (head) {
        head.value = headers;
        if (head._cm) {
          try {
            if (head._cm.getValue() !== headers) head._cm.setValue(headers);
          } catch (e) {}
        }
      }
      var letter = $("readmeHostsLetter");
      var body = (hostsBlot && hostsBlot.letter_body) || "";
      if (letter) {
        letter.value = body;
        if (letter._cm) {
          try {
            if (letter._cm.getValue() !== body) letter._cm.setValue(body);
          } catch (e2) {}
        }
      }
      var bar = $("readmeHostsLetterBar");
      var lab = bar && bar.querySelector(".readme-letter-label");
      if (lab) {
        var tip = (hostsBlot && hostsBlot.letter_path) || "room letter";
        lab.textContent = "room letter";
        lab.title = tip;
      }
      if (letterFace === "hosts") {
        try {
          if (typeof cmFitEl === "function") {
            cmFitEl($("readmeHostsHeaders"));
            cmFitEl($("readmeHostsLetter"));
          }
          var hh = $("readmeHostsHeaders");
          if (hh && hh._cm) hh._cm.refresh();
        } catch (e3) {}
      }
    }

    function syncHostsLetterView() {
      var view = $("readmeHostsLetterView");
      var editBtn = document.querySelector("[data-hosts-edit]");
      var cancelBtn = document.querySelector("[data-hosts-cancel]");
      var leaf = $("readmeHostsLetter");
      var pane = view && view.closest ? view.closest(".readme-pane") : null;
      if (!view || !leaf) return;
      if (letterFace !== "hosts") {
        view.hidden = true;
        if (editBtn) editBtn.setAttribute("hidden", "");
        if (cancelBtn) cancelBtn.setAttribute("hidden", "");
        if (pane) pane.classList.remove("is-printout", "is-editing");
        if (leaf._cm) {
          try {
            var w = leaf._cm.getWrapperElement();
            if (w) w.style.display = "none";
          } catch (e) {}
        }
        leaf.setAttribute("hidden", "");
        return;
      }
      var has = !!(hostsBlot.letter_body && String(hostsBlot.letter_body).trim());
      var editing = hostsEditMode || !has;
      if (pane) {
        pane.classList.toggle("is-printout", !editing);
        pane.classList.toggle("is-editing", editing);
      }
      function showHostsCm(on) {
        if (!leaf._cm) return;
        try {
          var w = leaf._cm.getWrapperElement();
          if (w) w.style.display = on ? "" : "none";
          if (on) leaf._cm.refresh();
        } catch (e) {}
      }
      if (editing) {
        view.hidden = true;
        leaf.removeAttribute("hidden");
        if (leaf._cm) {
          leaf.style.display = "none";
          showHostsCm(true);
        } else {
          leaf.style.display = "";
        }
        if (editBtn) editBtn.setAttribute("hidden", "");
        if (cancelBtn) {
          if (has) cancelBtn.removeAttribute("hidden");
          else cancelBtn.setAttribute("hidden", "");
        }
      } else {
        view.hidden = false;
        view.innerHTML =
          (hostsBlot.letter_html && String(hostsBlot.letter_html).trim()) ||
          '<p class="readme-letter-empty">(empty letter - hit Edit)</p>';
        leaf.setAttribute("hidden", "");
        leaf.style.display = "none";
        showHostsCm(false);
        if (editBtn) editBtn.removeAttribute("hidden");
        if (cancelBtn) cancelBtn.setAttribute("hidden", "");
      }
    }


    function fillCoat() {
      var coat = blot.coat || null;
      var el = $(ids.coat);
      var bar = $("readmeCoatBar");
      var which = coatWhich();
      var body = "";
      var label = "coat css";
      if (coat) {
        if (which === "page" && coat.page_override) {
          body = coat.page_override_css != null ? String(coat.page_override_css) : "";
          label = "page css · " + (coat.page_override.file || "") + " (override)";
        } else {
          body = coat.css != null ? String(coat.css) : "";
          label = "coat css · " + (coat.file || "") + (coat.source ? " · " + coat.source : "");
          if (coat.exists === false) label += " (missing file)";
        }
      }
      if (el) {
        el.value = body;
        if (el._cm) {
          try {
            if (el._cm.getValue() !== body) el._cm.setValue(body);
          } catch (e) {}
        }
      }
      if (bar) bar.textContent = label;
      if (letterFace === "coat") ensureCoatCm();
    }

    function fillClay() {
      var clay = currentClay();
      var head = $(ids.headers);
      var md = $(ids.markdown);
      if (head) head.value = (clay && clay.headers) || "";
      if (md) md.value = (clay && clay.markdown) || "";
      if (head && head._cm) head._cm.setValue(head.value);
      if (md && md._cm) md._cm.setValue(md.value);
      readmePaneBars();
    }

    var statusHide = 0;
    var statusFade = 0;

    function setStatus(msg, isErr) {
      var el = $(ids.status);
      if (!el) return;
      if (statusHide) {
        clearTimeout(statusHide);
        statusHide = 0;
      }
      if (statusFade) {
        clearTimeout(statusFade);
        statusFade = 0;
      }
      el.classList.remove("is-fade");
      el.textContent = msg || "";
      el.classList.toggle("is-err", !!isErr);
      if (!msg) return;
      var shown = msg;
      statusHide = setTimeout(function () {
        statusHide = 0;
        el.classList.add("is-fade");
        statusFade = setTimeout(function () {
          statusFade = 0;
          if (el.textContent !== shown) return;
          el.textContent = "";
          el.classList.remove("is-err", "is-fade");
        }, 450);
      }, isErr ? 5500 : 4000);
    }

    function wantOpen() {
      try {
        if (sessionStorage.getItem(cfg.openKey) === "1") return true;
        if (cfg.openKeyLegacy && sessionStorage.getItem(cfg.openKeyLegacy) === "1") return true;
        return false;
      } catch (e) {
        return false;
      }
    }

    function rememberOpen(on) {
      if (SIDECAR) return;
      try {
        if (on) sessionStorage.setItem(cfg.openKey, "1");
        else sessionStorage.removeItem(cfg.openKey);
        if (cfg.openKeyLegacy) sessionStorage.removeItem(cfg.openKeyLegacy);
      } catch (e) {}
    }

    function applyOpen(on) {
      on = !!on;
      if (on === open) return;
      if (on && !SIDECAR) dockOnly(cfg.id);
      open = on;
      document.body.classList.toggle(cfg.bodyClass, open);
      var drawer = $(ids.drawer);
      if (drawer) {
        if (open) drawer.removeAttribute("hidden");
        else drawer.setAttribute("hidden", "");
      }
      rememberOpen(open);
      if (!SIDECAR) {
        if (open) dockRemember(cfg.id);
        else if (dockWanted() === cfg.id) dockRemember("");
      }
      if (open) {
        loadBlot();
        stopRefresh();
        refreshTimer = window.setInterval(function () {
          refreshBlot(true);
        }, 15000);
      } else {
        stopRefresh();
      }
    }

    function toggle() {
      applyOpen(!open);
      if (open) {
        if (cfg.kind === "catalog" || cfg.kind === "tps" || cfg.kind === "cards") return;
        var leaf = $(ids.leaf);
        if (leaf) leaf.focus();
      }
    }

    function render() {
      if (isChipGuest() && letterFace === "page" && letterWhich === "note") {
        var guestPages = clayPages();
        letterWhich = (guestPages[0] && guestPages[0].kind) || "";
        if (!letterWhich) letterFace = "room";
      }
      var pathEl = $(ids.path);
      var countEl = $(ids.count);
      var stack = $(ids.stack);
      var composer = $(ids.composer);
      var drawer = $(ids.drawer);
      if (!stack || !drawer) return;
      var off = librarianOff();
      drawer.classList.toggle("librarian-off", off);
      var pocket = blot.pocket || "/" + vaultPath();
      if (cfg.kind === "letter" && letterFace === "page") {
        var clay = currentClay();
        pocket = (clay && clay.pocket) || vaultPath() || pocket;
      }
      if (pathEl) {
        if (off) {
          pathEl.textContent = "no blotter on this page";
          pathEl.removeAttribute("title");
        } else if (cfg.kind === "letter") {
                    var shortPath;
          var fullPath;
          var face = biosFaceLabel();
          shortPath = face.door;
          fullPath = face.loc;
          pathEl.textContent = face.loc;
          pathEl.title = face.loc;
          paintBiosSidecarTitle(face.title);

        } else if (cfg.kind === "catalog" || cfg.kind === "tags" || cfg.kind === "tps") {
          pathEl.textContent = "";
          pathEl.hidden = true;
        } else {
          pathEl.hidden = false;
          pathEl.textContent = pocket;
          pathEl.removeAttribute("title");
        }
      }
      var crateEl = $(ids.crate);
      if (crateEl) {
        if (off) {
          crateEl.innerHTML = "";
        } else {
          var crateId = blot.crate || "";
          if (cfg.kind === "letter" && letterFace === "page") {
            var clayCrate = currentClay();
            crateId = (clayCrate && clayCrate.crate) || "";
          }
          if (cfg.kind === "catalog") {
            crateEl.innerHTML = "";
            crateEl.hidden = true;
            var copyBtn = drawer.querySelector("[data-copy-crate]");
            if (copyBtn) {
              var oc = ontoCrate();
              copyBtn.hidden = !oc;
              copyBtn.title = oc
                ? "Copy " + ontoLabel() + " crate " + oc
                : "No crate";
              copyBtn.setAttribute("data-crate-id", oc || "");
            }
          } else if (cfg.kind === "tags" || cfg.kind === "tps") {
            crateEl.innerHTML = "";
            crateEl.hidden = true;
          } else if (crateId) {
            crateEl.hidden = false;
            crateEl.innerHTML =
              '<a class="tagbay-crate-id" href="/?k=' +
              encodeURIComponent(crateId) +
              '">' +
              escapeHtml(crateId) +
              '</a><button type="button" class="tagbay-copy" data-copy-crate>copy</button>';
          } else if (cfg.kind === "letter") {
            crateEl.innerHTML = "";
          } else {
            crateEl.innerHTML =
              '<em class="tagbay-off">off ledger</em>' +
              '<button type="button" class="tagbay-issue" data-issue-crate>issue crate</button>';
          }
        }
      }
      if (cfg.kind === "catalog") {
        var ontoBar = drawer.querySelector(".catalog-onto");
        if (ontoBar) {
          if (hereIsShell()) catalogOnto = "shell";
          else if (!blot.shell && catalogOnto === "shell") catalogOnto = "page";
          if (canOntoShell()) {
            ontoBar.removeAttribute("hidden");
            ontoBar.classList.toggle("is-here-shell", hereIsShell());
            var hall = shellName();
            var btns = ontoBar.querySelectorAll("[data-catalog-onto]");
            for (var bi = 0; bi < btns.length; bi++) {
              var which = btns[bi].getAttribute("data-catalog-onto");
              btns[bi].classList.toggle("is-on", which === catalogOnto);
              if (which === "shell") {
                btns[bi].title = hall
                  ? hall + " — every page in this hall"
                  : "the shell — every page in this hall";
              }
            }
          } else {
            ontoBar.setAttribute("hidden", "");
            ontoBar.classList.remove("is-here-shell");
            catalogOnto = "page";
          }
        }
      }
      var n =
        cfg.kind === "catalog"
          ? (blot.fields || []).length +
            (blot.hunts || []).length +
            (blot.shell && blot.shell.fields ? blot.shell.fields.length : 0) +
            (blot.shell && blot.shell.hunts ? blot.shell.hunts.length : 0)
          : cfg.kind === "tps"
          ? (blot.stamps || []).length + (blot.eras || []).length
          : cfg.kind === "tags"
          ? (blot.thoughts || []).length +
            (blot.lore || []).length +
            (blot.threads || []).length +
            (blot.hashes || []).length
          : cfg.kind === "cards"
          ? (blot.cards || []).length
          : (blot.thoughts || []).length;
      var unit = n === 1 ? cfg.slips[0] : cfg.slips[1];
      if (countEl) {
        if (off) countEl.textContent = "";
        else if (cfg.kind === "letter") countEl.textContent = "";
        else if (cfg.kind === "tps") {
          var datesN = (blot.stamps || []).length;
          var erasN = (blot.eras || []).length;
          var bits = [];
          if (datesN) bits.push(datesN + (datesN === 1 ? " date" : " dates"));
          if (erasN) bits.push(erasN + (erasN === 1 ? " event" : " events"));
          countEl.textContent = bits.join(" · ");
        } else countEl.textContent = n + " " + unit;
      }
      if (composer) composer.hidden = off;
      if (off) {
        stack.innerHTML =
          SIDECAR && !here.vault
            ? '<p class="librarian-empty">Following the other window. Open a vault page there.</p>'
            : '<p class="librarian-empty">Wiki, tags, and missing pages have no drawer. Open a vault page.</p>';
        return;
      }
      if (cfg.kind === "letter") {
        var roomPane = $("readmeRoom");
        var pagePane = $("readmePage");
        var coatPane = $("readmeCoatPane");
        if (roomPane) roomPane.hidden = letterFace !== "room";
        if (pagePane) pagePane.hidden = letterFace !== "page";
        if (coatPane) coatPane.hidden = letterFace !== "coat";
        var helpPane = $("readmeHelpPane");
        if (helpPane) helpPane.hidden = letterFace !== "help";
        var hostsPane = $("readmeHostsPane");
        if (hostsPane) hostsPane.hidden = letterFace !== "hosts";
        var cratesPane = $("readmeCratesPane");
        if (cratesPane) cratesPane.hidden = letterFace !== "crates";
        syncRoomLetterView();
        syncHelpLetterView();
        syncHostsLetterView();
        syncRenameBtn();
        syncRenameFolderBtn();
        syncShellBtn();
        syncLetterBtn();
        syncHelpFab();
        syncHostsFab();
        syncCratesFab();
        function cmShow(el, on) {
          if (!el || !el._cm) return;
          try {
            var w = el._cm.getWrapperElement();
            if (w) w.style.display = on ? "" : "none";
          } catch (e) {}
        }
        cmShow(
          $(ids.leaf),
          letterFace === "room" && (letterEditMode || !(blot.body && String(blot.body).trim()))
        );
        cmShow($(ids.headers), letterFace === "page");
        cmShow($(ids.markdown), letterFace === "page");
        cmShow($("readmeHostsHeaders"), letterFace === "hosts");
        if (letterFace === "coat") {
          ensureCoatCm();
          cmShow($(ids.coat), true);
          bindCoatSplitToggle();
          bindCoatPalette();
          renderCoatPalette();
          applyCoatSplitState();
        } else {
          tearDownCoatCm();
          var pal = $("readmeCoatPalette");
          if (pal) pal.hidden = true;
        }
        var tabs = drawer.querySelectorAll("[data-readme-face]");
        for (var t = 0; t < tabs.length; t++) {
          tabs[t].classList.toggle(
            "is-on",
            tabs[t].getAttribute("data-readme-face") === letterFace
          );
        }
        var kick = drawer.querySelector(".librarian-kicker");
        if (kick) {
          /* BIOS identity lives in head; room/page tabs carry face */
          kick.textContent = "";
          kick.hidden = true;
        }
        var doors = $("readmeDoors");
        if (doors) {
          var pages = clayPages();
          var byKind = {};
          var pi;
          for (pi = 0; pi < pages.length; pi++) {
            byKind[pages[pi].kind || ""] = pages[pi];
          }
          if (letterFace === "page") {
            if (!letterWhich || !byKind[letterWhich]) {
              letterWhich =
                (byKind.note && "note") ||
                (byKind.paper && "paper") ||
                (byKind.shell && "shell") ||
                (pages[0] && pages[0].kind) ||
                "";
            }
          }
          var doorHtml =
            '<button type="button" class="readme-tab' +
            (letterFace === "room" ? " is-on" : "") +
            '" data-readme-door="room" title="room letter — how we use this space">room letter</button>';
          /* Hosts is a Help-style chrome window (FAB), not a room door. */

          var order = [];
          if (byKind.shell) order.push(byKind.shell);
          if (byKind.paper) order.push(byKind.paper);
          for (pi = 0; pi < pages.length; pi++) {
            var kk = pages[pi].kind || "";
            if (kk !== "shell" && kk !== "paper") order.push(pages[pi]);
          }
          for (pi = 0; pi < order.length; pi++) {
            var p = order[pi];
            var kind = p.kind || p.file || "page";
            var label =
              kind === "shell"
                ? "shell"
                : kind === "paper"
                ? "paper"
                : kind === "note"
                ? "page"
                : kind;
            var tip =
              kind === "shell"
                ? p.here === false
                  ? "shell — inherited from " + (p.dir || "zone above") + "/_shell.md"
                  : "shell — _shell for " + (p.dir || "this folder" || "this zone")
                : kind === "paper"
                ? "paper — the page body / index fill"
                : kind === "note"
                ? "page — this note (shell still from the _shell zone above)"
                : kind;
            if (kind === "shell" && p.here === false) label = "shell↑";
            doorHtml +=
              '<button type="button" class="readme-tab' +
              (letterFace === "page" && letterWhich === kind ? " is-on" : "") +
              '" data-readme-door="' +
              escapeHtml(kind) +
              '" title="' +
              escapeHtml(tip) +
              '">' +
              escapeHtml(label) +
              "</button>";
          }
          if (blot.coat && blot.coat.env) {
            doorHtml +=
              '<button type="button" class="readme-tab' +
              (letterFace === "coat" && letterWhich !== "page" ? " is-on" : "") +
              '" data-readme-door="coat" title="coat — mats/styles/' +
              escapeHtml(blot.coat.file || blot.coat.env + ".css") +
              '">css</button>';
            if (blot.coat.page_override && blot.coat.page_override.env) {
              doorHtml +=
                '<button type="button" class="readme-tab' +
                (letterFace === "coat" && letterWhich === "page" ? " is-on" : "") +
                '" data-readme-door="coat-page" title="page override — mats/styles/' +
                escapeHtml(blot.coat.page_override.file || "") +
                '">page css</button>';
            }
          }
          doors.innerHTML = doorHtml;
        }
        fillCoat();
        readmePaneBars();
        stack.innerHTML = "";
        return;
      }
      if (cfg.kind === "cards") {
        renderCards(stack);
        return;
      }
      if (cfg.kind === "catalog") {
        renderCatalog(stack);
        return;
      }
      if (cfg.kind === "tps") {
        paintTpsSheet();
        renderTps(stack);
        return;
      }
      if (cfg.kind === "tags") {
        var thoughts = blot.thoughts || [];
        var lore = blot.lore || [];
        var threads = blot.threads || [];
        var hashes = blot.hashes || [];
        if (!thoughts.length && !lore.length && !threads.length && !hashes.length) {
          stack.innerHTML = '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
          return;
        }
        var html = loreBlockHtml(lore);
        if (threads.length) {
          html += '<div class="cork-board cork-threads"><div class="catalog-head">threads</div>';
          threads.forEach(function (t) {
            html +=
              '<div class="cork-pin cork-thread" data-id="' +
              escapeHtml(t.id || "") +
              '">' +
              charlieEndHtml(t.from, "from") +
              '<span class="charlie-sep" aria-hidden="true">*</span>' +
              charlieEndHtml(t.rel, "rel", "cork-rel") +
              '<span class="charlie-sep" aria-hidden="true">&gt;</span>' +
              charlieEndHtml(t.to, "to") +
              '<button type="button" class="cork-unpin" data-drop-thread="' +
              escapeHtml(t.id || "") +
              '" title="unpin">×</button></div>';
          });
          html += "</div>";
        }
        if (thoughts.length) {
          html += '<div class="cork-board"><div class="catalog-head">tags</div>';
          thoughts.forEach(function (t) {
            var name = String(t.leaf || t.id || "").replace(/^#+\s*/, "").trim();
            var also = t.also || [];
            var alsoHtml = "";
            if (also.length) {
              alsoHtml =
                '<span class="cork-also">' +
                also.length +
                "</span><ul class='tagbay-also'>";
              also.forEach(function (b) {
                alsoHtml +=
                  '<li><a href="' +
                  escapeHtml(b.href || "/?p=" + String(b.pocket || "").replace(/^\//, "")) +
                  '">' +
                  escapeHtml(b.title || b.pocket || "") +
                  "</a></li>";
              });
              alsoHtml += "</ul>";
            }
            html +=
              '<div class="cork-pin" data-id="' +
              escapeHtml(t.id || "") +
              '">' +
              '<span class="cork-head"></span>' +
              '<a class="cork-name" href="/?c=' +
              encodeURIComponent(t.id || "") +
              '&as=tag">' +
              escapeHtml(name) +
              "</a>" +
              alsoHtml +
              '<button type="button" class="cork-unpin" data-drop="' +
              escapeHtml(t.id || "") +
              '" title="unpin">×</button>' +
              "</div>";
          });
          html += "</div>";
        }
        if (hashes.length) {
          html += '<div class="cork-board cork-hashes"><div class="catalog-head">hashes</div>';
          hashes.forEach(function (h) {
            var name = String(h.leaf || h.id || "").replace(/^#+\s*/, "").trim();
            html +=
              '<a class="cork-pin cork-hash-pin" href="/?h=code.tags&p=' +
              encodeURIComponent(String(h.id || name).replace(/^#/, '').toLowerCase().replace(/\s+/g, '-') + '.md') +
              '">' +
              '<span class="cork-hash" aria-hidden="true">#</span>' +
              escapeHtml(name) +
              "</a>";
          });
          html += "</div>";
        }
        stack.innerHTML = html;
        return;
      }
      var thoughts = blot.thoughts || [];
      if (!thoughts.length) {
        stack.innerHTML = '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
        return;
      }
      var html = "";
      thoughts.forEach(function (t) {
        html +=
          '<article class="librarian-thought" data-id="' +
          escapeHtml(t.id || "") +
          '">' +
          '<div class="librarian-meta">' +
          '<span class="librarian-id">' +
          escapeHtml(t.id || "") +
          "</span>" +
          '<span class="librarian-when">' +
          escapeHtml(fmtWhen(t.at)) +
          "</span>" +
          '<button type="button" class="librarian-drop" data-drop="' +
          escapeHtml(t.id || "") +
          '">void</button>' +
          "</div>" +
          '<div class="librarian-body">' +
          paintLeaf(t.leaf || "") +
          "</div>" +
          "</article>";
      });
      stack.innerHTML = html;
    }

    function fmtFieldValue(f) {
      var kind = String((f && f.type) || "input");
      var val = f && f.value;
      if (kind === "bool") return val ? "yes" : "no";
      if (kind === "time") {
        var n = Number(val);
        if (n) return fmtWhen(n) + " · " + n;
        return String(val || "");
      }
      return String(val == null ? "" : val);
    }

    function loreBlockHtml(lore, onto) {
      lore = lore || [];
      onto = onto || catalogOnto || "page";
      if (!lore.length) return "";
      var html = '<div class="catalog-block catalog-lore-shelf"><div class="catalog-head">lore</div><div class="catalog-mini-shelf">';
      lore.forEach(function (card) {
        var houseRaw = String(card.house || card.maker || "").toLowerCase();
        var houseSlug = "";
        if (houseRaw.indexOf("detective") >= 0 || houseRaw.indexOf("agent") >= 0) houseSlug = "detective";
        else if (houseRaw.indexOf("charlie") >= 0) houseSlug = "charlie";
        else if (houseRaw.indexOf("tps") >= 0) houseSlug = "tps";
        else if (houseRaw.indexOf("librarian") >= 0 || houseRaw.indexOf("io") >= 0) houseSlug = "librarian";
        var houseClass = houseSlug ? " house-" + houseSlug : "";
        var crate = String(card.crate || "").trim();
        var mouth = String(card.mouth || "").trim().toLowerCase();
        if (!mouth) {
          mouth = houseSlug || "";
        }
        html +=
          '<div class="catalog-mini-wrap">' +
          '<a class="catalog-mini-card lorecard' +
          houseClass +
          '" href="' +
          escapeHtml(card.href || "#") +
          '">' +
          (card.class
            ? '<span class="kicker">' + escapeHtml(card.class) + "</span>"
            : "") +
          (card.house || card.maker
            ? '<span class="house">' + escapeHtml(card.maker || card.house) + "</span>"
            : "") +
          "<h1>" +
          escapeHtml(card.title || card.file || "lore") +
          "</h1>" +
          (card.line
            ? '<p class="line">' + escapeHtml(card.line) + "</p>"
            : "") +
          "</a>" +
          '<div class="catalog-mini-tools">' +
          '<button type="button" class="catalog-edit" data-edit-lore="' +
          escapeHtml(crate) +
          '" title="edit">edit</button>' +
          '<button type="button" class="catalog-drop" data-drop-lore="' +
          escapeHtml(crate) +
          '" data-lore-mouth="' +
          escapeHtml(mouth) +
          '" data-onto="' +
          escapeHtml(onto) +
          '" title="detach from ' +
          escapeHtml(onto) +
          '">drop</button>' +
          "</div></div>";
      });
      html += "</div></div>";
      return html;
    }


    function loreByCrate(crate) {
      return loreByCrateFrom(crate);
    }

    function catalogBagHtml(bag, onto, title) {
      bag = bag || {};
      var fields = bag.fields || [];
      var lore = bag.lore || [];
      var hunts = bag.hunts || [];
      if (!fields.length && !lore.length && !hunts.length) return "";
      var html = '<div class="catalog-bag is-' + onto + (catalogOnto === onto ? " is-on" : "") + '">';
      html += '<div class="catalog-head catalog-bag-title">' + escapeHtml(title);
      if (bag.crate) {
        html +=
          ' <a class="tagbay-crate-id" href="/?k=' +
          encodeURIComponent(bag.crate) +
          '">' +
          escapeHtml(bag.crate) +
          "</a>";
      }
      html += "</div>";
      if (hunts.length) {
        html += '<div class="catalog-block hunt-slips"><div class="catalog-head">pinned</div>';
        hunts.forEach(function (h, hi) {
          html +=
            '<article class="hunt-slip hunt-slip-n' +
            ((hi % 3) + 1) +
            '">' +
            '<a class="hunt-slip-title" href="' +
            escapeHtml(h.href || "#") +
            '">' +
            escapeHtml(h.title || "slip") +
            "</a>" +
            (h.snippet
              ? '<p class="hunt-slip-body">' + escapeHtml(h.snippet) + "</p>"
              : "") +
            '<div class="hunt-slip-meta">' +
            (h.when
              ? '<time class="hunt-when">' + escapeHtml(h.when) + "</time>"
              : "") +
            (h.mindset
              ? '<span class="hunt-mind">' + escapeHtml(h.mindset) + "</span>"
              : "") +
            (h.crate
              ? '<span class="hunt-slip-tools">' +
                '<button type="button" class="catalog-edit" data-edit-hunt="' +
                escapeHtml(h.crate) +
                '" title="edit">edit</button>' +
                '<button type="button" class="catalog-drop" data-drop-hunt="' +
                escapeHtml(h.crate) +
                '" title="drop">drop</button>' +
                "</span>"
              : "") +
            "</div></article>";
        });
        html += "</div>";
      }
      if (fields.length) {
        html += '<div class="catalog-block"><div class="catalog-head catalog-meta-head">meta</div>';
        fields.forEach(function (f) {
          var bits = "";
          (f.chips || []).forEach(function (c) {
            bits +=
              '<a class="catalog-hit" href="' +
              escapeHtml(c.href || "#") +
              '">' +
              escapeHtml(c.value || "") +
              "</a>";
          });
          if (!bits) bits = escapeHtml(fmtFieldValue(f));
          var idx = f.i != null ? String(f.i) : "";
          html +=
            '<div class="catalog-row">' +
            '<span class="catalog-type">' +
            escapeHtml(f.type || "") +
            '</span><a class="catalog-label" href="' +
            escapeHtml(f.label_href || "#") +
            '">' +
            escapeHtml(f.label || "") +
            '</a><span class="catalog-tools">' +
            '<button type="button" class="catalog-edit" data-edit-meta="' +
            escapeHtml(idx) +
            '" data-onto="' +
            onto +
            '" title="edit">edit</button>' +
            '<button type="button" class="catalog-drop" data-drop-meta="' +
            escapeHtml(idx) +
            '" data-onto="' +
            onto +
            '" title="drop">drop</button>' +
            '</span><span class="catalog-value">' +
            bits +
            "</span></div>";
        });
        html += "</div>";
      }
      if (lore.length) {
        html += loreBlockHtml(lore, onto);
      }
      html += "</div>";
      return html;
    }


    function enhanceCardShelf(root) {
      if (!root) return;
      var shelf = root.classList && root.classList.contains("card-shelf")
        ? root
        : root.querySelector
        ? root.querySelector(".card-shelf")
        : null;
      if (!shelf) return;
      Array.prototype.forEach.call(
        shelf.querySelectorAll(".card-shelf-item"),
        function (item) {
          if (!item.hasAttribute("tabindex")) item.setAttribute("tabindex", "0");
          if (!item.hasAttribute("role")) item.setAttribute("role", "button");
          item.setAttribute(
            "aria-expanded",
            item.classList.contains("is-open") ? "true" : "false"
          );
          item.title = item.classList.contains("is-open")
            ? "click to fold"
            : "click to open shelf";
        }
      );
    }

    function bindCardShelfClicks() {
      if (document.__cardShelfBound) return;
      document.__cardShelfBound = true;
      document.addEventListener("click", function (e) {
        var item =
          e.target && e.target.closest
            ? e.target.closest(".librarian.is-cards .card-shelf-item")
            : null;
        if (!item) return;
        if (item.closest && item.closest(".lore-attach-list")) return;
        if (
          e.target.closest &&
          e.target.closest("a, button, input, textarea, select, label.lore-attach-face")
        )
          return;
        e.preventDefault();
        var open = item.classList.contains("is-open");
        var shelf = item.closest(".card-shelf");
        if (shelf) {
          Array.prototype.forEach.call(
            shelf.querySelectorAll(".card-shelf-item.is-open"),
            function (el) {
              if (el !== item) {
                el.classList.remove("is-open");
                el.setAttribute("aria-expanded", "false");
                el.title = "click to open shelf";
              }
            }
          );
        }
        item.classList.toggle("is-open", !open);
        item.setAttribute("aria-expanded", (!open).toString());
        item.title = !open ? "click to fold" : "click to open shelf";
      });
      document.addEventListener("keydown", function (e) {
        if (e.key !== "Enter" && e.key !== " ") return;
        var item =
          e.target && e.target.closest
            ? e.target.closest(".librarian.is-cards .card-shelf-item")
            : null;
        if (!item) return;
        e.preventDefault();
        item.click();
      });
    }

    function renderCards(stack) {
      if (deckHits) {
        if (!deckHits.length) {
          stack.innerHTML =
            '<p class="librarian-empty">nothing in the deck matches</p>';
          return;
        }
        stack.innerHTML = deckHits
          .map(function (card) {
            var title = escapeHtml(card.title || "untitled");
            var klass = escapeHtml(card.class || "");
            var house = escapeHtml(card.house || "");
            var line = escapeHtml(card.line || "");
            var href = escapeHtml(card.href || "#");
            var pop = card.pop
              ? '<a class="lore-chip-pop" href="' +
                escapeHtml(card.pop) +
                '">pop</a>'
              : "";
            return (
              '<article class="lore-chip deck-hit">' +
              '<a class="lore-chip-title" href="' +
              href +
              '">' +
              title +
              "</a>" +
              (klass
                ? '<span class="lore-chip-class">' + klass + "</span>"
                : "") +
              (house
                ? '<span class="lore-chip-house">' + house + "</span>"
                : "") +
              (line ? '<p class="lore-chip-line">' + line + "</p>" : "") +
              pop +
              "</article>"
            );
          })
          .join("");
        return;
      }
      var cards = blot.cards || [];
      var html = blot.html || "";
      if (!cards.length && !String(html).trim()) {
        stack.innerHTML =
          '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
        return;
      }
      if (String(html).trim()) {
        stack.innerHTML = html;
      } else {
        var out = '<div class="card-shelf">';
        cards.forEach(function (card) {
          if (card && card.html) out += card.html;
        });
        out += "</div>";
        stack.innerHTML = out;
      }
      enhanceCardShelf(stack);
      bindCardShelfClicks();
    }

    function renderCatalog(stack) {
      if (hereIsShell()) catalogOnto = "shell";
      var pageHtml = hereIsShell()
        ? ""
        : catalogBagHtml(blot, "page", "this page");
      var shellBag = blot.shell || (hereIsShell() ? blot : null);
      var hall = shellName();
      var shellTitle = hall ? "shell · " + hall : "the shell";
      var shellHtml = shellBag
        ? catalogBagHtml(shellBag, "shell", shellTitle)
        : "";
      if (!pageHtml && !shellHtml) {
        var empty = hereIsShell()
          ? "No fields on this shell yet. Add meta or lore — it applies to every page in this hall."
          : cfg.empty;
        stack.innerHTML =
          '<p class="librarian-empty">' + escapeHtml(empty) + "</p>";
        return;
      }
      stack.innerHTML = shellHtml + pageHtml;
    }

    function paintTpsSheet() {
      var drawer = $(ids.drawer);
      if (!drawer) return;
      var whereEl = drawer.querySelector(".tps-coord-where");
      var whenEl = drawer.querySelector(".tps-coord-when");
      var p = String(blot.pocket || vaultPath() || "").replace(/\/$/, "");
      var leaf = p.split("/").pop() || "this page";
      leaf = leaf.replace(/^go\./, "") || "this page";
      if (whereEl) whereEl.textContent = leaf;
      var stamps = blot.stamps || [];
      if (whenEl) {
        whenEl.textContent = stamps.length
          ? stamps[0].when || "stamped"
          : "unstamped";
      }
      paintEraNames();
    }

    function renderTps(stack) {
      var stamps = blot.stamps || [];
      var slices = blot.slices || {};
      var lore = blot.lore || [];
      var eras = blot.eras || [];
      if (!stamps.length && !lore.length && !eras.length) {
        stack.innerHTML = '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
        return;
      }
      var html = loreBlockHtml(lore);
      if (eras.length) {
        html += '<div class="catalog-block era-slips"><div class="catalog-head">worldline</div>';
        eras.forEach(function (h, hi) {
          html +=
            '<article class="era-slip era-slip-n' +
            ((hi % 3) + 1) +
            '">' +
            '<a class="era-slip-title" href="' +
            escapeHtml(h.href || "#") +
            '">' +
            escapeHtml(h.title || "") +
            "</a>" +
            (h.code
              ? '<p class="era-code">' + escapeHtml(h.code) + "</p>"
              : "") +
            (h.snippet
              ? '<p class="era-slip-body">' + escapeHtml(h.snippet) + "</p>"
              : "") +
            '<div class="era-slip-meta">' +
            (h.perspective
              ? '<span class="era-sit">' + escapeHtml(h.perspective) + "</span>"
              : "") +
            (h.when
              ? '<span class="era-sit-when">' + escapeHtml(h.when) + "</span>"
              : "") +
            (h.crate
              ? '<span class="era-slip-tools">' +
                '<button type="button" class="catalog-edit" data-edit-era="' +
                escapeHtml(h.crate) +
                '" title="edit">edit</button>' +
                '<button type="button" class="catalog-drop" data-drop-era="' +
                escapeHtml(h.crate) +
                '" title="drop">×</button></span>'
              : "") +
            "</div></article>";
        });
        html += "</div>";
      }
      if (!stamps.length) {
        stack.innerHTML = html || '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
        return;
      }
      html += '<div class="catalog-block tps-dates"><div class="catalog-head">filed</div>';
      stamps.forEach(function (s) {
        html +=
          '<div class="catalog-row tps-stamp">' +
          '<a class="catalog-label" href="' +
          escapeHtml(s.title_href || "#") +
          '">' +
          escapeHtml(s.title || "") +
          '</a><span class="catalog-tools">' +
          '<button type="button" class="catalog-drop" data-drop-stamp="' +
          escapeHtml(s.id || "") +
          '" title="drop">×</button>' +
          "</span>" +
          '<span class="catalog-value">' +
          '<a class="tps-when" href="' +
          escapeHtml(s.when_href || s.unix_href || "#") +
          '">' +
          escapeHtml(s.when || "") +
          "</a>" +
          (s.grain === "clock"
            ? '<code class="tps-unix">' +
              escapeHtml(String(s.at || "")) +
              "</code>"
            : "") +
          "</span></div>";
      });
      html += "</div>";
      var order = ["month", "day", "year", "hour"];
      var bins = "";
      order.forEach(function (kind) {
        var rows = slices[kind] || [];
        if (!rows.length) return;
        bins +=
          '<div class="tps-bin"><span class="tps-bin-label">' +
          escapeHtml(kind) +
          '</span><span class="tps-bucket">';
        rows.forEach(function (r) {
          bins +=
            '<a class="catalog-hit" href="' +
            escapeHtml(r.href || "#") +
            '">' +
            escapeHtml(r.value || "") +
            (r.n > 1 ? '<span class="tps-n">' + r.n + "</span>" : "") +
            "</a>";
        });
        bins += "</span></div>";
      });
      if (bins) {
        html +=
          '<div class="catalog-block tps-bins"><div class="catalog-head">routing</div>' +
          bins +
          "</div>";
      }
      stack.innerHTML = html;
    }

    function thoughtById(id) {
      var thoughts = blot.thoughts || [];
      for (var i = 0; i < thoughts.length; i++) {
        if (String(thoughts[i].id || "") === id) return thoughts[i];
      }
      return null;
    }

    function startAmend(id) {
      if (cfg.kind === "tags" || cfg.kind === "letter") return;
      if (!id || librarianOff()) return;
      var stack = $(ids.stack);
      if (!stack) return;
      var already = stack.querySelector(".librarian-thought.is-amending");
      if (already && already.getAttribute("data-id") !== id) {
        render();
      }
      var art = stack.querySelector('.librarian-thought[data-id="' + id.replace(/"/g, "") + '"]');
      if (!art || art.classList.contains("is-amending")) return;
      var t = thoughtById(id);
      if (!t) return;
      var body = art.querySelector(".librarian-body");
      if (!body) return;
      art.classList.add("is-amending");
      var ta = document.createElement("textarea");
      ta.className = "librarian-amend";
      ta.rows = 4;
      ta.value = t.leaf || "";
      body.replaceWith(ta);
      ta.focus();
      ta.setSelectionRange(ta.value.length, ta.value.length);
      ta.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          saveAmend(id, ta.value);
        } else if (e.key === "Escape") {
          e.preventDefault();
          render();
          setStatus("");
        }
      });
    }

    function saveAmend(id, leaf) {
      if (!id || librarianOff()) return;
      if (!String(leaf).trim()) {
        setStatus("Blank slip — nothing kept.", true);
        return;
      }
      api("PUT", cfg.api, { pocket: vaultPath(), id: id, leaf: leaf })
        .then(function (data) {
          blot = data || blot;
          render();
          setStatus("amended " + id);
        })
        .catch(function (err) {
          setStatus(err.message || "could not amend", true);
        });
    }

    var refreshTimer = 0;
    var loading = false;

    function holdRefresh() {
      /* never yank the page out from under someone mid-edit */
      var drawer = $(ids.drawer);
      if (!drawer) return true;
      if (drawer.querySelector(".is-amending")) return true;
      var modal = $(ids.modal);
      if (modal && !modal.hasAttribute("hidden")) return true;
      var leaf = $(ids.leaf);
      if (leaf && String(leaf.value || "").trim()) return true;
      var act = document.activeElement;
      if (act && drawer.contains(act)) {
        var tag = (act.tagName || "").toLowerCase();
        if (tag === "textarea" || tag === "input" || tag === "select") return true;
      }
      return false;
    }

    function refreshBlot(auto) {
      if (loading || librarianOff()) return;
      if (auto && holdRefresh()) return;
      loading = true;
      var p = vaultPath();
      api("GET", cfg.api + "?p=" + encodeURIComponent(p))
        .then(function (data) {
          blot = data || blot;
          render();
        })
        .catch(function (err) {
          setStatus(err.message || "could not refresh blotter", true);
        })
        .then(function () {
          loading = false;
        });
    }

    function stopRefresh() {
      if (refreshTimer) {
        window.clearInterval(refreshTimer);
        refreshTimer = 0;
      }
    }

    function loadBlot() {
      dismissChromeWindowsIfVaultMoved();
      if (librarianOff()) {
        blot =
          cfg.kind === "letter"
            ? { body: "", pocket: "", crate: "", route: "" }
            : cfg.kind === "catalog"
            ? { fields: [], lore: [], hunts: [], pocket: "", crate: "" }
            : cfg.kind === "tps"
            ? { stamps: [], slices: {}, eras: [], pocket: "", crate: "" }
            : cfg.kind === "cards"
            ? { cards: [], html: "", pocket: "", crate: "" }
            : { thoughts: [], lore: [], pocket: "", next: 1, crate: "" };
        if (!holdRefresh()) render();
        return Promise.resolve(blot);
      }
      var p = vaultPath();
      return api("GET", cfg.api + "?p=" + encodeURIComponent(p))
        .then(function (data) {
          blot = data || blot;
          if (!holdRefresh()) render();
          if (cfg.kind === "letter") {
            var el = $(ids.leaf);
            if (el) el.value = blot.body || ""; if (el && el._cm) el._cm.setValue(el.value);
            if (!pendingKeep) {
              letterEditMode = !(blot.body && String(blot.body).trim());
            }
            var pages = clayPages();
            if (letterWhich) {
              var ok = false;
              for (var i = 0; i < pages.length; i++) {
                if (pages[i].kind === letterWhich) ok = true;
              }
              if (!ok) letterWhich = "";
            }
            if (!letterWhich && pages.length) letterWhich = pages[0].kind || "";
            fillClay();
            restoreKeepCursor();
          }
          setStatus("");
        })
        .catch(function (err) {
          setStatus(err.message || "could not load blotter", true);
        });
    }

    function storeThought() {
      if (librarianOff()) return;
      var el = $(ids.leaf);
      var leaf = el ? el.value : "";
      if (cfg.kind === "letter") {
        if (letterFace === "crates") {
          setStatus("crates finder — nothing to Keep");
          return;
        }
        if (letterFace === "hosts") {
          var hostsHead = $("readmeHostsHeaders");
          var hostsLetter = $("readmeHostsLetter");
          if (hostsHead && hostsHead._cm) {
            try {
              hostsHead._cm.save();
            } catch (e) {}
          }
          if (hostsLetter && hostsLetter._cm) {
            try {
              hostsLetter._cm.save();
            } catch (e2) {}
          }
          var saveLetter = !!hostsEditMode;
          var letterPayload = saveLetter
            ? hostsLetter
              ? hostsLetter.value
              : ""
            : null;
          var isRoam = !!(hostsBlot && hostsBlot.kind === "roam");
          var headerText = hostsHead ? hostsHead.value : "";
          var hostKey = hostsSlug || (hostsBlot && hostsBlot.host) || "";
          var parsedRoam = isRoam ? parseHostHeaders(headerText) : null;
          // Roam: yaml connection fields + same shell frontmatter go doors read.
          var firstPut = isRoam
            ? api("PUT", "/api/hosts", {
                host: hostKey,
                what: "roam",
                source: (parsedRoam && parsedRoam.source) || "",
                title: (parsedRoam && parsedRoam.title) || "",
                environment: (parsedRoam && parsedRoam.environment) || "",
              }).then(function (data) {
                hostsBlot = data || hostsBlot;
                if (hostsBlot.host) hostsSlug = hostsBlot.host;
                return api("PUT", "/api/hosts", {
                  host: hostsSlug || hostKey,
                  what: "shell",
                  headers: headerText,
                  markdown:
                    hostsBlot && hostsBlot.shell_markdown != null
                      ? hostsBlot.shell_markdown
                      : undefined,
                });
              })
            : api("PUT", "/api/hosts", {
                host: hostKey,
                what: "shell",
                headers: headerText,
                markdown:
                  hostsBlot && hostsBlot.shell_markdown != null
                    ? hostsBlot.shell_markdown
                    : undefined,
              });
          firstPut
            .then(function (data) {
              hostsBlot = data || hostsBlot;
              if (hostsBlot.host) hostsSlug = hostsBlot.host;
              // Roam exterior folders often have no ~readme letter path.
              if (letterPayload === null || (isRoam && !(hostsBlot && hostsBlot.letter_path))) {
                hostsEditMode = false;
                fillHosts();
                syncHostsLetterView();
                setStatus(isRoam ? "roam frontmatter kept." : "hosts shell kept.");
                render();
                refreshDesk();
                return null;
              }
              return api("PUT", "/api/hosts", {
                host: hostsSlug || (hostsBlot && hostsBlot.host) || "",
                what: "letter",
                body: letterPayload,
              });
            })
            .then(function (data) {
              if (data == null) return;
              hostsBlot = data || hostsBlot;
              if (hostsBlot.host) hostsSlug = hostsBlot.host;
              hostsEditMode = false;
              fillHosts();
              syncHostsLetterView();
              setStatus("hosts kept.");
              render();
              refreshDesk();
            })
            .catch(function (err) {
              setStatus(err.message || "hosts failed", true);
            });
          return;
        }
        if (letterFace === "help") {
          var helpEl = $("readmeHelpLeaf");
          if (helpEl && helpEl._cm) {
            try {
              helpEl._cm.save();
            } catch (e) {}
          }
          api("PUT", "/api/help", {
            page: helpSlug || "_index",
            body: helpEl ? helpEl.value : "",
          })
            .then(function (data) {
              helpBlot = data || helpBlot;
              helpEditMode = false;
              fillHelp();
              syncHelpLetterView();
              setStatus("help kept.");
              render();
            })
            .catch(function (err) {
              setStatus(err.message || "help failed", true);
            });
          return;
        }
        if (letterFace === "coat") {
          var coatEl = $(ids.coat);
          if (coatEl && coatEl._cm) {
            try {
              coatEl._cm.save();
            } catch (e) {}
          }
          api("PUT", cfg.api, {
            pocket: vaultPath(),
            what: "coat",
            which: coatWhich(),
            css: coatEl ? coatEl.value : "",
          }).then(function (data) {
            blot = data || blot;
            setStatus("coat kept.");
            render();
            refreshDesk();
            try {
              cmPullFromTextareas();
            } catch (e) {}
            try {
              ensureCoatCm();
            } catch (e2) {}
          }).catch(function (err) {
            setStatus(err.message || "coat failed", true);
          });
          return;
        }
if (letterFace === "page") {
          var clayNow = currentClay();
          var whichNow = (clayNow && clayNow.kind) || letterWhich || "";
          if (isChipGuest() && whichNow === "note") {
            setStatus("guest chip - BIOS cannot Keep this paper", true);
            return;
          }
          var head = $(ids.headers);
          var md = $(ids.markdown);
          api("PUT", cfg.api, {
            pocket: vaultPath(),
            what: "page",
            which: whichNow,
            headers: head ? head.value : "",
            markdown: md ? md.value : "",
          })
            .then(function (data) {
              var caret = snapshotEditorCaret();
              blot = data || blot;
              render();
              fillClay();
              restoreEditorCaret(caret);
              setStatus("kept page");
              refreshDeskStay();
            })
            .catch(function (err) {
              setStatus(err.message || "could not keep page", true);
            });
          return;
        }
        /* room letter printout: Keep is not the way in — Edit is */
        if (!letterEditMode && blot.body && String(blot.body).trim()) {
          setStatus("on printout — Edit is next to Keep");
          return;
        }
        if (el && el._cm) {
          try {
            el._cm.save();
            leaf = el.value;
          } catch (e) {}
        }
        api("PUT", cfg.api, { pocket: vaultPath(), body: leaf })
          .then(function (data) {
            blot = data || blot;
            letterEditMode = false;
            render();
            setStatus("kept — back on printout");
            refreshDesk();
          })
          .catch(function (err) {
            setStatus(err.message || "could not keep", true);
          });
        return;
      }
      if (cfg.kind === "tags") {
        var fromEl = $(ids.leaf);
        var relEl = $(ids.rel);
        var toEl = $(ids.to);
        var frm = fromEl ? fromEl.value : "";
        var rel = relEl ? relEl.value : "";
        var to = toEl ? toEl.value : "";
        if (!String(frm).trim() && !String(rel).trim() && !String(to).trim()) {
          setStatus("Empty leaf — nothing stored.", true);
          return;
        }
        api("POST", cfg.api, {
          pocket: vaultPath(),
          from: frm,
          rel: rel,
          to: to,
        })
          .then(function (data) {
            blot = data || blot;
            if (fromEl) fromEl.value = "";
            if (relEl) relEl.value = "";
            if (toEl) toEl.value = "";
            if (fromEl) fromEl.focus();
            render();
            var issued = (data && data.issued) || [];
            setStatus(issued.length ? "issued " + issued.join(", ") : "already on the bag");
          })
          .catch(function (err) {
            setStatus(err.message || "could not store", true);
          });
        return;
      }
      if (!String(leaf).trim()) {
        setStatus("Empty leaf — nothing stored.", true);
        return;
      }
      api("POST", cfg.api, { pocket: vaultPath(), leaf: leaf })
        .then(function (data) {
          blot = data || blot;
          if (el) {
            el.value = "";
            el.focus();
          }
          render();
          setStatus("issued " + ((data.thoughts && data.thoughts[0] && data.thoughts[0].id) || ""));
        })
        .catch(function (err) {
          setStatus(err.message || "could not store", true);
        });
    }

    function dropThought(id, what) {
      if (!id || librarianOff()) return;
      api("DELETE", cfg.api, { pocket: vaultPath(), id: id, what: what || "" })
        .then(function (data) {
          blot = data || blot;
          render();
          setStatus("voided " + id);
        })
        .catch(function (err) {
          setStatus(err.message || "could not drop", true);
        });
    }

    function huntPadEls() {
      var drawer = $(ids.drawer);
      return {
        title: drawer && drawer.querySelector("[data-hunt-title]"),
        mind: drawer && drawer.querySelector("[data-hunt-mind]"),
        body: drawer && drawer.querySelector("[data-hunt-body]"),
        form: drawer && drawer.querySelector(".hunt-pad"),
        btn: drawer && drawer.querySelector("[data-add-hunt]"),
        toggle: drawer && drawer.querySelector("[data-hunt-open]"),
      };
    }

    function huntPadClear() {
      var els = huntPadEls();
      if (els.title) els.title.value = "";
      if (els.mind) els.mind.value = "";
      if (els.body) els.body.value = "";
      if (els.form) els.form.removeAttribute("data-hunt-crate");
      if (els.btn) els.btn.textContent = "keep";
    }

    function huntPadShow() {
      var els = huntPadEls();
      if (els.form) els.form.hidden = false;
      if (els.toggle) els.toggle.hidden = true;
    }

    function huntPadHide() {
      huntPadClear();
      var els = huntPadEls();
      if (els.form) els.form.hidden = true;
      if (els.toggle) els.toggle.hidden = false;
    }

    function huntByCrate(crate) {
      var want = crateIdOf(crate);
      if (!want) return null;
      var bags = [blot];
      if (blot && blot.shell) bags.push(blot.shell);
      for (var bi = 0; bi < bags.length; bi++) {
        var hunts = (bags[bi] && bags[bi].hunts) || [];
        for (var i = 0; i < hunts.length; i++) {
          if (crateIdOf(hunts[i].crate) === want) return hunts[i];
        }
      }
      return null;
    }

    function searchLoreDeck() {
      if (cfg.kind !== "cards") return;
      var drawer = $(ids.drawer);
      var qEl = drawer && drawer.querySelector("[data-lore-q]");
      var q = qEl ? String(qEl.value || "").trim() : "";
      if (!q) {
        deckHits = null;
        render();
        setStatus("");
        return;
      }
      api("GET", "/api/cards/search?q=" + encodeURIComponent(q))
        .then(function (data) {
          deckHits = data.hits || [];
          render();
          setStatus((deckHits.length || 0) + " in the deck");
        })
        .catch(function (err) {
          setStatus(err.message || "could not look", true);
        });
    }

    function blotterApi() {
      return cfg.id === "librarian" ? "/api/librarian/blot" : "/api/detective/hunt";
    }

    function blotterHouse() {
      return cfg.id === "detective" || cfg.id === "librarian";
    }

    function pinHunt(e) {
      if (e) e.preventDefault();
      if (!blotterHouse()) return;
      if (librarianOff()) {
        setStatus("off this page", true);
        return;
      }
      var els = huntPadEls();
      var title = els.title ? String(els.title.value || "").trim() : "";
      var body = els.body ? String(els.body.value || "").trim() : "";
      var mind = els.mind ? String(els.mind.value || "").trim() : "";
      var crate = els.form
        ? crateIdOf(els.form.getAttribute("data-hunt-crate"))
        : "";
      if (!title && !body) {
        setStatus("need a thought", true);
        return;
      }
      if (!title) {
        title = body.split("\n")[0].replace(/^#+\s*/, "").trim().slice(0, 80);
      }
      var payload = {
        pocket: vaultPath(),
        title: title,
        body: body,
        mindset: mind,
      };
      if (crate) payload.crate = crate;
      api(crate ? "PUT" : "POST", blotterApi(), payload)
        .then(function (data) {
          blot = data || blot;
          huntPadHide();
          render();
          var shown =
            (data && data.hunt && data.hunt.title) || title || "slip";
          setStatus((crate ? "saved " : "pinned ") + shown);
        })
        .catch(function (err) {
          setStatus(err.message || (crate ? "could not save" : "could not pin"), true);
        });
    }

    function editHunt(crate) {
      if (!blotterHouse()) return;
      var rec = huntByCrate(crate);
      if (!rec) {
        setStatus("no slip", true);
        return;
      }
      var els = huntPadEls();
      if (els.title) els.title.value = rec.title || "";
      if (els.mind) els.mind.value = rec.mindset || "";
      if (els.body) els.body.value = rec.body || rec.snippet || "";
      if (els.form) els.form.setAttribute("data-hunt-crate", rec.crate || crate);
      if (els.btn) els.btn.textContent = "save";
      huntPadShow();
      setStatus("editing " + (rec.title || "slip"));
      if (els.title) els.title.focus();
    }

    function dropHunt(crate) {
      crate = crateIdOf(crate);
      if (!crate) {
        setStatus("no slip", true);
        return;
      }
      if (librarianOff()) {
        setStatus("off this page", true);
        return;
      }
      api("DELETE", blotterApi(), { pocket: vaultPath(), crate: crate })
        .then(function (data) {
          blot = data || blot;
          var els = huntPadEls();
          if (els.form && crateIdOf(els.form.getAttribute("data-hunt-crate")) === crate) {
            huntPadClear();
          }
          render();
          setStatus("dropped slip");
        })
        .catch(function (err) {
          setStatus(err.message || "could not drop", true);
        });
    }

    function eraPadEls() {
      var drawer = $(ids.drawer);
      return {
        title: drawer && drawer.querySelector("[data-era-title]"),
        code: drawer && drawer.querySelector("[data-era-code]"),
        sit: drawer && drawer.querySelector("[data-era-sit]"),
        body: drawer && drawer.querySelector("[data-era-body]"),
        form: drawer && drawer.querySelector(".era-pad"),
        btn: drawer && drawer.querySelector("[data-add-era]"),
        toggle: drawer && drawer.querySelector("[data-era-open]"),
        names: drawer && drawer.querySelector("#era-names"),
      };
    }

    function paintEraNames() {
      var els = eraPadEls();
      if (!els.names) return;
      var names = blot.era_names || [];
      els.names.innerHTML = names
        .map(function (n) {
          var t = String((n && n.title) || "").trim();
          if (!t) return "";
          var c = String((n && n.code) || "").trim();
          return (
            "<option value=\"" +
            escapeHtml(t) +
            "\"" +
            (c ? " data-code=\"" + escapeHtml(c) + "\"" : "") +
            "></option>"
          );
        })
        .join("");
    }

    function eraKnownByTitle(title) {
      var want = String(title || "").trim().toLowerCase();
      if (!want) return null;
      var names = blot.era_names || [];
      for (var i = 0; i < names.length; i++) {
        if (String((names[i] && names[i].title) || "").trim().toLowerCase() === want) {
          return names[i];
        }
      }
      return null;
    }

    function preloadEraPerspective() {
      var els = eraPadEls();
      if (!els.title || !els.sit) return;
      if (els.form && els.form.getAttribute("data-era-crate")) return;
      var rec = eraKnownByTitle(els.title.value);
      var filled = els.form ? String(els.form.getAttribute("data-era-sit-filled") || "") : "";
      var cur = String(els.sit.value || "");
      if (rec) {
        var sit = String(rec.perspective || "");
        els.sit.value = sit;
        if (els.code && rec.code) els.code.value = rec.code;
        if (els.form) els.form.setAttribute("data-era-sit-filled", sit);
        return;
      }
      if (filled && cur === filled) els.sit.value = "";
      if (els.form) els.form.removeAttribute("data-era-sit-filled");
    }

    function eraPadClear() {
      var els = eraPadEls();
      if (els.title) els.title.value = "";
      if (els.code) els.code.value = "";
      if (els.sit) els.sit.value = "";
      if (els.body) els.body.value = "";
      if (els.form) {
        els.form.removeAttribute("data-era-crate");
        els.form.removeAttribute("data-era-sit-filled");
      }
      if (els.btn) els.btn.textContent = "keep";
    }

    function eraPadShow() {
      var els = eraPadEls();
      if (els.form) els.form.hidden = false;
      if (els.toggle) els.toggle.hidden = true;
    }

    function eraPadHide() {
      eraPadClear();
      var els = eraPadEls();
      if (els.form) els.form.hidden = true;
      if (els.toggle) els.toggle.hidden = false;
    }

    function eraByCrate(crate) {
      var want = crateIdOf(crate);
      if (!want) return null;
      var eras = (blot && blot.eras) || [];
      for (var i = 0; i < eras.length; i++) {
        if (crateIdOf(eras[i].crate) === want) return eras[i];
      }
      return null;
    }

    function pinEra(e) {
      if (e) e.preventDefault();
      if (cfg.kind !== "tps") return;
      if (librarianOff()) {
        setStatus("off this page", true);
        return;
      }
      var els = eraPadEls();
      var title = els.title ? String(els.title.value || "").trim() : "";
      var evcode = els.code ? String(els.code.value || "").trim() : "";
      var body = els.body ? String(els.body.value || "").trim() : "";
      var sit = els.sit ? String(els.sit.value || "").trim() : "";
      var crate = els.form
        ? crateIdOf(els.form.getAttribute("data-era-crate"))
        : "";
      if (!title && !body) {
        setStatus("need an event", true);
        return;
      }
      if (!title) {
        title = body.split("\n")[0].replace(/^#+\s*/, "").trim().slice(0, 80);
      }
      var payload = {
        pocket: vaultPath(),
        title: title,
        body: body,
        perspective: sit,
        code: evcode,
      };
      if (crate) payload.crate = crate;
      api(crate ? "PUT" : "POST", "/api/tps/event", payload)
        .then(function (data) {
          blot = data || blot;
          eraPadHide();
          render();
          var shown =
            (data && data.era && data.era.title) || title || "event";
          setStatus((crate ? "saved " : "tagged ") + shown);
        })
        .catch(function (err) {
          setStatus(err.message || (crate ? "could not save" : "could not tag"), true);
        });
    }

    function editEra(crate) {
      if (cfg.kind !== "tps") return;
      var rec = eraByCrate(crate);
      if (!rec) {
        setStatus("no slip", true);
        return;
      }
      var els = eraPadEls();
      if (els.title) els.title.value = rec.title || "";
      if (els.code) els.code.value = rec.code || "";
      if (els.sit) els.sit.value = rec.perspective || "";
      if (els.body) els.body.value = rec.body || rec.snippet || "";
      if (els.form) els.form.setAttribute("data-era-crate", rec.crate || crate);
      if (els.form) els.form.setAttribute("data-era-sit-filled", rec.perspective || "");
      if (els.btn) els.btn.textContent = "save";
      eraPadShow();
      setStatus("editing " + (rec.title || "event"));
      if (els.title) els.title.focus();
    }

    function dropEra(crate) {
      crate = crateIdOf(crate);
      if (!crate) {
        setStatus("no slip", true);
        return;
      }
      if (librarianOff()) {
        setStatus("off this page", true);
        return;
      }
      api("DELETE", "/api/tps/event", { pocket: vaultPath(), crate: crate })
        .then(function (data) {
          blot = data || blot;
          var els = eraPadEls();
          if (els.form && crateIdOf(els.form.getAttribute("data-era-crate")) === crate) {
            eraPadClear();
          }
          render();
          setStatus("untagged");
        })
        .catch(function (err) {
          setStatus(err.message || "could not drop", true);
        });
    }

    function copyCrate() {
      var c = blot.crate || "";
      if (cfg.kind === "catalog") {
        c = (typeof ontoCrate === "function" && ontoCrate()) || "";
      } else if (cfg.kind === "letter" && letterFace === "page") {
        var clayCopy = currentClay();
        c = (clayCopy && clayCopy.crate) || "";
      }
      if (!c) {
        setStatus("no crate on this bag", true);
        return;
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(c).then(
          function () {
            setStatus("copied " + c);
          },
          function () {
            setStatus("could not copy", true);
          }
        );
      } else {
        setStatus(c);
      }
    }

    function popOut() {
      if (SIDECAR) return;
      applyOpen(false);
      openRail(cfg, setStatus);
    }

    function issueCrate() {
      if (librarianOff()) return;
      api("POST", "/api/crate", { pocket: vaultPath() })
        .then(function (data) {
          blot.crate = (data && data.crate) || blot.crate;
          render();
          setStatus(data && data.minted ? "issued " + blot.crate : "already " + blot.crate);
        })
        .catch(function (err) {
          setStatus(err.message || "could not issue crate", true);
        });
    }

    function loadSuggest() {
      return api("GET", cfg.api + "/suggest")
        .then(function (data) {
          if (cfg.kind === "tps") {
            suggest = { titles: (data && data.titles) || [] };
          } else {
            suggest = data || suggest;
          }
          return suggest;
        })
        .catch(function () {
          return suggest;
        });
    }

    
    function hasLocalShell() {
      var pages = clayPages();
      for (var i = 0; i < pages.length; i++) {
        if (pages[i].kind === "shell" && pages[i].here !== false) return true;
      }
      return false;
    }

    function syncShellBtn() {
      var btn = document.querySelector("[data-new-shell]");
      if (!btn) return;
      // Show when this folder has no local _shell (inherited shell still counts as missing local).
      var show = cfg.kind === "letter" && !librarianOff() && !hasLocalShell();
      if (show) btn.removeAttribute("hidden");
      else btn.setAttribute("hidden", "");
    }

    function hasLocalLetter() {
      return !!(blot && blot.local_letter);
    }

    function syncLetterBtn() {
      var btn = document.querySelector("[data-new-letter]");
      if (!btn) return;
      var show = cfg.kind === "letter" && !librarianOff() && !hasLocalLetter();
      if (show) btn.removeAttribute("hidden");
      else btn.setAttribute("hidden", "");
    }

function openNewNoteModal() {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        modalMode = "note";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = "New";
        var folderPocket = String(vaultPath() || "")
          .replace(/\\/g, "/")
          .replace(/\/[^/]+\.md$/i, "");
        body.innerHTML =
          '<p class="librarian-onto">in ' +
          escapeHtml(ontoName(folderPocket) || "this folder") +
          "</p>" +
          "<label>name</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="the page title">';
        modal.removeAttribute("hidden");
        var first = body.querySelector('[data-field="title"]');
        if (first) {
          first.focus();
          first.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
              e.preventDefault();
              confirmModal();
            }
          });
        }
      });
    }

    
    
    function openNewRoamModal() {
      if (librarianOff()) return;
      modalMode = "roam";
      var titleEl = $(ids.modalTitle);
      var body = $(ids.modalBody);
      var modal = $(ids.modal);
      if (!titleEl || !body || !modal) return;
      titleEl.textContent = "Connect roam";
      body.innerHTML =
        '<p class="librarian-onto">point roam.* at a folder on disk. disconnect later does not delete it.</p>' +
        "<label>roam name</label>" +
        '<input data-field="slug" class="librarian-leaf tagbay-input" type="text" placeholder="drop">' +
        "<label>source folder</label>" +
        '<input data-field="source" class="librarian-leaf tagbay-input" type="text" placeholder="C:\\Users\\you\\Desktop\\library">' +
        "<label>title (optional)</label>" +
        '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="display name">' +
        "<label>environment (optional coat)</label>" +
        '<input data-field="environment" class="librarian-leaf tagbay-input" type="text" placeholder="portico">';
      modal.removeAttribute("hidden");
      var first = body.querySelector('[data-field="slug"]');
      if (first) {
        first.focus();
        first.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            confirmModal();
          }
        });
      }
    }

    function openNewHostModal() {
      if (librarianOff()) return;
      modalMode = "host";
      var titleEl = $(ids.modalTitle);
      var body = $(ids.modalBody);
      var modal = $(ids.modal);
      if (!titleEl || !body || !modal) return;
      titleEl.textContent = "New host";
      body.innerHTML =
        '<p class="librarian-onto">mint go.* under ~hosts</p>' +
        "<label>go name</label>" +
        '<input data-field="slug" class="librarian-leaf tagbay-input" type="text" placeholder="mausoleum">' +
        "<label>title (optional)</label>" +
        '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="display name">' +
        templateSelectHtml("stack");
      modal.removeAttribute("hidden");
      var first = body.querySelector('[data-field="slug"]');
      if (first) {
        first.focus();
        first.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            confirmModal();
          }
        });
      }
    }


    function currentHallPath() {
      var p = String(vaultPath() || "")
        .replace(/\\/g, "/")
        .replace(/\/+/g, "/")
        .replace(/\/$/, "");
      if (/\.md$/i.test(p) || /\.chip$/i.test(p) || /\.canvas$/i.test(p)) {
        p = p.replace(/\/[^/]+$/, "");
      }
      return p;
    }

    function currentHallName() {
      return ontoName(currentHallPath()) || "";
    }

    function canRenameCurrentHall() {
      var p = currentHallPath();
      if (!p || p === "/" || p === "" || p === ".") return false;
      var parts = p.split("/").filter(Boolean);
      // need at least one hall under the host vault
      if (!parts.length) return false;
      var leaf = parts[parts.length - 1];
      if (!leaf || leaf.charAt(0) === "." || leaf.charAt(0) === "~") return false;
      return true;
    }


    function biosPlusForcedOpen() {
      try {
        return window.localStorage.getItem("pocketgo.bios.plus") === "open";
      } catch (e) {
        return false;
      }
    }

    function setBiosPlusForcedOpen(on) {
      try {
        if (on) window.localStorage.setItem("pocketgo.bios.plus", "open");
        else window.localStorage.removeItem("pocketgo.bios.plus");
      } catch (e) {}
    }

    function syncBiosPlusBar() {
      bindBiosPlusBar();
      var group = document.querySelector("[data-bios-plus]");
      if (!group) return;
      var toggle = group.querySelector("[data-bios-plus-toggle]");
      var tray = group.querySelector(".bios-plus-tray");
      var bar = group.closest(".bios-actions");
      if (!toggle || !tray) return;
      var acts = tray.querySelectorAll("button.librarian-store");
      var visible = 0;
      for (var i = 0; i < acts.length; i++) {
        if (!acts[i].hasAttribute("hidden")) visible++;
      }
      var crowded = visible > 3;
      if (!crowded && bar) {
        /* width overflow of the whole BIOS action row */
        crowded = bar.scrollWidth > bar.clientWidth + 2;
      }
      var forced = biosPlusForcedOpen();
      if (crowded) {
        toggle.removeAttribute("hidden");
        if (forced) {
          group.classList.remove("is-plus-collapsed");
          group.classList.add("is-plus-open");
          toggle.textContent = "−";
          toggle.setAttribute("aria-expanded", "true");
          toggle.title = "collapse file actions";
        } else {
          group.classList.add("is-plus-collapsed");
          group.classList.remove("is-plus-open");
          toggle.textContent = "+";
          toggle.setAttribute("aria-expanded", "false");
          toggle.title = "more file actions (" + visible + ")";
        }
      } else {
        toggle.setAttribute("hidden", "");
        group.classList.remove("is-plus-collapsed");
        group.classList.remove("is-plus-open");
        setBiosPlusForcedOpen(false);
      }
    }

    function bindBiosPlusBar() {
      var root = document;
      if (root._biosPlusBound) return;
      root._biosPlusBound = true;
      document.addEventListener("click", function (e) {
        var t = e.target && e.target.closest ? e.target.closest("[data-bios-plus-toggle]") : null;
        if (!t) return;
        e.preventDefault();
        var group = t.closest("[data-bios-plus]");
        if (!group) return;
        var open = !group.classList.contains("is-plus-open");
        setBiosPlusForcedOpen(open);
        syncBiosPlusBar();
      });
    }

    function syncRenameFolderBtn() {
      var btn = document.querySelector("[data-rename-folder]");
      if (!btn) return;
      if (librarianOff() || !canRenameCurrentHall()) {
        btn.setAttribute("hidden", "");
        return;
      }
      btn.removeAttribute("hidden");
    }

    function openRenameFolderModal() {
      withFreshVault(function () {
        if (librarianOff()) return;
        if (!canRenameCurrentHall()) {
          setStatus("stand inside a hall to rename it", true);
          return;
        }
        modalMode = "folder-rename";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        var hall = currentHallName();
        titleEl.textContent = "Rename folder";
        body.innerHTML =
          '<p class="librarian-onto">hall ' +
          escapeHtml(hall) +
          "</p>" +
          "<label>new folder name</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="hall / wing name" value="' +
          escapeHtml(hall) +
          '">';
        modal.removeAttribute("hidden");
        var first = body.querySelector('[data-field="title"]');
        if (first) {
          first.focus();
          first.select();
          first.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
              e.preventDefault();
              confirmModal();
            }
          });
        }
      });
    }

function openNewFolderModal() {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        modalMode = "folder";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = "New folder";
        var folderPocket = String(vaultPath() || "")
          .replace(/\\/g, "/")
          .replace(/\/[^/]+\.md$/i, "");
        body.innerHTML =
          '<p class="librarian-onto">in ' +
          escapeHtml(ontoName(folderPocket) || "this folder") +
          "</p>" +
          "<label>folder name</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="hall / wing / drawer">';
        modal.removeAttribute("hidden");
        var first = body.querySelector('[data-field="title"]');
        if (first) {
          first.focus();
          first.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
              e.preventDefault();
              confirmModal();
            }
          });
        }
      });
    }

        function openRenameNoteModal() {
      withFreshVault(function () {
        if (librarianOff()) return;
        if (cfg.kind !== "letter") return;
        var clay = currentClay();
        if (!clay || !clay.file) {
          setStatus("open a page to rename", true);
          return;
        }
        modalMode = "rename";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = "Rename";
        var stem = String(clay.file || "").replace(/\.md$/i, "");
        body.innerHTML =
          '<p class="librarian-onto">file ' +
          escapeHtml(clay.file || "") +
          "</p>" +
          "<label>new name</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="filename / title">';
        modal.removeAttribute("hidden");
        var first = body.querySelector('[data-field="title"]');
        if (first) {
          first.value = stem;
          first.focus();
          first.select();
          first.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
              e.preventDefault();
              confirmModal();
            }
          });
        }
      });
    }

function goHref(href) {
      href = String(href || "").trim();
      if (!href) return;
      // Sidecar/sheet must nudge the pocket desk. sendDeck lives inside bootHere
      // and is out of scope here — calling it threw and skipped navigation.
      if (SIDECAR || htmlRoot().hasAttribute("data-sheet")) {
        nudgeDesk(href);
        return;
      }
      window.location.assign(href);
    }


    function openNewLetterModal() {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        if (hasLocalLetter()) {
          setStatus("this room already has a letter", true);
          return;
        }
        modalMode = "letter";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = "New room letter";
        var folderPocket = String(vaultPath() || "")
          .replace(/\\/g, "/")
          .replace(/\/[^/]+\.md$/i, "");
        var leaf = (folderPocket || "").replace(/^.*\//, "") || "this room";
        body.innerHTML =
          '<p class="librarian-onto">~readme letter for ' +
          escapeHtml(ontoName(folderPocket) || leaf) +
          " — host letter stays put</p>" +
          "<label>title</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="room title" value="' +
          escapeHtml(leaf) +
          '">';
        modal.removeAttribute("hidden");
        var first = body.querySelector('[data-field="title"]');
        if (first) {
          try {
            first.focus();
            first.select();
          } catch (e) {}
        }
      });
    }

    function openNewShellModal() {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        if (hasLocalShell()) {
          setStatus("this folder already has a shell", true);
          return;
        }
        modalMode = "shell";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = "New subshell";
        var folderPocket = String(vaultPath() || "")
          .replace(/\\/g, "/")
          .replace(/\/[^/]+\.md$/i, "");
        var leaf = (folderPocket || "").replace(/^.*\//, "") || "this folder";
        body.innerHTML =
          '<p class="librarian-onto">_shell.md for ' +
          escapeHtml(ontoName(folderPocket) || leaf) +
          " — nests in the parent paper hole</p>" +
          "<label>title</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" type="text" placeholder="room title" value="' +
          escapeHtml(leaf) +
          '">';
        modal.removeAttribute("hidden");
        var first = body.querySelector('[data-field="title"]');
        if (first) {
          try {
            first.focus();
            first.select();
          } catch (e) {}
        }
      });
    }


    
    function cabinetModalOpen(modes) {
      var modal = $(ids.modal);
      if (!modal || modal.hasAttribute("hidden")) return false;
      if (!modes) return true;
      if (typeof modes === "string") modes = [modes];
      for (var i = 0; i < modes.length; i++) {
        if (modalMode === modes[i]) return true;
      }
      return false;
    }

    function toggleOrOpenCabinet(modes, openFn) {
      if (cabinetModalOpen(modes)) {
        closeModal();
        hideLibrarianSuggest();
        setStatus("");
        return;
      }
      openFn();
    }

function revealCabinetModal(focusEl) {
      var modal = $(ids.modal);
      if (!modal) return;
      var root = $(ids.drawer) || $(cfg.id) || (modal.closest && modal.closest(".librarian"));
      var stack = root ? root.querySelector(".librarian-stack") : null;
      var keep = stack ? stack.scrollTop : 0;
      var pageKeep = 0;
      try {
        pageKeep = window.scrollY || document.documentElement.scrollTop || 0;
      } catch (e) {}
      modal.removeAttribute("hidden");
      if (focusEl && focusEl.focus) {
        try {
          focusEl.focus({ preventScroll: true });
        } catch (e2) {
          try {
            focusEl.focus();
          } catch (e3) {}
        }
      }
      if (stack) stack.scrollTop = keep;
      try {
        window.scrollTo(0, pageKeep);
      } catch (e4) {}
      requestAnimationFrame(function () {
        if (stack) stack.scrollTop = keep;
        try {
          window.scrollTo(0, pageKeep);
        } catch (e5) {}
      });
    }

    function closeModal() {
      modalMode = "";
      editIndex = -1;
      editLoreCrate = "";
      try {
        hideLibrarianSuggest();
      } catch (e) {}
      var modal = $(ids.modal);
      if (modal) modal.setAttribute("hidden", "");
    }

    function datalistFor(kind) {
      /* native datalist is unthemeable — IO uses librarianSuggest */
      return "";
    }

    function suggestWordsFor(kind) {
      kind = String(kind || "").trim() || "input";
      var words = suggest[kind] || suggest.class || suggest.input || [];
      if (!Array.isArray(words)) words = [];
      return words;
    }

    function hideLibrarianSuggest() {
      var menu = document.getElementById(cfg.id + "SuggestMenu");
      if (menu) menu.hidden = true;
    }

    function ensureLibrarianSuggestMenu(host) {
      var id = cfg.id + "SuggestMenu";
      var menu = document.getElementById(id);
      host = host || null;
      if (menu) {
        if (host && menu.parentElement !== host) host.appendChild(menu);
        return menu;
      }
      menu = document.createElement("div");
      menu.id = id;
      menu.className = "librarian-suggest";
      menu.hidden = true;
      var parent =
        host ||
        document.querySelector(".librarian-modal-card") ||
        $(ids.drawer) ||
        $(cfg.id);
      if (!parent) return null;
      parent.appendChild(menu);
      return menu;
    }

    function showLibrarianSuggest(input, kind) {
      if (!input) return;
      var card =
        (input.closest && input.closest(".librarian-modal-card")) || null;
      if (card) {
        card.classList.add("has-suggest-host");
        if (window.getComputedStyle(card).position === "static") {
          card.style.position = "relative";
        }
      }
      var menu = ensureLibrarianSuggestMenu(card);
      if (!menu) return;
      var q = String(input.value || "").trim().toLowerCase();
      var words = suggestWordsFor(kind);
      var hits = [];
      for (var i = 0; i < words.length; i++) {
        var w = String(words[i] || "");
        if (!w) continue;
        if (!q || w.toLowerCase().indexOf(q) >= 0) hits.push(w);
        if (hits.length >= 12) break;
      }
      if (!hits.length) {
        menu.hidden = true;
        return;
      }
      var html = "";
      hits.forEach(function (w, idx) {
        html +=
          '<button type="button" class="librarian-suggest-item' +
          (idx === 0 ? " is-on" : "") +
          '" data-suggest-pick="' +
          escapeHtml(w) +
          '">' +
          escapeHtml(w) +
          "</button>";
      });
      menu.innerHTML = html;
      menu.hidden = false;
      menu.setAttribute("data-for-field", input.getAttribute("data-field") || "");
      var host = menu.parentElement;
      if (!host) return;
      var ir = input.getBoundingClientRect();
      var hr = host.getBoundingClientRect();
      var top = ir.bottom - hr.top + host.scrollTop + 2;
      var left = ir.left - hr.left + host.scrollLeft;
      menu.style.left = Math.max(0, left) + "px";
      menu.style.top = Math.max(0, top) + "px";
      menu.style.width = Math.max(120, ir.width) + "px";
      menu.style.right = "auto";
    }

    function bindLibrarianSuggest(root) {
      if (!root || root._suggestBound) return;
      root._suggestBound = true;
      root.addEventListener("focusin", function (e) {
        var input = e.target;
        if (!input || !input.getAttribute) return;
        var kind = input.getAttribute("data-suggest");
        if (!kind) return;
        showLibrarianSuggest(input, kind);
      });
      root.addEventListener("input", function (e) {
        var input = e.target;
        if (!input || !input.getAttribute) return;
        var kind = input.getAttribute("data-suggest");
        if (!kind) return;
        showLibrarianSuggest(input, kind);
      });
      root.addEventListener("focusout", function () {
        window.setTimeout(function () {
          var menu = document.getElementById(cfg.id + "SuggestMenu");
          if (!menu) return;
          var active = document.activeElement;
          if (
            active &&
            (menu.contains(active) ||
              (active.getAttribute && active.getAttribute("data-suggest")))
          )
            return;
          menu.hidden = true;
        }, 120);
      });
      root.addEventListener("keydown", function (e) {
        var input = e.target;
        if (!input || !input.getAttribute || !input.getAttribute("data-suggest"))
          return;
        var menu = document.getElementById(cfg.id + "SuggestMenu");
        if (!menu || menu.hidden) return;
        var items = menu.querySelectorAll(".librarian-suggest-item");
        if (!items.length) return;
        var on = menu.querySelector(".librarian-suggest-item.is-on");
        var idx = 0;
        for (var i = 0; i < items.length; i++) {
          if (items[i] === on) idx = i;
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          if (on) on.classList.remove("is-on");
          idx = (idx + 1) % items.length;
          items[idx].classList.add("is-on");
        } else if (e.key === "ArrowUp") {
          e.preventDefault();
          if (on) on.classList.remove("is-on");
          idx = (idx - 1 + items.length) % items.length;
          items[idx].classList.add("is-on");
        } else if (e.key === "Enter" || e.key === "Tab") {
          var pick = menu.querySelector(".librarian-suggest-item.is-on") || items[0];
          if (!pick) return;
          if (e.key === "Enter") e.preventDefault();
          input.value = pick.getAttribute("data-suggest-pick") || pick.textContent || "";
          menu.hidden = true;
        } else if (e.key === "Escape") {
          menu.hidden = true;
        }
      });
      root.addEventListener("mousedown", function (e) {
        var btn =
          e.target && e.target.closest
            ? e.target.closest("[data-suggest-pick]")
            : null;
        if (!btn) return;
        e.preventDefault();
        var field =
          btn.parentElement && btn.parentElement.getAttribute("data-for-field");
        var modal = $(ids.modalBody);
        var input =
          (modal && field && modal.querySelector('[data-field="' + field + '"]')) ||
          null;
        if (!input) input = document.activeElement;
        if (input && input.tagName === "INPUT") {
          input.value = btn.getAttribute("data-suggest-pick") || "";
        }
        hideLibrarianSuggest();
      });
    }


    function valueControl(kind) {
      if (kind === "bool") {
        return '<label class="catalog-check"><input type="checkbox" data-field="value"> yes</label>';
      }
      if (kind === "textbox") {
        return '<textarea data-field="value" rows="4" class="librarian-leaf" placeholder="the value"></textarea>';
      }
      var ph = kind === "time" ? "unix or 2026-08-30 15:00" : "the value";
      return (
        '<input data-field="value" class="librarian-leaf tagbay-input" type="text" placeholder="' +
        ph +
        '">'
      );
    }

    function fieldByIndex(i, onto) {
      var bag = onto === "shell" && blot.shell ? blot.shell : blot;
      var fields = bag.fields || [];
      var n = Number(i);
      for (var k = 0; k < fields.length; k++) {
        if (Number(fields[k].i) === n) return fields[k];
      }
      return fields[n] || null;
    }

    function loreByCrateFrom(crate) {
      var want = String(crate || "");
      var bags = [blot];
      if (blot.shell) bags.push(blot.shell);
      for (var b = 0; b < bags.length; b++) {
        var lore = bags[b].lore || [];
        for (var i = 0; i < lore.length; i++) {
          if (String(lore[i].crate || "") === want) return lore[i];
        }
      }
      return null;
    }

    function fillMetaForm(body, field) {
      var kind = String((field && field.type) || "input");
      var typeSel = body.querySelector('[data-field="type"]');
      if (typeSel) typeSel.value = kind;
      var slot = body.querySelector("[data-value-slot]");
      if (slot) slot.innerHTML = valueControl(kind);
      var dl = body.querySelector("datalist");
      if (dl) {
        var html = "";
        (suggest[kind] || []).forEach(function (w) {
          html += "<option value=\"" + escapeHtml(w) + "\">";
        });
        dl.innerHTML = html;
      }
      var lab = body.querySelector('[data-field="label"]');
      if (lab) lab.value = (field && field.label) || "";
      var valEl = body.querySelector('[data-field="value"]');
      if (!valEl) return;
      if (kind === "bool") {
        valEl.checked = !!(field && (field.value === true || field.value === "true" || field.value === 1));
      } else if (field && field.value != null) {
        valEl.value = String(field.value);
      }
    }

    function openMetaModal(field) {
      if (librarianOff()) return;
      modalMode = field ? "meta-edit" : "meta";
      editIndex = field && field.i != null ? Number(field.i) : -1;
      var titleEl = $(ids.modalTitle);
      var body = $(ids.modalBody);
      var modal = $(ids.modal);
      if (!titleEl || !body || !modal) return;
      titleEl.textContent = field
        ? "Edit Meta Data"
        : "Add Meta Data";
      var kind = String((field && field.type) || "input");
      body.innerHTML =
        '<p class="librarian-onto">onto ' +
        escapeHtml(ontoLabel()) +
        "</p>" +
        '<label>type</label>' +
        '<select data-field="type" class="librarian-leaf tagbay-input">' +
        '<option value="time">time</option>' +
        '<option value="bool">bool</option>' +
        '<option value="input">input</option>' +
        '<option value="textbox">textbox</option>' +
        "</select>" +
        '<label>label</label>' +
        '<input data-field="label" class="librarian-leaf tagbay-input" data-suggest="' +
        escapeHtml(kind) +
        '" placeholder="' +
        escapeHtml(cfg.metaHint || "e.g. author") +
        '">' +
        '<label>value</label>' +
        '<div data-value-slot>' +
        valueControl(kind) +
        "</div>";
      fillMetaForm(body, field);
      var typeSel = body.querySelector('[data-field="type"]');
      if (typeSel && !typeSel._suggestTypeBound) {
        typeSel._suggestTypeBound = true;
        typeSel.addEventListener("change", function () {
          var lab = body.querySelector('[data-field="label"]');
          if (lab) lab.setAttribute("data-suggest", typeSel.value || "input");
          hideLibrarianSuggest();
        });
      }
      revealCabinetModal(body.querySelector("input, textarea, select"));
      setStatus(field ? "edit meta" : "add meta");
      loadSuggest().then(function () {
        if (modalMode !== "meta" && modalMode !== "meta-edit") return;
        var live = $(ids.modalBody);
        var lab = live && live.querySelector('[data-field="label"]');
        if (lab && document.activeElement === lab) {
          showLibrarianSuggest(lab, lab.getAttribute("data-suggest") || "input");
        }
      });
    }

    function dropField(i, onto) {
      if (i === "" || i == null || librarianOff()) return;
      api("DELETE", cfg.api, { pocket: vaultPath(), index: Number(i), onto: onto || catalogOnto })
        .then(function (data) {
          blot = data || blot;
          render();
          setStatus("dropped field");
        })
        .catch(function (err) {
          setStatus(err.message || "could not drop", true);
        });
    }

    function unixToLocal(ts) {
      var n = Number(ts);
      if (!n) return "";
      var d = new Date(n * 1000);
      function pad(x) {
        return (x < 10 ? "0" : "") + x;
      }
      return (
        d.getFullYear() +
        "-" +
        pad(d.getMonth() + 1) +
        "-" +
        pad(d.getDate()) +
        "T" +
        pad(d.getHours()) +
        ":" +
        pad(d.getMinutes())
      );
    }

    function stampTitles() {
      var fromFile = (suggest && suggest.titles) || [];
      var have = {};
      var out = [];
      fromFile.forEach(function (t) {
        var k = String(t || "").toLowerCase();
        if (!k || have[k]) return;
        have[k] = true;
        out.push(t);
      });
      return out;
    }

    function openStampModal() {
      if (librarianOff()) return;
      loadSuggest().then(function () {
        modalMode = "stamp";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = "Stamp a when";
        var opts = "";
        stampTitles().forEach(function (t) {
          opts += "<option value=\"" + escapeHtml(t) + "\">";
        });
        body.innerHTML =
          "<label>title</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" list="' +
          cfg.id +
          'Suggest" placeholder="imported on, last modified, …">' +
          '<datalist id="' +
          cfg.id +
          'Suggest">' +
          opts +
          "</datalist>" +
          "<label>when</label>" +
          '<input data-field="when" class="librarian-leaf tagbay-input" type="datetime-local">' +
          "<label>as known</label>" +
          '<input data-field="known" class="librarian-leaf tagbay-input" type="text" placeholder="1999 · March 1999 · 2001-02-24 · or unix">';
        modal.removeAttribute("hidden");
        var first = body.querySelector('[data-field="title"]');
        if (first) first.focus();
      });
    }

    function dropStampRow(id) {
      if (!id || librarianOff()) return;
      api("DELETE", cfg.api, { pocket: vaultPath(), id: id })
        .then(function (data) {
          blot = data || blot;
          render();
          setStatus("dropped date");
        })
        .catch(function (err) {
          setStatus(err.message || "could not drop", true);
        });
    }

    function dropLoreCard(crate, mouth, onto) {
      crate = String(crate || "").trim();
      if (!crate) {
        setStatus("no lore crate", true);
        return;
      }
      mouth = String(mouth || "").trim().toLowerCase();
      onto = onto || catalogOnto || "page";
      setStatus("dropping…");
      withFreshVault(function (pocket) {
        if (librarianOff()) return;
        api("POST", "/api/cards/lore/sync", {
          pocket: pocket,
          onto: onto,
          attach: [],
          detach: [{ crate: crate, mouth: mouth }],
        })
          .then(function (data) {
            return loadBlot().then(function () {
              return data;
            });
          })
          .then(function (data) {
            render();
            var n = data && data.detached_n;
            if (n === 0) {
              setStatus("nothing to drop (edge not on this bag?)", true);
            } else {
              setStatus(
                "dropped lore from " +
                  (onto === "shell" ? "the shell" : "this page")
              );
              try {
                refreshDesk();
              } catch (e) {}
            }
          })
          .catch(function (err) {
            setStatus((err && err.message) || "drop failed", true);
          });
      });
    }


    function openLoreModal(card) {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        var editing = !!(card && card.crate);
        modalMode = editing ? "lore-edit" : "lore";
        editLoreCrate = editing ? String(card.crate || "") : "";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = editing ? "Edit Lore" : "Add Lore";
        body.innerHTML =
          '<p class="librarian-onto">' +
          (editing ? "this card" : "onto " + escapeHtml(ontoLabel())) +
          "</p>" +
          "<label>class</label>" +
          '<input data-field="class" class="librarian-leaf tagbay-input" data-suggest="class" placeholder="' +
          escapeHtml(cfg.loreClassHint || "e.g. recovered") +
          '">' +
          '<label>maker <em>(corner — blank = ' +
          escapeHtml(cfg.defaultMaker || "this cabinet") +
          ")</em></label>" +
          '<input data-field="maker" class="librarian-leaf tagbay-input" placeholder="' +
          escapeHtml(cfg.defaultMaker || "Teehee, Agent K, SAM.exe…") +
          '">' +
          "<label>lore title</label>" +
          '<input data-field="title" class="librarian-leaf tagbay-input" placeholder="names the file">' +
          "<label>lore line</label>" +
          '<textarea data-field="line" class="librarian-leaf" rows="3" maxlength="255" placeholder="255 characters"></textarea>' +
          "<label>time</label>" +
          '<input data-field="time" class="librarian-leaf tagbay-input" placeholder="' +
          (editing ? "blank = keep" : "blank = now") +
          '">';
        if (editing) {
          var klassEl = body.querySelector('[data-field="class"]');
          var makerEl = body.querySelector('[data-field="maker"]');
          var titleField = body.querySelector('[data-field="title"]');
          var lineEl = body.querySelector('[data-field="line"]');
          var timeEl = body.querySelector('[data-field="time"]');
          if (klassEl) klassEl.value = card.class || "";
          if (makerEl) makerEl.value = card.maker || card.house || "";
          if (titleField) titleField.value = card.title || "";
          if (lineEl) lineEl.value = card.line || "";
          if (timeEl && card.tps) timeEl.value = String(card.tps);
        }
        var first = body.querySelector(
          editing ? '[data-field="title"]' : '[data-field="class"]'
        );
        revealCabinetModal(first);
        setStatus(editing ? "edit lore" : "add lore");
        /* suggest fills datalist in background — never block the form */
        loadSuggest().then(function () {
          if (modalMode !== "lore" && modalMode !== "lore-edit") return;
          var liveBody = $(ids.modalBody);
          var klassInput = liveBody && liveBody.querySelector('[data-field="class"]');
          if (klassInput && document.activeElement === klassInput) {
            showLibrarianSuggest(klassInput, "class");
          }
        });
      });
    }

function openAttachModal() {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        var loreUrl =
          cfg.kind === "cards" ? "/api/cards/lore" : cfg.api + "/lore";
        var deckPick = cfg.kind === "cards";
        modalMode = "attach";
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = deckPick ? "Deck · Attach" : "Attach Lore";
        var okBtn = modal.querySelector("[data-modal-ok]");
        if (okBtn) {
          okBtn.textContent = deckPick ? "Apply" : "Confirm";
          okBtn.disabled = true;
        }
        body.innerHTML =
          '<p class="librarian-onto">onto ' +
          escapeHtml(ontoLabel()) +
          (deckPick ? " · from any cabinet" : "") +
          "</p>" +
          '<p class="lore-attach-loading">' +
          (deckPick ? "opening filters" : "loading cards") +
          "</p>";
        modal.removeAttribute("hidden");
        setStatus(deckPick ? "opening attach…" : "loading lore…");

        function uniqSorted(vals) {
          var seen = {};
          var out = [];
          vals.forEach(function (v) {
            v = String(v || "").trim();
            if (!v) return;
            var key = v.toLowerCase();
            if (seen[key]) return;
            seen[key] = true;
            out.push(v);
          });
          out.sort(function (a, b) {
            return a.toLowerCase().localeCompare(b.toLowerCase());
          });
          return out;
        }

        function optionsHtml(values, allLabel) {
          var html = '<option value="">' + escapeHtml(allLabel) + "</option>";
          values.forEach(function (v) {
            html +=
              '<option value="' +
              escapeHtml(v) +
              '">' +
              escapeHtml(v) +
              "</option>";
          });
          return html;
        }

        function cardHay(card) {
          return [
            card.title,
            card.file,
            card.class,
            card.maker,
            card.house,
            card.mouth,
            card.line,
            card.tps,
            (card.edges || []).join(" "),
          ]
            .join(" ")
            .toLowerCase();
        }

        function ensureMeta() {
          if (deckPick && attachMetaCache && attachMetaCache.cards) {
            return Promise.resolve(attachMetaCache);
          }
          var url = deckPick ? "/api/cards/lore" : loreUrl;
          return api("GET", cfg.api + "?p=" + encodeURIComponent(vaultPath()))
            .then(function (blotData) {
              blot = blotData || blot;
              return api("GET", url);
            })
            .then(function (data) {
              if (deckPick) attachMetaCache = data || { cards: [] };
              return data || { cards: [] };
            });
        }

        function fetchFacesFor(cards) {
          var need = [];
          cards.forEach(function (card) {
            var crate = String(card.crate || "").trim();
            if (!crate) return;
            if (attachFaceCache[crate] || String(card.html || "").trim()) return;
            need.push({
              crate: crate,
              mouth: String(card.mouth || "").trim(),
            });
          });
          if (!need.length) return Promise.resolve();
          return api("POST", "/api/cards/lore/faces", { crates: need }).then(
            function (data) {
              var faces = (data && data.faces) || {};
              Object.keys(faces).forEach(function (crate) {
                if (faces[crate]) attachFaceCache[crate] = faces[crate];
              });
              ((data && data.cards) || []).forEach(function (card) {
                var c = String((card && card.crate) || "").trim();
                if (c && card.html) attachFaceCache[c] = card.html;
              });
            }
          );
        }

        ensureMeta()
          .then(function (data) {
            if (okBtn) okBtn.disabled = false;
            titleEl = $(ids.modalTitle);
            body = $(ids.modalBody);
            modal = $(ids.modal);
            if (!titleEl || !body || !modal) return;
            var here = ontoCrate();
            var allCards = (data && data.cards) || [];
            var pickState = {};
            allCards.forEach(function (card) {
              var crate = String(card.crate || "").trim();
              if (!crate) return;
              var edges = card.edges || [];
              var on = false;
              if (here) {
                for (var i = 0; i < edges.length; i++) {
                  if (edges[i] === here) {
                    on = true;
                    break;
                  }
                }
              }
              pickState[crate] = {
                on: on,
                was: on,
                mouth: String(card.mouth || "").trim(),
              };
              if (card.html) attachFaceCache[crate] = card.html;
            });

            var faceWait = null;

            function filtersActive() {
              if (!deckPick) return true;
              var qEl = body.querySelector("[data-attach-q]");
              var houseEl = body.querySelector("[data-attach-house]");
              var makerEl = body.querySelector("[data-attach-maker]");
              var classEl = body.querySelector("[data-attach-class]");
              var q = qEl ? String(qEl.value || "").trim() : "";
              var houseWant = houseEl ? String(houseEl.value || "").trim() : "";
              var makerWant = makerEl ? String(makerEl.value || "").trim() : "";
              var classWant = classEl ? String(classEl.value || "").trim() : "";
              return !!(q || houseWant || makerWant || classWant);
            }

            function filteredCards() {
              var qEl = body.querySelector("[data-attach-q]");
              var houseEl = body.querySelector("[data-attach-house]");
              var makerEl = body.querySelector("[data-attach-maker]");
              var classEl = body.querySelector("[data-attach-class]");
              var q = qEl ? String(qEl.value || "").trim().toLowerCase() : "";
              var houseWant = houseEl
                ? String(houseEl.value || "").trim().toLowerCase()
                : "";
              var makerWant = makerEl
                ? String(makerEl.value || "").trim().toLowerCase()
                : "";
              var classWant = classEl
                ? String(classEl.value || "").trim().toLowerCase()
                : "";
              var words = q ? q.split(/\s+/).filter(Boolean) : [];
              var shown = [];
              allCards.forEach(function (card) {
                var house = String(card.house || card.mouth || "").trim();
                var maker = String(card.maker || "").trim();
                var klass = String(card.class || "").trim();
                if (houseWant && house.toLowerCase() !== houseWant) return;
                if (makerWant && maker.toLowerCase() !== makerWant) return;
                if (classWant && klass.toLowerCase() !== classWant) return;
                if (words.length) {
                  var hay = cardHay(card);
                  for (var w = 0; w < words.length; w++) {
                    if (hay.indexOf(words[w]) < 0) return;
                  }
                }
                shown.push(card);
              });
              return shown;
            }

            function paintList() {
              var list = body.querySelector("[data-attach-list]");
              var countEl = body.querySelector("[data-attach-count]");
              if (!list) return;

              if (deckPick && !filtersActive()) {
                if (countEl) {
                  countEl.textContent =
                    allCards.length + " in cabinets · set a filter to load";
                }
                list.innerHTML =
                  '<p class="librarian-empty">Pick a house, maker, class, or search — cards load only after that, so Attach stays light.</p>';
                return;
              }

              var shown = filteredCards();
              var selectedN = 0;
              Object.keys(pickState).forEach(function (k) {
                if (pickState[k].on) selectedN += 1;
              });
              if (countEl) {
                countEl.textContent =
                  shown.length +
                  " shown · " +
                  selectedN +
                  " on page";
              }

              var missing = [];
              shown.forEach(function (card) {
                var crate = String(card.crate || "").trim();
                if (!crate) return;
                if (!attachFaceCache[crate] && !String(card.html || "").trim()) {
                  missing.push(card);
                }
              });
              if (deckPick && missing.length) {
                list.innerHTML =
                  '<p class="lore-attach-loading">loading ' +
                  missing.length +
                  " face" +
                  (missing.length === 1 ? "" : "s") +
                  "</p>";
                if (!faceWait) {
                  faceWait = fetchFacesFor(missing)
                    .catch(function () {})
                    .then(function () {
                      faceWait = null;
                      paintList();
                    });
                }
                return;
              }

              if (!shown.length) {
                list.innerHTML =
                  '<p class="librarian-empty">nothing matches — loosen search or filters</p>';
                return;
              }

              if (deckPick) {
                var html = '<div class="card-shelf lore-attach-shelf">';
                shown.forEach(function (card) {
                  var crate = String(card.crate || "").trim();
                  var st = pickState[crate] || { on: false, mouth: "" };
                  var mouth = st.mouth || String(card.mouth || "").trim();
                  var face =
                    attachFaceCache[crate] ||
                    String(card.html || "").trim();
                  if (!face) {
                    var strip = String(card.strip || "").trim();
                    face =
                      '<article class="card-shelf-item lore-attach-thumb"' +
                      (crate
                        ? ' data-crate="' + escapeHtml(crate) + '"'
                        : "") +
                      (strip
                        ? ' style="--card-strip:' + escapeHtml(strip) + '"'
                        : "") +
                      ">" +
                      '<div class="lore-attach-thumb-rail"' +
                      (strip
                        ? ' style="background:' + escapeHtml(strip) + '"'
                        : "") +
                      "></div>" +
                      '<div class="lore-attach-thumb-body">' +
                      "<strong>" +
                      escapeHtml(card.title || card.file || "lore") +
                      "</strong></div></article>";
                  }
                  html +=
                    '<label class="lore-attach-face' +
                    (st.on ? " is-on" : "") +
                    (st.was ? " was-on" : "") +
                    '">' +
                    '<input type="checkbox" data-field="card" value="' +
                    escapeHtml(crate) +
                    '"' +
                    (mouth
                      ? ' data-mouth="' + escapeHtml(mouth) + '"'
                      : "") +
                    (st.on ? " checked" : "") +
                    ">" +
                    '<span class="lore-attach-face-body">' +
                    face +
                    "</span></label>";
                });
                html += "</div>";
                list.innerHTML = html;
                enhanceCardShelf(list);
                return;
              }

              var html2 = "";
              shown.forEach(function (card) {
                var crate = String(card.crate || "").trim();
                var st = pickState[crate] || { on: false, mouth: "" };
                var mouth = st.mouth || String(card.mouth || "").trim();
                var metaBits = [];
                if (card.class) metaBits.push(card.class);
                if (card.maker) metaBits.push(card.maker);
                else if (card.house || mouth) metaBits.push(card.house || mouth);
                if (st.was) metaBits.push("on");
                var houseRaw = String(card.house || card.maker || mouth || "").toLowerCase();
                var strip = "#38b433";
                if (houseRaw.indexOf("detective") >= 0 || houseRaw.indexOf("agent") >= 0) strip = "#c4202a";
                else if (houseRaw.indexOf("charlie") >= 0) strip = "#c9892d";
                else if (houseRaw.indexOf("tps") >= 0) strip = "#c42820";
                else if (houseRaw.indexOf("librarian") >= 0 || houseRaw.indexOf("io") >= 0)
                  strip = "#38b433";
                var preview = String(card.line || "").trim();
                if (preview.length > 96) preview = preview.slice(0, 94) + "…";
                html2 +=
                  '<label class="lore-pick lore-chip' +
                  (st.on ? " is-checked" : "") +
                  (st.was ? " was-on" : "") +
                  '" style="--chip-strip:' +
                  strip +
                  '">' +
                  '<input type="checkbox" data-field="card" value="' +
                  escapeHtml(crate) +
                  '"' +
                  (mouth
                    ? ' data-mouth="' + escapeHtml(mouth) + '"'
                    : "") +
                  (st.on ? " checked" : "") +
                  ">" +
                  '<span class="lore-pick-body">' +
                  '<span class="lore-chip-top">' +
                  "<strong>" +
                  escapeHtml(card.title || card.file || "lore") +
                  "</strong>" +
                  (metaBits.length
                    ? '<span class="lore-pick-meta">' +
                      escapeHtml(metaBits.join(" · ")) +
                      "</span>"
                    : "") +
                  "</span>" +
                  (preview
                    ? '<span class="lore-chip-line">' +
                      escapeHtml(preview) +
                      "</span>"
                    : "") +
                  "</span></label>";
              });
              list.innerHTML = html2;
            }

            body.__attachPickState = pickState;
            body.__attachDeckPick = deckPick;

            if (!allCards.length) {
              body.innerHTML =
                '<p class="librarian-onto">onto ' +
                escapeHtml(ontoLabel()) +
                "</p>" +
                '<p class="librarian-empty">' +
                (deckPick
                  ? "no lore in any cabinet yet. Add Lore in Librarian, Detective, Charlie, or TPS first."
                  : "no lore in this house yet. Add Lore first.") +
                "</p>";
              setStatus("no lore yet");
              return;
            }

            var houses = uniqSorted(
              allCards.map(function (c) {
                return c.house || c.mouth || "";
              })
            );
            var makers = uniqSorted(
              allCards.map(function (c) {
                return c.maker || "";
              })
            );
            var classes = uniqSorted(
              allCards.map(function (c) {
                return c.class || "";
              })
            );

            var html =
              '<p class="librarian-onto">onto ' +
              escapeHtml(ontoLabel()) +
              (deckPick
                ? " · filter to load · Apply attaches & detaches"
                : "") +
              "</p>" +
              '<div class="lore-attach-filters">' +
              '<label class="lore-attach-field lore-attach-q">search' +
              '<input type="search" data-attach-q class="librarian-leaf tagbay-input" placeholder="title, maker, class, line…" autocomplete="off">' +
              "</label>" +
              (deckPick || houses.length > 1
                ? '<label class="lore-attach-field">house<select data-attach-house class="librarian-leaf tagbay-input">' +
                  optionsHtml(houses, "all houses") +
                  "</select></label>"
                : "") +
              (makers.length
                ? '<label class="lore-attach-field">maker<select data-attach-maker class="librarian-leaf tagbay-input">' +
                  optionsHtml(makers, "all makers") +
                  "</select></label>"
                : "") +
              (classes.length
                ? '<label class="lore-attach-field">class<select data-attach-class class="librarian-leaf tagbay-input">' +
                  optionsHtml(classes, "all classes") +
                  "</select></label>"
                : "") +
              '<p class="lore-attach-count" data-attach-count></p>' +
              "</div>" +
              '<div class="lore-attach-list' +
              (deckPick ? " is-deck" : "") +
              '" data-attach-list></div>';

            body.innerHTML = html;
            paintList();
            var filters = body.querySelector(".lore-attach-filters");
            if (filters) {
              filters.addEventListener("input", paintList);
              filters.addEventListener("change", paintList);
            }
            var listEl = body.querySelector("[data-attach-list]");
            if (listEl) {
              listEl.addEventListener("change", function (e) {
                var input = e.target;
                if (
                  !input ||
                  !input.matches ||
                  !input.matches('input[data-field="card"]')
                )
                  return;
                var crate = String(input.value || "").trim();
                if (!crate || !pickState[crate]) return;
                pickState[crate].on = !!input.checked;
                var face = input.closest(".lore-attach-face");
                if (face) face.classList.toggle("is-on", !!input.checked);
                var row = input.closest(".lore-pick");
                if (row) row.classList.toggle("is-checked", !!input.checked);
                var countEl = body.querySelector("[data-attach-count]");
                if (countEl) {
                  var shownN = filtersActive()
                    ? filteredCards().length
                    : 0;
                  var selectedN = 0;
                  Object.keys(pickState).forEach(function (k) {
                    if (pickState[k].on) selectedN += 1;
                  });
                  countEl.textContent = filtersActive()
                    ? shownN + " shown · " + selectedN + " on page"
                    : allCards.length +
                      " in cabinets · set a filter to load";
                }
              });
            }
            var qFocus = body.querySelector("[data-attach-q]");
            if (qFocus) qFocus.focus();
            setStatus(
              deckPick
                ? allCards.length + " catalogued — filter to load faces"
                : allCards.length + " cards ready"
            );
          })
          .catch(function (err) {
            var okFail = modal && modal.querySelector("[data-modal-ok]");
            if (okFail) okFail.disabled = false;
            if (body) {
              body.innerHTML =
                '<p class="librarian-empty">' +
                escapeHtml(err.message || "could not list lore") +
                "</p>";
            }
            setStatus(err.message || "could not list lore", true);
          });
      });
    }

function fieldVal(body, name, isCheck) {
      var el = body.querySelector('[data-field="' + name + '"]');
      if (!el) return "";
      if (isCheck) return !!el.checked;
      return el.value;
    }

    function confirmModal() {
      if (librarianOff() || !modalMode) return;
      var body = $(ids.modalBody);
      if (!body) return;
      if (modalMode === "note") {
        var name = String(fieldVal(body, "title") || "").trim();
        if (!name) {
          setStatus("need a name", true);
          return;
        }
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api, { pocket: pocket, title: name })
            .then(function (data) {
              closeModal();
              var href = (data && data.href) || "";
              setStatus("opened " + ((data && data.file) || name));
              if (!href) {
                setStatus("page made, but no pocket link — hard-refresh", true);
                return;
              }
              goHref(href);
            })
            .catch(function (err) {
              setStatus(err.message || "could not make page", true);
            });
        });
        return;
      }
      if (modalMode === "folder-rename") {
        var renameFolderTo = String(fieldVal(body, "title") || "").trim();
        if (!renameFolderTo) {
          setStatus("need a name", true);
          return;
        }
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api, {
            pocket: pocket,
            what: "folder-rename",
            title: renameFolderTo,
          })
            .then(function (data) {
              closeModal();
              setStatus("renamed folder " + ((data && data.folder) || renameFolderTo));
              goHref(data && data.href);
            })
            .catch(function (err) {
              setStatus(err.message || "could not rename folder", true);
            });
        });
        return;
      }
      if (modalMode === "folder") {
        var folderName = String(fieldVal(body, "title") || "").trim();
        if (!folderName) {
          setStatus("need a name", true);
          return;
        }
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api, { pocket: pocket, what: "folder", title: folderName })
            .then(function (data) {
              closeModal();
              setStatus("opened folder " + ((data && data.folder) || folderName));
              goHref(data && data.href);
            })
            .catch(function (err) {
              setStatus(err.message || "could not make folder", true);
            });
        });
        return;
      }
      if (modalMode === "letter") {
        var letterTitle = String(fieldVal(body, "title") || "").trim();
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api, { pocket: pocket, what: "readme", title: letterTitle })
            .then(function (data) {
              closeModal();
              blot = data || blot;
              letterFace = "room";
              letterEditMode = true;
              setStatus("room letter for this hall");
              if (typeof loadBlot === "function") loadBlot();
              else render();
              refreshDesk();
            })
            .catch(function (err) {
              setStatus(err.message || "could not make room letter", true);
            });
        });
        return;
      }
      if (modalMode === "shell") {
        var shellTitle = String(fieldVal(body, "title") || "").trim();
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api, { pocket: pocket, what: "shell", title: shellTitle })
            .then(function (data) {
              closeModal();
              setStatus("subshell " + ((data && data.file) || "_shell.md"));
              // reload BIOS on same place so shell door appears
              if (typeof load === "function") load();
              else if (data && data.href) goHref(data.href);
            })
            .catch(function (err) {
              setStatus(err.message || "could not make shell", true);
            });
        });
        return;
      }
      if (modalMode === "apply-template") {
        var applyTid = String(fieldVal(body, "template") || "").trim();
        var applyMode = String(fieldVal(body, "mode") || "overwrite").trim() || "overwrite";
        if (!applyTid) {
          setStatus("pick a template", true);
          return;
        }
        var applySlug = hostsSlug || (hostsBlot && hostsBlot.host) || currentPocketHost() || "";
        if (!applySlug) {
          setStatus("open a host first", true);
          return;
        }
        api("POST", "/api/templates/apply", {
          pocket: "go." + applySlug,
          template: applyTid,
          mode: applyMode,
        })
          .then(function (data) {
            closeModal();
            setStatus(
              "applied " +
                applyTid +
                (data && data.css ? " → " + data.css : "") +
                (applyMode === "fork" ? " (fork)" : "")
            );
            loadHosts(applySlug);
            render();
            refreshDesk();
          })
          .catch(function (err) {
            setStatus(err.message || "could not apply template", true);
          });
        return;
      }
      if (modalMode === "host") {
        var hostSlug = String(fieldVal(body, "slug") || "").trim();
        var hostTitle = String(fieldVal(body, "title") || "").trim();
        if (!hostSlug && !hostTitle) {
          setStatus("need a go name", true);
          return;
        }
        var hostTemplate = String(fieldVal(body, "template") || "").trim();
        api("POST", "/api/hosts", {
          slug: hostSlug,
          title: hostTitle || hostSlug,
          template: hostTemplate,
        })
          .then(function (data) {
            closeModal();
            var made = (data && data.host) || hostSlug;
            setStatus("minted go." + made);
            hostsEditMode = false;
            letterFace = "hosts";
            loadHosts(made);
            render();
            refreshDesk();
          })
          .catch(function (err) {
            setStatus(err.message || "could not mint host", true);
          });
        return;
      }
      if (modalMode === "roam") {
        var roamSlug = String(fieldVal(body, "slug") || "").trim();
        var roamTitle = String(fieldVal(body, "title") || "").trim();
        var roamSource = String(fieldVal(body, "source") || "").trim();
        var roamEnv = String(fieldVal(body, "environment") || "").trim();
        if (!roamSlug && !roamTitle) {
          setStatus("need a roam name", true);
          return;
        }
        if (!roamSource) {
          setStatus("need a source folder", true);
          return;
        }
        api("POST", "/api/hosts", {
          kind: "roam",
          slug: roamSlug,
          title: roamTitle || roamSlug,
          source: roamSource,
          environment: roamEnv,
        })
          .then(function (data) {
            closeModal();
            var made = (data && data.host) || roamSlug;
            setStatus("connected roam." + made);
            hostsEditMode = false;
            letterFace = "hosts";
            loadHosts(made);
            render();
            refreshDesk();
          })
          .catch(function (err) {
            setStatus(err.message || "could not connect roam", true);
          });
        return;
      }
      if (modalMode === "rename") {
        var renameTo = String(fieldVal(body, "title") || "").trim();
        if (!renameTo) {
          setStatus("need a name", true);
          return;
        }
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api, {
            pocket: pocket,
            what: "rename",
            title: renameTo,
            which: (currentClay() && currentClay().kind) || letterWhich || "",
          })
            .then(function (data) {
              closeModal();
              setStatus("renamed " + ((data && data.file) || renameTo));
              goHref(data && data.href);
            })
            .catch(function (err) {
              setStatus(err.message || "could not rename", true);
            });
        });
        return;
      }
      if (modalMode === "stamp") {
        var stampTitle = String(fieldVal(body, "title") || "").trim();
        var known = String(fieldVal(body, "known") || "").trim();
        var when = String(fieldVal(body, "when") || "").trim();
        if (!stampTitle) {
          setStatus("need a title", true);
          return;
        }
        var rawTime = known;
        if (!rawTime && when) {
          var parsed = Date.parse(when);
          if (!isNaN(parsed)) rawTime = String(Math.floor(parsed / 1000));
        }
        if (!rawTime) {
          setStatus("need a date", true);
          return;
        }
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api, { pocket: pocket, title: stampTitle, time: rawTime })
            .then(function (data) {
              blot = data || blot;
              closeModal();
              render();
              setStatus("stamped " + stampTitle);
            })
            .catch(function (err) {
              setStatus(err.message || "could not stamp", true);
            });
        });
        return;
      }
      if (modalMode === "attach") {
        var pickState = body.__attachPickState || null;
        var deckPick = !!body.__attachDeckPick;
        if (deckPick && pickState) {
          var attachList = [];
          var detachList = [];
          Object.keys(pickState).forEach(function (crate) {
            var st = pickState[crate];
            if (!st) return;
            if (st.on && !st.was) {
              attachList.push({ crate: crate, mouth: st.mouth || "" });
            } else if (!st.on && st.was) {
              detachList.push({ crate: crate, mouth: st.mouth || "" });
            }
          });
          if (!attachList.length && !detachList.length) {
            setStatus("no changes", true);
            return;
          }
          withFreshVault(function (pocket) {
            if (librarianOff()) return;
            api("POST", "/api/cards/lore/sync", {
              pocket: pocket,
              onto: catalogOnto,
              attach: attachList,
              detach: detachList,
            })
              .then(function (data) {
                blot = data || blot;
                closeModal();
                render();
                var parts = [];
                if (data && data.attached_n)
                  parts.push("attached " + data.attached_n);
                if (data && data.detached_n)
                  parts.push("detached " + data.detached_n);
                setStatus(parts.length ? parts.join(" · ") : "deck updated");
              })
              .catch(function (err) {
                setStatus(err.message || "could not update deck", true);
              });
          });
          return;
        }
        var picked = body.querySelectorAll(
          '[data-field="card"]:checked:not([disabled])'
        );
        if (!picked.length) {
          setStatus("pick at least one card", true);
          return;
        }
        // Non-deck cabinets: attach each checked card (no detach here yet).
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          var chain = Promise.resolve();
          var last = null;
          var n = 0;
          Array.prototype.forEach.call(picked, function (el) {
            var cardCrate = String(el.value || "").trim();
            if (!cardCrate) return;
            n += 1;
            chain = chain.then(function () {
              return api("POST", cfg.api + "/lore/attach", {
                pocket: pocket,
                crate: cardCrate,
                onto: catalogOnto,
              }).then(function (data) {
                last = data;
              });
            });
          });
          if (!n) {
            setStatus("pick at least one card", true);
            return;
          }
          chain
            .then(function () {
              if (last) blot = last;
              closeModal();
              render();
              setStatus("attached " + n);
            })
            .catch(function (err) {
              setStatus(err.message || "could not attach", true);
            });
        });
        return;
      }
      if (modalMode === "meta" || modalMode === "meta-edit") {
        var kind = String(fieldVal(body, "type") || "input");
        var label = String(fieldVal(body, "label") || "").trim();
        var value =
          kind === "bool" ? fieldVal(body, "value", true) : fieldVal(body, "value");
        if (!label) {
          setStatus("need a label", true);
          return;
        }
        var editing = modalMode === "meta-edit";
        var payload = {
          pocket: vaultPath(),
          type: kind,
          label: label,
          value: value,
          onto: catalogOnto,
        };
        if (editing) payload.index = editIndex;
        api(editing ? "PUT" : "POST", cfg.api, payload)
          .then(function (data) {
            blot = data || blot;
            closeModal();
            render();
            setStatus(editing ? "amended " + label : "filed " + label);
            loadSuggest();
          })
          .catch(function (err) {
            setStatus(err.message || (editing ? "could not amend" : "could not file"), true);
          });
        return;
      }
      if (modalMode === "lore" || modalMode === "lore-edit") {
        var klass = String(fieldVal(body, "class") || "").trim();
        var title = String(fieldVal(body, "title") || "").trim();
        var line = String(fieldVal(body, "line") || "").trim();
        var when = String(fieldVal(body, "time") || "").trim();
        if (!title) {
          setStatus("need a lore title", true);
          return;
        }
        if (!line) {
          setStatus("need a lore line", true);
          return;
        }
        var amending = modalMode === "lore-edit";
        if (amending && !editLoreCrate) {
          setStatus("no such lore", true);
          return;
        }
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          var maker = String(fieldVal(body, "maker") || "").trim();
          var payload = {
            pocket: pocket,
            class: klass,
            title: title,
            line: line,
            time: when,
            onto: catalogOnto,
            maker: maker,
          };
          if (amending) payload.crate = editLoreCrate;
          api(amending ? "PUT" : "POST", cfg.api + "/lore", payload)
            .then(function (data) {
              blot = data || blot;
              closeModal();
              render();
              setStatus(
                amending
                  ? "amended " + title
                  : "filed " + (data && data.file ? data.file : title)
              );
              loadSuggest();
            })
            .catch(function (err) {
              setStatus(
                err.message || (amending ? "could not amend lore" : "could not file lore"),
                true
              );
            });
        });
        return;
      }
    }

    function mount() {
      var stage = document.querySelector(".wwwExplorer_stage");
      if (!stage || $(ids.drawer)) return;
      var aside = document.createElement("aside");
      aside.id = cfg.id;
      aside.className = "librarian" + (cfg.skin ? " " + cfg.skin : "");
      aside.setAttribute("hidden", "");
      var modalHtml =
        '<div class="librarian-modal" id="' +
        ids.modal +
        '" hidden>' +
        '<div class="librarian-modal-card">' +
        '<strong id="' +
        ids.modalTitle +
        '"></strong>' +
        '<div id="' +
        ids.modalBody +
        '"></div>' +
        '<div class="librarian-modal-actions">' +
        '<button type="button" data-modal-cancel>Cancel</button>' +
        '<button type="button" class="librarian-store" data-modal-ok>Confirm</button>' +
        "</div></div></div>";
      var composerHtml =
        cfg.kind === "cards"
          ? '<div class="librarian-composer" id="' +
            ids.composer +
            '">' +
            '<div class="librarian-kicker">' +
            escapeHtml(cfg.kicker) +
            "</div>" +
            '<p class="librarian-hint">lore cards on this page and its shell. Search hunts the whole deck.</p>' +
            '<form class="lore-search-pad" data-lore-search>' +
            '<input type="search" data-lore-q placeholder="search the deck" autocomplete="off" spellcheck="false">' +
            '<button type="submit">look</button>' +
            "</form>" +
            '<div class="catalog-actions">' +
            '<button type="button" class="librarian-store" data-attach-lore>Attach Lore</button>' +
            "</div>" +
            '<p class="librarian-status" id="' +
            ids.status +
            '"></p></div>' +
            modalHtml
          : cfg.kind === "catalog"
          ? '<div class="librarian-composer" id="' +
            ids.composer +
            '">' +
            '<div class="librarian-kicker-row">' +
            '<div class="librarian-kicker">' +
            escapeHtml(cfg.kicker) +
            "</div>" +
            '<div class="catalog-onto" hidden>' +
            '<button type="button" class="catalog-onto-btn" data-catalog-onto="shell">shell</button>' +
            '<button type="button" class="catalog-onto-btn is-on" data-catalog-onto="page">this page</button>' +
            "</div>" +
            "</div>" +
            (cfg.id === "detective" || cfg.id === "librarian"
              ? '<button type="button" class="hunt-toggle" data-hunt-open>pin slip</button>' +
                '<form class="hunt-pad" hidden autocomplete="off">' +
                '<input class="hunt-title tagbay-input" type="text" data-hunt-title placeholder="' +
                (cfg.id === "librarian" ? "a note" : "a thought") +
                '">' +
                '<input class="hunt-mind tagbay-input" type="text" data-hunt-mind placeholder="' +
                (cfg.id === "librarian" ? "in the margin (optional)" : "mindset (optional)") +
                '">' +
                '<textarea class="hunt-body tagbay-input" data-hunt-body rows="2" placeholder="' +
                (cfg.id === "librarian" ? "the card" : "the fragment") +
                '"></textarea>' +
                '<div class="hunt-pad-tools">' +
                '<button type="submit" class="librarian-store" data-add-hunt>keep</button>' +
                '<button type="button" class="hunt-cancel" data-hunt-cancel>cancel</button>' +
                "</div></form>"
              : "") +
            '<div class="catalog-actions">' +
            (cfg.id === "detective"
              ? '<button type="button" class="librarian-store" data-add-meta>meta</button>' +
                '<button type="button" class="librarian-store" data-add-lore>lore</button>' +
                '<button type="button" class="librarian-store" data-attach-lore>attach</button>'
              : '<button type="button" class="librarian-store" data-add-meta>Add Meta Data</button>' +
                '<button type="button" class="librarian-store" data-add-lore>Add Lore</button>' +
                '<button type="button" class="librarian-store" data-attach-lore>Attach Lore</button>') +
            "</div>" +
            '<p class="librarian-status" id="' +
            ids.status +
            '"></p></div>' +
            modalHtml
          : cfg.kind === "tps"
          ? '<div class="librarian-composer tps-sheet" id="' +
            ids.composer +
            '">' +
            '<div class="tps-sheet-mast">' +
            '<strong class="tps-mark">TPS</strong>' +
            '<span class="tps-sheet-label">cover sheet</span>' +
            '<span class="librarian-count" id="' +
            ids.count +
            '"></span>' +
            '<div class="tps-sheet-tools">' +
            '<button type="button" class="tagbay-copy" data-refresh title="Refresh this cabinet now">↻</button>' +
            (SIDECAR
              ? ""
              : '<button type="button" class="librarian-pop" data-pop title="Open as a window">⧉</button>') +
            "</div></div>" +
            '<p class="tps-memo">Time positional system. God forbid you file without a TPS — how will it know where to go.</p>' +
            '<div class="tps-coords">' +
            '<div class="tps-coord"><span>where</span><strong class="tps-coord-where">this page</strong></div>' +
            '<div class="tps-coord"><span>when</span><strong class="tps-coord-when">unstamped</strong></div>' +
            "</div>" +
            '<button type="button" class="era-toggle" data-era-open>pin event</button>' +
            '<form class="era-pad" hidden autocomplete="off">' +
            '<input class="era-title tagbay-input" type="text" data-era-title placeholder="event name" list="era-names">' +
            '<datalist id="era-names"></datalist>' +
            '<input class="era-code tagbay-input" type="text" data-era-code placeholder="event code (blank = assign EV-001)">' +
            '<input class="era-sit tagbay-input" type="text" data-era-sit placeholder="perspective (optional)">' +
            '<textarea class="era-body tagbay-input" data-era-body rows="2" placeholder="what happened here"></textarea>' +
            '<div class="era-pad-tools">' +
            '<button type="submit" class="librarian-store" data-add-era>keep</button>' +
            '<button type="button" class="era-cancel" data-era-cancel>cancel</button>' +
            "</div></form>" +
            '<div class="tps-punch">' +
            '<button type="button" class="tps-clock" data-add-stamp>stamp</button>' +
            '<button type="button" class="tps-file" data-add-lore>lore</button>' +
            '<button type="button" class="tps-file" data-attach-lore>attach</button>' +
            "</div>" +
            '<p class="librarian-status" id="' +
            ids.status +
            '"></p></div>' +
            modalHtml
          : '<form class="librarian-composer' +
            (cfg.kind === "tags" ? " charlie-loom" : "") +
            '" id="' +
            ids.composer +
            '" autocomplete="off">' +
            (cfg.kind === "tags"
              ? ""
              : '<div class="librarian-kicker">' +
                escapeHtml(cfg.kicker) +
                "</div>") +
            (cfg.kind === "tags"
              ? '<div class="charlie-loom-mast">' +
                '<strong class="charlie-mark">CHARLIE</strong>' +
                '<span class="charlie-loom-label">loom</span>' +
                '<span class="librarian-count" id="' +
                ids.count +
                '"></span>' +
                '<div class="charlie-loom-tools">' +
                '<button type="button" class="tagbay-copy" data-refresh title="Refresh this cabinet now">↻</button>' +
                (SIDECAR
                  ? ""
                  : '<button type="button" class="librarian-pop" data-pop title="Open as a window">⧉</button>') +
                "</div></div>" +
                '<div class="charlie-tri">' +
                '<label class="charlie-slot">from' +
                '<input id="' +
                ids.leaf +
                '" class="librarian-leaf tagbay-input" type="text" autocomplete="off" placeholder="a tag">' +
                "</label>" +
                '<span class="charlie-sep" aria-hidden="true">*</span>' +
                '<label class="charlie-slot">rel' +
                '<input id="' +
                ids.rel +
                '" class="librarian-leaf tagbay-input" type="text" autocomplete="off">' +
                "</label>" +
                '<span class="charlie-sep" aria-hidden="true">&gt;</span>' +
                '<label class="charlie-slot">to' +
                '<input id="' +
                ids.to +
                '" class="librarian-leaf tagbay-input" type="text" autocomplete="off">' +
                "</label>" +
                "</div>" +
                '<div class="charlie-shuttle">' +
                '<button type="submit" class="charlie-tie">thread</button>' +
                '<button type="button" class="charlie-stitch" data-add-lore>lore</button>' +
                '<button type="button" class="charlie-stitch" data-attach-lore>attach</button>' +
                "</div>"
              : cfg.kind === "letter"
              ? '<div class="readme-tabs bios-doors" id="readmeDoors"></div>' +
                '<div id="readmeRoom">' +
                '<div class="readme-pane is-md is-letter">' +
                '<div class="readme-pane-bar">' +
                '<span class="readme-letter-label">room letter</span>' +
                "</div>" +
                '<article id="readmeRoomView" class="readme-letter-view" hidden></article>' +
                '<textarea id="' +
                ids.leaf +
                '" class="librarian-leaf librarian-letter" rows="18" placeholder="' +
                escapeHtml(cfg.placeholder) +
                '"></textarea>' +
                "</div>" +
                "</div>" +
                '<div id="readmePage" hidden>' +
                '<div class="readme-pane is-yaml">' +
                '<div class="readme-pane-bar">headers</div>' +
                '<textarea id="' +
                ids.headers +
                '" class="librarian-leaf readme-headers" rows="8" placeholder="yaml front matter"></textarea>' +
                "</div>" +
                '<div class="readme-pane is-md">' +
                '<div class="readme-pane-bar">markdown</div>' +
                '<textarea id="' +
                ids.markdown +
                '" class="librarian-leaf librarian-letter" rows="12" placeholder="the page body"></textarea>' +
                "</div>" +
                "</div>" +
                '<div id="readmeHelpPane" hidden>' +
                '<div class="readme-pane is-md is-letter is-help">' +
                '<div class="readme-pane-bar" id="readmeHelpBar">' +
                '<span class="readme-letter-label">help</span>' +
                '<div class="readme-help-pages" id="readmeHelpPages"></div>' +
                '</div>' +
                '<article id="readmeHelpView" class="readme-letter-view" hidden></article>' +
                '<textarea id="readmeHelpLeaf" class="librarian-leaf librarian-letter" rows="18" placeholder="field manual — edit and Keep"></textarea>' +
                '</div>' +
                '</div>' +
                '<div id="readmeHostsPane" hidden>' +
                '<div class="readme-hosts-bar" id="readmeHostsBar">' +
                '<span class="readme-letter-label">hosts</span>' +
                '<select id="readmeHostsSelect" class="readme-hosts-select" title="pick a host"></select>' +
                '<button type="button" class="librarian-store readme-hosts-meta-btn" data-hosts-show title="show on go or roam doors">Show</button>' +
                '<button type="button" class="librarian-store readme-hosts-meta-btn" data-hosts-pin title="pin on go or roam doors">Pin</button>' +
                '<button type="button" class="librarian-store readme-hosts-meta-btn" data-apply-template title="apply thin layout template to this host">apply template…</button>' +
                '</div>' +
                '<div id="readmeHostsRoam" class="readme-pane is-hosts-roam" hidden>' +
                '<div class="readme-pane-bar">roam</div>' +
                '<p class="readme-hosts-scheme" id="readmeHostsScheme"></p>' +
                '<button type="button" class="librarian-store readme-hosts-disconnect" data-hosts-disconnect>Disconnect</button>' +
                '<p class="readme-hosts-roam-hint">Edit kind / source / title / environment in roam frontmatter below. Disconnect drops the yaml line; the folder on disk stays.</p>' +
                '</div>' +
                '<div class="readme-pane is-yaml is-hosts-shell">' +
                '<div class="readme-pane-bar">shell frontmatter</div>' +
                '<textarea id="readmeHostsHeaders" class="librarian-leaf readme-headers" rows="10" placeholder="title / section / neighborhood yaml"></textarea>' +
                '</div>' +
                '<div class="readme-pane is-md is-letter is-hosts-letter">' +
                '<div class="readme-pane-bar" id="readmeHostsLetterBar">' +
                '<span class="readme-letter-label">room letter</span>' +
                '</div>' +
                '<article id="readmeHostsLetterView" class="readme-letter-view" hidden></article>' +
                '<textarea id="readmeHostsLetter" class="librarian-leaf librarian-letter" rows="14" placeholder="room letter for this host"></textarea>' +
                '</div>' +
                '</div>' +
                '<div id="readmeCratesPane" hidden>' +
                '<div class="readme-crates-bar" id="readmeCratesBar">' +
                '<span class="readme-letter-label">crates</span>' +
                '<select id="readmeCratesMode" class="readme-crates-mode" title="search mode">' +
                '<option value="all">all</option>' +
                '<option value="title">title</option>' +
                '<option value="path">path</option>' +
                '<option value="body">body</option>' +
                '<option value="crate">crate</option>' +
                '</select>' +
                '<input type="search" id="readmeCratesQ" class="readme-crates-q" placeholder="title / path / crate hex" autocomplete="off" spellcheck="false" />' +
                '</div>' +
                '<div class="readme-crates-results" id="readmeCratesResults">' +
                '<p class="readme-crates-empty">type a title, path, or crate hex</p>' +
                '</div>' +
                '</div>' +
                '<div id="readmeCoatPane" hidden>' +
                '<div class="readme-pane is-css">' +
                '<div class="readme-pane-bar" id="readmeCoatBar">' +
                '<span>coat css</span>' +
                '<button type="button" class="readme-coat-split-toggle" id="readmeCoatSplitToggle" title="toggle color panel">colors</button>' +
                '</div>' +
                '<div class="readme-coat-split" id="readmeCoatSplit">' +
                '<div id="readmeCoatPalette" class="readme-coat-palette" hidden></div>' +
                '<div class="readme-coat-editor">' +
                '<textarea id="' +
                ids.coat +
                '" class="librarian-leaf librarian-letter" rows="18" placeholder="environment coat — mats/styles/{env}.css"></textarea>' +
                '</div>' +
                '</div>' +
                "</div>" +
                "</div>"
              : '<textarea id="' +
                ids.leaf +
                '" class="librarian-leaf" rows="4" placeholder="' +
                escapeHtml(cfg.placeholder) +
                '"></textarea>') +
            (cfg.kind === "tags"
              ? ""
              : '<div class="librarian-actions' +
            (cfg.kind === "letter" ? " bios-actions" : "") +
            '">' +
            (cfg.kind === "letter"
              ? '<div class="bios-act-group bios-act-primary">' +
                '<button type="submit" class="librarian-store">' +
                escapeHtml(cfg.issue) +
                "</button>" +
                '<button type="button" class="librarian-store readme-letter-edit-btn" data-letter-edit hidden>Edit</button>' +
                '<button type="button" class="librarian-store readme-letter-edit-btn" data-letter-cancel hidden>Cancel</button>' +
                '<button type="button" class="librarian-store readme-letter-edit-btn" data-help-edit hidden>Edit</button>' +
                '<button type="button" class="librarian-store readme-letter-edit-btn" data-help-cancel hidden>Cancel</button>' +
                '<button type="button" class="librarian-store readme-letter-edit-btn" data-hosts-edit hidden>Edit</button>' +
                '<button type="button" class="librarian-store readme-letter-edit-btn" data-hosts-cancel hidden>Cancel</button>' +
                "</div>" +
                '<div class="bios-act-group bios-act-file" data-bios-plus>' +
                '<button type="button" class="librarian-store bios-plus-toggle" data-bios-plus-toggle hidden title="more file actions" aria-expanded="false">+</button>' +
                '<div class="bios-plus-tray">' +
                '<button type="button" class="librarian-store" data-new-shell hidden title="mint _shell.md subshell — nests in the parent paper hole">+ shell</button>' +
                '<button type="button" class="librarian-store" data-new-note>+ page</button>' +
                '<button type="button" class="librarian-store bios-act-rename" data-rename-note hidden>Rename page</button>' +
                '<button type="button" class="librarian-store" data-new-folder>+ folder</button>' +
                '<button type="button" class="librarian-store bios-act-rename-folder" data-rename-folder title="rename this hall (folder) on disk">Rename folder</button>' +
                '<button type="button" class="librarian-store" data-new-letter hidden title="mint a room letter for this hall — host letter stays put">+ readme</button>' +
                '<button type="button" class="librarian-store" data-new-host hidden>+ host</button>' +
                '<button type="button" class="librarian-store" data-new-roam hidden>+ roam</button>' +
                "</div>" +
                "</div>" +
                (cfg.lore
                  ? '<div class="bios-act-group bios-act-lore">' +
                    '<button type="button" class="librarian-store" data-add-lore>+ Lore</button>' +
                    '<button type="button" class="librarian-store" data-attach-lore>Attach</button>' +
                    "</div>"
                  : "") +
                '<div class="bios-act-group bios-act-help">' +
                '<button type="button" class="librarian-store readme-hosts-fab" id="readmeHostsFab" title="start doors registry — edit any host shell/letter">Hosts</button>' +
                '<button type="button" class="librarian-store readme-crates-fab" id="readmeCratesFab" title="crate finder — copy crate.HEX or {{link:crate.HEX}}">Crates</button>' +
                '<button type="button" class="librarian-store readme-help-fab" id="readmeHelpFab" title="system field manual — tokens, type, notes">Help</button>' +
                "</div>" : '<button type="submit" class="librarian-store">' +
                escapeHtml(cfg.issue) +
                "</button>" +
                (cfg.lore
                  ? '<button type="button" class="librarian-store" data-add-lore>Add Lore</button>' +
                    '<button type="button" class="librarian-store" data-attach-lore>Attach Lore</button>'
                  : "") +
                '<span class="librarian-hint">Ctrl+Enter</span>') +
            "</div>") +
            '<p class="librarian-status" id="' +
            ids.status +
            '"></p>' +
            "</form>" +
            (cfg.lore || cfg.kind === "letter" ? modalHtml : "");
      aside.innerHTML =
        cfg.kind === "letter"
          ? '<div class="librarian-head bios-id">' +
            "<strong>" +
            escapeHtml(cfg.title) +
            "</strong>" +
            '<span class="librarian-count" id="' +
            ids.count +
            '" hidden></span>' +
            '<span class="librarian-path" id="' +
            ids.path +
            '"></span>' +
            '<span class="tagbay-crate" id="' +
            ids.crate +
            '"></span>' +
            '<button type="button" class="tagbay-copy" data-refresh title="Refresh this cabinet now">refresh</button>' +
            (SIDECAR
              ? ""
              : '<button type="button" class="librarian-pop" data-pop title="Open as a window">pop</button>') +
            "</div>" +
            composerHtml +
            '<img class="skyline-stamp" src="/i/skyline-approved-stamp.png" alt="Skyline approved" width="48" height="48" title="Skyline approved">' +
            '<div class="librarian-stack" id="' +
            ids.stack +
            '"></div>'
          : cfg.kind === "tags" || cfg.kind === "tps"
          ? composerHtml +
            '<div class="librarian-path" id="' +
            ids.path +
            '" hidden></div>' +
            '<div class="tagbay-crate" id="' +
            ids.crate +
            '" hidden></div>' +
            '<div class="librarian-stack" id="' +
            ids.stack +
            '"></div>'
          : '<div class="librarian-head">' +
            '<div class="librarian-mast">' +
            (cfg.id === "librarian"
              ? '<img class="librarian-seal" src="/i/quire-librarian-seal.png" alt="" width="40" height="40">'
              : "") +
            "<strong>" +
            escapeHtml(cfg.title) +
            "</strong>" +
            "</div>" +
            '<span class="librarian-count" id="' +
            ids.count +
            '" hidden></span>' +
            '<div class="librarian-head-tools">' +
            (cfg.kind === "catalog"
              ? '<button type="button" class="tagbay-copy librarian-crate-copy" data-copy-crate title="Copy active crate id">#</button>'
              : "") +
            '<button type="button" class="tagbay-copy" data-refresh title="Refresh this cabinet now">↻</button>' +
            (SIDECAR
              ? ""
              : '<button type="button" class="librarian-pop" data-pop title="Open as a window">⧉</button>') +
            "</div>" +
            "</div>" +
            '<div class="librarian-path" id="' +
            ids.path +
            '"></div>' +
            '<div class="tagbay-crate" id="' +
            ids.crate +
            '"></div>' +
            composerHtml +
            '<div class="librarian-stack" id="' +
            ids.stack +
            '"></div>';
      stage.appendChild(aside);

      var form = $(ids.composer);
      if (form && form.tagName === "FORM") {
        form.addEventListener("submit", function (e) {
          e.preventDefault();
          storeThought();
        });
      }
      var huntForm = aside.querySelector(".hunt-pad");
      if (huntForm) {
        huntForm.addEventListener("submit", function (e) {
          e.preventDefault();
          pinHunt(e);
        });
      }
      var eraForm = aside.querySelector(".era-pad");
      if (eraForm) {
        eraForm.addEventListener("submit", function (e) {
          e.preventDefault();
          pinEra(e);
        });
        var eraTitle = eraForm.querySelector("[data-era-title]");
        if (eraTitle) {
          eraTitle.addEventListener("input", preloadEraPerspective);
          eraTitle.addEventListener("change", preloadEraPerspective);
          eraTitle.addEventListener("blur", preloadEraPerspective);
        }
      }
      var loreForm = aside.querySelector("[data-lore-search]");
      if (loreForm) {
        loreForm.addEventListener("submit", function (e) {
          e.preventDefault();
          searchLoreDeck();
        });
      }
      var leaf = $(ids.leaf);
      if (leaf) {
        leaf.addEventListener("keydown", function (e) {
          if (cfg.kind === "tags") return;
          if (isKeepChord(e)) {
            e.preventDefault();
            storeThought();
            return;
          }
          if (cfg.kind === "letter" && e.key === "Tab" && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.preventDefault();
            insertIndent(leaf, e.shiftKey);
          }
        });
      }
      function isKeepChord(e) {
        if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey) return false;
        var k = e.key;
        // letter Keep: Ctrl/Cmd+S, Ctrl/Cmd+K, or Ctrl/Cmd+Enter.
        // Epiphany may still steal Ctrl+S / Ctrl+K; Ctrl+Enter remains the fallback.
        if (cfg.kind === "letter" && (k === "s" || k === "S" || k === "k" || k === "K"))
          return true;
        return k === "Enter";
      }
      var INDENT = "  ";
      function insertIndent(el, out) {
        var start = el.selectionStart;
        var end = el.selectionEnd;
        var val = el.value;
        var wide = start !== end && val.slice(start, end).indexOf("\n") !== -1;
        if (wide) {
          var lineStart = val.lastIndexOf("\n", start - 1) + 1;
          var lineEnd = val.indexOf("\n", end);
          if (lineEnd < 0) lineEnd = val.length;
          var block = val.slice(lineStart, lineEnd);
          var next = block.split("\n").map(function (line) {
            if (!out) return INDENT + line;
            if (line.indexOf(INDENT) === 0) return line.slice(INDENT.length);
            if (line.charAt(0) === "\t" || line.charAt(0) === " ") return line.slice(1);
            return line;
          }).join("\n");
          el.value = val.slice(0, lineStart) + next + val.slice(lineEnd);
          el.selectionStart = lineStart;
          el.selectionEnd = lineStart + next.length;
          return;
        }
        if (out) {
          var ls = val.lastIndexOf("\n", start - 1) + 1;
          var before = val.slice(ls, start);
          var drop = before.slice(-2) === INDENT ? 2 : before.slice(-1) === " " || before.slice(-1) === "\t" ? 1 : 0;
          if (!drop) return;
          el.value = val.slice(0, start - drop) + val.slice(end);
          el.selectionStart = el.selectionEnd = start - drop;
          return;
        }
        el.value = val.slice(0, start) + INDENT + val.slice(end);
        el.selectionStart = el.selectionEnd = start + INDENT.length;
      }
      function bindKeep(el) {
        if (!el) return;
        el.addEventListener("keydown", function (e) {
          if (isKeepChord(e)) {
            e.preventDefault();
            storeThought();
            return;
          }
          if (cfg.kind === "letter" && e.key === "Tab" && !e.ctrlKey && !e.metaKey && !e.altKey) {
            e.preventDefault();
            insertIndent(el, e.shiftKey);
          }
        });
      }

      bindKeep($(ids.headers));
      bindKeep($(ids.markdown));
      bindKeep($(ids.coat));

      /* BIOS IDE: CodeMirror colorize */
      var readmeCms = [];
      function loadCssOnce(href) {
        if (document.querySelector('link[data-cm="' + href + '"]')) return;
        var l = document.createElement("link");
        l.rel = "stylesheet";
        l.href = href;
        l.setAttribute("data-cm", href);
        document.head.appendChild(l);
      }
      function loadScriptOnce(src) {
        return new Promise(function (resolve, reject) {
          if (document.querySelector('script[data-cm="' + src + '"]')) {
            resolve();
            return;
          }
          var s = document.createElement("script");
          s.src = src;
          s.async = true;
          s.setAttribute("data-cm", src);
          s.onload = function () {
            resolve();
          };
          s.onerror = function () {
            reject(new Error("cm load fail " + src));
          };
          document.head.appendChild(s);
        });
      }
      function ensureCodeMirror() {
        if (window.CodeMirror) return Promise.resolve();
        var base = "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/";
        loadCssOnce(base + "codemirror.min.css");
        loadCssOnce(base + "theme/material-darker.min.css");
        return loadScriptOnce(base + "codemirror.min.js")
          .then(function () {
            return loadScriptOnce(base + "addon/mode/overlay.min.js");
          })
          .then(function () {
            return loadScriptOnce(base + "mode/yaml/yaml.min.js");
          })
          .then(function () {
            return loadScriptOnce(base + "mode/xml/xml.min.js");
          })
          .then(function () {
            return loadScriptOnce(base + "mode/markdown/markdown.min.js");
          })
          .then(function () {
            return loadScriptOnce(base + "mode/css/css.min.js");
          })
          .then(function () {
            if (window.CodeMirror && !window.CodeMirror.modes["pocket-md"]) {
              window.CodeMirror.defineMode("pocket-md", function (config) {
                var md = window.CodeMirror.getMode(config, {
                  name: "markdown",
                  highlightFormatting: true,
                  fencedCodeBlockHighlighting: false,
                  xml: false,
                });
                var pocket = {
                  token: function (stream) {
                    var m = stream.match(/\{\{([^}\n]*)\}\}/);
                    if (m) {
                      var inner = (m[1] || "").trim();
                      // dress / structure: {{div:}}, {{/div}}, {{span:}}, {{.class}}, {{#id}}
                      if (
                        /^(div\b|\/div\b|span\b|\/span\b|\.|#)/i.test(inner)
                      ) {
                        return "pg-token-dress";
                      }
                      return "pg-token";
                    }
                    if (stream.match(/\[\[[^\]\n]*\]\]/)) return "pg-wiki";
                    if (stream.match(/#[A-Za-z0-9_][\w-]*/)) return "pg-hash";
                    while (stream.next() != null) {
                      if (stream.match(/\{\{|\[\[|#/, false)) break;
                    }
                    return null;
                  },
                };
                return window.CodeMirror.overlayMode(md, pocket, true);
              });
            }
          });
      }
      function cmSaveAll() {
        for (var ci = 0; ci < readmeCms.length; ci++) {
          try {
            readmeCms[ci].save();
          } catch (e) {}
        }
      }
      function cmRefreshAll() {
        for (var ri = 0; ri < readmeCms.length; ri++) {
          try {
            readmeCms[ri].refresh();
          } catch (e) {}
        }
      }
      function cmRebuildList() {
        readmeCms = [];
        var els = [
          $(ids.leaf),
          $(ids.headers),
          $(ids.markdown),
          $(ids.coat),
          $("readmeHostsHeaders"),
          $("readmeHostsLetter"),
          $("readmeHelpLeaf"),
        ];
        for (var i = 0; i < els.length; i++) {
          if (els[i] && els[i]._cm) readmeCms.push(els[i]._cm);
        }
      }
      
      function cmFitEl(el) {
        if (!el || !el._cm) return;
        var wrap = el._cm.getWrapperElement();
        if (!wrap) return;
        var pane = wrap.parentElement;
        if (!pane) return;
        // don't fit editors in hidden faces (coat was leaking + thrashing layout)
        var host = pane.closest("#readmeRoom, #readmePage, #readmeCoatPane, #readmeHelpPane, #readmeHostsPane, #readmeCratesPane") || pane;
        if (host.hidden || (host.getAttribute && host.getAttribute("hidden") !== null)) {
          wrap.style.display = "none";
          return;
        }
        wrap.style.display = "";
        var bar = pane.querySelector(".readme-pane-bar");
        var h = pane.clientHeight - (bar ? bar.offsetHeight : 0) - 2;
        if (!(h > 60)) h = 120;
        try {
          el._cm.setSize("100%", h);
          el._cm.refresh();
        } catch (e) {}
      }
      function cmFitAllPanes() {
        cmFitEl($(ids.leaf));
        cmFitEl($(ids.headers));
        cmFitEl($(ids.markdown));
        cmFitEl($(ids.coat));
        cmFitEl($("readmeHostsHeaders"));
        cmFitEl($("readmeHostsLetter"));
      }
      function cmObservePane(el) {
        if (!el || !el._cm || el._cmFitObs) return;
        var wrap = el._cm.getWrapperElement();
        var pane = wrap && wrap.parentElement;
        if (!pane || typeof ResizeObserver === "undefined") return;
        var obs = new ResizeObserver(function () {
          cmFitEl(el);
        });
        obs.observe(pane);
        el._cmFitObs = obs;
        var root = document.getElementById(cfg.id);
        if (root && !root._cmFitObs) {
          var ro = new ResizeObserver(function () {
            cmFitAllPanes();
          });
          ro.observe(root);
          root._cmFitObs = ro;
        }
      }

      cmPullFromTextareas = function () {
        function pull(el) {
          if (!el || !el._cm) return;
          var v = el.value || "";
          if (el._cm.getValue() !== v) el._cm.setValue(v);
        }
        pull($(ids.leaf));
        pull($(ids.headers));
        pull($(ids.markdown));
        if (letterFace === "coat") pull($(ids.coat));
        function kick() {
          cmRebuildList();
          cmRefreshAll();
          try {
            cmFitAllPanes();
          } catch (e) {
            for (var i = 0; i < readmeCms.length; i++) {
              try {
                readmeCms[i].refresh();
              } catch (e2) {}
            }
          }
        }
        window.requestAnimationFrame(function () {
          kick();
          window.requestAnimationFrame(kick);
          window.setTimeout(kick, 50);
          window.setTimeout(kick, 200);
        });
      }
      function wireReadmeIde() {
        if (cfg.kind !== "letter") return;
        ensureCodeMirror()
          .then(function () {

                        function mount(el, mode) {
              if (!el) return;
              if (el._cm) {
                try {
                  el._cm.setValue(el.value || "");
                  cmFitEl(el);
                } catch (e) {}
                return;
              }
              var cm = window.CodeMirror.fromTextArea(el, {
                mode: mode,
                theme: "material-darker",
                lineNumbers: true,
                gutters: ["CodeMirror-linenumbers"],
                fixedGutter: true,
                lineWrapping: true,
                tabSize: 2,
                indentWithTabs: false,
                viewportMargin: Infinity,
                extraKeys: {
                  "Ctrl-S": function () {
                    cmSaveAll();
                    storeThought();
                    return false;
                  },
                  "Cmd-S": function () {
                    cmSaveAll();
                    storeThought();
                    return false;
                  },
                  "Ctrl-K": function () {
                    cmSaveAll();
                    storeThought();
                    return false;
                  },
                  "Cmd-K": function () {
                    cmSaveAll();
                    storeThought();
                    return false;
                  },
                  "Ctrl-Enter": function () {
                    cmSaveAll();
                    storeThought();
                    return false;
                  },
                  "Cmd-Enter": function () {
                    cmSaveAll();
                    storeThought();
                    return false;
                  },
                  Tab: function (c) {
                    c.replaceSelection("  ", "end");
                  },
                },
              });
              el._cm = cm;
              cm.setValue(el.value || "");
              cm.on("changes", function () {
                cm.save();
              });
              cmObservePane(el);
              window.requestAnimationFrame(function () {
                cmFitEl(el);
                window.requestAnimationFrame(function () {
                  cmFitEl(el);
                });
              });
              window.requestAnimationFrame(function () {
                cm.refresh();
              });
            }
            mount($(ids.leaf), "pocket-md");
            mount($(ids.headers), "yaml");
            mount($(ids.markdown), "pocket-md");
            mount($("readmeHostsHeaders"), "yaml");
            mount($("readmeHostsLetter"), "pocket-md");
            try {
              if ($(ids.leaf) && $(ids.leaf)._cm) biosTableBind($(ids.leaf)._cm);
              if ($(ids.markdown) && $(ids.markdown)._cm) biosTableBind($(ids.markdown)._cm);
              if ($("readmeHostsLetter") && $("readmeHostsLetter")._cm) biosTableBind($("readmeHostsLetter")._cm);
              if ($("readmeHelpLeaf") && $("readmeHelpLeaf")._cm) biosTableBind($("readmeHelpLeaf")._cm);
            } catch (eBiosTbl) {}
            /* coat CM lazy-mounted only on css door */
            cmRebuildList();
            cmPullFromTextareas();
            restoreKeepCursor();
          })
          .catch(function (err) {
            setStatus(
              (err && err.message) || "IDE colorizer offline — plain text still works",
              true
            );
          });
      }
      wireReadmeIde();
      try { biosDdBoot(); } catch (eBiosDd) {}
      var __storeThoughtBare = storeThought;
      storeThought = function () {
        cmSaveAll();
        return __storeThoughtBare.apply(this, arguments);
      };

      aside.addEventListener("change", function (e) {
        if (cfg.kind !== "catalog") return;
        var sel = e.target && e.target.getAttribute && e.target.getAttribute("data-field") === "type" ? e.target : null;
        if (!sel) return;
        var body = $(ids.modalBody);
        if (!body) return;
        var slot = body.querySelector("[data-value-slot]");
        var lab = body.querySelector('[data-field="label"]');
        if (slot) slot.innerHTML = valueControl(sel.value);
        if (lab) {
          lab.setAttribute("list", cfg.id + "Suggest");
          var dl = body.querySelector("datalist");
          if (dl) {
            var html = "";
            (suggest[sel.value] || []).forEach(function (w) {
              html += "<option value=\"" + escapeHtml(w) + "\">";
            });
            dl.innerHTML = html;
          }
        }
      });
      aside.addEventListener("change", function (e) {
        var t = e.target;
        if (!t || t.id !== "readmeHostsSelect") return;
        var hsSel = t.value || "";
        hostsEditMode = false;
        loadHosts(hsSel);
      });
      aside.addEventListener("input", function (e) {
        var t = e.target;
        if (!t || t.id !== "readmeCratesQ") return;
        scheduleCratesSearch();
      });
      aside.addEventListener("change", function (e) {
        var t = e.target;
        if (!t || t.id !== "readmeCratesMode") return;
        cratesSearchMode();
        var qNow = cratesSearchQuery();
        if (!qNow) return;
        if (cratesTimer) {
          window.clearTimeout(cratesTimer);
          cratesTimer = null;
        }
        runCratesSearch(qNow);
      });
      aside.addEventListener("keydown", function (e) {
        var t = e.target;
        if (!t || t.id !== "readmeCratesQ") return;
        if (e.key === "Enter") {
          e.preventDefault();
          if (cratesTimer) {
            window.clearTimeout(cratesTimer);
            cratesTimer = null;
          }
          runCratesSearch(t.value);
        } else if (e.key === "Escape") {
          e.preventDefault();
          closeCratesFace();
        }
      });
      bindLibrarianSuggest(aside);
      aside.addEventListener("click", function (e) {
        
        
        var hostsFab = e.target && e.target.closest ? e.target.closest("#readmeHostsFab, .readme-hosts-fab") : null;
        if (hostsFab) {
          e.preventDefault();
          if (letterFace === "hosts") {
            closeHostsFace();
            return;
          }
          openHostsFace();
          return;
        }

        var cratesFab = e.target && e.target.closest ? e.target.closest("#readmeCratesFab, .readme-crates-fab") : null;
        if (cratesFab) {
          e.preventDefault();
          if (letterFace === "crates") {
            closeCratesFace();
            return;
          }
          openCratesFace();
          return;
        }

        var cratesCopyBtn = e.target && e.target.closest ? e.target.closest("[data-crates-copy]") : null;
        if (cratesCopyBtn) {
          e.preventDefault();
          var cCopy = cratesCopyBtn.getAttribute("data-crates-copy") || "";
          copyCratesText(cCopy, "copied " + cCopy);
          return;
        }
        var cratesLinkBtn = e.target && e.target.closest ? e.target.closest("[data-crates-link]") : null;
        if (cratesLinkBtn) {
          e.preventDefault();
          var cLink = cratesLinkBtn.getAttribute("data-crates-link") || "";
          copyCratesText("{{link:" + cLink + "}}", "copied {{link:" + cLink + "}}");
          return;
        }
        var cratesFaceBtn = e.target && e.target.closest ? e.target.closest("[data-crates-face]") : null;
        if (cratesFaceBtn) {
          e.preventDefault();
          var cFace = cratesFaceBtn.getAttribute("data-crates-face") || "";
          copyCratesText("{{face:" + cFace + "}}", "copied {{face:" + cFace + "}}");
          return;
        }

        var helpFab = e.target && e.target.closest ? e.target.closest("#readmeHelpFab") : null;
        if (helpFab) {
          e.preventDefault();
          if (letterFace === "help") {
            closeHelpFace();
            return;
          }
          openHelpFace();
          return;
        }

        var hostsShowBtn = e.target && e.target.closest ? e.target.closest("[data-hosts-show]") : null;
        if (hostsShowBtn) {
          e.preventDefault();
          var curShow = !(hostsBlot && hostsBlot.show === false);
          var slugShow = hostsSlug || (hostsBlot && hostsBlot.host) || "";
          if (!slugShow) return;
          api("PUT", "/api/hosts", { host: slugShow, what: "meta", show: !curShow })
            .then(function (data) {
              hostsBlot = data || hostsBlot;
              if (hostsBlot.host) hostsSlug = hostsBlot.host;
              fillHosts();
              setStatus(hostsBlot.show === false ? "hidden from doors." : "shown on doors.");
              refreshDesk();
            })
            .catch(function (err) {
              setStatus(err.message || "show toggle failed", true);
            });
          return;
        }
        var hostsPinBtn = e.target && e.target.closest ? e.target.closest("[data-hosts-pin]") : null;
        if (hostsPinBtn) {
          e.preventDefault();
          var curPin = hostsBlot && hostsBlot.pin != null && hostsBlot.pin !== "";
          var slugPin = hostsSlug || (hostsBlot && hostsBlot.host) || "";
          if (!slugPin) return;
          var pinBody = { host: slugPin, what: "meta", pin: curPin ? null : true };
          api("PUT", "/api/hosts", pinBody)
            .then(function (data) {
              hostsBlot = data || hostsBlot;
              if (hostsBlot.host) hostsSlug = hostsBlot.host;
              fillHosts();
              setStatus(hostsBlot.pin != null ? "pinned " + hostsBlot.pin + "." : "unpinned.");
              refreshDesk();
            })
            .catch(function (err) {
              setStatus(err.message || "pin toggle failed", true);
            });
          return;
        }
        var hostsDisconnectBtn = e.target && e.target.closest ? e.target.closest("[data-hosts-disconnect]") : null;
        if (hostsDisconnectBtn) {
          e.preventDefault();
          var slugCut = hostsSlug || (hostsBlot && hostsBlot.host) || "";
          if (!slugCut) return;
          api("PUT", "/api/hosts", { host: slugCut, what: "disconnect" })
            .then(function (data) {
              hostsBlot = data || hostsBlot;
              if (hostsBlot.host) hostsSlug = hostsBlot.host;
              else hostsSlug = "";
              fillHosts();
              syncHostsLetterView();
              setStatus("disconnected roam." + slugCut + " (folder kept).");
              render();
              refreshDesk();
            })
            .catch(function (err) {
              setStatus(err.message || "disconnect failed", true);
            });
          return;
        }
        var hostsEditBtn = e.target && e.target.closest ? e.target.closest("[data-hosts-edit]") : null;
        if (hostsEditBtn) {
          e.preventDefault();
          letterFace = "hosts";
          hostsEditMode = true;
          syncHostsLetterView();
          render();
          return;
        }
        var hostsCancelBtn = e.target && e.target.closest ? e.target.closest("[data-hosts-cancel]") : null;
        if (hostsCancelBtn) {
          e.preventDefault();
          hostsEditMode = false;
          fillHosts();
          syncHostsLetterView();
          return;
        }

        var helpEditBtn = e.target && e.target.closest ? e.target.closest("[data-help-edit]") : null;
        if (helpEditBtn) {
          e.preventDefault();
          letterFace = "help";
          helpEditMode = true;
          syncHelpLetterView();
          render();
          return;
        }
        var helpCancelBtn = e.target && e.target.closest ? e.target.closest("[data-help-cancel]") : null;
        if (helpCancelBtn) {
          e.preventDefault();
          helpEditMode = false;
          fillHelp();
          syncHelpLetterView();
          return;
        }
        var helpPageBtn = e.target && e.target.closest ? e.target.closest("[data-help-page]") : null;
        if (helpPageBtn) {
          e.preventDefault();
          var hs = helpPageBtn.getAttribute("data-help-page") || "_index";
          helpEditMode = false;
          loadHelp(hs);
          return;
        }

        var letterEditBtn = e.target && e.target.closest ? e.target.closest("[data-letter-edit]") : null;
        if (letterEditBtn) {
          e.preventDefault();
          letterFace = "room";
          letterEditMode = true;
          render();
          cmPullFromTextareas();
          syncRoomLetterView();
          setStatus("editing letter — Keep to save, Cancel to back out");
          return;
        }
        var letterCancelBtn = e.target && e.target.closest ? e.target.closest("[data-letter-cancel]") : null;
        if (letterCancelBtn) {
          e.preventDefault();
          letterFace = "room";
          letterEditMode = false;
          /* restore editor buffer from last kept body so Cancel does not leave dirty CM */
          var leafEl = $(ids.leaf);
          if (leafEl) {
            leafEl.value = blot.body || "";
            if (leafEl._cm) {
              try {
                leafEl._cm.setValue(leafEl.value);
              } catch (err) {}
            }
          }
          render();
          setStatus("printout");
          return;
        }
        var doorBtn = e.target && e.target.closest ? e.target.closest("[data-readme-door]") : null;
        if (doorBtn) {
          e.preventDefault();
          var door = doorBtn.getAttribute("data-readme-door") || "room";
          if (door === "hosts") {
            openHostsFace();
            return;
          } else if (door === "crates") {
            openCratesFace();
            return;
          } else if (door === "help") {
            openHelpFace();
            return;
          }
          dismissChromeWindows();
          if (door === "room") {
            letterFace = "room";
          } else if (door === "coat" || door === "coat-page") {
            letterFace = "coat";
            letterWhich = door === "coat-page" ? "page" : "shell";
            fillCoat();
          } else {
            letterFace = "page";
            letterWhich = door;
            fillClay();
          }
          render();
          cmPullFromTextareas();
          return;
        }
        var faceBtn = e.target && e.target.closest ? e.target.closest("[data-readme-face]") : null;
        if (faceBtn) {
          e.preventDefault();
          letterFace = faceBtn.getAttribute("data-readme-face") || "room";
          if (letterFace === "page") fillClay();
          render();
          cmPullFromTextareas();
          return;
        }
        var whichBtn = e.target && e.target.closest ? e.target.closest("[data-readme-which]") : null;
        if (whichBtn) {
          e.preventDefault();
          letterFace = "page";
          letterWhich = whichBtn.getAttribute("data-readme-which") || "";
          fillClay();
          render();
          cmPullFromTextareas();
          return;
        }
        var refreshBtn = e.target && e.target.closest ? e.target.closest("[data-refresh]") : null;
        if (refreshBtn) {
          e.preventDefault();
          refreshBlot();
          refreshDesk();
          return;
        }
        var popBtn = e.target && e.target.closest ? e.target.closest("[data-pop]") : null;
        if (popBtn) {
          e.preventDefault();
          popOut();
          return;
        }
        var copyBtn = e.target && e.target.closest ? e.target.closest("[data-copy-crate]") : null;
        if (copyBtn) {
          e.preventDefault();
          copyCrate();
          return;
        }
        var issueBtn = e.target && e.target.closest ? e.target.closest("[data-issue-crate]") : null;
        if (issueBtn) {
          e.preventDefault();
          issueCrate();
          return;
        }
        var newNote = e.target && e.target.closest ? e.target.closest("[data-new-note]") : null;
        if (newNote) {
          e.preventDefault();
          openNewNoteModal();
          return;
        }
        var renameFolder = e.target && e.target.closest ? e.target.closest("[data-rename-folder]") : null;
        if (renameFolder) {
          e.preventDefault();
          openRenameFolderModal();
          return;
        }
        var newFolder = e.target && e.target.closest ? e.target.closest("[data-new-folder]") : null;
        if (newFolder) {
          e.preventDefault();
          openNewFolderModal();
          return;
        }
        var newShell = e.target && e.target.closest ? e.target.closest("[data-new-shell]") : null;
        if (newShell) {
          e.preventDefault();
          openNewShellModal();
          return;
        }
        var newLetter = e.target && e.target.closest ? e.target.closest("[data-new-letter]") : null;
        if (newLetter) {
          e.preventDefault();
          openNewLetterModal();
          return;
        }
        var applyTpl = e.target && e.target.closest ? e.target.closest("[data-apply-template]") : null;
        if (applyTpl) {
          e.preventDefault();
          openApplyTemplateModal();
          return;
        }
        var newHost = e.target && e.target.closest ? e.target.closest("[data-new-host]") : null;
        if (newHost) {
          e.preventDefault();
          openNewHostModal();
          return;
        }
        var newRoam = e.target && e.target.closest ? e.target.closest("[data-new-roam]") : null;
        if (newRoam) {
          e.preventDefault();
          openNewRoamModal();
          return;
        }
        var renameNote = e.target && e.target.closest ? e.target.closest("[data-rename-note]") : null;
        if (renameNote) {
          e.preventDefault();
          openRenameNoteModal();
          return;
        }
        var addStamp = e.target && e.target.closest ? e.target.closest("[data-add-stamp]") : null;
        if (addStamp) {
          e.preventDefault();
          openStampModal();
          return;
        }
        var dropStamp = e.target && e.target.closest ? e.target.closest("[data-drop-stamp]") : null;
        if (dropStamp) {
          e.preventDefault();
          dropStampRow(dropStamp.getAttribute("data-drop-stamp") || "");
          return;
        }
        var ontoBtn = e.target && e.target.closest ? e.target.closest("[data-catalog-onto]") : null;
        if (ontoBtn) {
          e.preventDefault();
          catalogOnto = ontoBtn.getAttribute("data-catalog-onto") || "page";
          render();
          return;
        }
        var addMeta = e.target && e.target.closest ? e.target.closest("[data-add-meta]") : null;
        if (addMeta) {
          e.preventDefault();
          toggleOrOpenCabinet(["meta"], function () {
            openMetaModal();
          });
          return;
        }
        var editMeta = e.target && e.target.closest ? e.target.closest("[data-edit-meta]") : null;
        if (editMeta) {
          e.preventDefault();
          catalogOnto = editMeta.getAttribute("data-onto") || catalogOnto;
          var found = fieldByIndex(editMeta.getAttribute("data-edit-meta"), catalogOnto);
          if (!found) {
            setStatus("no such field", true);
            return;
          }
          openMetaModal(found);
          return;
        }
        var dropMeta = e.target && e.target.closest ? e.target.closest("[data-drop-meta]") : null;
        if (dropMeta) {
          e.preventDefault();
          dropField(dropMeta.getAttribute("data-drop-meta"), dropMeta.getAttribute("data-onto"));
          return;
        }
        var huntOpen = e.target && e.target.closest ? e.target.closest("[data-hunt-open]") : null;
        if (huntOpen) {
          e.preventDefault();
          huntPadShow();
          var openEls = huntPadEls();
          if (openEls.title) openEls.title.focus();
          return;
        }
        var huntCancel = e.target && e.target.closest ? e.target.closest("[data-hunt-cancel]") : null;
        if (huntCancel) {
          e.preventDefault();
          huntPadHide();
          return;
        }
        var addHunt = e.target && e.target.closest ? e.target.closest("[data-add-hunt]") : null;
        if (addHunt) {
          e.preventDefault();
          pinHunt(e);
          return;
        }
        var editHuntBtn = e.target && e.target.closest ? e.target.closest("[data-edit-hunt]") : null;
        if (editHuntBtn) {
          e.preventDefault();
          e.stopPropagation();
          editHunt(editHuntBtn.getAttribute("data-edit-hunt"));
          return;
        }
        var dropHuntBtn = e.target && e.target.closest ? e.target.closest("[data-drop-hunt]") : null;
        if (dropHuntBtn) {
          e.preventDefault();
          e.stopPropagation();
          dropHunt(dropHuntBtn.getAttribute("data-drop-hunt"));
          return;
        }
        var eraOpen = e.target && e.target.closest ? e.target.closest("[data-era-open]") : null;
        if (eraOpen) {
          e.preventDefault();
          eraPadShow();
          var eraOpenEls = eraPadEls();
          if (eraOpenEls.title) eraOpenEls.title.focus();
          return;
        }
        var eraCancel = e.target && e.target.closest ? e.target.closest("[data-era-cancel]") : null;
        if (eraCancel) {
          e.preventDefault();
          eraPadHide();
          return;
        }
        var addEra = e.target && e.target.closest ? e.target.closest("[data-add-era]") : null;
        if (addEra) {
          e.preventDefault();
          pinEra(e);
          return;
        }
        var editEraBtn = e.target && e.target.closest ? e.target.closest("[data-edit-era]") : null;
        if (editEraBtn) {
          e.preventDefault();
          e.stopPropagation();
          editEra(editEraBtn.getAttribute("data-edit-era"));
          return;
        }
        var dropEraBtn = e.target && e.target.closest ? e.target.closest("[data-drop-era]") : null;
        if (dropEraBtn) {
          e.preventDefault();
          e.stopPropagation();
          dropEra(dropEraBtn.getAttribute("data-drop-era"));
          return;
        }
        var addLore = e.target && e.target.closest ? e.target.closest("[data-add-lore]") : null;
        if (addLore) {
          e.preventDefault();
          toggleOrOpenCabinet(["lore"], function () {
            openLoreModal();
          });
          return;
        }
        var popLore = e.target && e.target.closest ? e.target.closest("[data-pop-lore]") : null;
        if (popLore) {
          e.preventDefault();
          var popCrate = popLore.getAttribute("data-pop-lore") || "";
          var look = lookupFromHref("/?card=" + encodeURIComponent(popCrate));
          if (look && launchLookup(look, setStatus)) return;
          setStatus("could not pop", true);
          return;
        }
        var dropLore = e.target && e.target.closest ? e.target.closest("[data-drop-lore]") : null;
        if (dropLore) {
          e.preventDefault();
          e.stopPropagation();
          dropLoreCard(
            dropLore.getAttribute("data-drop-lore"),
            dropLore.getAttribute("data-lore-mouth"),
            dropLore.getAttribute("data-onto")
          );
          return;
        }
        var editLore = e.target && e.target.closest ? e.target.closest("[data-edit-lore]") : null;
        if (editLore) {
          e.preventDefault();
          e.stopPropagation();
          var editCrate = String(editLore.getAttribute("data-edit-lore") || "");
          if (
            cabinetModalOpen(["lore-edit"]) &&
            String(editLoreCrate || "") === editCrate
          ) {
            closeModal();
            hideLibrarianSuggest();
            setStatus("");
            return;
          }
          var card = loreByCrate(editCrate);
          if (!card) {
            setStatus("no such lore", true);
            return;
          }
          openLoreModal(card);
          return;
        }
        var attachLore = e.target && e.target.closest ? e.target.closest("[data-attach-lore]") : null;
        if (attachLore) {
          e.preventDefault();
          toggleOrOpenCabinet(["attach"], function () {
            openAttachModal();
          });
          return;
        }
        var cancel = e.target && e.target.closest ? e.target.closest("[data-modal-cancel]") : null;
        if (cancel) {
          e.preventDefault();
          closeModal();
          return;
        }
        var ok = e.target && e.target.closest ? e.target.closest("[data-modal-ok]") : null;
        if (ok) {
          e.preventDefault();
          confirmModal();
          return;
        }
        var thrBtn = e.target && e.target.closest ? e.target.closest("[data-drop-thread]") : null;
        if (thrBtn) {
          e.preventDefault();
          dropThought(thrBtn.getAttribute("data-drop-thread") || "", "thread");
          return;
        }
        var btn = e.target && e.target.closest ? e.target.closest("[data-drop]") : null;
        if (btn) {
          e.preventDefault();
          dropThought(btn.getAttribute("data-drop") || "");
          return;
        }
        if (cfg.kind === "tags") {
          var count = e.target && e.target.closest ? e.target.closest(".cork-also, .tagbay-count") : null;
          if (count) {
            e.preventDefault();
            var lab = count.closest(".cork-pin, .tagbay-label");
            if (lab) lab.classList.toggle("is-open");
          }
          return;
        }
        if (cfg.kind === "letter" || cfg.kind === "catalog" || cfg.kind === "tps") return;
        var art = e.target && e.target.closest ? e.target.closest(".librarian-thought") : null;
        if (!art || art.classList.contains("is-amending")) return;
        if (e.target && e.target.closest && e.target.closest("textarea")) return;
        startAmend(art.getAttribute("data-id") || "");
      });
    }

    function bindKeys() {
      window.addEventListener(
        "keydown",
        function (e) {
          var key = (e.key || "").toLowerCase();
          // Keep: Ctrl/Cmd+S (restored), Ctrl/Cmd+K, Ctrl/Cmd+Enter.
          // Bound globally so coat CSS / palette focus still Keep.
          // Match Ctrl+E: fire whenever BIOS is open (not only when focus is inside the drawer).
          // Epiphany may still steal Ctrl+S / Ctrl+K; Ctrl+Enter remains the fallback.
          if (
            cfg.kind === "letter" &&
            (e.ctrlKey || e.metaKey) &&
            !e.altKey &&
            !e.shiftKey &&
            (key === "s" || key === "k" || key === "enter")
          ) {
            var modal = $(ids.modal);
            if (modal && !modal.hidden) return;
            if (SIDECAR || open) {
              e.preventDefault();
              e.stopPropagation();
              if (typeof e.stopImmediatePropagation === "function") e.stopImmediatePropagation();
              storeThought();
            }
            return;
          }
          // Ctrl/Cmd+E — open room letter editor (BIOS)
          if (
            cfg.kind === "letter" &&
            (key === "e" || key === "E") &&
            (e.ctrlKey || e.metaKey) &&
            !e.altKey &&
            !e.shiftKey
          ) {
            if (SIDECAR || open) {
              e.preventDefault();
              e.stopPropagation();
              letterFace = "room";
              letterEditMode = true;
              render();
              cmPullFromTextareas();
              syncRoomLetterView();
              setStatus("editing letter — Keep to save, Cancel to back out");
            }
            return;
          }
          if (key !== cfg.hotkey.key) return;
          if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
          if (!!e.shiftKey !== !!cfg.hotkey.shift) return;
          e.preventDefault();
          if (SIDECAR) {
            /* In a sidecar, this house's hotkey dismisses the window.
               Other houses are not mounted here. */
            window.close();
            return;
          }
          /* Desk: dock/toggle the rail (keep BIOS). pop / Ctrl+Shift+O still open windows. */
          toggle();
        },
        true
      );
    }

    mount();
    bindKeys();
    window.addEventListener("focus", function () {
      if (SIDECAR || open) refreshBlot(true);
    });
    followFns.push(function () {
      if (SIDECAR || open) loadBlot();
    });
    render();
    if (SIDECAR) applyOpen(true);

    return { toggle: toggle, applyOpen: applyOpen, popOut: popOut, isOpen: function () { return !!open; } };
  }

  function bootTagbay() {
    if (SIDECAR) return;

    var bay = { key: "", kind: "", open: false, layer: null, title: "", look: null };
    var LOOKUP_SKIN = {
      charlie: "is-tagbay",
      librarian: "is-libbay",
      detective: "is-agentbay",
      agent: "is-agentbay",
      tps: "is-tpsbay",
      crate: "is-cratebay",
    };

    function isFullBayPage() {
      return (
        htmlRoot().getAttribute("data-librarian") === "off" &&
        !!document.querySelector("#browserWindow > .tagbay")
      );
    }

    function lookupFromHash() {
      var h = String(window.location.hash || "").replace(/^#/, "");
      if (!h) return null;
      return lookupFromHref("/?" + h);
    }

    function clearLookupSkin() {
      document.body.classList.remove(
        "is-tagbay",
        "is-libbay",
        "is-agentbay",
        "is-detectivebay",
        "is-tpsbay",
        "is-cratebay"
      );
    }

    function applyLookupSkin(kind) {
      clearLookupSkin();
      document.body.classList.add(LOOKUP_SKIN[kind] || "is-tagbay");
    }

    function ensureBaySkin() {
      if (document.querySelector('link[href="/tagbay.css"]')) return;
      var link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "/tagbay.css";
      document.head.appendChild(link);
    }

    function ensureBayLayer(kind) {
      ensureBaySkin();
      var home =
        kind === "tps" || kind === "crate"
          ? document.querySelector(".wwwExplorer_stage")
          : document.querySelector(".go-shell");
      home = home || document.body;
      if (bay.layer && bay.layer.parentNode !== home) {
        home.appendChild(bay.layer);
        return bay.layer;
      }
      if (bay.layer) return bay.layer;
      var layer = document.createElement("div");
      layer.id = "tagbay-layer";
      layer.hidden = true;
      layer.setAttribute("role", "dialog");
      layer.setAttribute("aria-label", "Lookup");
      home.appendChild(layer);
      bay.layer = layer;
      return layer;
    }

    function paintBayChrome(on) {
      var go = document.getElementById("GO");
      if (!go) return;
      if (on) {
        if (!go.getAttribute("data-go-label")) {
          go.setAttribute("data-go-label", go.textContent || "GO!");
        }
        go.textContent = "DESK";
        go.setAttribute("title", "Back to the page");
        go.classList.add("is-desk");
      } else {
        go.textContent = go.getAttribute("data-go-label") || "GO!";
        go.removeAttribute("title");
        go.classList.remove("is-desk");
      }
    }
    function leaveFullBay() {
      var pin = readDeskPin();
      if (pin && pin.href) {
        window.location.assign(pin.href);
        return;
      }
      if (window.history.length > 1) window.history.back();
      else window.location.assign("/");
    }

    function closeTagbay(opts) {
      opts = opts || {};
      if (!bay.open) return;
      bay.open = false;
      bay.key = "";
      bay.kind = "";
      bay.look = null;
      if (bay.layer) {
        bay.layer.hidden = true;
        bay.layer.innerHTML = "";
      }
      clearLookupSkin();
      paintBayChrome(false);
      if (bay.title) document.title = bay.title;
      if (opts.push !== false) {
        window.history.pushState(
          { tagbay: "" },
          "",
          window.location.pathname + window.location.search
        );
      }
    }

    function openLookup(look, opts) {
      opts = opts || {};
      if (!look || !look.key) return;
      if (isFullBayPage()) {
        window.location.assign(look.href || "/");
        return;
      }
      if (bay.open && bay.key === look.key && opts.toggle !== false) {
        closeTagbay();
        return;
      }
      var layer = ensureBayLayer(look.kind);
      applyLookupSkin(look.kind);
      paintBayChrome(true);
      layer.hidden = false;
      layer.setAttribute(
        "aria-label",
        look.kind === "detective"
          ? "Detective index"
          : look.kind === "librarian"
            ? "Librarian catalog"
            : look.kind === "tps"
              ? "TPS report"
              : look.kind === "crate"
                ? "Crate report"
                : "Charlie lookup"
      );
      bay.open = true;
      bay.key = look.key;
      bay.kind = look.kind;
      if (!bay.title) bay.title = document.title;
      document.title = look.title || look.key;
      layer.innerHTML = '<p class="tagbay-void">looking…</p>';
      var url = look.fetch;
      if (look.kind === "charlie") {
        var standing = vaultPath();
        if (standing) {
          url +=
            (url.indexOf("?") >= 0 ? "&" : "?") +
            "here=" +
            encodeURIComponent(standing);
        }
      }
      fetch(url)
        .then(function (res) {
          return res.text();
        })
        .then(function (html) {
          if (bay.key !== look.key) return;
          layer.innerHTML = html;
        })
        .catch(function () {
          if (bay.key !== look.key) return;
          layer.innerHTML = '<p class="tagbay-void">could not open this lookup.</p>';
        });
      if (opts.push !== false) {
        window.history.pushState(
          { tagbay: look.key },
          "",
          window.location.pathname + window.location.search + look.hash
        );
      }
    }

    function openTagbay(slug) {
      var word = String(slug || "").replace(/^#/, "").trim();
      if (!word) return;
      var dest = "/?h=code.tags&p=" + encodeURIComponent(word.toLowerCase().replace(/\s+/g, "-") + ".md");
      if (SIDECAR && typeof sendDeck === "function") {
        sendDeck(dest);
        return;
      }
      window.location.assign(dest);
    }

    window.openLookup = function (look, opts) {
      if (launchLookup(look)) return;
      openLookup(look, opts);
    };
    window.openTagbay = openTagbay;

    document.addEventListener(
      "click",
      function (e) {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
          return;
        }
        var go = e.target && e.target.closest ? e.target.closest("#GO") : null;
        if (go && (bay.open || isFullBayPage())) {
          e.preventDefault();
          e.stopPropagation();
          if (bay.open) closeTagbay();
          else leaveFullBay();
          return;
        }
        var desk = e.target && e.target.closest ? e.target.closest("[data-tagbay-desk]") : null;
        if (desk) {
          e.preventDefault();
          if (bay.open) closeTagbay();
          else if (isFullBayPage()) leaveFullBay();
          return;
        }
        var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
        if (!a) return;
        if (htmlRoot().hasAttribute("data-sheet") && a.hasAttribute("data-sheet-stay")) {
          e.preventDefault();
          window.location.assign(a.getAttribute("href") || "");
          return;
        }
        var look = lookupFromHref(a.getAttribute("href") || "");
        if (!look) {
          if (htmlRoot().hasAttribute("data-sheet")) {
            e.preventDefault();
            nudgeDesk(a.getAttribute("href") || "");
          }
          return;
        }
        e.preventDefault();
        var sheetKind = htmlRoot().getAttribute("data-sheet") || "";
        if (sheetKind && look.kind === sheetKind) {
          window.location.assign(look.href || "");
          return;
        }
        if (launchLookup(look)) return;
        if (sheetKind) return;
        if (isFullBayPage() && !bay.open) {
          window.location.assign(look.href);
          return;
        }
        if (bay.open && bay.key === look.key) closeTagbay();
        else openLookup(look);
      },
      true
    );

    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (!bay.open) return;
      e.preventDefault();
      closeTagbay();
    });

    window.addEventListener("popstate", function () {
      if (isFullBayPage()) return;
      if (bay.open) closeTagbay({ push: false });
    });

    if (htmlRoot().hasAttribute("data-sheet")) return;
    if (isFullBayPage()) paintBayChrome(true);
  }

  function consumePopHandoff() {
    if (SIDECAR) {
      try {
        sessionStorage.setItem(WINDOW_KEY, "1");
        localStorage.removeItem(POP_KEY);
      } catch (e) {}
      return false;
    }
    if (htmlRoot().hasAttribute("data-sheet") || htmlRoot().getAttribute("data-librarian") === "off") {
      try {
        sessionStorage.setItem(WINDOW_KEY, "1");
      } catch (e) {}
      return false;
    }
    var already = false;
    try {
      already = sessionStorage.getItem(WINDOW_KEY) === "1";
    } catch (e) {}
    if (already) return false;
    var pop = null;
    try {
      pop = JSON.parse(localStorage.getItem(POP_KEY) || "");
      localStorage.removeItem(POP_KEY);
    } catch (e) {
      pop = null;
    }
    try {
      sessionStorage.setItem(WINDOW_KEY, "1");
    } catch (e) {}
    if (!pop || !pop.house) return false;
    if (Date.now() - Number(pop.t || 0) > 8000) return false;
    var ok = false;
    for (var i = 0; i < HOUSES.length; i++) {
      if (HOUSES[i].id === pop.house) ok = true;
    }
    if (!ok) return false;
    window.location.replace("/?sidecar=" + encodeURIComponent(pop.house));
    return true;
  }

  if (consumePopHandoff()) return;

  function popOutAll() {
    HOUSES.forEach(function (cfg) {
      if (!SIDECAR) {
        var shelf = shelves[cfg.id];
        if (shelf && shelf.applyOpen) shelf.applyOpen(false);
      }
      openRail(cfg);
    });
  }

  function bindCabinets() {
    window.addEventListener(
      "keydown",
      function (e) {
        var key = (e.key || "").toLowerCase();
        if (key !== "o") return;
        if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
        if (!e.shiftKey) return;
        e.preventDefault();
        popOutAll();
      },
      true
    );
    if (SIDECAR || !isDesk()) return;
    var extras = window.DECK_ROM_MENU_EXTRAS;
    if (!Array.isArray(extras)) extras = [];
    extras = extras.filter(function (item) {
      if (!item) return false;
      if (item.id === "cabinets" || item.label === "Cabinets") return false;
      var lab = String(item.label || "");
      for (var i = 0; i < HOUSES.length; i++) {
        if (lab === HOUSES[i].menu || lab === HOUSES[i].menu + " · dock") return false;
      }
      return true;
    });
    var mouths = HOUSES.map(function (cfg) {
      return {
        label: cfg.menu,
        items: [
          {
            label: "Window",
            run: function () {
              var shelf = shelves[cfg.id];
              if (shelf && shelf.popOut) shelf.popOut();
            },
          },
          {
            labelFn: function () {
              var shelf = shelves[cfg.id];
              var on = shelf && shelf.isOpen && shelf.isOpen();
              return (on ? "✓ " : "") + "Dock";
            },
            run: function () {
              var shelf = shelves[cfg.id];
              if (shelf && shelf.toggle) shelf.toggle();
            },
          },
        ],
      };
    });
    mouths.push({ sep: true });
    mouths.push({
      label: "All windows",
      run: popOutAll,
    });
    extras.push({
      id: "cabinets",
      label: "Cabinets",
      items: mouths,
    });
    window.DECK_ROM_MENU_EXTRAS = extras;
  }

  function inDeckHost() {
    if (window.pywebview) return true;
    var html = htmlRoot();
    if (html.classList.contains("deck-host-integrated")) return true;
    if (document.getElementById("deck-host-menu")) return true;
    return false;
  }

  function bindMarkRails() {
    if (SIDECAR || !isDesk()) return;
    var btn = document.querySelector("[data-deck-menu]");
    if (!btn) return;
    var menu = document.getElementById("go-rail-menu");
    if (!menu) {
      menu = document.createElement("div");
      menu.id = "go-rail-menu";
      menu.setAttribute("role", "menu");
      menu.setAttribute("hidden", "");
      document.body.appendChild(menu);
    }
    function closeMenu() {
      menu.setAttribute("hidden", "");
      btn.setAttribute("aria-expanded", "false");
    }
    function fillMenu() {
      menu.textContent = "";
      HOUSES.forEach(function (cfg) {
        var shelf = shelves[cfg.id];
        var on = shelf && shelf.isOpen && shelf.isOpen();
        var item = document.createElement("button");
        item.type = "button";
        item.setAttribute("role", "menuitem");
        item.textContent = (on ? "✓ " : "") + cfg.menu;
        item.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          closeMenu();
          if (shelf && shelf.toggle) shelf.toggle();
        });
        menu.appendChild(item);
      });
    }
    function placeMenu() {
      var r = btn.getBoundingClientRect();
      menu.style.top = Math.round(r.bottom + 2) + "px";
      menu.style.left = Math.round(r.left) + "px";
    }
    function toggleMenu() {
      if (!menu.hasAttribute("hidden")) {
        closeMenu();
        return;
      }
      fillMenu();
      placeMenu();
      menu.removeAttribute("hidden");
      btn.setAttribute("aria-expanded", "true");
    }
    btn.setAttribute("aria-haspopup", "true");
    btn.setAttribute("aria-expanded", "false");
    if (!inDeckHost()) {
      btn.title = "Cabinets · dock a rail";
    }
    btn.addEventListener("click", function (e) {
      if (inDeckHost()) return;
      e.preventDefault();
      e.stopPropagation();
      toggleMenu();
    });
    document.addEventListener(
      "click",
      function (e) {
        if (menu.hasAttribute("hidden")) return;
        var t = e.target;
        if (t && t.closest && (t.closest("#go-rail-menu") || t.closest("[data-deck-menu]"))) {
          return;
        }
        closeMenu();
      },
      true
    );
    document.addEventListener("keydown", function (e) {
      if ((e.key || "") === "Escape") closeMenu();
    });
  }

  function bindSheetResize() {
    var html = htmlRoot();
    var sheet = html.hasAttribute("data-sheet");
    var sidecar = SIDECAR || html.getAttribute("data-sidecar") || "";
    var desk = !SIDECAR && typeof isDesk === "function" && isDesk();
    if (!sheet && !sidecar && !desk) return;
    var host = window.pywebview && window.pywebview.api;
    if (!host || !host.resize) return;
    if (document.getElementById("deck-host-resize")) return;
    var grip = document.querySelector(".sheet-resize");
    if (!grip) {
      grip = document.createElement("div");
      grip.className = "sheet-resize";
      grip.setAttribute("aria-label", "Resize");
      document.body.appendChild(grip);
    }
    grip.removeAttribute("hidden");
    var drag = null;
    var minW = sidecar && sidecar !== "readme" && !sheet ? 320 : 480;
    var minH = sidecar === "readme" || desk ? 480 : 420;
    function sizeNow() {
      return {
        w: window.outerWidth || document.documentElement.clientWidth || 640,
        h: window.outerHeight || document.documentElement.clientHeight || 820,
      };
    }
    grip.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      var now = sizeNow();
      drag = { x: e.screenX, y: e.screenY, w: now.w, h: now.h };
      try {
        grip.setPointerCapture(e.pointerId);
      } catch (err) {}
    });
    function applySize(e) {
      if (!drag) return;
      var w = Math.max(minW, Math.round(drag.w + (e.screenX - drag.x)));
      var h = Math.max(minH, Math.round(drag.h + (e.screenY - drag.y)));
      var a = window.pywebview && window.pywebview.api;
      if (a && a.resize) a.resize(w + "x" + h);
    }
    grip.addEventListener("pointermove", applySize);
    grip.addEventListener("pointerup", function () {
      drag = null;
    });
    grip.addEventListener("pointercancel", function () {
      drag = null;
    });
  }

  seedHere();
  var houses = SIDECAR
    ? HOUSES.filter(function (h) {
        return h.id === SIDECAR;
      })
    : HOUSES;
  houses.forEach(function (cfg) {
    shelves[cfg.id] = makeShelf(cfg);
  });
  window.pocketShelves = shelves;
  window.pocketHouses = HOUSES;
  window.pocketAfterSoftNav = function () {
    try {
      publishHere();
    } catch (e) {}
    followFns.forEach(function (fn) {
      try {
        fn();
      } catch (e) {}
    });
  };

  if (!SIDECAR && isDesk()) {
    /* Keep any open rails across page navigations (BIOS + one cabinet). */
    HOUSES.forEach(function (cfg) {
      var want = false;
      try {
        if (sessionStorage.getItem(cfg.openKey) === "1") want = true;
        if (cfg.openKeyLegacy && sessionStorage.getItem(cfg.openKeyLegacy) === "1") want = true;
      } catch (e) {}
      if (want && shelves[cfg.id] && shelves[cfg.id].applyOpen) {
        shelves[cfg.id].applyOpen(true);
      }
    });
  }
  bindCabinets();
  bindMarkRails();
  bootHere();
  bootGoDesk();
  bootTagbay();
  bindSheetResize();
  bindDockRoom();
})();



/* rail-house-switcher */
(function () {
  if (document.documentElement.getAttribute("data-sidecar")) return;
  // Catalog rails + TPS + Deck. BIOS stays a separate window — not in this cycle.
  var RAIL_IDS = ["librarian", "charlie", "detective", "tps", "cards"];

  function getShelves() {
    return window.pocketShelves || null;
  }

  function paintSwitchers() {
    var shelves = getShelves();
    if (!shelves) return;
    RAIL_IDS.forEach(function (id) {
      var aside = document.getElementById(id);
      if (!aside || aside.hasAttribute("hidden")) return;
      var strong =
        aside.querySelector(".librarian-head strong") ||
        aside.querySelector(".charlie-mark") ||
        aside.querySelector(".tps-mark");
      if (!strong) return;
      if (strong.getAttribute("data-rail-switch") === "1") return;
      strong.setAttribute("data-rail-switch", "1");
      strong.title = "Click to switch cabinet (Librarian / Charlie / Detective / TPS / Deck)";
      strong.style.cursor = "pointer";
      strong.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var sh = getShelves();
        if (!sh) return;
        var cur = RAIL_IDS.indexOf(id);
        if (cur < 0) cur = 0;
        var next = RAIL_IDS[(cur + 1) % RAIL_IDS.length];
        RAIL_IDS.forEach(function (hid) {
          if (sh[hid] && sh[hid].applyOpen) sh[hid].applyOpen(false);
        });
        if (sh[next] && sh[next].applyOpen) sh[next].applyOpen(true);
        window.setTimeout(paintSwitchers, 30);
      });
    });
  }

  var obs = new MutationObserver(function () {
    paintSwitchers();
  });

  function boot() {
    var stage = document.querySelector(".wwwExplorer_stage");
    if (stage) {
      obs.observe(stage, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["hidden", "class"],
      });
    }
    var tries = 0;
    (function wait() {
      if (getShelves() || tries > 40) {
        paintSwitchers();
        return;
      }
      tries += 1;
      window.setTimeout(wait, 50);
    })();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
  window.addEventListener("pageshow", function () {
    window.setTimeout(paintSwitchers, 50);
  });
})();
/* /rail-house-switcher */

/* col-resize-grips-js */
(function () {
  if (typeof SIDECAR !== "undefined" && SIDECAR) return;
  var KEY = "pocket-go-col-widths-v1";
  // Catalog rails share one column width (chip-cycle same slot).
  var CATALOG_IDS = { librarian: 1, charlie: 1, detective: 1, agent: 1, tps: 1, cards: 1 };
  var CATALOG_KEY = "catalog-rail";

  function loadMap() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}") || {};
    } catch (e) {
      return {};
    }
  }
  function saveMap(map) {
    try {
      localStorage.setItem(KEY, JSON.stringify(map));
    } catch (e) {}
  }
  function houseId(el) {
    return (el && el.id) || "";
  }
  function widthKey(el) {
    var id = houseId(el);
    if (CATALOG_IDS[id]) return CATALOG_KEY;
    return id;
  }
  function storedWidth(el) {
    var map = loadMap();
    var key = widthKey(el);
    if (!key) return null;
    var w = map[key];
    if (w && isFinite(w)) return w;
    // migrate old per-rail widths into the shared catalog slot
    if (key === CATALOG_KEY) {
      var legacy = ["charlie", "librarian", "detective", "agent", "tps", "cards"];
      for (var i = 0; i < legacy.length; i++) {
        var lw = map[legacy[i]];
        if (lw && isFinite(lw)) return lw;
      }
    }
    return null;
  }
  function applyStored(el) {
    if (document.documentElement.classList.contains("col-resizing")) return;
    var w = storedWidth(el);
    if (!w) return;
    el.style.flexBasis = w + "px";
    el.style.width = w + "px";
  }
  function ensureGrip(el) {
    if (!el || el.querySelector(":scope > .colResize")) return;
    var grip = document.createElement("div");
    grip.className = "colResize";
    grip.title = "Drag to resize";
    grip.setAttribute("aria-hidden", "true");
    el.appendChild(grip);
    var startX = 0;
    var startW = 0;
    function onMove(e) {
      var dx = e.clientX - startX;
      /* grip is on left edge — drag left = wider panel (boundary moves into the page) */
      var next = Math.round(startW - dx);
      var min = el.classList.contains("is-readme") ? 160 : 120;
      var max = el.classList.contains("is-readme") ? 960 : 760;
      if (next < min) next = min;
      if (next > max) next = max;
      el.style.flexBasis = next + "px";
      el.style.width = next + "px";
    }
    function onUp() {
      document.removeEventListener("mousemove", onMove, true);
      document.removeEventListener("mouseup", onUp, true);
      grip.classList.remove("is-dragging");
      document.documentElement.classList.remove("col-resizing");
      var key = widthKey(el);
      if (!key) return;
      var map = loadMap();
      var w = Math.round(el.getBoundingClientRect().width);
      map[key] = w;
      if (key === CATALOG_KEY) {
        // keep legacy keys in sync so old code / stale maps don't fight
        map.charlie = w;
        map.librarian = w;
        map.agent = w;
        map.tps = w;
        map.cards = w;
      }
      saveMap(map);
    }
    grip.addEventListener("mousedown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      e.stopPropagation();
      startX = e.clientX;
      startW = el.getBoundingClientRect().width;
      grip.classList.add("is-dragging");
      document.documentElement.classList.add("col-resizing");
      document.addEventListener("mousemove", onMove, true);
      document.addEventListener("mouseup", onUp, true);
    });
  }
  function sync() {
    var stage = document.querySelector(".wwwExplorer_stage");
    if (!stage) return;
    stage.querySelectorAll(":scope > .librarian").forEach(function (el) {
      if (el.hasAttribute("hidden")) return;
      applyStored(el);
      ensureGrip(el);
    });
  }
  var obs = new MutationObserver(function () {
    if (document.documentElement.classList.contains("col-resizing")) return;
    sync();
  });
  function boot() {
    var stage = document.querySelector(".wwwExplorer_stage");
    if (stage) {
      // Do NOT observe style — applyStored writes style and that re-fired sync,
      // which slammed the saved width back mid-drag (one-shot resize bug).
      obs.observe(stage, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["hidden", "class"],
      });
    }
    sync();
    window.addEventListener("pageshow", sync);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
/* /col-resize-grips-js */

/* pocket-pic-zoom — full-size image stays inside the pocket / sidecar */
(function () {
  var layer = null;
  var pic = null;
  var scale = 1;

  function closePic() {
    if (!layer) return;
    scale = 1;
    if (pic) {
      pic.style.transform = "";
      pic.removeAttribute("src");
    }
    layer.setAttribute("hidden", "");
    document.documentElement.classList.remove("pocket-pic-open");
  }

  function openPic(src, alt) {
    src = String(src || "").trim();
    if (!src) return;
    if (!layer) {
      layer = document.createElement("div");
      layer.className = "pocket-pic-zoom";
      layer.setAttribute("hidden", "");
      layer.setAttribute("role", "dialog");
      layer.setAttribute("aria-modal", "true");
      layer.setAttribute("aria-label", "picture");
      layer.innerHTML =
        '<button type="button" class="pocket-pic-zoom-x" aria-label="close picture">×</button>' +
        '<img class="pocket-pic-zoom-img" alt="">';
      document.body.appendChild(layer);
      pic = layer.querySelector(".pocket-pic-zoom-img");
      layer.addEventListener("click", function () {
        closePic();
      });
      layer.addEventListener(
        "wheel",
        function (e) {
          if (layer.hasAttribute("hidden")) return;
          e.preventDefault();
          var next = scale * (e.deltaY < 0 ? 1.12 : 0.9);
          scale = Math.min(8, Math.max(1, next));
          if (pic) pic.style.transform = scale === 1 ? "" : "scale(" + scale + ")";
        },
        { passive: false }
      );
    }
    scale = 1;
    pic.style.transform = "";
    pic.alt = String(alt || "");
    pic.src = src;
    layer.removeAttribute("hidden");
    document.documentElement.classList.add("pocket-pic-open");
  }

  function isPicHref(raw) {
    try {
      var path = new URL(String(raw || ""), window.location.href).pathname || "";
      if (path.indexOf("/i/") === 0) return true;
      return /\.(gif|png|jpe?g|webp|svg|bmp|ico)$/i.test(path);
    } catch (e) {
      return false;
    }
  }

  window.openPocketPic = openPic;
  window.closePocketPic = closePic;

  document.addEventListener(
    "click",
    function (e) {
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var t = e.target;
      if (!t || !t.closest) return;
      if (t.closest(".pocket-pic-zoom")) return;
      if (t.closest("ul.dir a.has-cover")) return;
      if (t.closest("a.outlink, a[data-outlink], [data-rom]")) return;

      var src = "";
      var alt = "";
      var zoom = t.closest("a.pic-zoom, a.jacket-zoom");
      if (zoom) {
        src = zoom.getAttribute("href") || "";
        var nested = zoom.querySelector("img");
        alt = (nested && nested.getAttribute("alt")) || "";
      } else {
        var slide = t.closest("img.slides-pic");
        if (slide) {
          src = slide.getAttribute("src") || "";
          alt = slide.getAttribute("alt") || "";
        } else {
          var img = t.closest("img.pic");
          if (img) {
            var wrap = img.closest("a[href]");
            if (wrap && isPicHref(wrap.getAttribute("href"))) {
              src = wrap.getAttribute("href") || img.getAttribute("src") || "";
              alt = img.getAttribute("alt") || "";
            } else if (!wrap) {
              src = img.getAttribute("src") || "";
              alt = img.getAttribute("alt") || "";
            }
          }
        }
      }
      if (!src) {
        var link = t.closest("a[href]");
        if (link && isPicHref(link.getAttribute("href"))) {
          src = link.getAttribute("href") || "";
        }
      }
      if (!src) return;
      e.preventDefault();
      openPic(src, alt);
    },
    true
  );

  document.addEventListener(
    "keydown",
    function (e) {
      if (e.key !== "Escape") return;
      if (!document.documentElement.classList.contains("pocket-pic-open")) return;
      e.preventDefault();
      closePic();
    },
    true
  );
})();
/* /pocket-pic-zoom */

