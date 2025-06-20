import asyncio
from playwright.async_api import async_playwright, Request
import random

API_URL = "https://ppv.to/api/streams"
OUTPUT_FILE = "PPVLand.m3u8"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json",
    "Referer": "https://ppv.to/",
}

CUSTOM_LOGO = "https://tinyurl.com/drewsportslogo"
CUSTOM_ID = "Sports.Dummy.us"
CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]

ALLOWED_CATEGORIES = {"24/7 Streams", "Wrestling", "Football", "Basketball"}

def build_m3u(entries, url_map):
    lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']

    for entry in entries:
        title = entry["title"]
        cid = entry["channel_id"]
        url = url_map.get(cid, "#")

        tvg_id = CUSTOM_ID
        logo_url = CUSTOM_LOGO
        group_title = entry.get("category", "Live Events")

        lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo_url}" group-title="{group_title}",{title}')
        lines.extend(CUSTOM_HEADERS)
        lines.append(url)

    return "\n".join(lines)


async def fetch_schedule(page):
    try:
        res = await page.request.get(API_URL, headers=HEADERS)
        if not res.ok:
            print(f"❌ Failed to fetch API JSON: HTTP {res.status}")
            return []

        data = await res.json()
    except Exception as e:
        print(f"❌ Exception while fetching schedule: {e}")
        return []

    entries = []
    for category_data in data.get("streams", []):
        category_name = category_data.get("category", "")
        if category_name not in ALLOWED_CATEGORIES:
            continue
        for stream in category_data.get("streams", []):
            title = stream.get("name", "").strip()
            cid = str(stream.get("id", "")).strip()
            uri_name = stream.get("uri_name", "").strip()
            if not (title and cid and uri_name):
                continue  # skip incomplete entries
            entries.append({
                "title": title,
                "channel_id": cid,
                "uri_name": uri_name,
                "category": category_name
            })

    return entries


async def scrape_streams(entries):
    url_map = {}

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for entry in entries:
            cid = entry["channel_id"]
            if cid in url_map:
                continue

            m3u8_links = []

            def capture(request: Request):
                if ".m3u8" in request.url.lower():
                    print(f"🎯 Found .m3u8 URL: {request.url}")
                    m3u8_links.append(request.url)

            page.on("request", capture)

            try:
                print(f"\n🔄 Scraping: {entry['title']} (CID: {cid})")
                stream_url = f"https://ppv.to/live/{entry['uri_name']}"
                await page.goto(stream_url, timeout=60000)

                tries = 0
                while not m3u8_links and tries < 3:
                    await asyncio.sleep(5)
                    tries += 1
                    print(f"⏳ Waiting for .m3u8... ({tries}/3)")

            except Exception as e:
                print(f"❌ Error scraping CID {cid}: {e}")

            page.remove_listener("request", capture)

            if m3u8_links:
                url_map[cid] = random.choice(m3u8_links)
                print(f"✅ Selected stream URL: {url_map[cid]}")
            else:
                url_map[cid] = "#"
                print(f"⚠️ No stream found for CID {cid}")

        await browser.close()

    return url_map


async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        entries = await fetch_schedule(page)
        await browser.close()

    if not entries:
        print("⚠️ No streams found to scrape.")
        return

    print(f"\n📺 Found {len(entries)} streams to scrape")
    url_map = await scrape_streams(entries)

    print("💾 Writing M3U playlist...")
    m3u = build_m3u(entries, url_map)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u)

    print(f"\n✅ Done. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
