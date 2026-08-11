"""idnes.py – scraper pro idnes.cz/ostrava (RSS)"""
from .base import BaseScraper


class IdnesScraper(BaseScraper):
    name = "idnes.cz"
    source_url = "https://servis.idnes.cz/rss.aspx?c=ostrava"

    def fetch_articles(self) -> list[dict]:
        items = self._get_rss_items()
        articles = []
        for item in items:
            art = self._rss_item_to_dict(item)
            if art["url"]:
                articles.append(art)
        return articles
