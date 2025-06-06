import requests
import re
import time

UPSTREAM_URL = "http://drewlive24.duckdns.org:3000/"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"

def fetch_playlist():
    res = requests.get(UPSTREAM_URL, timeout=10)
    res.raise_for_status()
    return res.text.splitlines()

def refresh_force_params(lines):
    updated = []
    ts = int(time.time())

    for line in lines:
        if line.startswith("#EXTM3U"):
            updated.append(f'#EXTM3U url-tvg="{EPG_URL}"')
        elif line.startswith("http://") or line.startswith("https://"):
            # Update or append force param
            if "force=" in line:
                line = re.sub(r'force=\d+', f'force={ts}', line)
            else:
                sep = "&" if "?" in line else "?"
                line += f"{sep}force={ts}"
            updated.append(line)
        else:
            updated.append(line)

    return updated

def write_output(lines):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Updated force param and saved: {OUTPUT_FILE}")

if __name__ == "__main__":
    lines = fetch_playlist()
    refreshed = refresh_force_params(lines)
    write_output(refreshed)
