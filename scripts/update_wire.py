#!/usr/bin/env python3
"""
Aggiorna la sezione "Filo diretto" di index.html con notizie reali
prese da feed RSS pubblici del settore idrogeno.

Non usa librerie esterne: solo la standard library di Python, cosi'
funziona in un runner GitHub Actions senza bisogno di installare nulla.
"""
import html
import re
import sys
import urllib.request
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

# (url del feed, nome breve della fonte, url della homepage della fonte)
FEEDS = [
    ("https://www.hydrogenfuelnews.com/feed/", "Hydrogen Fuel News", "https://www.hydrogenfuelnews.com"),
    ("https://www.powermag.com/category/hydrogen/feed/", "POWER", "https://www.powermag.com/category/hydrogen/"),
    ("https://fchea.org/feed/", "FCHEA", "https://fchea.org"),
    ("https://www.hydrogencouncil.com/en/feed/", "Hydrogen Council", "https://hydrogencouncil.com"),
    ("https://hydrogeneurope.eu/feed/", "Hydrogen Europe", "https://hydrogeneurope.eu"),
    ("https://www.energy-storage.news/tag/hydrogen/feed/", "Energy Storage News", "https://www.energy-storage.news/tag/hydrogen/"),
    ("https://www.pv-magazine.com/tag/hydrogen/feed/", "PV Magazine", "https://www.pv-magazine.com/tag/hydrogen/"),
    ("https://www.offshore-energy.biz/tag/hydrogen/feed/", "Offshore Energy", "https://www.offshore-energy.biz/tag/hydrogen/"),
]

# Iniziali per l'avatar circolare nel feed (scelte a mano per restare distinte tra loro)
SOURCE_INITIALS = {
    "Hydrogen Fuel News": "HN",
    "POWER": "PW",
    "FCHEA": "FC",
    "Hydrogen Council": "HC",
    "Hydrogen Europe": "HE",
    "Energy Storage News": "ES",
    "PV Magazine": "PV",
    "Offshore Energy": "OE",
}

MAX_ITEMS = 27
TIMEOUT = 20
MIN_HEALTHY_FEEDS = 3  # sotto questa soglia il job fallisce apposta (vedi main())

ITALIAN_MONTHS = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; MolecolaBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def parse_feed(xml_bytes, source_name):
    items = []
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError:
        return items

    for item in root.iter("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        date_el = item.find("pubDate")
        desc_el = item.find("description")

        title = strip_html(title_el.text) if title_el is not None else None
        link = link_el.text.strip() if link_el is not None and link_el.text else None
        if not title or not link:
            continue

        pub_dt = None
        if date_el is not None and date_el.text:
            try:
                pub_dt = parsedate_to_datetime(date_el.text.strip())
            except (TypeError, ValueError):
                pub_dt = None

        excerpt = strip_html(desc_el.text) if desc_el is not None else ""
        if len(excerpt) > 170:
            excerpt = excerpt[:167].rsplit(" ", 1)[0] + "..."

        items.append({
            "title": title,
            "link": link,
            "date": pub_dt,
            "excerpt": excerpt,
            "source": source_name,
        })
    return items


def collect_items():
    all_items = []
    attempted = len(FEEDS)
    succeeded = 0
    for url, name, _home in FEEDS:
        try:
            raw = fetch(url)
            feed_items = parse_feed(raw, name)
            all_items.extend(feed_items)
            succeeded += 1
            print(f"OK  {name}: {len(feed_items)} articoli", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - graceful degradation by design
            print(f"SKIP {name}: {exc}", file=sys.stderr)
            continue

    dated = [i for i in all_items if i["date"] is not None]
    dated.sort(key=lambda i: i["date"], reverse=True)

    seen_titles = set()
    deduped = []
    for item in dated:
        key = item["title"].lower()[:60]
        if key in seen_titles:
            continue
        seen_titles.add(key)
        deduped.append(item)

    return deduped[:MAX_ITEMS], attempted, succeeded


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "fonte"


def build_wire_html(items):
    blocks = []
    for item in items:
        day_month = item["date"].strftime("%d.%m") if item["date"] else "--.--"
        iso_date = item["date"].strftime("%Y-%m-%d") if item["date"] else ""
        title = html.escape(item["title"])
        excerpt = html.escape(item["excerpt"]) if item["excerpt"] else ""
        source = html.escape(item["source"])
        source_slug = slugify(item["source"])
        initials = html.escape(SOURCE_INITIALS.get(item["source"], item["source"][:2].upper()))
        link = html.escape(item["link"], quote=True)
        excerpt_html = f'<p class="excerpt">{excerpt}</p>' if excerpt else ""
        blocks.append(f"""          <div class="wire-item" data-source="{source_slug}" data-date="{iso_date}" data-title="{title.lower()}">
            <span class="avatar src-{source_slug}">{initials}</span>
            <div class="wire-body">
              <h4><a href="{link}" target="_blank" rel="noopener">{title}</a></h4>
              {excerpt_html}
              <div class="wire-meta">
                <span class="wire-source">{source}</span>
                <span class="dot">·</span>
                <span class="wire-date mono num">{day_month}</span>
              </div>
            </div>
          </div>""")
    return "\n".join(blocks)


def build_updated_text(items, attempted, succeeded):
    if not items or items[0]["date"] is None:
        return None
    d = items[0]["date"]
    return (
        f"Aggiornato automaticamente · {d.day} {ITALIAN_MONTHS[d.month - 1]} · "
        f"{succeeded}/{attempted} fonti raggiunte · {len(items)} notizie"
    )


def replace_between(text, start_marker, end_marker, replacement):
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if not pattern.search(text):
        raise RuntimeError(f"Markers not found: {start_marker} .. {end_marker}")
    return pattern.sub(
        lambda _m: f"{start_marker}\n{replacement}\n{end_marker}",
        text,
        count=1,
    )


def main():
    items, attempted, succeeded = collect_items()

    # Guardia di salute: se troppi feed sono irraggiungibili, il job fallisce
    # di proposito. Un run GitHub Actions programmato che fallisce manda
    # automaticamente un'email al proprietario del repository: e' il modo
    # piu' semplice e robusto per essere avvisati se una fonte si e' rotta,
    # senza dover tenere in vita un processo di controllo separato.
    if succeeded < MIN_HEALTHY_FEEDS:
        print(
            f"ERRORE: solo {succeeded}/{attempted} feed raggiungibili "
            f"(soglia minima {MIN_HEALTHY_FEEDS}). Controllare le fonti in FEEDS.",
            file=sys.stderr,
        )
        return 1

    if not items:
        print("Nessun articolo trovato nei feed raggiunti: nessuna modifica.", file=sys.stderr)
        return 0

    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    wire_html = build_wire_html(items)
    content = replace_between(
        content, "<!-- WIRE_ITEMS_START -->", "<!-- WIRE_ITEMS_END -->", wire_html
    )

    updated_text = build_updated_text(items, attempted, succeeded)
    if updated_text:
        eyebrow = f'<span class="eyebrow" id="wire-updated">{html.escape(updated_text)}</span>'
        content = replace_between(
            content, "<!-- WIRE_UPDATED_START -->", "<!-- WIRE_UPDATED_END -->", eyebrow
        )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Aggiornati {len(items)} articoli nel Filo diretto ({succeeded}/{attempted} fonti).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
