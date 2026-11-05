"""Parse article cards from a fixed HTML sample."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup


HTML = """<main>
  <article class="card"><h2>First article</h2>
    <a href="/articles/1">Read</a></article>
  <article class="card"><h2>Incomplete article</h2></article>
  <article class="card"><h2>Second article</h2>
    <a href="/articles/2">Read</a></article>
</main>"""

base_url = "https://example.org/list"
soup = BeautifulSoup(HTML, "html.parser")
records = []
for card in soup.select("article.card"):
    title = card.select_one("h2")
    link = card.select_one("a[href]")
    if title is None or link is None:
        continue
    records.append({
        "title": title.get_text(" ", strip=True),
        "url": urljoin(base_url, link["href"]),
    })

assert len(records) == 2
for record in records:
    print(record)
