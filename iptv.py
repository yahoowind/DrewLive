import requests
import re
from datetime import datetime

playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveVOD.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TVPass.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Radio.m3u8",
    "http://drewlive24.duckdns.org:8081/PPVLand.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "http://drewlive24.duckdns.org:8081/Tims247.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/AriaPlus.m3u8",
    "http://drewlive24.duckdns.org:8081/Zuzz.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Xumo.m3u8"
]

EPG_URL = "https://tinyurl.com/DrewLive002-epg"
OUTPUT_FILE = "MergedPlaylist.m3u8"

def fetch_playlist(url):
    print(f"Attempting to fetch: {url}")
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return res.content.decode('utf-8', errors='ignore').strip().splitlines()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

def parse_playlist(lines, source_url="Unknown"):
    parsed_channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf_line = line
            channel_headers = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF:"):
                channel_headers.append(lines[i].strip())
                i += 1
            if i < len(lines):
                url_line = lines[i].strip()
                i += 1
                # ✅ Remove dead/invalid channels
                if not url_line or url_line == "*" or url_line.lower() in ["none", "null"]:
                    print(f"⚠️ Removed dead channel from {source_url}: {extinf_line}")
                    continue
                parsed_channels.append((extinf_line, tuple(channel_headers), url_line))
            else:
                print(f"⚠️ Warning ({source_url}): #EXTINF at line {i} not followed by a valid stream URL. Skipping.")
        else:
            i += 1
    print(f"✅ Parsed {len(parsed_channels)} valid channels from {source_url}.")
    return parsed_channels

def write_merged_playlist(all_unique_channels):
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]
    sortable_channels = []

    for extinf, headers, url in all_unique_channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        group = group_match.group(1) if group_match else "Other"
        title_match = re.search(r',([^,]+)$', extinf)
        title = title_match.group(1).strip() if title_match else ""
        sortable_channels.append((group.lower(), title.lower(), extinf, headers, url))

    sorted_channels = sorted(sortable_channels)
    current_group = None
    total_channels_written = 0

    for _, _, extinf, headers, url in sorted_channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        actual_group_name = group_match.group(1) if group_match else "Other"
        if actual_group_name != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f'#EXTGRP:{actual_group_name}')
            current_group = actual_group_name
        lines.append(extinf)
        lines.extend(headers)
        lines.append(url)
        total_channels_written += 1

    if lines and lines[-1] == "":
        lines.pop()

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f"\n✅ Merged playlist written to {OUTPUT_FILE}.")
    print(f"📊 Total unique channels merged: {total_channels_written}.")

if __name__ == "__main__":
    print(f"Starting playlist merge at {datetime.now()}...")

    all_unique_channels_set = set()
    for url in playlist_urls:
        lines = fetch_playlist(url)
        parsed_channels = parse_playlist(lines, source_url=url)
        all_unique_channels_set.update(parsed_channels)

    write_merged_playlist(list(all_unique_channels_set))
    print(f"Merging complete at {datetime.now()}.")
