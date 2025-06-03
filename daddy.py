import requests
import re
import urllib.parse

ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}

SOURCE_URL = 'http://drewlive24.duckdns.org:7860/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'


def get_group_title(extinf_line):
    for country, group_name in ALLOWED_COUNTRIES.items():
        if country.lower() in extinf_line.lower():
            if 'group-title="' in extinf_line:
                extinf_line = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', extinf_line)
            else:
                parts = extinf_line.split(',', 1)
                extinf_line = parts[0] + f' group-title="{group_name}",' + parts[1]
            return extinf_line, group_name
    return None, None


def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    if 'url' in query_params:
        return query_params['url'][0]
    return url


def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    channels = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            new_extinf_line, group_name = get_group_title(line)
            raw_url_line = lines[i + 1] if i + 1 < len(lines) else ''
            clean_url_line = unwrap_url(raw_url_line.strip())
            if new_extinf_line:
                channels.append((group_name, new_extinf_line, clean_url_line))
            i += 2
        else:
            i += 1

    # Sort channels by group_name alphabetically
    channels.sort(key=lambda x: x[0])

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"\n')
        for _, extinf_line, url_line in channels:
            f.write(extinf_line + '\n')
            f.write(url_line + '\n')


if __name__ == '__main__':
    main()
