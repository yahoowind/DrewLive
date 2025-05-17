import requests
import re
from urllib.parse import urlparse


# List of your playlist URLs
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


# Your custom EPG URL
EPG_URL = "https://tinyurl.com/merged2423-epg"


def fetch_playlist(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


def extract_group_title_from_url(url):
    path = urlparse(url).path
    return path.split('/')[-1].replace(".m3u8", "")


def parse_entries(content, group_title):
    lines = content.strip().splitlines()
    entries = []
    seen_urls = set()
    i = 0


    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            # Inject group-title
            if 'group-title=' not in line:
                line = re.sub(r'#EXTINF:-?\d+', f'#EXTINF:-1 group-title="{group_title}"', line)
            entry_lines = [line]


            j = i + 1
            while j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                entry_lines.append(lines[j])
                j += 1


            if j < len(lines):
                stream_url = lines[j].strip()
                if stream_url not in seen_urls:
                    entry_lines.append(stream_url)
                    entries.append(entry_lines)
                    seen_urls.add(stream_url)
                i = j + 1
            else:
                i = j
        else:
            i += 1
    return entries


def extract_channel_name(extinf_line):
    match = re.search(r',(.+)$', extinf_line)
    return match.group(1).strip() if match else ""


def merge_playlists(urls, epg_url):
    all_entries = []


    for url in urls:
        group_title = extract_group_title_from_url(url)
        content = fetch_playlist(url)
        if content:
            entries = parse_entries(content, group_title)
            all_entries.extend(entries)


    # Sort by channel name (alphabetical)
    all_entries.sort(key=lambda entry: extract_channel_name(entry[0]).lower())


    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U url-tvg="{epg_url}"\n')
        for entry in all_entries:
            for line in entry:
                f.write(f"{line.strip()}\n")
    print("Merged and sorted playlist saved as MergedPlaylist.m3u8")


if __name__ == "__main__":
    merge_playlists(playlist_urls, EPG_URL)
