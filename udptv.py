import requests
import re
import time

UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
FORCED_GROUP_TITLE = "UDPTV Live Streams"
OUTPUT_FILE = "UDPTV.m3u"

# Patterns to filter out unwanted lines
UNWANTED_PATTERNS = [
    re.compile(r"^# Last updated:"),
    re.compile(r"^# Updated:"),
    re.compile(r"^### IF YOU ARE A RESELLER OR LEECHER,"),
]

def fetch_playlist(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text.splitlines()

def clean_lines(lines):
    cleaned = []
    timestamp = int(time.time())
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip unwanted lines
        if any(p.match(line) for p in UNWANTED_PATTERNS):
            continue
        # Skip any extra #EXTM3U headers from upstream except first
        if line.startswith("#EXTM3U"):
            continue

        if line.startswith("#EXTINF"):
            # Force group-title only on EXTINF lines, keep other metadata intact
            if 'group-title="' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP_TITLE}"', line)
            else:
                line = re.sub(r'(,)', f' group-title="{FORCED_GROUP_TITLE}",', line, count=1)
            cleaned.append(line)
        elif line.startswith("http://") or line.startswith("https://"):
            # Force update URLs with timestamp param "force"
            if "?" in line:
                if re.search(r'force=\d+', line):
                    line = re.sub(r'force=\d+', f'force={timestamp}', line)
                else:
                    line += f"&force={timestamp}"
            else:
                line += f"?force={timestamp}"
            cleaned.append(line)
        else:
            # All other lines (metadata like tvg-name, tvg-id, logos, comments)
            cleaned.append(line)
    return cleaned

def write_output(lines):
    # Insert your clean #EXTM3U header with EPG url at the top
    header = f'#EXTM3U url-tvg="{EPG_URL}"'
    if lines and lines[0].startswith("#EXTM3U"):
        lines[0] = header
    else:
        lines.insert(0, header)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Cleaned, forced, and wrote: {OUTPUT_FILE}")

if __name__ == "__main__":
    raw_lines = fetch_playlist(UPSTREAM_URL)
    cleaned = clean_lines(raw_lines)
    write_output(cleaned)
