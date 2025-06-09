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

def patch_group_title(line):
    if 'group-title="' in line:
        return re.sub(r'group-title="[^"]+"', f'group-title="{FORCED_GROUP}"', line)
    else:
        return line.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{FORCED_GROUP}"')

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
            patched_line = patch_group_title(line)
            output_lines.append(patched_line)

            # Keep the next line (URL) and move on
            if i + 1 < len(lines):
                output_lines.append(lines[i + 1].strip())
                i += 2
            else:
                i += 1
        else:
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines) + '\n')

    print(f"[✔] {OUTPUT_FILE} updated with forced group title, fresh URLs, and timestamp.")

if __name__ == "__main__":
    playlist_lines = fetch_playlist()
    process_and_write_playlist(playlist_lines)
