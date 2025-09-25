import requests
import sys
import re
import time
import concurrent.futures

def get_all_matches():
    """Fetches all available matches from the API."""
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
    """Fetches the embed page URL for a given source."""
    api_url = f"https://streamed.pk/api/stream/{source['source']}/{source['id']}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        streams = response.json()
        if streams and streams[0].get('embedUrl'):
            return streams[0]['embedUrl']
    except requests.exceptions.RequestException:
        pass
    return None

def find_m3u8_in_content(page_content):
    """Searches for a .m3u8 or .m3u link in the given page source using multiple patterns."""
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
    """Visits the embed URL using requests and scrapes the static HTML for a .m3u8 link."""
    if not embed_url:
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://streamed.pk/'
        }
        response = requests.get(embed_url, headers=headers, timeout=15)
        response.raise_for_status()
        return find_m3u8_in_content(response.text)
            
    except requests.exceptions.RequestException:
        pass
    return None

def process_match(match):
    """
    Processes a single match to find a stream URL.
    This function is designed to be run in a separate thread.
    """
    title = match.get('title', 'Untitled Match')
    
    sources = match.get('sources')
    if sources:
        for source in sources:
            embed_url = get_stream_embed_url(source)
            if embed_url:
                print(f"  🔎 Checking embed link for '{title}': {embed_url}")
                final_stream_url = extract_m3u8_from_embed(embed_url)
                if final_stream_url:
                    return (match, final_stream_url)
    
    return (match, None)

def generate_m3u8():
    """Generates an M3U8 playlist string by scraping for direct stream links concurrently."""
    matches = get_all_matches()

    if not matches:
        return "#EXTM3U\n#EXTINF:-1,No Matches Found\n"

    m3u8_content = ["#EXTM3U"]
    successful_streams = 0

    print(f"\n⚙️  Processing all {len(matches)} matches concurrently (this may take a while)...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_match = {executor.submit(process_match, match): match for match in matches}

        for future in concurrent.futures.as_completed(future_to_match):
            original_match, final_stream_url = future.result()
            title = original_match.get('title', 'Untitled Match')

            if final_stream_url:
                category = original_match.get('category', 'General').capitalize()
                logo_url = ""
                teams = original_match.get('teams')
                if teams:
                    away_team = teams.get('away', {})
                    home_team = teams.get('home', {})
                    badge_id = away_team.get('badge') or home_team.get('badge')
                    if badge_id:
                        logo_url = f"https://streamed.pk/api/images/badge/{badge_id}.webp"

                extinf = f'#EXTINF:-1 tvg-name="{title}" tvg-logo="{logo_url}" group-title="StreamedSU - {category}",{title}'
                m3u8_content.append(extinf)
                m3u8_content.append(final_stream_url)
                successful_streams += 1
                print(f"  ✅ SUCCESS: Found .m3u8 for '{title}'")

    print(f"\n🎉 Successfully generated M3U8 with {successful_streams} direct stream links.")
    return "\n".join(m3u8_content)

if __name__ == "__main__":
    playlist_data = generate_m3u8()
    
    try:
        with open("StreamedSU.m3u8", "w", encoding="utf-8") as f:
            f.write(playlist_data)
        print("\n💾 Playlist saved to 'StreamedSU.m3u8'")
    except IOError as e:
        print(f"\n⚠️  Error saving file: {e}", file=sys.stderr)
        print("\n--- M3U8 Playlist Output ---")
        print(playlist_data)
