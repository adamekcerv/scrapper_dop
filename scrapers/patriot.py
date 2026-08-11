"""patriot.py – scraper pro patriotmagazin.cz (RSS)"""
from .base import BaseScraper


class PatriotScraper(BaseScraper):
    name = "patriotmagazin.cz"
    source_url = "https://www.patriotmagazin.cz/rss/"

    def fetch_articles(self) -> list[dict]:
        items = self._get_rss_items()
        articles = []
        for item in items:
            art = self._rss_item_to_dict(item)
            if art["url"]:
                articles.append(art)
        return articles
