import asyncio
from playwright.async_api import async_playwright

API_URL = "https://ppv.to/api/streams"

CUSTOM_LOGO = "https://tinyurl.com/drewsportslogo"
CUSTOM_ID = "Sports.Dummy.us"
CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]

ALLOWED_CATEGORIES = {"24/7 Streams", "Wrestling", "Football", "Basketball", "Baseball"}

async def get_streams():
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            return await resp.json()

async def grab_m3u8_from_iframe(page, iframe_url):
    found_streams = set()

    def handle_response(response):
        url = response.url
        if ".m3u8" in url and response.status == 200:
            if url not in found_streams:
                found_streams.add(url)
                print(f"🎥 Found stream URL: {url}")

    page.on("response", handle_response)
    print(f"🌐 Navigating to iframe: {iframe_url}")
    await page.goto(iframe_url)
    await asyncio.sleep(2)  # wait for ads/play button to appear

    viewport = page.viewport_size or {"width": 1280, "height": 720}
    center_x = viewport["width"] / 2
    center_y = viewport["height"] / 2

    print("🖱️ Aggressive clicking center to trigger play...")
    for i in range(10):
        print(f"Click #{i+1}")
        await page.mouse.click(center_x, center_y)
        await asyncio.sleep(0.2)

    print("⏳ Waiting 5 seconds for streams to load...")
    await asyncio.sleep(5)

    page.remove_listener("response", handle_response)
    return found_streams

def build_m3u(streams, url_map):
    lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    for s in streams:
        urls = url_map.get(s["name"], [])
        if not urls:
            continue
        for url in urls:
            lines.append(f'#EXTINF:-1 tvg-id="{CUSTOM_ID}" tvg-logo="{CUSTOM_LOGO}" group-title="{s["category"]}",{s["name"]}')
            for h in CUSTOM_HEADERS:
                lines.append(h)
            lines.append(url)
    return "\n".join(lines)

async def main():
    data = await get_streams()

    # Filter streams by allowed categories and collect all with iframe
    streams = []
    for category in data.get("streams", []):
        cat_name = category.get("category", "")
        if cat_name not in ALLOWED_CATEGORIES:
            continue
        for stream in category.get("streams", []):
            iframe = stream.get("iframe")
            if iframe:
                streams.append({
                    "name": stream.get("name"),
                    "iframe": iframe,
                    "category": cat_name
                })

    if not streams:
        print("No streams found in allowed categories.")
        return

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        url_map = {}
        for s in streams:
            print(f"\n🌐 Loading stream: {s['name']} ({s['category']})")
            found_urls = await grab_m3u8_from_iframe(page, s["iframe"])
            url_map[s["name"]] = found_urls

        await browser.close()

    print("\n📝 Writing to PPVLand.m3u8 ...")
    playlist = build_m3u(streams, url_map)
    with open("PPVLand.m3u8", "w", encoding="utf-8") as f:
        f.write(playlist)

    print("✅ Done! Playlist saved to PPVLand.m3u8")

asyncio.run(main())
