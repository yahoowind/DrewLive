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
    res = requests.get(UPSTREAM_URL, timeout=10)
    res.raise_for_status()
    lines = res.text.splitlines()
    # Remove any existing #EXTM3U header lines (with possible url-tvg or anything else)
    lines = [line for line in lines if not line.strip().startswith('#EXTM3U')]
    return lines

def should_remove_line(line):
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def patch_line(extinf):
    # Force the group-title to FORCED_GROUP in every #EXTINF line
    if 'group-title="' in extinf:
        extinf = re.sub(r'group-title="[^"]+"', f'group-title="{FORCED_GROUP}"', extinf)
    else:
        extinf = extinf.replace('#EXTINF:', f'#EXTINF:-1 group-title="{FORCED_GROUP}",', 1)
    return extinf

def process_and_write(lines):
    output = [f'#EXTM3U url-tvg="{EPG_URL}"\n']
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if should_remove_line(line):
            i += 1
            continue  # skip these lines entirely, no blank line added
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
            # Only append lines we want, no empty lines added
            if line != '':
                output.append(line + '\n')
            i += 1
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines(output)
    print(f"{OUTPUT_FILE} has been written with your EPG and forced groups, cleanly.")

if __name__ == "__main__":
    lines = fetch_playlist()
    process_and_write(lines)
