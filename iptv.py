import requests
from collections import defaultdict
import re
from datetime import datetime

playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DistroTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StirrTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveVOD.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Drew247TV.m3u8",
]

EPG_URL = "https://tinyurl.com/merged2423-epg"
OUTPUT_FILE = "MergedPlaylist.m3u8"

def fetch_playlist(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.text.strip().splitlines()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return []

def parse_playlist(lines):
    channels_by_group = defaultdict(list)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            extinf = line
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                group_match = re.search(r'group-title="([^"]+)"', extinf)
                group = group_match.group(1) if group_match else "Other"
                channels_by_group[group].append((extinf, url))
                i += 2
            else:
                i += 1
        else:
            i += 1
    return channels_by_group

def write_merged_playlist(channels_by_group):
    lines = [
        f'#EXTM3U url-tvg="{EPG_URL}"',
        f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    ]

    for group in sorted(channels_by_group.keys()):
        for extinf, url in channels_by_group[group]:
            lines.append(extinf)
            lines.append(url)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f"Merged playlist written to {OUTPUT_FILE}")

if __name__ == "__main__":
    all_channels = defaultdict(list)
    for url in playlist_urls:
        lines = fetch_playlist(url)
        parsed = parse_playlist(lines)
        for group, entries in parsed.items():
            all_channels[group].extend(entries)
    write_merged_playlist(all_channels)