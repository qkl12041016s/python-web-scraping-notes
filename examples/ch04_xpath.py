"""Extract records with relative XPath from local HTML."""

from lxml import html


SOURCE = """<main>
<article class="card"><h2>One</h2><a href="/item/1">Open</a></article>
<article class="card"><h2>Incomplete</h2></article>
<article class="card"><h2>Two</h2><a href="/item/2">Open</a></article>
</main>"""

def extract_cards(source: str) -> list[tuple[str, str]]:
    if not source.strip():
        raise ValueError("Empty response body is not a valid page sample")
    root = html.fromstring(source)
    records = []
    cards = root.xpath('//article[contains(concat(" ", normalize-space(@class), " "), " card ")]')
    for card in cards:
        titles = card.xpath(".//h2//text()")
        links = card.xpath(".//a/@href")
        title = " ".join(part.strip() for part in titles if part.strip())
        if title and links and links[0].strip():
            records.append((title, links[0].strip()))
    return records


if __name__ == "__main__":
    records = extract_cards(SOURCE)
    assert records == [("One", "/item/1"), ("Two", "/item/2")]
    print(records)
