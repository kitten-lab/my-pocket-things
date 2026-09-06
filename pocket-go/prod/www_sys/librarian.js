/**
 * Pocket Go shelves — README, Librarian, Charlie (weaver), Agent, TPS.
 * Independent drawers. README is one letter, not slips.
 * Ctrl+Shift+L readme · Ctrl+Shift+B librarian · Ctrl+Shift+C charlie · Ctrl+Shift+A agent · Ctrl+Shift+T tps · Ctrl+Shift+D cards.
 * Ctrl+Shift+O opens all cabinets as windows.
 * Gem: Cabinets → mouth → Window or Dock. Dock again puts the overlay away.
 * Window / hotkey opens a sidecar that follows the desk's page.
 * Charlie / Librarian / Agent / TPS / crate lookup opens a Pocket Go window.
 * Lookup windows are not a here — cabinets stay on the desk.
 */
(function () {
  var SIGIL = /(^|[^A-Za-z0-9._:/-])([#$^@])([A-Za-z0-9._:/-]+)/g;
  var CHIP = { "#": "tag", $: "ns", "@": "time", "^": "cite" };

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
      menu: "README",
      title: "README",
      kicker: "THIS ROOM",
      placeholder: "how we use this space.",
      empty: "Nothing in the letter yet.",
      issue: "Keep",
      slips: ["letter", "letter"],
      hotkey: { key: "l", shift: true },
      skin: "is-readme",
      kind: "letter",
      pop: { w: 440, h: 760 },
    },
    {
      id: "librarian",
      api: "/api/librarian",
      openKey: "pocket-go-librarian-open",
      bodyClass: "librarian-open",
      menu: "Librarian",
      title: "LIBRARIAN",
      kicker: "CATALOG",
      placeholder: "",
      empty: "No fields on this bag yet. Add meta data or lore.",
      issue: "Confirm",
      slips: ["field", "fields"],
      hotkey: { key: "b", shift: true },
      skin: "is-catalog",
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
      kicker: "TERM",
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
      id: "agent",
      api: "/api/agent",
      openKey: "pocket-go-agent-open",
      bodyClass: "agent-open",
      menu: "Agent",
      title: "AGENT",
      kicker: "INDEX",
      placeholder: "",
      empty: "No index on this bag yet. Add meta data or lore.",
      issue: "Confirm",
      slips: ["field", "fields"],
      hotkey: { key: "a", shift: true },
      skin: "is-catalog is-agent",
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
      kicker: "REPORT",
      placeholder: "",
      empty: "No dates or lore on this report yet. Add a dated stamp or lore.",
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
      empty: "No lore cards on this page yet.",
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
    q = String(q).toLowerCase();
    for (var i = 0; i < HOUSES.length; i++) {
      if (HOUSES[i].id === q) return q;
    }
    return "";
  })();

  var HERE_KEY = "pocket-go-here";
  var DESK_KEY = "pocket-go-desk";
  var POP_KEY = "pocket-go-pop";
  var WINDOW_KEY = "pocket-go-window";
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
    Object.keys(shelves).forEach(function (sid) {
      if (sid === id) return;
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
    if (window.opener && !window.opener.closed) {
      try {
        window.opener.location.href = href;
        return;
      } catch (e) {}
    }
    if (hereChannel) {
      try {
        hereChannel.postMessage({ type: "go", href: href });
      } catch (e) {}
    }
  }
  window.nudgeDesk = nudgeDesk;

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
          fetch: "/?c=" + encodeURIComponent(c) + "&bay=1" + extra,
          href: "/?c=" + encodeURIComponent(c) + extra,
        };
      }
      var m = String(u.searchParams.get("m") || "librarian")
        .trim()
        .toLowerCase();
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
      if (m !== "librarian" && m !== "agent") return null;
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
    if (el) el.textContent = label + " · " + path;
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
      if (window.opener && !window.opener.closed) {
        try {
          window.opener.location.href = href;
          return;
        } catch (e) {}
      }
      if (hereChannel) {
        try {
          hereChannel.postMessage({ type: "go", href: href });
        } catch (e) {}
      }
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
    var open = false;
    var suggest = { time: [], bool: [], input: [], textbox: [], class: [] };
    var modalMode = "";
    var editIndex = -1;
    var editLoreCrate = "";
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
    };
    var letterFace = "room";
    var letterWhich = "";
    var catalogOnto = "page";

    function clayPages() {
      if (blot.page && blot.page.pages && blot.page.pages.length) return blot.page.pages;
      return blot.page ? [blot.page] : [];
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

    function ontoLabel() {
      if (catalogOnto === "shell" && blot.shell) return "the shell";
      return "this page";
    }

    function ontoCrate() {
      if (catalogOnto === "shell" && blot.shell) return blot.shell.crate || "";
      return blot.crate || "";
    }

    function fillClay() {
      var clay = currentClay();
      var head = $(ids.headers);
      var md = $(ids.markdown);
      if (head) head.value = (clay && clay.headers) || "";
      if (md) md.value = (clay && clay.markdown) || "";
    }

    function setStatus(msg, isErr) {
      var el = $(ids.status);
      if (!el) return;
      el.textContent = msg || "";
      el.classList.toggle("is-err", !!isErr);
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
      if (pathEl) pathEl.textContent = off ? "no blotter on this page" : pocket;
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
          if (crateId) {
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
          if (blot.shell) {
            ontoBar.removeAttribute("hidden");
            var btns = ontoBar.querySelectorAll("[data-catalog-onto]");
            for (var bi = 0; bi < btns.length; bi++) {
              btns[bi].classList.toggle(
                "is-on",
                btns[bi].getAttribute("data-catalog-onto") === catalogOnto
              );
            }
          } else {
            ontoBar.setAttribute("hidden", "");
            catalogOnto = "page";
          }
        }
      }
      var n =
        cfg.kind === "catalog"
          ? (blot.fields || []).length +
            (blot.shell && blot.shell.fields ? blot.shell.fields.length : 0)
          : cfg.kind === "tps"
          ? (blot.stamps || []).length
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
        else countEl.textContent = n + " " + unit;
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
        if (roomPane) roomPane.hidden = letterFace !== "room";
        if (pagePane) pagePane.hidden = letterFace !== "page";
        var tabs = drawer.querySelectorAll("[data-readme-face]");
        for (var t = 0; t < tabs.length; t++) {
          tabs[t].classList.toggle(
            "is-on",
            tabs[t].getAttribute("data-readme-face") === letterFace
          );
        }
        var kick = drawer.querySelector(".librarian-kicker");
        if (kick) {
          if (letterFace === "page") {
            var clay = currentClay();
            kick.textContent =
              "THIS PAGE" +
              (clay && clay.file ? " · " + clay.file : "");
          } else {
            kick.textContent = "THIS ROOM";
          }
        }
        var clayBox = $("readmeClayTabs");
        if (clayBox) {
          var pages = clayPages();
          if (letterFace !== "page" || pages.length < 2) {
            clayBox.innerHTML = "";
            clayBox.hidden = true;
          } else {
            if (!letterWhich) letterWhich = pages[0].kind || "";
            var html = "";
            pages.forEach(function (p) {
              html +=
                '<button type="button" class="readme-tab' +
                (p.kind === letterWhich ? " is-on" : "") +
                '" data-readme-which="' +
                escapeHtml(p.kind || "") +
                '">' +
                escapeHtml(p.kind || p.file || "") +
                "</button>";
            });
            clayBox.innerHTML = html;
            clayBox.hidden = false;
          }
        }
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
              '<a class="cork-pin cork-hash-pin" href="/?c=' +
              encodeURIComponent(h.id || name) +
              '&as=hash">' +
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

    function loreBlockHtml(lore) {
      lore = lore || [];
      if (!lore.length) return "";
      var html = '<div class="catalog-block"><div class="catalog-head">lore</div>';
      lore.forEach(function (card) {
        var crate = card.crate || "";
        html +=
          '<div class="catalog-lore-row">' +
          '<a class="catalog-lore" href="' +
          escapeHtml(card.href || "#") +
          '"><strong>' +
          escapeHtml(card.title || card.file || "lore") +
          "</strong>" +
          (function () {
            var chips = [];
            if (card.class) chips.push('<span class="catalog-type">' + escapeHtml(card.class) + '</span>');
            if (card.maker) chips.push('<span class="catalog-type">' + escapeHtml(card.maker) + '</span>');
            else if (card.house) chips.push('<span class="catalog-type">' + escapeHtml(card.house) + '</span>');
            var out = chips.length ? '<span class="catalog-chips">' + chips.join(' ') + '</span>' : '';
            if (card.line) out += '<span class="catalog-line">' + escapeHtml(card.line) + '</span>';
            return out;
          })() +
          "</a>" +
          (crate
            ? '<span class="catalog-tools">' +
              '<button type="button" class="catalog-pop" data-pop-lore="' +
              escapeHtml(crate) +
              '" title="pop">pop</button>' +
              '<button type="button" class="catalog-edit" data-edit-lore="' +
              escapeHtml(crate) +
              '" title="edit">edit</button></span>'
            : "") +
          "</div>";
      });
      html += "</div>";
      return html;
    }

    function loreByCrate(crate) {
      return loreByCrateFrom(crate);
    }

    function catalogBagHtml(bag, onto, title) {
      bag = bag || {};
      var fields = bag.fields || [];
      var lore = bag.lore || [];
      if (!fields.length && !lore.length) return "";
      var html = '<div class="catalog-bag is-' + onto + (catalogOnto === onto ? " is-on" : "") + '">';
      html += '<div class="catalog-head">' + escapeHtml(title);
      if (bag.crate) {
        html +=
          ' <a class="tagbay-crate-id" href="/?k=' +
          encodeURIComponent(bag.crate) +
          '">' +
          escapeHtml(bag.crate) +
          "</a>";
      }
      html += "</div>";
      if (fields.length) {
        html += '<div class="catalog-block"><div class="catalog-head">meta</div>';
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
        html += loreBlockHtml(lore);
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
        if (
          e.target.closest &&
          e.target.closest("a, button, input, textarea, select")
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
      var pageHtml = catalogBagHtml(blot, "page", "this page");
      var shellHtml = blot.shell ? catalogBagHtml(blot.shell, "shell", "the shell") : "";
      if (!pageHtml && !shellHtml) {
        stack.innerHTML = '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
        return;
      }
      stack.innerHTML = shellHtml + pageHtml;
    }

    function renderTps(stack) {
      var stamps = blot.stamps || [];
      var slices = blot.slices || {};
      var lore = blot.lore || [];
      if (!stamps.length && !lore.length) {
        stack.innerHTML = '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
        return;
      }
      var html = loreBlockHtml(lore);
      if (!stamps.length) {
        stack.innerHTML = html || '<p class="librarian-empty">' + escapeHtml(cfg.empty) + "</p>";
        return;
      }
      html += '<div class="catalog-block tps-dates"><div class="catalog-head">dates</div>';
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
          '<div class="catalog-block tps-bins"><div class="catalog-head">slices</div>' +
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
      if (librarianOff()) {
        blot =
          cfg.kind === "letter"
            ? { body: "", pocket: "", crate: "", route: "" }
            : cfg.kind === "catalog"
            ? { fields: [], lore: [], pocket: "", crate: "" }
            : cfg.kind === "tps"
            ? { stamps: [], slices: {}, pocket: "", crate: "" }
            : cfg.kind === "cards"
            ? { cards: [], html: "", pocket: "", crate: "" }
            : { thoughts: [], lore: [], pocket: "", next: 1, crate: "" };
        render();
        return;
      }
      var p = vaultPath();
      api("GET", cfg.api + "?p=" + encodeURIComponent(p))
        .then(function (data) {
          blot = data || blot;
          render();
          if (cfg.kind === "letter") {
            var el = $(ids.leaf);
            if (el) el.value = blot.body || "";
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
        if (letterFace === "page") {
          var head = $(ids.headers);
          var md = $(ids.markdown);
          api("PUT", cfg.api, {
            pocket: vaultPath(),
            what: "page",
            which: (currentClay() && currentClay().kind) || letterWhich || "",
            headers: head ? head.value : "",
            markdown: md ? md.value : "",
          })
            .then(function (data) {
              blot = data || blot;
              render();
              setStatus("kept page");
              if (!SIDECAR) {
                window.setTimeout(function () {
                  window.location.reload();
                }, 80);
              }
            })
            .catch(function (err) {
              setStatus(err.message || "could not keep page", true);
            });
          return;
        }
        api("PUT", cfg.api, { pocket: vaultPath(), body: leaf })
          .then(function (data) {
            blot = data || blot;
            render();
            setStatus("kept");
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

    function copyCrate() {
      var c = blot.crate || "";
      if (cfg.kind === "letter" && letterFace === "page") {
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

    function goHref(href) {
      href = String(href || "").trim();
      if (!href) return;
      if (SIDECAR) sendDeck(href);
      else window.location.assign(href);
    }

    function closeModal() {
      modalMode = "";
      editIndex = -1;
      editLoreCrate = "";
      var modal = $(ids.modal);
      if (modal) modal.setAttribute("hidden", "");
    }

    function datalistFor(kind) {
      var id = cfg.id + "Suggest";
      var words = suggest[kind] || [];
      var html = '<datalist id="' + id + '">';
      words.forEach(function (w) {
        html += "<option value=\"" + escapeHtml(w) + "\">";
      });
      return html + "</datalist>";
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
      loadSuggest().then(function () {
        modalMode = field ? "meta-edit" : "meta";
        editIndex = field && field.i != null ? Number(field.i) : -1;
        var titleEl = $(ids.modalTitle);
        var body = $(ids.modalBody);
        var modal = $(ids.modal);
        if (!titleEl || !body || !modal) return;
        titleEl.textContent = field ? "Edit Meta Data" : "Add Meta Data";
        var kind = String((field && field.type) || "input");
        body.innerHTML =
          '<label>type</label>' +
          '<select data-field="type">' +
          '<option value="time">time</option>' +
          '<option value="bool">bool</option>' +
          '<option value="input">input</option>' +
          '<option value="textbox">textbox</option>' +
          "</select>" +
          '<label>label</label>' +
          '<input data-field="label" class="librarian-leaf tagbay-input" list="' +
          cfg.id +
          'Suggest" placeholder="' +
          escapeHtml(cfg.metaHint || "e.g. author") +
          '">' +
          datalistFor(kind) +
          '<label>value</label>' +
          '<div data-value-slot>' +
          valueControl(kind) +
          "</div>";
        fillMetaForm(body, field);
        modal.removeAttribute("hidden");
        var lab = body.querySelector('[data-field="label"]');
        if (lab) lab.focus();
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
        titleEl.textContent = "Add date";
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

    function openLoreModal(card) {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        loadBlot();
        loadSuggest().then(function () {
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
            '<label>class</label>' +
            '<input data-field="class" class="librarian-leaf tagbay-input" list="' +
            cfg.id +
            'Suggest" placeholder="' +
            escapeHtml(cfg.loreClassHint || "e.g. recovered") +
            '">' +
            datalistFor("class") +
            '<label>maker <em>(corner — blank = ' +
            escapeHtml(cfg.defaultMaker || "this cabinet") +
            ')</em></label>' +
            '<input data-field="maker" class="librarian-leaf tagbay-input" placeholder="' +
            escapeHtml(cfg.defaultMaker || "Teehee, Agent K, SAM.exe…") +
            '">' +
            '<label>lore title</label>' +
            '<input data-field="title" class="librarian-leaf tagbay-input" placeholder="names the file">' +
            '<label>lore line</label>' +
            '<textarea data-field="line" class="librarian-leaf" rows="3" maxlength="255" placeholder="255 characters"></textarea>' +
            '<label>time</label>' +
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
          modal.removeAttribute("hidden");
          var first = body.querySelector(editing ? '[data-field="title"]' : '[data-field="class"]');
          if (first) first.focus();
        });
      });
    }

    function openAttachModal() {
      if (librarianOff()) return;
      withFreshVault(function () {
        if (librarianOff()) return;
        api("GET", cfg.api + "?p=" + encodeURIComponent(vaultPath()))
          .then(function (blotData) {
            blot = blotData || blot;
            return api("GET", cfg.api + "/lore");
          })
          .then(function (data) {
            modalMode = "attach";
            var titleEl = $(ids.modalTitle);
            var body = $(ids.modalBody);
            var modal = $(ids.modal);
            if (!titleEl || !body || !modal) return;
            titleEl.textContent = "Attach Lore";
            var here = ontoCrate();
            var cards = (data && data.cards) || [];
            var html =
              '<p class="librarian-onto">onto ' +
              escapeHtml(ontoLabel()) +
              "</p>";
            if (!cards.length) {
              html +=
                '<p class="librarian-empty">no lore in this house yet. Add Lore first.</p>';
            } else {
              cards.forEach(function (card) {
                var edges = card.edges || [];
                var on = false;
                if (here) {
                  for (var i = 0; i < edges.length; i++) {
                    if (edges[i] === here) on = true;
                  }
                }
                html +=
                  '<label class="lore-pick' +
                  (on ? " is-on" : "") +
                  '"><input type="radio" name="lore-pick" data-field="card" value="' +
                  escapeHtml(card.crate || "") +
                  '"' +
                  (on ? " disabled" : "") +
                  "><strong>" +
                  escapeHtml(card.title || card.file || "lore") +
                  "</strong>" +
                  (card.class
                    ? "<em>" + escapeHtml(card.class) + "</em>"
                    : "") +
                  (card.line
                    ? '<span class="catalog-line">' +
                      escapeHtml(card.line) +
                      "</span>"
                    : "") +
                  (on
                    ? '<span class="catalog-type">already touching</span>'
                    : "") +
                  "</label>";
              });
            }
            body.innerHTML = html;
            modal.removeAttribute("hidden");
          })
          .catch(function (err) {
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
              setStatus("opened " + ((data && data.file) || name));
              goHref(data && data.href);
            })
            .catch(function (err) {
              setStatus(err.message || "could not make page", true);
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
        var picked = body.querySelector('[data-field="card"]:checked:not([disabled])');
        var cardCrate = picked ? String(picked.value || "").trim() : "";
        if (!cardCrate) {
          setStatus("pick a card to attach", true);
          return;
        }
        withFreshVault(function (pocket) {
          if (librarianOff()) return;
          api("POST", cfg.api + "/lore/attach", {
            pocket: pocket,
            crate: cardCrate,
            onto: catalogOnto,
          })
            .then(function (data) {
              blot = data || blot;
              closeModal();
              render();
              setStatus(
                data && data.attached === false
                  ? "already touching"
                  : "attached " + (data && data.file ? data.file : "lore")
              );
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
            '<p class="librarian-hint">view only — lore cards on this page</p>' +
            '<p class="librarian-status" id="' +
            ids.status +
            '"></p></div>'
          : cfg.kind === "catalog" || cfg.kind === "tps"
          ? '<div class="librarian-composer" id="' +
            ids.composer +
            '">' +
            '<div class="librarian-kicker">' +
            escapeHtml(cfg.kicker) +
            "</div>" +
            (cfg.kind === "catalog"
              ? '<div class="catalog-onto" hidden>' +
                '<button type="button" class="catalog-onto-btn" data-catalog-onto="shell">shell</button>' +
                '<button type="button" class="catalog-onto-btn is-on" data-catalog-onto="page">this page</button>' +
                "</div>"
              : "") +
            '<div class="catalog-actions">' +
            (cfg.kind === "tps"
              ? '<button type="button" class="librarian-store" data-add-stamp>Add date</button>' +
                '<button type="button" class="librarian-store" data-add-lore>Add Lore</button>' +
                '<button type="button" class="librarian-store" data-attach-lore>Attach Lore</button>'
              : '<button type="button" class="librarian-store" data-add-meta>Add Meta Data</button>' +
                '<button type="button" class="librarian-store" data-add-lore>Add Lore</button>' +
                '<button type="button" class="librarian-store" data-attach-lore>Attach Lore</button>') +
            "</div>" +
            '<p class="librarian-status" id="' +
            ids.status +
            '"></p></div>' +
            modalHtml
          : '<form class="librarian-composer" id="' +
            ids.composer +
            '" autocomplete="off">' +
            '<div class="librarian-kicker">' +
            escapeHtml(cfg.kicker) +
            "</div>" +
            (cfg.kind === "tags"
              ? '<div class="charlie-tri">' +
                '<label class="charlie-slot">from' +
                '<input id="' +
                ids.leaf +
                '" class="librarian-leaf tagbay-input" type="text" autocomplete="off">' +
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
                "</div>"
              : cfg.kind === "letter"
              ? '<div class="readme-tabs">' +
                '<button type="button" class="readme-tab is-on" data-readme-face="room">room</button>' +
                '<button type="button" class="readme-tab" data-readme-face="page">page</button>' +
                "</div>" +
                '<div id="readmeRoom">' +
                '<textarea id="' +
                ids.leaf +
                '" class="librarian-leaf librarian-letter" rows="18" placeholder="' +
                escapeHtml(cfg.placeholder) +
                '"></textarea>' +
                "</div>" +
                '<div id="readmePage" hidden>' +
                '<div id="readmeClayTabs" class="readme-tabs readme-clay-tabs" hidden></div>' +
                "<label>headers</label>" +
                '<textarea id="' +
                ids.headers +
                '" class="librarian-leaf readme-headers" rows="8" placeholder="yaml front matter"></textarea>' +
                "<label>markdown</label>" +
                '<textarea id="' +
                ids.markdown +
                '" class="librarian-leaf librarian-letter" rows="12" placeholder="the page body"></textarea>' +
                "</div>"
              : '<textarea id="' +
                ids.leaf +
                '" class="librarian-leaf" rows="4" placeholder="' +
                escapeHtml(cfg.placeholder) +
                '"></textarea>') +
            '<div class="librarian-actions">' +
            '<button type="submit" class="librarian-store">' +
            escapeHtml(cfg.issue) +
            "</button>" +
            (cfg.kind === "letter"
              ? '<button type="button" class="librarian-store" data-new-note>New</button>'
              : "") +
            (cfg.lore
              ? '<button type="button" class="librarian-store" data-add-lore>Add Lore</button>' +
                '<button type="button" class="librarian-store" data-attach-lore>Attach Lore</button>'
              : "") +
            '<span class="librarian-hint">' +
            (cfg.kind === "tags" ? "Enter" : cfg.kind === "letter" ? "Ctrl+S" : "Ctrl+Enter") +
            "</span>" +
            "</div>" +
            '<p class="librarian-status" id="' +
            ids.status +
            '"></p>' +
            "</form>" +
            (cfg.lore || cfg.kind === "letter" ? modalHtml : "");
      aside.innerHTML =
        '<div class="librarian-head"><strong>' +
        escapeHtml(cfg.title) +
        '</strong><span class="librarian-count" id="' +
        ids.count +
        '"></span>' +
        '<button type="button" class="tagbay-copy" data-refresh title="Refresh this cabinet now">refresh</button>' +
        (SIDECAR
          ? ""
          : '<button type="button" class="librarian-pop" data-pop title="Open as a window">pop</button>') +
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
        if (cfg.kind === "letter" && (k === "s" || k === "S")) return true;
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
      aside.addEventListener("click", function (e) {
        var faceBtn = e.target && e.target.closest ? e.target.closest("[data-readme-face]") : null;
        if (faceBtn) {
          e.preventDefault();
          letterFace = faceBtn.getAttribute("data-readme-face") || "room";
          if (letterFace === "page") fillClay();
          render();
          return;
        }
        var whichBtn = e.target && e.target.closest ? e.target.closest("[data-readme-which]") : null;
        if (whichBtn) {
          e.preventDefault();
          letterWhich = whichBtn.getAttribute("data-readme-which") || "";
          fillClay();
          render();
          return;
        }
        var refreshBtn = e.target && e.target.closest ? e.target.closest("[data-refresh]") : null;
        if (refreshBtn) {
          e.preventDefault();
          refreshBlot();
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
          openMetaModal();
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
        var addLore = e.target && e.target.closest ? e.target.closest("[data-add-lore]") : null;
        if (addLore) {
          e.preventDefault();
          openLoreModal();
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
        var editLore = e.target && e.target.closest ? e.target.closest("[data-edit-lore]") : null;
        if (editLore) {
          e.preventDefault();
          var card = loreByCrate(editLore.getAttribute("data-edit-lore"));
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
          openAttachModal();
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
          if (
            cfg.kind === "letter" &&
            key === "s" &&
            (e.ctrlKey || e.metaKey) &&
            !e.altKey &&
            !e.shiftKey
          ) {
            var modal = $(ids.modal);
            if (modal && !modal.hidden) return;
            var drawer = $(ids.drawer);
            var inDrawer = drawer && drawer.contains(e.target);
            if (SIDECAR || (open && inDrawer)) {
              e.preventDefault();
              e.stopPropagation();
              storeThought();
            }
            return;
          }
          if (key !== cfg.hotkey.key) return;
          if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
          if (!!e.shiftKey !== !!cfg.hotkey.shift) return;
          e.preventDefault();
          if (SIDECAR) {
            window.close();
            return;
          }
          popOut();
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
          : document.querySelector(".wwwExplorer_innerShell");
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
        look.kind === "agent"
          ? "Agent index"
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
      var look = lookupFromHref(
        "/?c=" + encodeURIComponent(String(slug || "").replace(/^#/, ""))
      );
      if (launchLookup(look)) return;
      openLookup(look);
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

  function bindSheetResize() {
    var html = htmlRoot();
    var sheet = html.hasAttribute("data-sheet");
    var readmePop =
      SIDECAR === "readme" || html.getAttribute("data-sidecar") === "readme";
    if (!sheet && !readmePop) return;
    var grip = document.querySelector(".sheet-resize");
    if (!grip) {
      grip = document.createElement("div");
      grip.className = "sheet-resize";
      grip.setAttribute("aria-label", "Resize");
      document.body.appendChild(grip);
    }
    grip.removeAttribute("hidden");
    var drag = null;
    var minW = 360;
    var minH = readmePop ? 480 : 420;
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
  if (!SIDECAR && isDesk()) {
    var dock = dockWanted();
    if (dock && shelves[dock] && shelves[dock].applyOpen) {
      shelves[dock].applyOpen(true);
    }
  }
  bindCabinets();
  bootHere();
  bootTagbay();
  bindSheetResize();
  bindDockRoom();
})();
