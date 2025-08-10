from playwright.sync_api import sync_playwright
import time
import re

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
EPG_URL = "https://zipline.nocn.ddnsfree.com/u/merged2_epg.xml.gz"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def inject_group_and_tvgid(extinf_line):
    extinf_line = re.sub(r'tvg-id="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'group-title="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'(#EXTINF:-1)\s+-1\s+', r'\1 ', extinf_line)
    return extinf_line.replace(
        "#EXTINF:-1",
        f'#EXTINF:-1 tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"',
        1
    )

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(f"{UPSTREAM_URL}?_={int(time.time())}", wait_until="networkidle")
    text = page.content()

    # Extract text inside <pre> or body
    lines = text.splitlines()

    output_lines = []
    first_line = True
    for line in lines:
        if first_line:
            output_lines.append(f'#EXTM3U url-tvg="{EPG_URL}"')
            first_line = False
            continue
        if line.startswith("#EXTINF:-1"):
            output_lines.append(inject_group_and_tvgid(line))
        else:
            output_lines.append(line)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    browser.close()
