"""okraj.py – scraper pro okraj.cz (RSS)"""
from .base import BaseScraper


class OkrajScraper(BaseScraper):
    name = "okraj.cz"
    source_url = "https://www.okraj.cz/feed/"

    def fetch_articles(self) -> list[dict]:
        items = self._get_rss_items()
        articles = []
        for item in items:
            art = self._rss_item_to_dict(item)
            if art["url"]:
                articles.append(art)
        return articles
