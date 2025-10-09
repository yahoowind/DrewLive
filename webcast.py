import asyncio
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext, Page, async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
)
POST_LOAD_WAIT_MS = 8000
STREAM_PATTERN = re.compile(r"\.m3u8($|\?)", re.IGNORECASE)
OUTPUT_FILE = "SportsWebcast.m3u8"

NFL_BASE_URL = "https://nflwebcast.com/"
NHL_BASE_URL = "https://slapstreams.com/"
MLB_BASE_URL = "https://mlbwebcast.com/"
MLS_BASE_URL = "https://mlswebcast.com/"
NBA_BASE_URL = "https://nbawebcast.top/"

NFL_CHANNEL_URLS = [
    "http://nflwebcast.com/nflnetwork/",
    "https://nflwebcast.com/nflredzone/",
    "https://nflwebcast.com/espnusa/",
]
MLB_CHANNEL_URLS = []
NHL_CHANNEL_URLS = []
MLS_CHANNEL_URLS = []

CHANNEL_METADATA = {
    "nflnetwork": {"name": "NFL Network", "id": "NFL.Network.HD.us2", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-network-hz-us.png?raw=true"},
    "nflredzone": {"name": "NFL RedZone", "id": "NFL.RedZone.HD.us2", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-red-zone-hz-us.png?raw=true"},
    "espnusa": {"name": "ESPN", "id": "ESPN.HD.us2", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-us.png?raw=true"},
}

NBA_STREAM_URL_PATTERN = "https://gg.poocloud.in/{team_name}/tracks-v1a1/mono.ts.m3u8"
NBA_CUSTOM_HEADERS = {
    "origin": "https://ppv.to",
    "referrer": "https://ppv.to/",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
}

def normalize_game_name(original_name: str) -> str:
    cleaned_name = " ".join(original_name.splitlines()).strip()
    if "@" in cleaned_name:
        parts = cleaned_name.split("@")
        if len(parts) == 2:
            team1 = parts[0].strip().title()
            team2 = parts[1].strip().title()
            team2 = team2.split("October")[0].strip()
            return f"{team1} @ {team2}"
    return " ".join(cleaned_name.strip().split()).title()

async def verify_stream_url(session: aiohttp.ClientSession, url: str) -> bool:
    try:
        async with session.head(url, timeout=10, allow_redirects=True) as response:
            if response.status == 200:
                print(f"    ✔️  URL Verified (200 OK): {url}")
                return True
            else:
                print(f"    ❌ URL Failed ({response.status}): {url}")
                return False
    except asyncio.TimeoutError:
        print(f"    ❌ URL Timed Out: {url}")
        return False
    except aiohttp.ClientError as e:
        print(f"    ❌ URL Client Error ({type(e).__name__}): {url}")
        return False

async def find_stream_in_page(page: Page, url: str, session: aiohttp.ClientSession) -> Optional[str]:
    candidate_urls: List[str] = []
    def handle_request(request):
        if STREAM_PATTERN.search(request.url) and request.url not in candidate_urls:
            print(f"    ✅ Captured potential stream: {request.url}")
            candidate_urls.append(request.url)

    page.on("request", handle_request)
    try:
        await page.goto(url, wait_until="load", timeout=30000)
        await page.wait_for_timeout(POST_LOAD_WAIT_MS)
    except Exception as e:
        print(f"    ❌ Error loading or processing page {url}: {e}")
    finally:
        page.remove_listener("request", handle_request)

    for stream_url in reversed(candidate_urls):
        if await verify_stream_url(session, stream_url):
            return stream_url
    return None

async def find_stream_from_servers_on_page(context: BrowserContext, page_url: str, base_url: str, session: aiohttp.ClientSession) -> Optional[str]:
    page = await context.new_page()
    server_urls = []
    try:
        print(f"   L_ Navigating to content page: {page_url}")
        await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
        server_links = page.locator("#multistmb a")
        count = await server_links.count()

        if count == 0:
            print("    Fallback: '#multistmb a' not found. Trying generic selector.")
            server_links = page.locator("a:has-text('Server'), a:has-text('HD'), a:has-text('Home'), a:has-text('Away')")
            count = await server_links.count()

        print(f"    Found {count} potential server links.")
        for i in range(count):
            href = await server_links.nth(i).get_attribute("href")
            if href:
                full_url = urljoin(base_url, href)
                if full_url not in server_urls:
                    server_urls.append(full_url)
    except Exception as e:
        print(f"    ❌ Could not load page or find server links: {e}")
        return None
    finally:
        await page.close()

    for server_url in server_urls:
        print(f"    ➡️ Trying Server: {server_url}")
        server_page = await context.new_page()
        stream_url = await find_stream_in_page(server_page, server_url, session)
        await server_page.close()
        if stream_url:
            return stream_url
    print("    ❌ All servers tried, but no valid stream was found.")
    return None

async def scrape_league(base_url: str, channel_urls: List[str], group_prefix: str, default_id: str, default_logo: str) -> List[Dict]:
    print(f"\nScraping {group_prefix} streams from {base_url}...")
    found_streams: Dict[str, Tuple[str, str, Optional[str]]] = {}
    results: List[Dict] = []
    
    async with async_playwright() as p, aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        try:
            page = await context.new_page()
            await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(POST_LOAD_WAIT_MS)

            game_links_info = []
            event_rows = page.locator("#mtable tr.singele_match_date:not(.mdatetitle)")
            count = await event_rows.count()
            
            for i in range(count):
                row = event_rows.nth(i)
                
                link_locator = row.locator("td.teamvs a")
                name = await link_locator.inner_text()
                href = await link_locator.get_attribute("href")

                logo_url = None
                logo_locators = row.locator("td.teamlogo img")
                if await logo_locators.count() > 1:
                    logo_url = await logo_locators.nth(1).get_attribute("src")
                elif await logo_locators.count() > 0:
                    logo_url = await logo_locators.nth(0).get_attribute("src")

                if name and href:
                    unique_name_key = " ".join(name.splitlines()).strip()
                    full_url = urljoin(base_url, href)
                    final_logo_url = logo_url if logo_url else default_logo
                    game_links_info.append({"name": unique_name_key, "url": full_url, "logo": final_logo_url})

            await page.close()
            print(f"  Found {len(game_links_info)} potential live game links.")

            for game in game_links_info:
                print(f"  ➡️ Processing Game: {normalize_game_name(game['name'])}")
                stream_url = await find_stream_from_servers_on_page(context, game["url"], base_url, session)
                if stream_url:
                    found_streams[game["name"]] = (stream_url, "Live Games", game["logo"])
            
            for url in channel_urls:
                slug = url.strip("/").split("/")[-1]
                print(f"  ➡️ Processing Channel: {slug}")
                stream_url = await find_stream_from_servers_on_page(context, url, base_url, session)
                if stream_url:
                    found_streams[slug] = (stream_url, "24/7 Channels", None)
        except Exception as e:
            print(f"  ❌ A critical error occurred while scraping {group_prefix}: {e}")
        finally:
            await browser.close()

    for slug, data_tuple in sorted(found_streams.items()):
        stream_url, category, scraped_logo = data_tuple
        
        info = CHANNEL_METADATA.get(slug, {})
        pretty_name = info.get("name", normalize_game_name(slug))
        tvg_id = info.get("id", default_id)
        tvg_logo = info.get("logo") or scraped_logo or default_logo
        
        results.append({"name": pretty_name, "url": stream_url, "tvg_id": tvg_id, "tvg_logo": tvg_logo, "group": f"{group_prefix} - {category}", "ref": base_url})
    return results

async def scrape_nba_league(default_logo: str) -> List[Dict]:
    print(f"\nScraping NBAWebcast streams from {NBA_BASE_URL}...")
    results: List[Dict] = []
    
    async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        try:
            async with session.get(NBA_BASE_URL, timeout=20) as response:
                response.raise_for_status()
                html_content = await response.text()
        except aiohttp.ClientError as e:
            print(f"  ❌ Error fetching NBA page: {e}")
            return []

        soup = BeautifulSoup(html_content, 'lxml')
        schedule_table = soup.find('table', class_='NBA_schedule_container')
        if not schedule_table:
            print("  ❌ Could not find NBA schedule table.")
            return []

        game_rows = schedule_table.find('tbody').find_all('tr')
        print(f"  Found {len(game_rows)} potential NBA games.")

        for row in game_rows:
            try:
                teams = [span.text for span in row.find_all('td', class_='teamvs')]
                away_team, home_team = teams[0].strip(), teams[1].strip()
                
                logos = row.find_all('td', class_='teamlogo')
                logo_url = logos[1].find('img')['src'] if len(logos) > 1 and logos[1].find('img') else default_logo
                
                watch_button = row.find('button', class_='watch_btn')
                if watch_button and watch_button.has_attr('data-team'):
                    team_key = watch_button['data-team']
                    stream_url = NBA_STREAM_URL_PATTERN.format(team_name=team_key)
                    match_title = f"{away_team} vs {home_team}"
                    
                    if await verify_stream_url(session, stream_url):
                        results.append({
                            "name": match_title,
                            "url": stream_url,
                            "tvg_id": "NBA.Basketball.Dummy.us",
                            "tvg_logo": logo_url,
                            "group": "NBAWebcast - Live Games",
                            "ref": NBA_BASE_URL,
                            "custom_headers": NBA_CUSTOM_HEADERS,
                        })
            except (AttributeError, IndexError) as e:
                print(f"  ⚠️ Could not parse an NBA game row, skipping. Error: {e}")
            
    return results

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
            
            if "custom_headers" in entry:
                headers = entry["custom_headers"]
                f.write(f'#EXTVLCOPT:http-origin={headers["origin"]}\n')
                f.write(f'#EXTVLCOPT:http-referrer={headers["referrer"]}\n')
                f.write(f'#EXTVLCOPT:http-user-agent={headers["user_agent"]}\n')
            else:
                f.write(f'#EXTVLCOPT:http-origin={entry["ref"]}\n')
                f.write(f'#EXTVLCOPT:http-referrer={entry["ref"]}\n')
                f.write(f"#EXTVLCOPT:http-user-agent={USER_AGENT}\n")
                
            f.write(entry["url"] + "\n")

    print(f"✅ Playlist with {len(streams)} streams saved successfully to {filename}!")

async def main():
    print("🚀 Starting Sports Webcast Scraper...")

    NBA_DEFAULT_LOGO = "http://drewlive24.duckdns.org:9000/Logos/Basketball.png"

    tasks = [
        scrape_league(
            base_url=NFL_BASE_URL, channel_urls=NFL_CHANNEL_URLS, group_prefix="NFLWebcast",
            default_id="NFL.Dummy.us", default_logo="http://drewlive24.duckdns.org:9000/Logos/Maxx.png"
        ),
        scrape_league(
            base_url=NHL_BASE_URL, channel_urls=NHL_CHANNEL_URLS, group_prefix="NHLWebcast",
            default_id="NHL.Hockey.Dummy.us", default_logo="http://drewlive24.duckdns.org:9000/Logos/Hockey.png"
        ),
        scrape_league(
            base_url=MLB_BASE_URL, channel_urls=MLB_CHANNEL_URLS, group_prefix="MLBWebcast",
            default_id="MLB.Baseball.Dummy.us", default_logo="http://drewlive24.duckdns.org:9000/Logos/MLB.png"
        ),
        scrape_league(
            base_url=MLS_BASE_URL, channel_urls=MLS_CHANNEL_URLS, group_prefix="MLSWebcast",
            default_id="MLS.Soccer.Dummy.us", default_logo="http://drewlive24.duckdns.org:9000/Logos/Football2.png"
        ),
        scrape_nba_league(default_logo=NBA_DEFAULT_LOGO),
    ]
    
    results = await asyncio.gather(*tasks)
    
    all_streams = [stream for league_streams in results for stream in league_streams]
    
    write_playlist(all_streams, OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(main())
