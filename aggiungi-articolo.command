#!/bin/bash
# Doppio clic da Finder per aggiungere un articolo a mano al filo diretto.
cd "$(dirname "$0")" || exit 1
python3 scripts/add_article.py
echo
read -n 1 -s -r -p "Premi un tasto per chiudere."
