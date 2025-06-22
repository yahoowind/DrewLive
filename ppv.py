import asyncio
import os
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
        # Debug log to track URLs seen in CI
        if os.getenv("GITHUB_ACTIONS") == "true":
            print(f"🛰️ Saw URL: {url} - Status: {response.status}")
        if not found_stream and ".m3u8" in url and response.status == 200:
            found_stream = url
            print(f"🎥 First valid stream URL: {url}")

    page.on("response", handle_response)

    print(f"🌐 Navigating to iframe: {iframe_url}")
    await page.goto(iframe_url)
    await page.wait_for_load_state('networkidle')  # Wait for full network idle

    # Try clicking inside iframe if possible
    try:
        frame = page.frame(url=iframe_url)
        if frame:
            await frame.click("body", position={"x": 50, "y": 50})
    except Exception:
        # Fallback to clicking center of page
        viewport = page.viewport_size or {"width": 1280, "height": 720}
        center_x = viewport["width"] / 2
        center_y = viewport["height"] / 2
        print("🖱️ Aggressive clicking center to trigger play...")
        for i in range(10):
            if found_stream:
                break
            print(f"Click #{i+1}")
            await page.mouse.click(center_x, center_y)
            await asyncio.sleep(0.2)

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
        # Use chromium in GitHub Actions for better compatibility
        browser_type = p.chromium if os.getenv("GITHUB_ACTIONS") == "true" else p.firefox
        browser = await browser_type.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        url_map = {}
        MAX_RETRIES = 3 if os.getenv("GITHUB_ACTIONS") == "true" else 1

        for s in streams:
            for attempt in range(MAX_RETRIES):
                print(f"\n🌐 Loading stream: {s['name']} (Attempt {attempt + 1})")
                found_urls = await grab_m3u8_from_iframe(page, s["iframe"])
                if found_urls:
                    url_map[s["name"]] = found_urls
                    break

        await browser.close()

    print("\n📝 Writing to PPVLand.m3u8 ...")
    playlist = build_m3u(streams, url_map)
    with open("PPVLand.m3u8", "w", encoding="utf-8") as f:
        f.write(playlist)

    print("✅ Done! Playlist saved to PPVLand.m3u8")

if __name__ == "__main__":
    asyncio.run(main())
