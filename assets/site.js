/* =========================================================================
   Molecola — comportamento della pagina.
   Nessuna dipendenza esterna. Tutto cio' che sta qui e' un miglioramento:
   con JavaScript disattivato la pagina resta leggibile e navigabile.
   ========================================================================= */
(function () {
  "use strict";

  var root = document.documentElement;
  var L = root.getAttribute("lang") === "en" ? "en" : "it";
  var STR = {
    it: { copied: "Citazione copiata", copyFail: "Copia non riuscita",
          saved: "Aggiunto alla tua lista", unsaved: "Rimosso dalla lista",
          shown: "articoli mostrati", empty: "Nessun articolo salvato. Usa «Salva» su un articolo per aggiungerlo.",
          removeTitle: "Rimuovi" },
    en: { copied: "Citation copied", copyFail: "Could not copy",
          saved: "Added to your list", unsaved: "Removed from your list",
          shown: "articles shown", empty: "Nothing saved yet. Use “Save” on an article to add it.",
          removeTitle: "Remove" }
  }[L];

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  /* ---------- Tema ---------- */
  var THEME_KEY = "molecola:theme";
  function readStore(key) { try { return window.localStorage.getItem(key); } catch (e) { return null; } }
  function writeStore(key, val) { try { window.localStorage.setItem(key, val); } catch (e) { /* modalità privata */ } }

  var storedTheme = readStore(THEME_KEY);
  if (storedTheme === "dark" || storedTheme === "light") root.setAttribute("data-theme", storedTheme);

  $$("[data-action='theme']").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      var current = root.getAttribute("data-theme") || (systemDark ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      writeStore(THEME_KEY, next);
    });
  });

  /* ---------- Avviso temporaneo ---------- */
  var toast = $("#toast");
  var toastTimer = null;
  function say(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("on");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () { toast.classList.remove("on"); }, 2100);
  }

  /* ---------- Barra compatta allo scorrimento ---------- */
  var sticky = $("#sticky");
  var masthead = $(".masthead");
  if (sticky && masthead && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      sticky.classList.toggle("on", !entries[0].isIntersecting);
    }, { rootMargin: "-4px 0px 0px 0px", threshold: 0 }).observe(masthead);
  }

  /* ---------- Lista personale (solo su questo browser) ---------- */
  var SAVED_KEY = "molecola:saved";
  function loadSaved() {
    try { return JSON.parse(readStore(SAVED_KEY) || "[]"); } catch (e) { return []; }
  }
  function storeSaved(list) { writeStore(SAVED_KEY, JSON.stringify(list.slice(0, 500))); }
  var saved = loadSaved();
  function isSaved(id) { return saved.some(function (x) { return x.id === id; }); }

  var drawer = $("#saved-drawer");
  var drawerBody = $("#saved-body");
  var overlay = $("#overlay");
  var counters = $$(".saved-count");

  function itemFromNode(node) {
    var link = $("a[data-role='title']", node);
    return {
      id: node.getAttribute("data-id"),
      title: (link && link.textContent || "").trim(),
      url: link ? link.href : "",
      source: node.getAttribute("data-source-name") || "",
      date: node.getAttribute("data-date") || ""
    };
  }

  function refreshCounter() {
    counters.forEach(function (node) {
      node.textContent = saved.length;
      node.classList.toggle("on", saved.length > 0);
    });
  }

  function refreshDrawer() {
    if (!drawerBody) return;
    if (!saved.length) {
      drawerBody.innerHTML = "<p class='rail-note' style='padding:18px 0'>" + STR.empty + "</p>";
      return;
    }
    drawerBody.innerHTML = "";
    saved.forEach(function (entry) {
      var wrap = document.createElement("div");
      wrap.className = "saved-item";
      var title = document.createElement("p");
      title.className = "t";
      var a = document.createElement("a");
      a.href = entry.url; a.target = "_blank"; a.rel = "noopener";
      a.textContent = entry.title;
      title.appendChild(a);
      var meta = document.createElement("div");
      meta.className = "m";
      var span = document.createElement("span");
      span.textContent = entry.source + (entry.date ? " · " + entry.date.slice(0, 10) : "");
      var remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "×  " + STR.removeTitle;
      remove.addEventListener("click", function () { toggleSave(entry.id); });
      meta.appendChild(span); meta.appendChild(remove);
      wrap.appendChild(title); wrap.appendChild(meta);
      drawerBody.appendChild(wrap);
    });
  }

  function syncSaveButtons() {
    $$("[data-action='save']").forEach(function (btn) {
      var node = btn.closest("[data-id]");
      if (!node) return;
      btn.setAttribute("aria-pressed", isSaved(node.getAttribute("data-id")) ? "true" : "false");
    });
  }

  function toggleSave(id, node) {
    var existing = isSaved(id);
    if (existing) {
      saved = saved.filter(function (x) { return x.id !== id; });
      say(STR.unsaved);
    } else {
      var host = node || $("[data-id='" + id + "']");
      if (!host) return;
      saved.unshift(itemFromNode(host));
      say(STR.saved);
    }
    storeSaved(saved);
    refreshCounter(); refreshDrawer(); syncSaveButtons();
  }

  function openDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle("on", open);
    if (overlay) overlay.classList.toggle("on", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    if (open) { refreshDrawer(); var c = $("[data-action='close-drawer']", drawer); if (c) c.focus(); }
  }

  $$("[data-action='open-drawer']").forEach(function (b) {
    b.addEventListener("click", function () { openDrawer(!drawer.classList.contains("on")); });
  });
  $$("[data-action='close-drawer']").forEach(function (b) {
    b.addEventListener("click", function () { openDrawer(false); });
  });
  if (overlay) overlay.addEventListener("click", function () { openDrawer(false); });

  var clearBtn = $("[data-action='clear-saved']");
  if (clearBtn) clearBtn.addEventListener("click", function () {
    saved = []; storeSaved(saved); refreshCounter(); refreshDrawer(); syncSaveButtons();
  });

  /* ---------- Citazione e esportazioni ---------- */
  function citationOf(entry) {
    var day = entry.date ? entry.date.slice(0, 10) : "";
    return entry.source + (day ? ", " + day : "") + ". " + entry.title + ". " + entry.url;
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { say(STR.copied); },
        function () { say(STR.copyFail); });
      return;
    }
    var ta = document.createElement("textarea");
    ta.value = text; ta.setAttribute("readonly", "");
    ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); say(STR.copied); }
    catch (e) { say(STR.copyFail); }
    document.body.removeChild(ta);
  }

  function download(filename, mime, content) {
    var blob = new Blob([content], { type: mime + ";charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1200);
  }

  function csvCell(value) { return '"' + String(value == null ? "" : value).replace(/"/g, '""') + '"'; }

  var csvBtn = $("[data-action='export-csv']");
  if (csvBtn) csvBtn.addEventListener("click", function () {
    if (!saved.length) return;
    var rows = [["date", "source", "title", "url"].join(",")];
    saved.forEach(function (e) {
      rows.push([csvCell(e.date), csvCell(e.source), csvCell(e.title), csvCell(e.url)].join(","));
    });
    download("molecola-selezione.csv", "text/csv", "﻿" + rows.join("\r\n"));
  });

  var bibBtn = $("[data-action='export-bib']");
  if (bibBtn) bibBtn.addEventListener("click", function () {
    if (!saved.length) return;
    var seen = {};
    var entries = saved.map(function (e, index) {
      var year = (e.date || "").slice(0, 4) || "n.d.";
      var stem = (e.source || "src").toLowerCase().replace(/[^a-z0-9]+/g, "") + year;
      var key = stem; var n = 1;
      while (seen[key]) { key = stem + String.fromCharCode(96 + (++n)); }
      seen[key] = true;
      return "@online{" + key + ",\n" +
        "  title        = {" + e.title.replace(/[{}]/g, "") + "},\n" +
        "  organization = {" + e.source + "},\n" +
        "  year         = {" + year + "},\n" +
        "  urldate      = {" + new Date().toISOString().slice(0, 10) + "},\n" +
        "  url          = {" + e.url + "}\n}";
    });
    download("molecola-selezione.bib", "application/x-bibtex", entries.join("\n\n") + "\n");
  });

  document.addEventListener("click", function (event) {
    var btn = event.target.closest && event.target.closest("[data-action]");
    if (!btn) return;
    var action = btn.getAttribute("data-action");
    var node = btn.closest("[data-id]");
    if (action === "save" && node) { toggleSave(node.getAttribute("data-id"), node); }
    if (action === "cite" && node) { copyText(citationOf(itemFromNode(node))); }
  });

  refreshCounter(); syncSaveButtons(); refreshDrawer();

  /* ---------- Ricerca e filtri ---------- */
  var search = $("#search");
  var scope = $("#filterable");
  if (scope) {
    var entries = $$("[data-searchable]", scope);
    var groupHeads = $$(".day-head", scope);
    var emptyState = $("#empty-state");
    var resultCount = $("#result-count");
    var active = { category: null, source: null, lang: null };

    entries.forEach(function (node) {
      node._hay = ((node.getAttribute("data-title") || "") + " " +
        (node.getAttribute("data-source-name") || "") + " " +
        (node.textContent || "")).toLowerCase();
    });

    function apply() {
      var query = (search && search.value || "").trim().toLowerCase();
      var terms = query ? query.split(/\s+/) : [];
      var visible = 0;
      entries.forEach(function (node) {
        var ok = true;
        if (active.category && node.getAttribute("data-category") !== active.category) ok = false;
        if (ok && active.source && node.getAttribute("data-source") !== active.source) ok = false;
        if (ok && active.lang && node.getAttribute("data-lang") !== active.lang) ok = false;
        if (ok && terms.length) {
          ok = terms.every(function (term) { return node._hay.indexOf(term) !== -1; });
        }
        node.classList.toggle("is-hidden", !ok);
        if (ok) visible++;
      });
      // Un'intestazione di giorno sparisce se il suo gruppo e' rimasto vuoto.
      groupHeads.forEach(function (head) {
        var sibling = head.nextElementSibling, any = false;
        while (sibling && !sibling.classList.contains("day-head")) {
          if (sibling.hasAttribute("data-searchable") && !sibling.classList.contains("is-hidden")) { any = true; break; }
          sibling = sibling.nextElementSibling;
        }
        head.classList.toggle("is-hidden", !any);
      });
      if (emptyState) emptyState.classList.toggle("on", visible === 0);
      if (resultCount) resultCount.textContent = visible + " " + STR.shown;
    }

    $$(".chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        var dimension = chip.getAttribute("data-dim");
        var value = chip.getAttribute("data-value") || null;
        active[dimension] = (active[dimension] === value) ? null : value;
        $$(".chip[data-dim='" + dimension + "']").forEach(function (other) {
          var on = other.getAttribute("data-value") === active[dimension];
          other.setAttribute("aria-pressed", on ? "true" : "false");
        });
        apply();
      });
    });

    var reset = $("[data-action='reset-filters']");
    if (reset) reset.addEventListener("click", function () {
      active = { category: null, source: null, lang: null };
      if (search) search.value = "";
      $$(".chip").forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
      apply();
    });

    if (search) {
      var debounce = null;
      search.addEventListener("input", function () {
        window.clearTimeout(debounce);
        debounce = window.setTimeout(apply, 110);
      });
      search.addEventListener("keydown", function (event) {
        if (event.key === "Escape") { search.value = ""; apply(); search.blur(); }
      });
    }
    apply();
  }

  /* ---------- Tastiera ---------- */
  document.addEventListener("keydown", function (event) {
    var tag = (event.target.tagName || "").toLowerCase();
    var typing = tag === "input" || tag === "textarea" || event.target.isContentEditable;
    if (event.key === "/" && !typing && search) { event.preventDefault(); search.focus(); search.select(); }
    if (event.key === "Escape" && drawer && drawer.classList.contains("on")) openDrawer(false);
  });
})();

/* Orario locale del lettore: il build gira in UTC, ma chi legge sta altrove. */
(function () {
  "use strict";
  var lang = document.documentElement.getAttribute("lang") === "en" ? "en-GB" : "it-IT";
  Array.prototype.forEach.call(document.querySelectorAll("time[data-localtime]"), function (node) {
    var iso = node.getAttribute("datetime");
    if (!iso) return;
    var when = new Date(iso);
    if (isNaN(when.getTime())) return;
    try {
      node.textContent = new Intl.DateTimeFormat(lang, {
        day: "numeric", month: "long", hour: "2-digit", minute: "2-digit"
      }).format(when);
      node.title = new Intl.DateTimeFormat(lang, { dateStyle: "full", timeStyle: "long" }).format(when);
    } catch (e) { /* si tiene il testo generato dal build */ }
  });
})();
