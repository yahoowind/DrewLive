import requests
import re

UPSTREAM_URL = "http://tvpass.org/playlist/m3u"
OUTPUT_FILE = "TVPass.m3u"
FORCED_GROUP = "TVPass"

def fetch_upstream_playlist():
    res = requests.get(UPSTREAM_URL, timeout=10)
    res.raise_for_status()
    return res.text.splitlines()

def force_group_title(extinf_line):
    if not extinf_line.startswith("#EXTINF"):
        return extinf_line

    if 'group-title="' in extinf_line:
        return re.sub(r'group-title=".*?"', f'group-title="{FORCED_GROUP}"', extinf_line)
    else:
        return extinf_line.replace("#EXTINF:", f'#EXTINF: group-title="{FORCED_GROUP}",')

def process_upstream(lines):
    updated = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            updated.append(force_group_title(lines[i]))
            if i + 1 < len(lines):
                updated.append(lines[i + 1].strip())
            i += 2
        else:
            if lines[i].startswith("#") or lines[i].strip() == "":
                updated.append(lines[i])
            i += 1
    return updated

def main():
    upstream_lines = fetch_upstream_playlist()
    updated_lines = process_upstream(upstream_lines)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines) + "\n")

    print(f"✅ TVPass.m3u fully updated from upstream. {len(updated_lines)//2} streams refreshed.")

if __name__ == "__main__":
    main()
