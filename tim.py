import re
import time
from datetime import datetime
import requests

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/tims"
EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"
FORCED_TVG_ID = "24.7.Dummy.us"

def inject_group_and_tvgid(extinf_line):
    # Only inject tvg-id if missing
    if 'tvg-id=' not in extinf_line:
        extinf_line = extinf_line.replace(
            "#EXTINF:-1",
            f'#EXTINF:-1 tvg-id="{FORCED_TVG_ID}"',
            1
        )
    # Only inject group-title if missing
    if 'group-title=' not in extinf_line:
        extinf_line = extinf_line.replace(
            "#EXTINF:-1",
            f'#EXTINF:-1 group-title="{FORCED_GROUP}"',
            1
        )
    return extinf_line

def main():
    url = f"{UPSTREAM_URL}?_={int(time.time())}"
    response = requests.get(url)
    response.raise_for_status()

    content = response.text
    lines = content.splitlines()

    output_lines = []
    first_line = True
    header_handled = False

    for line in lines:
        # Handle #EXTM3U header line
        if first_line:
            if line.strip().startswith("#EXTM3U"):
                # Keep upstream header but add EPG URL as a comment (if you want)
                output_lines.append(line.strip())
                # Optionally add a separate comment line with EPG URL
                output_lines.append(f"#EXT-X-EPG-URL:{EPG_URL}")
                header_handled = True
            else:
                # No header from upstream, add our own clean one
                output_lines.append("#EXTM3U")
                output_lines.append(f"#EXT-X-EPG-URL:{EPG_URL}")
                # Also add the current line since it’s not header
                output_lines.append(line)
            first_line = False
            continue

        # Inject tvg-id and group-title if EXTINF line
        if line.startswith("#EXTINF:-1"):
            output_lines.append(inject_group_and_tvgid(line))
        else:
            output_lines.append(line)

    # Save output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"[💾] Playlist updated -> {OUTPUT_FILE}")
    print(f"[⏰] Updated at: {datetime.now()}")

if __name__ == "__main__":
    main()
