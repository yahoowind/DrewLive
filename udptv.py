import requests
from collections import OrderedDict
import re
from urllib.parse import urlparse, quote

# Playlist sources
GIT_RAW_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u"
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"

FORCED_GROUP_TITLE = "UDPTV Live Streams"
MY_DOMAIN = "http://drewlive24.duckdns.org:3000"

def fetch_m3u(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def clean_lines(lines):
    return [line.strip() for line in lines if line.strip() and not line.startswith("#EXTM3U") and "url-tvg=" not in line]

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
        meta = re.sub(r'(#EXTINF:[^,]+,)', r'\1 group-title="' + forced_group + '",', meta, count=1)
    return meta

def is_url_alive(url):
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False

def replace_domain(url):
    try:
        encoded_url = quote(url, safe='')
        return f"{MY_DOMAIN}/stream?url={encoded_url}"
    except Exception:
        return url

def merge_playlists(git_dict, upstream_dict):
    merged_dict = {}

    for key, (meta, _) in git_dict.items():
        original_url = upstream_dict.get(key, (None, None))[1]
        if original_url and is_url_alive(original_url):
            proxy_url = replace_domain(original_url)
            merged_dict[key] = (force_group_title(meta), proxy_url)

    for key, (meta, url) in upstream_dict.items():
        if key not in merged_dict and is_url_alive(url):
            proxy_url = replace_domain(url)
            merged_dict[key] = (force_group_title(meta), proxy_url)

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
