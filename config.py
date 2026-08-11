"""
config.py – Konfigurace scrapperu.

Změňte OUTPUT_PATH na cestu kam chcete ukládat výsledný Excel.
Může to být lokální cesta nebo cesta k OneDrive/SharePoint synchronizované složce.
"""

import os

# ── Výstupní cesta pro Excel ─────────────────────────────────────────────────
# Defaultní cesta (SharePoint/OneDrive synchronizovaná složka):
OUTPUT_PATH = r"C:\Users\cervenka\mappaostrava\Data - Dokumenty\4_MAPPA_PRAC\CERVENKA\Scrapper\vysledky.xlsx"

# Záložní cesta (pokud složka neexistuje, uloží sem):
FALLBACK_PATH = os.path.join(os.path.dirname(__file__), "vysledky.xlsx")


def get_output_path() -> str:
    """Vrátí platnou výstupní cestu – preferuje SharePoint, jinak lokální."""
    folder = os.path.dirname(OUTPUT_PATH)
    if os.path.isdir(folder):
        return OUTPUT_PATH
    print(f"  [WARN] Složka '{folder}' neexistuje, ukládám lokálně: {FALLBACK_PATH}")
    return FALLBACK_PATH
