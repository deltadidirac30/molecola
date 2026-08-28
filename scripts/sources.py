#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Definizione delle fonti monitorate da Molecola.

Ogni fonte e' un dizionario con questi campi:

  slug       identificatore stabile, usato in CSS/filtri/archivio. NON cambiarlo
             una volta pubblicato: e' la chiave con cui l'archivio storico
             ricollega un articolo alla sua fonte.
  name       nome mostrato
  kind       "rss"  -> RSS 2.0 / RSS 1.0 (RDF) / Atom, riconosciuti da soli
             "arxiv"    -> API arXiv (Atom con namespace proprio)
             "openalex" -> API OpenAlex (JSON)
  url        endpoint del feed
  home       homepage della fonte (per la sezione "Fonti")
  category   "industria" | "politica" | "ricerca"
  lang       "en" | "it"  (lingua degli articoli, non della UI)
  paywall    True se l'articolo completo richiede abbonamento o registrazione
  topical    True  = la fonte pubblica SOLO idrogeno: si prende tutto
             False = fonte generalista: si tengono solo gli articoli che
                     contengono una parola chiave (vedi KEYWORDS)
  initials   2 lettere per la sigla nel filo diretto
  weight     priorita' a parita' di data (piu' alto = preferito nel dedup)
  poll       False = la fonte NON viene interrogata, resta solo come link nella
             sezione «Fonti» del sito. Si usa per chi non espone un feed
             leggibile da uno script: quasi sempre una protezione anti-bot
             (Cloudflare risponde 403 agli indirizzi dei datacenter, qualunque
             sia lo user-agent) o l'assenza di un RSS pubblico. Il motivo va
             scritto in `note`, così non si riprova all'infinito la stessa
             strada gia' verificata come chiusa.
  note       perche' la fonte non e' interrogabile (solo quando poll=False)

Aggiungere una fonte = aggiungere una riga qui. Nient'altro da toccare:
il build genera da solo filtri, legenda, sezione "Fonti" e colori.

Prima di aggiungere una fonte in produzione, lanciare il workflow
"Verifica fonti" (Actions -> Verifica fonti -> Run workflow): gira sui runner
GitHub, che hanno accesso pieno alla rete, e dice quali endpoint rispondono
davvero e con quanti articoli.
"""

# Parole chiave usate per filtrare le fonti generaliste (topical=False).
# Confrontate in minuscolo su titolo + estratto.
KEYWORDS = [
    "hydrogen", "idrogeno", "h2 ", " h2", "h₂",
    "electroly",          # electrolysis, electrolyser, electrolyzer
    "elettroli",          # elettrolisi, elettrolizzatore
    "fuel cell", "cella a combustibile", "celle a combustibile",
    "rfnbo", "ammonia", "ammoniaca", "e-fuel", "efuel",
    "power-to-x", "power to x", "green steel", "acciaio verde",
]

SOURCES = [
    # ------------------------------------------------------------------
    # Stampa di settore — specializzata idrogeno / energia
    # ------------------------------------------------------------------
    dict(slug="hydrogen-fuel-news", name="Hydrogen Fuel News", kind="rss",
         url="https://www.hydrogenfuelnews.com/feed/",
         home="https://www.hydrogenfuelnews.com",
         category="industria", lang="en", paywall=False, topical=True,
         initials="HN", weight=5),

    dict(slug="fuel-cells-works", name="Fuel Cells Works", kind="rss",
         url="https://fuelcellsworks.com/feed/",
         home="https://fuelcellsworks.com",
         category="industria", lang="en", paywall=False, topical=True,
         initials="FW", weight=6),

    dict(slug="h2-view", name="H2 View", kind="rss",
         url="https://www.h2-view.com/feed/",
         home="https://www.h2-view.com",
         category="industria", lang="en", paywall=True, topical=True,
         initials="H2", weight=7,
         poll=False, note="Cloudflare respinge le richieste automatiche (403)"),

    dict(slug="hydrogen-insight", name="Hydrogen Insight", kind="rss",
         url="https://www.hydrogeninsight.com/?service=rss",
         home="https://www.hydrogeninsight.com",
         category="industria", lang="en", paywall=True, topical=True,
         initials="HI", weight=8,
         poll=False, note="nessun feed pubblico raggiungibile; il sito serve HTML anche su /rss"),

    dict(slug="power", name="POWER", kind="rss",
         url="https://www.powermag.com/category/hydrogen/feed/",
         home="https://www.powermag.com/category/hydrogen/",
         category="industria", lang="en", paywall=False, topical=True,
         initials="PW", weight=4),

    dict(slug="pv-magazine", name="PV Magazine", kind="rss",
         url="https://www.pv-magazine.com/tag/hydrogen/feed/",
         home="https://www.pv-magazine.com/tag/hydrogen/",
         category="industria", lang="en", paywall=False, topical=True,
         initials="PV", weight=4),

    dict(slug="energy-storage-news", name="Energy Storage News", kind="rss",
         url="https://www.energy-storage.news/tag/hydrogen/feed/",
         home="https://www.energy-storage.news/tag/hydrogen/",
         category="industria", lang="en", paywall=False, topical=True,
         initials="ES", weight=3),

    dict(slug="offshore-energy", name="Offshore Energy", kind="rss",
         url="https://www.offshore-energy.biz/tag/hydrogen/feed/",
         home="https://www.offshore-energy.biz/tag/hydrogen/",
         category="industria", lang="en", paywall=False, topical=True,
         initials="OE", weight=4),

    dict(slug="green-car-congress", name="Green Car Congress", kind="rss",
         url="https://www.greencarcongress.com/index.rdf",
         home="https://www.greencarcongress.com",
         category="industria", lang="en", paywall=False, topical=False,
         initials="GC", weight=2,
         poll=False, note="dominio non piu' risolvibile"),

    # ------------------------------------------------------------------
    # Associazioni e piattaforme di settore
    # ------------------------------------------------------------------
    dict(slug="hydrogen-europe", name="Hydrogen Europe", kind="rss",
         url="https://hydrogeneurope.eu/feed/",
         home="https://hydrogeneurope.eu",
         category="politica", lang="en", paywall=False, topical=True,
         initials="HE", weight=6),

    dict(slug="hydrogen-council", name="Hydrogen Council", kind="rss",
         url="https://hydrogencouncil.com/en/feed/",
         home="https://hydrogencouncil.com",
         category="industria", lang="en", paywall=False, topical=True,
         initials="HC", weight=5,
         poll=False, note="Cloudflare respinge le richieste automatiche (403)"),

    dict(slug="fchea", name="FCHEA", kind="rss",
         url="https://fchea.org/feed/",
         home="https://fchea.org",
         category="industria", lang="en", paywall=False, topical=True,
         initials="FC", weight=3),

    dict(slug="clean-hydrogen-partnership", name="Clean Hydrogen Partnership", kind="rss",
         url="https://www.clean-hydrogen.europa.eu/rss_en.xml",
         home="https://www.clean-hydrogen.europa.eu",
         category="politica", lang="en", paywall=False, topical=True,
         initials="CH", weight=7,
         poll=False, note="nessun RSS pubblico (404 su tutte le varianti)"),

    # ------------------------------------------------------------------
    # Istituzionali — Unione europea
    # ------------------------------------------------------------------
    # Il press corner e' l'unico endpoint istituzionale europeo che risponda a
    # uno script: energy.ec.europa.eu, CINEA e Clean Hydrogen Partnership non
    # espongono RSS (404 su tutte le varianti provate con la sonda).
    dict(slug="ec-presscorner", name="Commissione europea", kind="rss",
         url="https://ec.europa.eu/commission/presscorner/api/rss?language=en",
         home="https://ec.europa.eu/commission/presscorner/home/en",
         category="politica", lang="en", paywall=False, topical=False,
         initials="EC", weight=9),

    dict(slug="eea", name="Agenzia europea dell'ambiente", kind="rss",
         url="https://www.eea.europa.eu/en/newsroom/news/rss.xml",
         home="https://www.eea.europa.eu",
         category="politica", lang="en", paywall=False, topical=False,
         initials="EE", weight=6),

    # ------------------------------------------------------------------
    # Istituzionali — internazionali
    # ------------------------------------------------------------------
    dict(slug="iea", name="IEA", kind="rss",
         url="https://www.iea.org/rss/news",
         home="https://www.iea.org/energy-system/low-emission-fuels/hydrogen",
         category="politica", lang="en", paywall=False, topical=False,
         initials="IE", weight=9,
         poll=False, note="Cloudflare respinge le richieste automatiche (403)"),

    dict(slug="irena", name="IRENA", kind="rss",
         url="https://www.irena.org/rss/news",
         home="https://www.irena.org",
         category="politica", lang="en", paywall=False, topical=False,
         initials="IR", weight=7,
         poll=False, note="Cloudflare respinge le richieste automatiche (403)"),

    dict(slug="us-doe", name="US DOE — Energy", kind="rss",
         url="https://www.energy.gov/rss/articles.xml",
         home="https://www.energy.gov/eere/fuelcells/hydrogen-and-fuel-cell-technologies-office",
         category="politica", lang="en", paywall=False, topical=False,
         initials="DO", weight=6),

    # ------------------------------------------------------------------
    # Italia
    # ------------------------------------------------------------------
    dict(slug="rinnovabili", name="Rinnovabili.it", kind="rss",
         url="https://www.rinnovabili.it/tag/idrogeno/feed/",
         home="https://www.rinnovabili.it/tag/idrogeno/",
         category="industria", lang="it", paywall=False, topical=True,
         initials="RI", weight=4,
         poll=False, note="Cloudflare respinge le richieste automatiche (403)"),

    dict(slug="qualenergia", name="QualEnergia", kind="rss",
         url="https://www.qualenergia.it/feed/",
         home="https://www.qualenergia.it",
         category="politica", lang="it", paywall=False, topical=False,
         initials="QE", weight=5),

    dict(slug="canale-energia", name="Canale Energia", kind="rss",
         url="https://www.canaleenergia.com/feed/",
         home="https://www.canaleenergia.com",
         category="industria", lang="it", paywall=False, topical=False,
         initials="CE", weight=3),

    dict(slug="mase", name="MASE — Ministero Ambiente", kind="rss",
         url="https://www.mase.gov.it/rss/comunicati",
         home="https://www.mase.gov.it",
         category="politica", lang="it", paywall=False, topical=False,
         initials="MA", weight=8,
         poll=False, note="Cloudflare respinge le richieste automatiche (403)"),

    dict(slug="h2it", name="H2IT", kind="rss",
         url="https://www.h2it.it/feed/",
         home="https://www.h2it.it",
         category="politica", lang="it", paywall=False, topical=True,
         initials="HT", weight=6),

    # ------------------------------------------------------------------
    # Ricerca — preprint e letteratura
    # ------------------------------------------------------------------
    dict(slug="arxiv", name="arXiv", kind="arxiv",
         url=("http://export.arxiv.org/api/query?search_query="
              "abs:%22green+hydrogen%22+OR+abs:%22hydrogen+production%22+OR+"
              "abs:%22water+electrolysis%22+OR+abs:%22hydrogen+storage%22+OR+"
              "abs:%22electrolyser%22+OR+abs:%22electrolyzer%22+OR+"
              "abs:%22fuel+cell%22"
              "&sortBy=submittedDate&sortOrder=descending&max_results=40"),
         home="https://arxiv.org",
         category="ricerca", lang="en", paywall=False, topical=True,
         initials="aX", weight=6),

    dict(slug="openalex", name="OpenAlex", kind="openalex",
         url=("https://api.openalex.org/works?"
              "filter=title_and_abstract.search:hydrogen%20electrolysis%20OR%20"
              "green%20hydrogen%20OR%20hydrogen%20storage,"
              "from_publication_date:{since},type:article"
              "&sort=publication_date:desc&per-page=40"),
         home="https://openalex.org",
         category="ricerca", lang="en", paywall=False, topical=True,
         initials="OA", weight=4),
]

# Le fonti effettivamente interrogate a ogni run. Le altre restano elencate
# nella sezione «Fonti» del sito come riferimento, con il motivo per cui non
# sono automatizzabili.
POLLED = [s for s in SOURCES if s.get("poll", True)]
MANUAL = [s for s in SOURCES if not s.get("poll", True)]
BY_SLUG = {s["slug"]: s for s in SOURCES}


def matches_keywords(text):
    """True se il testo contiene almeno una parola chiave del dominio."""
    low = " " + (text or "").lower() + " "
    return any(k in low for k in KEYWORDS)
