"""
base.py – Základní třída pro všechny scrapery.
"""

import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import parsedate_to_datetime

SEEN_URLS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seen_urls.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Kmeny slov pro Ostravu a její obvody (vč. skloňování: Ostravě, Ostravou, Porubě...)
OSTRAVA_STEMS = [
    "ostrav", "porub", "vítkovic", "vitkovic", "zábřeh", "zabreh",
    "hrabov", "hrabův", "hrabuv", "svinov", "mariánské hor", "marianske hor",
    "slezské ostrav", "slezske ostrav", "slezská ostrav", "slezska ostrav",
    "přívoz", "privoz", "radvanic", "bartovic", "michálkovic", "michalkovice",
    "staré běl", "stare bel", "stará běl", "stara bela", "nové běl", "nove bel", "nová běl", "nova bela",
    "kunčic", "kuncic", "polank", "pustkov", "třebovic", "trebovice",
    "hošťálkovic", "hostalkovice", "lhotk", "petřkovic", "petrkovice", "proskovic",
    "krásné pol", "krasne pol", "martinov", "plesn"
]

# Kmeny slov pro ostatní města v Moravskoslezském kraji
OTHER_CITY_STEMS = [
    "karvin", "havíř", "havir", "frýd", "fryd", "míst", "mist",
    "opav", "třinec", "trinec", "bohumín", "bohumin", "orlov",
    "nové jičín", "nove jicin", "nový jičín", "novy jicin", "novojičín", "novojicin",
    "krnov", "bruntál", "bruntal", "kopřivnic", "koprivnice",
    "české těšín", "ceske tesin", "český těšín", "cesky tesin",
    "hlučín", "hlucin", "frenštát", "frenstat", "studénk", "studenk",
    "příbor", "pribor", "bílovec", "bilovec", "rychvald", "petrovic",
    "václavovic", "vaclavovice", "šenov", "senov", "vratimov",
    "dětmarovic", "detmarovice", "albrechtic", "stonav", "těrlick", "terlick",
    "horní such", "horni such", "palkovic", "čeladn", "celadn", "nošovic", "nosovice",
    "jablunkov", "janovic", "návsí", "navsi", "dobré", "dobre", "dobrá", "dobra",
    "bašk", "bask", "paskov", "odry", "fulnek"
]


def load_seen_urls() -> set:
    """Načte již zpracované URL ze souboru (odolné vůči poškození)."""
    if os.path.exists(SEEN_URLS_FILE):
        try:
            with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
        except Exception as e:
            print(f"  [WARN] Nelze načíst seen_urls.json ({e}) – začínám s prázdnou databází.")
    return set()


def save_seen_urls(seen: set) -> None:
    """Uloží zpracované URL do souboru."""
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def detect_city(title: str, perex: str = "", category: str = "") -> str:
    """
    Chytrá detekce města:
    1. Titulek má nejvyšší váhu (např. nehoda ve Frýdku-Místku -> Jiné, i když je v textu Ostrava)
    2. Rubrika/kategorie má druhou nejvyšší váhu
    3. Perex a zbytek textu
    """
    title_lower = (title or "").lower()
    cat_lower   = (category or "").lower()
    perex_lower = (perex or "").lower()
    full_lower  = f"{title_lower} {cat_lower} {perex_lower}"

    title_ostrava = any(s in title_lower for s in OSTRAVA_STEMS)
    title_other   = any(s in title_lower for s in OTHER_CITY_STEMS)

    cat_ostrava   = any(s in cat_lower for s in OSTRAVA_STEMS)
    cat_other     = any(s in cat_lower for s in OTHER_CITY_STEMS)

    full_ostrava  = any(s in full_lower for s in OSTRAVA_STEMS)
    full_other    = any(s in full_lower for s in OTHER_CITY_STEMS)

    # 1. Titulek určuje město s nejvyšší prioritou
    if title_other and not title_ostrava:
        return "Jiné"
    if title_ostrava and not title_other:
        return "Ostrava"

    # 2. Kategorie (pokud titulek neobsahoval konkrétní město)
    if cat_other and not cat_ostrava:
        return "Jiné"
    if cat_ostrava and not cat_other:
        return "Ostrava"

    # 3. Zbytek textu
    if full_ostrava and not full_other:
        return "Ostrava"
    if full_other and not full_ostrava:
        return "Jiné"

    # 4. Pokud je zmíněno obojí v textu (např. trasa Ostrava-Opava)
    if full_ostrava:
        return "Ostrava"

    return "Jiné"


def parse_rfc822_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = parsedate_to_datetime(date_str.strip())
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return date_str.strip()


def parse_iso_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        clean = re.sub(r"[+-]\d{2}:\d{2}$", "", date_str.strip()).replace("Z", "")
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return date_str.strip()


class BaseScraper:
    name: str = "unknown"
    source_url: str = ""

    def fetch_articles(self) -> list[dict]:
        raise NotImplementedError

    def get_new_articles(self, seen_urls: set) -> list[dict]:
        all_articles = self.fetch_articles()
        new = [a for a in all_articles if a.get("url") not in seen_urls]
        return new

    def _get_soup_html(self, url: str = None) -> BeautifulSoup | None:
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
        target = url or self.source_url
        try:
            r = requests.get(target, headers=HEADERS, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            if not items:
                items = soup.find_all("entry")
            return items
        except Exception as e:
            print(f"[{self.name}] Chyba při stahování RSS {target}: {e}")
            return []

    def _rss_item_to_dict(self, item, extra_fields: dict = None) -> dict:
        title = (item.find("title") or item.find("title")).get_text(strip=True) if item.find("title") else ""
        url = ""
        link_tag = item.find("link")
        if link_tag:
            url = link_tag.get_text(strip=True) or link_tag.get("href", "")

        date_str = ""
        for tag in ["pubDate", "published", "updated", "dc:date"]:
            t = item.find(tag)
            if t:
                date_str = t.get_text(strip=True)
                break

        if "+" in date_str or date_str.endswith("Z") or re.search(r"\d{4}-\d{2}-\d{2}T", date_str):
            date_formatted = parse_iso_date(date_str)
        else:
            date_formatted = parse_rfc822_date(date_str)

        perex = ""
        for tag in ["description", "summary", "content:encoded"]:
            t = item.find(tag)
            if t:
                raw = t.get_text(strip=True)
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

        city = detect_city(title=title, perex=perex, category=category)

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
