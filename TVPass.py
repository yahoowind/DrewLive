import requests

UPSTREAM_URL = "http://tvpass.org/playlist/m3u"
LOCAL_FILE = "TVPass.m3u"

def fetch_upstream_urls():
    """Get all URLs from upstream (lines not starting with #)"""
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    lines = res.text.splitlines()
    return [line.strip() for line in lines if line and not line.startswith("#")]

def read_local_playlist():
    with open(LOCAL_FILE, "r", encoding="utf-8") as f:
        return f.read().splitlines()

def update_playlist(local_lines, upstream_urls):
    output = []
    url_idx = 0
    i = 0

    while i < len(local_lines):
        line = local_lines[i].strip()
        if line.startswith("#EXTINF"):
            # Metadata line - keep as-is
            output.append(local_lines[i])
            i += 1
            # Next line should be URL - replace with upstream URL if available
            if url_idx < len(upstream_urls):
                output.append(upstream_urls[url_idx])
                url_idx += 1
            else:
                # No more upstream URLs, keep old URL
                output.append(local_lines[i] if i < len(local_lines) else "")
            i += 1
        else:
            # Lines that aren't #EXTINF (headers, comments, blank) keep as-is
            output.append(local_lines[i])
            i += 1

    return output

def main():
    local_lines = read_local_playlist()
    upstream_urls = fetch_upstream_urls()

    updated_lines = update_playlist(local_lines, upstream_urls)

    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines) + "\n")

    print(f"✅ Updated {LOCAL_FILE} with {len(upstream_urls)} new URLs, metadata preserved.")

if __name__ == "__main__":
    main()
