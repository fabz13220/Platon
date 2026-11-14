/* BLIZ · traductions. Chargé seulement quand la langue choisie n'est pas le français (voir le haut de platoz.html).
   Le code du jeu reste écrit en français. Ce fichier :
   - remplace les cartes par leur traduction (I18N.cards, appelé par platoz.html) : cards[jeu]["champs|français"] = [champs traduits] ;
   - traduit tout texte affiché à l'écran : chaque texte de l'interface est cherché dans le dictionnaire de la langue
     (exact, sinon par motif avec des trous {}), y compris les messages, les infobulles et l'image de la story.
   Données : window.BLIZ_LANG, dans i18n/<langue>.js (ui, re, cards, locale). */
(function () {
  const L = window.BLIZ_LANG;
  if (!L) return;
  const ui = L.ui || {};
  // motifs : "Manche {} / {}" → /^Manche (.*?) \/ (.*?)$/ ; dans la traduction, {1} = le 1er trou (traduit s'il est connu),
  // {2?cartes:carte} = « cartes » si le 2e trou n'est pas vide (pluriels)
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  // {#} : un trou qui ne prend que des chiffres ; {s} : un trou court (un prénom)
  const re = Object.entries(L.re || {}).map(([k, v]) => [new RegExp("^" + k.split(/(\{\}|\{#\}|\{s\})/).map((x, i) => i % 2 ? (x === "{#}" ? "(\\d+)" : x === "{s}" ? "(.{1,24}?)" : "(.*?)") : esc(x)).join("") + "$", "s"), v, k.length])
    .sort((a, b) => b[2] - a[2]);
  // {1-} : le trou sans le « de » / « d' » français devant (« Au tour d'Inès » → « Inès »)
  const fillPat = (v, g) => v.replace(/\{(\d)(-)?(?:\?([^:}]*):([^}]*))?\}/g, (_, n, de, yes, no) => {
    let x = g[+n] == null ? "" : g[+n];
    if (de) x = x.replace(/^(de |d['’])/, "");
    if (yes !== undefined) return x.trim() ? yes : no;
    return trText(x);
  });
  function trText(t) {
    if (!t) return t;
    const r = ui[t];
    if (r !== undefined) return r;
    for (const [rx, v] of re) { const m = t.match(rx); if (m) return fillPat(v, m); }
    // emoji ou symbole devant (« 🧼 Hygiène », « ⚡ … ») : on traduit le reste
    const e = t.match(/^([^\p{L}\p{N}«"'(]+)(\p{L}.*)$/u);
    if (e) { const r2 = trText(e[2]); if (r2 !== e[2]) return e[1] + r2; }
    return t;
  }
  // garde les espaces autour du texte (« Je n'ai jamais <b>…</b> »)
  // un texte déjà traduit n'est pas retraduit (en danois, « Rapportér et problem » tombait sur le motif « {} et {} »)
  const done = new Set();
  function tr(s) {
    if (typeof s !== "string" || !/[A-Za-zÀ-ÿ]/.test(s)) return s;
    const a = s.match(/^\s*/)[0].length, b = s.match(/\s*$/)[0].length;
    const core = s.slice(a, s.length - b).replace(/\s+/g, " ");
    if (done.has(core)) return s;
    const t = trText(core);
    if (t !== core) done.add(t);
    return t === core ? s : s.slice(0, a) + t + s.slice(s.length - b);
  }

  /* ---------- cartes ---------- */
  // une carte traduite garde l'originale dans .fr (votes, auteurs et cartes retirées restent liés à la carte française)
  const custom = (() => { try { return new Set((JSON.parse(localStorage.getItem("scandale:custom")) || []).map(o => o.type + ":" + o.card.slice(1).join("|"))); } catch (e) { return new Set(); } })();
  const hot = new Set();
  function cards(C, opt) {
    opt = opt || {};
    for (const k in C) {
      const m = (L.cards || {})[k];
      if (!m) continue; // jeu pas encore traduit : il reste en français
      const out = [];
      for (const c of C[k]) {
        if (c.fr) { out.push(c); continue; }
        const key = c.slice(1).join("|"), f = m[key];
        if (!f) { if (custom.has(k + ":" + key)) out.push(c); continue; } // carte pas traduite (ou réécrite dans l'admin) : retirée
        // les cartes traduites ne repassent pas dans les motifs (une carte danoise « … et … » n'est pas un « {} et {} » français)
        for (const x of f) for (const p of String(x).split("{q}")) { const q = p.trim().replace(/\s+/g, " "); if (q) done.add(q); }
        const t = [c[0], ...f]; // L'Imposteur : un 4e champ traduit = le mot du faux sosie
        t.fr = c;
        if (opt.isHot && opt.isHot(k, c)) hot.add(f.join(" "));
        out.push(t);
      }
      C[k].length = 0; C[k].push(...out);
    }
  }
  const cardText = (k, s) => { const f = ((L.cards || {})[k] || {})[s]; return f ? f[0] : s; };

  /* ---------- écran ---------- */
  const ATTR = ["placeholder", "aria-label", "title", "alt"];
  const SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1 }; // les <svg> sont parcourus : la roue des jeux y écrit le nom des jeux
  function fixEl(el) {
    for (const a of ATTR) { const v = el.getAttribute(a); if (v) { const t = tr(v); if (t !== v) el.setAttribute(a, t); } }
  }
  function walk(root) {
    if (root.nodeType === 3) { fixText(root); return; }
    if (root.nodeType !== 1 || SKIP[root.nodeName]) return;
    fixEl(root);
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
      acceptNode: n => n.nodeType === 1 && SKIP[n.nodeName] ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
    });
    let n; while ((n = w.nextNode())) n.nodeType === 3 ? fixText(n) : fixEl(n);
  }
  function fixText(n) {
    const p = n.parentNode; if (p && SKIP[p.nodeName]) return;
    const v = n.nodeValue, t = tr(v); if (t !== v) n.nodeValue = t;
  }
  function start() {
    document.documentElement.lang = L.code;
    if (document.title) document.title = tr(document.title);
    walk(document.body);
    new MutationObserver(list => {
      for (const r of list) {
        if (r.type === "childList") r.addedNodes.forEach(walk);
        else if (r.type === "characterData") fixText(r.target);
        else if (r.type === "attributes") fixEl(r.target);
      }
    }).observe(document.documentElement, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTR });
  }
  if (document.body) start(); else document.addEventListener("DOMContentLoaded", start);

  // fenêtres du navigateur, partage et image de la story
  for (const f of ["alert", "confirm", "prompt"]) { const o = window[f]; if (o) window[f] = function (m, ...a) { return o.call(window, tr(String(m)), ...a); }; }
  if (navigator.share) { const o = navigator.share.bind(navigator); navigator.share = d => o(d && d.text ? Object.assign({}, d, { text: tr(d.text) }) : d); }
  const P = window.CanvasRenderingContext2D && CanvasRenderingContext2D.prototype;
  if (P) for (const f of ["fillText", "strokeText", "measureText"]) { const o = P[f]; P[f] = function (t, ...a) { return o.call(this, tr(String(t)), ...a); }; }

  window.I18N = { lang: L.code, locale: L.locale, tr, cards, cardText, hot, name: L.name };
})();
