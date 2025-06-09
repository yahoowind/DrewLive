import requests

UPSTREAM_URL = "http://tvpass.org/playlist/m3u"
OUTPUT_FILE = "TVPass.m3u"
FORCED_GROUP = "TVPass"

def fetch_upstream_urls():
    res = requests.get(UPSTREAM_URL, timeout=15)
    res.raise_for_status()
    lines = res.text.splitlines()
    # Extract stream URLs only (lines not starting with #)
    return [line.strip() for line in lines if not line.startswith("#")]

def force_group_title(line):
    if not line.startswith("#EXTINF"):
        return line

    comma_index = line.find(",")
    if comma_index == -1:
        return line  # Malformed? Leave untouched

    meta = line[:comma_index]
    title = line[comma_index:]

    if 'group-title="' in meta:
        # Replace existing group-title
        before = meta.split('group-title="')[0]
        after = meta.split('group-title="')[1].split('"', 1)[1]
        rest = after  # Keep anything after group-title=""
        # Rebuild line with forced group-title
        new_meta = before + f'group-title="{FORCED_GROUP}"' + rest
    else:
        # Add group-title at end of metadata
        new_meta = meta + f' group-title="{FORCED_GROUP}"'

    return new_meta + title

def process_playlist(local_lines, upstream_urls):
    output_lines = []
    url_index = 0
    i = 0

    while i < len(local_lines):
        line = local_lines[i].strip()

        if line.startswith("#EXTINF"):
            # Force group-title
            output_lines.append(force_group_title(line))
            i += 1
            if i < len(local_lines):
                if url_index < len(upstream_urls):
                    output_lines.append(upstream_urls[url_index])  # Replace URL
                    url_index += 1
                else:
                    output_lines.append(local_lines[i])  # Fallback: keep original
            i += 1
        else:
            output_lines.append(line)
            i += 1

    return output_lines

def main():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        local_lines = f.read().splitlines()

    upstream_urls = fetch_upstream_urls()
    updated_lines = process_playlist(local_lines, upstream_urls)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines) + "\n")

    print(f"[✅] TVPass.m3u updated: URLs refreshed + group-title='{FORCED_GROUP}' enforced. Nothing else touched.")

if __name__ == "__main__":
    main()