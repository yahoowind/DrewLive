import requests
import json
import base64
from urllib.parse import urljoin

# --- Configuration ---
# API endpoints and keys from the site's code
API_URL = "https://timgfdscfghnjmhbgfrfcredcedeerrffrrfrf.jdx3.org/main"
FETCH_URL = "https://cr6rabe9r4sterowutru5o9o5hepiva2r.ruseneslt0xadlcrahithot2dlcum4j3f.jdx3.org/fetch"
SECRET_KEY = "SwlD#yekl1rexoswaprO7UTUsTlML4emifutR8s3o"

# Mirror sites for fallback and referer checking
MIRRORS = ["https://timstreams.xyz/", "https://timstreams.cfd/"]
BASE_URL = MIRRORS[0] # Use the first mirror for general API calls

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0'
}

OUTPUT_FILENAME = "Tims247.m3u8"

# Import decryption libraries
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def verify_link(session, url):
    """
    Checks if a URL is live by testing it with each mirror as a Referer.
    Returns the successful mirror URL if the link is live, otherwise None.
    """
    for mirror in MIRRORS:
        try:
            # Temporarily set headers for this specific check
            check_headers = session.headers.copy()
            check_headers['Referer'] = mirror
            check_headers['Origin'] = mirror.strip('/')
            
            with session.head(url, headers=check_headers, timeout=5, allow_redirects=True) as response:
                if response.status_code == 200:
                    return mirror # Return the mirror that worked
        except requests.RequestException:
            continue # If an error occurs, just try the next mirror
    return None

def get_final_m3u8(session, stream_url):
    """
    Takes a stream source URL, decrypts it, and verifies it's online using the mirror list.
    Returns a tuple of (final_url, working_mirror) if successful.
    """
    final_url = None
    if 'kleanpro.cfd/embed/' in stream_url:
        try:
            stream_id = stream_url.split('/')[-1].strip()
            if not stream_id: return None, None

            with session.post(FETCH_URL, json={'id': stream_id}, timeout=10) as response:
                response.raise_for_status()
                payload = response.text.strip()

            combined_bytes = base64.b64decode(payload)
            iv, ciphertext = combined_bytes[:16], combined_bytes[16:]
            key_bytes = SECRET_KEY.encode('utf-8')[:16]
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(ciphertext)
            final_url = unpad(decrypted_padded, AES.block_size).decode('utf-8').strip()

        except Exception as e:
            print(f"   ❌ Decryption failed for {stream_url}: {e}")
            return None, None
    else:
        final_url = stream_url

    # Verify the link and get the working mirror
    working_mirror = verify_link(session, final_url)
    if working_mirror:
        return final_url, working_mirror
    else:
        print(f"   ❌ Verification failed (dead link): {final_url}")
        return None, None

def generate_m3u():
    """Main function to generate the M3U playlist."""
    m3u_content = ["#EXTM3U"]
    
    with requests.Session() as session:
        session.headers.update(HEADERS)
        # Set a default Referer/Origin for the main API calls
        session.headers['Referer'] = BASE_URL
        session.headers['Origin'] = BASE_URL.strip('/')
        
        try:
            with session.get(API_URL, timeout=15) as response:
                response.raise_for_status()
                data = response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"## ❌ ERROR: Failed to fetch main API data: {e}")
            return

        for category in data:
            category_name = category.get("category", "Unknown")
            events = category.get("events", [])
            
            for event in events:
                event_name = event.get("name")
                logo_path = event.get("logo")
                stream_sources = event.get("streams", [])
                
                if not event_name or not stream_sources: continue

                logo_url = urljoin(BASE_URL, logo_path) if logo_path else ""
                
                print(f"\n[*] Processing event: {event_name}")
                
                found_stream = False
                for i, source in enumerate(stream_sources):
                    source_url = source.get("URL") or source.get("url")
                    if not source_url: continue

                    final_m3u8, working_mirror = get_final_m3u8(session, source_url)
                    
                    if final_m3u8 and working_mirror:
                        found_stream = True
                        
                        # Adjust stream name based on number of sources
                        if len(stream_sources) > 1:
                            stream_name = f"{event_name} - Source {i + 1}"
                        else:
                            stream_name = event_name
                        
                        print(f"   ✅ Success: Got stream for '{stream_name}'")
                        print(f"      -> {final_m3u8}")
                        
                        # --- MODIFICATION: Set group-title and revert tvg-id ---
                        group_title_formatted = f"Tims247 - {category_name}"
                        
                        extinf_line = f'#EXTINF:-1 tvg-id="24.7.Dummy.us" tvg-name="{stream_name}" tvg-logo="{logo_url}" group-title="{group_title_formatted}",{stream_name}'
                        
                        m3u_content.append(extinf_line)
                        m3u_content.append(f'#EXTVLCOPT:http-origin={working_mirror.strip("/")}')
                        m3u_content.append(f'#EXTVLCOPT:http-referer={working_mirror}')
                        m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                        m3u_content.append(final_m3u8)

                if not found_stream:
                    print(f"   ❌ Failed to get any valid streams for '{event_name}'")

    try:
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        print(f"\n\n🟢 Playlist successfully saved to '{OUTPUT_FILENAME}'")
    except IOError as e:
        print(f"\n\n❌ ERROR: Could not write to file '{OUTPUT_FILENAME}': {e}")

if __name__ == "__main__":
    generate_m3u()
