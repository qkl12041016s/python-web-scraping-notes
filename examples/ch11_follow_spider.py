"""Follow two local pages and let an enabled Pipeline drop a bad item."""

from pathlib import Path
import scrapy


class FollowLocalSpider(scrapy.Spider):
    name = "follow_local"
    start_urls = [(Path(__file__).parent / "fixtures" / "ch11_page1.html").resolve().as_uri()]
    custom_settings = {
        "ITEM_PIPELINES": {"examples.ch12_pipeline.CleanTitlePipeline": 300},
        "LOG_LEVEL": "ERROR",
    }

    def parse(self, response):
        for card in response.css("article.card"):
            href = card.css("a::attr(href)").get(default="")
            yield {"title": card.css("h2::text").get(default=""),
                   "url": response.urljoin(href) if href else ""}
        next_href = response.css("a[rel=next]::attr(href)").get()
        if next_href:
            yield response.follow(next_href, callback=self.parse)
