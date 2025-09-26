import asyncio
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from playwright.async_api import Page, async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
)
POST_LOAD_WAIT_MS = 8000
STREAM_PATTERN = re.compile(r"\.m3u8($|\?)", re.IGNORECASE)
OUTPUT_FILE = "SportsWebcast.m3u8"

NFL_BASE_URL = "https://nflwebcast.com/"
NHL_BASE_URL = "https://nhlwebcast.com/200"
MLB_BASE_URL = "https://mlbwebcast.com/"

NFL_CHANNEL_URLS = [
    "http://nflwebcast.com/nflnetwork/",
    "https://nflwebcast.com/nflredzone/",
    "https://nflwebcast.com/espnusa/",
]
MLB_CHANNEL_URLS = [
    "https://mlbwebcast.com/mlb-network-live/",
    "https://mlbwebcast.com/fox-sports-live/",
]
NHL_CHANNEL_URLS = []

CHANNEL_METADATA = {
    "nflnetwork": {
        "name": "NFL Network",
        "id": "NFL.Network.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-network-hz-us.png?raw=true",
    },
    "nflredzone": {
        "name": "NFL RedZone",
        "id": "NFL.RedZone.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-red-zone-hz-us.png?raw=true",
    },
    "espnusa": {
        "name": "ESPN",
        "id": "ESPN.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-us.png?raw=true",
    },
    "mlb-network-live": {
        "name": "MLB Network",
        "id": "MLB.Network.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/mlb-network-us.png?raw=true",
    },
    "fox-sports-live": {
        "name": "Fox Sports 1",
        "id": "FS1.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-sports-1-us.png?raw=true",
    },
}

def normalize_game_name(original_name: str) -> str:
    if "@" in original_name:
        parts = original_name.split("@")
        if len(parts) == 2:
            team1 = parts[0].strip().title()
            team2 = parts[1].strip().title()
            return f"{team1} @ {team2}"
    return " ".join(original_name.strip().split()).title()


async def find_stream_in_page(page: Page, url: str) -> Optional[str]:
    final_url: Optional[str] = None

    def handle_request(request):
        nonlocal final_url
        if STREAM_PATTERN.search(request.url) and not final_url:
            print(f"    ✅ Captured stream URL: {request.url}")
            final_url = request.url

    page.on("request", handle_request)
    try:
        await page.goto(url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(POST_LOAD_WAIT_MS)
    except Exception as e:
        print(f"    ❌ Error loading or processing page {url}: {e}")
    finally:
        page.remove_listener("request", handle_request)

    return final_url


def write_playlist(streams: List[Dict], filename: str):
    if not streams:
        print("⏹️ No streams found to write to the playlist.")
        return

    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for entry in streams:
            extinf_line = (
                f'#EXTINF:-1 tvg-id="{entry["tvg_id"]}" '
                f'tvg-name="{entry["name"]}" '
                f'tvg-logo="{entry["tvg_logo"]}" '
                f'group-title="{entry["group"]}",{entry["name"]}\n'
            )
            f.write(extinf_line)
            f.write(f'#EXTVLCOPT:http-referrer={entry["ref"]}\n')
            f.write(f"#EXTVLCOPT:http-user-agent={USER_AGENT}\n")
            f.write(f'#EXTVLCOPT:http-origin={entry["ref"]}\n')
            f.write(entry["url"] + "\n")

    print(f"✅ Playlist with {len(streams)} streams saved successfully to {filename}!")


async def scrape_league(
    base_url: str,
    channel_urls: List[str],
    group_prefix: str,
    default_id: str,
    default_logo: str,
) -> List[Dict]:
    print(f"\n scraping {group_prefix} streams from {base_url}...")
    found_streams: Dict[str, Tuple[str, str]] = {}
    results: List[Dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)

        try:
            page = await context.new_page()
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(POST_LOAD_WAIT_MS)

            game_links_info = []
            event_cards = page.locator("a:has-text('@')")
            count = await event_cards.count()
            for i in range(count):
                card = event_cards.nth(i)
                name = await card.inner_text()
                href = await card.get_attribute("href")
                if name and href:
                    clean_name = " ".join(name.split()).replace(" @ ", "@")
                    full_url = urljoin(base_url, href)
                    game_links_info.append({"name": clean_name, "url": full_url})
            
            print(f"  Found {len(game_links_info)} potential live game links.")

            for game in game_links_info:
                print(f"  ➡️ Processing Game: {game['name']}")
                game_page = await context.new_page()
                stream_url = await find_stream_in_page(game_page, game["url"])
                if stream_url:
                    found_streams[game["name"]] = (stream_url, "Live Games")
                await game_page.close()

            for url in channel_urls:
                slug = url.strip("/").split("/")[-1]
                print(f"  ➡️ Processing Channel: {slug}")
                channel_page = await context.new_page()
                stream_url = await find_stream_in_page(channel_page, url)
                if stream_url:
                    found_streams[slug] = (stream_url, "24/7 Channels")
                await channel_page.close()

        except Exception as e:
            print(f"  ❌ A critical error occurred while scraping {group_prefix}: {e}")
        finally:
            await browser.close()

    for slug, (stream_url, category) in sorted(found_streams.items()):
        is_channel = slug in CHANNEL_METADATA

        if is_channel:
            info = CHANNEL_METADATA[slug]
            pretty_name = info["name"]
            tvg_id = info["id"]
            tvg_logo = info["logo"]
        else:
            pretty_name = normalize_game_name(slug)
            tvg_id = default_id
            tvg_logo = default_logo

        results.append(
            {
                "name": pretty_name,
                "url": stream_url,
                "tvg_id": tvg_id,
                "tvg_logo": tvg_logo,
                "group": f"{group_prefix} - {category}",
                "ref": base_url,
            }
        )
    return results


async def main():
    print("🚀 Starting Sports Webcast Scraper...")

    nfl_streams = await scrape_league(
        base_url=NFL_BASE_URL,
        channel_urls=NFL_CHANNEL_URLS,
        group_prefix="NFLWebcast 🏈",
        default_id="NFL.Dummy.us",
        default_logo="http://drewlive24.duckdns.org:9000/Logos/Maxx.png",
    )

    nhl_streams = await scrape_league(
        base_url=NHL_BASE_URL,
        channel_urls=NHL_CHANNEL_URLS,
        group_prefix="NHLWebcast 🏒",
        default_id="NHL.Hockey.Dummy.us",
        default_logo="http://drewlive24.duckdns.org:9000/Logos/Hockey.png",
    )

    mlb_streams = await scrape_league(
        base_url=MLB_BASE_URL,
        channel_urls=MLB_CHANNEL_URLS,
        group_prefix="MLBWebcast ⚾",
        default_id="MLB.Baseball.Dummy.us",
        default_logo="http://drewlive24.duckdns.org:9000/Logos/MLB.png",
    )

    all_streams = nfl_streams + nhl_streams + mlb_streams
    write_playlist(all_streams, OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())
