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
LOG_FILE = "merge_log.txt"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(full_msg + "\n")

def fetch_playlist(url):
    try:
        log(f"Fetching playlist: {url}")
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        log(f"✅ Successfully fetched: {url} ({len(res.content)} bytes)")
        return res.content.decode('utf-8', errors='ignore').splitlines()
    except Exception as e:
        log(f"❌ Failed to fetch {url}: {e}")
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
                if not url_line:
                    log(f"⚠ Skipped empty URL for EXTINF: {extinf_line}")
                    continue
                parsed_channels.append((extinf_line, tuple(headers), url_line))
                log(f"Parsed channel: {url_line}")
        else:
            i += 1
    return parsed_channels

def write_merged_playlist(channels):
    lines = ["#EXTM3U", ""]
    groups = {}
    for extinf, headers, url in channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        group_name = group_match.group(1) if group_match else "Other"
        extinf_with_epg = re.sub(r'(tvg-logo="[^"]*")', f'\\1 tvg-url="{EPG_URL}"', extinf)
        groups.setdefault(group_name, []).append((extinf_with_epg, headers, url))

    for group_name in sorted(groups.keys()):
        lines.append(f'#EXTGRP:{group_name}')
        for extinf, headers, url in sorted(groups[group_name], key=lambda x: re.search(r',(.+)$', x[0]).group(1).lower() if re.search(r',(.+)$', x[0]) else x[0]):
            lines.append(extinf)
            lines.extend(headers)
            lines.append(url)
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

    total_channels = sum(len(ch) for ch in groups.values())
    log(f"✅ Merged playlist written to {OUTPUT_FILE}. Total channels: {total_channels}")

if __name__ == "__main__":
    log("Starting merge process...")
    all_channels = []
    for url in playlist_urls:
        lines = fetch_playlist(url)
        parsed = parse_playlist(lines)
        all_channels.extend(parsed)
    write_merged_playlist(all_channels)
    log("Merge process complete!")
