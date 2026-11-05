"""Read a card inserted by JavaScript in a local browser page."""

import os

from playwright.sync_api import sync_playwright


HTML = """<main id="app"></main>
<script>
const app = document.querySelector('#app');
setTimeout(() => {
  app.innerHTML = '<article class="card"><h2>Ready</h2></article>';
}, 150);
</script>"""

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel=os.getenv("BROWSER_CHANNEL"))
    page = browser.new_page()
    page.set_content(HTML)
    card = page.locator("article.card")
    card.wait_for(state="visible", timeout=2000)
    print(card.locator("h2").inner_text())
    browser.close()
