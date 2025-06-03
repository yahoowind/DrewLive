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


def get_group_title(display_name, tv_ids):
    # Check if any allowed country name is inside display name
    for country_name, group_title in ALLOWED_COUNTRIES.items():
        if country_name.lower() in display_name.lower():
            return group_title
    # If display name is in tv_ids, assign USA group by default
    if display_name.lower() in tv_ids:
        return ALLOWED_COUNTRIES['UNITED STATES']
    # Otherwise None - skip channel
    return None


def update_extinf(line, tv_ids, logos):
    if ',' not in line:
        return line
    prefix, display_name = line.split(',', 1)
    key = display_name.strip().lower()

    # Update tvg-id
    if key in tv_ids:
        if 'tvg-id="' in prefix:
            prefix = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tv_ids[key]}"', prefix)
        else:
            prefix += f' tvg-id="{tv_ids[key]}"'

    # Update tvg-logo
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
    count = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            # Get display name part after comma
            if ',' not in line:
                i += 2
                continue
            display_name = line.split(',', 1)[1].strip()

            group = get_group_title(display_name, tv_ids)
            if not group:
                i += 2  # skip this channel + URL
                continue

            # Update or add group-title
            if 'group-title="' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', line)
            else:
                parts = line.split(',', 1)
                line = parts[0] + f' group-title="{group}",' + parts[1]

            # Update tvg-id and tvg-logo
            line = update_extinf(line, tv_ids, logos)

            # Unwrap URL
            stream_url = unwrap_url(lines[i + 1].strip())
            result.append(line)
            result.append(stream_url)

            count += 1
            i += 2
        else:
            i += 1

    with open(os.path.join(BASE_DIR, OUTPUT_FILE), 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    print(f"[+] Processed and wrote {count} channels to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
