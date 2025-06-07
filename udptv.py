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
    headers = {'Cache-Control': 'no-cache'}
    res = requests.get(UPSTREAM_URL, headers=headers, timeout=10)
    res.raise_for_status()
    return res.text.splitlines()

def should_remove_line(line):
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def patch_line(extinf):
    # Always force group title to YOUR forced group exactly
    if 'group-title="' in extinf:
        extinf = re.sub(r'group-title="[^"]+"', f'group-title="{FORCED_GROUP}"', extinf)
    else:
        extinf = extinf.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}"')
    # You can add more patch logic here if needed
    return extinf

def process_and_write(lines):
    output = [f'#EXTM3U url-tvg="{EPG_URL}"\n']
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if should_remove_line(line):
            i += 1
            continue
        if line.startswith('#EXTINF'):
            patched = patch_line(line)
            output.append(patched + '\n')
            if i + 1 < len(lines):
                stream_url = lines[i + 1].strip()
                output.append(stream_url + '\n')
                i += 2
            else:
                i += 1
        else:
            i += 1
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines(output)
    print(f"{OUTPUT_FILE} forcibly updated and written.")

if __name__ == "__main__":
    lines = fetch_playlist()
    process_and_write(lines)
