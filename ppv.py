import requests
import re
import time

UPSTREAM_URL = "https://pigscanflyyy-scraper.vercel.app/ppv"
OUTPUT_FILE = "PPVLand.m3u8"

CATEGORY_TVG_IDS = {
    "24/7 Streams": "24.7.Dummy.us",
    "Football": "Soccer.Dummy.us",
    "Wrestling": "PPV.EVENTS.Dummy.us",
    "Combat Sports": "PPV.EVENTS.Dummy.us",
    "Baseball": "MLB.Baseball.Dummy.us",
    "Basketball": "Basketball.Dummy.us",
    "Motorsports": "Racing.Dummy.us",
    "Boxing": "PPV.EVENTS.Dummy.us",
    "Darts": "Darts.Dummy.us",
    "American Football": "NFL.Dummy.us"
}

GROUP_RENAME_MAP = {
    "24/7 Streams": "PPVLand - Live Channels 24/7",
    "Wrestling": "PPVLand - Wrestling Events",
    "Football": "PPVLand - Global Football Streams",
    "Basketball": "PPVLand - Basketball Hub",
    "Baseball": "PPVLand - Baseball Action HD",
    "Combat Sports": "PPVLand - MMA & Fight Nights",
    "Motorsports": "PPVLand - Motorsport Live",
    "Boxing": "PPVLand - Boxing",
    "Darts": "PPVLand - Darts",
    "American Football": "PPVLand - American Football Action NFL/NCAAF"
}

def fetch_url_until_ready(url, delay=5, timeout=60):
    session = requests.Session()
    attempt = 1
    while True:
        try:
            print(f"Attempt {attempt}: Fetching {url} ...")
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            text = r.text.strip()
            if "#EXTINF" in text:
                print("✅ Playlist loaded successfully.")
                return text
            else:
                print(f"Attempt {attempt}: Not a valid playlist, retrying in {delay}s...")
        except Exception as e:
            print(f"Attempt {attempt}: Error fetching {url}: {e}")
        attempt += 1
        time.sleep(delay)

def safe_tvg_id(name: str) -> str:
    if not name:
        return "Uncategorized.Dummy.us"
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '.', name).strip(".")
    return f"{cleaned}.Dummy.us"

def normalize_group_name(name):
    return re.sub(r'\s+', ' ', name.strip()).lower() if name else ""

def modify_playlist(playlist_text):
    seen_categories = set()

    # Normalized maps for matching
    normalized_map = {normalize_group_name(k): v for k, v in GROUP_RENAME_MAP.items()}
    normalized_ids = {normalize_group_name(k): v for k, v in CATEGORY_TVG_IDS.items()}

    def repl(match):
        attrs = match.group(1)
        channel_name = match.group(2)

        group_match = re.search(r'group-title="([^"]+)"', attrs)
        upstream_group = group_match.group(1).strip() if group_match else None
        normalized_upstream = normalize_group_name(upstream_group)

        # Apply remap if exists
        new_group = normalized_map.get(normalized_upstream, upstream_group)
        tvg_id = normalized_ids.get(normalized_upstream, safe_tvg_id(upstream_group))

        seen_categories.add((upstream_group, new_group, tvg_id))

        # Remove old tvg-id/group-title but keep logos and other attrs
        attrs = re.sub(r'tvg-id="[^"]*"', '', attrs)
        attrs = re.sub(r'group-title="[^"]*"', '', attrs)
        attrs = attrs.strip()

        new_attrs = f'tvg-id="{tvg_id}" group-title="{new_group}"'
        if attrs:
            new_attrs = attrs + ' ' + new_attrs

        return f'#EXTINF:{new_attrs},{channel_name}'

    modified = re.sub(r'#EXTINF:([^\n]*?),(.*)', repl, playlist_text)

    print("\n📌 Category Mapping Report:")
    for cat, new_grp, tid in sorted(seen_categories):
        print(f"- Upstream: {cat} → Group: {new_grp}, tvg-id: {tid}")

    return modified

def main():
    print("Fetching upstream playlist...")
    playlist = fetch_url_until_ready(UPSTREAM_URL, delay=5, timeout=60)

    print("Modifying playlist with upstream-following remap...")
    modified_playlist = modify_playlist(playlist)

    print(f"Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(modified_playlist)

    print("✅ Done. Playlist converted with remapped group names where applicable.")

if __name__ == "__main__":
    main()
