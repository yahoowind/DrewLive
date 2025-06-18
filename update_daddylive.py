import asyncio
from playwright.async_api import async_playwright, Request
import os
import subprocess
import random
import re
import requests

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

UPSTREAM_PLAYLIST_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

def parse_m3u_playlist(content):
    """Parse m3u playlist content into list of entries with metadata and url."""
    lines = content.strip().splitlines()
    entries = []
    current_meta = None

    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            current_meta = line
        elif line and not line.startswith("#"):
            if current_meta:
                entries.append({"meta": current_meta, "url": line})
                current_meta = None
            else:
                # In case there's URL without preceding meta (rare)
                entries.append({"meta": None, "url": line})
    return entries

def serialize_m3u_playlist(entries):
    """Convert list of entries back into m3u playlist text."""
    lines = ["#EXTM3U"]
    for e in entries:
        if e["meta"]:
            lines.append(e["meta"])
        lines.append(e["url"])
    return "\n".join(lines) + "\n"

async def fetch_m3u8_links():
    urls_all = {}

    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for name, cid in CHANNELS_TO_PROCESS.items():
            channel_urls = []

            def capture_m3u8(request: Request):
                url_lower = request.url.lower()
                if ".m3u8" in url_lower:
                    print(f"🔍 Detected m3u8 request on {name}: {request.url}")
                    channel_urls.append(request.url)

            page.on("request", capture_m3u8)

            try:
                print(f"🔄 Loading {name}...")
                await page.goto(f"https://thedaddy.click/stream/stream-{cid}.php", timeout=60000)
                await asyncio.sleep(10)  # wait to capture m3u8 requests

                screenshot_path = f"screenshots/{name.replace(' ', '_')}.png"
                await page.screenshot(path=screenshot_path)

            except Exception as e:
                print(f"❌ Failed for {name}: {e}")

            page.off("request", capture_m3u8)

            if channel_urls:
                chosen_url = random.choice(channel_urls)
                urls_all[name] = chosen_url
                print(f"🎯 Picked URL for {name}: {chosen_url}")
            else:
                print(f"⚠️ No URLs found for {name}")

        await browser.close()

    print("\n🔔 Final summary of picked streams:")
    for name, url in urls_all.items():
        print(f"{name}: {url}")

    return urls_all

def merge_playlists(upstream_entries, fresh_urls):
    """
    Replace URLs in upstream playlist entries matching fresh_urls by channel name.
    Add new entries if fresh_urls have channels not in upstream.
    """

    # Helper to extract channel name from #EXTINF meta line
    def extract_name(meta_line):
        # #EXTINF:-1 tvg-id="XXX" tvg-logo="YYY" group-title="ZZZ",Channel Name
        match = re.search(r",(.+)$", meta_line)
        if match:
            return match.group(1).strip()
        return None

    updated_names = set()
    new_entries = []

    # Replace URLs for channels found fresh
    for entry in upstream_entries:
        name = extract_name(entry["meta"])
        if name and name in fresh_urls:
            old_url = entry["url"]
            new_url = fresh_urls[name]
            if old_url != new_url:
                print(f"🔄 Updating URL for {name}")
                entry["url"] = new_url
            updated_names.add(name)

    # Add any fresh channels not in upstream
    for name, url in fresh_urls.items():
        if name not in updated_names:
            # Create minimal meta line - you can customize if you want
            meta = f'#EXTINF:-1,{name}'
            new_entries.append({"meta": meta, "url": url})
            print(f"➕ Adding new channel {name}")

    return upstream_entries + new_entries

def git_push():
    try:
        subprocess.run(["git", "add", OUTPUT_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Auto update DaddyLive playlist"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Playlist updated and pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")

async def main():
    print("⬇️ Downloading upstream playlist...")
    resp = requests.get(UPSTREAM_PLAYLIST_URL)
    resp.raise_for_status()
    upstream_content = resp.text

    upstream_entries = parse_m3u_playlist(upstream_content)
    print(f"ℹ️ Parsed {len(upstream_entries)} entries from upstream playlist")

    fresh_urls = await fetch_m3u8_links()

    merged_entries = merge_playlists(upstream_entries, fresh_urls)

    final_content = serialize_m3u_playlist(merged_entries)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_content)
    print(f"✅ Saved merged playlist to {OUTPUT_FILE}")

    git_push()

if __name__ == "__main__":
    asyncio.run(main())
