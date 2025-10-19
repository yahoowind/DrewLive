import asyncio
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext, async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0"
)

DYNAMIC_WAIT_TIMEOUT = 20000
GAME_TABLE_WAIT_TIMEOUT = 45000

STREAM_PATTERN = re.compile(r"\.m3u8($|\?)", re.IGNORECASE)
OUTPUT_FILE = "SportsWebcast.m3u8"

NFL_BASE_URL = "https://nflwebcast.com/"
NHL_BASE_URL = "https://slapstreams.com/"
MLB_BASE_URL = "https://mlbwebcast.com/"
MLS_BASE_URL = "https://mlswebcast.com/"
NBA_BASE_URL = "https://nbawebcast.top/"

NFL_CHANNEL_URLS = [
    "https://nflwebcast.com/nflnetwork/",
    "https://nflwebcast.com/nflredzone/",
    "https://nflwebcast.com/espnusa/",
]
NHL_CHANNEL_URLS = []
MLB_CHANNEL_URLS = []
MLS_CHANNEL_URLS = []

CHANNEL_METADATA = {
    "nflnetwork": {
        "name": "NFL Network",
        "id": "NFL.Network.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-network-hz-us.png?raw=true"
    },
    "nflredzone": {
        "name": "NFL RedZone",
        "id": "NFL.RedZone.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-red-zone-hz-us.png?raw=true"
    },
    "espnusa": {
        "name": "ESPN",
        "id": "ESPN.HD.us2",
        "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-us.png?raw=true"
    },
}

NBA_STREAM_URL_PATTERN = "https://gg.poocloud.in/{team_name}/tracks-v1a1/mono.ts.m3u8"
NBA_CUSTOM_HEADERS = {
    "origin": "https://ppv.to",
    "referrer": "https://ppv.to/",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
}


def normalize_game_name(name: str) -> str:
    name = " ".join(name.splitlines()).strip()
    if "@" in name:
        parts = name.split("@")
        if len(parts) == 2:
            team1 = parts[0].strip().title()
            team2 = re.split(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b', parts[1], 1)[0].strip()
            return f"{team1} @ {team2}"
    return name.title()


async def verify_stream_url(session: aiohttp.ClientSession, url: str, headers: Optional[Dict[str, str]] = None) -> bool:
    request_headers = headers or {}
    request_headers.setdefault("User-Agent", USER_AGENT)

    try:
        async with session.get(url, timeout=10, allow_redirects=True, headers=request_headers) as r:
            if r.status == 200:
                print(f"    ✔️ Verified: {url}")
                return True
            else:
                print(f"    ❌ Bad status {r.status}: {url}")
    except Exception as e:
        print(f"    ❌ Error verifying {url}: {type(e).__name__}")
    return False


async def find_stream_from_servers_on_page(context: BrowserContext, page_url: str, base_url: str, session: aiohttp.ClientSession) -> Optional[str]:
    page = await context.new_page()
    candidates = []

    def on_req(req):
        if STREAM_PATTERN.search(req.url) and req.url not in candidates:
            candidates.append(req.url)
            print(f"    🔎 Captured: {req.url}")

    page.on("request", on_req)

    try:
        await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=DYNAMIC_WAIT_TIMEOUT)

        for url in reversed(candidates):
            if await verify_stream_url(session, url, {"Origin": base_url, "Referer": base_url}):
                return url

        iframe = page.frame_locator("iframe").first
        links = iframe.locator("#multistmb a, a:has-text('Server'), a:has-text('HD')")
        for i in range(await links.count()):
            link = links.nth(i)
            await link.click()
            await page.wait_for_timeout(3000)
            for url in reversed(candidates):
                if await verify_stream_url(session, url, {"Origin": base_url, "Referer": base_url}):
                    return url

    except Exception as e:
        print(f"    ❌ Error {page_url}: {e}")
    finally:
        page.remove_listener("request", on_req)
        await page.close()
    return None


async def scrape_league(base_url, channel_urls, group_prefix, default_id, default_logo):
    results = []
    async with async_playwright() as p, aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(user_agent=USER_AGENT)

        page = await context.new_page()
        await page.goto(base_url, wait_until="domcontentloaded", timeout=60000)

        try:
            await page.wait_for_selector("#mtable tr.singele_match_date:not(.mdatetitle)", timeout=GAME_TABLE_WAIT_TIMEOUT)
        except Exception:
            print(f"⚠️ No game table for {group_prefix}")
            await browser.close()
            return []

        rows = page.locator("#mtable tr.singele_match_date:not(.mdatetitle)")
        for i in range(await rows.count()):
            row = rows.nth(i)
            link = row.locator("td.teamvs a")
            href = await link.get_attribute("href")
            name = await link.inner_text()
            if not href:
                continue
            full_url = urljoin(base_url, href)
            stream_url = await find_stream_from_servers_on_page(context, full_url, base_url, session)
            if stream_url:
                results.append({
                    "name": normalize_game_name(name),
                    "url": stream_url,
                    "tvg_id": default_id,
                    "tvg_logo": default_logo,
                    "group": f"{group_prefix} - Live Games",
                    "ref": base_url
                })

        # process 24/7 channels
        for url in channel_urls:
            slug = url.strip("/").split("/")[-1]
            stream_url = await find_stream_from_servers_on_page(context, url, base_url, session)
            if stream_url:
                meta = CHANNEL_METADATA.get(slug, {})
                results.append({
                    "name": meta.get("name", slug),
                    "url": stream_url,
                    "tvg_id": meta.get("id", default_id),
                    "tvg_logo": meta.get("logo", default_logo),
                    "group": f"{group_prefix} - 24/7 Channels",
                    "ref": base_url
                })

        await browser.close()
    return results


async def scrape_nba_league(default_logo):
    print("🏀 Scraping NBAWebcast...")
    results = []
    async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as s:
        try:
            async with s.get(NBA_BASE_URL, timeout=20) as r:
                r.raise_for_status()
                html = await r.text()
        except Exception as e:
            print(f"  ❌ NBA fetch failed: {e}")
            return results

        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", class_="NBA_schedule_container")
        if not table:
            print("  ⚠️ NBA table missing")
            return results

        for tr in table.select("tbody tr"):
            btn = tr.find("button", class_="watch_btn")
            if not btn or not btn.has_attr("data-team"):
                continue
            team_key = btn["data-team"]
            stream = NBA_STREAM_URL_PATTERN.format(team_name=team_key)
            if await verify_stream_url(s, stream, NBA_CUSTOM_HEADERS):
                results.append({
                    "name": "NBA Game",
                    "url": stream,
                    "tvg_id": "NBA.Dummy.us",
                    "tvg_logo": default_logo,
                    "group": "NBAWebcast - Live Games",
                    "ref": NBA_BASE_URL,
                    "custom_headers": NBA_CUSTOM_HEADERS
                })
    return results


def write_playlist(streams, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for s in streams:
            f.write(f'#EXTINF:-1 tvg-id="{s["tvg_id"]}" tvg-logo="{s["tvg_logo"]}" group-title="{s["group"]}",{s["name"]}\n')
            if "custom_headers" in s:
                h = s["custom_headers"]
                f.write(f'#EXTVLCOPT:http-origin={h["origin"]}\n#EXTVLCOPT:http-referrer={h["referrer"]}\n#EXTVLCOPT:http-user-agent={h["user_agent"]}\n')
            else:
                f.write(f'#EXTVLCOPT:http-origin={s["ref"]}\n#EXTVLCOPT:http-referrer={s["ref"]}\n#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
            f.write(s["url"] + "\n")
    print(f"✅ Wrote {len(streams)} entries to {filename}")


async def main():
    print("🚀 Running SportsWebcast Scraper...")
    logo = "http://drewlive24.duckdns.org:9000/Logos/Basketball.png"
    results = await asyncio.gather(
        scrape_league(NFL_BASE_URL, NFL_CHANNEL_URLS, "NFLWebcast", "NFL.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Maxx.png"),
        scrape_league(NHL_BASE_URL, NHL_CHANNEL_URLS, "NHLWebcast", "NHL.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Hockey.png"),
        scrape_league(MLB_BASE_URL, MLB_CHANNEL_URLS, "MLBWebcast", "MLB.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/MLB.png"),
        scrape_league(MLS_BASE_URL, MLS_CHANNEL_URLS, "MLSWebcast", "MLS.Dummy.us", "http://drewlive24.duckdns.org:9000/Logos/Football2.png"),
        scrape_nba_league(logo),
    )
    streams = [s for group in results for s in group]
    write_playlist(streams, OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())
