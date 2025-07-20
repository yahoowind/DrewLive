import asyncio
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
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

async def scrape_tv_urls():
    urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🔄 Loading /tv channel list...")
        await page.goto(CHANNEL_LIST_URL, timeout=60000)
        links = await page.locator("ol.list-group a").all()
        hrefs = [await link.get_attribute("href") for link in links if await link.get_attribute("href")]
        await page.close()

        for href in hrefs:
            full_url = BASE_URL + href
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
                    print(f"✅ {quality}: {stream_url}")
                    urls.append(stream_url)
                else:
                    print(f"❌ {quality} not found")

        await browser.close()
    return urls

async def scrape_section_urls(context, section_path, group_name):
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
                    stream_url = real

            new_page.on("response", handle_response)
            await new_page.goto(full_url, timeout=60000)

            try:
                await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
            except:
                pass

            await asyncio.sleep(4)
            await new_page.close()

            if stream_url:
                print(f"✅ {quality}: {stream_url}")
                urls.append((stream_url, group_name, title))
            else:
                print(f"❌ {quality} not found")

    return urls

async def scrape_all_append_sections():
    all_urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()

        for section_path, group_name in SECTIONS_TO_APPEND.items():
            urls = await scrape_section_urls(context, section_path, group_name)
            all_urls.extend(urls)

        await browser.close()
    return all_urls

def parse_m3u_sections(lines):
    sections = {
        "header": [],
        "tv": [],
        "other": []
    }
    current_section = "header"
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if current_section == "header":
            if line.startswith("#EXTINF:"):
                current_section = "tv"
                continue
            else:
                sections["header"].append(line)
                i += 1
                continue

        if current_section == "tv":
            if line.startswith("#EXTINF:"):
                sections["tv"].append(line)
                i += 1
                if i < len(lines):
                    sections["tv"].append(lines[i].strip())
            else:
                sections["other"].append(line)
            i += 1
        else:
            sections["other"].append(line)
            i += 1

    return sections

def rebuild_m3u_from_sections(sections, tv_urls, sports_urls):
    result = []

    # Get today's date string (UTC)
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Write header
    if "header" in sections and sections["header"]:
        result.extend(sections["header"])
    else:
        result.append("#EXTM3U")

    # Rebuild tv section with new URLs
    if "tv" in sections:
        tv_lines = sections["tv"]
        url_idx = 0
        for i in range(len(tv_lines)):
            line = tv_lines[i]
            if not line.startswith("#EXTINF:") and line.strip().startswith("http"):
                if url_idx < len(tv_urls):
                    result.append(tv_urls[url_idx])
                    url_idx += 1
                else:
                    result.append(line)
            else:
                result.append(line)

    # Append sports section streams filtered by date
    for url, group, title in sports_urls:
        # Skip entries with a date that is not today (flexible for common date formats)
        # Checks if title contains a date string that is NOT today's date
        if any(d in title for d in ["202", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
            if today_str not in title:
                continue  # skip old dated entry

        if group == "MLB":
            ext = f'#EXTINF:-1 tvg-id="MLB.Baseball.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/Baseball-2.png" group-title="MLB",{title}'
        elif group == "PPV":
            ext = f'#EXTINF:-1 tvg-id="PPV.EVENTS.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/PPV.png" group-title="PPV",{title}'
        else:
            ext = f'#EXTINF:-1 group-title="{group}",{title}'
        result.append(ext)
        result.append(url)

    # Append other leftover lines
    if "other" in sections:
        result.extend(sections["other"])

    return result

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    print("🔧 Parsing M3U sections...")
    sections = parse_m3u_sections(lines)

    print("🔄 Scraping /tv section URLs...")
    tv_urls = await scrape_tv_urls()
    if not tv_urls:
        print("❌ No TV URLs scraped, aborting.")
        return

    print("\n📦 Scraping sports and other sections...")
    sports_urls = await scrape_all_append_sections()

    print("\n🔧 Rebuilding playlist with updated URLs...")
    updated_lines = rebuild_m3u_from_sections(sections, tv_urls, sports_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))

    print(f"\n✅ {M3U8_FILE} updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
