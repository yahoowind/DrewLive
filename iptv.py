import requests
import re
import time
from datetime import datetime

playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewLiveVOD.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TVPass.m3u",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Radio.m3u8",
    "http://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "http://drewlive24.duckdns.org:8081/PPVLand.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/Roku.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "http://drewlive24.duckdns.org:8081/Tims247.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/LGTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/AriaPlus.m3u8",
    "http://drewlive24.duckdns.org:8081/Zuzz.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8"
]

UDPTV_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u"
EPG_URL = "http://drewlive24.duckdns.org:8081/merged2_epg.xml.gz"
OUTPUT_FILE = "MergedPlaylist.m3u8"


def fetch_playlist(url, retries=3, delay=5):
    print(f"📡 Fetching playlist: {url}")
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            content = response.content.decode("utf-8", errors="ignore")
            if "#EXTM3U" not in content:
                print(f"⚠️ Skipping invalid playlist (no #EXTM3U) from {url}")
                return []
            return content.splitlines()
        except Exception as e:
            print(f"❌ Attempt {attempt} failed for {url}: {e}")
            if "raw.githubusercontent.com" not in url and attempt < retries:
                time.sleep(delay)
            else:
                break
    return []


def extract_udptv_timestamp(lines):
    for line in lines:
        if line.strip().startswith("# Last forced update:"):
            return line.strip()
    return None


def parse_playlist(lines, source="Unknown"):
    parsed = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            metadata = []
            i += 1

            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF:"):
                metadata.append(lines[i].strip())
                i += 1

            if (
                i < len(lines)
                and lines[i].strip()
                and not lines[i].strip().startswith("#")
                and re.match(r'^(https?|rtmp|rtsp|udp)://', lines[i].strip())
            ):
                url = lines[i].strip()
                if re.search(r'group-title="([^"]+)"', extinf):
                    parsed.append((extinf, tuple(metadata), url))
                else:
                    print(f"⚠️ Skipping channel with no group-title in {source}: {extinf}")
                i += 1
            else:
                i += 1
        else:
            i += 1
    return parsed


def write_merged_playlist(channels, udptv_timestamp):
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"']
    if udptv_timestamp:
        lines.append(udptv_timestamp)
    lines.append("")

    def get_group_title(extinf, metadata):
        m = re.search(r'group-title="([^"]+)"', extinf)
        return m.group(1) if m else None

    def get_channel_name(extinf):
        m = re.search(r',([^,]+)$', extinf)
        return m.group(1).strip() if m else ""

    sorted_channels = sorted(
        channels,
        key=lambda c: (get_group_title(c[0], c[1]).lower(), get_channel_name(c[0]).lower())
    )

    current_group = None
    for extinf, metadata, url in sorted_channels:
        group = get_group_title(extinf, metadata)
        if not group:
            continue  # skip channels with no group-title
        if group != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f"#EXTGRP:{group}")
            current_group = group

        lines.append(extinf)
        lines.extend(metadata)
        lines.append(url)

    if lines[-1] != "":
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Merged playlist saved to {OUTPUT_FILE}")
    print(f"📺 Total channels: {len(channels)}")
    print(f"🕒 Saved at: {datetime.now()}")


if __name__ == "__main__":
    all_channels = []

    udptv_lines = fetch_playlist(UDPTV_URL)
    udptv_timestamp = extract_udptv_timestamp(udptv_lines)
    all_channels.extend(parse_playlist(udptv_lines, source="UDPTV"))

    for url in playlist_urls:
        if url == UDPTV_URL:
            continue
        lines = fetch_playlist(url)
        all_channels.extend(parse_playlist(lines, source=url))

    write_merged_playlist(all_channels, udptv_timestamp)
