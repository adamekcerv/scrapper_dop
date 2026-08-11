"""zdopravy.py – scraper pro zdopravy.cz (RSS)"""
from .base import BaseScraper


class ZdopravyScraper(BaseScraper):
    name = "zdopravy.cz"
    source_url = "https://zdopravy.cz/feed/"

    def fetch_articles(self) -> list[dict]:
        items = self._get_rss_items()
        articles = []
        for item in items:
            art = self._rss_item_to_dict(item)
            if art["url"]:
                articles.append(art)
        return articles
