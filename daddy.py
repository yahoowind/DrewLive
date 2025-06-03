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
TV_ID_FILE = 'tv-ids.txt'
LOGO_FILE = 'logos.txt'


def normalize(name):
    return name.lower().strip().replace(' hd', '').replace(' us', '').replace(' au', '').replace(' ca', '')


def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params['url'][0] if 'url' in query_params else url


def load_metadata(file_path):
    data = {}
    if os.path.exists(file_path):
        with open(file_path, encoding='utf-8') as f:
            for line in f:
                if '|' in line:
                    name, value = line.strip().split('|', 1)
                    data[normalize(name)] = value
    return data


def update_extinf(extinf, group_title, tvg_id, logo):
    # Replace or insert group-title
    if 'group-title="' in extinf:
        extinf = re.sub(r'group-title="[^"]*"', f'group-title="{group_title}"', extinf)
    else:
        extinf = extinf.replace(',', f' group-title="{group_title}",', 1)

    # Replace or insert tvg-id
    if tvg_id:
        if 'tvg-id="' in extinf:
            extinf = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tvg_id}"', extinf)
        else:
            extinf = extinf.replace('#EXTINF:', f'#EXTINF:-1 tvg-id="{tvg_id}"', 1)

    # Replace or insert tvg-logo
    if logo:
        if 'tvg-logo="' in extinf:
            extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo}"', extinf)
        else:
            extinf = extinf.replace('#EXTINF:', f'#EXTINF:-1 tvg-logo="{logo}"', 1)

    return extinf


def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    tv_ids = load_metadata(TV_ID_FILE)
    logos = load_metadata(LOGO_FILE)

    channels = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            raw_url_line = lines[i + 1] if i + 1 < len(lines) else ''
            clean_url = unwrap_url(raw_url_line.strip())

            channel_name = line.split(',')[-1].strip()
            norm_name = normalize(channel_name)

            # Check if it's from an allowed country
            group_title = None
            for country, group in ALLOWED_COUNTRIES.items():
                if country.lower() in line.lower():
                    group_title = group
                    break

            if group_title:
                tvg_id = tv_ids.get(norm_name)
                logo = logos.get(norm_name)
                updated_extinf = update_extinf(line, group_title, tvg_id, logo)
                channels.append((group_title, updated_extinf, clean_url))
            i += 2
        else:
            i += 1

    # Sort by group title
    channels.sort(key=lambda x: x[0])

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"\n')
        for _, extinf, url in channels:
            f.write(extinf + '\n')
            f.write(url + '\n')


if __name__ == '__main__':
    main()
