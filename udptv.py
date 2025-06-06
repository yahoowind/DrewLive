import requests
import re
import time

UPSTREAM_URL = "http://drewlive24.duckdns.org:3000/"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"
FORCED_GROUP = 'UDPTV Live Streams'

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=10)
    res.raise_for_status()
    return res.text.splitlines()

def process_lines(lines):
    ts = int(time.time())
    output = []

    for line in lines:
        if line.startswith("#EXTM3U"):
            output.append(f'#EXTM3U url-tvg="{EPG_URL}"')
        elif line.startswith("#EXTINF"):
            # Force group-title
            if 'group-title="' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{FORCED_GROUP}"', line)
            else:
                line = re.sub(r'(,)', f' group-title="{FORCED_GROUP}",', line, count=1)
            output.append(line)
        elif line.startswith("http://") or line.startswith("https://"):
            # Update or add force param
            if "force=" in line:
                line = re.sub(r'force=\d+', f'force={ts}', line)
            else:
                sep = "&" if "?" in line else "?"
                line += f"{sep}force={ts}"
            output.append(line)
        else:
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
