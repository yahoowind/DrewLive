import requests
import re
from datetime import datetime

UPSTREAM_URL = "https://pigzillaaa-scraper.vercel.app/tims"
EPG_URL = "https://tinyurl.com/DrewLive002-epg"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def force_group_and_tvgid(line):
    if line.startswith("#EXTINF"):
        # Remove existing tvg-id and group-title attributes
        line = re.sub(r'tvg-id="[^"]*"', '', line)
        line = re.sub(r'group-title="[^"]*"', '', line)

        # Insert new attributes
        line = line.replace('#EXTINF:', f'#EXTINF:-1 tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}" ', 1)
    return line.strip()

def main():
    print("[🔁] Fetching upstream playlist...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': '*/*'
    }

    try:
        res = requests.get(UPSTREAM_URL, headers=headers, timeout=15)
        res.raise_for_status()
        lines = res.text.strip().splitlines()
        print(f"[✅] Upstream fetched successfully, {len(lines)} lines.")
    except requests.exceptions.RequestException as e:
        print(f"[❌] Failed to fetch upstream: {e}")
        # Optional: fallback to a backup file
        # try:
        #     with open("backup.m3u8", "r", encoding="utf-8") as f:
        #         lines = f.read().splitlines()
        #         print("[⚠️] Using backup.m3u8")
        # except Exception as e2:
        #     print(f"[❌] No backup available: {e2}")
        return

    output_lines = [
        f'#EXTM3U url-tvg="{EPG_URL}"',
        f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    ]

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        output_lines.append(force_group_and_tvgid(line))

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines) + "\n")
        print(f"[💾] Playlist saved to {OUTPUT_FILE} with group-title='{FORCED_GROUP}' and tvg-id='{FORCED_TVG_ID}'.")
    except Exception as e:
        print(f"[❌] Failed to write playlist: {e}")

if __name__ == "__main__":
    main()
