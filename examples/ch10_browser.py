"""Read a card inserted by JavaScript in a local browser page."""

import os
import sys

try:
    from playwright.sync_api import Error, sync_playwright
except ImportError:
    raise SystemExit(
        "缺少 Playwright。请在终端执行：\n"
        f'"{sys.executable}" -m pip install playwright'
    ) from None


HTML = """<main id="app"></main>
<script>
const app = document.querySelector('#app');
setTimeout(() => {
  app.innerHTML = '<article class="card"><h2>Ready</h2></article>';
}, 150);
</script>"""

def main():
    with sync_playwright() as playwright:
        channel = os.getenv("BROWSER_CHANNEL") or None
        try:
            browser = playwright.chromium.launch(channel=channel)
        except Error as error:
            reason = str(error).splitlines()[0]
            raise SystemExit(
                "浏览器启动失败。若尚未安装匹配的 Chromium，\n"
                "请在终端执行：\n"
                f'"{sys.executable}" -m playwright install chromium\n'
                "已安装 Edge 可在 PowerShell 设置：\n"
                "$env:BROWSER_CHANNEL='msedge'\n"
                "然后重跑本脚本；若仍失败，核对渠道和系统依赖。\n"
                f"原始原因：{reason}"
            ) from None
        try:
            page = browser.new_page()
            page.set_content(HTML)
            card = page.locator("article.card")
            card.wait_for(state="visible", timeout=2000)
            print(card.locator("h2").inner_text())
        finally:
            browser.close()


if __name__ == "__main__":
    main()
