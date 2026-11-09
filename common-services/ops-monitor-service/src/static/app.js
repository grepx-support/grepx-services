/* Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved. Proprietary and confidential.
 *
 * The live operations screen. Generic: everything product-specific (title, map centre, what a place is, which numbers)
 * arrives from api/config and api/board. All text from the server is put on the page with textContent, never as HTML.
 */
(function () {
  "use strict";

  if (!location.pathname.endsWith("/")) { location.replace(location.pathname + "/" + location.search); return; }

  var TOKEN_KEY = "grepx-ops-token";
  var COLORS = { ACCEPTED: "#4cc3ff", REJECTED: "#ff9b3d", FAILED: "#ff9b3d", NEW: "#c9d6e3", CLAIMED: "#c9d6e3" };
  var DEFAULT_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

  var state = {
    token: readToken(), config: null, seq: 0, events: [], filter: "all", view: "map",
    board: { places: [], kpis: [], services: [], stats: null }, placeById: {},
    map: null, mapReady: false, pulses: [], layers: { places: true, pulses: true, heat: true },
    graph: { nodes: {}, particles: [] }, polling: false
  };

  var $ = function (id) { return document.getElementById(id); };

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function readToken() { try { return sessionStorage.getItem(TOKEN_KEY) || ""; } catch (e) { return ""; } }
  function writeToken(t) { try { if (t) sessionStorage.setItem(TOKEN_KEY, t); else sessionStorage.removeItem(TOKEN_KEY); } catch (e) { /* private mode */ } }

  // ---------------------------------------------------------------- server
  function api(path) {
    return fetch("api/" + path, { headers: { Authorization: "Bearer " + state.token }, cache: "no-store" }).then(function (r) {
      if (r.status === 401 || r.status === 403) {
        var err = new Error(r.status === 403 ? "This account may not see the operations screen." : "Please sign in.");
        err.auth = true; throw err;
      }
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  function showLogin(message) {
    state.polling = false;
    $("app").hidden = true;
    $("login").hidden = false;
    $("login-error").textContent = message || "";
    $("email").focus();
  }

  $("login-form").addEventListener("submit", function (ev) {
    ev.preventDefault();
    $("login-error").textContent = "";
    fetch("/api/v1/auth/login", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: $("email").value.trim(), password: $("password").value })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (body) {
        if (!r.ok || !body.token) throw new Error(body.message || body.detail || body.error || "Sign-in failed.");
        state.token = body.token; writeToken(body.token);
        $("password").value = "";
        start();
      });
    }).catch(function (e) {
      $("login-error").textContent = e.message === "Failed to fetch"
        ? "Sign-in is only available through the site address (…/ops/)." : e.message;
    });
  });

  $("logout").addEventListener("click", function () { state.token = ""; writeToken(""); showLogin(""); });

  // ---------------------------------------------------------------- start
  function start() {
    if (!state.token) { showLogin(""); return; }
    api("config").then(function (cfg) {
      state.config = cfg;
      $("login").hidden = true;
      $("app").hidden = false;
      $("title").textContent = cfg.title || "Live";
      $("subtitle").textContent = cfg.subtitle || "";
      document.title = (cfg.title || "Live") + " · operations";
      $("places-title").textContent = word("places", "Places");
      if (cfg.accent) document.documentElement.style.setProperty("--accent", cfg.accent);
      setupMap();
      setupGraph();
      return Promise.all([refreshBoard(), api("events?after=0").then(function (r) { addEvents(r.events, true); })]);
    }).then(function () {
      setLive(true);
      if (!state.polling) { state.polling = true; poll(); }
    }).catch(function (e) {
      if (e.auth) showLogin(e.message); else setLive(false, "Cannot reach the monitor");
    });
  }

  function word(key, fallback) { return (state.config && state.config.words && state.config.words[key]) || fallback; }

  function poll() {
    if (!state.polling) return;
    api("events?after=" + state.seq + "&wait=20").then(function (r) {
      setLive(true);
      addEvents(r.events, false);
      poll();
    }).catch(function (e) {
      if (e.auth) { showLogin(e.message); return; }
      setLive(false, "Reconnecting…");
      setTimeout(poll, 3000);
    });
  }

  function refreshBoard() {
    return api("board").then(function (b) {
      state.board = b;
      state.placeById = {};
      (b.places || []).forEach(function (p) { state.placeById[p.id] = p; });
      renderKpis(); renderPlaces(); renderReasons(); renderServices(); updateMapData(); updateGraphNodes();
    }).catch(function (e) { if (e.auth) showLogin(e.message); });
  }
  setInterval(function () { if (state.polling) refreshBoard(); }, 10000);

  function setLive(on, text) {
    $("live").className = "live " + (on ? "on" : "off");
    $("live-text").textContent = on ? "Live" : (text || "Offline");
  }

  setInterval(function () { $("clock").textContent = new Date().toLocaleTimeString([], { hour12: false }); }, 1000);

  // ---------------------------------------------------------------- events
  function addEvents(list, initial) {
    if (!list || !list.length) return;
    list.forEach(function (e) {
      state.seq = Math.max(state.seq, e.seq);
      state.events.push(e);
      if (!initial && !e.recovered) { pulse(e); flow(e); }
    });
    if (state.events.length > 1500) state.events = state.events.slice(-1000);
    renderWire(initial ? null : list);
  }

  function placeOf(e) {
    var refs = e.refs || {};
    for (var k in refs) { if (state.placeById[refs[k]]) return state.placeById[refs[k]]; }
    return null;
  }

  function short(service) { return String(service || "").replace(/-service$/, "").replace(/-bff$/, " api"); }

  function hhmmss(iso) {
    var d = new Date(iso);
    return isNaN(d) ? "" : d.toLocaleTimeString([], { hour12: false });
  }

  function interesting(e) {
    if (e.status === "CLAIMED") return false;
    if (state.filter === "problems") return e.status === "REJECTED" || e.status === "FAILED";
    return true;
  }

  function wireItem(e, fresh) {
    var li = el("li", fresh ? "fresh" : ""), b = el("button");
    b.type = "button";
    b.appendChild(el("span", "t", hhmmss(e.at)));
    b.appendChild(el("span", "what", short(e.to_service || e.table) + " · " + (e.action || e.table)));
    var badge = COLORS[e.status] ? e.status : "OTHER";
    b.appendChild(el("span", "badge " + badge, e.status === "REJECTED" && e.reason ? e.reason : e.status));
    var p = placeOf(e), parts = [];
    if (p) parts.push(p.label);
    if (e.ms !== null && e.ms !== undefined) parts.push(e.ms + " ms");
    else if (e.status === "NEW" && e.from_service) parts.push("from " + short(e.from_service));
    else if (e.recovered) parts.push("earlier");
    b.appendChild(el("span", "where", parts.join(" · ")));
    if (e.trace_id) b.setAttribute("data-trace", e.trace_id);
    li.appendChild(b);
    return li;
  }

  // New lines are added on top; the list is only rebuilt when the filter changes, so a line stays clickable while traffic flows.
  function renderWire(newOnes) {
    var list = $("wire");
    if (newOnes === null) {
      list.textContent = "";
      state.events.filter(interesting).slice(-250).forEach(function (e) { list.insertBefore(wireItem(e, false), list.firstChild); });
    } else {
      newOnes.filter(interesting).forEach(function (e) {
        var empty = list.querySelector(".empty");
        if (empty) list.removeChild(empty);
        list.insertBefore(wireItem(e, true), list.firstChild);
      });
      while (list.children.length > 250) list.removeChild(list.lastChild);
    }
    if (!list.children.length) list.appendChild(el("li", "empty", state.filter === "problems" ? "No refusals or failures in the window." : "Waiting for activity…"));
  }

  $("wire").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-trace]");
    if (b) openTrace(b.getAttribute("data-trace"));
  });

  Array.prototype.forEach.call(document.querySelectorAll(".chip"), function (c) {
    c.addEventListener("click", function () {
      state.filter = c.getAttribute("data-filter");
      Array.prototype.forEach.call(document.querySelectorAll(".chip"), function (x) { x.setAttribute("aria-pressed", String(x === c)); });
      renderWire(null);
    });
  });

  // ---------------------------------------------------------------- side panels
  function fmt(n) { return n === null || n === undefined ? "–" : Number(n).toLocaleString(); }

  function kpi(label, value, extra, hot, ratio) {
    var box = el("div", "kpi" + (hot ? " hot" : ""));
    box.appendChild(el("div", "label", label));
    var v = el("div", "value", value);
    if (extra) { v.appendChild(document.createTextNode(" ")); v.appendChild(el("small", "", extra)); }
    box.appendChild(v);
    if (ratio !== undefined) { var bar = el("div", "bar"), fill = el("span"); fill.style.width = Math.min(100, Math.round(ratio * 100)) + "%"; bar.appendChild(fill); box.appendChild(bar); }
    return box;
  }

  function renderKpis() {
    var row = $("kpis"), b = state.board, s = b.stats || {};
    row.textContent = "";
    (b.kpis || []).forEach(function (k, i) {
      var of = Number(k.of);
      row.appendChild(kpi(k.label, fmt(k.value), of ? "of " + fmt(of) : k.hint, i === 0, of ? k.value / of : undefined));
    });
    var share = s.verdicts ? Math.round((s.accepted / s.verdicts) * 1000) / 10 + "%" : "–";
    row.appendChild(kpi("Requests / min", fmt(s.per_minute), "last hour " + fmt(s.requests)));
    row.appendChild(kpi("Accepted", share, s.rejected ? fmt(s.rejected) + " refused" : ""));
    row.appendChild(kpi("Request → answer p95", s.p95_ms === null || s.p95_ms === undefined ? "–" : s.p95_ms + " ms", s.timed ? "n=" + s.timed : "needs 20 samples"));
    var up = (b.services || []).filter(function (x) { return x.up; }).length;
    row.appendChild(kpi("Services up", up + " / " + (b.services || []).length, "", up < (b.services || []).length));
  }

  function renderPlaces() {
    var list = $("places"), names = (state.config && state.config.counts) || [];
    list.textContent = "";
    var places = state.board.places || [];
    if (!places.length) { list.appendChild(el("li", "empty", "Nothing scheduled.")); return; }
    places.forEach(function (p) {
      var li = el("li"), b = el("button");
      b.type = "button";
      var first = names[0] ? (p.counts[names[0]] || 0) : 0, full = p.capacity && first >= p.capacity;
      var r1 = el("span", "row1");
      r1.appendChild(el("span", "name", p.label));
      r1.appendChild(el("span", "mono muted" + (full ? " full" : ""), full ? "FULL" : (p.date || "")));
      b.appendChild(r1);
      var r2 = el("span", "row2");
      names.forEach(function (n) { r2.appendChild(el("span", "", word(n, n) + " " + fmt(p.counts[n] || 0) + (n === names[0] && p.capacity ? " / " + fmt(p.capacity) : ""))); });
      if (p.lng === null) r2.appendChild(el("span", "", "not on map"));
      b.appendChild(r2);
      if (p.capacity) { var bar = el("span", "bar"), f = el("span"); f.style.width = Math.min(100, Math.round(first / p.capacity * 100)) + "%"; bar.appendChild(f); b.appendChild(bar); }
      b.addEventListener("click", function () { flyTo(p); });
      li.appendChild(b);
      list.appendChild(li);
    });
  }

  function renderReasons() {
    var list = $("reasons"), reasons = (state.board.stats && state.board.stats.reasons) || [];
    list.textContent = "";
    if (!reasons.length) { list.appendChild(el("li", "empty", "None in the last hour.")); return; }
    var max = reasons[0][1];
    reasons.forEach(function (r) {
      var li = el("li"), r1 = el("div", "r1");
      r1.appendChild(el("span", "", r[0])); r1.appendChild(el("span", "muted", r[1]));
      var bar = el("div", "bar"), f = el("span"); f.style.width = Math.round(r[1] / max * 100) + "%"; bar.appendChild(f);
      li.appendChild(r1); li.appendChild(bar); list.appendChild(li);
    });
  }

  function renderServices() {
    var box = $("services"), list = state.board.services || [];
    box.textContent = "";
    var up = 0;
    list.forEach(function (s) {
      if (s.up) up++;
      var d = el("div", "svc" + (s.up ? "" : " down"));
      d.title = s.service + (s.up ? " · up" : " · no heartbeat") + (s.last_error ? " · last error: " + s.last_error : "");
      d.appendChild(el("span", "dot")); d.appendChild(el("span", "", short(s.service)));
      box.appendChild(d);
    });
    $("svc-count").textContent = list.length ? up + "/" + list.length : "";
  }

  // ---------------------------------------------------------------- trace
  function openTrace(id) {
    $("trace").hidden = false;
    $("trace-id").textContent = id.slice(0, 12);
    $("trace-summary").textContent = "Loading…";
    $("trace-steps").textContent = "";
    api("trace/" + encodeURIComponent(id)).then(function (r) {
      var ev = r.events || [];
      if (!ev.length) { $("trace-summary").textContent = "No events for this trace in the monitor's window."; return; }
      var t0 = new Date(ev[0].seen).getTime();
      var services = [];
      ev.forEach(function (e) { var s = e.to_service || e.table; if (services.indexOf(s) < 0) services.push(s); });
      var bad = ev.filter(function (e) { return e.status === "REJECTED" || e.status === "FAILED"; });
      $("trace-summary").textContent = ev.length + " events · " + services.map(short).join(" → ") + (bad.length ? " · refused: " + (bad[0].reason || bad[0].status) : " · all accepted");
      ev.forEach(function (e) {
        var li = el("li", e.status), rail = el("span", "rail"), body = el("span", "body");
        li.appendChild(el("span", "at", "+" + Math.max(0, new Date(e.seen).getTime() - t0) + " ms"));
        rail.appendChild(el("i")); rail.appendChild(el("b"));
        li.appendChild(rail);
        body.appendChild(el("div", "", short(e.to_service || e.table) + " · " + e.status + (e.reason ? " · " + e.reason : "")));
        body.appendChild(el("div", "", e.table + (e.action ? " " + e.action : "") + (e.from_service ? " · from " + short(e.from_service) : "") + (e.ms !== null && e.ms !== undefined ? " · " + e.ms + " ms" : "")));
        if (e.error) body.appendChild(el("div", "", e.error));
        li.appendChild(body);
        $("trace-steps").appendChild(li);
      });
    }).catch(function (e) { $("trace-summary").textContent = e.message; });
  }
  $("trace-close").addEventListener("click", function () { $("trace").hidden = true; });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") $("trace").hidden = true; });

  // ---------------------------------------------------------------- map
  function setupMap() {
    if (state.map) return;
    if (typeof maplibregl === "undefined") { mapNote("The map library could not load (no internet access?). The wire and the System view still work."); return; }
    var m = (state.config && state.config.map) || {};
    try {
      state.map = new maplibregl.Map({
        container: "map", style: m.style || DEFAULT_STYLE, center: m.center || [0, 20], zoom: m.zoom || 2,
        attributionControl: { compact: true }, dragRotate: false, pitchWithRotate: false
      });
    } catch (e) { mapNote("This browser cannot draw the map (WebGL is off). The System view still works."); return; }
    state.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    state.map.on("error", function (e) {
      if (!state.mapReady) mapNote("Map tiles could not load - places still update in the list.");
    });
    state.map.on("load", function () {
      state.mapReady = true;
      $("map-note").hidden = true;
      var map = state.map;
      map.addSource("places", { type: "geojson", data: empty() });
      map.addSource("pulses", { type: "geojson", data: empty() });
      map.addSource("heat", { type: "geojson", data: empty() });
      map.addLayer({ id: "heat", type: "heatmap", source: "heat", maxzoom: 15, paint: {
        "heatmap-weight": ["get", "w"], "heatmap-intensity": 1.2, "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 8, 25, 14, 60],
        "heatmap-opacity": 0.55,
        "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, "rgba(0,0,0,0)", 0.2, "rgba(120,20,60,0.5)", 0.5, "rgba(230,50,80,0.75)", 1, "rgba(255,200,120,0.95)"] } });
      map.addLayer({ id: "places-glow", type: "circle", source: "places", paint: {
        "circle-radius": ["+", 14, ["*", 26, ["get", "fill"]]], "circle-color": "#ff4d5e", "circle-opacity": 0.12, "circle-blur": 0.8 } });
      map.addLayer({ id: "places-full", type: "circle", source: "places", filter: ["==", ["get", "full"], true], paint: {
        "circle-radius": ["+", 10, ["*", 16, ["get", "fill"]]], "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": "#ff9b3d", "circle-stroke-width": 2 } });
      map.addLayer({ id: "places", type: "circle", source: "places", paint: {
        "circle-radius": ["+", 5, ["*", 12, ["get", "fill"]]], "circle-color": "#ff4d5e", "circle-opacity": 0.85,
        "circle-stroke-color": "#ffd0d5", "circle-stroke-width": 1 } });
      map.addLayer({ id: "pulses", type: "circle", source: "pulses", paint: {
        "circle-radius": ["get", "r"], "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": ["get", "c"],
        "circle-stroke-width": 2, "circle-stroke-opacity": ["get", "o"] } });
      try {
        map.addLayer({ id: "place-labels", type: "symbol", source: "places", layout: {
          "text-field": ["get", "label"], "text-size": 12, "text-offset": [0, 1.6], "text-anchor": "top", "text-font": ["Open Sans Semibold", "Open Sans Regular"] },
          paint: { "text-color": "#e4ecf4", "text-halo-color": "#05080d", "text-halo-width": 1.5 } });
      } catch (e) { /* style without glyphs: circles only */ }
      map.on("click", "places", function (ev) {
        var p = state.placeById[ev.features[0].properties.id];
        if (p) popup(p);
      });
      map.on("mouseenter", "places", function () { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "places", function () { map.getCanvas().style.cursor = ""; });
      applyLayers();
      updateMapData();
      requestAnimationFrame(animatePulses);
    });
  }

  function mapNote(text) { $("map-note").textContent = text; $("map-note").hidden = false; }
  function empty() { return { type: "FeatureCollection", features: [] }; }
  function point(p, props) { return { type: "Feature", geometry: { type: "Point", coordinates: [p.lng, p.lat] }, properties: props }; }

  function updateMapData() {
    if (!state.mapReady) return;
    var names = (state.config && state.config.counts) || [], located = (state.board.places || []).filter(function (p) { return p.lng !== null && p.lat !== null; });
    var max = 1;
    located.forEach(function (p) { max = Math.max(max, p.capacity || 0, p.counts[names[0]] || 0); });
    state.map.getSource("places").setData({ type: "FeatureCollection", features: located.map(function (p) {
      var n = p.counts[names[0]] || 0;
      return point(p, { id: p.id, label: p.label, fill: p.capacity ? Math.min(1, n / p.capacity) : Math.min(1, n / max), full: !!(p.capacity && n >= p.capacity) });
    }) });
    var cutoff = Date.now() - 3600 * 1000, weight = {};
    state.events.forEach(function (e) {
      var p = placeOf(e);
      if (p && p.lng !== null && new Date(e.at).getTime() >= cutoff && e.status !== "CLAIMED") weight[p.id] = (weight[p.id] || 0) + 1;
    });
    state.map.getSource("heat").setData({ type: "FeatureCollection", features: Object.keys(weight).map(function (id) {
      return point(state.placeById[id], { w: Math.min(1, 0.25 + weight[id] / 10) });
    }) });
  }

  function pulse(e) {
    var p = placeOf(e);
    if (!p || p.lng === null || e.status === "CLAIMED") return;
    state.pulses.push({ p: p, born: performance.now(), c: COLORS[e.status] || COLORS.NEW });
    if (state.pulses.length > 200) state.pulses.shift();
  }

  function animatePulses(now) {
    if (state.mapReady && state.layers.pulses) {
      var life = 2200;
      state.pulses = state.pulses.filter(function (x) { return now - x.born < life; });
      state.map.getSource("pulses").setData({ type: "FeatureCollection", features: state.pulses.map(function (x) {
        var t = (now - x.born) / life;
        return point(x.p, { r: 6 + 34 * t, o: 1 - t, c: x.c });
      }) });
    }
    requestAnimationFrame(animatePulses);
  }

  function flyTo(p) {
    setView("map");
    if (state.mapReady && p.lng !== null) { state.map.flyTo({ center: [p.lng, p.lat], zoom: Math.max(state.map.getZoom(), 13), speed: 1.2 }); popup(p); }
  }

  function popup(p) {
    var names = (state.config && state.config.counts) || [], box = el("div");
    box.appendChild(el("strong", "", p.label));
    box.appendChild(el("div", "muted", p.address));
    names.forEach(function (n) { box.appendChild(el("div", "mono", word(n, n) + ": " + fmt(p.counts[n] || 0) + (n === names[0] && p.capacity ? " / " + fmt(p.capacity) : ""))); });
    if (p.date) box.appendChild(el("div", "mono muted", p.date));
    new maplibregl.Popup({ closeButton: true, offset: 14 }).setLngLat([p.lng, p.lat]).setDOMContent(box).addTo(state.map);
  }

  function applyLayers() {
    if (!state.mapReady) return;
    var vis = function (on) { return on ? "visible" : "none"; };
    ["places", "places-glow", "places-full", "place-labels"].forEach(function (id) { if (state.map.getLayer(id)) state.map.setLayoutProperty(id, "visibility", vis(state.layers.places)); });
    state.map.setLayoutProperty("pulses", "visibility", vis(state.layers.pulses));
    state.map.setLayoutProperty("heat", "visibility", vis(state.layers.heat));
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-layer]"), function (box) {
    box.addEventListener("change", function () { state.layers[box.getAttribute("data-layer")] = box.checked; applyLayers(); });
  });

  // ---------------------------------------------------------------- views
  function setView(view) {
    state.view = view;
    Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (t) { t.setAttribute("aria-pressed", String(t.getAttribute("data-view") === view)); });
    $("map").hidden = view !== "map";
    $("graph").hidden = view !== "system";
    document.querySelector(".layers").hidden = view !== "map";
    if (view === "map" && state.map) state.map.resize();
    if (view === "system") sizeGraph();
  }
  Array.prototype.forEach.call(document.querySelectorAll(".tab"), function (t) {
    t.addEventListener("click", function () { setView(t.getAttribute("data-view")); });
  });

  // ---------------------------------------------------------------- system graph (canvas)
  var canvas = $("graph"), ctx = canvas.getContext("2d");

  function setupGraph() { sizeGraph(); requestAnimationFrame(drawGraph); }

  function sizeGraph() {
    var r = canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, r.width * dpr); canvas.height = Math.max(1, r.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener("resize", function () { if (state.view === "system") sizeGraph(); });

  function node(name) {
    var g = state.graph.nodes;
    if (!g[name]) {
      var n = Object.keys(g).length, a = n * 2.399;          // golden-angle spiral start
      g[name] = { name: name, x: Math.cos(a) * (60 + n * 9), y: Math.sin(a) * (60 + n * 9), vx: 0, vy: 0, up: true, heat: 0 };
    }
    return g[name];
  }

  function updateGraphNodes() {
    (state.board.services || []).forEach(function (s) { var n = node(s.service); n.up = s.up; });
    ((state.board.stats && state.board.stats.edges) || []).forEach(function (e) { node(e.from); node(e.to); });
  }

  function flow(e) {
    if (!e.from_service || !e.to_service || e.status === "CLAIMED") return;
    var verdict = e.status !== "NEW";
    var a = node(verdict ? e.to_service : e.from_service), b = node(verdict ? e.from_service : e.to_service);
    state.graph.particles.push({ a: a, b: b, t: 0, c: COLORS[e.status] || COLORS.NEW });
    (verdict ? a : b).heat = 1;
    if (state.graph.particles.length > 400) state.graph.particles.shift();
  }

  function layout() {
    var nodes = Object.keys(state.graph.nodes).map(function (k) { return state.graph.nodes[k]; });
    var edges = (state.board.stats && state.board.stats.edges) || [];
    for (var i = 0; i < nodes.length; i++) {
      for (var j = i + 1; j < nodes.length; j++) {
        var a = nodes[i], b = nodes[j], dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy + 0.01, f = 2600 / d2;
        a.vx += dx * f / Math.sqrt(d2); a.vy += dy * f / Math.sqrt(d2); b.vx -= dx * f / Math.sqrt(d2); b.vy -= dy * f / Math.sqrt(d2);
      }
    }
    edges.forEach(function (e) {
      var a = state.graph.nodes[e.from], b = state.graph.nodes[e.to];
      if (!a || !b) return;
      var dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) || 1, f = (d - 150) * 0.004;
      a.vx += dx / d * f * d * 0.1; a.vy += dy / d * f * d * 0.1; b.vx -= dx / d * f * d * 0.1; b.vy -= dy / d * f * d * 0.1;
    });
    nodes.forEach(function (n) { n.vx -= n.x * 0.004; n.vy -= n.y * 0.004; n.x += n.vx * 0.5; n.y += n.vy * 0.5; n.vx *= 0.6; n.vy *= 0.6; n.heat *= 0.96; });
    return { nodes: nodes, edges: edges };
  }

  function drawGraph() {
    requestAnimationFrame(drawGraph);
    if (state.view !== "system") return;
    var w = canvas.clientWidth, h = canvas.clientHeight, g = layout(), cx = w / 2, cy = h / 2;
    ctx.clearRect(0, 0, w, h);
    var max = 1;
    g.edges.forEach(function (e) { max = Math.max(max, e.n); });
    g.edges.forEach(function (e) {
      var a = state.graph.nodes[e.from], b = state.graph.nodes[e.to];
      if (!a || !b) return;
      ctx.strokeStyle = "rgba(76,195,255," + (0.08 + 0.3 * e.n / max) + ")";
      ctx.lineWidth = 1 + 2 * e.n / max;
      ctx.beginPath(); ctx.moveTo(cx + a.x, cy + a.y); ctx.lineTo(cx + b.x, cy + b.y); ctx.stroke();
    });
    state.graph.particles = state.graph.particles.filter(function (p) { return p.t < 1; });
    state.graph.particles.forEach(function (p) {
      p.t += 0.018;
      var x = cx + p.a.x + (p.b.x - p.a.x) * p.t, y = cy + p.a.y + (p.b.y - p.a.y) * p.t;
      ctx.fillStyle = p.c; ctx.shadowColor = p.c; ctx.shadowBlur = 12;
      ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();
    });
    ctx.shadowBlur = 0;
    g.nodes.forEach(function (n) {
      var x = cx + n.x, y = cy + n.y, r = 7 + n.heat * 6, col = n.up ? "#ff4d5e" : "#ff9b3d";
      ctx.fillStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 10 + n.heat * 20;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = n.up ? "#e4ecf4" : "#ff9b3d";
      ctx.font = "11px 'JetBrains Mono', monospace"; ctx.textAlign = "center";
      ctx.fillText(short(n.name) + (n.up ? "" : " (down)"), x, y + r + 14);
    });
    if (!g.nodes.length) { ctx.fillStyle = "#8fa1b3"; ctx.font = "13px Inter, sans-serif"; ctx.textAlign = "center"; ctx.fillText("Waiting for services…", cx, cy); }
  }

  start();
})();
