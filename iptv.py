import requests
import re
from collections import defaultdict


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
]


EPG_URL = "https://tinyurl.com/merged2423-epg"


def fetch_playlist(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


def extract_group_title(extinf):
    match = re.search(r'group-title="(.*?)"', extinf)
    return match.group(1).strip() if match else "Unknown"


def extract_channel_name(extinf):
    match = re.search(r',(.+)$', extinf)
    return match.group(1).strip() if match else ""


def parse_entries(content):
    lines = content.strip().splitlines()
    grouped = defaultdict(list)
    seen = set()
    i = 0


    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            entry = [line]
            j = i + 1
            while j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                entry.append(lines[j])
                j += 1
            if j < len(lines):
                url = lines[j].strip()
                if url not in seen:
                    entry.append(url)
                    group = extract_group_title(line)
                    grouped[group].append(entry)
                    seen.add(url)
                i = j + 1
            else:
                i = j
        else:
            i += 1
    return grouped


def merge_playlists(urls, epg_url):
    merged = defaultdict(list)


    for url in urls:
        content = fetch_playlist(url)
        if content:
            entries = parse_entries(content)
            for group, group_entries in entries.items():
                merged[group].extend(group_entries)


    # Sort each group by channel name
    for group in merged:
        merged[group].sort(key=lambda entry: extract_channel_name(entry[0]).lower())


    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U url-tvg="{epg_url}"\n')
        for group in sorted(merged.keys()):
            for entry in merged[group]:
                for line in entry:
                    f.write(f"{line}\n")
    print("Final playlist saved as MergedPlaylist.m3u8 with proper grouping and sorting.")


if __name__ == "__main__":
    merge_playlists(playlist_urls, EPG_URL)
