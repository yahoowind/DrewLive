import requests
import re

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = 'UDPTV Live Streams'

REMOVE_PATTERNS = [
    re.compile(r'^# (Last updated|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
    re.compile(r'^#EXTM3U', re.IGNORECASE),
]

def fetch_playlist():
    # Always pull fresh, no cache, no retries except fatal error
    res = requests.get(UPSTREAM_URL, timeout=10)
    res.raise_for_status()
    return res.text.splitlines()

def should_remove_line(line):
    for pattern in REMOVE_PATTERNS:
        if pattern.match(line):
            return True
    return False

def patch_extinf_line(line):
    # Clean out any group-title, force your group
    line = re.sub(r'group-title="[^"]*"', '', line)
    line = re.sub(r'\s{2,}', ' ', line)
    parts = line.split(',', 1)
    if len(parts) == 2:
        before_comma, after_comma = parts
        before_comma = before_comma.strip()
        before_comma += f' group-title="{FORCED_GROUP}"'
        return f"{before_comma},{after_comma}"
    else:
        return f'#EXTINF:-1 group-title="{FORCED_GROUP}" {line[8:]}'

def process_and_write(lines):
    # Always overwrite, no matter what
    output = [f'#EXTM3U url-tvg="{EPG_URL}"\n']
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if should_remove_line(line):
            i += 1
            continue
        if line.startswith('#EXTINF'):
            output.append(patch_extinf_line(line) + '\n')
            if i + 1 < len(lines):
                output.append(lines[i + 1].strip() + '\n')
                i += 2
            else:
                i += 1
        else:
            output.append(line + '\n')
            i += 1
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines(output)
    print(f"🔥 {OUTPUT_FILE} double triple force updated.")

if __name__ == "__main__":
    lines = fetch_playlist()
    process_and_write(lines)
