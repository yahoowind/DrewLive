import asyncio
from playwright.async_api import async_playwright, Request
import random
import re
import os
import sys

INPUT_FILE = "DaddyLive.m3u8"
OUTPUT_FILE = "DaddyLive.m3u8"
DRY_RUN = "--dry-run" in sys.argv

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

VLC_OPT_LINES = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]


def parse_m3u_playlist(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    entries = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTM3U"):
            entries.append({"meta": '#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"', "headers": [], "url": None})
            i += 1
        elif line.startswith("#EXTINF:"):
            meta = line
            headers = []
            i += 1
            while i < len(lines) and lines[i].startswith("#EXTVLCOPT"):
                headers.append(lines[i])
                i += 1
            url = lines[i] if i < len(lines) else ""
            entries.append({"meta": meta, "headers": headers, "url": url})
            i += 1
        else:
            i += 1
    return entries


def extract_channel_name(meta_line):
    match = re.search(r'tvg-name="([^"]+)"', meta_line)
    if match:
        return match.group(1).strip()
    comma = meta_line.rfind(",")
    return meta_line[comma + 1:].strip() if comma != -1 else None


async def scrape_channel(context, name, cid):
    page = await context.new_page()
    stream_urls = []

    def capture_m3u8(request: Request):
        if ".m3u8" in request.url.lower():
            stream_urls.append(request.url)

    page.on("request", capture_m3u8)

    try:
        await page.goto(f"https://thedaddy.click/stream/stream-{cid}.php", timeout=60000)
        for _ in range(3):
            if stream_urls:
                break
            await asyncio.sleep(5)
    except Exception as e:
        print(f"❌ {name}: {e}")
    finally:
        page.off("request", capture_m3u8)
        await page.close()

    return (name, random.choice(stream_urls)) if stream_urls else (name, None)


async def fetch_updated_urls():
    urls = {}
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        print("\n🌐 Scraping stream URLs...")
        tasks = [scrape_channel(context, name, cid) for name, cid in CHANNELS_TO_PROCESS.items()]
        results = await asyncio.gather(*tasks)

        for name, url in results:
            if url:
                urls[name] = url
                print(f"✅ {name}")
            else:
                print(f"⚠️ No stream found for {name}")

        await browser.close()
    return urls


def update_playlist(entries, new_urls):
    updated_entries = []

    for entry in entries:
        if entry["meta"].startswith("#EXTM3U"):
            updated_entries.append(entry)
            continue

        name = extract_channel_name(entry["meta"])
        if name in new_urls:
            print(f"🔁 Updating: {name}")
            updated_entries.append({
                "meta": entry["meta"],
                "headers": VLC_OPT_LINES,
                "url": new_urls[name]
            })
        else:
            updated_entries.append(entry)
    return updated_entries


def save_playlist(entries, filepath):
    if DRY_RUN:
        print("\n🚫 Dry run mode enabled. No file saved.")
        return

    with open(filepath, "w", encoding="utf-8") as f:
        for entry in entries:
            if entry["meta"]:
                f.write(entry["meta"] + "\n")
            if "headers" in entry:
                for h in entry["headers"]:
                    f.write(h + "\n")
            if entry["url"]:
                f.write(entry["url"] + "\n")
    print(f"\n✅ Playlist saved to {filepath}")


async def main():
    print("📥 Loading existing playlist...")
    entries = parse_m3u_playlist(INPUT_FILE)

    new_urls = await fetch_updated_urls()

    print("\n🛠️ Rebuilding playlist...")
    updated_entries = update_playlist(entries, new_urls)

    save_playlist(updated_entries, OUTPUT_FILE)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Aborted by user.")
