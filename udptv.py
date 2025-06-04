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

def fetch_m3u(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def clean_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        # Remove empty lines, #EXTM3U header, url-tvg lines, and the remove phrase line
        if not line or line.startswith("#EXTM3U") or 'url-tvg=' in line or line == REMOVE_PHRASE:
            continue
        cleaned.append(line)
    return cleaned

def parse_m3u(lines):
    """
    Parse the M3U lines into OrderedDict keyed by tvg-id if exists,
    else by full #EXTINF line. Each value is (metadata line, url line).
    """
    result = OrderedDict()
    last_extinf = None
    for line in lines:
        if line.startswith("#EXTINF"):
            last_extinf = line
        elif line.startswith("#"):
            # skip any other tags between extinf/url pairs
            continue
        else:
            if last_extinf:
                key = None
                # Use tvg-id as unique key if present, else whole EXTINF line as key
                if 'tvg-id="' in last_extinf:
                    key = last_extinf.split('tvg-id="')[1].split('"')[0].strip()
                key = key or last_extinf
                result[key] = (last_extinf, line)
                last_extinf = None
    return result

def channel_name_from_extinf(extinf_line):
    """
    Extract channel display name from the #EXTINF line:
    It's the part after the last comma.
    """
    return extinf_line.split(",")[-1].strip().lower()

def merge_playlists(template_dict, upstream_dict):
    merged = [f'#EXTM3U url-tvg="{EPG_URL}"']
    processed_keys = set()
    combined_items = []

    # First add/merge template entries, prefer upstream URL if different
    for key, (meta, url) in template_dict.items():
        upstream_url = upstream_dict.get(key, (None, None))[1]
        final_url = upstream_url if upstream_url and upstream_url != url else url
        combined_items.append((meta, final_url))
        processed_keys.add(key)

    # Add upstream entries not in template
    for key, (meta, url) in upstream_dict.items():
        if key not in processed_keys:
            combined_items.append((meta, url))

    # Sort by channel name (from #EXTINF line)
    combined_items.sort(key=lambda x: channel_name_from_extinf(x[0]))

    # Add to merged list
    for meta, url in combined_items:
        merged.append(meta)
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
