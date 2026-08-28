# Molecola — Osservatorio idrogeno

Rassegna automatica sull'idrogeno per uso di ricerca.
Sito: **https://deltadidirac30.github.io/molecola/** (italiano) ·
**/en/** (inglese) · **/archivio/** (archivio storico)

Niente testo scritto, riassunto o tradotto automaticamente: titoli, estratti e
date sono quelli pubblicati dalla fonte, con link diretto all'originale.

## Cosa fa

Ogni tre ore un workflow GitHub Actions esegue `scripts/build.py`, che:

1. legge le fonti definite in `scripts/sources.py` — stampa di settore, fonti
   istituzionali europee e italiane, preprint di ricerca (arXiv, OpenAlex);
2. filtra per parola chiave le fonti non specializzate (ministeri, agenzie,
   testate generaliste di energia), così resta solo l'idrogeno;
3. ripulisce gli estratti dal rumore ricorrente dei feed — i footer
   «The post … appeared first on …», le firme in testa, gli inviti alla lettura —
   e scarta quelli che ripetono solo il titolo;
4. aggiunge le novità a `data/archive.json`, l'archivio permanente in sola
   aggiunta;
5. rigenera **tutte** le pagine: home italiana e inglese, indice e pagine
   dell'archivio per anno, `feed.xml`, `sitemap.xml`, `robots.txt`.

La prima pagina si costruisce sempre dall'archivio, mai direttamente dalla
risposta delle fonti in quell'istante: se metà dei feed cade per un'ora, il
sito resta pieno e coerente invece di svuotarsi.

## Struttura

```
scripts/
  sources.py            elenco delle fonti — l'unico file da toccare per aggiungerne
  fetching.py           lettura e normalizzazione (RSS 2.0, RSS 1.0/RDF, Atom, arXiv, OpenAlex)
  store.py              archivio in append su data/archive.json
  i18n.py               stringhe dell'interfaccia, italiano e inglese
  render.py             generazione dell'HTML
  build.py              orchestratore
  check_sources.py      diagnostica delle fonti
  migrate_from_html.py  recupero una tantum dalle vecchie versioni di index.html
data/
  archive.json          archivio permanente (generato)
  indicators.json       cifre IEA della sezione «L'idrogeno in numeri» (a mano)
assets/                 CSS, JS, favicon, immagine di anteprima social
```

Tutto il resto (`index.html`, `en/`, `archivio/`, `feed.xml`, `sitemap.xml`,
`robots.txt`, `assets/favicon.svg`, `assets/social.svg`) è **generato**:
modificarlo a mano non serve, il build successivo lo sovrascrive.

## Lavorarci sopra

```bash
python3 scripts/build.py              # legge le fonti, aggiorna archivio e pagine
python3 scripts/build.py --offline    # rigenera le pagine dal solo archivio, senza rete
python3 scripts/build.py --dry-run    # legge le fonti senza scrivere nulla
python3 scripts/check_sources.py      # quali fonti rispondono, con quanti articoli
```

Solo standard library: nessuna dipendenza da installare, né in locale né in Actions.

### Aggiungere una fonte

Si aggiunge una riga a `SOURCES` in `scripts/sources.py` e basta: filtri,
legenda, sezione «Fonti» e colori si generano da soli. Prima di darla per
buona, lanciare **Actions → Verifica fonti → Run workflow**: i runner GitHub
hanno accesso pieno alla rete e dicono se l'endpoint risponde davvero.

Campo `topical`: `True` se la fonte pubblica solo idrogeno (si prende tutto),
`False` se è generalista (si tiene solo ciò che contiene una parola chiave).
Campo `paywall`: `True` se l'articolo completo richiede abbonamento — il sito
lo segnala al lettore prima del clic.
Campo `poll`: `False` per una fonte che non è interrogabile da uno script;
resta elencata nella sezione «Fonti» come riferimento, con in `note` il motivo.

### Trovare il feed giusto di una fonte nuova

**Actions → Verifica fonti → Run workflow**, campo *urls*: si incollano gli URL
candidati separati da spazio. Il workflow li prova tutti e scrive l'esito in
`data/probe-results.txt` — quali rispondono, con quanti articoli e quanto
recenti. Una misura invece di un tentativo alla cieca.

### Fonti che non si possono automatizzare

Nove fonti hanno `poll=False`. Non è una dimenticanza: sono state provate e
sono chiuse. IEA, IRENA, Hydrogen Council, MASE, Rinnovabili.it e H2 View
rispondono `403` a qualunque richiesta automatica — è Cloudflare che blocca gli
indirizzi dei datacenter, e non si aggira cambiando user-agent. CINEA e Clean
Hydrogen Partnership non espongono alcun RSS pubblico. Green Car Congress non
risolve più. Restano nella sezione «Fonti» del sito come link di riferimento,
con il motivo in `note`, così nessuno rifà la stessa strada.

### Aggiornare le cifre IEA

`data/indicators.json`, a mano, quando esce un nuovo *Global Hydrogen Review*.
Ogni cifra deve avere `cite` e `url` che puntano al capitolo esatto.

## Se qualcosa si rompe

`build.py` fallisce di proposito quando meno di 5 fonti producono articoli, o
quando l'articolo più recente ha più di 96 ore. Un job programmato che
fallisce fa partire un'email automatica al proprietario del repository — non
serve un servizio di monitoraggio esterno. La metrica è «quante fonti hanno
prodotto articoli», non «quante hanno risposto»: un feed che restituisce una
pagina d'errore risponde benissimo e non serve a niente.

Per capire quale fonte è caduta: **Actions → Verifica fonti → Run workflow**.

Se il sito pubblicato non si aggiorna nonostante nuovi commit su `main`, è
GitHub Pages che si è incantato: Settings → Pages → Source su «None», salvare,
poi di nuovo su «Deploy from a branch» / `main` / `/ (root)`.

## Diritti

Titoli ed estratti appartengono alle rispettive testate e organizzazioni, qui
riportati a fini di rassegna con link diretto all'originale. Le cifre IEA sono
riprodotte con attribuzione secondo la licenza CC BY 4.0 del *Global Hydrogen
Review*.
