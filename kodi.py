import urllib.parse

input_file = "MergedPlaylist.m3u8"
output_file = "MergedPlaylist_Kodi.m3u8"

def convert_to_kodi_format(lines):
    result = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            # Write EXTINF line
            result.append(line)
            i += 1

            # Collect headers from following #EXTVLCOPT lines
            headers = {}
            while i < len(lines) and lines[i].strip().startswith("#EXTVLCOPT:"):
                hdr_line = lines[i].strip()[len("#EXTVLCOPT:"):]  # e.g. "http-referrer=https://..."
                if "=" in hdr_line:
                    key, value = hdr_line.split("=", 1)
                    # Normalize keys to capitalized form for Kodi (optional)
                    # e.g. http-referrer -> Referer
                    key_map = {
                        "http-referrer": "Referer",
                        "http-user-agent": "User-Agent",
                        "http-origin": "Origin"
                    }
                    key = key_map.get(key.lower(), key)
                    headers[key] = value
                i += 1
            
            # Next line should be the stream URL
            if i < len(lines):
                stream_url = lines[i].strip()
                i += 1

                # If headers found, append them as url-encoded params after pipe
                if headers:
                    params = []
                    for k, v in headers.items():
                        params.append(f"{k}={urllib.parse.quote(v, safe='')}")
                    stream_url += "|" + "&".join(params)
                
                result.append(stream_url)
            else:
                # No stream URL, just continue
                continue
        else:
            # Other lines pass through unchanged
            result.append(line)
            i += 1

    return result

with open(input_file, "r", encoding="utf-8") as infile:
    lines = infile.readlines()

converted = convert_to_kodi_format(lines)

with open(output_file, "w", encoding="utf-8") as outfile:
    outfile.write("\n".join(converted) + "\n")
