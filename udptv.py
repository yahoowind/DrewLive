import requests
import re

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = 'UDPTV Live Streams'

REMOVE_PATTERNS = [
    re.compile(r'^# *(Last updated|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=10)
    res.raise_for_status()
    return [line.strip() for line in res.text.splitlines() if line.strip()]  # removes blank lines too

def should_remove_line(line):
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def patch_line(extinf):
    if 'group-title="' in extinf:
        extinf = re.sub(r'group-title="[^"]+"', f'group-title="{FORCED_GROUP}"', extinf)
    else:
        extinf = extinf.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}"')
    return extinf

def process_and_write(lines):
    output = [f'#EXTM3U url-tvg="{EPG_URL}"']
    i = 0
    while i < len(lines):
        line = lines[i]
        if should_remove_line(line):
            i += 1
            continue
        if line.startswith('#EXTINF'):
            patched = patch_line(line)
            output.append(patched)
            if i + 1 < len(lines) and lines[i + 1].startswith("http"):
                output.append(lines[i + 1])
                i += 2
            else:
                i += 1
        else:
            i += 1
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output) + '\n')
    print(f"{OUTPUT_FILE} has been force-updated cleanly.")

if __name__ == "__main__":
    lines = fetch_playlist()
    process_and_write(lines)
