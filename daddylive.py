import asyncio
import requests
from playwright.async_api import async_playwright, Request

SCHEDULE_JSON_URL = "https://thedaddy.click/24.7channels.php"
RAW_PLAYLIST = "DaddyLiveRAW.m3u8"
FINAL_PLAYLIST = "DaddyLive.m3u8"
PROXY_BASE_URL = "https://tinyurl.com/DrewProxy224"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Referer": "https://thedaddy.click/"
}

def fetch_schedule():
    print("📡 Fetching schedule JSON...")
    resp = requests.get(SCHEDULE_JSON_URL, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    entries = []
    for entry in data:
        cid = str(entry.get("id", "")).strip()
        title = entry.get("title", "").strip()
        if cid and title:
            entries.append({"channel_id": cid, "title": title})
    return entries

async def scrape_and_handshake(entries):
    playlist_lines = ["#EXTM3U"]
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for entry in entries:
            cid = entry["channel_id"]
            title = entry["title"]
            m3u8_links = set()

            def capture(request: Request):
                if ".m3u8" in request.url.lower():
                    m3u8_links.add(request.url)

            page.on("request", capture)

            try:
                url = f"https://thedaddy.click/cast/stream-{cid}.php"
                print(f"\n🔄 Scraping: {title} (CID: {cid}) -> {url}")
                await page.goto(url, timeout=20000)

                tries = 0
                while not m3u8_links and tries < 3:
                    await asyncio.sleep(4)
                    tries += 1
                    print(f"⏳ Waiting for stream ({tries}/3)...")

            except Exception as e:
                print(f"❌ Failed to load {title}: {e}")

            page.remove_listener("request", capture)

            if m3u8_links:
                stream_url = sorted(m3u8_links)[0]
                print(f"✅ Found stream: {stream_url}")

                # Handshake via proxy
                proxy_url = f"{PROXY_BASE_URL}?stream={stream_url}"
                try:
                    await page.goto(proxy_url, timeout=15000)
                    await asyncio.sleep(2)
                except:
                    print(f"⚠️ Handshake fail: {proxy_url}")

                playlist_lines.append(f"#EXTINF:-1,{title}")
                playlist_lines.append(stream_url)
            else:
                print(f"⚠️ No stream found for {title}")

        await browser.close()

    return playlist_lines

def write_playlist(filename, lines):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"💾 Saved to {filename}")

def main():
    entries = fetch_schedule()
    if not entries:
        print("❌ No entries found in schedule.")
        return

    lines = asyncio.run(scrape_and_handshake(entries))
    write_playlist(RAW_PLAYLIST, lines)
    write_playlist(FINAL_PLAYLIST, lines)

if __name__ == "__main__":
    main()
