import requests

UPSTREAM_URL = "http://tvpass.org/playlist/m3u"
LOCAL_FILE = "TVPass.m3u"

def fetch_upstream_pairs():
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    lines = res.text.splitlines()
    pairs = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            meta = lines[i].strip()
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                pairs.append((meta, url))
        i += 1
    return pairs

def parse_local_playlist():
    with open(LOCAL_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    header = lines[0] if lines and lines[0].startswith("#EXTM3U") else "#EXTM3U"
    pairs = []
    i = 1
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            meta = lines[i].strip()
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                pairs.append((meta, url))
        i += 1
    return header, pairs

def extract_title(extinf_line):
    return extinf_line.split(",")[-1].strip().lower()

def update_playlist(local_pairs, upstream_pairs):
    updated = []
    used_titles = set()

    upstream_map = {extract_title(meta): url for meta, url in upstream_pairs}

    for meta, url in local_pairs:
        title = extract_title(meta)
        if title in upstream_map:
            updated.append((meta, upstream_map[title]))  # Update URL
            used_titles.add(title)
        else:
            updated.append((meta, url))  # Keep as-is

    # Add new entries from upstream that don't exist locally
    for meta, url in upstream_pairs:
        title = extract_title(meta)
        if title not in used_titles:
            updated.append((meta, url))

    return updated

def write_playlist(header, updated_pairs):
    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        for meta, url in updated_pairs:
            f.write(meta + "\n")
            f.write(url + "\n")
    print(f"✅ Updated {LOCAL_FILE} with {len(updated_pairs)} total streams.")

def main():
    header, local_pairs = parse_local_playlist()
    upstream_pairs = fetch_upstream_pairs()
    updated_pairs = update_playlist(local_pairs, upstream_pairs)
    write_playlist(header, updated_pairs)

if __name__ == "__main__":
    main()
