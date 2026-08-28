#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stringhe dell'interfaccia, italiano e inglese.

Si traduce SOLO l'involucro del sito: intestazioni, etichette, metodologia,
note legali. Titoli ed estratti degli articoli restano nella lingua in cui la
fonte li ha pubblicati — tradurli automaticamente significherebbe mettere in
bocca a una testata parole che non ha scritto, ed e' esattamente cio' che
Molecola promette di non fare.
"""

LANGS = ("it", "en")

MONTHS = {
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
           "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}

WEEKDAYS = {
    "it": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}

T = {
    "it": {
        "html_lang": "it",
        "tagline": "Osservatorio idrogeno",
        "description": ("Rassegna quotidiana sull'idrogeno: stampa di settore, fonti "
                        "istituzionali europee e italiane, preprint di ricerca. "
                        "Aggregazione automatica, nessun testo generato, link diretto "
                        "alla fonte."),
        "nav_wire": "Filo diretto",
        "nav_research": "Ricerca",
        "nav_data": "Numeri",
        "nav_archive": "Archivio",
        "nav_sources": "Fonti",
        "nav_about": "Metodo",
        "nav_code": "Codice",
        "skip": "Vai al contenuto",
        "other_lang_label": "English",
        "other_lang_title": "Read this page in English",
        "updated_prefix": "Ultimo aggiornamento",
        "updated_at": "alle",
        "sources_reached": "fonti raggiunte",
        "articles_in_feed": "articoli in pagina",
        "newest_article": "articolo più recente",
        "lead_kicker": "In apertura",
        "section_latest": "Le ultime",
        "section_more": "Altre notizie",
        "section_research": "Dalla ricerca",
        "section_research_note": ("Preprint e articoli indicizzati nelle ultime "
                                  "settimane. Nessun altro aggregatore di settore "
                                  "li mette accanto ai comunicati."),
        "section_data": "L'idrogeno in numeri",
        "section_sources": "Le fonti",
        "section_method": "Come è fatto",
        "search_placeholder": "Cerca fra titoli, estratti e fonti…",
        "search_label": "Cerca nel filo diretto",
        "search_hint": "Premi / per cercare",
        "filter_all": "Tutte",
        "filter_category": "Ambito",
        "filter_source": "Fonte",
        "filter_lang": "Lingua",
        "cat_industria": "Industria",
        "cat_politica": "Politica",
        "cat_ricerca": "Ricerca",
        "lang_en": "in inglese",
        "lang_it": "in italiano",
        "no_results": "Nessun articolo corrisponde alla ricerca.",
        "reset_filters": "Azzera i filtri",
        "results_count": "articoli mostrati",
        "paywall": "abbonamento",
        "paywall_title": "La fonte richiede abbonamento o registrazione per l'articolo completo",
        "save": "Salva",
        "saved": "Salvato",
        "save_title": "Salva nella tua lista (resta su questo browser)",
        "cite": "Cita",
        "cite_title": "Copia la citazione negli appunti",
        "cited": "Copiato",
        "saved_panel": "La tua lista",
        "saved_empty": "Nessun articolo salvato. Usa «Salva» su un articolo per aggiungerlo.",
        "saved_note": "La lista resta su questo browser: non viene inviata da nessuna parte.",
        "export_csv": "Esporta CSV",
        "export_bib": "Esporta BibTeX",
        "clear_saved": "Svuota",
        "close": "Chiudi",
        "today": "Oggi",
        "yesterday": "Ieri",
        "this_week": "Questa settimana",
        "earlier": "Prima",
        "archive_title": "Archivio",
        "in_archive": "in archivio",
        "archive_intro": ("Tutti gli articoli passati dal filo diretto da quando "
                          "l'osservatorio è attivo, in ordine di data. "
                          "Ogni voce rimanda alla fonte originale."),
        "archive_year": "Archivio {year}",
        "archive_items": "articoli",
        "archive_all_years": "Tutti gli anni",
        "archive_back": "Torna alla home",
        "archive_search": "Cerca nell'archivio {year}…",
        "archive_download": "Scarica l'archivio completo (JSON)",
        "read_source": "Leggi sulla fonte",
        "authors_more": "e altri",
        "back_to_top": "Torna su",
        "theme_toggle": "Cambia tema",
        "rights": ("Titoli ed estratti appartengono alle rispettive testate e "
                   "organizzazioni, riportati qui a fini di rassegna con link "
                   "diretto all'originale."),
        "footer_purpose": "Rassegna automatica per uso di ricerca",
        "feed_link": "Feed RSS di Molecola",
        "method_body": [
            "Ogni tre ore un workflow su GitHub Actions legge le fonti elencate qui "
            "sopra, scarta quelle irraggiungibili, elimina i duplicati e ricostruisce "
            "questa pagina. Titoli, estratti e date sono quelli pubblicati dalla fonte: "
            "nulla viene riscritto, riassunto o tradotto automaticamente.",
            "Le fonti generaliste (ministeri, agenzie, testate di energia) vengono "
            "filtrate per parola chiave, così in pagina finisce solo ciò che riguarda "
            "idrogeno, elettrolisi, celle a combustibile e vettori derivati.",
            "Ogni articolo che passa di qui entra nell'archivio permanente e non ne "
            "esce più, anche quando scompare dal feed della fonte.",
            "La sezione «L'idrogeno in numeri» non è automatica: è aggiornata a mano "
            "dal report annuale IEA Global Hydrogen Review, con link diretto a ogni cifra.",
        ],
        "health_warning": "Attenzione: oggi meno fonti del solito hanno risposto.",
    },
    "en": {
        "html_lang": "en",
        "tagline": "Hydrogen observatory",
        "description": ("A daily read on hydrogen: trade press, European and Italian "
                        "institutional sources, research preprints. Automatically "
                        "aggregated, nothing generated, always linked to the source."),
        "nav_wire": "The wire",
        "nav_research": "Research",
        "nav_data": "Numbers",
        "nav_archive": "Archive",
        "nav_sources": "Sources",
        "nav_about": "Method",
        "nav_code": "Code",
        "skip": "Skip to content",
        "other_lang_label": "Italiano",
        "other_lang_title": "Leggi questa pagina in italiano",
        "updated_prefix": "Last updated",
        "updated_at": "at",
        "sources_reached": "sources reached",
        "articles_in_feed": "articles on this page",
        "newest_article": "newest article",
        "lead_kicker": "Leading",
        "section_latest": "Latest",
        "section_more": "More news",
        "section_research": "From research",
        "section_research_note": ("Preprints and newly indexed papers. No other trade "
                                  "aggregator puts them next to the press releases."),
        "section_data": "Hydrogen in numbers",
        "section_sources": "Sources",
        "section_method": "How it works",
        "search_placeholder": "Search titles, excerpts and sources…",
        "search_label": "Search the wire",
        "search_hint": "Press / to search",
        "filter_all": "All",
        "filter_category": "Beat",
        "filter_source": "Source",
        "filter_lang": "Language",
        "cat_industria": "Industry",
        "cat_politica": "Policy",
        "cat_ricerca": "Research",
        "lang_en": "in English",
        "lang_it": "in Italian",
        "no_results": "No article matches your search.",
        "reset_filters": "Clear filters",
        "results_count": "articles shown",
        "paywall": "subscription",
        "paywall_title": "This source requires a subscription or registration for the full article",
        "save": "Save",
        "saved": "Saved",
        "save_title": "Save to your list (stays in this browser)",
        "cite": "Cite",
        "cite_title": "Copy the citation to the clipboard",
        "cited": "Copied",
        "saved_panel": "Your list",
        "saved_empty": "Nothing saved yet. Use “Save” on an article to add it.",
        "saved_note": "The list stays in this browser: it is never sent anywhere.",
        "export_csv": "Export CSV",
        "export_bib": "Export BibTeX",
        "clear_saved": "Clear",
        "close": "Close",
        "today": "Today",
        "yesterday": "Yesterday",
        "this_week": "This week",
        "earlier": "Earlier",
        "archive_title": "Archive",
        "in_archive": "archived",
        "archive_intro": ("Every article that has passed through the wire since the "
                          "observatory went live, newest first. Each entry links to "
                          "the original source."),
        "archive_year": "{year} archive",
        "archive_items": "articles",
        "archive_all_years": "All years",
        "archive_back": "Back to the front page",
        "archive_search": "Search the {year} archive…",
        "archive_download": "Download the full archive (JSON)",
        "read_source": "Read at the source",
        "authors_more": "and others",
        "back_to_top": "Back to top",
        "theme_toggle": "Switch theme",
        "rights": ("Headlines and excerpts belong to their respective publications and "
                   "organisations, reproduced here as a press review with a direct link "
                   "to the original."),
        "footer_purpose": "Automated press review for research use",
        "feed_link": "Molecola RSS feed",
        "method_body": [
            "Every three hours a GitHub Actions workflow reads the sources listed above, "
            "drops the unreachable ones, removes duplicates and rebuilds this page. "
            "Headlines, excerpts and dates are exactly as the source published them: "
            "nothing is rewritten, summarised or machine-translated.",
            "General-interest sources (ministries, agencies, energy trade press) are "
            "keyword-filtered, so only hydrogen, electrolysis, fuel cells and derived "
            "carriers make it onto the page.",
            "Every article that passes through enters the permanent archive and stays "
            "there, even once it drops out of the source's own feed.",
            "The “Hydrogen in numbers” section is not automated: it is updated by hand "
            "from the annual IEA Global Hydrogen Review, with a direct link per figure.",
        ],
        "health_warning": "Heads up: fewer sources than usual responded today.",
    },
}


def t(lang, key, **kwargs):
    value = T[lang].get(key, T["it"].get(key, key))
    if kwargs and isinstance(value, str):
        return value.format(**kwargs)
    return value


def format_date(dt, lang, with_time=False):
    months = MONTHS[lang]
    if lang == "en":
        base = f"{months[dt.month - 1]} {dt.day}, {dt.year}"
    else:
        base = f"{dt.day} {months[dt.month - 1]} {dt.year}"
    if with_time:
        base += f" · {dt:%H:%M}"
    return base


def format_dateline(dt, lang):
    weekday = WEEKDAYS[lang][dt.weekday()]
    if lang == "en":
        return f"{weekday}, {MONTHS['en'][dt.month - 1]} {dt.day}, {dt.year}"
    return f"{weekday} {dt.day} {MONTHS['it'][dt.month - 1]} {dt.year}"
