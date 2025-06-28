import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def fetch_fstv_html():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Visiting FSTV...")
        await page.goto("https://fstv.us/live-tv.html?timezone=America%2FDenver", timeout=60000)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
        with open("FSTV_PAGE_SOURCE.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Saved full page source to FSTV_PAGE_SOURCE.html")

        await browser.close()

def update_playlist_from_html():
    with open("FSTV_PAGE_SOURCE.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Grab the stream URLs
    html_urls = []
    for div in soup.find_all("div", class_="item-channel"):
        url = div.get("data-link")
        if url:
            html_urls.append(url)

    with open("FSTV.m3u8", "r", encoding="utf-8") as f:
        playlist_lines = f.readlines()

    updated_lines = []
    url_index = 0

    for line in playlist_lines:
        if line.startswith("http") or line.startswith("https"):
            if url_index < len(html_urls):
                updated_lines.append(html_urls[url_index] + "\n")
                url_index += 1
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"🎯 Updated {url_index} URLs in FSTV24.m3u8")

async def main():
    await fetch_fstv_html()
    update_playlist_from_html()

if __name__ == "__main__":
    asyncio.run(main())
