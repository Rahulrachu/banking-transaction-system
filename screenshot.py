import asyncio
from playwright.async_api import async_playwright

async def scroll_main(page, y):
    await page.evaluate(f"""(() => {{
      const c = document.querySelector('[data-testid="stMain"]');
      if (c) c.scrollTop = {y};
    }})()""")
    await page.wait_for_timeout(900)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox", "--disable-gpu"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto("http://localhost:8501/", wait_until="domcontentloaded", timeout=60000)
        try:
            await page.wait_for_selector("text=Your money", timeout=90000)
            print("hero found")
        except Exception as e:
            print("hero wait failed:", e)
        try:
            await page.wait_for_selector("svg.main-svg", timeout=90000)
            print("chart svg found")
        except Exception as e:
            print("chart wait failed:", e)
        # wait for CSS fade-up animations + count-up to finish
        await page.wait_for_timeout(5000)
        try:
            kpi = await page.inner_text(".kpi-row")
            print("KPI row text:", kpi[:200].replace("\n", " | "))
        except Exception as e:
            print("kpi read failed:", e)
        try:
            diag = await page.evaluate("""(() => {
              const c = document.querySelector('[data-testid="stAppViewContainer"]');
              const hero = document.querySelector('.hero');
              const op = hero ? getComputedStyle(hero).opacity : 'no-hero';
              return {scrollTop: c ? c.scrollTop : -1, scrollHeight: c ? c.scrollHeight : -1,
                      heroOpacity: op, docH: document.body.scrollHeight};
            })()""")
            print("diag:", diag)
        except Exception as e:
            print("diag failed:", e)
        # TOP screenshot at scroll 0
        await scroll_main(page, 0)
        await page.wait_for_timeout(1200)
        await page.screenshot(path="screenshots/banking_dashboard.png", full_page=False)
        print("saved top")
        # warm all charts: slow scroll to bottom
        maxh = await page.evaluate("""(() => {
          const c = document.querySelector('[data-testid="stMain"]');
          return c ? c.scrollHeight : document.body.scrollHeight;
        })()""")
        print("main scrollHeight:", maxh)
        y = 0
        while y < int(maxh):
            y += 450
            await scroll_main(page, y)
        charts = await page.query_selector_all("svg.main-svg")
        print(f"charts rendered: {len(charts)}")
        # MID ~45%
        await scroll_main(page, int(int(maxh) * 0.45))
        await page.wait_for_timeout(1200)
        await page.screenshot(path="screenshots/banking_dashboard_mid.png", full_page=False)
        print("saved mid")
        # BOTTOM at max
        await scroll_main(page, int(maxh))
        await page.wait_for_timeout(1200)
        await page.screenshot(path="screenshots/banking_dashboard_bottom.png", full_page=False)
        print("saved bottom")
        await browser.close()

asyncio.run(main())
