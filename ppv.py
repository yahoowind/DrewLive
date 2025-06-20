import asyncio
from playwright.async_api import async_playwright, Request

OUTPUT_FILE = "PPVLand.m3u8"

CUSTOM_LOGO = "https://tinyurl.com/drewsportslogo"
CUSTOM_ID = "Sports.Dummy.us"
CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]


def build_m3u(entries, url_map):
    lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']

    for entry in entries:
        title = entry["title"]
        cid = entry["channel_id"]
        url = url_map.get(cid, "#")

        group_title = entry.get("category", "Live Events")

        lines.append(f'#EXTINF:-1 tvg-id="{CUSTOM_ID}" tvg-logo="{CUSTOM_LOGO}" group-title="{group_title}",{title}')
        lines.extend(CUSTOM_HEADERS)
        lines.append(url)

    return "\n".join(lines)


async def fetch_live_streams_from_page(page):
    await page.goto("https://ppv.to/live", timeout=60000)

    # Select all <a> tags with data-id attribute (stream entries)
    stream_links = await page.query_selector_all("a[data-id]")

    entries = []
    for link in stream_links:
        cid = await link.get_attribute("data-id")
        uri_name = await link.get_attribute("data-uri")
        raw_title = await link.inner_text()
        title = " ".join(raw_title.splitlines()).strip()

        if cid and title and uri_name:
            entries.append({
                "title": title,
                "channel_id": cid,
                "uri_name": uri_name,
                "category": "Live"
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
                url = request.url.lower()
                if url.endswith(".m3u8") or ".m3u8?" in url:
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
                # Prefer links containing 'master' or 'index' if available
                m3u8_links.sort(key=lambda u: ('master' in u or 'index' in u), reverse=True)
                selected = m3u8_links[0]
                url_map[cid] = selected
                print(f"✅ Selected stream URL: {selected}")
            else:
                url_map[cid] = "#"
                print(f"⚠️ No stream found for CID {cid}")

        await browser.close()

    return url_map


async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        entries = await fetch_live_streams_from_page(page)
        await browser.close()

    if not entries:
        print("⚠️ No live streams found.")
        return

    print(f"\n📺 Found {len(entries)} live streams to scrape")
    url_map = await scrape_streams(entries)

    print("💾 Writing M3U playlist...")
    m3u = build_m3u(entries, url_map)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u)

    print(f"\n✅ Done. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
