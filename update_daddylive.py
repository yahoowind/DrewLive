import asyncio
from playwright.async_api import async_playwright, Request
import os
import random
import re

INPUT_FILE = "DaddyLive.m3u8"
OUTPUT_FILE = "DaddyLive.m3u8"

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

def parse_m3u_playlist(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]

    entries = []
    meta = None
    for line in lines:
        if line.startswith("#EXTINF:"):
            meta = line
        elif meta and line and not line.startswith("#"):
            entries.append({"meta": meta, "url": line})
            meta = None
    return entries

def extract_channel_name(meta_line):
    match = re.search(r",(.+)$", meta_line)
    return match.group(1).strip() if match else None

async def fetch_updated_urls():
    urls = {}
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for name, cid in CHANNELS_TO_PROCESS.items():
            stream_urls = []

            def capture_m3u8(request: Request):
if ".m3u8" in request.url.lower():
            print(f"🔍 Detected m3u8 stream: {request.url}")
            stream_urls.append(request.url)
        
            page.on("request", capture_m3u8)

            try:
                print(f"🔄 Scraping {name}...")
                await page.goto(f"https://thedaddy.click/stream/stream-{cid}.php", timeout=60000)
                await asyncio.sleep(10)
            except Exception as e:
                print(f"❌ Failed for {name}: {e}")

            page.remove_listener("request", capture_m3u8)

            if stream_urls:
                urls[name] = random.choice(stream_urls)
                print(f"✅ Got stream for {name}")
            else:
                print(f"⚠️ No streams found for {name}")

        await browser.close()
    return urls

def update_playlist(entries, new_urls):
    for entry in entries:
        name = extract_channel_name(entry["meta"])
        if name in new_urls:
            print(f"🔁 Replacing URL for {name}")
            entry["url"] = new_urls[name]
    return entries

def save_playlist(entries, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for entry in entries:
            f.write(entry["meta"] + "\n")
            f.write(entry["url"] + "\n")
    print(f"✅ Updated playlist saved to {filepath}")

async def main():
    entries = parse_m3u_playlist(INPUT_FILE)
    new_urls = await fetch_updated_urls()
    updated_entries = update_playlist(entries, new_urls)
    save_playlist(updated_entries, OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(main())
