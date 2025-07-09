import asyncio
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

M3U8_FILE = "TheTVApp.m3u8"  # your file to read and overwrite
BASE_URL = "https://thetvapp.to"
CHANNEL_LIST_URL = f"{BASE_URL}/tv"

def extract_real_m3u8(url: str):
    if "ping.gif" in url and "mu=" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        mu = qs.get("mu", [None])[0]
        if mu:
            return urllib.parse.unquote(mu)
    if ".m3u8" in url:
        return url
    return None

async def scrape_all_m3u8_urls():
    urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Loading TheTVApp channel list...")
        await page.goto(CHANNEL_LIST_URL)
        links = await page.locator("ol.list-group a").all()

        for link in links:
            href = await link.get_attribute("href")
            if not href:
                continue

            full_url = BASE_URL + href
            print(f"Scraping {full_url}")

            for quality in ["SD", "HD"]:
                stream_url = None
                new_page = await context.new_page()

                async def handle_response(response):
                    nonlocal stream_url
                    real = extract_real_m3u8(response.url)
                    if real and not stream_url:
                        stream_url = real

                new_page.on("response", handle_response)
                await new_page.goto(full_url)

                try:
                    await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
                except:
                    pass

                await asyncio.sleep(4)
                await new_page.close()

                if stream_url:
                    print(f"✅ {quality}: {stream_url}")
                    urls.append(stream_url)
                else:
                    print(f"❌ {quality} not found")

        await browser.close()
    return urls

def replace_urls_in_m3u8(lines, new_urls):
    result = []
    url_idx = 0
    for line in lines:
        if line.strip().startswith("http") and url_idx < len(new_urls):
            result.append(new_urls[url_idx])
            url_idx += 1
        else:
            result.append(line)
    return result

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    new_urls = await scrape_all_m3u8_urls()
    if not new_urls:
        print("❌ No new URLs scraped.")
        return

    updated_lines = replace_urls_in_m3u8(lines, new_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))

    print(f"\n✅ {M3U8_FILE} overwritten with fresh stream URLs.")

if __name__ == "__main__":
    asyncio.run(main())
