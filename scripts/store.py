#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archivio storico degli articoli: data/archive.json.

Un file JSON in append, versionato con git. Scelta deliberata rispetto a un
database esterno: l'archivio e' una lista di link in sola aggiunta, non ha
scritture concorrenti, e tenerlo nel repository significa zero credenziali da
gestire in Actions, zero dipendenze di rete in piu' da cui il build possa
dipendere, e ogni variazione tracciata nella history di git. Un anno pieno di
copertura sta in pochi MB.

Formato:
    {"version": 2,
     "updated": "2026-08-28T10:14:00+00:00",
     "items": [ {...}, ... ]}   # ordinati dal piu' recente
"""
import json
import os
from datetime import datetime, timezone

ARCHIVE_PATH = os.path.join("data", "archive.json")
FIELDS = ("id", "title", "link", "source", "source_slug", "category",
          "lang", "paywall", "date", "excerpt", "authors", "first_seen")


def load(path=ARCHIVE_PATH):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        try:
            payload = json.load(fh)
        except json.JSONDecodeError:
            return []
    return payload.get("items", []) if isinstance(payload, dict) else list(payload)


def merge(existing, fresh, now=None):
    """
    Fonde gli articoli appena letti nell'archivio.

    - un id gia' presente non viene duplicato, ma i suoi campi vengono
      aggiornati (una fonte puo' correggere un titolo o aggiungere un estratto);
    - first_seen resta la prima volta che l'articolo e' comparso qui: e' il dato
      che rende l'archivio una cronologia e non solo un elenco.
    """
    now = now or datetime.now(timezone.utc).isoformat(timespec="seconds")
    by_id = {item["id"]: dict(item) for item in existing}
    added = 0
    for item in fresh:
        current = by_id.get(item["id"])
        if current is None:
            record = {k: item.get(k) for k in FIELDS if k != "first_seen"}
            record["first_seen"] = now
            by_id[item["id"]] = record
            added += 1
        else:
            for key in ("title", "excerpt", "authors", "source", "source_slug",
                        "category", "lang", "paywall", "date"):
                if item.get(key):
                    current[key] = item[key]
    merged = sorted(by_id.values(), key=lambda i: (i.get("date") or ""), reverse=True)
    return merged, added


def save(items, path=ARCHIVE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "version": 2,
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(items),
        "items": items,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")


HEALTH_PATH = os.path.join("data", "source-health.json")


def save_health(report, path=HEALTH_PATH):
    """
    Scrive lo stato di ogni fonte accanto all'archivio.

    Serve a leggere il referto senza aprire i log di Actions: il file finisce
    nel repository a ogni run, quindi la diagnosi di una fonte caduta e'
    sempre a un colpo d'occhio e resta nella history.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sources = sorted(report, key=lambda r: (bool(r.get("count")), r["slug"]))

    # Se la sostanza non cambia non si riscrive il file: altrimenti il solo
    # orario del controllo produrrebbe un commit a ogni run, otto al giorno,
    # per sempre.
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                previous = json.load(fh)
            if previous.get("sources") == json.loads(json.dumps(sources)):
                return False
        except (json.JSONDecodeError, OSError):
            pass

    payload = {
        "checked": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "productive": sum(1 for r in report if r.get("ok") and r.get("count")),
        "total": len(report),
        "sources": sources,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return True


def years(items):
    return sorted({(i.get("date") or "")[:4] for i in items if i.get("date")},
                  reverse=True)
