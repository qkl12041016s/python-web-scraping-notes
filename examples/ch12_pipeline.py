"""Test a Scrapy item pipeline without starting a spider."""

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class CleanTitlePipeline:
    def process_item(self, item):
        adapter = ItemAdapter(item)
        title = adapter.get("title")
        if not isinstance(title, str) or not title.strip():
            raise DropItem("missing title")
        url = adapter.get("url")
        if not isinstance(url, str) or not url.strip():
            raise DropItem("missing URL")
        adapter["title"] = title.strip()
        adapter["url"] = url.strip()
        return item


if __name__ == "__main__":
    pipeline = CleanTitlePipeline()
    record = pipeline.process_item({"title": "  A title  ", "url": "/a"})
    assert record["title"] == "A title"
    try:
        pipeline.process_item({"title": "   ", "url": "/bad"})
    except DropItem:
        print("dropped blank title")
    else:
        raise AssertionError("Blank title must be rejected")
    print(record)
