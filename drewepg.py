import gzip
import re
import requests
import time
from xml.etree import ElementTree as ET
from io import BytesIO

epg_sources = [
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Plex/all.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/PlutoTV/all.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/SamsungTVPlus/all.xml",
    "https://raw.githubusercontent.com/BuddyChewChew/localnow-playlist-generator/refs/heads/main/epg.xml",
    "https://tvpass.org/epg.xml",
    "https://animenosekai.github.io/japanterebi-xmltv/guide.xml",
    "https://raw.githubusercontent.com/luongz/iptv-jp/refs/heads/main/.xmltv_id",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Roku/all.xml",
    "https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz"
]

playlist_url = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/MergedPlaylist.m3u8"

output_filename = "DrewLive.xml.gz"

def fetch_tvg_ids_from_playlist(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                                 "Chrome/140.0.0.0 Safari/537.36"}
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        ids = set(re.findall(r'tvg-id="([^"]+)"', r.text))
        print(f"✅ Loaded {len(ids)} tvg-ids from playlist")
        return ids
    except Exception as e:
        print(f"❌ Failed to fetch tvg-ids from playlist: {e}")
        return set()

def fetch_with_retry(url, retries=3, delay=10, timeout=30):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/140.0.0.0 Safari/537.36"}
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(delay)
    return None

def stream_parse_epg(file_obj, valid_tvg_ids, root):
    kept_channels = 0
    total_items = 0
    try:
        tree = ET.parse(file_obj)
        for child in tree.getroot():
            if child.tag in ('channel', 'programme'):
                total_items += 1
                tvg_id = child.get('id') or child.get('channel')
                if tvg_id in valid_tvg_ids:
                    root.append(child)
                    kept_channels += 1
    except ET.ParseError:
        print("❌ XML Parse Error")
    return total_items, kept_channels

def merge_and_filter_epg(epg_sources, playlist_url, output_file):
    valid_tvg_ids = fetch_tvg_ids_from_playlist(playlist_url)
    root = ET.Element("tv")
    cumulative_kept = 0
    cumulative_total = 0

    for url in epg_sources:
        print(f"\n🌐 Processing: {url}")
        resp = fetch_with_retry(url, retries=3, delay=10, timeout=60)
        if not resp:
            print(f"❌ Failed to fetch {url}")
            continue

        content = resp.content
        if url.endswith(".gz") or content[:2] == b'\x1f\x8b':
            try:
                content = gzip.decompress(content)
            except Exception as e:
                print(f"⚠️ Failed to decompress {url}: {e}")
                continue

        total, kept = stream_parse_epg(BytesIO(content), valid_tvg_ids, root)
        cumulative_total += total
        cumulative_kept += kept
        print(f"📊 Total items found: {total}, Kept: {kept}")

    with gzip.open(output_file, "wt", encoding="utf-8") as f:
        ET.ElementTree(root).write(f, encoding="unicode", xml_declaration=True)

    print(f"\n✅ Filtered EPG saved to: {output_file}")
    print(f"📈 Cumulative items processed: {cumulative_total}")
    print(f"📈 Total items kept: {cumulative_kept}")

if __name__ == "__main__":
    merge_and_filter_epg(epg_sources, playlist_url, output_filename)
