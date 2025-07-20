import asyncio
import urllib.parse
from pathlib import Path
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
    if "ping.gif" in url and "mu=" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        mu = qs.get("mu", [None])[0]
        if mu:
            return urllib.parse.unquote(mu)
    if ".m3u8" in url:
        return url
    return None

def normalize_title(title: str):
    title = title.lower()
    for tag in [" (hd)", " (sd)"]:
        title = title.replace(tag, "")
    return title.strip()

async def scrape_tv_urls():
    results = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔄 Loading TV channels...")
        await page.goto(CHANNEL_LIST_URL, timeout=60000)
        links = await page.locator("ol.list-group a").all()

        for link in links:
            href = await link.get_attribute("href")
            title_raw = await link.text_content()
            if not href or not title_raw:
                continue
            title = " - ".join(line.strip() for line in title_raw.splitlines() if line.strip())
            full_url = BASE_URL + href
            print(f"🎯 {title} - {full_url}")

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
                    title_q = f"{title} ({quality})"
                    results.append((stream_url, quality, title_q))

        await browser.close()
    return results

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
                full_title = f"{title} ({quality})"
                urls.append((stream_url, group_name, full_title))
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

def replace_tv_section(lines, tv_streams):
    result = []
    stream_idx = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:-1") and stream_idx < len(tv_streams):
            url, quality, title = tv_streams[stream_idx]
            parts = line.split(",")
            new_extinf = ",".join(parts[:-1]) + "," + title
            result.append(new_extinf)
            result.append(url)
            stream_idx += 1
            i += 2
        else:
            result.append(line)
            i += 1
    return result

def append_new_streams(lines, new_urls_with_groups):
    lines = [line for line in lines if line.strip() != "#EXTM3U"]

    clean_lines = []
    skip_next = False
    for line in lines:
        if skip_next:
            skip_next = False
            continue
        if line.startswith("#EXTINF:-1") and any(g in line for g in ["MLB", "PPV"]):
            skip_next = True
            continue
        clean_lines.append(line)

    existing_titles = set()
    for i in range(0, len(clean_lines) - 1, 2):
        if clean_lines[i].startswith("#EXTINF:-1"):
            title = clean_lines[i].split(",")[-1].strip()
            existing_titles.add(normalize_title(title))

    for url, group, title in new_urls_with_groups:
        if normalize_title(title) in existing_titles:
            continue
        if group == "MLB":
            ext = f'#EXTINF:-1 tvg-id="MLB.Baseball.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/Baseball-2.png" group-title="MLB",{title}'
        elif group == "PPV":
            ext = f'#EXTINF:-1 tvg-id="PPV.EVENTS.Dummy.us" tvg-name="{title}" tvg-logo="http://drewlive24.duckdns.org:9000/Logos/PPV.png" group-title="PPV",{title}'
        else:
            ext = f'#EXTINF:-1 group-title="{group}",{title}'
        clean_lines.append(ext)
        clean_lines.append(url)
        existing_titles.add(normalize_title(title))

    clean_lines.insert(0, "#EXTM3U")
    return clean_lines

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    print("🔧 Replacing /tv streams...")
    tv_new_urls = await scrape_tv_urls()
    updated_lines = replace_tv_section(lines, tv_new_urls)

    print("\n📦 Scraping additional sections...")
    append_urls = await scrape_all_append_sections()
    updated_lines = append_new_streams(updated_lines, append_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))

    print("\n✅ Playlist updated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
