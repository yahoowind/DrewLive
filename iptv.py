import requests
from collections import defaultdict
import re

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
            match = re.search(r'group-title="([^"]+)"', line)
            group = match.group(1).strip() if match else "ZZZ_Unsorted"
            extinf = line
            if i + 1 < len(lines):
                stream = lines[i + 1].strip()
                if stream and not stream.startswith("#"):
                    channels_by_group[group].append((extinf, stream))
                    i += 2
                    continue
        i += 1
    return channels_by_group

def merge_playlists(urls, epg_url):
    all_channels = defaultdict(list)

    for url in urls:
        lines = fetch_playlist(url)
        if lines and lines[0].startswith("#EXTM3U"):
            lines = lines[1:]  # Remove header
        parsed = parse_playlist(lines)
        for group, entries in parsed.items():
            all_channels[group].extend(entries)

    sorted_groups = sorted(all_channels.keys(), key=lambda x: x.lower())

    output = [f'#EXTM3U url-tvg="{epg_url}"\n']
    for group in sorted_groups:
        for extinf, stream in all_channels[group]:
            output.append(extinf.strip())
            output.append(stream.strip())

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(output) + "\n")

    print(f"{OUTPUT_FILE} has been rebuilt — metadata untouched, groups in order.")

if __name__ == "__main__":
    merge_playlists(playlist_urls, EPG_URL)
