"""A Scrapy spider that reads only a bundled local HTML fixture."""

from pathlib import Path

import scrapy


class LocalArticlesSpider(scrapy.Spider):
    name = "local_articles"
    start_urls = [
        (Path(__file__).parent / "fixtures" / "articles.html").resolve().as_uri()
    ]

    def parse(self, response):
        for card in response.css("article.card"):
            title = card.css("h2::text").get()
            href = card.css("a::attr(href)").get()
            if title and href:
                yield {"title": title.strip(), "url": response.urljoin(href)}
