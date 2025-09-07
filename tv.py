import asyncio
import urllib.parse
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

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
    "/ppv": "PPV",
    "/events": "Events"
}

def extract_real_m3u8(url: str):
    """Extracts the real .m3u8 URL from ping.gif or direct links."""
    if "ping.gif" in url and "mu=" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        mu = qs.get("mu", [None])[0]
        if mu:
            return urllib.parse.unquote(mu)
    if ".m3u8" in url:
        return url
    return None

async def scrape_tv_urls():
    """Scrape main TV section."""
    urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔄 Loading /tv channel list...")
        await page.goto(CHANNEL_LIST_URL)
        links = await page.locator("ol.list-group a").all()
        hrefs_and_titles = [(await link.get_attribute("href"), await link.text_content())
                            for link in links if await link.get_attribute("href")]
        await page.close()

        for href, title_raw in hrefs_and_titles:
            full_url = BASE_URL + href
            title = " - ".join(line.strip() for line in title_raw.splitlines() if line.strip())
            print(f"🎯 Scraping TV page: {full_url}")

            for quality in ["SD", "HD"]:
                stream_url = None
                new_page = await context.new_page()

                async def handle_response(response):
                    nonlocal stream_url
                    real = extract_real_m3u8(response.url)
                    if real and not stream_url:
                        stream_url = real

                new_page.on("response", handle_response)
                await new_page.goto(full_url)

                try:
                    await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
                except:
                    pass

                await asyncio.sleep(4)
                await new_page.close()

                if stream_url:
                    urls.append((stream_url, "TV", f"{title} {quality}"))
                    print(f"✅ {quality}: {stream_url}")
                else:
                    print(f"❌ {quality} not found")

        await browser.close()
    return urls

async def scrape_section_urls(context, section_path, group_name):
    """Scrape other sports/PPV sections."""
    urls = []
    page = await context.new_page()
    section_url = BASE_URL + section_path
    print(f"\n📁 Loading section: {section_url}")
    await page.goto(section_url)
    links = await page.locator("ol.list-group a").all()
    hrefs_and_titles = []

    for link in links:
        href = await link.get_attribute("href")
        title_raw = await link.text_content()
        if href and title_raw:
            title = " - ".join(line.strip() for line in title_raw.splitlines() if line.strip())
            hrefs_and_titles.append((href, title))
    await page.close()

    for href, title in hrefs_and_titles:
        full_url = BASE_URL + href
        print(f"🎯 Scraping {group_name}: {title}")

        for quality in ["SD", "HD"]:
            stream_url = None
            new_page = await context.new_page()

            async def handle_response(response):
                nonlocal stream_url
                real = extract_real_m3u8(response.url)
                if real and not stream_url:
                    stream_url = real

            new_page.on("response", handle_response)
            await new_page.goto(full_url)

            try:
                await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
            except:
                pass

            await asyncio.sleep(4)
            await new_page.close()

            if stream_url:
                urls.append((stream_url, group_name, f"{title} {quality}"))
                print(f"✅ {quality}: {stream_url}")
            else:
                print(f"❌ {quality} not found")

    return urls

async def scrape_all_append_sections():
    """Scrape all additional sections."""
    all_urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        for section_path, group_name in SECTIONS_TO_APPEND.items():
            urls = await scrape_section_urls(context, section_path, group_name)
            all_urls.extend(urls)

        await browser.close()
    return all_urls

def clean_m3u_header(lines):
    """Ensure correct M3U header."""
    lines = [line for line in lines if not line.strip().startswith("#EXTM3U")]
    timestamp = int(datetime.utcnow().timestamp())
    lines.insert(0, f'#EXTM3U url-tvg="http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz" # Updated: {timestamp}')
    return lines

def replace_tv_urls(lines, tv_urls):
    """Replace existing TV URLs in place while preserving #EXTINF metadata."""
    updated = []
    tv_idx = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("http") and tv_idx < len(tv_urls):
            group, title = tv_urls[tv_idx][1], tv_urls[tv_idx][2]
            # Preserve EXTINF line before URL
            if i > 0 and lines[i - 1].startswith("#EXTINF"):
                extinf = lines[i - 1]
                if "," in extinf:
                    parts = extinf.split(",")
                    parts[-1] = title
                    extinf = ",".join(parts)
                updated[-1] = extinf
            updated.append(tv_urls[tv_idx][0])
            tv_idx += 1
        else:
            updated.append(line)
        i += 1
    return updated

def append_new_streams(lines, new_urls_with_groups):
    """Append new streams while avoiding duplicates."""
    existing = set()
    for line in lines:
        if line.startswith("#EXTINF"):
            title = line.split(",")[-1].strip()
            group = line.split('group-title="')[1].split('"')[0] if 'group-title="' in line else ""
            existing.add((group, title))

    for url, group, title in new_urls_with_groups:
        key = (group, title)
        if key in existing:
            continue
        # Build EXTINF
        if group == "MLB":
            ext = f'#EXTINF:-1 tvg-id="MLB.Baseball.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/Baseball-2.png" group-title="TheTVApp - MLB",{title}'
        elif group == "PPV":
            ext = f'#EXTINF:-1 tvg-id="PPV.EVENTS.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/PPV.png" group-title="TheTVApp - PPV",{title}'
        elif group == "NFL":
            ext = f'#EXTINF:-1 tvg-id="NFL.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/NFL.png" group-title="TheTVApp - NFL",{title}'
        elif group == "NCAAF":
            ext = f'#EXTINF:-1 tvg-id="NCAA.Football.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/CFB.png" group-title="TheTVApp - NCAAF",{title}'
        else:
            ext = f'#EXTINF:-1 tvg-name="{title}" group-title="TheTVApp - {group}",{title}'
        lines.append(ext)
        lines.append(url)
    return lines

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    lines = clean_m3u_header(lines)

    print("🔧 Replacing /tv stream URLs...")
    tv_new_urls = await scrape_tv_urls()
    if not tv_new_urls:
        print("❌ No TV URLs scraped.")
        return
    lines = replace_tv_urls(lines, tv_new_urls)

    print("\n📦 Scraping all other sections...")
    append_new_urls = await scrape_all_append_sections()
    if append_new_urls:
        lines = append_new_streams(lines, append_new_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ {M3U8_FILE} fully refreshed and working.")

if __name__ == "__main__":
    asyncio.run(main())
