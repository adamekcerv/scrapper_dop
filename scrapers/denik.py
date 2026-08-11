"""denik.py – scraper pro moravskoslezsky.denik.cz (RSS)"""
from .base import BaseScraper


class DenikScraper(BaseScraper):
    name = "denik.cz"
    source_url = "https://moravskoslezsky.denik.cz/rss/index.html"

    def fetch_articles(self) -> list[dict]:
        items = self._get_rss_items()
        articles = []
        for item in items:
            art = self._rss_item_to_dict(item)
            if art["url"]:
                articles.append(art)
        return articles
