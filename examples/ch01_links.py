"""Extract same-site HTTP links from a fixed HTML fragment."""

from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit


class LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.allowed_host = urlsplit(base_url).hostname
        self.links: list[str] = []
        self.seen: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if not href:
            return
        absolute_url = urljoin(self.base_url, href)
        parts = urlsplit(absolute_url)
        if parts.scheme not in {"http", "https"} or parts.hostname != self.allowed_host:
            return
        clean_url = urldefrag(absolute_url).url
        if clean_url not in self.seen:
            self.seen.add(clean_url)
            self.links.append(clean_url)


if __name__ == "__main__":
    html = """<a href="/articles/intro#top">Intro</a>
    <a href="https://example.org/articles/advanced">Advanced</a>
    <a href="/articles/intro#comments">Intro again</a>
    <a href="https://other.example/articles/1">Other site</a>
    <a href="javascript:alert(1)">Script</a>"""
    parser = LinkParser("https://example.org/catalog/index.html")
    parser.feed(html)
    for link in parser.links:
        print(link)
