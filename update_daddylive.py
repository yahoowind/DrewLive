import asyncio
from playwright.async_api import async_playwright, Request
import os
import subprocess
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
    "SEC Network USA": "385",
}

OUTPUT_FILE = "DaddyLive.m3u8"

async def fetch_m3u8_links():
    urls_all = {name: [] for name in CHANNELS_TO_PROCESS.keys()}

    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        async def capture_m3u8(request: Request):
            url_lower = request.url.lower()
            if ".m3u8" in url_lower:
                ref = request.headers.get("referer", "")
                print(f"🔍 Detected m3u8 request: {request.url} with referer: {ref}")
                for name, cid in CHANNELS_TO_PROCESS.items():
                    if f"stream-{cid}.php" in ref.lower():
                        urls_all[name].append(request.url)
                        print(f"➕ Collected {name} URL: {request.url}")

        page.on("request", capture_m3u8)

        for name, cid in CHANNELS_TO_PROCESS.items():
            try:
                print(f"🔄 Loading {name}...")
                await page.goto(f"https://thedaddy.click/stream/stream-{cid}.php", timeout=60000)
                await asyncio.sleep(5)  # wait for stream requests to start

                # wait a bit more to gather multiple URLs
                await asyncio.sleep(10)

                screenshot_path = f"screenshots/{name.replace(' ', '_')}.png"
                await page.screenshot(path=screenshot_path)
            except Exception as e:
                print(f"❌ Failed for {name}: {e}")

        await browser.close()

    # pick one random url per channel if any found
    urls = {}
    for name, url_list in urls_all.items():
        if url_list:
            chosen_url = random.choice(url_list)
            urls[name] = chosen_url
            print(f"🎯 Picked random URL for {name}: {chosen_url}")
        else:
            print(f"⚠️ No URLs found for {name}")

    return urls

def save_playlist(urls):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for name, url in urls.items():
            f.write(f"#EXTINF:-1,{name}\n")
            f.write(f"{url}\n")
    print(f"✅ Saved playlist to {OUTPUT_FILE}")

def git_push():
    try:
        subprocess.run(["git", "add", OUTPUT_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Auto update DaddyLive playlist"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Playlist updated and pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")

if __name__ == "__main__":
    urls = asyncio.run(fetch_m3u8_links())
    if urls:
        save_playlist(urls)
        git_push()
    else:
        print("⚠️ No streams found, skipping git push")
