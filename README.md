# Molecola — Osservatorio idrogeno

Rassegna stampa automatica sull'idrogeno, pensata per un uso di ricerca:
niente contenuto scritto o tradotto artificialmente, solo titoli, estratti
e link reali presi da 8 feed RSS di settore (vedi `scripts/update_wire.py`
per l'elenco) e aggiornati ogni 3 ore da un workflow GitHub Actions
(`.github/workflows/update-news.yml`). Se meno di 3 fonti su 8 rispondono,
il job fallisce di proposito e GitHub manda un'email automatica al
proprietario del repository — non serve un servizio di monitoraggio esterno.

La homepage include anche:
- una sezione "L'idrogeno in numeri" con dati reali citati dal report IEA
  Global Hydrogen Review, aggiornata a mano (non da RSS);
- una sezione "Fonti" con i link diretti alle organizzazioni di settore e
  agli osservatori istituzionali di riferimento (IEA, DOE, Hydrogen Council,
  Hydrogen Europe, FCHEA).

Pubblicato con GitHub Pages dal branch `main`.
