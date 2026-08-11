"""
polar.py – scraper pro polar.cz/zpravy/ostrava (HTML scraping)

Struktura stránky:
  - Každý článek: <div class="row mb-4-5">
    - Odkaz a titulek: <h2><a href="...">titulek</a></h2>
    - Datum/čas + kategorie: <div class="text-1 text-tertiary">
    - Perex: <p class="block-truncate">
    - Autor: <a href="/zpravy/redaktor/...">
"""
import re
from datetime import datetime
from .base import BaseScraper, detect_city, HEADERS
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://polar.cz"

CZECH_MONTHS = {
    "ledna": 1, "února": 2, "března": 3, "dubna": 4,
    "května": 5, "června": 6, "července": 7, "srpna": 8,
    "září": 9, "října": 10, "listopadu": 11, "prosince": 12,
}


def _parse_polar_date(text: str) -> str:
    """
    Parsuje datum ve formátu polar.cz:
      - 'Dnes 14:13'  → dnešní datum
      - 'Včera 14:05' → včerejší datum
      - '7. srpna 14:30' → konkrétní datum
    """
    from datetime import timedelta
    text = text.strip()
    now = datetime.now()

    if text.lower().startswith("dnes"):
        time_str = text.split()[-1]  # "14:13"
        try:
            return now.strftime(f"%d.%m.%Y {time_str}")
        except Exception:
            return now.strftime("%d.%m.%Y")

    if text.lower().startswith("včera"):
        time_str = text.split()[-1]
        yesterday = now - timedelta(days=1)
        try:
            return yesterday.strftime(f"%d.%m.%Y {time_str}")
        except Exception:
            return yesterday.strftime("%d.%m.%Y")

    # Formát: "7. srpna 14:30"
    m = re.match(r"(\d+)\.\s*(\w+)\s+(\d+:\d+)", text)
    if m:
        day, month_cs, time_str = m.group(1), m.group(2).lower(), m.group(3)
        month_num = CZECH_MONTHS.get(month_cs, 1)
        year = now.year
        return f"{int(day):02d}.{month_num:02d}.{year} {time_str}"

    return text


class PolarScraper(BaseScraper):
    name = "polar.cz"
    source_url = "https://polar.cz/zpravy/ostrava"

    def fetch_articles(self) -> list[dict]:
        articles = []
        try:
            r = requests.get(self.source_url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "lxml")
        except Exception as e:
            print(f"[polar.cz] Chyba při stahování: {e}")
            return []

        # Každý článek je v div.row.mb-4-5
        rows = soup.find_all("div", class_=lambda c: c and "mb-4-5" in c)

        for row in rows:
            # Titulek a URL
            h2 = row.find("h2")
            if not h2:
                continue
            a_tag = h2.find("a")
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if href.startswith("/"):
                url = BASE_URL + href
            else:
                url = href

            if not url or not title:
                continue

            # Datum + kategorie + autor
            meta_div = row.find("div", class_="text-1")
            date_str = ""
            category = ""
            author = ""
            if meta_div:
                spans = meta_div.find_all("span")
                # Datum je v prvních dvou spanech (den + čas)
                if len(spans) >= 2:
                    date_str = _parse_polar_date(f"{spans[0].get_text(strip=True)} {spans[1].get_text(strip=True)}")

                # Kategorie – odkaz na region
                region_links = meta_div.find_all("a", href=lambda h: h and "/zpravy/" in h and "/redaktor/" not in h)
                if region_links:
                    category = region_links[0].get_text(strip=True)

                # Autor – odkaz na redaktora
                author_links = meta_div.find_all("a", href=lambda h: h and "/redaktor/" in h)
                if author_links:
                    author = author_links[0].get_text(strip=True)

            # Perex
            perex_tag = row.find("p", class_=lambda c: c and "block-truncate" in c)
            perex = perex_tag.get_text(strip=True) if perex_tag else ""

            city = detect_city(f"{title} {perex} {category}")

            articles.append({
                "url": url,
                "title": title,
                "date": date_str,
                "perex": perex,
                "author": author,
                "category": category,
                "scraped_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "city": city,
                "source_name": self.name,
            })

        return articles
