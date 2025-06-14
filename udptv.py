import requests
import re
from datetime import datetime

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = "UDPTV Live Streams"

REMOVE_PATTERNS = [
    re.compile(r'^# (Last forced update|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    return res.text.strip().splitlines()

def should_remove_line(line):
    return any(pat.match(line) for pat in REMOVE_PATTERNS)

def force_group_title(extinf_line):
    # If group-title exists, replace it
    if 'group-title="' in extinf_line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', extinf_line)
    else:
        # Insert group-title before the last closing bracket or at the end of the line
        # We add it right after the duration value (-1 or whatever)
        return extinf_line.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}" ', 1)

def process_and_write_playlist(upstream_lines):
    # Remove unwanted lines from upstream
    upstream_filtered = [line.strip() for line in upstream_lines if line.strip() and not should_remove_line(line)]

    # Extract all URLs from upstream (lines immediately after #EXTINF)
    upstream_urls = []
    for i in range(len(upstream_filtered)):
        if upstream_filtered[i].startswith("#EXTINF"):
            if i + 1 < len(upstream_filtered):
                upstream_urls.append(upstream_filtered[i + 1].strip())

    # Load existing playlist to keep metadata (names, logos, tvg-id, etc)
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            original = f.read().splitlines()
    except FileNotFoundError:
        # If file doesn't exist, build new header and URLs with forced groups
        print("[WARN] Existing playlist not found, creating new one from upstream.")
        output_lines = [
            f'#EXTM3U url-tvg="{EPG_URL}"',
            f'# Last forced update: {datetime.utcnow().isoformat()}Z'
        ]
        for i, url in enumerate(upstream_urls):
            extinf_line = upstream_filtered[i*2].strip() if i*2 < len(upstream_filtered) else '#EXTINF:-1'
            extinf_line = force_group_title(extinf_line)
            output_lines.append(extinf_line)
            output_lines.append(url)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines) + "\n")
        print(f"[✅] {OUTPUT_FILE} created with forced groups.")
        return

    # Start output with updated header
    output_lines = [
        f'#EXTM3U url-tvg="{EPG_URL}"',
        f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    ]

    url_index = 0
    i = 0
    while i < len(original):
        line = original[i].strip()
        if should_remove_line(line):
            i += 1
            continue
        if line.startswith("#EXTINF"):
            # Keep original metadata line but force group-title
            forced_line = force_group_title(line)
            output_lines.append(forced_line)

            # Replace the URL line with upstream URL if available
            if url_index < len(upstream_urls):
                output_lines.append(upstream_urls[url_index])
                url_index += 1
                # Skip next original line since it's URL
                i += 2
            else:
                i += 1
        else:
            # Copy everything else as is (logos, tvg-id lines, comments, etc)
            # Except header lines replaced by our new header above
            if line.startswith("#EXTM3U") or line.startswith("# Last forced update"):
                i += 1
                continue
            output_lines.append(line)
            i += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"[✅] {OUTPUT_FILE} updated successfully with forced groups, URLs, and timestamp.")

if __name__ == "__main__":
    upstream_playlist = fetch_playlist()
    process_and_write_playlist(upstream_playlist)
