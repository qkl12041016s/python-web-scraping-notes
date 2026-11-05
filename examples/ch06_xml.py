"""Parse a namespaced XML response only after validating its type."""

from xml.etree import ElementTree


SOURCE = """<feed xmlns="urn:example:articles">
  <article id="1"><title>First</title></article>
  <article id="2"><title>Second</title></article>
</feed>"""
NS = {"a": "urn:example:articles"}


def parse_xml(status: int, content_type: str, source: str) -> list[dict]:
    if status != 200 or "xml" not in content_type.lower():
        raise ValueError("Expected a successful XML response")
    root = ElementTree.fromstring(source)
    records = []
    for article in root.findall("a:article", NS):
        article_id = (article.get("id") or "").strip()
        title = (article.findtext("a:title", default="", namespaces=NS) or "").strip()
        if not article_id or not title:
            raise ValueError("XML article has a missing required field")
        records.append({"id": article_id, "title": title})
    return records


if __name__ == "__main__":
    result = parse_xml(200, "application/xml", SOURCE)
    assert result == [{"id": "1", "title": "First"},
                      {"id": "2", "title": "Second"}]
    print(result)
