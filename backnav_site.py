"""Back navigation for in-page jumps (map study links, module links, Command Decoder chips, search
results, drill/lab debrief links, job-search unlock links).

Every jump the reader starts pushes a history entry, so browser Back, the mouse back button and
Alt+Left return to the exact place they left: the map with the same topic and panel scroll, or the
same scroll position in the module. The entry they left keeps where they were in history.state
(bnPt = map panel scrollTop, bnY/bnA/bnO = window scrollY, nearest heading id and its offset);
the landing entry keeps {bn: key, bo: origin} for a floating "Back" pill that names the origin.
Automatic corrections (map topic hash, legacy ids) keep using replaceState elsewhere.
The page gets the CSS and script without comments and indentation (about 6 KB together).
"""
import re

BACKNAV_HTML = ('<div id="backnav" class="backnav" aria-live="polite" hidden>'
                '<button type="button" class="bn-go">← Back</button>'
                '<button type="button" class="bn-x" aria-label="Hide the back button" title="Hide (Esc)">✕</button></div>')

BACKNAV_CSS = """
/* "← Back" pill after an in-page jump (backnav_site.py) */
.backnav { position: fixed; z-index: 18; left: 316px; bottom: 18px; display: flex; overflow: hidden;
  max-width: calc(100vw - 392px); background: var(--bg2); border: 1px solid var(--accent); border-radius: 999px; box-shadow: 0 4px 16px var(--shadow); animation: bn-in .18s ease-out; }
.backnav button { font: inherit; font-size: 14px; min-height: 40px; background: none; border: 0; cursor: pointer; color: var(--accent); padding: 0 13px 0 9px; }
.bn-go { min-width: 0; padding-left: 15px !important; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.backnav .bn-x { flex: none; color: var(--fg-dim); border-left: 1px solid var(--border); }
.backnav button:hover { background: var(--bg3); }
.backnav button:focus-visible { outline: 2px solid var(--accent); outline-offset: -3px; }
.map-open .backnav, .drill-open .backnav, .lab-on .backnav { display: none; }
@media (max-width: 900px) { .backnav { left: 16px; max-width: calc(100vw - 90px); } }
@keyframes bn-in { from { opacity: 0; transform: translateY(8px); } }
@media (prefers-reduced-motion: reduce) { .backnav { animation: none; } }
"""

BACKNAV_SCRIPT = r"""<script>
/* Back pill + real history for in-page jumps (backnav_site.py) */
(function () {
  "use strict";
  var W = window, D = document, R = D.documentElement, pill = D.getElementById("backnav"), main = D.getElementById("main");
  if (!pill || !main) return;
  var btn = pill.firstChild, cur = null, pre = null, landY = null, hideT = 0, tok = 0, seq = 0, H = history, was;
  var raf = W.requestAnimationFrame || setTimeout, $ = function (id) { return D.getElementById(id) || {}; };
  function st() { return H.state && typeof H.state === "object" ? H.state : {}; }
  function rs(o) { try { H.replaceState(Object.assign({}, st(), o), ""); } catch (_) { /* file:// */ } }
  function over() { return /map-open|drill-open|lab-on/.exec(R.className); }
  /* where the reader is: a map topic, a drill or lab room, or a spot in a module */
  function here() {
    var M = W.__map, S = M && M.state, o = over(), n, sec, a;
    if (S && S.open) { n = M.graph.byId[S.selected]; return { m: S.selected || "", pt: $("map-panel").scrollTop, t: "map" + (n ? ": " + n.title : "") }; }
    if (o) return { t: o[0] === "lab-on" ? "lab: " + $("lab-v-title").textContent : "drill: " + $("drill-v-title").textContent };
    var line = $("topbar").getBoundingClientRect().bottom + 8;
    main.querySelectorAll(":scope > .mod-section:not([data-fx-off])").forEach(function (s) { if (s.getBoundingClientRect().top <= line) sec = a = s; });
    if (sec) sec.querySelectorAll("h2[id],h3[id]").forEach(function (h) { var r = h.getBoundingClientRect(); if (r.height && r.top <= line) a = h; });
    return { y: W.scrollY, a: a ? a.id : "", o: a ? a.getBoundingClientRect().top : 0, t: sec ? sec.getAttribute("data-title") : "" };
  }
  /* back to the spot; re-align while lazy modules settle, any input cancels */
  function hold(a, o, y) {
    var el = a && D.getElementById(a), k = ++tok, t0 = Date.now(), still = t0, J = W.__handbookJump;
    if (J && J.stop) J.stop();
    (function fix() {
      var want = el ? el.getBoundingClientRect().top + W.scrollY - o : y, t = Date.now();
      if (k !== tok) return;
      if (Math.abs(W.scrollY - want) >= 1) { W.scrollTo(0, want); still = t; }
      if (t - still < 350 && t - t0 < 2500) raf(fix);
    })();
  }
  ["wheel", "touchstart", "keydown", "pointerdown"].forEach(function (t) {
    addEventListener(t, function () { tok++; if (!pill.hidden && landY == null) { landY = W.scrollY; hideT = setTimeout(later, 12000); } }, { capture: true, passive: true });
  });
  function later() { if (pill.contains(D.activeElement)) hideT = setTimeout(later, 4000); else hide(); }
  addEventListener("scroll", function () { if (landY != null && Math.abs(W.scrollY - landY) > 1.5 * innerHeight) hide(); }, { passive: true });
  function show(c) {
    var s = c.t ? "Back to " + c.t.trim() : "Back";
    btn.textContent = "← " + s; btn.title = s; btn.setAttribute("aria-label", s);
    pill.hidden = false; landY = null; clearTimeout(hideT);
  }
  function hide(f) {
    if (f && pill.contains(D.activeElement)) main.focus({ preventScroll: true });
    pill.hidden = true; clearTimeout(hideT); landY = null;
  }
  /* the jump: keep the origin on its own entry, push the landing entry, then scroll */
  function jump(el, hash, from, flash) {
    from = from || here(); from.k = Date.now() + "." + ++seq;
    if (from.m != null) { rs({ bnK: from.k, bnPt: from.pt }); W.__map.close({ keepHistory: true }); }
    else rs({ bnK: from.k, bnY: from.y, bnA: from.a, bnO: from.o });
    cur = from;
    try { H.pushState({ bn: from.k, bo: from }, "", hash || location.href); } catch (_) { /* file:// */ }
    was = st();
    var c = el.closest(".subm");
    if (c) c.classList.add("in");
    W.__handbookJump(el, flash ? "center" : "start");
    if (flash) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
    show(from);
  }
  function link(e) { var a = e.target.closest && e.target.closest("a[href^='#']"); return a && !a.closest("#sidebar,#map,.skip-link") && a; }
  /* capture phase: drill and lab views close on a link click before it bubbles here */
  D.addEventListener("click", function (e) { pre = link(e) ? here() : null; }, true);
  D.addEventListener("click", function (e) {
    var a = link(e), from = pre, id = "", el;
    pre = null;
    if (!a || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    try { id = decodeURIComponent(a.hash.slice(1)); } catch (_) { return; }
    el = id && !/^(map([./]|$)|drill\.|lab\.)/.test(id) && D.getElementById(id);
    if (el && main.contains(el)) { e.preventDefault(); jump(el, "#" + id, from); }
  });
  /* Back from a landing onto its origin restores the spot (only from that landing: elsewhere the
     saved spot may be stale); Forward onto a landing shows the pill again */
  addEventListener("popstate", function () {
    var s = st(), M = W.__map, p = $("map-panel"), back = was && s.bnK && was.bn === s.bnK;
    was = s;
    if (s.bn && s.bo) show(cur = s.bo); else hide();
    if (!back) return;
    if (s.bnPt != null && M && M.state.open) { p.scrollTop = s.bnPt; raf(function () { p.scrollTop = s.bnPt; }); }
    else if (s.bnY != null && !over()) hold(s.bnA, s.bnO, s.bnY);
  });
  addEventListener("hashchange", function () { was = st(); if (!was.bn) hide(); });   /* a native link moved on */
  function back() {
    var c = cur, M = W.__map;
    hide();
    if (!c) return;
    if (st().bn === c.k) return H.back();                 /* our entry: the same as the browser's Back */
    if (c.m != null && M) {                               /* entry replaced meanwhile: rebuild from what we kept */
      M.open({ push: M.core.mapHash(c.m) }); if (c.m) M.select(c.m);
      raf(function () { $("map-panel").scrollTop = c.pt; });
    } else if (c.y != null) hold(c.a, c.o, c.y);
  }
  btn.addEventListener("click", back);
  pill.lastChild.addEventListener("click", function () { hide(1); });
  D.addEventListener("keydown", function (e) {
    var f = D.activeElement;
    if (e.key === "Escape" && !pill.hidden && !over() && !D.querySelector("dialog[open],#sidebar.open") && !/^(INPUT|TEXTAREA|SELECT)$/.test(f && f.tagName)) hide(1);
  });
  was = st();
  W.__backnav = { jump: jump, here: here, back: back, hide: hide };
})();
</script>"""


def _compact(src):
    """Drop /* comments */ and indentation: this file stays readable, the page stays small."""
    return re.sub(r"\n[ \t]+", "\n", re.sub(r"[ \t]*/\*.*?\*/", "", src, flags=re.S))


BACKNAV_CSS, BACKNAV_SCRIPT = _compact(BACKNAV_CSS), _compact(BACKNAV_SCRIPT)
