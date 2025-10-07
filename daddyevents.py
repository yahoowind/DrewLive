import json
import re
import asyncio
import platform
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

EVENTS_URL = "https://dlhd.dad/schedule/schedule-generated.php"
SITE_ROOT = "https://dlhd.dad/"
OUTPUT_FILE = "DaddyLiveEvents.m3u8"

CUSTOM_HEADERS = [
    '#EXTVLCOPT:http-origin=https://jxoxkplay.xyz',
    '#EXTVLCOPT:http-referrer=https://jxoxkplay.xyz/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0'
]

CATEGORY_MAPPING = {
    "PPV Events": "PPV Events",
    "Soccer": "Soccer",
    "Motorsport": "Motorsport",
    "Boxing": "Boxing",
    "MMA": "MMA",
    "WWE": "WWE",
    "Combat sports": "Combat sports",
    "Golf": "Golf",
    "Am. Football": "Am. Football",
    "Baseball (MLB)": "Baseball (MLB)",
    "Basketball": "Basketball",
    "Ice Hockey": "Ice Hockey",
    "NFL": "Am. Football",
    "NHL": "Ice Hockey",
    "WNBA": "Basketball",
    "Soccer - Ireland Republic": "Soccer",
    "All Soccer Events": "Soccer"
}

API_TO_GROUP = {
    "PPV Events": "DaddyLive - Premium PPVs",
    "Soccer": "DaddyLive - Soccer Action",
    "Motorsport": "DaddyLive - Race Circuit",
    "Boxing": "DaddyLive - Fight Night",
    "MMA": "DaddyLive - Mixed Martial Arts",
    "WWE": "DaddyLive - Pro Wrestling",
    "Combat sports": "DaddyLive - Combat Zone",
    "Golf": "DaddyLive - Golf Tee-Off",
    "Am. Football": "DaddyLive - Gridiron Football",
    "Baseball (MLB)": "DaddyLive - Diamond Baseball",
    "Basketball": "DaddyLive - Hoops Central",
    "Ice Hockey": "DaddyLive - Ice Hockey"
}

CATEGORY_LOGOS = {
    "DaddyLive - Premium PPVs": "http://drewlive24.duckdns.org:9000/Logos/PPV.png",
    "DaddyLive - Soccer Action": "http://drewlive24.duckdns.org:9000/Logos/Soccer.png",
    "DaddyLive - Race Circuit": "http://drewlive24.duckdns.org:9000/Logos/Motorsport.png",
    "DaddyLive - Fight Night": "http://drewlive24.duckdns.org:9000/Logos/Boxing-2.png",
    "DaddyLive - Mixed Martial Arts": "http://drewlive24.duckdns.org:9000/Logos/MMA.png",
    "DaddyLive - Pro Wrestling": "http://drewlive24.duckdns.org:9000/Logos/WWE.png",
    "DaddyLive - Combat Zone": "http://drewlive24.duckdns.org:9000/Logos/Combat-Sports.png",
    "DaddyLive - Golf Tee-Off": "http://drewlive24.duckdns.org:9000/Logos/Golf.png",
    "DaddyLive - Gridiron Football": "http://drewlive24.duckdns.org:9000/Logos/Am-Football.png",
    "DaddyLive - Diamond Baseball": "http://drewlive24.duckdns.org:9000/Logos/Baseball-2.png",
    "DaddyLive - Hoops Central": "http://drewlive24.duckdns.org:9000/Logos/Basketball-2.png",
    "DaddyLive - Ice Hockey": "http://drewlive24.duckdns.org:9000/Logos/Hockey.png"
}

CATEGORY_TVG_IDS = {
    "DaddyLive - Premium PPVs": "PPV.EVENTS.Dummy.us",
    "DaddyLive - Soccer Action": "Soccer.Dummy.us",
    "DaddyLive - Race Circuit": "Racing.Dummy.us",
    "DaddyLive - Fight Night": "PPV.EVENTS.Dummy.us",
    "DaddyLive - Mixed Martial Arts": "UFC.Fight.Pass.Dummy.us",
    "DaddyLive - Pro Wrestling": "PPV.EVENTS.Dummy.us",
    "DaddyLive - Combat Zone": "PPV.EVENTS.Dummy.us",
    "DaddyLive - Golf Tee-Off": "Golf.Dummy.us",
    "DaddyLive - Gridiron Football": "Football.Dummy.us",
    "DaddyLive - Diamond Baseball": "Baseball.Dummy.us",
    "DaddyLive - Hoops Central": "Basketball.Dummy.us",
    "DaddyLive - Ice Hockey": "NHL.Hockey.Dummy.us"
}

def flatten_events(json_data):
    flat = []
    is_windows = platform.system() == "Windows"
    date_format = "%b %#d, %Y %#I:%M %p" if is_windows else "%b %-d, %Y %-I:%M %p"

    tz_uk = ZoneInfo("Europe/London")
    tz_mt = ZoneInfo("America/Denver")
    tz_est = ZoneInfo("America/New_York")

    for date_key, day in json_data.items():
        cleaned_date = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})', date_key)
        if not cleaned_date:
            continue

        day_num, month_str, year = cleaned_date.groups()
        date_obj = None
        for fmt in ("%d %b %Y", "%d %B %Y"):
            try:
                date_obj = datetime.strptime(f"{day_num} {month_str} {year}", fmt).date()
                break
            except ValueError:
                continue
        if not date_obj:
            continue

        for category, events in day.items():
            standard_category = CATEGORY_MAPPING.get(category)
            if not standard_category:
                continue

            group = API_TO_GROUP.get(standard_category, "DaddyLive - Other")

            for event in events:
                title_raw = event.get("event", "").strip()
                time_str = event.get("time", "00:00").strip()

                try:
                    hour, minute = map(int, time_str.split(":"))
                    dt_uk = datetime.combine(date_obj, datetime.min.time()).replace(hour=hour, minute=minute, tzinfo=tz_uk)
                    dt_utc = dt_uk.astimezone(ZoneInfo("UTC"))
                    dt_mt = dt_utc.astimezone(tz_mt)
                    dt_est = dt_utc.astimezone(tz_est)
                    final_time_block = f"{dt_uk.strftime(date_format)} UK / {dt_mt.strftime(date_format)} MT / {dt_est.strftime(date_format)} EST"
                except Exception:
                    final_time_block = f"{time_str} (invalid time)"

                full_title = f"{title_raw} ({final_time_block})"

                channels2 = event.get("channels2", [])
                channels1 = event.get("channels", [])
                if isinstance(channels2, dict):
                    channels2 = [channels2]
                if isinstance(channels1, dict):
                    channels1 = [channels1]

                chosen_list = channels2 if channels2 else channels1
                if chosen_list:
                    for ch in chosen_list:
                        cid = ch.get("channel_id")
                        if cid and cid.isdigit() and int(cid) < 1000:
                            flat.append({
                                "cid": str(cid),
                                "title": full_title,
                                "group": group
                            })
    return flat


def build_m3u(flat):
    lines = [
        '#EXTM3U url-tvg="http://drewlive24.duckdns.org:8081/DrewLive.xml.gz"',
        f'# Generated: {datetime.now(timezone.utc).isoformat()} UTC\n'
    ]

    for entry in flat:
        cid = entry["cid"]
        url = f"https://dlhd.dad/watch.php?id={cid}"
        title = re.sub(r",\s*", "-", entry["title"])
        group = entry["group"]
        logo = CATEGORY_LOGOS.get(group, "")
        tvg_id = CATEGORY_TVG_IDS.get(group, f"DL.{cid}")

        lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{title}')
        lines.extend(CUSTOM_HEADERS)
        lines.append(url)
    return "\n".join(lines)


async def fetch_json_via_browser(retries: int = 3):
    """
    Use Playwright Firefox and run window.fetch() from the page context to retrieve the JSON.
    This tends to bypass server-side blocking that rejects non-browser TLS clients.
    """
    attempt = 0
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        page = await context.new_page()

        try:
            await page.goto(SITE_ROOT, wait_until="networkidle", timeout=20000)
        except Exception:
            pass

        while attempt < retries:
            attempt += 1
            print(f"🌐 Browser-fetch attempt {attempt}/{retries} for {EVENTS_URL} ...")
            try:
                result = await page.evaluate(
                    """async (url) => {
                        try {
                            const resp = await fetch(url, {
                                method: 'GET',
                                credentials: 'include',
                                headers: {
                                    'Accept': 'application/json, text/plain, */*',
                                    'Sec-Fetch-Site': 'same-origin',
                                    'Sec-Fetch-Mode': 'cors',
                                    'Sec-Fetch-Dest': 'empty'
                                }
                            });
                            const text = await resp.text();
                            return { status: resp.status, text: text };
                        } catch (e) {
                            return { error: String(e) };
                        }
                    }""",
                    EVENTS_URL
                )

                if not result:
                    print("⚠️ No response from page.evaluate()")
                    await asyncio.sleep(1)
                    continue

                if "error" in result:
                    print("❌ fetch() error inside browser:", result["error"])
                    await asyncio.sleep(1)
                    continue

                status = result.get("status")
                text = result.get("text", "")

                if not text or text.strip() == "":
                    print(f"⚠️ Empty response text (status={status}). Retrying...")
                    await asyncio.sleep(1)
                    continue

                try:
                    parsed = json.loads(text)
                    await browser.close()
                    return parsed
                except json.JSONDecodeError:
                    print("❌ Response is not valid JSON. First 500 chars of response:")
                    print(text[:500].replace("\n", " ") )
                    await asyncio.sleep(1)
                    continue

            except Exception as e:
                print("❌ Unexpected error during browser fetch:", e)
                await asyncio.sleep(1)
                continue

        await browser.close()
    return None


async def main():
    json_data = await fetch_json_via_browser(retries=4)
    if not json_data:
        print("⚠️ Could not retrieve schedule data. Exiting.")
        return

    flat_list = flatten_events(json_data)
    if not flat_list:
        print("⚠️ No valid events found. Exiting.")
        return

    playlist = build_m3u(flat_list)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(playlist)

    print(f"\n✅ Finished writing to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
