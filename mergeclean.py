import requests
import re
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
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/TheTVApp.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/AriaPlus.m3u8",
    "http://drewlive24.duckdns.org:8081/Zuzz.m3u8",
    "http://drewlive24.duckdns.org:8081/TazzTV.m3u",
    "http://drewlive24.duckdns.org:8081/StreamedSU.m3u",
    "http://drewlive24.duckdns.org:8081/RBTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/main/Xumo.m3u8"
]

EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "MergedCleanPlaylist.m3u8"
REMOVED_FILE = "Removed_NSFW.m3u8"

def fetch_playlist(url):
    print(f"Fetching: {url}")
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return res.content.decode('utf-8', errors='ignore').strip().splitlines()
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return []

def parse_playlist(lines, source_url="Unknown"):
    parsed = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            headers = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF:"):
                headers.append(lines[i].strip())
                i += 1
            if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#"):
                url = lines[i].strip()
                parsed.append((extinf, tuple(headers), url))
                i += 1
            else:
                print(f"⚠️ Skipped invalid channel in {source_url}")
        else:
            i += 1
    print(f"✅ Parsed {len(parsed)} channels from {source_url}")
    return parsed

def is_nsfw(extinf, headers, url):
    nsfw_keywords = ['nsfw', 'xxx', 'porn']
    combined_text = f"{extinf.lower()} {' '.join(headers).lower()} {url.lower()}"
    group_match = re.search(r'group-title="([^"]+)"', extinf.lower())
    if group_match and any(k in group_match.group(1) for k in nsfw_keywords):
        return True
    return any(k in combined_text for k in nsfw_keywords)

def write_merged_playlist(all_channels):
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]

    sortable = []
    for extinf, headers, url in all_channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        group = group_match.group(1) if group_match else "Other"
        title_match = re.search(r',([^,]+)$', extinf)
        title = title_match.group(1).strip() if title_match else ""
        sortable.append((group.lower(), title.lower(), group, extinf, headers, url))

    sorted_channels = sorted(sortable)

    current_group = None
    count = 0

    for _, _, group_name, extinf, headers, url in sorted_channels:
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

    print(f"\n✅ Wrote {count} clean channels to {OUTPUT_FILE} ({len(final_output.splitlines())} lines).")

def write_removed_channels(nsfw_channels):
    if not nsfw_channels:
        return
    with open(REMOVED_FILE, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for extinf, headers, url in nsfw_channels:
            f.write(extinf + "\n")
            for h in headers:
                f.write(h + "\n")
            f.write(url + "\n\n")
    print(f"🗑️ Logged {len(nsfw_channels)} removed NSFW/XXX/Porn entries to {REMOVED_FILE}")

if __name__ == "__main__":
    print(f"🚀 Starting merge: {datetime.now()}\n")

    all_channels = []

    for url in playlist_urls:
        lines = fetch_playlist(url)
        all_channels.extend(parse_playlist(lines, url))

    # Filter NSFW
    nsfw_channels = [entry for entry in all_channels if is_nsfw(*entry)]
    clean_channels = [entry for entry in all_channels if not is_nsfw(*entry)]

    write_removed_channels(nsfw_channels)
    write_merged_playlist(clean_channels)

    print(f"\n✅ Merge complete: {datetime.now()}")
