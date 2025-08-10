import requests
import re
import os
from datetime import datetime

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
EPG_URL = "https://zipline.nocn.ddnsfree.com/u/merged2_epg.xml.gz"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def inject_group_and_tvgid(extinf_line):
    # Remove any existing tvg-id and group-title
    extinf_line = re.sub(r'tvg-id="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'group-title="[^"]*"', '', extinf_line)

    # Normalize EXTINF formatting
    extinf_line = re.sub(r'(#EXTINF:-1)\s+-1\s+', r'\1 ', extinf_line)

    # Insert forced group & tvg-id
    extinf_line = extinf_line.replace(
        "#EXTINF:-1",
        f'#EXTINF:-1 tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"',
        1
    )

    # Cleanup spaces
    extinf_line = re.sub(r'\s+', ' ', extinf_line).strip()
    extinf_line = re.sub(r' ,', ',', extinf_line)
    return extinf_line

def fetch_upstream():
    print("[🔁] Fetching upstream playlist...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': '*/*',
        'Cache-Control': 'no-cache'
    }

    res = requests.get(UPSTREAM_URL, headers=headers, timeout=30)
    res.raise_for_status()
    return res.text.strip().splitlines()

def save_if_changed(content):
    new_content = "\n".join(content) + "\n"

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()
        if old_content == new_content:
            print("[ℹ️] No changes detected, skipping update.")
            return False

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[💾] Playlist updated and saved to {OUTPUT_FILE}")
    return True

def main():
    try:
        lines = fetch_upstream()
        print(f"[✅] Upstream fetched: {len(lines)} lines.")
    except requests.exceptions.RequestException as e:
        print(f"[❌] Failed to fetch upstream: {e}")
        return

    output_lines = [
        f'#EXTM3U url-tvg="{EPG_URL}"',
        f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    ]

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF:-1"):
            output_lines.append(inject_group_and_tvgid(line))
        else:
            output_lines.append(line)

    save_if_changed(output_lines)

if __name__ == "__main__":
    main()
