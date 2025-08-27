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
    "http://drewlive24.duckdns.org:8081/ppv.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "http://drewlive24.duckdns.org:8081/tims.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/AriaPlus.m3u8",
    "http://drewlive24.duckdns.org:8081/Zuzz.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Xumo.m3u8"
]

EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "MergedPlaylist.m3u8"

def fetch_playlist(url):
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return res.content.decode('utf-8', errors='ignore').splitlines()
    except:
        return []

def parse_playlist(lines):
    parsed_channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf_line = line
            headers = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("#"):
                headers.append(lines[i].strip())
                i += 1
            if i < len(lines):
                url_line = lines[i].strip()
                i += 1
                if not url_line or url_line == "*":
                    continue
                parsed_channels.append((extinf_line, tuple(headers), url_line))
        else:
            i += 1
    return parsed_channels

def add_tvg_url(extinf):
    # Only add tvg-url if not already present
    if 'tvg-url=' not in extinf:
        parts = extinf.split(',', 1)
        extinf = parts[0] + f' tvg-url="{EPG_URL}",' + (parts[1] if len(parts) > 1 else '')
    return extinf

def write_merged_playlist(channels):
    lines = ["#EXTM3U", ""]
    groups = {}

    # Group channels
    for extinf, headers, url in channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        group_name = group_match.group(1) if group_match else "Other"
        extinf_with_epg = add_tvg_url(extinf)
        groups.setdefault(group_name, []).append((extinf_with_epg, headers, url))

    # Sort groups alphabetically
    for group_name in sorted(groups.keys()):
        lines.append(f'#EXTGRP:{group_name}')
        # Sort channels alphabetically by name after last comma
        sorted_channels = sorted(
            groups[group_name],
            key=lambda x: re.search(r',(.+)$', x[0]).group(1).lower() if re.search(r',(.+)$', x[0]) else x[0]
        )
        for extinf, headers, url in sorted_channels:
            lines.append(extinf)
            lines.extend(headers)
            lines.append(url)
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    print(f"🟢 Starting merge at {datetime.now()}...")
    all_channels = []
    for url in playlist_urls:
        lines = fetch_playlist(url)
        parsed = parse_playlist(lines)
        all_channels.extend(parsed)
        print(f"   ➡ {url} → {len(parsed)} channels parsed")
    write_merged_playlist(all_channels)

    # Lightweight summary
    groups = {}
    for extinf, _, _ in all_channels:
        match = re.search(r'group-title="([^"]+)"', extinf)
        group = match.group(1) if match else "Other"
        groups[group] = groups.get(group, 0) + 1

    print(f"✅ Merge complete! Total channels: {len(all_channels)}")
    print("   Group summary:")
    for group_name in sorted(groups.keys()):
        print(f"      {group_name}: {groups[group_name]}")
