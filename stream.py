import asyncio
from datetime import datetime
from playwright.async_api import async_playwright, Request

BASE_URL = "https://www.streameast.xyz"
M3U8_FILE = "StreamEast.m3u8"

STREAM_DOMAINS = [
    "streameast.sk", "streameast.ch", "streameast.ec",
    "streameast.fi", "streameast.ms", "streameast.ps",
    "streameast.ph", "streameast.sg", "thestreameast.ru",
    "thestreameast.st", "thestreameast.su", "zd.strmd.top"
]

CATEGORY_LOGOS = {
    "StreamEast - PPV Events": "http://drewlive24.duckdns.org:9000/Logos/PPV.png",
    "StreamEast - Soccer": "http://drewlive24.duckdns.org:9000/Logos/Football2.png",
    "StreamEast - F1": "http://drewlive24.duckdns.org:9000/Logos/F1.png",
    "StreamEast - Boxing": "http://drewlive24.duckdns.org:9000/Logos/Boxing-2.png",
    "StreamEast - MMA": "http://drewlive24.duckdns.org:9000/Logos/MMA.png",
    "StreamEast - WWE": "http://drewlive24.duckdns.org:9000/Logos/WWE.png",
    "StreamEast - Golf": "http://drewlive24.duckdns.org:9000/Logos/Golf.png",
    "StreamEast - Am. Football": "http://drewlive24.duckdns.org:9000/Logos/NFL4.png",
    "StreamEast - College Football": "http://drewlive24.duckdns.org:9000/Logos/CFB3.png",
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
    "StreamEast - Am. Football": "NFL.Dummy.us",
    "StreamEast - College Football": "NCAA.Football.Dummy.us",
    "StreamEast - Baseball": "MLB.Baseball.Dummy.us",
    "StreamEast - Basketball Hub": "Basketball.Dummy.us",
    "StreamEast - Hockey": "NHL.Hockey.Dummy.us",
    "StreamEast - WNBA": "WNBA.dummy.us",
}

def categorize_stream(url, title=""):
    lowered = (url + " " + title).lower()
    if "wnba" in lowered: return "StreamEast - WNBA"
    if "nba" in lowered or "basketball" in lowered: return "StreamEast - Basketball Hub"
    if "nfl" in lowered or "pro football" in lowered: return "StreamEast - Am. Football"
    if "cfb" in lowered or "college" in lowered or "ncaa" in lowered: return "StreamEast - College Football"
    if "mlb" in lowered or "baseball" in lowered: return "StreamEast - Baseball"
    if "ufc" in lowered or "mma" in lowered: return "StreamEast - MMA"
    if "wwe" in lowered or "wrestling" in lowered: return "StreamEast - WWE"
    if "boxing" in lowered: return "StreamEast - Boxing"
    if "soccer" in lowered or "futbol" in lowered: return "StreamEast - Soccer"
    if "golf" in lowered: return "StreamEast - Golf"
    if "hockey" in lowered or "nhl" in lowered: return "StreamEast - Hockey"
    if "f1" in lowered or "nascar" in lowered or "motorsport" in lowered: return "StreamEast - F1"
    return "StreamEast - PPV Events"

async def safe_goto(page, url, tries=3, timeout=20000):
    for attempt in range(tries):
        try:
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            html = await page.content()
            if any(x in html.lower() for x in ["cloudflare", "just a moment", "attention required"]):
                await asyncio.sleep(2)
                continue
            return True
        except Exception as e:
            print(f"⚠️ Error loading {url}: {e}")
            await asyncio.sleep(2)
    return False

async def get_event_links(page):
    if not await safe_goto(page, BASE_URL):
        return []
    links = await page.evaluate("""() => Array.from(document.querySelectorAll('a'))
        .map(a => a.href)
        .filter(h => h.includes('/cfb') || h.includes('/nba') || h.includes('/mlb') ||
                     h.includes('/ufc') || h.includes('/f1') || h.includes('/soccer') ||
                     h.includes('/wnba') || h.includes('/boxing') || h.includes('/wwe') || h.includes('/nfl'))""")
    return list(set(links))

async def scrape_stream_url(context, url):
    m3u8_links = []
    event_name = "Unknown Event"
    page = await context.new_page()

    def capture_request(request: Request):
        if ".m3u8" in request.url.lower() and any(d in request.url.lower() for d in STREAM_DOMAINS):
            if request.url not in m3u8_links:
                m3u8_links.append(request.url)

    page.on("request", capture_request)

    try:
        if not await safe_goto(page, url):
            return event_name, []
        try:
            await page.wait_for_selector("video, iframe", timeout=15000)
        except:
            pass
        event_name = await page.evaluate("""() => {
            const sel = ['h1', '.event-title', '.title', '.stream-title'];
            for (const s of sel) {
                const el = document.querySelector(s);
                if (el) return el.textContent.trim();
            }
            return document.title.trim();
        }""")
        await asyncio.sleep(6)  # wait for streams
    finally:
        await page.close()

    return event_name, m3u8_links[:3]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            viewport={"width": 1366, "height": 768},
            ignore_https_errors=True
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        main_page = await context.new_page()
        links = await get_event_links(main_page)
        await main_page.close()

        with open(M3U8_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# Updated at {datetime.utcnow().isoformat()}Z\n")

            for idx, link in enumerate(links, 1):
                name, streams = await scrape_stream_url(context, link)
                category = categorize_stream(link, name)
                logo = CATEGORY_LOGOS.get(category, "")
                tvg_id = CATEGORY_TVG_IDS.get(category, "")

                for s_url in streams:
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{category}",{name}\n')
                    f.write('#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0\n')
                    f.write('#EXTVLCOPT:http-origin=https://embedsports.top\n')
                    f.write('#EXTVLCOPT:http-referrer=https://embedsports.top/\n')
                    f.write(f'{s_url}\n')

        await browser.close()
        print("✅ StreamEast.m3u8 saved.")

if __name__ == "__main__":
    asyncio.run(main())
