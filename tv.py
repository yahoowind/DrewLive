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
    "/ppv": "PPV"
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

        await page.goto(CHANNEL_LIST_URL, timeout=60000)
        links = await page.locator("ol.list-group a").all()
        hrefs = [await link.get_attribute("href") for link in links if await link.get_attribute("href")]
        await page.close()

        for href in hrefs:
            full_url = BASE_URL + href
            # Just grab SD or HD URL, whichever is available, prioritizing HD
            stream_url = None
            new_page = await context.new_page()

            async def handle_response(response):
                nonlocal stream_url
                real = extract_real_m3u8(response.url)
                if real and not stream_url:
                    stream_url = real

            new_page.on("response", handle_response)
            await new_page.goto(full_url)
            # Try HD first
            try:
                await new_page.get_by_text("Load HD Stream", exact=True).click(timeout=5000)
            except:
                # fallback to SD
                try:
                    await new_page.get_by_text("Load SD Stream", exact=True).click(timeout=5000)
                except:
                    pass
            await asyncio.sleep(4)
            await new_page.close()

            if stream_url:
                urls.append(stream_url)
            else:
                urls.append("")  # placeholder if no URL found

        await browser.close()
    return urls

async def scrape_section_urls(context, section_path, group_name):
    urls = []
    page = await context.new_page()
    section_url = BASE_URL + section_path
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
        for quality in ["HD", "SD"]:  # HD prioritized first
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
                urls.append((stream_url, group_name, title))
                break  # stop after first successful quality found

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
    header = []
    tv = []
    sports_and_others = []

    i = 0
    # Capture header until first EXTINF of TV section
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            break
        header.append(line)
        i += 1

    # Capture TV section (pairs of EXTINF + URL lines)
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

    # The rest are sports and others - discard old sports in rebuild
    while i < len(lines):
        sports_and_others.append(lines[i].strip())
        i += 1

    return header, tv, sports_and_others

def rebuild_m3u(header, tv_lines, tv_urls, sports_urls):
    result = []
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Header intact
    result.extend(header)

    # Rebuild TV section: keep all EXTINF lines untouched,
    # replace only URLs with new scraped URLs in order
    url_idx = 0
    for i in range(len(tv_lines)):
        line = tv_lines[i]
        if line.startswith("#EXTINF:"):
            result.append(line)
        else:
            # URL line
            if url_idx < len(tv_urls) and tv_urls[url_idx]:
                result.append(tv_urls[url_idx])
            else:
                # fallback to original if no new url
                result.append(line)
            url_idx += 1

    # Append fresh sports entries only (old sports removed)
    for url, group, title in sports_urls:
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

    # Do NOT append old sports_and_others lines (old sports removed)

    return result

async def main():
    if not Path(M3U8_FILE).exists():
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    header, tv_lines, _ = parse_m3u_sections(lines)

    tv_urls = await scrape_tv_urls()
    if not tv_urls:
        return

    sports_urls = await scrape_all_append_sections()

    new_m3u = rebuild_m3u(header, tv_lines, tv_urls, sports_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(new_m3u))

if __name__ == "__main__":
    asyncio.run(main())
