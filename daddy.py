import requests

# Allowed full country names in ALL CAPS
ALLOWED_COUNTRIES = [
    'UNITED STATES',
    'UNITED KINGDOM',
    'CANADA',
    'AUSTRALIA',
    'NEW ZEALAND'
]

SOURCE_URL = 'http://drewlive24.duckdns.org:7860/playlist/channels'
OUTPUT_FILE = 'DaddyLive.m3u8'

def country_allowed(extinf_line):
    return any(country in extinf_line for country in ALLOWED_COUNTRIES)

def main():
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('#EXTINF'):
                extinf_line = line
                url_line = lines[i + 1] if i + 1 < len(lines) else ''
                if country_allowed(extinf_line):
                    f.write(extinf_line + '\n')
                    f.write(url_line + '\n')
                i += 2
            else:
                i += 1

if __name__ == '__main__':
    main()