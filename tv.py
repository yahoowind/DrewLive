import asyncio
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
import re
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
    "/ppv": "PPV",
    "/events": "Events"
}

SPORTS_GROUPS = {"MLB", "NFL", "NCAAF", "PPV", "NBA", "WNBA", "NCAAB", "Soccer"}

def extract_real_m3u8(url: str):
    """Extract the actual .m3u8 URL even if wrapped in a ping.gif mu= parameter"""
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
    """Scrape /tv section, returning a dict {title: stream_url}"""
    urls_dict = {}
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🔄 Loading /tv channel list...")
        await page.goto(CHANNEL_LIST_URL, timeout=60000)
        links = await page.locator("ol.list-group a").all()
        hrefs = [(await link.get_attribute("href"), await link.text_content()) for link in links if await link.get_attribute("href")]
        await page.close()

        for href, title_raw in hrefs:
            full_url = BASE_URL + href
            title = " - ".join(line.strip() for line in title_raw.splitlines() if line.strip())
            print(f"🎯 Scraping TV page: {full_url}")
            stream_url = None
            for quality in ["SD", "HD"]:
                new_page = await context.new_page()

                async def handle_response(response):
                    nonlocal stream_url
                    real = extract_real_m3u8(response.url)
                    if real and not stream_url:
                        # append timestamp to avoid caching
                        stream_url = f"{real}?t={int(datetime.utcnow().timestamp())}"

                new_page.on("response", handle_response)
                await new_page.goto(full_url)
                try:
                    await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
                except:
                    pass
                await asyncio.sleep(4)
                await new_page.close()

                if stream_url:
                    urls_dict[title] = stream_url
                    print(f"✅ {quality}: {stream_url}")
                    break
            if not stream_url:
                print(f"❌ {title} not found")
        await browser.close()
    return urls_dict

async def scrape_section_urls(context, section_path, group_name):
    """Scrape sports/event sections and return list of (url, group, title)"""
    urls = []
    page = await context.new_page()
    section_url = BASE_URL + section_path
    print(f"\n📁 Loading section: {section_url}")
    await page.goto(section_url, timeout=60000)
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
                    stream_url = f"{real}?t={int(datetime.utcnow().timestamp())}"

            new_page.on("response", handle_response)
            await new_page.goto(full_url, timeout=60000)
            try:
                await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
            except:
                pass
            await asyncio.sleep(4)
            await new_page.close()

            if stream_url:
                urls.append((stream_url, group_name, f"{title} {quality}"))
                print(f"✅ {quality}: {stream_url}")
                break
            else:
                print(f"❌ {quality} not found")
    return urls

async def scrape_all_append_sections():
    """Scrape all sports/event sections"""
    all_urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        for section_path, group_name in SECTIONS_TO_APPEND.items():
            urls = await scrape_section_urls(context, section_path, group_name)
            all_urls.extend(urls)

        await browser.close()
    return all_urls

def replace_urls_by_name(lines, tv_channels_dict):
    """Replace /tv section URLs based on tvg-name match"""
    result = []
    skip_next = False
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if line.startswith("#EXTINF"):
            match = re.search(r'tvg-name="([^"]+)"', line)
            if match:
                channel_name = match.group(1).strip()
                if channel_name in tv_channels_dict:
                    result.append(line)
                    result.append(tv_channels_dict[channel_name])
                    skip_next = True
                    continue
        result.append(line)
    return result

def append_new_streams(lines, new_urls_with_groups):
    """Append sports section streams with logos and correct tvg-name"""
    # Remove old sports entries
    cleaned_lines = []
    skip_next = False
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if line.startswith("#EXTINF:-1") and any(f'TheTVApp - {sport}' in line for sport in SPORTS_GROUPS):
            skip_next = True
            continue
        cleaned_lines.append(line)
    lines = cleaned_lines

    for url, group, title in new_urls_with_groups:
        tvg_name = title  # matches name after comma
        if group == "MLB":
            ext = f'#EXTINF:-1 tvg-id="MLB.Baseball.Dummy.us" tvg-name="{tvg_name}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/Baseball-2.png" group-title="TheTVApp - MLB",{title}'
        elif group == "PPV":
            ext = f'#EXTINF:-1 tvg-id="PPV.EVENTS.Dummy.us" tvg-name="{tvg_name}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/PPV.png" group-title="TheTVApp - PPV",{title}'
        elif group == "NFL":
            ext = f'#EXTINF:-1 tvg-id="NFL.Dummy.us" tvg-name="{tvg_name}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/NFL.png" group-title="TheTVApp - NFL",{title}'
        elif group == "NCAAF":
            ext = f'#EXTINF:-1 tvg-id="NCAA.Football.Dummy.us" tvg-name="{tvg_name}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/CFB.png" group-title="TheTVApp - NCAAF",{title}'
        else:
            ext = f'#EXTINF:-1 tvg-name="{tvg_name}" group-title="TheTVApp - {group}",{title}'
        lines.append(ext)
        lines.append(url)

    if not lines or lines[0].strip() != "#EXTM3U":
        lines.insert(0, "#EXTM3U")
    return lines

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    print("🔧 Replacing /tv stream URLs in site order...")
    tv_new_urls = await scrape_tv_urls()
    if not tv_new_urls:
        print("❌ No TV URLs scraped.")
        return

    updated_lines = replace_urls_by_name(lines, tv_new_urls)

    print("\n📦 Scraping all sports sections (NBA, NFL, NCAAF, MLB, PPV, etc)...")
    append_new_urls = await scrape_all_append_sections()
    if append_new_urls:
        updated_lines = append_new_streams(updated_lines, append_new_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))

    print(f"\n✅ {M3U8_FILE} updated: /tv site order preserved, sports refreshed, SD/HD appended, logos injected, tvg-name matches display name.")

if __name__ == "__main__":
    asyncio.run(main())
