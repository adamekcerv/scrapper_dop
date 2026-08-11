"""drbna.py – scraper pro ostravska.drbna.cz (RSS)"""
from .base import BaseScraper


class DrbnaScraper(BaseScraper):
    name = "drbna.cz"
    source_url = "https://ostravska.drbna.cz/rss/"

    def fetch_articles(self) -> list[dict]:
        items = self._get_rss_items()
        articles = []
        for item in items:
            art = self._rss_item_to_dict(item)
            if art["url"]:
                articles.append(art)
        return articles
