import asyncio
from playwright.async_api import async_playwright, Request
import re
import random

LIVE_SCHEDULE_PAGE = "https://ppv.to/live/"
OUTPUT_FILE = "PPVLand.m3u8"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "text/html",
    "Referer": "https://ppv.to/",
}

CUSTOM_LOGO = "https://tinyurl.com/drewsportslogo"
CUSTOM_ID = "Sports.Dummy.us"
CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]

ALLOWED_CATEGORIES = {"Baseball", "Basketball", "Football", "Wrestling", "24/7 Streams"}

def build_m3u(entries, url_map):
    lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']

    for entry in entries:
        title = entry["title"]
        cid = entry["id"]
        url = url_map.get(cid, "#")
        group_title = entry.get("category", "Live Events")

        lines.append(f'#EXTINF:-1 tvg-id="{CUSTOM_ID}" tvg-logo="{CUSTOM_LOGO}" group-title="{group_title}",{title}')
        lines.extend(CUSTOM_HEADERS)
        lines.append(url)

    return "\n".join(lines)

async def fetch_live_events(page):
    """Scrape live event URLs and info from the main live page"""

    await page.goto(LIVE_SCHEDULE_PAGE, wait_until="domcontentloaded")

    # Extract event links & titles with categories from page anchors
    # Example href: /live/mlb-/2025-06-20/9179-chc or /live/wwe/smackdown/25-06-20
    anchors = await page.query_selector_all("a[href^='/live/']")

    events = []
    seen_urls = set()

    for a in anchors:
        href = await a.get_attribute("href")
        text = (await a.text_content()) or ""
        text = text.strip()
        if not href or href in seen_urls or not text:
            continue
        seen_urls.add(href)

        # Attempt to infer category from href
        # e.g. /live/mlb- -> Baseball, /live/wwe/ -> Wrestling, etc
        if "mlb" in href:
            category = "Baseball"
        elif "wnba" in href or "basketball" in href:
            category = "Basketball"
        elif "wwe" in href or "aew" in href or "wrestling" in href:
            category = "Wrestling"
        elif "football" in href or "soccer" in href or "liga" in href:
            category = "Football"
        elif "24-7" in href or "247" in href:
            category = "24/7 Streams"
        else:
            category = "Other"

        if category not in ALLOWED_CATEGORIES:
            continue

        events.append({
            "title": text,
            "url": "https://ppv.to" + href,
            "category": category,
            "id": href.split("/")[-1].replace(",", "-")  # crude unique id from URL last part
        })

    return events

async def scrape_streams(events):
    """Aggressively visit each event page and catch .m3u8 stream URLs"""

    url_map = {}

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for event in events:
            m3u8_links = []

            def on_request(request: Request):
                url = request.url.lower()
                if url.endswith(".m3u8") or ".m3u8?" in url:
                    print(f"🎯 Found .m3u8 URL: {request.url}")
                    m3u8_links.append(request.url)

            page.on("request", on_request)

            print(f"\n🔄 Scraping: {event['title']} ({event['id']})")
            try:
                await page.goto(event["url"], timeout=60000)
                tries = 0
                while not m3u8_links and tries < 3:
                    await asyncio.sleep(5)
                    tries += 1
                    print(f"⏳ Waiting for .m3u8... ({tries}/3)")
            except Exception as e:
                print(f"❌ Error scraping {event['title']}: {e}")

            page.remove_listener("request", on_request)

            if m3u8_links:
                url_map[event["id"]] = random.choice(m3u8_links)
                print(f"✅ Selected stream URL: {url_map[event['id']]}")
            else:
                url_map[event["id"]] = "#"
                print(f"⚠️ No stream found for {event['title']}")

        await browser.close()

    return url_map

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()

        print("🔍 Fetching live events...")
        events = await fetch_live_events(page)

        await browser.close()

    if not events:
        print("⚠️ No live events found.")
        return

    print(f"📺 Found {len(events)} live events")

    url_map = await scrape_streams(events)

    print("💾 Writing M3U playlist...")
    m3u_content = build_m3u(events, url_map)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"✅ Done. Playlist saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
