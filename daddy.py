import requests
import re
import urllib.parse
import os

ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}

SOURCE_URL = 'https://drewski2423-dproxy.hf.space/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TVIDS_FILE = 'tvids.txt'
LOGOS_FILE = 'logos.txt'


def load_mapping(file_path):
    mapping = {}
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return mapping
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' in line:
                name, val = line.strip().split('|', 1)
                mapping[name.strip().lower()] = val.strip()
    return mapping


def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params.get('url', [url])[0]


def extract_group_title(line):
    match = re.search(r'group-title="([^"]+)"', line)
    return match.group(1).strip().upper() if match else None


def replace_group_title(line, old_group):
    return re.sub(r'group-title="[^"]+"', f'group-title="{ALLOWED_COUNTRIES[old_group]}"', line)


def update_extinf(line, display_name, tv_ids, logos):
    prefix = line.split(',', 1)[0]
    key = display_name.strip().lower()

    # tvg-id
    if key in tv_ids:
        if 'tvg-id="' in prefix:
            prefix = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tv_ids[key]}"', prefix)
        else:
            prefix += f' tvg-id="{tv_ids[key]}"'

    # tvg-logo
    if key in logos:
        if 'tvg-logo="' in prefix:
            prefix = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logos[key]}"', prefix)
        else:
            prefix += f' tvg-logo="{logos[key]}"'

    return f'{prefix},{display_name}'


def main():
    tv_ids = load_mapping(TVIDS_FILE)
    logos = load_mapping(LOGOS_FILE)

    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    result = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    i = 0
    kept = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF') and (i + 1) < len(lines):
            display_name = line.split(',', 1)[1].strip()
            group_title = extract_group_title(line)

            if group_title and group_title.upper() in ALLOWED_COUNTRIES:
                # Rename group-title
                line = replace_group_title(line, group_title.upper())

                # Update tvg-id and logo
                line = update_extinf(line, display_name, tv_ids, logos)

                # Append only matching entries
                result.append(line)
                result.append(unwrap_url(lines[i + 1].strip()))
                kept += 1

            i += 2
        else:
            i += 1  # Skip non-EXTINF lines

    with open(os.path.join(BASE_DIR, OUTPUT_FILE), 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    print(f"[+] Wrote {kept} channels (only from allowed groups) to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
