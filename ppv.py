import asyncio
from playwright.async_api import async_playwright
import aiohttp

API_URL = "https://ppv.to/api/streams"

CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]

ALLOWED_CATEGORIES = {
    "24/7 Streams", "Wrestling", "Football", "Basketball", "Baseball",
    "Boxing", "Fighting", "MMA", "Combat Sports"
}

CATEGORY_LOGOS = {
    "24/7 Streams": "http://drewlive24.duckdns.org:9000/Logos/247.png",
    "Wrestling": "http://drewlive24.duckdns.org:9000/Logos/Wrestling.png",
    "Football": "http://drewlive24.duckdns.org:9000/Logos/Football.png",
    "Basketball": "http://drewlive24.duckdns.org:9000/Logos/Basketball.png",
    "Baseball": "http://drewlive24.duckdns.org:9000/Logos/Baseball.png",
    "Boxing": "http://drewlive24.duckdns.org:9000/Logos/Boxing.png",
    "Fighting": "http://drewlive24.duckdns.org:9000/Logos/Boxing.png",
    "MMA": "http://drewlive24.duckdns.org:9000/Logos/MMA.png",
    "Combat Sports": "http://drewlive24.duckdns.org:9000/Logos/Combat-Sports.png"
}

CATEGORY_TVG_IDS = {
    "24/7 Streams": "24.7.Dummy.us",
    "Football": "Soccer.Dummy.us",
    "Boxing": "PPV.EVENTS.Dummy.us",
    "MMA": "UFC.Fight.Pass.Dummy.us",
    "Wrestling": "PPV.EVENTS.Dummy.us",
    "Combat Sports": "PPV.EVENTS.Dummy.us",
    "Fighting": "PPV.EVENTS.Dummy.us",
    "Baseball": "Baseball.Dummy.us",
    "Basketball": "Basketball.Dummy.us"
}

async def get_streams():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            return await resp.json()

async def grab_m3u8_from_iframe(page, iframe_url):
    found_stream = None

    def handle_response(response):
        nonlocal found_stream
        url = response.url

        if found_stream:
            return  # Already found

        if ".m3u8" not in url.lower():
            return  # Not a playlist URL

        if response.status != 200:
            return  # Bad response status

        # Ignore URLs with ad/tracking keywords
        blacklist = ["ads", "preview", "test", "promo", "tracker", "doubleclick"]
        if any(word in url.lower() for word in blacklist):
            return

        # Ensure URL ends with .m3u8 (ignore query params)
        if not url.lower().split("?")[0].endswith(".m3u8"):
            return

        found_stream = url
        print(f"🎥 Found candidate stream URL: {url}")

    page.on("response", handle_response)
    print(f"🌐 Navigating to iframe: {iframe_url}")
    await page.goto(iframe_url)
    await asyncio.sleep(3)

    viewport = page.viewport_size or {"width": 1280, "height": 720}
    center_x = viewport["width"] / 2
    center_y = viewport["height"] / 2

    print("🖱️ Aggressively clicking center to trigger play...")
    for i in range(10):
        if found_stream:
            break
        print(f"Click #{i+1}")
        await page.mouse.click(center_x, center_y)
        await asyncio.sleep(0.3)

    print("⏳ Waiting 10 seconds for stream to load...")
    await asyncio.sleep(10)

    page.remove_listener("response", handle_response)
    return {found_stream} if found_stream else set()

def build_m3u(streams, url_map):
    lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    for s in streams:
        urls = url_map.get(s["name"], [])
        if not urls:
            continue
        logo = CATEGORY_LOGOS.get(s["category"], "")
        tvg_id = CATEGORY_TVG_IDS.get(s["category"], "Sports.Dummy.us")
        for url in urls:
            lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{s["category"]}",{s["name"]}')
            lines.extend(CUSTOM_HEADERS)
            lines.append(url)
    return "\n".join(lines)

async def main():
    data = await get_streams()

    print("🔍 Available categories from API:")
    for category in data.get("streams", []):
        print(f" - {category.get('category')}")

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
        print("❌ No streams found in allowed categories.")
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

if __name__ == "__main__":
    asyncio.run(main())
