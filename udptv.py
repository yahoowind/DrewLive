import requests
import re
from datetime import datetime

# Config
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = "UDPTV Live Streams"

# Patterns to remove
REMOVE_PATTERNS = [
    re.compile(r'^# (Last forced update|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    """Download the M3U playlist."""
    response = requests.get(UPSTREAM_URL, timeout=10)
    response.raise_for_status()
    return response.text.splitlines()

def should_remove_line(line):
    """Identify lines that should be deleted."""
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def patch_extinf_line(extinf_line):
    """Patch only group-title, leave all other metadata untouched."""
    if 'group-title="' in extinf_line:
        extinf_line = re.sub(r'group-title="[^"]+"', f'group-title="{FORCED_GROUP}"', extinf_line)
    else:
        extinf_line = extinf_line.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}"')
    return extinf_line

def process_playlist(lines):
    """Clean and process the playlist content."""
    output = [f'#EXTM3U url-tvg="{EPG_URL}"',
              f'# Last forced update: {datetime.utcnow().isoformat()}Z']
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or should_remove_line(line):
            i += 1
            continue

        if line.startswith("#EXTINF"):
            line = patch_extinf_line(line)
            output.append(line)

            if i + 1 < len(lines):
                output.append(lines[i + 1].strip())
                i += 2
            else:
                i += 1
        else:
            i += 1
    return output

def save_playlist(output_lines):
    """Write processed lines to output file."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines) + '\n')
    print(f"[✅] Saved '{OUTPUT_FILE}' with forced group-title + EPG (metadata untouched)")

def main():
    print("[🎯] Fetching original playlist...")
    lines = fetch_playlist()

    print("[🔧] Processing lines (forcing group, preserving metadata)...")
    final_output = process_playlist(lines)

    print("[💾] Writing playlist...")
    save_playlist(final_output)

if __name__ == "__main__":
    main()
