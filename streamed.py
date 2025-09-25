import requests
import sys
import re
import concurrent.futures

FALLBACK_LOGOS = {
    "football": "https://i.imgur.com/RvN0XSF.png",
    "soccer":   "https://i.imgur.com/RvN0XSF.png",
    "fight":    "https://i.imgur.com/QlBOQft.png",
    "mma":      "https://i.imgur.com/QlBOQft.png",
    "boxing":   "https://i.imgur.com/QlBOQft.png"
}

def get_all_matches():
    url = "https://streamed.pk/api/matches/all"
    try:
        print("📡 Fetching all matches from the API...")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        print("✅ Successfully fetched match list.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching matches: {e}", file=sys.stderr)
        return None

def get_stream_embed_url(source):
    try:
        src_name = source.get('source')
        src_id = source.get('id')
        if not src_name or not src_id:
            return None
        api_url = f"https://streamed.pk/api/stream/{src_name}/{src_id}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        streams = response.json()
        if streams and streams[0].get('embedUrl'):
            return streams[0]['embedUrl']
    except:
        pass
    return None

def find_m3u8_in_content(page_content):
    patterns = [
        r'source:\s*["\'](https?://[^\'"]+\.m3u8?[^\'"]*)["\']',
        r'file:\s*["\'](https?://[^\'"]+\.m3u8?[^\'"]*)["\']',
        r'hlsSource\s*=\s*["\'](https?://[^\'"]+\.m3u8?[^\'"]*)["\']',
        r'src\s*:\s*["\'](https?://[^\'"]+\.m3u8?[^\'"]*)["\']',
        r'["\'](https?://[^\'"]+\.m3u8?[^\'"]*)["\']'
    ]
    for pattern in patterns:
        match = re.search(pattern, page_content)
        if match:
            return match.group(1)
    return None

def extract_m3u8_from_embed(embed_url):
    if not embed_url:
        return None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://streamed.pk/'
        }
        response = requests.get(embed_url, headers=headers, timeout=15)
        response.raise_for_status()
        return find_m3u8_in_content(response.text)
    except:
        return None

def validate_logo(url, fallback):
    """Replace broken URLs with fallback"""
    if not url:
        return fallback
    try:
        resp = requests.head(url, timeout=5)
        if resp.status_code == 200:
            return url
    except:
        pass
    return fallback

def build_logo_url(match):
    """Returns a safe logo URL and normalized category"""
    api_category = (match.get('category') or '').lower()
    logo_url = None

    # Try badge first
    teams = match.get('teams', {})
    for team_key in ['away','home']:
        team = teams.get(team_key, {})
        badge = team.get('badge') or team.get('id')
        if badge:
            logo_url = f"https://streamed.pk/api/images/badge/{badge}.webp"
            break

    # Try poster if no badge
    if not logo_url and match.get('poster'):
        poster = match['poster']
        logo_url = f"https://streamed.pk/api/images/proxy/{poster}.webp"

    # Apply your fallback logic only if category matches
    for key in FALLBACK_LOGOS:
        if key in api_category:
            logo_url = validate_logo(logo_url, FALLBACK_LOGOS[key])
            break

    # If category doesn’t match any fallback, keep original badge/poster (even if broken)
    return logo_url, api_category

def process_match(match):
    title = match.get('title','Untitled Match')
    sources = match.get('sources', [])
    for source in sources:
        embed_url = get_stream_embed_url(source)
        if embed_url:
            print(f"  🔎 Checking '{title}': {embed_url}")
            m3u8 = extract_m3u8_from_embed(embed_url)
            if m3u8:
                return match, m3u8
    return match, None

def generate_m3u8():
    matches = get_all_matches()
    if not matches:
        return "#EXTM3U\n#EXTINF:-1,No Matches Found\n"

    content = ["#EXTM3U"]
    success = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_match, m): m for m in matches}
        for future in concurrent.futures.as_completed(futures):
            match, url = future.result()
            title = match.get('title','Untitled Match')
            if url:
                logo, cat = build_logo_url(match)
                display_cat = cat.replace('-', ' ').title() if cat else "General"
                content.append(f'#EXTINF:-1 tvg-name="{title}" tvg-logo="{logo}" group-title="StreamedSU - {display_cat}",{title}')
                content.append(url)
                success += 1
                print(f"  ✅ {title} ({logo})")

    print(f"🎉 Found {success} streams.")
    return "\n".join(content)

if __name__ == "__main__":
    playlist = generate_m3u8()
    try:
        with open("StreamedSU.m3u8","w",encoding="utf-8") as f:
            f.write(playlist)
        print("💾 Playlist saved.")
    except IOError as e:
        print(f"⚠️ Error saving file: {e}")
        print(playlist)
