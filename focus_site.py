"""Focused topic reading and "locked until mastered" for the 3D map's handbook links.

Opening a handbook item from a map topic (Study path or Related playbooks & notes) shows ONLY that
section: an h2 target shows its whole div.subm card, an h3 target shows the heading and its sibling
content up to the next heading of the same or a higher rank. Everything else in #main is hidden.
A sticky bar names the topic and section ("section i of N") with Previous / Next (study items,
then links, in panel order), "Show whole module" and "Back to topic"; an end card offers the next
section, or on the last one "Mark done" (the map's own toggleDone) and the next topic.

"Show whole module" is learning mode: only that module (every other module is hidden), and its
sections that belong only to OTHER topics whose prerequisites are not all done collapse behind a
lock card with "Open anyway" (it holds while you stay on that topic). Its end card leads with the map's next
step, "Next topic: …" (the same choice as the last section's end card), then "Back to topic", and a smaller
"Next module in the book: X (🔒 N locked) ›" in handbook order (opened the same way, locks included), shown
only while that module has a section this reader can open (a topic's section that is unlocked, or a module
with nothing to lock): the book's order often jumps to an unrelated area.

A topic's reading sequence skips the area-wide "Sources: X" sections (the build marks those
items "area"); the end card links them as "Related incidents in this area (N)", opened as
reference reading. A section listed inside another listed section of the same topic shows once,
as part of the outer one; its own link or "#read.TOPIC.INNER" opens the outer one scrolled to it. A "#read.TOPIC.ANCHOR" whose anchor left the topic opens the topic's
first section with a short note. Locked sections do not print. The end card also lists the
topic's key commands, explained (keycmd_site.py, rendered by the map's cmdList). Reading from the sidebar, search or a cross-reference is reference mode and never
locked (nobody should hit a lock during an outage). Locks are recomputed when S.done changes
(the map dispatches "roadmap-done").

State lives in the URL hash "#read.TOPIC.ANCHOR" (focus) or "#read.TOPIC.ANCHOR.module[.MODULE]"
(learning mode; MODULE names the shown module when "Next module" moved on from the topic's own), bare characters only like "#map.ID", so it survives a reload and the claude.ai host frame,
and plain "#anchor" links keep working exactly as before. Opening pushes one history entry through
backnav_site.py (Back returns to the map topic); Previous / Next / Show whole module replace it.
Hidden elements carry data-fx-off="f" (focus) or "l" (lock); the scrollspy skips them.
"""
from page_slim import minify_css, minify_js

FOCUS_CSS = """
/* focused topic reading + learning-mode locks (focus_site.py) */
[data-fx-off] { display: none !important; }
.fx-bar { position: sticky; top: var(--tb-total); z-index: 15; display: flex; flex-wrap: wrap; align-items: center;
  gap: 8px 14px; margin: -6px 0 18px; padding: 10px 14px; background: var(--bg2); border: 1px solid var(--accent);
  border-radius: 12px; box-shadow: 0 4px 16px var(--shadow); }
.fx-what { flex: 1 1 340px; min-width: 0; font-size: 14px; line-height: 1.45; }
.fx-what strong { color: var(--accent); }
.fx-n { color: var(--fg-dim); white-space: nowrap; }
.fx-btns { display: flex; flex-wrap: wrap; gap: 6px; }
.fx-btn { font: inherit; font-size: 13.5px; min-height: 34px; padding: 0 12px; border-radius: 8px; cursor: pointer;
  border: 1px solid var(--border); background: var(--bg); color: var(--fg); }
.fx-btn:hover:not(:disabled) { background: var(--bg3); }
.fx-btn:disabled { opacity: .45; cursor: default; }
.fx-btn.fx-pri { background: var(--accent); border-color: var(--accent); color: var(--on-accent); font-weight: 600; }
.fx-btn.fx-pri:hover { background: var(--accent); filter: brightness(1.08); }
.fx-btn.fx-sm { font-size: 12.5px; min-height: 30px; padding: 0 10px; }
.fx-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.fx-end { margin: 22px 0 34px; padding: 16px 18px; border: 1px dashed var(--accent); border-radius: 14px; background: var(--accent-soft); }
.fx-end-h { margin: 0 0 10px; font-weight: 700; }
.fx-lock { margin: 16px 0; padding: 12px 16px; border: 1px solid var(--border); border-left: 4px solid var(--fg-dim);
  border-radius: 12px; background: var(--bg2); font-size: 14px; }
.fx-lock p { margin: 0 0 8px; }
.fx-lock .fx-lock-s { color: var(--fg-dim); font-size: 13px; }
.fx-note { flex-basis: 100%; font-size: 13px; color: var(--fg-dim); }
.fx-area { margin: 10px 0 0; font-size: 13.5px; }
.fx-kc { margin: 12px 0 0; }
.fx-kc > summary { cursor: pointer; font-weight: 600; font-size: 14px; }
/* the plain page background under the rows: on the card's accent tint the read-only badge and Decode links fell below 4.5:1 */
.fx-kc > .mp-cmds { margin-top: 8px; padding: 4px 10px 2px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); }
.fx-on .backnav, .fx-on #readbar { display: none; }
.fx-on #main [id] { scroll-margin-top: calc(var(--tb-total) + var(--fx-h, 60px) + 14px); }
@media print {
  .fx-bar, .fx-end, .fx-lock { display: none !important; }
}
"""

FOCUS_SCRIPT = r"""<script>
/* Focused topic reading + learning-mode locks (focus_site.py). Test hooks: window.__focus. */
(function () {
  "use strict";
  var W = window, D = document, R = D.documentElement, H = history, main = D.getElementById("main"), M = W.__map;
  if (!main || !M || !M.graph) return;
  var G = M.graph, S = M.state, core = M.core, OFF = "data-fx-off", RX = /^#read\.([^.]+)\.([^.]+)(\.module(?:\.([^.]+))?)?$/;
  var cur = null, hid = [], lockHid = [], locks = [], opened = new Set(), openedFor = null, own = null, end = null, stale = 0, kcOpen = Object.create(null);
  var raf = W.requestAnimationFrame || setTimeout;
  function $(id) { return id ? D.getElementById(id) : null; }
  function h(tag, attrs) {
    var el = D.createElement(tag), k, i;
    for (k in attrs || {}) {
      if (attrs[k] == null || attrs[k] === false) continue;
      if (k === "on") el.addEventListener("click", attrs[k]); else el.setAttribute(k, attrs[k] === true ? "" : attrs[k]);
    }
    for (i = 2; i < arguments.length; i++) [].concat(arguments[i]).forEach(function (c) { if (c != null) el.append(c); });
    return el;
  }
  function btn(k, label, fn, aria, pri, dis) {
    return h("button", { type: "button", class: "fx-btn" + (pri ? " fx-pri" : ""), "data-k": k, "aria-label": aria || null,
      title: aria || null, disabled: !!dis, on: fn }, label);
  }
  var bar = h("nav", { class: "fx-bar", "aria-label": "Focused reading" });
  function st() { return H.state && typeof H.state === "object" ? H.state : {}; }
  function rs(hash) { try { H.replaceState(H.state, "", hash); } catch (_) { /* file:// */ } }
  function enc(t, a, whole, mid) { return "#read." + t + "." + a + (whole ? ".module" + (mid ? "." + mid : "") : ""); }
  /* the topic's handbook sections in panel order: study items first, then links. Area-wide source sections
     ("area", from the build) stay out of the sequence (see areas); a section inside another listed one is dropped */
  function items(t) {
    var n = G.byId[t], seen = Object.create(null), out = [];
    if (n) (n.study || []).concat(n.links || []).forEach(function (it) {
      var el = it && it.anchor && !it.area && !seen[it.anchor] && $(it.anchor);
      if (el && main.contains(el)) {
        seen[it.anchor] = 1;
        out.push({ a: it.anchor, el: el, r: range(el), label: String(it.label || it.heading || it.anchor).replace(/^Handbook:\s*/, "") });
      }
    });
    return out.filter(function (x) { return !out.some(function (y) { return y !== x && within(y.r, x.el); }); });
  }
  function areas(t) {
    var n = G.byId[t], out = [];
    (n && n.links || []).forEach(function (it) {
      var el = it.area && $(it.anchor), c = el && el.closest(".subm");
      if (c) out.push({ a: it.anchor, n: c.querySelectorAll(".source-entry").length, t: title(el).replace(/^Sources:\s*/, "") });
    });
    return out;
  }
  /* the item for an anchor: its own, else the listed section it sits in */
  function find(L, a) {
    var el = $(a), i;
    for (i = 0; i < L.length; i++) if (L[i].a === a) return i;
    for (i = 0; el && i < L.length; i++) if (within(L[i].r, el)) return i;
    return -1;
  }
  function modOf(id) { var e = $(id); return e && e.parentElement === main && e.classList.contains("mod-section") ? e : null; }
  /* a known topic whose anchor moved opens at its first section (p.moved); an anchor inside a listed section opens
     that section at the anchor (p.at); p.named: the URL names a module (corrected when it is not shown as another) */
  function parse(hash) {
    var m = RX.exec(hash || ""), t, a, i, L;
    if (!m) return null;
    try { t = decodeURIComponent(m[1]); a = decodeURIComponent(m[2]); } catch (_) { return null; }
    L = G.byId[t] ? items(t) : [];
    if (!L.length) return null;
    i = find(L, a);
    return { t: t, i: Math.max(i, 0), whole: !!m[3], mod: m[4] ? modOf(m[4]) : null, named: !!m[4], moved: i < 0, at: i >= 0 && L[i].a !== a ? a : null };
  }
  function rank(el) { var m = /^H([1-6])$/.exec(el.tagName); return m ? +m[1] : 9; }
  /* an h2 card shows its whole div.subm; any other heading runs to the next heading of the same or a higher rank */
  function range(hd) {
    var p = hd.parentElement, out = [hd], r = rank(hd), s;
    if (p && p.classList.contains("subm") && p.firstElementChild === hd) return [p];
    for (s = hd.nextElementSibling; s && rank(s) > r; s = s.nextElementSibling) out.push(s);
    return out;
  }
  function within(rng, el) { return rng.some(function (r) { return r === el || r.contains(el); }); }
  function title(el) { return el.textContent.replace(/\s+/g, " ").trim(); }
  function hide(el, why, list) { if (!el.hasAttribute(OFF)) { el.setAttribute(OFF, why); list.push(el); } }
  function unhide(list) { list.forEach(function (e) { e.removeAttribute(OFF); }); list.length = 0; }
  function layout() {
    if (bar.isConnected) R.style.setProperty("--fx-h", bar.offsetHeight + "px");
    D.dispatchEvent(new Event("handbook-layout"));
  }
  function reveal(el) {
    var b = el.closest(".env"), e = R.getAttribute("data-env"), p;
    if (b && e && b.getAttribute("data-env") !== e && W.__setHandbookEnv) W.__setHandbookEnv("both");
    for (p = el; p && p !== main; p = p.parentElement) {
      if (p.tagName === "DETAILS") p.open = true;
      if (p.classList.contains("subm")) p.classList.add("in");
    }
  }
  function focusEl(el) { if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "-1"); try { el.focus({ preventScroll: true }); } catch (_) { /* old browser */ } }
  /* same button again; a button gone in the new mode falls back to the first one; Next / Previous disabled at the
     end lets go() move to the section heading (falling back to Previous turned Enter, Enter into going back) */
  function refocus(box, k) {
    var b = k && box.querySelector('[data-k="' + k + '"]');
    if (!b) b = k && box.querySelector(".fx-btn:not(:disabled)");
    if (b && !b.disabled) b.focus({ preventScroll: true });
  }
  function keyIn(box) { var f = D.activeElement; return f && box && box.contains(f) ? f.getAttribute("data-k") || "x" : ""; }
  function modTitle() { return cur.mod ? cur.mod.getAttribute("data-title") || "" : ""; }

  /* ---------- the next topic: the map's next steps that are now open, else the guided path ---------- */
  function nextTopic(t) {
    var n = G.byId[t], ok = function (id) { return id === t || S.done.has(id); }, c, i, k;
    c = n.children.filter(function (id) { return !S.done.has(id) && G.byId[id].parents.every(ok); });
    if (c.length) return c[0];
    i = G.path.indexOf(t);
    for (k = i + 1; i >= 0 && k < G.path.length; k++) if (!S.done.has(G.path[k])) return G.path[k];
    return n.children[0] || null;
  }
  function toMap(t) { M.open({ push: core.mapHash(t) }); M.select(t, { fly: true }); }
  /* back to the topic: the browser's Back when the entry before is that map topic, else open it */
  function toTopic() {
    var t = cur.t, s = st(), B = W.__backnav;
    if (s.bn && s.bo && s.bo.m === t) { if (B) B.hide(); H.back(); return; }
    toMap(t);
  }

  /* ---------- bar and end card ---------- */
  function renderBar() {
    var L = cur.L, i = cur.i, x = L[i], n = G.byId[cur.t], k = keyIn(bar), kids;
    var back = btn("bk", "← Back to topic", toTopic, "Back to the topic " + n.title + " on the course map");
    if (!cur.whole) kids = [
      h("span", { class: "fx-what", "aria-live": "polite" }, "📘 Reading for: ", h("strong", null, n.title), " — ", title(x.el),
        h("span", { class: "fx-n" }, " · section " + (i + 1) + " of " + L.length)),
      h("span", { class: "fx-btns" },
        btn("pv", "‹ Previous", function () { step(-1); }, i ? "Previous section for this topic: " + L[i - 1].label : "No previous section", 0, !i),
        btn("nx", "Next ›", function () { step(1); }, i < L.length - 1 ? "Next section for this topic: " + L[i + 1].label : "No next section", 0, i >= L.length - 1),
        btn("wm", "Show whole module", whole, "Show the whole module " + modTitle() + "; sections of topics you have not reached stay locked"),
        back)];
    else kids = [
      h("span", { class: "fx-what", "aria-live": "polite" }, "📘 Learning: ", h("strong", null, n.title), " — whole module “" + modTitle() + "”",
        h("span", { class: "fx-n" }, locks.length ? " · 🔒 " + locks.length + " section" + (locks.length === 1 ? "" : "s") + " locked" : " · nothing locked")),
      h("span", { class: "fx-btns" },
        btn("sc", "Back to the section", function () { go(cur.i, false); }, "Show only the section " + title(x.el) + " again"),
        back,
        btn("lv", "✕ Leave learning mode", leave, "Leave learning mode: every section unlocked, as from the sidebar"))];
    if (cur.moved) kids.push(h("span", { class: "fx-note", role: "status" }, "That section moved, starting at the beginning of this topic"));
    bar.replaceChildren.apply(bar, kids);
    refocus(bar, k);
  }
  function nextMod(m) { for (m = m.nextElementSibling; m; m = m.nextElementSibling) if (m.classList.contains("mod-section")) return m; return null; }
  function endCard() {
    var L = cur.L, nx = L[cur.i + 1], t = cur.t, n = G.byId[t], done = S.done.has(t), nt = nextTopic(t), b = [], nm, nb, k, kc;
    var head = cur.whole ? "End of module “" + modTitle() + "”" : "End of this section";
    if (cur.whole) {   // the map's next step leads; the book's order often jumps to an unrelated area
      if (nt) b.push(btn("nt", "Next topic: " + G.byId[nt].title + " →", function () { toMap(nt); }, null, 1));
    } else if (nx) b.push(btn("en", "Next section for this topic: " + nx.label + " →", function () { step(1); }, null, 1));
    else {
      b.push(h("button", { type: "button", class: "fx-btn" + (done ? "" : " fx-pri"), "data-k": "dn", "aria-pressed": String(done),
        on: function () { M.toggleDone(t); } }, done ? "✓ ‘" + n.title + "’ is done (undo)" : "✓ Mark ‘" + n.title + "’ done"));
      if (nt) b.push(btn("nt", "Next topic: " + G.byId[nt].title + " →", function () { toMap(nt); }, null, done));
    }
    b.push(btn("eb", "← Back to topic", toTopic, "Back to the topic " + n.title + " on the course map"));
    /* handbook order, smaller: opened in learning mode too (sections of topics not reached stay locked), and only
       while it has a section this reader can open (one that unlocked, or nothing that locks at all) */
    if (cur.whole && (nm = nextMod(cur.mod)) && ((k = plan(nm)).free || !k.length)) {
      nb = btn("nm", "Next module in the book: " + nm.getAttribute("data-title") + (k.length ? " (🔒 " + k.length + " locked)" : "") + " ›",
        function () { go(cur.i, true, nm); });
      nb.classList.add("fx-sm");
      b.push(nb);
    }
    kc = M.cmdList && (n.commands || []).length && h("details", { class: "fx-kc", open: !!kcOpen[t] },
      h("summary", null, "⌨️ Key commands for this topic (" + n.commands.length + "): what each one does"), M.cmdList(n));
    /* stays open when the card is drawn again (Back from a Decode link, Next, a lock change): Back lands on the same link */
    if (kc) kc.addEventListener("toggle", function () { kcOpen[t] = kc.open; });
    /* plain links: the cross-reference handler below leaves focus, backnav_site.py makes the jump (Back returns) */
    end = h("div", { class: "fx-end", role: "group", "aria-label": head }, h("p", { class: "fx-end-h" }, head), h("div", { class: "fx-btns" }, b),
      areas(t).map(function (s, i, A) {
        return h("p", { class: "fx-area" }, h("a", { href: "#" + s.a }, "Related incidents in this area" + (A.length > 1 ? ": " + s.t : "") + " (" + s.n + ") ›"));
      }), kc || null);
    return end;
  }

  /* ---------- locks (learning mode only) ---------- */
  function owners() {
    if (own) return own;
    own = Object.create(null);
    G.nodes.forEach(function (n) {
      (n.study || []).concat(n.links || []).forEach(function (it) {
        var a = it && !it.area && it.anchor;   // area-wide source sections belong to nobody: never locked
        if (a && (own[a] = own[a] || []).indexOf(n.id) < 0) own[a].push(n.id);
      });
    });
    return own;
  }
  /* the reading topic's prerequisites (all the way down) are behind the reader, never locked */
  function below(t) {
    var out = new Set(), todo = [t], id;
    while (todo.length) G.byId[id = todo.pop()].parents.forEach(function (p) { if (!out.has(p)) { out.add(p); todo.push(p); } });
    return out;
  }
  function ready(id) {
    var n = G.byId[id];
    return !!n && (id === cur.t || S.done.has(id) || cur.pre.has(id) || n.parents.every(function (p) { return S.done.has(p); }));
  }
  function unlock() { unhide(lockHid); locks.forEach(function (c) { c.card.remove(); }); locks = []; }
  function lockCard(x, ts) {
    ts = ts.slice().sort(function (p, q) { return G.byId[p].li - G.byId[q].li; });
    var n = G.byId[ts[0]], need = n.parents.filter(function (p) { return !S.done.has(p); }).map(function (p) { return G.byId[p].title; });
    var more = ts.length > 1 ? " (and " + (ts.length - 1) + " more topic" + (ts.length > 2 ? "s" : "") + ")" : "";
    return h("div", { class: "fx-lock", role: "note" },
      h("p", null, "🔒 Part of topic ", h("strong", null, n.title), " (" + core.levelLabel(G.levels[n.li], false) + ")" + more +
        ". Unlocks when you finish: " + need.join(", ") + "."),
      h("p", { class: "fx-lock-s" }, "Hidden section: " + title(x.el)),
      btn("oa", "Open anyway", function () { opened.add(x.a); relock(); focusEl(x.el); }, "Open the locked section " + title(x.el) + " anyway"));
  }
  /* the sections of module `mod` that lock for the reading topic, outermost only (reads the page, changes nothing);
     .free counts the topic sections in it that are open for this reader */
  function plan(mod) {
    var O = owners(), list = [], okR = [], out = [], a, el;
    for (a in O) { el = $(a); if (el && mod.contains(el)) list.push({ a: a, el: el, ok: opened.has(a) || O[a].some(ready) }); }
    list.sort(function (p, q) { return p.el.compareDocumentPosition(q.el) & 4 ? -1 : 1; });
    list.forEach(function (x) { if (x.ok) okR.push(range(x.el)); });
    list.forEach(function (x) {
      if (x.ok) return;
      var rng = range(x.el);
      if (okR.some(function (r) { return within(r, x.el) || rng.some(function (e) { return within([e], r[0]); }); })) return;  // inside or around an open section
      if (out.some(function (l) { return within(l.rng, x.el); })) return;                                                      // inside a lock already
      out.push({ a: x.a, el: x.el, rng: rng, ts: O[x.a] });
    });
    out.free = okR.length;
    return out;
  }
  function relock() {
    unlock();
    plan(cur.mod).forEach(function (x) {
      var card = lockCard(x, x.ts);
      x.rng[0].before(card);
      x.rng.forEach(function (e) { hide(e, "l", lockHid); });
      locks.push({ a: x.a, rng: x.rng, card: card });
    });
    if (cur.whole) {   // the end card counts the next module's locks (and hides it when all of it locks)
      var k = keyIn(end), old = end;
      if (old && old.isConnected) { old.replaceWith(endCard()); refocus(end, k); } else cur.mod.after(endCard());
    }
    if (bar.isConnected) renderBar();
    layout();
  }

  /* ---------- modes ---------- */
  /* whole: learning mode on the item's module, or on `mod` (Next module); moved: the URL's anchor left the topic;
     at: an anchor inside the section to start at (a listed section nested in this one) */
  function apply(t, i, whole, mod, moved, at) {
    var L = items(t), x = L[i], rng, keep, path, p, c, home;
    if (!x) return false;
    unhide(hid); unlock(); stale = 0;
    if (end) { end.remove(); end = null; }
    if (openedFor !== t) { opened.clear(); openedFor = t; }   // "Open anyway" holds for the topic it was chosen in
    home = x.el.closest(".mod-section");
    mod = whole && mod && mod !== home ? mod : null;
    cur = { t: t, i: i, whole: !!whole, L: L, mod: mod || home, alt: !!mod, pre: below(t), moved: !!moved, at: !whole && at ? $(at) : null };
    if (!mod) reveal(x.el);
    if (!whole) {
      rng = range(x.el); keep = new Set(rng); path = new Set();
      for (p = rng[0].parentElement; p; p = p.parentElement) { path.add(p); if (p === main) break; }
      path.forEach(function (q) {
        for (c = q.firstElementChild; c; c = c.nextElementSibling)
          if (!path.has(c) && !keep.has(c) && c !== bar && c.tagName !== "SUMMARY") hide(c, "f", hid);
      });
      rng[rng.length - 1].after(endCard());
    } else for (c = main.firstElementChild; c; c = c.nextElementSibling) if (c !== cur.mod && c !== bar) hide(c, "f", hid);   // this module only
    R.classList.add("fx-on"); R.classList.toggle("fx-sec", !whole);
    if (bar.parentNode !== main || main.firstChild !== bar) main.prepend(bar);
    if (whole && cur.mod) relock(); else { renderBar(); layout(); }
    return true;
  }
  /* where a view starts: the section (or the anchor inside it), or for another module (Next module) the module itself,
     hero and all: as an [id] it gets the scroll margin under the bar (its h1 has none: scrolled to, it sat behind the
     top bar). Focus goes to that h1 */
  function spot(f) { return cur.alt ? (f && cur.mod.querySelector("h1")) || cur.mod : cur.at || cur.L[cur.i].el; }
  function url() { return enc(cur.t, cur.L[cur.i].a, cur.whole, cur.alt && cur.mod.id); }
  function go(i, whole, mod) {
    var fromBar = !!keyIn(bar);
    apply(cur.t, i, whole, mod);
    rs(url());
    W.__handbookJump(spot());
    if (!fromBar || !bar.contains(D.activeElement)) focusEl(spot(1));
  }
  function step(d) { if (cur && cur.i + d >= 0 && cur.i + d < cur.L.length) go(cur.i + d, false); }
  function whole() { go(cur.i, true); }
  /* open a topic's handbook item focused; false when the anchor is not one of that topic's sections. An anchor
     inside a listed section opens that section, at the anchor (its URL names the anchor: a reload lands there too) */
  function open(t, a) {
    var L = items(t), i = find(L, a), B = W.__backnav, from, hash, el;
    if (i < 0) return false;
    from = B && B.here();
    apply(t, i, false, null, false, a);
    hash = enc(t, a);
    el = $(a);
    if (B) B.jump(el, hash, from);
    else {
      if (S.open) M.close({ keepHistory: true });
      try { H.pushState({}, "", hash); } catch (_) { /* file:// */ }
      W.__handbookJump(el);
    }
    focusEl(el);
    return true;
  }
  function exit(keepUrl) {
    if (!cur) return;
    var a = cur.alt ? cur.mod.id : cur.L[cur.i].a;
    unhide(hid); unlock();
    if (end) { end.remove(); end = null; }
    bar.remove();
    R.classList.remove("fx-on", "fx-sec"); R.style.removeProperty("--fx-h");
    cur = null;
    if (!keepUrl && RX.test(location.hash)) rs("#" + a);
    layout();
  }
  /* keep the block at the reading line in place while sections above open or close: walk down from #main to
     the element under the line (a heading above it can sit behind a lock card that opens); a lock card's
     section stands in for the card, and a section that locks again is stood in for by its new card */
  function keep(fn) {
    var line = bar.getBoundingClientRect().bottom + 8, el = main, k, r, o, c;
    for (;;) {   // the child across the line, or the first one below a gap: descend only into the former
      for (k = el.firstElementChild; k; k = k.nextElementSibling) { r = k.getBoundingClientRect(); if (r.height && r.bottom > line) break; }
      if (!k) break;
      el = k;
      if (r.top > line) break;
    }
    c = el.closest(".fx-lock");
    o = (c || el).getBoundingClientRect().top;
    if (c) el = c.nextElementSibling;
    fn();
    if (el && !el.getClientRects().length) { c = el.closest("[" + OFF + "]"); el = c && c.previousElementSibling; }
    if (el && el.getClientRects().length) W.scrollTo(0, el.getBoundingClientRect().top + W.scrollY - o);
  }
  function leave() { keep(exit); main.focus({ preventScroll: true }); }

  /* the sidebar is reference reading: leave before its own handlers scroll (capture phase); a click that only
     folds or unfolds a module in the tree (the arrow, or an open module's button) stays in focus */
  D.addEventListener("click", function (e) {
    var t = cur && !(e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) && e.target.closest && e.target.closest("#sidebar a,#sidebar button"), li;
    if (!t) return;
    li = t.matches(".mod-btn") && t.parentElement;
    if (li && li.querySelector(":scope > .subnav") && (li.classList.contains("expanded") || e.target.closest(".chev"))) return;
    exit(t.tagName === "A");   // a link pushes its own entry, so this one keeps "#read…" and Back returns to the section
  }, true);
  /* a cross-reference to hidden content: focus mode steps aside (Back returns to it), a lock opens.
     Registered before backnav_site.py's handler, which then makes the jump. */
  D.addEventListener("click", function (e) {
    var a = cur && e.target.closest && e.target.closest("a[href^='#']"), id = "", el, off;
    if (!a || a.closest("#sidebar,#map") || e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (a.classList.contains("skip-link")) { e.preventDefault(); main.focus({ preventScroll: true }); return; }   // "#main" would end focused reading
    try { id = decodeURIComponent(a.hash.slice(1)); } catch (_) { return; }
    el = id && !/^(map([./]|$)|drill\.|lab\.|read\.)/.test(id) && $(id);
    off = el && main.contains(el) && el.closest("[" + OFF + "]");
    if (!off) return;
    if (off.getAttribute(OFF) === "f") exit(1);
    else locks.forEach(function (l) { if (within(l.rng, el)) { opened.add(l.a); relock(); } });
  });
  /* Back / Forward onto or off a reading entry */
  function same(p) { return cur && cur.t === p.t && cur.i === p.i && cur.whole === p.whole && (cur.alt ? cur.mod === p.mod : !p.mod || p.mod === cur.mod); }
  /* from the URL: a moved anchor gets the note and the topic's first section's URL; a module that is not shown loses its name */
  function load(p) { apply(p.t, p.i, p.whole, p.mod, p.moved, p.at); if (p.moved || p.named && !cur.alt) rs(url()); }
  function sync() {
    var p = parse(location.hash);
    if (p) {
      if (same(p)) { if (stale && !S.open) setTimeout(function () { if (stale && cur && cur.whole) { stale = 0; keep(relock); } }); return; }   // after the browser puts the scroll back
      load(p);
      if (st().bnY == null) W.__handbookJump(spot());     // a saved spot: backnav_site.py restores it
    } else if (cur && !/^#(drill|lab)\./.test(location.hash)) exit(1);
  }
  addEventListener("popstate", sync);
  addEventListener("hashchange", sync);
  D.addEventListener("roadmap-done", function () {
    if (!cur) return;
    if (cur.whole) { if (S.open) stale = 1; else keep(relock); return; }   // under the map: on its way back (sync)
    if (end && end.isConnected) { var k = keyIn(end), old = end; old.replaceWith(endCard()); refocus(end, k); }
  });
  var p0 = parse(location.hash);
  if (p0) { load(p0); raf(function () { if (cur) W.__handbookJump(spot()); }); }
  W.__focus = { open: open, exit: exit, step: step, whole: whole, parse: parse, enc: enc, items: items, areas: areas, range: range,
    state: function () {
      return cur && { topic: cur.t, index: cur.i, whole: cur.whole, total: cur.L.length, anchor: cur.L[cur.i].a, module: cur.mod && cur.mod.id,
        moved: cur.moved, locks: locks.map(function (l) { return l.a; }) };
    } };
})();
</script>"""

FOCUS_CSS = minify_css(FOCUS_CSS)
FOCUS_SCRIPT = "<script>" + minify_js(FOCUS_SCRIPT[len("<script>"):-len("</script>")]) + "</script>"
