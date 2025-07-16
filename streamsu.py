import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

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

async def main():
    m3u_path = "StreamedSU.m3u8"
    if os.path.exists(m3u_path):
        os.remove(m3u_path)

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        request = context.request

        m3u = ["#EXTM3U"]

        sports_resp = await request.get("https://streamed.su/api/sports")
        sports = await sports_resp.json()

        for sport in sports:
            sport_name = sport["name"]
            if sport_name not in ALLOWED_CATEGORIES:
                continue

            sport_id = sport["id"]
            tvg_id = ALLOWED_CATEGORIES[sport_name]["tvg-id"]
            fallback_logo = ALLOWED_CATEGORIES[sport_name]["logo"]
            group_title = f"StreamedSU - {sport_name}"

            print(f"\n=== {sport_name} ===")

            matches_resp = await request.get(f"https://streamed.su/api/matches/{sport_id}")
            matches = await matches_resp.json()

            for match in matches:
                title = match.get("title", "No Title")
                date_ts = match.get("date", 0)
                date = datetime.fromtimestamp(date_ts / 1000).strftime("%Y-%m-%d %H:%M")

                sources = match.get("sources", [])
                if not sources:
                    continue

                valid_stream = None

                for source in sources:
                    source_id = source.get("id")
                    source_type = source.get("source")

                    streams_resp = await request.get(f"https://streamed.su/api/stream/{source_type}/{source_id}")
                    streams = await streams_resp.json()

                    for stream_info in streams:
                        embed_url = stream_info.get("embedUrl")
                        if not embed_url:
                            continue

                        language = stream_info.get("language", "Unknown")
                        quality = "HD" if stream_info.get("hd") else "SD"
                        m3u8_url = None

                        try:
                            async def capture_route(route, req):
                                nonlocal m3u8_url
                                if ".m3u8" in req.url and "master" in req.url:
                                    m3u8_url = req.url
                                await route.continue_()

                            await context.route("**/*", capture_route)

                            print(f"▶️ Trying stream: {embed_url}")
                            await page.goto(embed_url, timeout=30000)
                            await page.wait_for_timeout(3000)

                            box = await page.evaluate("""() => ({
                                width: window.innerWidth,
                                height: window.innerHeight
                            })""")
                            x, y = box["width"] // 2, box["height"] // 2

                            for _ in range(6):
                                await page.mouse.click(x, y)
                                await page.wait_for_timeout(2000)
                                if m3u8_url:
                                    break

                            # If no URL or player error visible
                            error_text = await page.inner_text("body", timeout=5000).catch(lambda _: "")
                            if "error" in error_text.lower() or not m3u8_url:
                                print(f"[✖] Skipped: Playback error or no m3u8 found.")
                                continue

                            valid_stream = {
                                "url": m3u8_url,
                                "language": language,
                                "quality": quality,
                                "embed": embed_url
                            }
                            break  # ✅ Found good stream, stop checking backups

                        except Exception as e:
                            print(f"[!] Error checking stream: {e}")
                            continue

                    if valid_stream:
                        break

                if not valid_stream:
                    print(f"[✖] No valid stream found for {title}")
                    continue

                # Use fallback logo unless better one found
                logo = fallback_logo
                teams = match.get("teams")
                if teams:
                    home = teams.get("home")
                    if home and home.get("badge"):
                        logo = f"https://streamed.su/api/images/badge/{home['badge']}.webp"

                extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group_title}",{title} ({valid_stream["language"]} - {valid_stream["quality"]})'
                m3u.append(extinf)
                m3u.append(valid_stream["url"])
                print(f"[✔] Added: {title} ({valid_stream['language']} - {valid_stream['quality']})")

        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))

        print("\n✅ Done. Playlist written to StreamedSU.m3u8")
        await browser.close()

asyncio.run(main())
