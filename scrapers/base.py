"""
base.py – Základní třída pro všechny scrapery.
Obsahuje:
  - RSS parsing (společný pro většinu webů)
  - HTML scraping (záložní metoda)
  - Deduplikaci přes seen_urls.json
  - Detekci města
"""

import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

SEEN_URLS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seen_urls.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

OSTRAVA_KEYWORDS = [
    "ostrava", "ostravsk", "moravskoslezsk", "poruba", "vítkovice",
    "zábřeh", "hrabová", "svinov", "opava", "karviná", "havířov",
    "frýdek", "třinec", "bohumín", "orlová"
]


def load_seen_urls() -> set:
    """Načte již zpracované URL ze souboru."""
    if os.path.exists(SEEN_URLS_FILE):
        with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_urls(seen: set) -> None:
    """Uloží zpracované URL do souboru."""
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def detect_city(text: str) -> str:
    """Detekuje zda článek je o Ostravě nebo jiném městě."""
    text_lower = text.lower()
    for kw in OSTRAVA_KEYWORDS:
        if kw in text_lower:
            return "Ostrava"
    return "Jiné"


def parse_rfc822_date(date_str: str) -> str:
    """Parsuje RFC 822 datum z RSS (např. Mon, 01 Jan 2024 12:00:00 +0000)."""
    if not date_str:
        return ""
    try:
        dt = parsedate_to_datetime(date_str.strip())
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return date_str.strip()


def parse_iso_date(date_str: str) -> str:
    """Parsuje ISO 8601 datum."""
    if not date_str:
        return ""
    try:
        # Odstranit timezone pro jednodušší parsing
        clean = re.sub(r"[+-]\d{2}:\d{2}$", "", date_str.strip()).replace("Z", "")
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return date_str.strip()


class BaseScraper:
    """
    Základní třída pro všechny scrapery.
    Podtřídy musí implementovat metodu `fetch_articles()`.
    """

    # Název webu (zobrazí se jako název listu v Excelu)
    name: str = "unknown"
    # URL zdroje (RSS nebo HTML)
    source_url: str = ""

    def fetch_articles(self) -> list[dict]:
        """
        Vrátí seznam článků jako list slovníků.
        Každý slovník musí obsahovat alespoň:
          - url (str)
          - title (str)
          - date (str)  – formát DD.MM.YYYY HH:MM
          - perex (str)
          - author (str)
          - category (str)
          - scraped_at (str)
          - city (str)   – 'Ostrava' nebo 'Jiné'
          - source_name (str)
        """
        raise NotImplementedError

    def get_new_articles(self, seen_urls: set) -> list[dict]:
        """Vrátí pouze nové články (které nejsou v seen_urls)."""
        all_articles = self.fetch_articles()
        new = [a for a in all_articles if a.get("url") not in seen_urls]
        return new

    def _get_soup_html(self, url: str = None) -> BeautifulSoup | None:
        """Stáhne HTML stránku a vrátí BeautifulSoup objekt."""
        target = url or self.source_url
        try:
            r = requests.get(target, headers=HEADERS, timeout=20)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return BeautifulSoup(r.text, "lxml")
        except Exception as e:
            print(f"[{self.name}] Chyba při stahování HTML {target}: {e}")
            return None

    def _get_rss_items(self, url: str = None) -> list:
        """Stáhne RSS feed a vrátí seznam <item> elementů."""
        target = url or self.source_url
        try:
            r = requests.get(target, headers=HEADERS, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            if not items:
                items = soup.find_all("entry")  # Atom feed
            return items
        except Exception as e:
            print(f"[{self.name}] Chyba při stahování RSS {target}: {e}")
            return []

    def _rss_item_to_dict(self, item, extra_fields: dict = None) -> dict:
        """
        Převede <item> z RSS na standardní slovník článku.
        extra_fields: doplňkové hodnoty specifické pro daný web.
        """
        title = (item.find("title") or item.find("title")).get_text(strip=True) if item.find("title") else ""
        url = ""
        link_tag = item.find("link")
        if link_tag:
            url = link_tag.get_text(strip=True) or link_tag.get("href", "")

        # Datum – zkusíme různé tagy
        date_str = ""
        for tag in ["pubDate", "published", "updated", "dc:date"]:
            t = item.find(tag)
            if t:
                date_str = t.get_text(strip=True)
                break

        # Zkusit parsovat datum
        if "+" in date_str or date_str.endswith("Z") or re.search(r"\d{4}-\d{2}-\d{2}T", date_str):
            date_formatted = parse_iso_date(date_str)
        else:
            date_formatted = parse_rfc822_date(date_str)

        # Perex
        perex = ""
        for tag in ["description", "summary", "content:encoded"]:
            t = item.find(tag)
            if t:
                raw = t.get_text(strip=True)
                # Odstraníme HTML tagy pokud jsou přítomny
                raw_soup = BeautifulSoup(raw, "lxml")
                perex = raw_soup.get_text(strip=True)[:500]
                break

        author = ""
        for tag in ["author", "dc:creator", "creator"]:
            t = item.find(tag)
            if t:
                author = t.get_text(strip=True)
                break

        category = ""
        cats = item.find_all("category")
        if cats:
            category = ", ".join(c.get_text(strip=True) for c in cats[:3])

        city_text = f"{title} {perex}"
        city = detect_city(city_text)

        article = {
            "url": url,
            "title": title,
            "date": date_formatted,
            "perex": perex,
            "author": author,
            "category": category,
            "scraped_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "city": city,
            "source_name": self.name,
        }
        if extra_fields:
            article.update(extra_fields)
        return article
