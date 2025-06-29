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

    # Grab channel data: title, logo, url
    channel_data = []
    for div in soup.find_all("div", class_="item-channel"):
        url = div.get("data-link")
        logo = div.get("data-logo", "")
        title = div.get("title", "Untitled Channel")
        if url:
            channel_data.append({
                "url": url,
                "logo": logo,
                "title": title
            })

    with open("FSTV.m3u8", "r", encoding="utf-8") as f:
        playlist_lines = f.readlines()

    updated_lines = []
    url_index = 0

    for line in playlist_lines:
        if line.startswith("#EXTINF") and url_index < len(channel_data):
            extinf = f'#EXTINF:-1 tvg-logo="{channel_data[url_index]["logo"]}" group-title="FSTV", {channel_data[url_index]["title"]}\n'
            updated_lines.append(extinf)
        elif line.startswith("http") or line.startswith("https"):
            if url_index < len(channel_data):
                updated_lines.append(channel_data[url_index]["url"] + "\n")
                url_index += 1
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    print(f"🎯 Updated {url_index} streams with logos and titles in FSTV24.m3u8")

async def main():
    await fetch_fstv_html()
    update_playlist_from_html()

if __name__ == "__main__":
    asyncio.run(main())
