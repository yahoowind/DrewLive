import asyncio
import re
from playwright.async_api import async_playwright
import json

EVENT_LIST = [
    {
        "title": "Chicago Cubs vs. Seattle Mariners",
        "url": "https://ppv.to/live/mlb-/2025-06-20/9179-chc",
        "cid": 8840
    },
    # Add more events as needed...
]

OUTPUT_FILE = "PPVLiveStreams.m3u"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Referer": "https://ppv.to/"
}


def clean_title(title):
    return re.sub(r'[^a-zA-Z0-9 \-]', '', title)


async def extract_stream_from_iframe(iframe_url, context):
    page = await context.new_page()
    m3u8_urls = []

    def handle_request(request):
        if ".m3u8" in request.url:
            print(f"🎯 Found .m3u8 URL: {request.url}")
            m3u8_urls.append(request.url)

    page.on("request", handle_request)

    try:
        await page.goto(iframe_url, timeout=20000)
        await asyncio.sleep(10)
    except Exception as e:
        print(f"❌ Failed to load iframe: {iframe_url}\n{e}")
    await page.close()
    return m3u8_urls


async def main():
    playlist = "#EXTM3U\n"

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(extra_http_headers=HEADERS)

        for event in EVENT_LIST:
            print(f"\n🔄 Scraping: {event['title']} (CID: {event['cid']})")
            event_page = await context.new_page()
            try:
                await event_page.goto(event["url"], timeout=20000)
                content = await event_page.content()

                match = re.search(r'<iframe[^>]+src="([^"]+veplay[^"]+)"', content)
                if not match:
                    print("⚠️ No iframe found.")
                    await event_page.close()
                    continue

                iframe_url = match.group(1)
                print(f"🔎 Found iframe: {iframe_url}")
                await event_page.close()

                m3u8_links = await extract_stream_from_iframe(iframe_url, context)
                final_stream = next((url for url in m3u8_links if "master.m3u8" in url or ".m3u8" in url), None)

                if final_stream:
                    print(f"✅ Final stream: {final_stream}")
                    playlist += f"#EXTINF:-1,{clean_title(event['title'])}\n{final_stream}\n"
                else:
                    print("❌ No working .m3u8 found.")

            except Exception as err:
                print(f"❌ Error scraping event: {err}")
                await event_page.close()

        await browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(playlist)
    print(f"\n✅ Saved playlist to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
