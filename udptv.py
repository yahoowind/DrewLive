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

def should_remove_timestamp(line):
    return line.strip().lower().startswith("# last forced update:")

def force_group_title(extinf_line):
    if 'group-title="' in extinf_line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', extinf_line)
    else:
        return extinf_line.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}" ', 1)

def process_and_write_playlist(upstream_lines):
    # Clean upstream lines
    upstream_filtered = [line.strip() for line in upstream_lines if line.strip() and not should_remove_line(line)]

    # Extract URLs after #EXTINF
    upstream_urls = []
    for i in range(len(upstream_filtered)):
        if upstream_filtered[i].startswith("#EXTINF"):
            if i + 1 < len(upstream_filtered):
                upstream_urls.append(upstream_filtered[i + 1].strip())

    # Read existing playlist or create new if missing
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            original = f.read().splitlines()
    except FileNotFoundError:
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

    # Remove all old timestamp lines anywhere
    filtered_original = [line for line in original if not should_remove_timestamp(line)]

    # Find #EXTM3U line index
    extm3u_index = None
    for i, line in enumerate(filtered_original):
        if line.strip().lower().startswith("#extm3u"):
            extm3u_index = i
            break

    # Remove any existing timestamp line right after #EXTM3U (just in case)
    if extm3u_index is not None:
        if extm3u_index + 1 < len(filtered_original):
            next_line = filtered_original[extm3u_index + 1].strip().lower()
            if next_line.startswith("# last forced update:"):
                filtered_original.pop(extm3u_index + 1)

    # Insert new timestamp right after #EXTM3U line or at top if missing
    timestamp_line = f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    if extm3u_index is not None:
        filtered_original.insert(extm3u_index + 1, timestamp_line)
    else:
        filtered_original.insert(0, timestamp_line)

    # Replace URLs with upstream URLs, force group-title in #EXTINF lines
    url_index = 0
    i = 0
    while i < len(filtered_original):
        line = filtered_original[i].strip()
        if should_remove_line(line):
            i += 1
            continue
        if line.startswith("#EXTINF"):
            # Force group-title
            forced_line = force_group_title(line)
            filtered_original[i] = forced_line

            # Replace next line URL if available
            if url_index < len(upstream_urls) and i + 1 < len(filtered_original):
                filtered_original[i + 1] = upstream_urls[url_index]
                url_index += 1
            i += 2
        else:
            i += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_original) + "\n")

    print(f"[✅] {OUTPUT_FILE} updated successfully with a single timestamp and forced groups.")

if __name__ == "__main__":
    upstream_playlist = fetch_playlist()
    process_and_write_playlist(upstream_playlist)
