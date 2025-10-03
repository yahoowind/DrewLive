import gzip
import re
import time
from io import BytesIO
from xml.etree import ElementTree as ET
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# === SOURCES ===
# List of EPG sources to fetch and merge.
epg_sources = [
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Plex/all.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/PlutoTV/all.xml",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/SamsungTVPlus/all.xml",
    "https://raw.githubusercontent.com/BuddyChewChew/localnow-playlist-generator/refs/heads/main/epg.xml",
    "https://tvpass.org/epg.xml",
    "https://animenosekai.github.io/japanterebi-xmltv/guide.xml",
    "https://epg.freejptv.com/jp.xml", # This is the problematic URL
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Roku/all.xml",
    "https://raw.githubusercontent.com/BuddyChewChew/xumo-playlist-generator/main/playlists/xumo_epg.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz"
]

# The M3U8 playlist URL to get the list of valid TVG IDs from.
playlist_url = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/MergedPlaylist.m3u8"
# The name of the final output file.
output_filename = "DrewLive.xml.gz"

# === REQUEST HEADERS ===
# Using a realistic User-Agent to avoid being blocked.
BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/xml,text/html,application/xhtml+xml,text/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
}

# Initialize a requests session to reuse connections and headers.
session = requests.Session()
session.headers.update(BASE_HEADERS)
session.max_redirects = 5

# === FETCH TVG IDs ===
def fetch_tvg_ids_from_playlist(url):
    """Fetches the content of a playlist and extracts all unique tvg-id values."""
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        ids = set(re.findall(r'tvg-id="([^"]+)"', r.text))
        print(f"✅ Loaded {len(ids)} unique tvg-ids from playlist.")
        return ids
    except requests.RequestException as e:
        print(f"❌ Failed to fetch tvg-ids from playlist: {e}")
        return set()


# === PLAYWRIGHT FETCH ===
def fetch_protected_url_with_playwright(url, timeout=90):
    """
    Uses Playwright to fetch content from a URL protected by anti-bot measures.
    This is necessary for sites that require JavaScript to render.
    """
    print("⏳ Attempting to fetch with Playwright...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Go to the page and wait until the network is idle, which indicates
            # that JavaScript challenges are likely complete.
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            # Add a small extra delay just in case.
            page.wait_for_timeout(5000)
            content = page.content()
            browser.close()
            print("✅ Playwright successfully fetched the page content.")
            return content.encode("utf-8")
    except PlaywrightTimeoutError:
        print(f"❌ Playwright timed out after {timeout} seconds for {url}.")
        return None
    except Exception as e:
        print(f"❌ An unexpected Playwright error occurred for {url}: {e}")
        return None


# === FETCH WITH RETRY ===
def fetch_with_retry(url, retries=3, initial_delay=3, timeout=60):
    """
    Fetches a URL, with special handling for the protected freejptv.com.
    Implements an exponential backoff retry mechanism.
    """
    attempt = 0
    while attempt < retries:
        attempt += 1
        try:
            # Special handling for the protected URL.
            if "freejptv.com" in url:
                content = fetch_protected_url_with_playwright(url, timeout=90)
                if content:
                    # Wrap the content in a dummy response object to maintain a consistent interface.
                    class DummyResponse:
                        def __init__(self, content):
                            self.content = content
                    return DummyResponse(content)
                # If Playwright fails, we'll hit the retry logic below.
                raise Exception("Playwright failed to retrieve content.")
            else:
                r = session.get(url, timeout=timeout)
                r.raise_for_status()
                return r
        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                delay = initial_delay * (2 ** (attempt - 1))
                print(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
    return None


# === PARSE XML ===
def stream_parse_epg(file_obj, valid_tvg_ids, root_element):
    """
    Parses an XML file object and appends only the elements
    (channel and programme) with a valid tvg-id to the root element.
    """
    kept_items = 0
    total_items = 0
    try:
        tree = ET.parse(file_obj)
        for child in tree.getroot():
            total_items += 1
            # Check for 'channel' or 'programme' tags.
            # Handles 'program' as a fallback.
            if child.tag in ("channel", "programme", "program"):
                # The ID for a channel is in 'id', for a programme it's in 'channel'.
                tvg_id = child.get("id") or child.get("channel")
                if tvg_id in valid_tvg_ids:
                    root_element.append(child)
                    kept_items += 1
    except ET.ParseError as e:
        print(f"❌ XML Parse Error: {e}. Skipping this source.")
    return total_items, kept_items


# === MERGE & FILTER ===
def merge_and_filter_epg(sources, playlist, output_file):
    """Main function to orchestrate the fetching, filtering, and saving process."""
    valid_tvg_ids = fetch_tvg_ids_from_playlist(playlist)
    if not valid_tvg_ids:
        print("❌ No valid TVG IDs found. Aborting.")
        return

    root = ET.Element("tv")
    cumulative_kept = 0
    cumulative_total = 0

    for url in sources:
        print(f"\n🌐 Processing: {url}")
        resp = fetch_with_retry(url)
        if not resp:
            print(f"❌ Failed to fetch {url} after multiple retries. Skipping.")
            continue

        content = resp.content
        # Decompress if it's a gzipped file (checks by extension or magic bytes).
        is_gzipped = url.endswith(".gz") or content.startswith(b"\x1f\x8b")
        if is_gzipped:
            try:
                content = gzip.decompress(content)
                print("   Decompressed GZIP content.")
            except Exception as e:
                print(f"⚠️ Failed to decompress {url}: {e}. Skipping.")
                continue

        # Use BytesIO to treat the content as a file for parsing.
        total, kept = stream_parse_epg(BytesIO(content), valid_tvg_ids, root)
        cumulative_total += total
        cumulative_kept += kept
        if total > 0:
            print(f"📊 Found {total} items, kept {kept} ({kept/total:.1%}).")
        else:
            print("📊 No items found in this source.")

    # Write the final merged and filtered XML to a new gzipped file.
    try:
        with gzip.open(output_file, "wt", encoding="utf-8") as f:
            tree = ET.ElementTree(root)
            # Use the 'unicode' encoding argument to get a UTF-8 string.
            tree.write(f, encoding="unicode", xml_declaration=True)
        
        print(f"\n✅ Filtered EPG saved to: {output_file}")
        print(f"📈 Cumulative items processed: {cumulative_total}")
        print(f"📈 Total unique items kept: {len(root)}")

    except Exception as e:
        print(f"❌ Failed to write the final output file: {e}")


if __name__ == "__main__":
    start_time = time.time()
    merge_and_filter_epg(epg_sources, playlist_url, output_filename)
    end_time = time.time()
    print(f"\n✨ Done in {end_time - start_time:.2f} seconds.")
