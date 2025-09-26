import asyncio
import re
from urllib.parse import urljoin
from playwright.async_api import async_playwright, Page

NFL_BASE_URL = "https://nflwebcast.com/"
NFL_START_URLS = [
    NFL_BASE_URL,
    "http://nflwebcast.com/nflnetwork/",
    "https://nflwebcast.com/nflredzone/",
    "https://nflwebcast.com/espnusa/",
]
NFL_OUTPUT_FILE = "NFLWebcast.m3u8"

NHL_BASE_URL = "https://nhlwebcast.com/200"
NHL_OUTPUT_FILE = "NHLWebcast.m3u8"

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; "
              "rv:143.0) Gecko/20100101 Firefox/143.0")
POST_LOAD_WAIT_MS = 8000
STREAM_PATTERN = re.compile(r"\.m3u8($|\?)", re.I)

def normalize_name(original_name: str) -> str:
    name_map = {
        "Nflnetwork": "NFL Network",
        "Nflredzone": "NFL RedZone",
        "Espnusa": "ESPN USA"
    }
    if original_name in name_map:
        return name_map[original_name]
    if '@' in original_name:
        parts = original_name.split('@')
        if len(parts) == 2:
            team1 = parts[0].strip().title()
            team2 = parts[1].strip().title()
            return f"{team1} @ {team2}"
    return original_name

async def find_stream_in_page(page: Page, url: str) -> tuple[str | None, str | None]:
    final_url = None
    def handle_request(request):
        nonlocal final_url
        if STREAM_PATTERN.search(request.url):
            print(f"    ✅ Captured potential stream URL: {request.url}")
            final_url = request.url
    page.on("request", handle_request)
    try:
        await page.goto(url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(POST_LOAD_WAIT_MS)
    except Exception as e:
        print(f"    ❌ Error loading page {url}: {e}")
    finally:
        page.remove_listener("request", handle_request)
    return final_url, url

async def scrape_nfl():
    print("🚀 Starting NFL Webcast Scraper...")
    all_found_streams = {}
    CUSTOM_INFO = {
        "Nflnetwork": {
            "id": "NFL.Network.HD.us2",
            "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-network-hz-us.png?raw=true"
        },
        "Nflredzone": {
            "id": "NFL.RedZone.HD.us2",
            "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-red-zone-hz-us.png?raw=true"
        },
        "Espnusa": {
            "id": "ESPN.HD.us2",
            "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-us.png?raw=true"
        }
    }
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        try:
            await page.goto(NFL_BASE_URL, wait_until="domcontentloaded", timeout=60000)
            game_links_info = []
            event_cards = await page.query_selector_all("a:has-text('@')")
            for card in event_cards:
                name = await card.inner_text()
                href = await card.get_attribute("href")
                if name and href:
                    clean_name = ' '.join(name.split()).replace(' @ ', '@')
                    full_url = urljoin(NFL_BASE_URL, href)
                    game_links_info.append({"name": clean_name, "url": full_url})
            print(f"  Found {len(game_links_info)} potential game links.")
            for game in game_links_info:
                print(f"  ➡️ Processing Event: {game['name']}")
                game_page = await context.new_page()
                stream_url, _ = await find_stream_in_page(game_page, game['url'])
                if stream_url:
                    all_found_streams[game['name']] = stream_url
                await game_page.close()
            channel_urls = [u for u in NFL_START_URLS if u != NFL_BASE_URL]
            for url in channel_urls:
                page_name = url.strip('/').split('/')[-1].replace('-', ' ').title()
                print(f"  ➡️ Processing Channel: {page_name}")
                stream_url, _ = await find_stream_in_page(page, url)
                if stream_url:
                    all_found_streams[page_name] = stream_url
        except Exception as e:
            print(f"  ❌ Failed to process NFL pages: {e}")
        await browser.close()
    if not all_found_streams:
        print("⏹️ No NFL streams found.")
        return
    with open(NFL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, stream_url in sorted(all_found_streams.items()):
            group_title = "NFLWebcast - Live Games" if name in [g['name'] for g in game_links_info] else "NFLWebcast - 24/7 Streams"
            pretty_name = normalize_name(name)
            if name in CUSTOM_INFO:
                tvg_id = CUSTOM_INFO[name]["id"]
                tvg_logo = CUSTOM_INFO[name]["logo"]
            else:
                tvg_id = "NFL.Dummy.us"
                tvg_logo = "http://drewlive24.duckdns.org:9000/Logos/Maxx.png"
            extinf_line = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{pretty_name}" tvg-logo="{tvg_logo}" group-title="{group_title}",{pretty_name}\n'
            f.write(extinf_line)
            f.write(f'#EXTVLCOPT:http-referrer={NFL_BASE_URL}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
            f.write(f'#EXTVLCOPT:http-origin={NFL_BASE_URL}\n')
            f.write(stream_url + "\n")
    print("✅ NFL Playlist saved successfully!")

async def scrape_nhl():
    print("🚀 Starting NHL Webcast Scraper...")
    all_found_streams = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        try:
            await page.goto(NHL_BASE_URL, wait_until="domcontentloaded", timeout=60000)
            game_links_info = []
            event_cards = await page.query_selector_all("a:has-text('@')")
            for card in event_cards:
                name = await card.inner_text()
                href = await card.get_attribute("href")
                if name and href:
                    clean_name = ' '.join(name.split()).replace(' @ ', '@')
                    full_url = urljoin(NHL_BASE_URL, href)
                    game_links_info.append({"name": clean_name, "url": full_url})
            print(f"  Found {len(game_links_info)} potential game links.")
            for game in game_links_info:
                print(f"  ➡️ Processing Event: {game['name']}")
                game_page = await context.new_page()
                stream_url, _ = await find_stream_in_page(game_page, game['url'])
                if stream_url:
                    all_found_streams[game['name']] = stream_url
                await game_page.close()
        except Exception as e:
            print(f"  ❌ Failed to process NHL pages: {e}")
        await browser.close()
    if not all_found_streams:
        print("⏹️ No NHL streams found.")
        return
    with open(NHL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for name, stream_url in sorted(all_found_streams.items()):
            group_title = "NHLWebcast - Live Games"
            pretty_name = normalize_name(name)
            tvg_id = "NHL.Hockey.Dummy.us"
            tvg_logo = "http://drewlive24.duckdns.org:9000/Logos/Hockey.png"
            extinf_line = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{pretty_name}" tvg-logo="{tvg_logo}" group-title="{group_title}",{pretty_name}\n'
            f.write(extinf_line)
            f.write(f'#EXTVLCOPT:http-referrer={NHL_BASE_URL}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
            f.write(f'#EXTVLCOPT:http-origin={NHL_BASE_URL}\n')
            f.write(stream_url + "\n")
    print("✅ NHL Playlist saved successfully!")

if __name__ == "__main__":
    asyncio.run(scrape_nfl())
    asyncio.run(scrape_nhl())
