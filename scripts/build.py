#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build del sito.

    python3 scripts/build.py              # legge le fonti, aggiorna archivio e pagine
    python3 scripts/build.py --offline    # rigenera le pagine dal solo archivio su disco
    python3 scripts/build.py --dry-run    # legge le fonti ma non scrive nulla

La prima pagina si costruisce SEMPRE dall'archivio, mai direttamente da cio'
che le fonti hanno risposto in questo istante: se meta' dei feed cade per
un'ora, il sito resta pieno e coerente invece di svuotarsi.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetching
import i18n
import render
import sources as S
import store

FRONT_NEWS = 45          # notizie in prima pagina
FRONT_RESEARCH = 10      # preprint mescolati alle notizie
MIN_PRODUCTIVE = 5       # sotto questa soglia il job fallisce: vedi health_check()
STALE_HOURS = 96         # nessun articolo nuovo da cosi' tanto = qualcosa e' rotto


def health_check(report, archive):
    """
    Restituisce (ok, messaggi).

    La metrica non e' «quante fonti hanno risposto» ma «quante hanno prodotto
    almeno un articolo»: un feed che restituisce una pagina di errore risponde
    benissimo e non serve a niente. Era il difetto della guardia precedente.
    """
    productive = [r for r in report if r["ok"] and r["count"] > 0]
    problems = []
    if len(productive) < MIN_PRODUCTIVE:
        broken = [r["name"] for r in report if not r["ok"] or not r["count"]]
        problems.append(
            f"solo {len(productive)}/{len(report)} fonti hanno prodotto articoli "
            f"(soglia {MIN_PRODUCTIVE}). Senza articoli: {', '.join(broken[:12])}")

    newest = max((i.get("date") or "" for i in archive), default="")
    newest_dt = render.parse_dt(newest)
    if newest_dt:
        age = datetime.now(timezone.utc) - newest_dt
        if age > timedelta(hours=STALE_HOURS):
            problems.append(
                f"nessun articolo piu' recente di {age.days} giorni: "
                f"probabile rottura silenziosa delle fonti")
    return (not problems), problems


def select_front(archive):
    """Le voci di prima pagina: notizie e ricerca, ciascuna con il proprio tetto."""
    news, research = [], []
    for item in archive:                      # gia' ordinato dal piu' recente
        target = research if item["category"] == "ricerca" else news
        if len(target) < (FRONT_RESEARCH if item["category"] == "ricerca" else FRONT_NEWS):
            target.append(item)
        if len(news) >= FRONT_NEWS and len(research) >= FRONT_RESEARCH:
            break
    merged = sorted(news + research, key=lambda i: i.get("date") or "", reverse=True)
    return merged, research


def write(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def write_assets():
    """Favicon e immagine di anteprima social: generate qui per non tenere binari nel repo."""
    favicon = ("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 34 24">
<rect width="34" height="24" fill="#FBFAF6"/>
<circle cx="8.6" cy="12" r="6.4" fill="none" stroke="#0D5C63" stroke-width="2.4"/>
<circle cx="25.4" cy="12" r="6.4" fill="none" stroke="#0D5C63" stroke-width="2.4"/>
<path d="M15.8 12h2.4" stroke="#0D5C63" stroke-width="3" stroke-linecap="round"/>
</svg>
""")
    social = ("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
<rect width="1200" height="630" fill="#FBFAF6"/>
<g stroke="#14130E" stroke-width="3"><path d="M80 128h1040"/></g>
<g stroke="#14130E" stroke-width="1"><path d="M80 138h1040"/></g>
<circle cx="462" cy="300" r="56" fill="none" stroke="#0D5C63" stroke-width="9"/>
<circle cx="598" cy="300" r="56" fill="none" stroke="#0D5C63" stroke-width="9"/>
<path d="M522 300h16" stroke="#0D5C63" stroke-width="11" stroke-linecap="round"/>
<text x="600" y="452" text-anchor="middle" font-family="Georgia,serif" font-size="96"
      letter-spacing="14" fill="#14130E">MOLECOLA</text>
<text x="600" y="506" text-anchor="middle" font-family="Helvetica,Arial,sans-serif"
      font-size="25" letter-spacing="9" fill="#7B7870">OSSERVATORIO IDROGENO</text>
<text x="600" y="86" text-anchor="middle" font-family="Helvetica,Arial,sans-serif"
      font-size="23" letter-spacing="5" fill="#7B7870">STAMPA DI SETTORE · FONTI ISTITUZIONALI · RICERCA</text>
</svg>
""")
    write(os.path.join("assets", "favicon.svg"), favicon)
    write(os.path.join("assets", "social.svg"), social)


def main():
    parser = argparse.ArgumentParser(description="Costruisce il sito Molecola")
    parser.add_argument("--offline", action="store_true",
                        help="non contatta le fonti: rigenera dal solo archivio")
    parser.add_argument("--dry-run", action="store_true",
                        help="legge le fonti ma non scrive su disco")
    args = parser.parse_args()

    built_at = datetime.now(timezone.utc)
    archive = store.load()

    if args.offline:
        report = [dict(slug=s["slug"], name=s["name"], ok=True, error=None,
                       count=sum(1 for i in archive if i["source_slug"] == s["slug"]),
                       newest=None) for s in S.SOURCES]
        added = 0
        print("modalita' offline: nessuna fonte contattata", file=sys.stderr)
    else:
        fresh, report = fetching.collect_all()
        archive, added = store.merge(archive, fresh)
        print(f"\n{added} articoli nuovi, {len(archive)} in archivio", file=sys.stderr)

        ok, problems = health_check(report, archive)
        if not ok:
            for problem in problems:
                print(f"ERRORE: {problem}", file=sys.stderr)
            print("Il job fallisce di proposito: GitHub invia un'email al proprietario "
                  "del repository. Lanciare il workflow «Verifica fonti» per la diagnosi.",
                  file=sys.stderr)
            return 1

    if args.dry_run:
        print("dry-run: nessun file scritto", file=sys.stderr)
        return 0

    if not args.offline:
        store.save(archive)

    with open(os.path.join("data", "indicators.json"), "r", encoding="utf-8") as fh:
        indicators = json.load(fh)

    front, research = select_front(archive)
    years = store.years(archive)
    per_year = [(year, sum(1 for i in archive if (i.get("date") or "").startswith(year)))
                for year in years]

    written = []
    for lang in i18n.LANGS:
        page = render.front_page(lang, items=front, research=research, report=report,
                                 built_at=built_at, indicators=indicators,
                                 archive_total=len(archive))
        written.append(write("index.html" if lang == "it" else os.path.join("en", "index.html"), page))

        written.append(write(render.archive_paths(lang),
                             render.archive_index(lang, per_year=per_year, built_at=built_at,
                                                  report=report, total=len(archive))))
        for year in years:
            items = [i for i in archive if (i.get("date") or "").startswith(year)]
            written.append(write(render.archive_paths(lang, year),
                                 render.archive_year(lang, year, items, per_year=per_year,
                                                     built_at=built_at, report=report)))

    written.append(write("feed.xml", render.rss_feed(front, built_at)))
    written.append(write("sitemap.xml", render.sitemap(years, built_at)))
    written.append(write("robots.txt", render.robots()))
    write_assets()

    print(f"generate {len(written)} pagine · {len(front)} articoli in prima pagina "
          f"({len(research)} dalla ricerca) · anni in archivio: {', '.join(years) or '—'}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
