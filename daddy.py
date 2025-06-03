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


def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    return query_params['url'][0] if 'url' in query_params else url


def update_group_title(extinf_line):
    for country, group_name in ALLOWED_COUNTRIES.items():
        if country.lower() in extinf_line.lower():
            if 'group-title="' in extinf_line:
                extinf_line = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', extinf_line)
            else:
                extinf_line = extinf_line.replace(',', f' group-title="{group_name}",', 1)
            return extinf_line, group_name
    return extinf_line, 'Other'


def load_existing_metadata():
    existing = {}
    if not os.path.exists(OUTPUT_FILE):
        return existing

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        for i in range(0, len(lines) - 1, 2):
            extinf = lines[i]
            url = lines[i + 1]
            name = extinf.split(',')[-1].strip().lower()
            existing[name] = (extinf, url)
    return existing


def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    existing_channels = load_existing_metadata()
    updated_channels = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            raw_extinf = line
            raw_url = lines[i + 1] if i + 1 < len(lines) else ''
            name = raw_extinf.split(',')[-1].strip().lower()

            # unwrap URL
            clean_url = unwrap_url(raw_url.strip())

            # use existing EXTINF metadata if available
            if name in existing_channels:
                extinf_line = existing_channels[name][0]
                extinf_line, group_name = update_group_title(extinf_line)
            else:
                extinf_line, group_name = update_group_title(raw_extinf)

            updated_channels.append((group_name, extinf_line, clean_url))
            i += 2
        else:
            i += 1

    # sort by group
    updated_channels.sort(key=lambda x: x[0])

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"\n')
        for _, extinf, url in updated_channels:
            f.write(extinf + '\n')
            f.write(url + '\n')


if __name__ == '__main__':
    main()
