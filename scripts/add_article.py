#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggiunge a mano un articolo al filo diretto.

    python3 scripts/add_article.py                 # chiede tutto, partendo dal link
    python3 scripts/add_article.py <url>           # parte dal link
    python3 scripts/add_article.py <url> --no-push # prepara il commit ma non pubblica

Serve per gli articoli che l'automazione non puo' prendere: IEA, MASE,
Hydrogen Council e le altre fonti dietro protezione anti-bot, un PDF, un
comunicato arrivato per email. Lo script apre la pagina, ne ricava titolo,
data, testata e lingua, ti mostra cosa ha trovato e ti lascia correggere
ogni campo premendo Invio per accettare. Poi ricostruisce il sito, fa il
commit e lo pubblica.

Le voci aggiunte cosi' vivono in data/manual.json e vengono rifuse
nell'archivio a ogni build: nessun aggiornamento automatico puo' cancellarle.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetching
import sources as S
import store

MANUAL_PATH = os.path.join("data", "manual.json")

CATEGORIES = [
    ("industria", "progetti, impianti, aziende, mercato"),
    ("politica",  "regole, bandi, aste, decisioni pubbliche"),
    ("ricerca",   "articoli scientifici, preprint, brevetti"),
]


# ----------------------------------------------------------------------
# Lettura della pagina
# ----------------------------------------------------------------------

def _meta(html, *names):
    """Cerca <meta property="..."> o <meta name="..."> fra i nomi dati."""
    for name in names:
        pattern = (r'<meta[^>]+(?:property|name)\s*=\s*["\']%s["\'][^>]*?'
                   r'content\s*=\s*["\'](.*?)["\']' % re.escape(name))
        m = re.search(pattern, html, re.I | re.S)
        if not m:
            pattern = (r'<meta[^>]+content\s*=\s*["\'](.*?)["\'][^>]*?'
                       r'(?:property|name)\s*=\s*["\']%s["\']' % re.escape(name))
            m = re.search(pattern, html, re.I | re.S)
        if m and m.group(1).strip():
            return fetching.strip_html(m.group(1))
    return ""


def read_page(url):
    """Legge la pagina e ne ricava quel che puo'. Non solleva mai."""
    found = {}
    try:
        raw = fetching.fetch(url, accept="text/html,application/xhtml+xml,*/*")
    except Exception as exc:
        print(f"  non sono riuscito ad aprire la pagina ({type(exc).__name__}); "
              f"compilo a mano", file=sys.stderr)
        return found

    html = raw.decode("utf-8", errors="replace")

    title = _meta(html, "og:title", "twitter:title", "dc.title", "citation_title")
    if not title:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        if m:
            title = fetching.strip_html(m.group(1))
            # molte testate appendono " | Nome del sito": si taglia
            title = re.split(r"\s+[|–—]\s+(?=[^|–—]{2,40}$)", title)[0].strip()
    found["title"] = title

    date = _meta(html, "article:published_time", "citation_publication_date",
                 "datePublished", "dc.date", "date", "og:updated_time")
    if not date:
        m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
        if m:
            date = m.group(1)
    if not date:
        m = re.search(r"<time[^>]+datetime=[\"']([^\"']+)", html, re.I)
        if m:
            date = m.group(1)
    parsed = fetching.parse_date(date) if date else None
    found["date"] = parsed

    found["source"] = _meta(html, "og:site_name", "application-name")
    found["excerpt"] = _meta(html, "og:description", "description", "twitter:description")

    m = re.search(r"<html[^>]+lang=[\"']([a-zA-Z-]{2,5})", html)
    found["lang"] = "it" if (m and m.group(1).lower().startswith("it")) else "en"
    return found


# ----------------------------------------------------------------------
# Domande
# ----------------------------------------------------------------------

def ask(question, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{suffix}\n> ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nannullato.", file=sys.stderr)
        sys.exit(1)
    return answer or default


def ask_date(default_dt):
    default = default_dt.strftime("%Y-%m-%d") if default_dt else \
        datetime.now(timezone.utc).strftime("%Y-%m-%d")
    while True:
        raw = ask("Data di pubblicazione (AAAA-MM-GG, oppure «oggi» / «ieri»)", default)
        low = raw.lower()
        if low in ("oggi", "today"):
            return datetime.now(timezone.utc)
        if low in ("ieri", "yesterday"):
            return datetime.now(timezone.utc) - timedelta(days=1)
        normalised = raw
        m = re.fullmatch(r"(\d{1,2})[/.](\d{1,2})[/.](\d{4})", raw)
        if m:
            normalised = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
        parsed = fetching.parse_date(normalised)
        if parsed:
            return parsed
        print("  non ho capito la data, riprova (es. 2026-08-28)")


def ask_category(default="industria"):
    print("\nAmbito:")
    for i, (key, hint) in enumerate(CATEGORIES, 1):
        print(f"  {i}. {key:10s} {hint}")
    while True:
        raw = ask("Numero o nome", default)
        if raw.isdigit() and 1 <= int(raw) <= len(CATEGORIES):
            return CATEGORIES[int(raw) - 1][0]
        if raw.lower() in [c for c, _ in CATEGORIES]:
            return raw.lower()
        print("  scegli 1, 2 o 3")


# ----------------------------------------------------------------------
# Archivio delle voci manuali
# ----------------------------------------------------------------------

def load_manual():
    if not os.path.exists(MANUAL_PATH):
        return []
    with open(MANUAL_PATH, "r", encoding="utf-8") as fh:
        try:
            payload = json.load(fh)
        except json.JSONDecodeError:
            return []
    return payload.get("items", []) if isinstance(payload, dict) else list(payload)


def save_manual(items):
    os.makedirs(os.path.dirname(MANUAL_PATH), exist_ok=True)
    with open(MANUAL_PATH, "w", encoding="utf-8") as fh:
        json.dump({"_comment": "Articoli aggiunti a mano con scripts/add_article.py. "
                               "Rifusi nell'archivio a ogni build.",
                   "count": len(items), "items": items},
                  fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def run(command, **kwargs):
    return subprocess.run(command, check=False, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="Aggiunge un articolo a mano al filo diretto")
    parser.add_argument("url", nargs="?", help="link all'articolo")
    parser.add_argument("--no-push", action="store_true",
                        help="prepara il commit ma non lo pubblica")
    parser.add_argument("--no-build", action="store_true",
                        help="non ricostruire le pagine (lo fara' il prossimo run automatico)")
    args = parser.parse_args()

    if not os.path.exists("scripts/build.py"):
        print("Lancialo dalla cartella del progetto (quella che contiene scripts/).",
              file=sys.stderr)
        return 1

    print("\n  Aggiungi un articolo a Molecola")
    print("  " + "─" * 46)

    url = args.url or ask("\nLink all'articolo")
    if not url.startswith("http"):
        print("Serve un indirizzo che cominci con http.", file=sys.stderr)
        return 1

    item_id = fetching.item_id(url, "")
    if any(x["id"] == item_id for x in load_manual()):
        print("\nQuesto link è già stato aggiunto a mano.", file=sys.stderr)
        return 1
    if any(x["id"] == item_id for x in store.load()):
        print("\nQuesto articolo è già nell'archivio: l'automazione l'aveva già preso.",
              file=sys.stderr)
        return 1

    print("\n  leggo la pagina…")
    found = read_page(url)
    if found.get("title"):
        print(f"  trovato: «{found['title'][:70]}»")

    print("\n  Premi Invio per accettare quello che ti propongo.\n")
    title = ask("Titolo (come l'ha pubblicato la fonte)", found.get("title", ""))
    while not title:
        title = ask("Il titolo serve. Titolo")
    source = ask("Fonte (nome della testata o dell'organizzazione)", found.get("source", ""))
    while not source:
        source = ask("La fonte serve. Fonte")
    date = ask_date(found.get("date"))
    category = ask_category()
    lang = ask("Lingua dell'articolo (it / en)", found.get("lang", "en"))
    excerpt = ask("Estratto — facoltativo, Invio per lasciarlo vuoto",
                  fetching.clean_excerpt(found.get("excerpt", ""), title))

    known = next((s for s in S.SOURCES if s["name"].lower() == source.lower()), None)
    record = dict(
        id=fetching.item_id(url, title),
        title=title,
        link=url,
        source=source,
        source_slug=known["slug"] if known else fetching.re.sub(
            r"[^a-z0-9]+", "-", source.lower()).strip("-") or "manuale",
        category=category,
        lang="it" if lang.lower().startswith("it") else "en",
        paywall=bool(known["paywall"]) if known else False,
        date=date.astimezone(timezone.utc).isoformat(timespec="seconds"),
        excerpt=excerpt,
        authors=[],
        manual=True,
    )

    print("\n  " + "─" * 46)
    print(f"  {record['title']}")
    print(f"  {record['source']} · {record['date'][:10]} · {record['category']}")
    print(f"  {record['link']}")
    print("  " + "─" * 46)
    if ask("\nVa bene? (s/n)", "s").lower() not in ("s", "si", "sì", "y", "yes"):
        print("annullato.")
        return 1

    manual = load_manual()
    manual.append(record)
    manual.sort(key=lambda x: x["date"], reverse=True)
    save_manual(manual)
    print(f"\n  salvato in {MANUAL_PATH} ({len(manual)} voci aggiunte a mano)")

    if not args.no_build:
        print("  ricostruisco le pagine…")
        result = run([sys.executable, "scripts/build.py", "--offline"],
                     capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr[-800:], file=sys.stderr)
            print("Il build è fallito: non ho committato nulla.", file=sys.stderr)
            return 1

    run(["git", "add", "-A"])
    message = f"Aggiunge a mano: {title[:64]}"
    if run(["git", "commit", "-q", "-m", message]).returncode != 0:
        print("Niente da committare.", file=sys.stderr)
        return 1
    print(f"  commit: {message}")

    if args.no_push:
        print("\n  Fatto. Non ho pubblicato (--no-push): quando vuoi, «git push».")
        return 0

    print("  pubblico…")
    if run(["git", "push"]).returncode != 0:
        print("\n  Il commit è pronto ma il push non è riuscito.\n"
              "  Riprova a mano con «git push» (o «git pull --rebase» prima, se il\n"
              "  bot ha pubblicato nel frattempo).", file=sys.stderr)
        return 1

    print("\n  Fatto. L'articolo è online al prossimo deploy di Pages, un minuto circa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
