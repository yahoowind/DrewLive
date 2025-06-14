import requests

UPSTREAM_URL = "http://tvpass.org/playlist/m3u"
OUTPUT_FILE = "TVPass.m3u"

def fetch_upstream_urls():
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    return [line.strip() for line in res.text.splitlines() if not line.startswith("#")]

def replace_urls(local_lines, new_urls):
    updated = []
    url_index = 0
    i = 0

    while i < len(local_lines):
        line = local_lines[i]

        if line.startswith("#EXTINF"):
            # Keep EXTINF line as-is
            updated.append(line)
            i += 1

            # Replace the following URL line
            if i < len(local_lines) and not local_lines[i].startswith("#"):
                if url_index < len(new_urls):
                    updated.append(new_urls[url_index])
                    url_index += 1
                else:
                    # No new URL — keep old one
                    updated.append(local_lines[i])
                i += 1
        else:
            # Leave all non-stream lines as-is
            updated.append(line)
            i += 1

    return updated

def main():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        local_lines = f.read().splitlines()

    new_urls = fetch_upstream_urls()
    final_lines = replace_urls(local_lines, new_urls)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines) + "\n")

    print("✅ Stream URLs updated. Metadata untouched.")

if __name__ == "__main__":
    main()
