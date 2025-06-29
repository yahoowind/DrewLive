from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright

async def fetch_fstv_html():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🌐 Visiting FSTV...")
        await page.goto("https://fstv.us/live-tv.html?timezone=America%2FDenver", timeout=60000)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
        await browser.close()
        return html

def build_playlist_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    channels = []

    for div in soup.find_all("div", class_="item-channel"):
        url = div.get("data-link")
        logo = div.get("data-logo")
        name = div.get("title")

        if url and name:
            channels.append({"url": url, "logo": logo, "name": name})

    playlist_lines = ['#EXTM3U\n']
    for ch in channels:
        playlist_lines.append(
            f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="FSTV",{ch["name"]}\n'
        )
        playlist_lines.append(ch["url"] + "\n")

    return playlist_lines

async def main():
    html = await fetch_fstv_html()
    playlist_lines = build_playlist_from_html(html)
    with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
        f.writelines(playlist_lines)
    print(f"✅ Generated playlist with {len(playlist_lines)//2} channels in FSTV24.m3u8")

if __name__ == "__main__":
    asyncio.run(main())