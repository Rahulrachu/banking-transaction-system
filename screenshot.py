import asyncio
from playwright.async_api import async_playwright

async def scroll_all(page, y):
    await page.evaluate(f"""
    (() => {{
      const els = document.querySelectorAll('*');
      for (const el of els) {{
        if (el.scrollHeight > el.clientHeight + 500) el.scrollTop = {y};
      }}
      window.scrollTo(0, {y});
    }})()""")
    await page.wait_for_timeout(2000)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox", "--disable-gpu"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto("http://localhost:8501/", wait_until="domcontentloaded", timeout=60000)
        try:
            await page.wait_for_selector("text=Banking Transaction", timeout=60000)
        except Exception as e:
            print("selector wait failed:", e)
        try:
            await page.wait_for_selector("svg.main-svg", timeout=60000)
            print("chart svg found")
        except Exception as e:
            print("chart wait failed:", e)
        await page.wait_for_timeout(12000)
        # TOP screenshot first, pristine scroll 0
        await page.screenshot(path="screenshots/banking_dashboard.png", full_page=False)
        print("saved top")
        # warm all charts by scrolling through
        for y in [800, 1600, 2400, 3200, 4000, 4800, 5600, 6400, 7200, 8000]:
            await scroll_all(page, y)
        charts = await page.query_selector_all("svg.main-svg")
        print(f"charts rendered: {len(charts)}")
        # MID: scroll to Spending section (~1400)
        await scroll_all(page, 1400)
        await page.screenshot(path="screenshots/banking_dashboard_mid.png", full_page=False)
        print("saved mid")
        # BOTTOM: scroll to end
        await scroll_all(page, 9000)
        await page.wait_for_timeout(2000)
        await page.screenshot(path="screenshots/banking_dashboard_bottom.png", full_page=False)
        print("saved bottom")
        await browser.close()

asyncio.run(main())
