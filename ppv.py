import asyncio
from playwright.async_api import async_playwright, Request
import random
import re

API_URL = "https://ppv.to/api/streams"
OUTPUT_FILE = "PPVLand.m3u8"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "application/json",
    "Referer": "https://ppv.to/",
}

CUSTOM_LOGO = "https://tinyurl.com/drewsportslogo"
CUSTOM_ID = "Sports.Dummy.us"
CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0'
]

ALLOWED_CATEGORIES = {"24/7 Streams", "Wrestling", "Football", "Basketball", "Baseball"}

def build_m3u(entries, url_map):
    lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    for entry in entries:
        title = entry["title"]
        cid = entry["channel_id"]
        url = url_map.get(cid, "#")
        tvg_id = CUSTOM_ID
        logo_url = CUSTOM_LOGO
        group_title = entry.get("category", "Live Events")

        lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo_url}" group-title="{group_title}",{title}')
        lines.extend(CUSTOM_HEADERS)
        lines.append(url)
    return "\n".join(lines)

async def extract_from_iframe(context, iframe_src):
    page = await context.new_page()
    m3u8_links = []

    def capture(request: Request):
        url = request.url.lower()
        if ".m3u8" in url:
            print(f"🎯 Found iframe .m3u8 URL: {url}")
            m3u8_links.append(url)

    page.on("request", capture)
    try:
        await page.goto(iframe_src, timeout=30000)
        await asyncio.sleep(5)
        content = await page.content()
        if not m3u8_links:
            found = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', content)
            m3u8_links.extend(found)
    except Exception as e:
        print(f"❌ Error loading iframe: {e}")
    finally:
        await page.close()

    return m3u8_links

async def scrape_streams(entries):
    url_map = {}
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for entry in entries:
            cid = entry["channel_id"]
            if cid in url_map:
                continue

            m3u8_links = []

            def capture(request: Request):
                url = request.url.lower()
                if ".m3u8" in url:
                    print(f"🎯 Found direct .m3u8 URL: {url}")
                    m3u8_links.append(url)

            page.on("request", capture)
            try:
                print(f"\n🔄 Scraping: {entry['title']} (CID: {cid})")
                stream_url = f"https://ppv.to/live/{entry['uri_name']}"
                await page.goto(stream_url, timeout=60000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(4)

                try:
                    await page.click("button.play, div.play-button, .btn-play", timeout=3000)
                    print("👆 Clicked play button")
                    await asyncio.sleep(5)
                except:
                    pass

                # Iframe fallback logic
                if not m3u8_links:
                    iframe = await page.query_selector("iframe#player")
                    if iframe:
                        iframe_src = await iframe.get_attribute("src")
                        if iframe_src:
                            print(f"🔎 Found iframe: {iframe_src}")
                            m3u8_links = await extract_from_iframe(context, iframe_src)

                # Page HTML fallback
                if not m3u8_links:
                    html = await page.content()
                    found = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
                    if found:
                        print(f"🔍 Found .m3u8 in HTML fallback")
                        m3u8_links.extend(found)

            except Exception as e:
                print(f"❌ Error scraping CID {cid}: {e}")

            page.remove_listener("request", capture)
            url_map[cid] = random.choice(m3u8_links) if m3u8_links else "#"
            print(f"{'✅' if m3u8_links else '⚠️'} Final stream: {url_map[cid]}")

        await browser.close()
    return url_map

async def fetch_schedule(page):
    try:
        res = await page.request.get(API_URL, headers=HEADERS)
        if not res.ok:
            print(f"❌ API error: {res.status}")
            return []

        data = await res.json()
    except Exception as e:
        print(f"❌ Exception fetching schedule: {e}")
        return []

    entries = []
    for cat in data.get("streams", []):
        category = cat.get("category", "")
        if category not in ALLOWED_CATEGORIES:
            continue
        for stream in cat.get("streams", []):
            title = stream.get("name", "").strip()
            cid = str(stream.get("id", "")).strip()
            uri = stream.get("uri_name", "").strip()
            if title and cid and uri:
                entries.append({
                    "title": title,
                    "channel_id": cid,
                    "uri_name": uri,
                    "category": category
                })

    return entries

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        entries = await fetch_schedule(page)
        await browser.close()

    if not entries:
        print("⚠️ No valid entries found.")
        return

    print(f"\n📺 Scraping {len(entries)} events...")
    url_map = await scrape_streams(entries)

    print("💾 Writing M3U...")
    m3u = build_m3u(entries, url_map)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u)

    print(f"✅ Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
