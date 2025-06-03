import requests
import re
import urllib.parse

# Your allowed countries mapped to group names
ALLOWED_COUNTRIES = {
    'UNITED STATES': 'DaddyLive USA',
    'UNITED KINGDOM': 'DaddyLive UK',
    'CANADA': 'DaddyLive CA',
    'AUSTRALIA': 'DaddyLive AU',
    'NEW ZEALAND': 'DaddyLive NZ'
}

SOURCE_URL = 'https://drewski2423-dproxy.hf.space/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'

LOGOS_FILE = r'C:\Users\andre\Desktop\IPTV\Scripts\logos.txt'
TVIDS_FILE = r'C:\Users\andre\Desktop\IPTV\Scripts\tvids.txt'


def load_mapping(file_path):
    mapping = {}
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '|' not in line:
                continue
            name, val = line.split('|', 1)
            mapping[name.strip().lower()] = val.strip()
    return mapping


def unwrap_url(url):
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    if 'url' in query_params:
        return query_params['url'][0]
    return url


def get_country_from_line(line):
    for country in ALLOWED_COUNTRIES.keys():
        if country.lower() in line.lower():
            return country
    return None


def update_group_title(extinf_line, country):
    group_name = ALLOWED_COUNTRIES[country]
    if 'group-title="' in extinf_line:
        extinf_line = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', extinf_line)
    else:
        parts = extinf_line.split(',', 1)
        extinf_line = parts[0] + f' group-title="{group_name}",' + parts[1]
    return extinf_line


def update_extinf_line(extinf_line, tv_ids, logos):
    # Extract channel display name
    if ',' not in extinf_line:
        return extinf_line  # malformed
    prefix, display_name = extinf_line.split(',', 1)
    key = display_name.strip().lower()

    # Update tvg-id
    tvg_id = tv_ids.get(key)
    if tvg_id:
        if re.search(r'tvg-id="[^"]*"', prefix):
            prefix = re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tvg_id}"', prefix)
        else:
            prefix += f' tvg-id="{tvg_id}"'

    # Update tvg-logo
    tvg_logo = logos.get(key)
    if tvg_logo:
        if re.search(r'tvg-logo="[^"]*"', prefix):
            prefix = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{tvg_logo}"', prefix)
        else:
            prefix += f' tvg-logo="{tvg_logo}"'

    return f'{prefix},{display_name}'


def main():
    tv_ids = load_mapping(TVIDS_FILE)
    logos = load_mapping(LOGOS_FILE)

    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    output_lines = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            country = get_country_from_line(line)
            if not country:
                # Skip this channel completely if country not allowed
                i += 2
                continue

            # Update group-title to your allowed country group name
            updated_line = update_group_title(line, country)

            # Apply tvg-id and tvg-logo overrides
            updated_line = update_extinf_line(updated_line, tv_ids, logos)
            output_lines.append(updated_line)

            # Write the URL, unwrapped if needed
            if i + 1 < len(lines):
                url_line = unwrap_url(lines[i + 1].strip())
                output_lines.append(url_line)
            i += 2
        else:
            # Preserve lines not part of channels (like comments)
            output_lines.append(line)
            i += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines) + '\n')


if __name__ == '__main__':
    main()
