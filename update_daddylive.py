import asyncio
from playwright.async_api import async_playwright, Request
import os
import random

CHANNELS_TO_PROCESS = {
    "NBC10 Philadelphia": "277", "TNT Sports 1 UK": "31", "Discovery Channel": "313",
    "Discovery Life Channel": "311", "Disney Channel": "312", "Disney XD": "314",
    "E! Entertainment": "315", "ESPN Deportes": "375", "ESPN USA": "44",
    "ESPN2 USA": "45", "ESPNews": "288", "ESPNU USA": "316", "Fox Business": "297",
    "Fox News": "347", "Fox Sports 1": "39", "FOX USA": "54", "Freeform": "301",
    "FUSE TV USA": "279", "FX Movie Channel": "381", "FX USA": "317",
    "FXX USA": "298", "Game Show Network": "319", "GOLF Channel USA": "318",
    "Hallmark Movies & Mysteries": "296", "HBO USA": "321", "Headline News": "323",
    "HGTV": "382", "History USA": "322", "Investigation Discovery (ID USA)": "324",
    "ION USA": "325", "Law & Crime Network": "278", "HFTN": "531",
    "Lifetime Movies Network": "389", "Lifetime Network": "326", "Magnolia Network": "299",
    "MSNBC": "327", "MTV USA": "371", "National Geographic (NGC)": "328",
    "NBC Sports Philadelphia": "777", "NBC USA": "53", "NewsNation USA": "292",
    "NICK": "330", "NICK JR": "329", "Oprah Winfrey Network (OWN)": "331",
    "Oxygen True Crime": "332", "Pac-12 Network USA": "287",
    "Paramount Network": "334", "Reelz Channel": "293", "Science Channel": "294",
    "SEC Network USA": "385", "Comedy Central": "310", "Cleo TV": "715",
}

OUTPUT_FILE = "DaddyLive.m3u8"

def build_header(channel_name):
    return f'#EXTINF:-1 tvg-id="{channel_name}" tvg-name="{channel_name}" tvg-logo="https://logo.clearbit.com/{channel_name.replace(" ", "").lower()}.com" group-title="USA",{channel_name}'

async def fetch_m3u8_links():
    urls_all = {}

    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for name, cid in CHANNELS_TO_PROCESS.items():
            stream_urls = []

            def capture_m3u8(request: Request):
                if ".m3u8" in request.url.lower():
                    stream_urls.append(request.url)

            page.on("request", capture_m3u8)

            try:
                print(f"🔄 Scraping {name}...")
                await page.goto(f"https://thedaddy.click/stream/stream-{cid}.php", timeout=60000)
                await asyncio.sleep(10)
                await page.screenshot(path=f"screenshots/{name.replace(' ', '_')}.png")
            except Exception as e:
                print(f"❌ Error with {name}: {e}")

            page.remove_listener("request", capture_m3u8)

            if stream_urls:
                urls_all[name] = random.choice(stream_urls)
                print(f"✅ Got URL for {name}")
            else:
                print(f"⚠️ No stream found for {name}")

        await browser.close()

    return urls_all

def write_playlist(urls):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, url in urls.items():
            f.write(build_header(name) + "\n")
            f.write(url + "\n")
    print(f"✅ Final playlist written to {OUTPUT_FILE}")

async def main():
    fresh_urls = await fetch_m3u8_links()
    write_playlist(fresh_urls)

if __name__ == "__main__":
    asyncio.run(main())
