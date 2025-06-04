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

FORCED_GROUP_TITLE = "UDPTV Live Streams"  # your permanent group name here

DUCKDNS_HOST = "yourname.duckdns.org"  # <-- Replace this with your actual DuckDNS domain
CUSTOM_LOGO_DOMAIN = "logo.udptv.live"  # example domain to protect your logos from being changed

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
            or DUCKDNS_HOST in line   # Remove lines containing your DuckDNS domain
        ):
            continue
        cleaned.append(line)
    return cleaned

def parse_m3u(lines):
    result = OrderedDict()
    last_extinf = None
    for line in lines:
        if line.startswith("#EXTINF"):
            if DUCKDNS_HOST in line:  # Skip any #EXTINF with your DuckDNS domain
                last_extinf = None
                continue
            last_extinf = line
        elif line.startswith("#"):
            continue
        else:
            if last_extinf:
                key = None
                # Use tvg-id as key if present, else fallback to channel name in EXTINF
                if 'tvg-id="' in last_extinf:
                    key = last_extinf.split('tvg-id="')[1].split('"')[0].strip()
                else:
                    # fallback: extract channel name after comma
                    key = last_extinf.split(",")[-1].strip()
                result[key] = (last_extinf, line)
                last_extinf = None
    return result

def force_group_title(meta, forced_group=FORCED_GROUP_TITLE):
    if CUSTOM_LOGO_DOMAIN in meta:
        return meta  # preserve custom logos, don’t overwrite group title there
    if 'group-title="' in meta:
        meta = re.sub(r'group-title="[^"]*"', f'group-title="{forced_group}"', meta)
    else:
        meta = re.sub(r'(,)', f' group-title="{forced_group}",', meta, count=1)
    return meta

def merge_playlists(template_dict, upstream_dict):
    merged = [f'#EXTM3U url-tvg="{EPG_URL}"']
    processed_keys = set()

    # First output all channels from template in their order
    for key, (meta, url) in template_dict.items():
        upstream_url = upstream_dict.get(key, (None, None))[1]
        final_url = upstream_url if upstream_url and upstream_url != url else url
        final_meta = force_group_title(meta)
        merged.append(final_meta)
        merged.append(final_url)
        processed_keys.add(key)

    # Add any new upstream channels not in template, sorted alphabetically by channel name (key)
    new_channels = [
        (key, force_group_title(meta), url)
        for key, (meta, url) in upstream_dict.items() if key not in processed_keys
    ]
    new_channels.sort(key=lambda x: x[0].lower())  # sort by key (channel name)

    for key, meta, url in new_channels:
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
