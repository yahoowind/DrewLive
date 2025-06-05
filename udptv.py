import requests
from collections import OrderedDict
import re
from urllib.parse import urlparse

# 🔥 Your actual GitHub raw playlist (trusted source with logos, tvg-id, etc.)
GIT_RAW_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u"
# 🆕 Your upstream URL with possibly updated stream links
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
# 📺 EPG guide URL
EPG_URL = "https://tinyurl.com/merged2423-epg"
# 📁 Output filename
OUTPUT_FILE = "UDPTV.m3u"

# 🏷️ Force this group title for everything
FORCED_GROUP_TITLE = "UDPTV Live Streams"
# Your DuckDNS domain + port for streams
MY_DOMAIN = "http://drewlive24.duckdns.org:3000"

def fetch_m3u(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def clean_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U") or "url-tvg=" in line:
            continue
        cleaned.append(line)
    return cleaned

def get_channel_key(extinf):
    return extinf.split(",")[-1].strip().lower()

def parse_m3u(lines):
    result = OrderedDict()
    last_extinf = None
    for line in lines:
        if line.startswith("#EXTINF"):
            last_extinf = line
        elif last_extinf:
            key = get_channel_key(last_extinf)
            result[key] = (last_extinf, line)
            last_extinf = None
    return result

def force_group_title(meta, forced_group=FORCED_GROUP_TITLE):
    if 'group-title="' in meta:
        meta = re.sub(r'group-title="[^"]*"', f'group-title="{forced_group}"', meta)
    else:
        meta = re.sub(r'(,)', f' group-title="{forced_group}",', meta, count=1)
    return meta

def replace_domain(url):
    try:
        parsed = urlparse(url)
        new_url = MY_DOMAIN + parsed.path
        if parsed.query:
            new_url += "?" + parsed.query
        if parsed.fragment:
            new_url += "#" + parsed.fragment
        return new_url
    except Exception:
        return url

def merge_playlists(git_dict, upstream_dict):
    merged_dict = {}

    for key, (meta, url) in git_dict.items():
        original_url = upstream_dict.get(key, (None, url))[1]
        new_url = replace_domain(original_url)
        merged_dict[key] = (force_group_title(meta), new_url)

    for key, (meta, url) in upstream_dict.items():
        if key not in merged_dict:
            new_url = replace_domain(url)
            merged_dict[key] = (force_group_title(meta), new_url)

    merged = [f'#EXTM3U url-tvg="{EPG_URL}"']
    for key in sorted(merged_dict.keys()):
        meta, url = merged_dict[key]
        merged.append(meta)
        merged.append(url)

    return merged

def main():
    git_lines = clean_lines(fetch_m3u(GIT_RAW_URL))
    upstream_lines = clean_lines(fetch_m3u(UPSTREAM_URL))

    git_dict = parse_m3u(git_lines)
    upstream_dict = parse_m3u(upstream_lines)

    merged_playlist = merge_playlists(git_dict, upstream_dict)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged_playlist) + "\n")

if __name__ == "__main__":
    main()
