import requests
import re
import os
import time
from datetime import datetime

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def inject_group_and_tvgid(extinf_line):
    # Remove old tvg-id/group-title and insert forced ones
    extinf_line = re.sub(r'tvg-id="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'group-title="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'(#EXTINF:-1)\s+-1\s+', r'\1 ', extinf_line)
    return extinf_line.replace(
        "#EXTINF:-1",
        f'#EXTINF:-1 tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"',
        1
    )

def main():
    print("[🔁] Fetching latest upstream playlist...")
    try:
        # Add cache-buster so we never get a stale copy
        url_with_cachebuster = f"{UPSTREAM_URL}?_={int(time.time())}"
        res = requests.get(
            url_with_cachebuster,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            timeout=30
        )
        res.raise_for_status()
        lines = res.text.splitlines()
        print(f"[✅] Fresh playlist pulled: {len(lines)} lines.")
    except Exception as e:
        print(f"[❌] Failed to fetch upstream: {e}")
        return

    output_lines = []
    first_line = True

    for line in lines:
        if first_line:
            # Replace first line with EPG info
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
