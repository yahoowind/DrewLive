import requests
import re

ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}

SOURCE_URL = 'http://drewlive24.duckdns.org:8989/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'

def get_group_title(extinf_line):
    for country, group_name in ALLOWED_COUNTRIES.items():
        if country in extinf_line:
            if 'group-title="' in extinf_line:
                extinf_line = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', extinf_line)
            else:
                parts = extinf_line.split(',', 1)
                extinf_line = parts[0] + f' group-title="{group_name}",' + parts[1]
            return extinf_line
    return None

def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # Embed the EPG URL here
        f.write('#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('#EXTINF'):
                new_extinf_line = get_group_title(line)
                url_line = lines[i + 1] if i + 1 < len(lines) else ''
                if new_extinf_line:
                    f.write(new_extinf_line + '\n')
                    f.write(url_line + '\n')
                i += 2
            else:
                i += 1

if __name__ == '__main__':
    main()
