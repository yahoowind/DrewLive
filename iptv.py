import requests
import re
import time
from datetime import datetime

playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/TubiTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/DrewLiveVOD.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/TVPass.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/Radio.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/TheTVApp.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/AriaPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/LocalNowTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/Xumo.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/MoveOnJoy.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/A1x.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamedSU.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SportsWebcast.m3u8"
]

EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "MergedPlaylist.m3u8"

def fetch_playlist(url, retries=3, timeout=30):
    headers = {"User-Agent": "Mozilla/5.0"}
    for attempt in range(1, retries + 1):
        try:
            print(f"Attempting to fetch {url} (try {attempt})...")
            res = requests.get(url, timeout=timeout, headers=headers)
            res.raise_for_status()
            print(f"✅ Successfully fetched {url}")
            return res.text.strip().splitlines()
        except Exception as e:
            print(f"❌ Attempt {attempt} failed for {url}: {e}")
            time.sleep(2)
    print(f"⚠️ Skipping {url} after {retries} failed attempts.")
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
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                url_line = lines[i].strip()
                if url_line and not url_line.startswith("#") and url_line != "*":
                    parsed_channels.append((extinf_line, tuple(channel_headers), url_line))
                else:
                    print(f"⚠️ Skipped entry in {source_url}. Reason: Invalid or placeholder URL '{url_line}'. Channel Info: {extinf_line}")
                i += 1
            else:
                i += 1
        else:
            i += 1
    print(f"✅ Parsed {len(parsed_channels)} valid channels from {source_url}.")
    return parsed_channels

def write_merged_playlist(all_channels):
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]
    sortable = []
    
    for extinf, headers, url in all_channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        group = group_match.group(1) if group_match else "Other"
        try:
            title = extinf.rsplit(',', 1)[1].strip()
        except IndexError:
            title = ""
        
        tvg_id_match = re.search(r'tvg-id="([^"]+)"', extinf)
        if tvg_id_match and tvg_id_match.group(1):
            unique_id = tvg_id_match.group(1).strip()
        else:
            unique_id = title.lower()
            
        sortable.append((group.lower(), title.lower(), group, extinf, headers, url, unique_id))
    
    sorted_channels = sorted(sortable)
    
    deduplicated_channels = []
    seen_ids = set()
    for group_lower, title_lower, group_name, extinf, headers, url, unique_id in sorted_channels:
        if unique_id and unique_id not in seen_ids:
            deduplicated_channels.append((group_name, extinf, headers, url))
            seen_ids.add(unique_id)
        elif not unique_id and title_lower not in seen_ids:
             deduplicated_channels.append((group_name, extinf, headers, url))
             seen_ids.add(title_lower)

    current_group = None
    count = 0

    for group_name, extinf, headers, url in deduplicated_channels:
        if group_name != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f"#EXTGRP:{group_name}")
            current_group = group_name
        lines.append(extinf)
        lines.extend(headers)
        lines.append(url)
        count += 1
    
    if lines and lines[-1] == "":
        lines.pop()

    final_output = '\n'.join(lines) + '\n'
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_output)
    
    print(f"\n✅ Wrote {count} de-duplicated channels to {OUTPUT_FILE} ({len(final_output.splitlines())} lines).")

if __name__ == "__main__":
    print(f"Starting playlist merge at {datetime.now()}...")
    all_channels_list = []

    for url in playlist_urls:
        lines = fetch_playlist(url)
        if lines:
            parsed_channels = parse_playlist(lines, source_url=url)
            all_channels_list.extend(parsed_channels)

    write_merged_playlist(all_channels_list)
    print(f"Merging complete at {datetime.now()}.")
