#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostica delle fonti: dice quali endpoint rispondono davvero e con che resa.

Va lanciato dove c'e' accesso pieno alla rete — in pratica dal workflow
«Verifica fonti» su GitHub Actions (Actions -> Verifica fonti -> Run workflow).
E' il modo corretto per validare una fonte prima di darla per buona, e per
capire quale si e' rotta quando il build fallisce.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetching
import sources as S


def main():
    rows, healthy = [], 0
    for source in S.SOURCES:
        items, error = fetching.collect_source(source)
        newest = max((i["date"] for i in items), default="")
        if error:
            state = "IRRAGGIUNGIBILE"
        elif not items:
            state = "VUOTA"
        else:
            state = "OK"
            healthy += 1
        rows.append((state, source["name"], source["kind"], len(items),
                     newest[:10], error or "", source["url"]))

    width = max(len(r[1]) for r in rows)
    print(f"{'STATO':<16} {'FONTE':<{width}}  {'TIPO':<9} {'N':>3}  {'PIÙ RECENTE':<12} NOTE")
    print("-" * (16 + width + 46))
    for state, name, kind, count, newest, error, url in rows:
        note = error if error else url
        print(f"{state:<16} {name:<{width}}  {kind:<9} {count:>3}  {newest:<12} {note[:70]}")

    import store
    store.save_health([dict(slug=s["slug"], name=s["name"],
                            ok=(state != "IRRAGGIUNGIBILE"), error=error or None,
                            count=count, newest=newest or None)
                       for (state, name, kind, count, newest, error, url), s
                       in zip(rows, S.SOURCES)])
    print(f"\n{healthy}/{len(rows)} fonti producono articoli.")
    print("Referto salvato in data/source-health.json")
    empty = [r[1] for r in rows if r[0] != "OK"]
    if empty:
        print("Da sistemare o rimuovere da scripts/sources.py: " + ", ".join(empty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
