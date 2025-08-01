import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
import aiohttp
import os

# 🛡️ Force .su → .pk to bypass 301 redirects
def fix_url(url):
    return url.replace("streamed.su", "streamed.pk")

# 🧠 Retry failed API calls with delay
async def safe_request_with_retry(request, url, retries=3, delay=5, headers=None):
    for attempt in range(retries):
        try:
            resp = await request.get(url, timeout=60000, headers=headers)
            return await resp.json()
        except Exception as e:
            print(f"[!] Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    return []

ALLOWED_CATEGORIES = {
    "Basketball": {
        "tvg-id": "Basketball.Dummy.us",
        "logo": "http://drewlive24.duckdns.org:9000/Logos/Basketball.png"
    },
    "Football": {
        "tvg-id": "Soccer.Dummy.us",
        "logo": "http://drewlive24.duckdns.org:9000/Logos/Football2.png"
    },
    "American Football": {
        "tvg-id": "Football.Dummy.us",
        "logo": "http://drewlive24.duckdns.org:9000/Logos/Am-Football.png"
    },
    "Baseball": {
        "tvg-id": "Baseball.Dummy.us",
        "logo": "http://drewlive24.duckdns.org:9000/Logos/Baseball.png"
    },
    "Motor Sports": {
        "tvg-id": "Racing.Dummy.us",
        "logo": "http://drewlive24.duckdns.org:9000/Logos/Motorsports2.png"
    },
    "Fight (UFC, Boxing)": {
        "tvg-id": "PPV.EVENTS.Dummy.us",
        "logo": "http://drewlive24.duckdns.org:9000/Logos/CombatSports2.png"
    },
    "Other": {
        "tvg-id": "PPV.EVENTS.Dummy.us",
        "logo": "http://drewlive24.duckdns.org:9000/Logos/PPV.png"
    }
}

# 🎯 Validate stream link
async def check_m3u8_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=7) as resp:
                return resp.status == 200
    except Exception:
        return False

async def main():
    m3u_path = "StreamedSU.m3u8"
    if os.path.exists(m3u_path):
        os.remove(m3u_path)

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36")
        page = await context.new_page()
        request = context.request

        m3u = ["#EXTM3U"]
        m3u8_url = None

        async def capture_route(route, req):
            nonlocal m3u8_url
            if ".m3u8" in req.url:
                m3u8_url = req.url
            await route.continue_()

        await context.route("**/*", capture_route)

        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
        }

        sports = await safe_request_with_retry(request, fix_url("https://streamed.su/api/sports"), headers=headers)
        if not sports:
            print("[✖] No sports data fetched. Aborting.")
            return

        for sport in sports:
            sport_name = sport.get("name")
            if sport_name not in ALLOWED_CATEGORIES:
                continue

            sport_id = sport.get("id")
            tvg_id = ALLOWED_CATEGORIES[sport_name]["tvg-id"]
            fallback_logo = ALLOWED_CATEGORIES[sport_name]["logo"]
            group_title = f"StreamedSU - {sport_name}"

            print(f"\n=== {sport_name} ===")

            matches = await safe_request_with_retry(request, fix_url(f"https://streamed.su/api/matches/{sport_id}"), headers=headers)
            if not matches:
                print(f"[!] No matches for {sport_name}")
                continue

            for match in matches:
                title = match.get("title", "No Title")
                date_ts = match.get("date", 0)
                date = datetime.fromtimestamp(date_ts / 1000).strftime("%Y-%m-%d %H:%M")

                sources = match.get("sources", [])
                if not sources:
                    continue

                m3u8_url = None
                language = "Unknown"
                quality = "SD"

                for source in sources:
                    source_id = source.get("id")
                    source_type = source.get("source")

                    stream_data = await safe_request_with_retry(
                        request,
                        fix_url(f"https://streamed.su/api/stream/{source_type}/{source_id}"),
                        headers=headers
                    )

                    for stream_info in stream_data:
                        embed_url = stream_info.get("embedUrl")
                        if not embed_url:
                            continue

                        language = stream_info.get("language", "Unknown")
                        quality = "HD" if stream_info.get("hd") else "SD"
                        m3u8_url = None

                        try:
                            print(f"\nVisiting: {title} (source: {source_type})")
                            await page.goto(embed_url, timeout=15000)
                            await page.wait_for_timeout(3000)

                            box = await page.evaluate("""() => {
                                return { width: window.innerWidth, height: window.innerHeight };
                            }""")
                            x = box["width"] // 2
                            y = box["height"] // 2

                            for _ in range(6):
                                try:
                                    await page.mouse.click(x, y)
                                    await page.wait_for_timeout(2000)
                                    if m3u8_url:
                                        break
                                except Exception as click_err:
                                    print(f"[!] Mouse click error: {click_err}")
                                    continue

                            if m3u8_url:
                                valid = await check_m3u8_url(m3u8_url)
                                if valid:
                                    break
                                else:
                                    print(f"[!] Invalid stream URL (not 200): {m3u8_url}")
                                    m3u8_url = None
                            else:
                                print(f"[✖] No m3u8 found at: {embed_url}")

                        except PlaywrightTimeoutError:
                            print(f"[!] Timeout while loading: {embed_url}")
                        except Exception as e:
                            print(f"[!] Error visiting embed for {title}: {e}")

                    if m3u8_url:
                        break

                if not m3u8_url:
                    print(f"[✖] Failed: No valid stream found for {title}")
                    continue

                logo = fallback_logo
                teams = match.get("teams")
                if teams:
                    home = teams.get("home")
                    if home and home.get("badge"):
                        logo = f"https://streamed.pk/api/images/badge/{home['badge']}.webp"

                extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group_title}",{title} ({language} - {quality})'
                m3u.append(extinf)
                m3u.append(m3u8_url)
                print(f"[✔] Success: {title} ({language} - {quality})")

        playlist = "\n".join(m3u)
        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write(playlist)

        print("\n✅ Done. Playlist written to StreamedSU.m3u8")
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[!] Fatal error in main: {e}")
