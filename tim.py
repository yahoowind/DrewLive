import re
import time
from datetime import datetime
import requests

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
EPG_URL = "https://zipline.nocn.ddnsfree.com/u/merged2_epg.xml.gz"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def inject_group_and_tvgid(extinf_line):
    # Remove any existing tvg-id or group-title to avoid duplicates
    extinf_line = re.sub(r'tvg-id="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'group-title="[^"]*"', '', extinf_line)
    # Clean up any weird formatting if needed
    extinf_line = re.sub(r'(#EXTINF:-1)\s+-1\s+', r'\1 ', extinf_line)
    # Inject your forced group and tvg-id
    return extinf_line.replace(
        "#EXTINF:-1",
        f'#EXTINF:-1 tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"',
        1
    )

def main():
    url = f"{UPSTREAM_URL}?_={int(time.time())}"
    response = requests.get(url)
    response.raise_for_status()  # Fail if request failed

    content = response.text
    lines = content.splitlines()

    output_lines = []
    first_line = True

    for line in lines:
        if first_line:
            # Replace the first line with your own #EXTM3U header referencing the EPG URL
            output_lines.append(f'#EXTM3U url-tvg="{EPG_URL}"')
            first_line = False
            continue
        if line.startswith("#EXTINF:-1"):
            output_lines.append(inject_group_and_tvgid(line))
        else:
            output_lines.append(line)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"[💾] Playlist updated -> {OUTPUT_FILE}")
    print(f"[⏰] Updated at: {datetime.now()}")

if __name__ == "__main__":
    main()
