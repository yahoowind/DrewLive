import asyncio
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime

M3U8_FILE = "TheTVApp.m3u8"
BASE_URL = "https://thetvapp.to"
CHANNEL_LIST_URL = f"{BASE_URL}/tv"

SECTIONS_TO_APPEND = {
    "/nba": "NBA",
    "/mlb": "MLB",
    "/wnba": "WNBA",
    "/nfl": "NFL",
    "/ncaaf": "NCAAF",
    "/ncaab": "NCAAB",
    "/soccer": "Soccer",
    "/ppv": "PPV"
}

# ---------- Helpers ----------

def extract_real_m3u8(url: str):
    if "ping.gif" in url and "mu=" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        mu = qs.get("mu", [None])[0]
        if mu:
            return urllib.parse.unquote(mu)
    if ".m3u8" in url:
        return url
    return None

async def fetch_stream_url(context, full_url: str, qualities=("HD", "SD"), wait_seconds=4, retries=2):
    """
    Visit a channel page, try HD then SD buttons, capture first m3u8.
    Retries whole flow 'retries' times if nothing captured.
    """
    for attempt in range(1, retries + 1):
        stream_url = None
        page = await context.new_page()

        async def handle_response(response):
            nonlocal stream_url
            if stream_url:
                return
            real = extract_real_m3u8(response.url)
            if real:
                stream_url = real

        page.on("response", handle_response)

        try:
            await page.goto(full_url, timeout=60000)
        except PlaywrightTimeoutError:
            print(f"❌ Timeout navigating to {full_url} (attempt {attempt}/{retries})")
            await page.close()
            continue
        except Exception as e:
            print(f"❌ Error navigating to {full_url}: {e} (attempt {attempt}/{retries})")
            await page.close()
            continue

        # Try qualities in order
        for q in qualities:
            if stream_url:
                break
            button_label = f"Load {q} Stream"
            try:
                await page.get_by_text(button_label, exact=True).click(timeout=5000)
                print(f"   🔘 Clicked {button_label}")
                await asyncio.sleep(wait_seconds)
            except PlaywrightTimeoutError:
                print(f"   ⚠️ {button_label} not found (timeout)")
            except Exception:
                print(f"   ⚠️ {button_label} click failed")

        # Wait a little more in case late network requests fire
        if not stream_url:
            await asyncio.sleep(1.5)

        await page.close()

        if stream_url:
            if attempt > 1:
                print(f"   ✅ Recovered stream after retry (attempt {attempt})")
            return stream_url
        else:
            print(f"   🚫 No stream captured on attempt {attempt}/{retries}")

    print(f"   ❌ Failed to capture any m3u8 for {full_url} after {retries} attempts")
    return None

# ---------- TV Section Scrape ----------

async def scrape_tv_urls():
    print("📺 Starting TV section scrape...")
    urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        page = await context.new_page()
        try:
            await page.goto(CHANNEL_LIST_URL, timeout=60000)
        except Exception as e:
            print(f"❌ Could not load TV list page: {e}")
            await browser.close()
            return []

        links = await page.locator("ol.list-group a").all()
        hrefs = []
        for link in links:
            href = await link.get_attribute("href")
            if href:
                hrefs.append(href)
        print(f"🔎 Found {len(hrefs)} TV channel links")
        await page.close()

        for idx, href in enumerate(hrefs, start=1):
            full_url = BASE_URL + href
            print(f"\n➡️ [{idx}/{len(hrefs)}] Visiting TV channel: {full_url}")
            stream_url = await fetch_stream_url(context, full_url)
            if stream_url:
                print(f"   ✅ Captured: {stream_url}")
                urls.append(stream_url)
            else:
                print("   ⚠️ Appending empty placeholder (no captured URL)")
                urls.append("")  # Keep placeholder to preserve ordering

        await browser.close()

    good = sum(1 for u in urls if u)
    print(f"\n✅ Completed TV scrape: {good}/{len(urls)} URLs captured")
    return urls

# ---------- Sports / Other Sections Scrape ----------

async def scrape_section_urls(context, section_path, group_name):
    print(f"\n🏷️  Scraping section {group_name} ({section_path})")
    result = []
    page = await context.new_page()
    section_url = BASE_URL + section_path
    try:
        await page.goto(section_url, timeout=60000)
    except Exception as e:
        print(f"❌ Could not load {section_url}: {e}")
        await page.close()
        return result

    links = await page.locator("ol.list-group a").all()
    entries = []
    for link in links:
        href = await link.get_attribute("href")
        title_raw = await link.text_content()
        if href and title_raw:
            title = " - ".join(line.strip() for line in title_raw.splitlines() if line.strip())
            entries.append((href, title))
    await page.close()
    print(f"   🔎 Found {len(entries)} entries in {group_name}")

    for idx, (href, title) in enumerate(entries, start=1):
        full_url = BASE_URL + href
        print(f"   → [{idx}/{len(entries)}] {group_name} item: {title}")
        stream_url = await fetch_stream_url(context, full_url)
        if stream_url:
            print(f"      ✅ {group_name} stream captured")
            result.append((stream_url, group_name, title))
        else:
            print(f"      🚫 No stream for this item (skipped)")

    print(f"   ✅ Finished {group_name}: {len(result)} usable streams")
    return result

async def scrape_all_append_sections():
    print("\n⚽ Starting sports/other sections scrape...")
    combined = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        for section_path, group_name in SECTIONS_TO_APPEND.items():
            section_results = await scrape_section_urls(context, section_path, group_name)
            combined.extend(section_results)

        await browser.close()

    print(f"✅ All extra sections done: {len(combined)} total new sports/other streams")
    return combined

# ---------- M3U Handling ----------

def parse_m3u_sections(lines):
    header = []
    tv = []
    sports_and_others = []

    i = 0
    # header
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            break
        header.append(line)
        i += 1

    # tv section (assumes contiguous EXTINF/URL pairs)
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            tv.append(line)
            i += 1
            if i < len(lines):
                tv.append(lines[i].strip())
            i += 1
        else:
            break

    # rest (old sports/etc) – we discard later
    while i < len(lines):
        sports_and_others.append(lines[i].strip())
        i += 1

    return header, tv, sports_and_others

def rebuild_m3u(header, tv_lines, tv_urls, sports_urls):
    result = []
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    result.extend(header)

    # Rebuild TV section: keep metadata (#EXTINF) exactly, swap URL lines if new available
    url_idx = 0
    for i, line in enumerate(tv_lines):
        if line.startswith("#EXTINF:"):
            result.append(line)
        else:
            # URL line position
            if url_idx < len(tv_urls) and tv_urls[url_idx]:
                result.append(tv_urls[url_idx])
            else:
                # Keep original line if we failed to fetch new one
                result.append(line)
            url_idx += 1

    # Append NEW sports only (old discarded)
    appended = 0
    for url, group, title in sports_urls:
        # Keep your date filter logic
        if today_str not in title:
            continue

        if group == "MLB":
            ext = f'#EXTINF:-1 tvg-id="MLB.Baseball.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/Baseball-2.png" group-title="MLB",{title}'
        elif group == "PPV":
            ext = f'#EXTINF:-1 tvg-id="PPV.EVENTS.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/PPV.png" group-title="PPV",{title}'
        else:
            ext = f'#EXTINF:-1 group-title="{group}",{title}'
        result.append(ext)
        result.append(url)
        appended += 1

    print(f"🧩 Appended {appended} new dated sports/other entries (filtered by today)")
    return result

# ---------- Main ----------

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ M3U file not found: {M3U8_FILE}")
        return

    print(f"📂 Loading existing M3U: {M3U8_FILE}")
    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    header, tv_lines, _old_sports = parse_m3u_sections(lines)
    print(f"📑 Parsed sections: header={len(header)} lines, TV section lines={len(tv_lines)}, old sports discarded={len(_old_sports)}")

    tv_urls = await scrape_tv_urls()

    # NEVER bail out just because TV urls list is empty
    if not any(tv_urls):
        print("⚠️ No new TV URLs captured; will keep existing ones.")

    sports_urls = await scrape_all_append_sections()

    new_m3u = rebuild_m3u(header, tv_lines, tv_urls, sports_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(new_m3u) + "\n")

    print(f"\n✅ DONE. Updated {M3U8_FILE}")
    print(f"   TV URLs fetched: {sum(1 for u in tv_urls if u)} / {len(tv_urls)}")
    print(f"   Sports/others fetched (before date filter): {len(sports_urls)}")
    print("🎯 Script completed without early exit.")

if __name__ == "__main__":
    asyncio.run(main())
