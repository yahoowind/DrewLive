import requests
import re
import time

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = 'UDPTV Live Streams'

# Patterns for lines to remove (like "leeched" messages)
REMOVE_PATTERNS = [
    re.compile(r'^# (Last updated|Updated):', re.IGNORECASE),
    re.compile(r'^### IF YOU ARE A RESELLER OR LEECHER', re.IGNORECASE),
]

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=10)
    res.raise_for_status()
    return res.text.splitlines()

def should_remove_line(line):
    return any(pattern.match(line) for pattern in REMOVE_PATTERNS)

def process_lines(lines):
    ts = int(time.time())
    output = []

    for line in lines:
        line = line.strip()
        if should_remove_line(line):
            # Skip any line that matches the remove patterns
            continue

        if line.startswith("#EXTM3U"):
            # Inject EPG url without touching other attributes
            if 'url-tvg="' not in line:
                output.append(f'#EXTM3U url-tvg="{EPG_URL}"')
            else:
                output.append(line)
        elif line.startswith("#EXTINF"):
            # Force group-title, but do NOT remove other tags like tvg-id or tvg-logo
            if 'group-title="' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', line)
            else:
                line = re.sub(r'(,)', f' group-title="{FORCED_GROUP}",', line, count=1)
            output.append(line)
        elif line.startswith("http://") or line.startswith("https://"):
            # Always update or add force param to force fresh tokens
            if "force=" in line:
                line = re.sub(r'force=\d+', f'force={ts}', line)
            else:
                sep = "&" if "?" in line else "?"
                line += f"{sep}force={ts}"
            output.append(line)
        else:
            # Keep any other lines untouched
            output.append(line)

    return output

def write_output(lines):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ All done. Saved: {OUTPUT_FILE}")
if __name__ == "__main__":
    lines = fetch_playlist()
    updated = process_lines(lines)
    write_output(updated)
