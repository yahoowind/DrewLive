import requests
import re
from datetime import datetime

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"

REMOVE_PATTERNS = [
    re.compile(r'^# (Last forced update|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    return res.text.splitlines()

def should_remove_line(line):
    return any(pat.match(line) for pat in REMOVE_PATTERNS)

def process_and_write_playlist(lines):
    output_lines = [
        f'#EXTM3U url-tvg="{EPG_URL}"',
        f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    ]

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or should_remove_line(line):
            i += 1
            continue

        if line.startswith("#EXTINF"):
            output_lines.append(line)
            if i + 1 < len(lines):
                url_line = lines[i + 1].strip()
                output_lines.append(url_line)
                i += 2
            else:
                i += 1
        else:
            i += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"[✅] {OUTPUT_FILE} updated safely.")

if __name__ == "__main__":
    playlist = fetch_playlist()
    process_and_write_playlist(playlist)
