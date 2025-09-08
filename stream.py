import asyncio
from playwright.async_api import async_playwright, Request

# Main domain
BASE_URL = "https://www.streameast.xyz"

# Mirrors (for reference, not used automatically)
MIRROR_DOMAINS = [
    "https://streameast.ga",
    "https://streameast.tw",
    "https://streameast.ph",
    "https://streameast.sg",
    "https://streameast.ch",
    "https://streameast.ec",
    "https://streameast.fi",
    "https://streameast.ms",
    "https://streameast.ps",
    "https://streameast.cf",
    "https://streameast.sk",
    "https://thestreameast.co",
    "https://thestreameast.fun",
    "https://thestreameast.ru",
    "https://thestreameast.su"
]

M3U8_FILE = "StreamEast.m3u8"

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

HEADERS_FOR_VLC = [
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0',
    '#EXTVLCOPT:http-origin=https://embedsports.top',
    '#EXTVLCOPT:http-referrer=https://embedsports.top/'
]

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
    for _ in range(tries):
        try:
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            html = await page.content()
            if any(x in html.lower() for x in ["cloudflare", "just a moment", "attention required"]):
                await asyncio.sleep(2)
                continue
            return True
        except:
            await asyncio.sleep(2)
    return False

async def get_event_links(page):
    print("🌐 Gathering event links...")
    if not await safe_goto(page, BASE_URL):
        return []

    links = await page.evaluate("""() => Array.from(document.querySelectorAll('a'))
        .map(a => a.href)
        .filter(h => ['/cfb','/nba','/mlb','/ufc','/f1','/soccer','/wnba','/boxing','/wwe','/nfl'].some(x => h.includes(x)))""")
    return list(set(links))

async def scrape_stream_url(context, url):
    m3u8_links = []
    event_name = "Unknown Event"
    page = await context.new_page()

    def capture_request(request: Request):
        if ".m3u8" in request.url.lower() and request.url not in m3u8_links:
            m3u8_links.append(request.url)
            print(f"🎯 Found stream: {request.url}")

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

        await page.mouse.click(200, 200)
        await asyncio.sleep(1)
        for i in range(0, 1800, 400):
            await page.evaluate(f"window.scrollTo(0, {i})")
            await asyncio.sleep(0.5)
        await asyncio.sleep(5)

    finally:
        await page.close()

    return event_name, m3u8_links[:1]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/142.0",
            viewport={"width": 1366, "height": 768},
            java_script_enabled=True,
            ignore_https_errors=True
        )

        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        main_page = await context.new_page()
        links = await get_event_links(main_page)
        await main_page.close()

        with open(M3U8_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            for idx, link in enumerate(links, 1):
                print(f"\n➡️ [{idx}/{len(links)}] {link}")
                name, streams = await scrape_stream_url(context, link)
                if not streams:
                    continue

                s_url = streams[0]
                category = categorize_stream(link, name)
                logo = CATEGORY_LOGOS.get(category, "")
                tvg_id = CATEGORY_TVG_IDS.get(category, "")
                safe_name = name.replace(",", " -")

                extinf = f'#EXTINF:-1'
                if tvg_id: extinf += f' tvg-id="{tvg_id}"'
                if logo: extinf += f' tvg-logo="{logo}"'
                extinf += f' group-title="{category}",{safe_name}'

                f.write(f"{extinf}\n")
                for header in HEADERS_FOR_VLC:
                    f.write(f"{header}\n")
                f.write(f"{s_url}\n\n")

        print(f"✅ {M3U8_FILE} saved.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
