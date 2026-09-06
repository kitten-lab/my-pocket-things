/* PocketGo Obsidian .canvas viewer — pan / zoom / fit (read-only) */
(function () {
  "use strict";

  var COLOR_IDS = {
    "1": "color-1",
    "2": "color-2",
    "3": "color-3",
    "4": "color-4",
    "5": "color-5",
    "6": "color-6"
  };

  function loadData() {
    var el = document.getElementById("canvas-data");
    if (!el) return { nodes: [], edges: [] };
    try {
      return JSON.parse(el.textContent || "{}");
    } catch (e) {
      console.warn("canvas-data parse failed", e);
      return { nodes: [], edges: [] };
    }
  }

  function colorClass(color) {
    if (color == null || color === "") return "";
    var s = String(color);
    if (COLOR_IDS[s]) return COLOR_IDS[s];
    return "";
  }

  function colorStyle(color) {
    if (color == null || color === "") return "";
    var s = String(color).trim();
    if (/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(s)) {
      return "border-color:" + s + ";";
    }
    return "";
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function sidePoint(node, side) {
    var x = +node.x || 0, y = +node.y || 0;
    var w = +node.width || 0, h = +node.height || 0;
    side = (side || "right").toLowerCase();
    if (side === "left") return { x: x, y: y + h / 2 };
    if (side === "right") return { x: x + w, y: y + h / 2 };
    if (side === "top") return { x: x + w / 2, y: y };
    if (side === "bottom") return { x: x + w / 2, y: y + h };
    return { x: x + w / 2, y: y + h / 2 };
  }

  function boundsOf(nodes) {
    if (!nodes.length) return { minX: 0, minY: 0, maxX: 400, maxY: 300 };
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    nodes.forEach(function (n) {
      var x = +n.x || 0, y = +n.y || 0;
      var w = +n.width || 100, h = +n.height || 60;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x + w);
      maxY = Math.max(maxY, y + h);
    });
    if (!isFinite(minX)) return { minX: 0, minY: 0, maxX: 400, maxY: 300 };
    return { minX: minX, minY: minY, maxX: maxX, maxY: maxY };
  }

  function boot() {
    var viewport = document.getElementById("canvas-viewport");
    var world = document.getElementById("canvas-world");
    var zoomLabel = document.getElementById("canvas-zoom-label");
    if (!viewport || !world) return;

    var data = loadData();
    var nodes = Array.isArray(data.nodes) ? data.nodes : [];
    var edges = Array.isArray(data.edges) ? data.edges : [];
    var byId = {};
    nodes.forEach(function (n) { if (n && n.id) byId[n.id] = n; });

    var state = { x: 0, y: 0, scale: 1 };
    var pan = { active: false, sx: 0, sy: 0, ox: 0, oy: 0 };

    function applyTransform() {
      world.style.transform =
        "translate(" + state.x + "px," + state.y + "px) scale(" + state.scale + ")";
      if (zoomLabel) zoomLabel.textContent = Math.round(state.scale * 100) + "%";
    }

    function fit() {
      var b = boundsOf(nodes);
      var pad = 40;
      var vw = Math.max(viewport.clientWidth || 800, 100);
      var vh = Math.max(viewport.clientHeight || 600, 100);
      var bw = Math.max(b.maxX - b.minX, 1);
      var bh = Math.max(b.maxY - b.minY, 1);
      var s = Math.min((vw - pad * 2) / bw, (vh - pad * 2) / bh, 1.5);
      s = Math.max(0.15, s);
      state.scale = s;
      state.x = (vw - bw * s) / 2 - b.minX * s;
      state.y = (vh - bh * s) / 2 - b.minY * s;
      applyTransform();
    }

    var groups = nodes.filter(function (n) { return n.type === "group"; });
    var others = nodes.filter(function (n) { return n.type !== "group"; });

    var frag = document.createDocumentFragment();

    var svgNS = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "canvas-edges");
    var maxR = 1, maxB = 1;
    nodes.forEach(function (n) {
      maxR = Math.max(maxR, (+n.x || 0) + (+n.width || 0));
      maxB = Math.max(maxB, (+n.y || 0) + (+n.height || 0));
    });
    svg.setAttribute("width", String(maxR + 200));
    svg.setAttribute("height", String(maxB + 200));
    svg.style.overflow = "visible";

    var colorHex = {
      "1": "#e74c3c",
      "2": "#e67e22",
      "3": "#f1c40f",
      "4": "#2ecc71",
      "5": "#1abc9c",
      "6": "#9b59b6"
    };

    edges.forEach(function (e) {
      var a = byId[e.fromNode], b = byId[e.toNode];
      if (!a || !b) return;
      var p0 = sidePoint(a, e.fromSide);
      var p1 = sidePoint(b, e.toSide);
      var path = document.createElementNS(svgNS, "path");
      var mx = (p0.x + p1.x) / 2, my = (p0.y + p1.y) / 2;
      var d =
        "M " + p0.x + " " + p0.y +
        " C " + mx + " " + p0.y + ", " + mx + " " + p1.y + ", " + p1.x + " " + p1.y;
      path.setAttribute("d", d);
      path.setAttribute("fill", "none");
      var stroke = "#888";
      if (e.color && /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(String(e.color))) {
        stroke = String(e.color);
      } else if (colorHex[String(e.color)]) {
        stroke = colorHex[String(e.color)];
      }
      path.setAttribute("stroke", stroke);
      path.setAttribute("stroke-width", "2");
      path.setAttribute("marker-end", "url(#canvas-arrow)");
      svg.appendChild(path);
      if (e.label) {
        var t = document.createElementNS(svgNS, "text");
        t.setAttribute("x", String(mx));
        t.setAttribute("y", String(my - 4));
        t.setAttribute("class", "canvas-edge-label");
        t.textContent = String(e.label);
        svg.appendChild(t);
      }
    });

    var defs = document.createElementNS(svgNS, "defs");
    var marker = document.createElementNS(svgNS, "marker");
    marker.setAttribute("id", "canvas-arrow");
    marker.setAttribute("markerWidth", "8");
    marker.setAttribute("markerHeight", "8");
    marker.setAttribute("refX", "6");
    marker.setAttribute("refY", "3");
    marker.setAttribute("orient", "auto");
    var mpath = document.createElementNS(svgNS, "path");
    mpath.setAttribute("d", "M0,0 L6,3 L0,6 Z");
    mpath.setAttribute("fill", "#888");
    marker.appendChild(mpath);
    defs.appendChild(marker);
    svg.insertBefore(defs, svg.firstChild);
    frag.appendChild(svg);

    function renderNode(n) {
      var el = document.createElement("div");
      var kind = n.type || "text";
      el.className = "canvas-node is-" + kind;
      var cc = colorClass(n.color);
      if (cc) el.className += " " + cc;
      var st = colorStyle(n.color);
      el.style.left = (+n.x || 0) + "px";
      el.style.top = (+n.y || 0) + "px";
      el.style.width = (+n.width || 120) + "px";
      el.style.height = (+n.height || 60) + "px";
      if (st) el.setAttribute("style", el.getAttribute("style") + st);
      el.dataset.id = n.id || "";
      if (kind === "group") {
        el.innerHTML = '<div class="node-label">' + esc(n.label || "") + "</div>";
      } else if (kind === "file") {
        var file = n.file || "";
        var base = file.split("/").pop() || file;
        el.innerHTML =
          '<div class="node-label">file</div>' +
          '<div class="node-file">' + esc(base) + "</div>";
        el.title = file;
      } else {
        el.textContent = n.text || n.label || "";
      }
      frag.appendChild(el);
    }

    groups.forEach(renderNode);
    others.forEach(renderNode);

    if (!nodes.length) {
      var empty = document.createElement("div");
      empty.className = "canvas-empty";
      empty.textContent = "empty canvas";
      viewport.appendChild(empty);
    }

    world.appendChild(frag);

    viewport.addEventListener("pointerdown", function (ev) {
      if (ev.button !== 0) return;
      pan.active = true;
      pan.sx = ev.clientX;
      pan.sy = ev.clientY;
      pan.ox = state.x;
      pan.oy = state.y;
      viewport.classList.add("is-panning");
      try { viewport.setPointerCapture(ev.pointerId); } catch (err) {}
    });
    viewport.addEventListener("pointermove", function (ev) {
      if (!pan.active) return;
      state.x = pan.ox + (ev.clientX - pan.sx);
      state.y = pan.oy + (ev.clientY - pan.sy);
      applyTransform();
    });
    function endPan(ev) {
      if (!pan.active) return;
      pan.active = false;
      viewport.classList.remove("is-panning");
      try { viewport.releasePointerCapture(ev.pointerId); } catch (err) {}
    }
    viewport.addEventListener("pointerup", endPan);
    viewport.addEventListener("pointercancel", endPan);

    viewport.addEventListener(
      "wheel",
      function (ev) {
        ev.preventDefault();
        var rect = viewport.getBoundingClientRect();
        var cx = ev.clientX - rect.left;
        var cy = ev.clientY - rect.top;
        var before = state.scale;
        var factor = ev.deltaY < 0 ? 1.1 : 1 / 1.1;
        var next = Math.min(3, Math.max(0.12, before * factor));
        var wx = (cx - state.x) / before;
        var wy = (cy - state.y) / before;
        state.scale = next;
        state.x = cx - wx * next;
        state.y = cy - wy * next;
        applyTransform();
      },
      { passive: false }
    );

    var fitBtn = document.getElementById("canvas-fit");
    if (fitBtn) fitBtn.addEventListener("click", fit);
    var zin = document.getElementById("canvas-zoom-in");
    var zout = document.getElementById("canvas-zoom-out");
    if (zin) {
      zin.addEventListener("click", function () {
        state.scale = Math.min(3, state.scale * 1.15);
        applyTransform();
      });
    }
    if (zout) {
      zout.addEventListener("click", function () {
        state.scale = Math.max(0.12, state.scale / 1.15);
        applyTransform();
      });
    }

    fit();
    window.addEventListener("resize", function () { fit(); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
