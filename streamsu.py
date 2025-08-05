import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
import os

# Config
m3u_path = "StreamedSU.m3u8"

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

async def fetch_via_browser(page, url):
    try:
        return await page.evaluate(f"""async () => {{
            const res = await fetch('{url}');
            const text = await res.text();
            try {{
                return JSON.parse(text);
            }} catch (e) {{
                console.error('❌ JSON parse failed. Raw response:', text.slice(0, 300));
                return [];
            }}
        }}""")
    except Exception as e:
        print(f"[!] Browser fetch failed for {url}: {e}")
        return []

async def main():
    if os.path.exists(m3u_path):
        os.remove(m3u_path)

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://streamed.pk", timeout=30000)
        await page.wait_for_timeout(5000)

        m3u = ["#EXTM3U"]

        sports = await fetch_via_browser(page, "https://streamed.pk/api/sports")
        if not sports:
            print("[✖] No sports data fetched. Writing stub file.")
            with open(m3u_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n# Failed to fetch sports data.\n")
            await browser.close()
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

            matches = await fetch_via_browser(page, f"https://streamed.pk/api/matches/{sport_id}")
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
                for source in sources:
                    source_id = source.get("id")
                    source_type = source.get("source")
                    stream_data = await fetch_via_browser(page, f"https://streamed.pk/api/stream/{source_type}/{source_id}")

                    for stream_info in stream_data:
                        embed_url = stream_info.get("embedUrl")
                        if not embed_url:
                            continue

                        try:
                            print(f"Visiting: {title} -> {embed_url}")
                            await page.goto(embed_url, timeout=20000)
                            await page.wait_for_timeout(5000)

                            content = await page.content()
                            if ".m3u8" in content:
                                start = content.find(".m3u8")
                                fragment = content[max(0, start-300):start+10]
                                m3u8_candidate = fragment.split('"')[-2]
                                if m3u8_candidate.startswith("http") and ".m3u8" in m3u8_candidate:
                                    m3u8_url = m3u8_candidate
                                    break

                        except Exception as e:
                            print(f"[!] Failed to load embed for {title}: {e}")

                    if m3u8_url:
                        break

                if not m3u8_url:
                    print(f"[✖] No stream found for {title}")
                    continue

                logo = fallback_logo
                teams = match.get("teams")
                if teams:
                    home = teams.get("home")
                    if home and home.get("badge"):
                        logo = f"https://streamed.pk/api/images/badge/{home['badge']}.webp"

                extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group_title}",{title} ({date})'
                m3u.extend([extinf, m3u8_url])
                print(f"[✔] Added: {title}")

        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))

        print("\n✅ Playlist written to StreamedSU.m3u8")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
