#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generazione delle pagine HTML.

Tutto il sito nasce da qui: home italiana e inglese, indice e pagine
dell'archivio per anno, feed RSS, sitemap. Niente piu' sostituzione di
segnaposto dentro un HTML scritto a mano — l'HTML e' un prodotto del build,
e cambiarlo significa cambiare questo file.
"""
import html
import json
import os
import re
from datetime import datetime, timedelta, timezone

import i18n
import sources as S

SITE_URL = "https://deltadidirac30.github.io/molecola"
REPO_URL = "https://github.com/deltadidirac30/molecola"

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Newsreader:ital,opsz,wght@0,6..72,200..700;1,6..72,200..700"
         "&family=Libre+Franklin:wght@400;500;600;700"
         "&family=IBM+Plex+Mono:wght@400;500&display=swap")

CURRENT_ATTR = ' aria-current="page"'
LEAD_COUNT = 1
GRID_COUNT = 9


def esc(text, quote=True):
    return html.escape(str(text if text is not None else ""), quote=quote)


def rel(depth, path):
    """URL relativo alla radice del sito da una pagina profonda `depth`."""
    return ("../" * depth) + path.lstrip("/") if depth else (path.lstrip("/") or "./")


def parse_dt(value):
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def _icon(name):
    paths = {
        "search": '<circle cx="7" cy="7" r="5.2"/><path d="M11 11l4 4"/>',
        "bookmark": '<path d="M4 2h8v13l-4-3-4 3z"/>',
        "quote": '<path d="M3 3h7v3H6v7H3z"/><path d="M11 3h5v3h-3v7h-2z"/>',
        "sun": ('<circle cx="8" cy="8" r="3.1"/><path d="M8 .8v2M8 13.2v2M.8 8h2M13.2 8h2'
                'M2.9 2.9l1.4 1.4M11.7 11.7l1.4 1.4M13.1 2.9l-1.4 1.4M4.3 11.7l-1.4 1.4"/>'),
        "close": '<path d="M3 3l10 10M13 3L3 13"/>',
    }
    return (f'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" '
            f'stroke-linecap="round" aria-hidden="true">{paths[name]}</svg>')


# ----------------------------------------------------------------------
# Involucro
# ----------------------------------------------------------------------

def document(lang, *, depth, title, description, body, canonical, alternate,
             page_id="", extra_head=""):
    t = lambda key, **kw: i18n.t(lang, key, **kw)
    css = rel(depth, "assets/site.css")
    js = rel(depth, "assets/site.js")
    og_image = f"{SITE_URL}/assets/social.svg"
    return f"""<!DOCTYPE html>
<html lang="{i18n.T[lang]['html_lang']}" data-page="{esc(page_id)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="alternate" hreflang="it" href="{esc(alternate['it'])}">
<link rel="alternate" hreflang="en" href="{esc(alternate['en'])}">
<link rel="alternate" hreflang="x-default" href="{esc(alternate['it'])}">
<link rel="alternate" type="application/rss+xml" title="Molecola" href="{rel(depth, 'feed.xml')}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Molecola">
<meta property="og:locale" content="{'it_IT' if lang == 'it' else 'en_GB'}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_image)}">
<meta name="theme-color" content="#FBFAF6" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#131310" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{rel(depth, 'assets/favicon.svg')}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="{css}">
{extra_head}</head>
<body>
<a class="skip-link" href="#main">{esc(t('skip'))}</a>
{body}
<div class="overlay" id="overlay"></div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script src="{js}" defer></script>
</body>
</html>
"""


def masthead(lang, *, depth, dateline, active, alternate_href):
    t = lambda key, **kw: i18n.t(lang, key, **kw)
    home_page = rel(depth, "index.html" if lang == "it" else "en/index.html")

    def anchor(fragment):
        # Sulla home l'ancora e' interna alla pagina; altrove va risolta sulla home.
        return fragment if active == "home" else home_page + fragment

    nav_items = [
        ("wire", anchor("#wire"), t("nav_wire")),
        ("data", anchor("#numeri"), t("nav_data")),
        ("archive", rel(depth, "archivio/index.html" if lang == "it" else "en/archive/index.html"), t("nav_archive")),
        ("sources", anchor("#fonti"), t("nav_sources")),
        ("about", anchor("#metodo"), t("nav_about")),
    ]
    nav_html = "\n".join(
        '        <a href="%s"%s>%s</a>' % (esc(href), CURRENT_ATTR if key == active else "", esc(label))
        for key, href, label in nav_items)
    home = home_page
    return f"""<div class="sticky-bar" id="sticky">
  <div class="sticky-inner">
    <a class="sticky-name" href="{esc(home)}">Molecola</a>
    <div class="sticky-links">
      <button class="ctrl" type="button" data-action="open-drawer" aria-label="{esc(t('saved_panel'))}">
        {_icon('bookmark')}<span>{esc(t('saved_panel'))}</span><span class="saved-count">0</span></button>
      <button class="ctrl" type="button" data-action="theme" aria-label="{esc(t('theme_toggle'))}">{_icon('sun')}</button>
    </div>
  </div>
</div>

<header class="masthead">
  <div class="wrap">
    <div class="masthead-top">
      <div class="masthead-side left">
        <span class="dateline">{esc(dateline)}</span>
      </div>
      <a class="wordmark" href="{esc(home)}">
        <span class="wordmark-row">
          <svg class="wordmark-mark" viewBox="0 0 34 24" aria-hidden="true">
            <circle cx="8.6" cy="12" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/>
            <circle cx="25.4" cy="12" r="7" fill="none" stroke="currentColor" stroke-width="1.8"/>
            <path d="M15.9 12h2.2" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
          </svg>
          <span class="wordmark-name">Molecola</span>
        </span>
        <span class="wordmark-sub">{esc(t('tagline'))}</span>
      </a>
      <div class="masthead-side right">
        <button class="ctrl" type="button" data-action="open-drawer">
          {_icon('bookmark')}<span>{esc(t('saved_panel'))}</span><span class="saved-count">0</span></button>
        <button class="ctrl" type="button" data-action="theme" aria-label="{esc(t('theme_toggle'))}">{_icon('sun')}</button>
        <a class="lang-switch" href="{esc(alternate_href)}" title="{esc(t('other_lang_title'))}">{esc(t('other_lang_label'))}</a>
      </div>
    </div>
    <div class="masthead-rule"></div>
    <nav class="nav" aria-label="{esc(t('nav_wire'))}">
{nav_html}
        <a href="{esc(REPO_URL)}" target="_blank" rel="noopener">{esc(t('nav_code'))}</a>
    </nav>
  </div>
</header>
"""


def drawer(lang):
    t = lambda key, **kw: i18n.t(lang, key, **kw)
    return f"""<aside class="drawer" id="saved-drawer" aria-hidden="true" aria-label="{esc(t('saved_panel'))}">
  <div class="drawer-head">
    <h2>{esc(t('saved_panel'))}</h2>
    <button class="ctrl" type="button" data-action="close-drawer" aria-label="{esc(t('close'))}">{_icon('close')}</button>
  </div>
  <div class="drawer-body" id="saved-body"></div>
  <div class="drawer-foot">
    <button class="btn btn-primary" type="button" data-action="export-csv">{esc(t('export_csv'))}</button>
    <button class="btn" type="button" data-action="export-bib">{esc(t('export_bib'))}</button>
    <button class="btn" type="button" data-action="clear-saved">{esc(t('clear_saved'))}</button>
    <p class="drawer-note">{esc(t('saved_note'))}</p>
  </div>
</aside>
"""


def footer(lang, *, depth, report):
    t = lambda key, **kw: i18n.t(lang, key, **kw)
    reached = sum(1 for r in report if r["ok"] and r["count"])
    groups = {"industria": [], "politica": [], "ricerca": []}
    for source in S.SOURCES:
        groups[source["category"]].append(source)
    columns = []
    for category, items in groups.items():
        links = "\n".join(
            f'        <li><a href="{esc(s["home"])}" target="_blank" rel="noopener">{esc(s["name"])}</a></li>'
            for s in sorted(items, key=lambda s: s["name"].lower()))
        columns.append(f"""      <div>
        <h3>{esc(t('cat_' + category))}</h3>
        <ul class="footer-links">
{links}
        </ul>
      </div>""")
    return f"""<footer class="site-footer" id="fonti">
  <div class="wrap">
    <div class="footer-grid">
{chr(10).join(columns)}
      <div>
        <h3>Molecola</h3>
        <ul class="footer-links">
          <li><a href="{esc(rel(depth, 'archivio/index.html' if lang == 'it' else 'en/archive/index.html'))}">{esc(t('archive_title'))}</a></li>
          <li><a href="{esc(rel(depth, 'feed.xml'))}">{esc(t('feed_link'))}</a></li>
          <li><a href="{esc(rel(depth, 'data/archive.json'))}">{esc(t('archive_download'))}</a></li>
          <li><a href="{esc(REPO_URL)}" target="_blank" rel="noopener">{esc(t('nav_code'))}</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>{esc(t('rights'))}</p>
      <p>{esc(t('footer_purpose'))} · {reached}/{len(S.SOURCES)} {esc(t('sources_reached'))}</p>
    </div>
  </div>
</footer>
"""


# ----------------------------------------------------------------------
# Blocchi della prima pagina
# ----------------------------------------------------------------------

def _authors_line(item, lang):
    names = item.get("authors") or []
    if not names:
        return ""
    shown = ", ".join(names[:3])
    if len(names) > 3:
        shown += " " + i18n.t(lang, "authors_more")
    return shown


def _item_attrs(item):
    return (f'data-id="{esc(item["id"])}" data-searchable '
            f'data-category="{esc(item["category"])}" '
            f'data-source="{esc(item["source_slug"])}" '
            f'data-source-name="{esc(item["source"])}" '
            f'data-lang="{esc(item.get("lang") or "en")}" '
            f'data-date="{esc(item["date"])}" '
            f'data-title="{esc((item["title"] or "").lower())}"')


def _actions(lang):
    t = lambda key: i18n.t(lang, key)
    return (f'<span class="story-actions">'
            f'<button class="act" type="button" data-action="save" aria-pressed="false" '
            f'title="{esc(t("save_title"))}">{_icon("bookmark")}<span>{esc(t("save"))}</span></button>'
            f'<button class="act" type="button" data-action="cite" '
            f'title="{esc(t("cite_title"))}">{_icon("quote")}<span>{esc(t("cite"))}</span></button>'
            f'</span>')


def _kicker(item, lang):
    t = lambda key: i18n.t(lang, key)
    paywall = (f'<span class="badge-paywall" title="{esc(t("paywall_title"))}">'
               f'{esc(t("paywall"))}</span>') if item.get("paywall") else ""
    return (f'<p class="story-kicker">'
            f'<span class="cat">{esc(t("cat_" + item["category"]))}</span>'
            f'<span class="sep">|</span>'
            f'<span class="src">{esc(item["source"])}</span>{paywall}</p>')


def _meta(item, lang):
    dt = parse_dt(item["date"])
    day = i18n.format_date(dt, lang) if dt else ""
    authors = _authors_line(item, lang)
    bits = [f'<span>{esc(day)}</span>']
    if authors:
        bits.append(f'<span>{esc(authors)}</span>')
    return f'<div class="story-meta">{"".join(bits)}{_actions(lang)}</div>'


def story_html(item, lang, *, lead=False):
    excerpt = (f'<p class="excerpt">{esc(item["excerpt"])}</p>'
               if item.get("excerpt") else "")
    tag = "h2" if lead else "h3"
    classes = "lead" if lead else "story"
    return f"""<article class="{classes}" id="item-{esc(item['id'])}" {_item_attrs(item)}>
  {_kicker(item, lang)}
  <{tag}><a href="{esc(item['link'])}" data-role="title" target="_blank" rel="noopener">{esc(item['title'])}</a></{tag}>
  {excerpt}
  {_meta(item, lang)}
</article>"""


def digest_html(items, lang):
    t = lambda key: i18n.t(lang, key)
    now = datetime.now(timezone.utc)
    today, yesterday = now.date(), (now - timedelta(days=1)).date()
    week_start = (now - timedelta(days=7)).date()

    def bucket(item):
        dt = parse_dt(item["date"])
        if not dt:
            return t("earlier")
        day = dt.date()
        if day >= today:
            return t("today")
        if day == yesterday:
            return t("yesterday")
        if day > week_start:
            return t("this_week")
        return t("earlier")

    chunks, current = [], None
    for item in items:
        label = bucket(item)
        if label != current:
            if current is not None:
                chunks.append('</div>')
            chunks.append(f'<h3 class="day-head">{esc(label)}</h3><div class="digest">')
            current = label
        dt = parse_dt(item["date"])
        day = f"{dt:%d.%m}" if dt else "--.--"
        paywall = (f' <span class="badge-paywall">{esc(t("paywall"))}</span>'
                   if item.get("paywall") else "")
        chunks.append(f"""<article class="digest-item" id="item-{esc(item['id'])}" {_item_attrs(item)}>
  <span class="digest-date">{esc(day)}</span>
  <div>
    <p class="digest-title"><a href="{esc(item['link'])}" data-role="title" target="_blank" rel="noopener">{esc(item['title'])}</a></p>
    <span class="digest-src">{esc(item['source'])}{paywall}</span>
  </div>
</article>""")
    if current is not None:
        chunks.append('</div>')
    return ''.join(chunks)


def controls_html(lang, items):
    t = lambda key: i18n.t(lang, key)
    counts_cat, counts_src, counts_lang = {}, {}, {}
    for item in items:
        counts_cat[item["category"]] = counts_cat.get(item["category"], 0) + 1
        counts_src[item["source_slug"]] = counts_src.get(item["source_slug"], 0) + 1
        counts_lang[item.get("lang") or "en"] = counts_lang.get(item.get("lang") or "en", 0) + 1

    def chips(dimension, pairs):
        return "".join(
            f'<button class="chip" type="button" data-dim="{dimension}" data-value="{esc(value)}" '
            f'aria-pressed="false">{esc(label)}<span class="n">{count}</span></button>'
            for value, label, count in pairs)

    cat_pairs = [(c, t("cat_" + c), counts_cat[c])
                 for c in ("industria", "politica", "ricerca") if counts_cat.get(c)]
    src_pairs = sorted(((s["slug"], s["name"], counts_src[s["slug"]])
                        for s in S.SOURCES if counts_src.get(s["slug"])),
                       key=lambda p: p[1].lower())
    lang_pairs = [(code, t("lang_" + code), counts_lang[code])
                  for code in ("en", "it") if counts_lang.get(code)]

    lang_group = (f'<div class="filter-group"><span class="kicker">{esc(t("filter_lang"))}</span>'
                  f'{chips("lang", lang_pairs)}</div>') if len(lang_pairs) > 1 else ""

    return f"""<div class="controls">
  <div class="search-row">
    {_icon('search')}
    <input class="search-input" id="search" type="search" autocomplete="off"
           placeholder="{esc(t('search_placeholder'))}" aria-label="{esc(t('search_label'))}">
    <span class="search-hint">/</span>
  </div>
  <div class="filters">
    <div class="filter-group"><span class="kicker">{esc(t('filter_category'))}</span>{chips("category", cat_pairs)}</div>
    {lang_group}
  </div>
  <div class="filters" style="margin-top:9px">
    <div class="filter-group"><span class="kicker">{esc(t('filter_source'))}</span>{chips("source", src_pairs)}</div>
  </div>
  <p class="result-line">
    <span id="result-count">{len(items)} {esc(t('results_count'))}</span>
    <button type="button" data-action="reset-filters">{esc(t('reset_filters'))}</button>
  </p>
</div>"""


def figures_html(lang, indicators):
    t = lambda key: i18n.t(lang, key)
    rows = []
    for figure in indicators["figures"]:
        meter = (f'<div class="fig-meter"><span style="width:{figure["meter"]}%"></span></div>'
                 if figure.get("meter") else "")
        rows.append(f"""<li>
  <span class="fig-label">{esc(figure['label'][lang])}</span>
  <p class="fig-value">{esc(figure['value'])}<span class="unit">{esc(figure['unit'][lang])}</span></p>
  {meter}
  <p class="fig-note">{esc(figure['note'][lang])}</p>
  <span class="fig-cite"><a href="{esc(figure['url'])}" target="_blank" rel="noopener">{esc(figure['cite'])}</a></span>
</li>""")
    return f"""<div class="rail-block" id="numeri">
  <h2>{esc(t('section_data'))}</h2>
  <p class="rail-note">{esc(indicators['source_label'])} · {esc(indicators['license'])}</p>
  <ul class="figures">
{"".join(rows)}
  </ul>
</div>"""


def research_rail(lang, research):
    if not research:
        return ""
    t = lambda key: i18n.t(lang, key)
    rows = []
    for item in research[:6]:
        dt = parse_dt(item["date"])
        authors = _authors_line(item, lang)
        meta = " · ".join(x for x in [item["source"], authors,
                                      i18n.format_date(dt, lang) if dt else ""] if x)
        rows.append(f"""<li>
  <p class="r-title"><a href="#item-{esc(item['id'])}">{esc(item['title'])}</a></p>
  <p class="r-meta">{esc(meta)}</p>
</li>""")
    return f"""<div class="rail-block" id="ricerca">
  <h2>{esc(t('section_research'))}</h2>
  <p class="rail-note">{esc(t('section_research_note'))}</p>
  <ul class="research">
{"".join(rows)}
  </ul>
</div>"""


def method_band(lang, indicators):
    t = lambda key: i18n.t(lang, key)
    body = "".join(f"<p>{paragraph}</p>" for paragraph in i18n.T[lang]["method_body"])
    return f"""<section class="band" id="metodo">
  <div class="section-head"><h2>{esc(t('section_method'))}</h2></div>
  <div class="band-grid">
    <div class="prose">{body}</div>
    <div class="prose">
      <h3>{esc(t('section_sources'))}</h3>
      <p>{len(S.SOURCES)} {esc(t('sources_reached'))} · <a href="{esc(REPO_URL)}/blob/main/scripts/sources.py" target="_blank" rel="noopener">scripts/sources.py</a></p>
      <p>{esc(t('rights'))}</p>
    </div>
  </div>
</section>"""


def front_page(lang, *, items, research, report, built_at, indicators, archive_total):
    t = lambda key, **kw: i18n.t(lang, key, **kw)
    depth = 0 if lang == "it" else 1
    alternate = {"it": f"{SITE_URL}/", "en": f"{SITE_URL}/en/"}
    alt_href = rel(depth, "en/index.html") if lang == "it" else rel(depth, "index.html")

    # Apertura e griglia pescano solo fra le notizie: i preprint arrivano a ritmo
    # quotidiano e, ordinati per data, finirebbero sistematicamente ad aprire la
    # pagina. Restano nel riepilogo, in ordine di data, e nell'indice di colonna.
    news = [i for i in items if i["category"] != "ricerca"]
    lead = news[:LEAD_COUNT]
    grid = news[LEAD_COUNT:LEAD_COUNT + GRID_COUNT]
    promoted = {i["id"] for i in lead + grid}
    rest = [i for i in items if i["id"] not in promoted]

    reached = sum(1 for r in report if r["ok"] and r["count"])
    newest = parse_dt(items[0]["date"]) if items else None
    warn = ('<span class="status-warn">' + esc(t("health_warning")) + "</span>"
            if reached < 5 else "")

    status = f"""<div class="status">
  <span class="status-live"><span class="live-dot" aria-hidden="true"></span>
    {esc(t('updated_prefix'))}
    <time datetime="{esc(built_at.isoformat(timespec='seconds'))}" data-localtime>{esc(i18n.format_date(built_at, lang, with_time=True))} UTC</time></span>
  <span><b>{reached}</b>/{len(S.SOURCES)} {esc(t('sources_reached'))}</span>
  <span><b>{len(items)}</b> {esc(t('articles_in_feed'))}</span>
  <span><b>{archive_total}</b> {esc(t('in_archive'))}</span>
  {f'<span>{esc(t("newest_article"))} <b>{esc(i18n.format_date(newest, lang))}</b></span>' if newest else ''}
  {warn}
</div>"""

    body = f"""{masthead(lang, depth=depth, dateline=i18n.format_dateline(built_at, lang), active='home', alternate_href=alt_href)}
<div class="wrap">{status}</div>
<main id="main">
  <div class="wrap">
    <div class="front">
      <div id="wire">
        {controls_html(lang, items)}
        <div id="filterable">
          {"".join(story_html(item, lang, lead=True) for item in lead)}
          <div class="stories">
            {"".join(story_html(item, lang) for item in grid)}
          </div>
          <div class="section-head" style="margin-top:14px">
            <h2>{esc(t('section_more'))}</h2>
            <span class="note">{esc(t('search_hint'))}</span>
          </div>
          {digest_html(rest, lang)}
        </div>
        <p class="empty-state" id="empty-state">{esc(t('no_results'))}</p>
      </div>
      <aside class="rail">
        {figures_html(lang, indicators)}
        {research_rail(lang, research)}
      </aside>
    </div>
    {method_band(lang, indicators)}
  </div>
</main>
{drawer(lang)}
{footer(lang, depth=depth, report=report)}"""

    return document(lang, depth=depth,
                    title=f"Molecola — {t('tagline')}",
                    description=t("description"),
                    body=body, canonical=alternate[lang], alternate=alternate,
                    page_id="home")


# ----------------------------------------------------------------------
# Archivio
# ----------------------------------------------------------------------

def archive_paths(lang, year=None):
    base = "archivio" if lang == "it" else "en/archive"
    return f"{base}/index.html" if year is None else f"{base}/{year}/index.html"


def archive_index(lang, *, per_year, built_at, report, total):
    t = lambda key, **kw: i18n.t(lang, key, **kw)
    depth = 1 if lang == "it" else 2
    alternate = {"it": f"{SITE_URL}/archivio/", "en": f"{SITE_URL}/en/archive/"}
    alt_href = rel(depth, archive_paths("en" if lang == "it" else "it"))

    cards = "".join(
        f'<a href="{esc(rel(depth, archive_paths(lang, year)))}">{esc(year)}'
        f'<span class="n">{count}</span></a>'
        for year, count in per_year)

    body = f"""{masthead(lang, depth=depth, dateline=i18n.format_dateline(built_at, lang), active='archive', alternate_href=alt_href)}
<main id="main">
  <div class="wrap">
    <div class="archive-head">
      <p class="kicker">Molecola</p>
      <h1>{esc(t('archive_title'))}</h1>
      <p class="intro">{esc(t('archive_intro'))}</p>
      <div class="year-nav">{cards}</div>
      <p class="rail-note" style="margin-top:18px">{total} {esc(t('archive_items'))} · <a href="{esc(rel(depth, 'data/archive.json'))}">{esc(t('archive_download'))}</a></p>
    </div>
  </div>
</main>
{drawer(lang)}
{footer(lang, depth=depth, report=report)}"""

    return document(lang, depth=depth,
                    title=f"{t('archive_title')} — Molecola",
                    description=t("archive_intro"),
                    body=body, canonical=alternate[lang], alternate=alternate,
                    page_id="archive")


def archive_year(lang, year, items, *, per_year, built_at, report):
    t = lambda key, **kw: i18n.t(lang, key, **kw)
    depth = 2 if lang == "it" else 3
    alternate = {"it": f"{SITE_URL}/archivio/{year}/", "en": f"{SITE_URL}/en/archive/{year}/"}
    alt_href = rel(depth, archive_paths("en" if lang == "it" else "it", year))

    by_month = {}
    for item in items:
        month = (item.get("date") or "")[5:7]
        by_month.setdefault(month, []).append(item)

    month_links, blocks = [], []
    for month in sorted(by_month, reverse=True):
        name = i18n.MONTHS[lang][int(month) - 1]
        rows = []
        for item in by_month[month]:
            dt = parse_dt(item["date"])
            paywall = (f' <span class="badge-paywall">{esc(t("paywall"))}</span>'
                       if item.get("paywall") else "")
            rows.append(f"""<article class="arch-item" {_item_attrs(item)}>
  <span class="arch-date">{esc(f'{dt:%d %b}' if dt else '')}</span>
  <p class="arch-title"><a href="{esc(item['link'])}" data-role="title" target="_blank" rel="noopener">{esc(item['title'])}</a></p>
  <span class="arch-src">{esc(item['source'])}{paywall}</span>
</article>""")
        month_links.append(f'<a href="#m{month}">{esc(name)}</a>')
        blocks.append(f"""<section class="month-block" id="m{month}">
  <h2>{esc(name)} {esc(year)} <span class="n">{len(by_month[month])}</span></h2>
  <div class="arch-list">{"".join(rows)}</div>
</section>""")

    years_nav = "".join(
        '<a href="%s"%s>%s<span class="n">%d</span></a>' % (
            esc(rel(depth, archive_paths(lang, y))),
            CURRENT_ATTR if y == year else "", esc(y), c)
        for y, c in per_year)

    body = f"""{masthead(lang, depth=depth, dateline=i18n.format_dateline(built_at, lang), active='archive', alternate_href=alt_href)}
<main id="main">
  <div class="wrap">
    <div class="archive-head">
      <p class="kicker"><a href="{esc(rel(depth, archive_paths(lang)))}" style="color:inherit">{esc(t('archive_all_years'))}</a></p>
      <h1>{esc(t('archive_year', year=year))}</h1>
      <p class="intro">{len(items)} {esc(t('archive_items'))}</p>
      <div class="year-nav">{years_nav}</div>
      <div class="search-row" style="margin-top:20px">
        {_icon('search')}
        <input class="search-input" id="search" type="search" autocomplete="off"
               placeholder="{esc(t('archive_search', year=year))}" aria-label="{esc(t('archive_search', year=year))}">
      </div>
      <p class="result-line"><span id="result-count"></span>
        <button type="button" data-action="reset-filters">{esc(t('reset_filters'))}</button></p>
    </div>
    <nav class="month-nav" aria-label="{esc(t('archive_title'))}">{"".join(month_links)}</nav>
    <div id="filterable">{"".join(blocks)}</div>
    <p class="empty-state" id="empty-state">{esc(t('no_results'))}</p>
  </div>
</main>
{drawer(lang)}
{footer(lang, depth=depth, report=report)}"""

    return document(lang, depth=depth,
                    title=f"{t('archive_year', year=year)} — Molecola",
                    description=f"{t('archive_intro')} ({year})",
                    body=body, canonical=alternate[lang], alternate=alternate,
                    page_id="archive-year")


# ----------------------------------------------------------------------
# Feed e sitemap
# ----------------------------------------------------------------------

def rss_feed(items, built_at, limit=60):
    def rfc822(value):
        dt = parse_dt(value)
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000") if dt else ""
    entries = []
    for item in items[:limit]:
        entries.append(f"""    <item>
      <title>{esc(item['title'], quote=False)}</title>
      <link>{esc(item['link'], quote=False)}</link>
      <guid isPermaLink="false">molecola-{esc(item['id'], quote=False)}</guid>
      <pubDate>{rfc822(item['date'])}</pubDate>
      <source url="{esc(SITE_URL)}/">{esc(item['source'], quote=False)}</source>
      <description>{esc((item.get('excerpt') or item['title']) + ' — ' + item['source'], quote=False)}</description>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Molecola — Osservatorio idrogeno</title>
    <link>{SITE_URL}/</link>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{esc(i18n.T['it']['description'], quote=False)}</description>
    <language>it</language>
    <lastBuildDate>{built_at.strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
    <ttl>180</ttl>
{chr(10).join(entries)}
  </channel>
</rss>
"""


def sitemap(years, built_at):
    day = built_at.strftime("%Y-%m-%d")
    urls = [f"{SITE_URL}/", f"{SITE_URL}/en/",
            f"{SITE_URL}/archivio/", f"{SITE_URL}/en/archive/"]
    for year in years:
        urls.append(f"{SITE_URL}/archivio/{year}/")
        urls.append(f"{SITE_URL}/en/archive/{year}/")
    body = "\n".join(f"  <url><loc>{u}</loc><lastmod>{day}</lastmod></url>" for u in urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""


def robots():
    return f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
