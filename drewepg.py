import gzip
import re
import requests
import time
from xml.etree import ElementTree as ET
from io import BytesIO
from urllib.parse import urlparse

# === CONFIG ===
epg_sources = [
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Plex/all.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/PlutoTV/all.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/SamsungTVPlus/all.xml",
    "https://raw.githubusercontent.com/BuddyChewChew/localnow-playlist-generator/refs/heads/main/epg.xml",
    "https://tvpass.org/epg.xml",
    "https://animenosekai.github.io/japanterebi-xmltv/guide.xml",
    "https://epg.freejptv.com/jp.xml", 
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Roku/all.xml",
    "https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz"
]

playlist_url = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/MergedPlaylist.m3u8"
output_filename = "DrewLive.xml.gz"

# === HEADERS ===
BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "application/xml, text/xml, */*;q=0.1",
    "Accept-Language": "en-US,en;q=0.9",
}

FREEJP_HEADERS = {
    **BASE_HEADERS,
    "Accept": "*/*",
    "Origin": "https://freejptv.com",
    "Referer": "https://freejptv.com/",
    "Sec-CH-UA": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Connection": "keep-alive",
}

session = requests.Session()
session.headers.update(BASE_HEADERS)
session.max_redirects = 5


# === FETCH TVG IDs ===
def fetch_tvg_ids_from_playlist(url):
    try:
        r = session.get(url.strip(), timeout=30)
        r.raise_for_status()
        ids = set(re.findall(r'tvg-id="([^"]+)"', r.text))
        print(f"✅ Loaded {len(ids)} tvg-ids from playlist")
        return ids
    except Exception as e:
        print(f"❌ Failed to fetch tvg-ids from playlist: {e}")
        return set()


# === FETCH URL WITH RETRIES ===
def fetch_with_retry(url, retries=5, initial_delay=3, timeout=30):
    """Fetch URL with retries and exponential backoff. Uses FreeJPTV headers if needed."""
    url = url.strip().rstrip(":")  # remove whitespace & trailing colon
    parsed = urlparse(url)
    headers = BASE_HEADERS.copy()
    if parsed.hostname and "freejptv.com" in parsed.hostname:
        headers = FREEJP_HEADERS

    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            r = session.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.HTTPError as he:
            status = getattr(he.response, "status_code", None)
            print(f"⚠️ Attempt {attempt} failed for {url}: {he} (status={status})")
        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed for {url}: {e}")
        sleep_time = min(initial_delay * (2 ** (attempt - 1)), 60)
        time.sleep(sleep_time)
    return None


# === PARSE EPG XML STREAM ===
def stream_parse_epg(file_obj, valid_tvg_ids, root):
    kept_channels = 0
    total_items = 0
    try:
        tree = ET.parse(file_obj)
        for child in tree.getroot():
            tag = child.tag
            if "}" in tag:
                tag = tag.split("}", 1)[1]  # strip namespace
            if tag in ("channel", "programme", "program"):
                total_items += 1
                tvg_id = child.get("id") or child.get("channel")
                if tvg_id in valid_tvg_ids:
                    root.append(child)
                    kept_channels += 1
    except ET.ParseError:
        print("❌ XML Parse Error")
    return total_items, kept_channels


# === MERGE & FILTER ===
def merge_and_filter_epg(epg_sources, playlist_url, output_file):
    valid_tvg_ids = fetch_tvg_ids_from_playlist(playlist_url)
    if not valid_tvg_ids:
        print("⚠️ No tvg-ids loaded; result will be empty.")
    root = ET.Element("tv")
    cumulative_kept = 0
    cumulative_total = 0

    for url in epg_sources:
        url = url.strip().rstrip(":")  # sanitize URL
        print(f"\n🌐 Processing: {url}")
        resp = fetch_with_retry(url, retries=5, initial_delay=3, timeout=60)
        if not resp:
            print(f"❌ Failed to fetch {url}")
            continue

        content = resp.content
        if url.endswith(".gz") or (len(content) >= 2 and content[:2] == b"\x1f\x8b"):
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
