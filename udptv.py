import requests
import re
from datetime import datetime

# URLs and output filename
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = "UDPTV Live Streams"

# Patterns to remove from the playlist
REMOVE_PATTERNS = [
    re.compile(r'^# (Last forced update|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    response = requests.get(UPSTREAM_URL, timeout=10)
    response.raise_for_status()
    return response.text.splitlines()

def should_remove_line(line):
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def patch_extinf_line(line):
    # Force group-title but preserve all other attributes like tvg-id, tvg-logo, etc.
    if 'group-title="' in line:
        line = re.sub(r'group-title="[^"]+"', f'group-title="{FORCED_GROUP}"', line)
    else:
        # If group-title doesn't exist, add it before the comma
        parts = line.split(",", 1)
        if len(parts) == 2:
            head, name = parts
            if not 'group-title=' in head:
                head += f' group-title="{FORCED_GROUP}"'
            line = f'{head},{name}'
    return line

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

        if line.startswith('#EXTINF'):
            line = patch_extinf_line(line)
            output_lines.append(line)

            # Add the next line (stream URL)
            if i + 1 < len(lines):
                stream_url = lines[i + 1].strip()
                output_lines.append(stream_url)
                i += 2
            else:
                i += 1
        else:
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines) + '\n')

    print(f"[✅] '{OUTPUT_FILE}' updated with preserved metadata and forced group title.")

if __name__ == "__main__":
    playlist_lines = fetch_playlist()
    process_and_write_playlist(playlist_lines)
