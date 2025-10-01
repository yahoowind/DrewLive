import requests
import json
import re

json_urls = [
    "https://magnetic.website/MAD_TITAN_SPORTS/TOOLS/METAL/luc-247.json",
    "https://magnetic.website/MAD_TITAN_SPORTS/TOOLS/METAL/ky-247.json",
    "https://magnetic.website/MAD_TITAN_SPORTS/TOOLS/METAL/sps-247.json",
    "https://magnetic.website/MAD_TITAN_SPORTS/LIVETV/playlist.json"
]

special_json_url = "https://magnetic.website/MAD_TITAN_SPORTS/LIVETV/playlist.json"

STATIC_TVG_ID = "24.7.Dummy.us"
STATIC_LOGO_URL = "https://www.wirelesshack.org/wp-content/uploads/2022/01/How-To-Install-Mad-Titan-Sports-Kodi-Add-on-2022.jpg"

m3u8_content = "#EXTM3U\n"

for url in json_urls:
    try:
        print(f"Fetching data from: {url}")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        channels = data.get("items", [])
        
        if not channels:
            print(f"Warning: No 'items' found or 'items' list is empty in {url}")
            continue

        for channel in channels:
            if url == special_json_url:
                
                title = channel.get("title", "Unknown Title")
                category = channel.get("category", "General")
                link_url = channel.get("link", "")
                
                channel_logo = channel.get("thumbnail") or STATIC_LOGO_URL
                
                channel_name = re.sub(r'\[.*?\]', '', title).strip()
                
                stream_url = ""
                if 'direct://' in link_url:
                    stream_url = link_url.split('direct://', 1)[-1]

                if stream_url:
                    group_title = f"MadTitan - {category}"
                    m3u8_content += f'#EXTINF:-1 tvg-logo="{channel_logo}" group-title="{group_title}",{channel_name}\n'
                    m3u8_content += f'{stream_url}\n'
            
            else:
                
                channel_name = channel.get("channel", "Unknown Name")
                stream_url = channel.get("stream", "")
                category = channel.get("category", "General")
                
                if stream_url:
                    group_title = f"MadTitan - {category}"
                    m3u8_content += f'#EXTINF:-1 tvg-id="{STATIC_TVG_ID}" tvg-logo="{STATIC_LOGO_URL}" group-title="{group_title}",{channel_name}\n'
                    m3u8_content += f'{stream_url}\n'

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {url}. It might be invalid.")
    except Exception as e:
        print(f"An unexpected error occurred while processing {url}: {e}")

try:
    with open("MadTitan.m3u8", "w", encoding="utf-8") as file:
        file.write(m3u8_content)
    print("\n✅ Success! The file 'MadTitan.m3u8' was created with the fallback logo logic.")
except Exception as e:
    print(f"\n❌ Error writing to file: {e}")
