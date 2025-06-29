from bs4 import BeautifulSoup
import asyncio
import json
from playwright.async_api import async_playwright

# 🔁 Load name mappings
def load_name_mapping(filename="FSTV-mapping.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load mapping file: {e}")
        return {}

# 🌐 Scrape HTML from site
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

# 🛠️ Build playlist and apply mapping
def build_playlist_from_html(html, name_mapping):
    soup = BeautifulSoup(html, "html.parser")
    channels = []

    for div in soup.find_all("div", class_="item-channel"):
        url = div.get("data-link")
        logo = div.get("data-logo")
        original_name = div.get("title")

        if not url or not logo or not original_name:
            print(f"⚠️ Skipping channel due to missing data: {original_name}")
            continue

        # 👇 Normalize key for mapping (case-insensitive, strip whitespace)
        normalized_key = original_name.strip().lower()
        mapped_name = name_mapping.get(normalized_key, original_name)

        channels.append({
            "url": url.strip(),
            "logo": logo.strip(),
            "name": mapped_name.strip()
        })

    playlist_lines = ['#EXTM3U\n']
    for ch in channels:
        playlist_lines.append(
            f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="FSTV",{ch["name"]}\n'
        )
        playlist_lines.append(ch["url"] + "\n")

    return playlist_lines

# 🚀 Main flow
async def main():
    name_mapping = load_name_mapping()
    html = await fetch_fstv_html()
    playlist_lines = build_playlist_from_html(html, name_mapping)
    with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
        f.writelines(playlist_lines)
    print(f"✅ Generated playlist with {len(playlist_lines)//2} channels in FSTV24.m3u8")

if __name__ == "__main__":
    asyncio.run(main())
