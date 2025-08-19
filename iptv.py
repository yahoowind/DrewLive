import requests
import re
from datetime import datetime

playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveVOD.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TVPass.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Radio.m3u8",
    "http://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PPVLand.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PBSKids.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "http://drewlive24.duckdns.org:8081/StreamedSU.m3u8",
    "http://drewlive24.duckdns.org:8081/Tims247.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/AriaPlus.m3u8"
]

UDPTV_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u"
EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "MergedPlaylist.m3u8"

def fetch_playlist(url):
    print(f"Fetching playlist: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.content.decode("utf-8", errors="ignore")
        return content.strip().splitlines()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

def extract_udptv_timestamp(lines):
    for line in lines:
        if line.strip().startswith("# Last forced update:"):
            print(f"✅ UDPTV timestamp found: {line.strip()}")
            return line.strip()
    print("⚠️ UDPTV timestamp not found.")
    return None

def parse_playlist(lines, source="Unknown"):
    parsed = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            metadata_lines = []
            i += 1

            while i < len(lines):
                next_line = lines[i].strip()
                if next_line == "":
                    i += 1
                elif next_line.startswith("#") and not next_line.startswith("#EXTINF:"):
                    metadata_lines.append(next_line)
                    i += 1
                elif next_line.startswith("#EXTINF:"):
                    break
                else:
                    url = next_line
                    i += 1
                    parsed.append((extinf, tuple(metadata_lines), url))
                    break
        else:
            i += 1

    print(f"✅ Parsed {len(parsed)} entries from {source}")
    return parsed

def write_merged_playlist(channels, udptv_timestamp):
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"']
    if udptv_timestamp:
        lines.append(udptv_timestamp)
    lines.append("")

    def get_group_title(extinf):
        m = re.search(r'group-title="([^"]+)"', extinf)
        return m.group(1) if m else "Other"

    def get_channel_name(extinf):
        m = re.search(r',([^,]+)$', extinf)
        return m.group(1).strip() if m else ""

    # Sort by group and then channel name
    sorted_channels = sorted(
        channels,
        key=lambda c: (get_group_title(c[0]).lower(), get_channel_name(c[0]).lower())
    )

    current_group = None
    for extinf, metadata, url in sorted_channels:
        group = get_group_title(extinf)
        if group != current_group:
            if current_group is not None:
                lines.append("")  # blank line between groups
            lines.append(f'#EXTGRP:{group}')
            current_group = group

        lines.append(extinf)
        lines.extend(metadata)
        lines.append(url)

    if lines and lines[-1] != "":
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Merged playlist saved to {OUTPUT_FILE}")
    print(f"📺 Total channels: {len(channels)}")
    print(f"🕒 Saved at: {datetime.now()}")

if __name__ == "__main__":
    print(f"Starting merge at {datetime.now()}\n")

    all_channels = []  # Use a list to preserve every channel

    # Fetch UDPTV first
    udptv_lines = fetch_playlist(UDPTV_URL)
    udptv_timestamp = extract_udptv_timestamp(udptv_lines)
    udptv_channels = parse_playlist(udptv_lines, source="UDPTV")
    all_channels.extend(udptv_channels)

    # Fetch and parse all other playlists
    for url in playlist_urls:
        if url == UDPTV_URL:
            continue
        lines = fetch_playlist(url)
        parsed = parse_playlist(lines, source=url)
        all_channels.extend(parsed)  # preserve all entries

    # Write the merged playlist
    write_merged_playlist(all_channels, udptv_timestamp)

    print(f"\nMerge complete at {datetime.now()}")
