#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrazione una tantum: recupera nell'archivio gli articoli gia' pubblicati
dalle vecchie versioni di index.html.

Prima di questa riscrittura il sito non conservava nulla: ogni aggiornamento
sovrascriveva i 27 articoli precedenti, che restavano solo nella history di
git. Questo script rilegge tutte le versioni di index.html mai committate e
ne estrae gli articoli, così l'archivio parte con la copertura storica reale
invece che da zero.

    python3 scripts/migrate_from_html.py        # aggiunge a data/archive.json

Va lanciato una volta sola; rilanciarlo non fa danni (gli id sono stabili e
il merge non duplica), ma dopo la migrazione non serve piu'.
"""
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetching
import sources as S
import store

ITEM_RE = re.compile(
    r'<div class="wire-item"[^>]*?data-source="(?P<slug>[^"]*)"[^>]*?'
    r'data-date="(?P<date>[^"]*)"(?P<rest>.*?)</div>\s*</div>',
    re.S)
LINK_RE = re.compile(r'<h4>\s*<a href="(?P<link>[^"]+)"[^>]*>(?P<title>.*?)</a>', re.S)
EXCERPT_RE = re.compile(r'<p class="excerpt">(?P<excerpt>.*?)</p>', re.S)
SOURCE_RE = re.compile(r'<span class="wire-source">(?P<name>.*?)</span>', re.S)

# Le 8 fonti della versione precedente, mappate sui nuovi slug.
LEGACY = {
    "hydrogen-fuel-news": "hydrogen-fuel-news", "power": "power", "fchea": "fchea",
    "hydrogen-council": "hydrogen-council", "hydrogen-europe": "hydrogen-europe",
    "energy-storage-news": "energy-storage-news", "pv-magazine": "pv-magazine",
    "offshore-energy": "offshore-energy",
}


def versions_of(path):
    revs = subprocess.run(["git", "log", "--all", "--format=%H", "--", path],
                          capture_output=True, text=True, check=True).stdout.split()
    for rev in revs:
        blob = subprocess.run(["git", "show", f"{rev}:{path}"],
                              capture_output=True, text=True)
        if blob.returncode == 0:
            yield rev, blob.stdout


def extract(document):
    out = []
    for match in ITEM_RE.finditer(document):
        rest = match.group("rest")
        link_match = LINK_RE.search(rest)
        if not link_match:
            continue
        title = fetching.strip_html(link_match.group("title"))
        link = fetching.strip_html(link_match.group("link"))
        if not title or not link.startswith("http"):
            continue
        name_match = SOURCE_RE.search(rest)
        excerpt_match = EXCERPT_RE.search(rest)
        slug = LEGACY.get(match.group("slug"), match.group("slug"))
        source = S.BY_SLUG.get(slug)
        name = (name_match.group("name").strip() if name_match
                else (source["name"] if source else slug))
        date = match.group("date")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date or ""):
            continue
        out.append(dict(
            id=fetching.item_id(link, title),
            title=title,
            link=link,
            source=name,
            source_slug=slug,
            category=source["category"] if source else "industria",
            lang=source["lang"] if source else "en",
            paywall=bool(source["paywall"]) if source else False,
            date=f"{date}T12:00:00+00:00",
            excerpt=fetching.clean_excerpt(
                excerpt_match.group("excerpt") if excerpt_match else "", title),
            authors=[],
        ))
    return out


def main():
    recovered, seen_versions = {}, 0
    for _rev, document in versions_of("index.html"):
        seen_versions += 1
        for item in extract(document):
            recovered.setdefault(item["id"], item)
    print(f"{seen_versions} versioni di index.html esaminate, "
          f"{len(recovered)} articoli distinti recuperati", file=sys.stderr)

    archive = store.load()
    merged, added = store.merge(archive, list(recovered.values()),
                                now=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    store.save(merged)
    print(f"{added} aggiunti all'archivio, ora {len(merged)} in totale", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
