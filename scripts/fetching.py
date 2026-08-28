#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lettura e normalizzazione delle fonti.

Un solo formato di uscita, qualunque sia il formato d'ingresso (RSS 2.0,
RSS 1.0/RDF, Atom, API arXiv, API OpenAlex):

    {id, title, link, source, source_slug, category, lang, paywall,
     date (ISO 8601 UTC), excerpt, authors}

Solo standard library: gira su un runner GitHub Actions senza installare nulla.
"""
import hashlib
import html
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import sources as S

TIMEOUT = 25
# Diversi siti di settore (IEA, IRENA, MASE, Hydrogen Council…) rispondono 403
# a qualunque user-agent che si dichiari automatico, anche solo per leggere un
# feed RSS pubblico. Ci si presenta come un browser normale: la richiesta e' la
# stessa che farebbe una persona che apre il feed, una ogni tre ore.
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

# Rumore ricorrente negli estratti RSS: footer WordPress, inviti alla lettura,
# firme in testa. Vengono tolti prima di decidere se l'estratto vale qualcosa.
_NOISE_PATTERNS = [
    re.compile(r"the post .*? appeared first on .*?$", re.I | re.S),
    re.compile(r"l'articolo .*? (proviene|sembra essere il primo) da .*?$", re.I | re.S),
    re.compile(r"^\s*\[?\s*(…|\.\.\.)\s*\]?\s*", re.S),
    re.compile(r"(continue reading|read more|leggi (tutto|l'articolo)|"
               r"the post appeared first)\s*[.…»>]*\s*$", re.I),
    re.compile(r"^\s*by\s+[A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,3}\s+"
               r"(?:January|February|March|April|May|June|July|August|"
               r"September|October|November|December)\s+\d{1,2},\s*\d{4}\s*", re.S),
    re.compile(r"^\s*(di|by)\s+[A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,2}\s*[—–-]\s*", re.S),
    re.compile(r"share (this|on) (post|twitter|linkedin|facebook).*$", re.I | re.S),
]

_ssl_ctx = ssl.create_default_context()


def _localname(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _find(el, *names):
    """Primo figlio (a qualsiasi profondita') il cui nome locale e' fra quelli dati."""
    for node in el.iter():
        if _localname(node.tag) in names and node is not el:
            return node
    return None


def _text_of(el):
    if el is None:
        return ""
    parts = [el.text or ""]
    for child in el:
        parts.append(_text_of(child))
        parts.append(child.tail or "")
    return "".join(parts)


def strip_html(text):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text or "", flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def clean_excerpt(raw, title, limit=220):
    """
    Ripulisce un estratto RSS e restituisce "" se non aggiunge nulla al titolo.
    Meglio nessun estratto che un estratto che ripete il titolo: era il difetto
    piu' visibile della versione precedente del sito.
    """
    text = strip_html(raw)
    for pattern in _NOISE_PATTERNS:
        text = pattern.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip(" —–-•|·")

    if len(text) < 32:
        return ""

    # Se l'estratto e' sostanzialmente il titolo ripetuto, non serve.
    def norm(s):
        return re.sub(r"[^a-z0-9]+", "", (s or "").lower())
    n_title, n_text = norm(title), norm(text)
    if n_title and (n_text.startswith(n_title[:60]) or n_title[:60] in n_text[:120]):
        remainder = n_text.replace(n_title, "", 1)
        if len(remainder) < 60:
            return ""

    if len(text) > limit:
        text = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:.—–-") + "…"
    return text


def fetch(url, accept=None):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept or ("application/rss+xml, application/atom+xml, "
                             "application/xml;q=0.9, text/xml;q=0.9, */*;q=0.8"),
        "Accept-Language": "en-GB,en;q=0.9,it;q=0.8",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_ctx) as resp:
        return resp.read()


def parse_date(value):
    """Accetta RFC 822 (RSS), ISO 8601 (Atom/API) e date secche AAAA-MM-GG."""
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
        if dt:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    iso = value.replace("Z", "+00:00")
    for candidate in (iso, iso[:19], iso[:10]):
        try:
            dt = datetime.fromisoformat(candidate)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def item_id(link, title):
    """Identita' stabile di un articolo: e' la chiave dell'archivio storico."""
    basis = (link or "").strip().lower() or (title or "").strip().lower()
    basis = re.sub(r"[?&](utm_[^=]+|fbclid|gclid)=[^&]*", "", basis).rstrip("/?&")
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


# ----------------------------------------------------------------------
# Adattatori per formato
# ----------------------------------------------------------------------

def _parse_xml_feed(raw):
    """RSS 2.0, RSS 1.0/RDF e Atom, ignorando i namespace."""
    root = ElementTree.fromstring(raw)
    entries = [n for n in root.iter() if _localname(n.tag) in ("item", "entry")]
    out = []
    for node in entries:
        title = strip_html(_text_of(_find(node, "title")))
        link = ""
        link_el = _find(node, "link")
        if link_el is not None:
            link = (link_el.get("href") or link_el.text or "").strip()
        if not link:
            guid = _find(node, "guid", "id")
            if guid is not None and (guid.text or "").startswith("http"):
                link = guid.text.strip()
        if not title or not link:
            continue

        date_el = _find(node, "pubDate", "published", "updated", "date")
        date = parse_date(_text_of(date_el)) if date_el is not None else None

        desc_el = _find(node, "description", "summary", "encoded", "content")
        raw_excerpt = _text_of(desc_el) if desc_el is not None else ""

        out.append(dict(title=title, link=link, date=date,
                        raw_excerpt=raw_excerpt, authors=[]))
    return out


def _parse_arxiv(raw):
    items = _parse_xml_feed(raw)
    root = ElementTree.fromstring(raw)
    entries = [n for n in root.iter() if _localname(n.tag) == "entry"]
    for item, node in zip(items, entries):
        names = [strip_html(_text_of(a)) for a in node.iter()
                 if _localname(a.tag) == "name"]
        item["authors"] = names[:6]
        # arXiv mette <link rel="alternate"> per la pagina abstract:
        for link_el in node.iter():
            if _localname(link_el.tag) == "link" and link_el.get("rel") == "alternate":
                item["link"] = link_el.get("href") or item["link"]
                break
    return items


def _parse_openalex(raw):
    payload = json.loads(raw.decode("utf-8"))
    out = []
    for work in payload.get("results", []):
        title = strip_html(work.get("title") or work.get("display_name") or "")
        link = work.get("doi") or work.get("id") or ""
        if not title or not link:
            continue
        authors = [a.get("author", {}).get("display_name", "")
                   for a in (work.get("authorships") or [])][:6]
        venue = ((work.get("primary_location") or {}).get("source") or {}).get("display_name")
        out.append(dict(title=title, link=link,
                        date=parse_date(work.get("publication_date")),
                        raw_excerpt=venue or "",
                        authors=[a for a in authors if a]))
    return out


PARSERS = {"rss": _parse_xml_feed, "arxiv": _parse_arxiv, "openalex": _parse_openalex}


# ----------------------------------------------------------------------
# Raccolta
# ----------------------------------------------------------------------

def collect_source(source, since_days=400):
    """
    Legge una fonte. Restituisce (items, error).
    Non solleva mai: una fonte rotta non deve far cadere l'intero build.
    """
    url = source["url"]
    if "{since}" in url:
        since = (datetime.now(timezone.utc) - timedelta(days=45)).strftime("%Y-%m-%d")
        url = url.replace("{since}", since)

    accept = "application/json" if source["kind"] == "openalex" else None
    try:
        raw = fetch(url, accept=accept)
    except Exception as exc:
        return [], f"{type(exc).__name__}: {str(exc)[:120]}"

    try:
        parsed = PARSERS[source["kind"]](raw)
    except Exception as exc:
        return [], f"parse {type(exc).__name__}: {str(exc)[:120]}"

    horizon = datetime.now(timezone.utc) - timedelta(days=since_days)
    future_limit = datetime.now(timezone.utc) + timedelta(days=2)
    items = []
    for entry in parsed:
        date = entry["date"]
        if date is None or date < horizon or date > future_limit:
            continue
        title = entry["title"]
        # Per OpenAlex il campo non e' un estratto ma il nome della rivista:
        # e' gia' pulito e va mostrato tale e quale.
        excerpt = (entry["raw_excerpt"].strip() if source["kind"] == "openalex"
                   else clean_excerpt(entry["raw_excerpt"], title))
        if not source["topical"] and not S.matches_keywords(title + " " + excerpt):
            continue
        items.append(dict(
            id=item_id(entry["link"], title),
            title=title,
            link=entry["link"],
            source=source["name"],
            source_slug=source["slug"],
            category=source["category"],
            lang=source["lang"],
            paywall=bool(source["paywall"]),
            date=date.astimezone(timezone.utc).isoformat(timespec="seconds"),
            excerpt=excerpt,
            authors=entry.get("authors") or [],
        ))
    if not items and not parsed:
        return [], "nessun elemento riconosciuto nel documento"
    return items, None


def collect_all(verbose=True):
    """
    Legge tutte le fonti. Restituisce (items, report) dove report e' una lista
    di dizionari con l'esito per fonte — usata sia dalla guardia di salute sia
    dal workflow di diagnostica.
    """
    all_items, report = [], []
    for source in S.SOURCES:
        items, error = collect_source(source)
        report.append(dict(slug=source["slug"], name=source["name"],
                           ok=error is None, error=error, count=len(items),
                           newest=max((i["date"] for i in items), default=None)))
        all_items.extend(items)
        if verbose:
            mark = "OK  " if error is None else "FAIL"
            detail = error or f"{len(items)} articoli"
            print(f"{mark} {source['name']:34s} {detail}", file=sys.stderr)
    return all_items, report
