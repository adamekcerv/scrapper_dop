"""
app.py – Hlavni orchestrator web scrapperu.

Spuštění:
    python app.py                  # Normální běh (pouze nové články)
    python app.py --reset          # Vymaže seen_urls.json a zpracuje vše znovu
    python app.py --output D:\path\vysledky.xlsx  # Vlastní cesta pro výstup

Workflow:
    1. Načti seznam již zpracovaných URL (seen_urls.json)
    2. Pro každý web spusť scraper a získej nové články
    3. Zapiš nové články do výstupního Excelu
    4. Ulož aktualizovaný seznam zpracovaných URL
    5. Vypiš souhrnný přehled
"""

import argparse
import io
import os
import sys
from datetime import datetime

# Nastavit UTF-8 pro Windows konzoli (PowerShell / cmd)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Přidání kořenového adresáře do path (pro spuštění odkudkoliv)
sys.path.insert(0, os.path.dirname(__file__))

from scrapers.base import load_seen_urls, save_seen_urls
from scrapers.polar     import PolarScraper
from scrapers.zdopravy  import ZdopravyScraper
from scrapers.denik     import DenikScraper
from scrapers.msstavby  import MsstavbyScraper
from scrapers.drbna     import DrbnaScraper
from scrapers.okraj     import OkrajScraper
from scrapers.idnes     import IdnesScraper
from scrapers.patriot   import PatriotScraper
from excel_writer       import write_articles_to_excel
from config             import get_output_path

# ── Registr všech scraperů ────────────────────────────────────────────────────
ALL_SCRAPERS = [
    PolarScraper(),
    ZdopravyScraper(),
    DenikScraper(),
    MsstavbyScraper(),
    DrbnaScraper(),
    OkrajScraper(),
    IdnesScraper(),
    PatriotScraper(),
]


def run(output_path: str = None, reset: bool = False):
    """Hlavní funkce – spustí všechny scrapery a zapíše výsledky."""
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"  Web Scrapper – start: {start_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"{'='*60}")

    # Reset seen_urls pokud požadováno
    if reset:
        from scrapers.base import SEEN_URLS_FILE
        if os.path.exists(SEEN_URLS_FILE):
            os.remove(SEEN_URLS_FILE)
            print("  [INFO] seen_urls.json byl vymazán – zpracovávám vše znovu.\n")

    seen_urls = load_seen_urls()
    print(f"  [INFO] Načteno {len(seen_urls)} již zpracovaných URL.\n")

    all_new_articles = []
    stats = {}

    for scraper in ALL_SCRAPERS:
        print(f"  [{scraper.name}] Scrapuji...", end=" ", flush=True)
        try:
            new_articles = scraper.get_new_articles(seen_urls)
            stats[scraper.name] = len(new_articles)
            all_new_articles.extend(new_articles)

            # Přidat URL do seen
            for art in new_articles:
                if art.get("url"):
                    seen_urls.add(art["url"])

            print(f"OK {len(new_articles)} novych clanku")
        except Exception as e:
            print(f"CHYBA: {e}")
            stats[scraper.name] = 0

    print()

    # Zápis do Excelu
    if all_new_articles:
        out = output_path or get_output_path()
        print(f"  [EXCEL] Zapisuji {len(all_new_articles)} clanku do: {out}")
        try:
            written = write_articles_to_excel(all_new_articles, out)
            print(f"  [EXCEL] ✓ Úspěšně zapsáno {written} článků.")
        except Exception as e:
            print(f"  [EXCEL] ✗ Chyba při zápisu: {e}")

        # Uložit nove_zpravy.json pro Power Automate
        try:
            import json
            json_file = os.path.join(os.path.dirname(__file__), "nove_zpravy.json")
            formatted_json = [
                {
                    "Web": a.get("source_name", ""),
                    "Titulek": a.get("title", ""),
                    "URL": a.get("url", ""),
                    "Datum": a.get("date", ""),
                    "Mesto": a.get("city", "Jiné"),
                    "ScrapedAt": a.get("scraped_at", ""),
                    "Autor": a.get("author", ""),
                    "Kategorie": a.get("category", "")
                }
                for a in all_new_articles
            ]
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(formatted_json, f, ensure_ascii=False, indent=2)
            print(f"  [JSON] Uloženo {len(formatted_json)} nových článků do nove_zpravy.json.")
        except Exception as e:
            print(f"  [JSON] Chyba při zápisu JSON: {e}")
    else:
        print("  [INFO] Žádné nové články k zapsání.")
        # Vytvořit prázdný JSON
        try:
            import json
            json_file = os.path.join(os.path.dirname(__file__), "nove_zpravy.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # Uložit seen_urls
    save_seen_urls(seen_urls)
    print(f"  [INFO] seen_urls.json uložen ({len(seen_urls)} URL celkem).")

    # Souhrnný přehled
    elapsed = (datetime.now() - start_time).seconds
    print(f"\n{'='*60}")
    print(f"  PŘEHLED – {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} ({elapsed}s)")
    print(f"{'='*60}")
    for name, count in stats.items():
        bar = "█" * min(count, 30)
        print(f"  {name:<25} {count:>4} nových  {bar}")
    total = sum(stats.values())
    print(f"{'─'*60}")
    print(f"  {'CELKEM':<25} {total:>4} nových článků")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Web scrapper pro moravskoslezské zpravodajské weby."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Cesta pro výstupní Excel soubor (výchozí: vysledky.xlsx ve složce skriptu)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Vymaže seen_urls.json a zpracuje všechny články znovu (první spuštění)"
    )
    args = parser.parse_args()

    run(output_path=args.output, reset=args.reset)


if __name__ == "__main__":
    main()
