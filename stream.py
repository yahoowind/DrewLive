import asyncio
import json
from playwright.async_api import async_playwright, Request

BASE_URL = "https://www.streameast.xyz"

CATEGORY_LOGOS = {
    "StreamEast - PPV Events": "http://drewlive24.duckdns.org:9000/Logos/PPV.png",
    "StreamEast - Soccer": "http://drewlive24.duckdns.org:9000/Logos/Football2.png",
    "StreamEast - F1": "http://drewlive24.duckdns.org:9000/Logos/F1.png",
    "StreamEast - Boxing": "http://drewlive24.duckdns.org:9000/Logos/Boxing-2.png",
    "StreamEast - MMA": "http://drewlive24.duckdns.org:9000/Logos/MMA.png",
    "StreamEast - WWE": "http://drewlive24.duckdns.org:9000/Logos/WWE.png",
    "StreamEast - Golf": "http://drewlive24.duckdns.org:9000/Logos/Golf.png",
    "StreamEast - Am. Football": "http://drewlive24.duckdns.org:9000/Logos/Am-Football.png",
    "StreamEast - Baseball": "http://drewlive24.duckdns.org:9000/Logos/MLB.png",
    "StreamEast - Basketball Hub": "http://drewlive24.duckdns.org:9000/Logos/Basketball5.png",
    "StreamEast - Hockey": "http://drewlive24.duckdns.org:9000/Logos/Hockey.png",
    "StreamEast - WNBA": "http://drewlive24.duckdns.org:9000/Logos/WNBA.png",
}

CATEGORY_TVG_IDS = {
    "StreamEast - PPV Events": "PPV.EVENTS.Dummy.us",
    "StreamEast - Soccer": "Soccer.Dummy.us",
    "StreamEast - F1": "Racing.Dummy.us",
    "StreamEast - Boxing": "Boxing.Dummy.us",
    "StreamEast - MMA": "UFC.Fight.Pass.Dummy.us",
    "StreamEast - WWE": "PPV.EVENTS.Dummy.us",
    "StreamEast - Golf": "Golf.Dummy.us",
    "StreamEast - Am. Football": "Football.Dummy.us",
    "StreamEast - Baseball": "MLB.Baseball.Dummy.us",
    "StreamEast - Basketball Hub": "Basketball.Dummy.us",
    "StreamEast - Hockey": "NHL.Hockey.Dummy.us",
    "StreamEast - WNBA": "WNBA.Basketball.Dummy.us",
}

def categorize_stream(url, title=""):
    lowered = (url + " " + title).lower()
    if "wnba" in lowered or "women's basketball" in lowered:
        return "StreamEast - WNBA"
    if "nba" in lowered or "basketball" in lowered:
        return "StreamEast - Basketball Hub"
    if "nfl" in lowered or "football" in lowered:
        return "StreamEast - Am. Football"
    if "mlb" in lowered or "baseball" in lowered:
        return "StreamEast - Baseball"
    if "ufc" in lowered or "mma" in lowered:
        return "StreamEast - MMA"
    if "wwe" in lowered or "wrestling" in lowered:
        return "StreamEast - WWE"
    if "boxing" in lowered:
        return "StreamEast - Boxing"
    if "soccer" in lowered or "futbol" in lowered:
        return "StreamEast - Soccer"
    if "golf" in lowered:
        return "StreamEast - Golf"
    if "hockey" in lowered or "nhl" in lowered:
        return "StreamEast - Hockey"
    if "f1" in lowered or "motorsport" in lowered or "nascar" in lowered:
        return "StreamEast - F1"
    return "StreamEast - PPV Events"


async def safe_goto(page, url, tries=3):
    for attempt in range(tries):
        try:
            print(f"🌐 Attempt {attempt+1} loading {url}")
            await page.goto(url, timeout=60000)
            html = await page.content()
            if "cloudflare" in html.lower() or "just a moment" in html.lower() or "attention required" in html.lower():
                print("🚨 Block or challenge detected, retrying after delay...")
                await asyncio.sleep(5)
                continue
            return True
        except Exception as e:
            print(f"⚠️ Error loading page (try {attempt+1}): {e}")
            await asyncio.sleep(5)
    print(f"❌ Failed to load page after {tries} tries: {url}")
    return False


async def get_event_links(page):
    print("🌐 Navigating to the main page to collect event links...")
    success = await safe_goto(page, BASE_URL)
    if not success:
        return []

    await asyncio.sleep(3)
    links = await page.evaluate("""() => Array.from(document.querySelectorAll('a'))
        .map(a => a.href)
        .filter(h =>
            h.includes('/nba') ||
            h.includes('/mlb') ||
            h.includes('/ufc') ||
            h.includes('/f1') ||
            h.includes('/soccer') ||
            h.includes('/wnba') ||
            h.includes('/boxing') ||
            h.includes('/wwe')
        )
    """)
    unique_links = list(set(links))
    print(f"📥 Collected {len(unique_links)} unique event links.")
    return unique_links


async def click_center_once(page):
    box = await page.evaluate_handle("document.body.getBoundingClientRect()")
    dimensions = await box.json_value()
    x = int(dimensions['width'] // 2)
    y = int(dimensions['height'] // 2)
    print(f"🖱️ Clicking center at ({x},{y})")
    await page.mouse.click(x, y)
    await asyncio.sleep(1.5)


async def fetch_v90_streams(context, sport):
    api_url = f"https://the.streameast.app/v90/{sport}/streams4"
    print(f"🔗 Fetching v90 API streams from: {api_url}")
    page = await context.new_page()
    m3u8_links = set()
    try:
        success = await safe_goto(page, api_url)
        if not success:
            return []
        text = await (await page.wait_for_response(api_url, timeout=30000)).text()
        data = json.loads(text)

        for stream in data.get("streams", []):
            url = stream.get("url")
            if url and url.endswith(".m3u8"):
                m3u8_links.add(url)
        print(f"✅ Found {len(m3u8_links)} streams from v90 API.")
    except Exception as e:
        print(f"⚠️ Error fetching v90 streams API: {e}")
    finally:
        await page.close()

    return list(m3u8_links)


async def scrape_stream_url(context, url):
    m3u8_links = set()
    event_name = "Unknown Event"

    if "the.streameast.app/v90" in url:
        parts = url.split('/')
        try:
            sport_index = parts.index("v90") + 1
            sport = parts[sport_index]
        except Exception:
            sport = None

        if sport:
            streams = await fetch_v90_streams(context, sport)
            event_name = sport.upper() + " Group Streams"
            return event_name, streams

    page = await context.new_page()

    def capture_request(request: Request):
        if ".m3u8" in request.url.lower() and len(m3u8_links) == 0:
            print(f"🎯 Captured .m3u8 URL: {request.url}")
            m3u8_links.add(request.url)

    page.on("request", capture_request)

    try:
        print(f"\n🔍 Scraping event page: {url}")
        success = await safe_goto(page, url)
        if not success:
            return event_name, []

        await asyncio.sleep(3)

        event_name = await page.evaluate(r"""
            () => {
                const selectors = [
                    'h1', '.event-title', '.title', '.stream-title',
                    '.stream-header', '.match-title', '.game-title'
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.textContent.trim().length > 0) {
                        return el.textContent.trim();
                    }
                }
                try {
                    const parts = window.location.pathname.split('/').filter(Boolean);
                    if (parts.length > 1) {
                        let lastSeg = decodeURIComponent(parts[parts.length - 1]);
                        lastSeg = lastSeg.replace(/[-_]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                        return lastSeg;
                    }
                } catch {}
                return document.title.trim();
            }
        """)

        print(f"📛 Event name: {event_name}")
        print("🖱️ Clicking center of page once to trigger streams...")
        await click_center_once(page)

        for _ in range(12):
            if m3u8_links:
                print("⏩ Stream found, moving on early...")
                break
            await asyncio.sleep(0.5)
        else:
            print("⚠️ No streams detected after wait, clicking once more...")
            await click_center_once(page)
            for _ in range(6):
                if m3u8_links:
                    print("⏩ Stream found after second click.")
                    break
                await asyncio.sleep(0.5)

    except Exception as e:
        print(f"⚠️ Error scraping event page: {e}")

    finally:
        await page.close()

    return event_name, list(m3u8_links)


async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            locale="en-US"
        )

        page = await context.new_page()
        event_links = await get_event_links(page)
        await page.close()

        with open("StreamEast.m3u8", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            total = len(event_links)
            for idx, link in enumerate(event_links, 1):
                print(f"\n➡️ [{idx}/{total}] Processing: {link}")
                event_name, streams = await scrape_stream_url(context, link)
                category = categorize_stream(link, event_name)
                logo = CATEGORY_LOGOS.get(category, "")
                tvg_id = CATEGORY_TVG_IDS.get(category, "")
                group = category

                for stream_url in streams:
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{event_name}\n')
                    f.write('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0\n')
                    f.write('#EXTVLCOPT:http-origin=https://streamscenter.online\n')
                    f.write('#EXTVLCOPT:http-referrer=https://streamscenter.online/\n')
                    f.write(f'{stream_url}\n\n')

                await asyncio.sleep(3)  # Small delay between processing links to reduce rate limiting

        print("\n✅ StreamEast.m3u8 saved with all streams.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
