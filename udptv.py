import requests
import re

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = 'UDPTV Live Streams'

REMOVE_PATTERNS = [
    re.compile(r'^# (Last updated|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    try:
        res = requests.get(UPSTREAM_URL, timeout=10)
        res.raise_for_status()
        return res.text.splitlines()
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []

def should_remove_line(line):
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def patch_line(extinf):
    # Force the group-title to YOUR group, no exceptions
    if 'group-title="' in extinf:
        extinf = re.sub(r'group-title="[^"]+"', f'group-title="{FORCED_GROUP}"', extinf)
    else:
        extinf = extinf.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}"')
    return extinf

def process_and_write(lines):
    output = [f'#EXTM3U url-tvg="{EPG_URL}"\n']  # Only your EPG line, no duplicates

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if should_remove_line(line):
            i += 1
            continue
        if line.startswith('#EXTINF'):
            patched = patch_line(line)
            output.append(patched + '\n')
            # Next line must be stream URL, just add it
            if i + 1 < len(lines):
                output.append(lines[i + 1].strip() + '\n')
                i += 2
            else:
                i += 1
        else:
            i += 1

    # Force overwrite the file every time you run this
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines(output)

    print(f"{OUTPUT_FILE} updated and overwritten — forced update complete.")

if __name__ == "__main__":
    lines = fetch_playlist()
    process_and_write(lines)
