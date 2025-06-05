import requests
from collections import OrderedDict
import re

TEMPLATE_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u"
UPSTREAM_URL = "https://tinyurl.com/drewliveudptv"
EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "UDPTV.m3u"

REMOVE_PHRASE = (
    "### IF YOU ARE A RESELLER OR LEECHER, PLEASE CONSIDER SUPPORTING OUR UDPTV SERVER "
    "BY DONATING TO KEEP IT RUNNING 😭 AND I WILL FORGIVE YOU. JOIN OUR DISCORD SERVER FOR "
    "AN UPDATED PLAYLIST: https://discord.gg/civ3"
)

FORCED_GROUP_TITLE = "UDPTV Live Streams"
DUCKDNS_HOST = "yourname.duckdns.org"
CUSTOM_LOGO_DOMAIN = "logo.udptv.live"

def fetch_m3u(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def clean_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if (
            not line
            or line.startswith("#EXTM3U")
            or 'url-tvg=' in line
            or REMOVE_PHRASE in line
            or DUCKDNS_HOST in line
        ):
            continue
        cleaned.append(line)
    return cleaned

def get_channel_key(extinf):
    """Normalize name for deduplication & sorting."""
    name = extinf.split(",")[-1].strip().lower()
    name = re.sub(r'\s*\(.*?\)|\s*HD|\s*\[.*?\]', '', name).strip()
    return name

def parse_m3u(lines):
    result = OrderedDict()
    last_extinf = None
    for line in lines:
        if line.startswith("#EXTINF"):
            if DUCKDNS_HOST in line:
                last_extinf = None
                continue
            last_extinf = line
        elif line.startswith("#"):
            continue
        else:
            if last_extinf:
                key = get_channel_key(last_extinf)
                result[key] = (last_extinf, line)
                last_extinf = None
    return result

def force_group_title(meta, forced_group=FORCED_GROUP_TITLE):
    if CUSTOM_LOGO_DOMAIN in meta:
        return meta
    if 'group-title="' in meta:
        meta = re.sub(r'group-title="[^"]*"', f'group-title="{forced_group}"', meta)
    else:
        meta = re.sub(r'(,)', f' group-title="{forced_group}",', meta, count=1)
    return meta

def merge_playlists(template_dict, upstream_dict):
    merged_dict = {}

    # Merge template first, then allow upstream to override
    for key, (meta, url) in template_dict.items():
        merged_dict[key] = (meta, url)
    for key, (meta, url) in upstream_dict.items():
        merged_dict[key] = (meta, url)

    # Build final list, all sorted alphabetically
    merged = [f'#EXTM3U url-tvg="{EPG_URL}"']
    for key in sorted(merged_dict.keys()):
        meta, url = merged_dict[key]
        final_meta = force_group_title(meta)
        merged.append(final_meta)
        merged.append(url)

    return merged

def main():
    template_lines = clean_lines(fetch_m3u(TEMPLATE_URL))
    upstream_lines = clean_lines(fetch_m3u(UPSTREAM_URL))

    template_dict = parse_m3u(template_lines)
    upstream_dict = parse_m3u(upstream_lines)

    merged_playlist = merge_playlists(template_dict, upstream_dict)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged_playlist) + "\n")

if __name__ == "__main__":
    main()
