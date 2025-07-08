import requests
import re
from datetime import datetime

UPSTREAM_URL = "https://pigzillaaa-scraper.vercel.app/tims"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "Tims247.m3u8"
FORCED_GROUP = "Tims247"

TIMESTAMP_PATTERNS = [
    re.compile(r'^#EXTM3U', re.IGNORECASE),
    re.compile(r'^# Last forced update:', re.IGNORECASE),
    re.compile(r'^# Updated at', re.IGNORECASE),
    re.compile(r'^# Updated:', re.IGNORECASE),
]

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    return res.text.strip().splitlines()

def should_remove_line(line):
    return any(pat.match(line) for pat in TIMESTAMP_PATTERNS)

def force_group_title(extinf_line):
    if 'group-title="' in extinf_line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', extinf_line)
    else:
        return extinf_line.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}" ', 1)

def process_and_write_playlist(upstream_lines):
    upstream_filtered = [line.strip() for line in upstream_lines if line.strip() and not should_remove_line(line)]

    upstream_urls = []
    for i in range(len(upstream_filtered)):
        if upstream_filtered[i].startswith("#EXTINF") and i + 1 < len(upstream_filtered):
            upstream_urls.append(upstream_filtered[i + 1].strip())

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            original = f.read().splitlines()
    except FileNotFoundError:
        original = []

    filtered_original = [line for line in original if not should_remove_line(line)]

    output_lines = [
        f'#EXTM3U url-tvg="{EPG_URL}"',
        f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    ]

    url_index = 0
    i = 0
    while i < len(filtered_original):
        line = filtered_original[i].strip()

        if line.startswith("#EXTINF"):
            forced_line = force_group_title(line)
            output_lines.append(forced_line)
            if url_index < len(upstream_urls):
                output_lines.append(upstream_urls[url_index])
                url_index += 1
                i += 2
            else:
                i += 1
        else:
            output_lines.append(line)
            i += 1

    cleaned_output = []
    seen_update = 0
    for line in output_lines:
        if any(p.match(line) for p in TIMESTAMP_PATTERNS):
            if seen_update < 2:
                cleaned_output.append(line)
                seen_update += 1
        else:
            cleaned_output.append(line)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned_output) + "\n")

    print(f"[✅] Playlist '{OUTPUT_FILE}' saved with locked group '{FORCED_GROUP}' and EPG URL.")

if __name__ == "__main__":
    upstream_playlist = fetch_playlist()
    process_and_write_playlist(upstream_playlist)
