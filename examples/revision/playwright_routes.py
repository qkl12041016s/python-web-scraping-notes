import asyncio
import os
import sys
try:
    from playwright.async_api import Error, async_playwright
except ImportError:
    raise SystemExit(
        "缺少 Playwright，请在终端执行：\n"
        f'"{sys.executable}" -m pip install playwright'
    ) from None


ORIGIN = "http://127.0.0.1:8765"
HTML = """<!doctype html><meta charset="utf-8">
<button id="load">Load</button><p id="result"></p>
<script>
window.notesRPC = (x) => ({title: x.title.trim()});
document.querySelector('#load').onclick = async () => {
  const response = await fetch('/api/items');
  const data = await response.json();
  document.querySelector('#result').textContent = data.title;
};
</script>"""


async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                channel=os.getenv("BROWSER_CHANNEL") or None
            )
        except Error as error:
            raise SystemExit(
                "浏览器启动失败；先在终端安装匹配内核：\n"
                f'"{sys.executable}" -m playwright install chromium\n'
                "或在已安装 Edge 的 PowerShell 设置：\n"
                "$env:BROWSER_CHANNEL='msedge'\n"
                f"原始原因：{str(error).splitlines()[0]}"
            ) from None
        try:
            context = await browser.new_context(
                service_workers="block"
            )
            await context.route(
                ORIGIN + "/",
                lambda route: route.fulfill(
                    content_type="text/html", body=HTML
                ),
            )
            await context.route(
                ORIGIN + "/api/items",
                lambda route: route.fulfill(
                    json={"title": "Local notes"}
                ),
            )
            page = await context.new_page()
            page.set_default_timeout(5000)
            await page.goto(ORIGIN + "/")
            async with page.expect_response("**/api/items") as result:
                await page.locator("#load").click()
            response = await result.value
            print(response.status, await response.json())
            rpc = await page.evaluate(
                "x => window.notesRPC(x)", {"title": " notes "}
            )
            print(rpc)
            await context.close()
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
