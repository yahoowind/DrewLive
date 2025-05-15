import requests


# List of your playlist URLs
playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/JapanTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DistroTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlexTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StirrTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TubiTV.m3u8",
]


def fetch_playlist(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""


def merge_playlists(urls):
    merged_lines = []
    seen_streams = set()


    # Add M3U header once
    merged_lines.append("#EXTM3U\n")


    for url in urls:
        content = fetch_playlist(url)
        if not content:
            continue


        lines = content.strip().splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("#EXTINF"):
                # Get the stream title from EXTINF line for uniqueness
                # EXTINF line format: #EXTINF:-1 tvg-id="" tvg-name="Name" ...
                # or sometimes just #EXTINF:-1, Channel Name
                title_line = line
                stream_url = ""
                header_lines = []


                # Collect any #EXTVLCOPT lines immediately after EXTINF
                j = i + 1
                while j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                    header_lines.append(lines[j])
                    j += 1
                
                # Next line after #EXTVLCOPT or EXTINF should be the stream URL
                if j < len(lines):
                    stream_url = lines[j].strip()
                    j += 1
                else:
                    i = j
                    continue


                # Use stream_url as unique key to avoid duplicates
                if stream_url not in seen_streams:
                    merged_lines.append(title_line)
                    merged_lines.extend(header_lines)
                    merged_lines.append(stream_url)
                    seen_streams.add(stream_url)


                i = j
            else:
                # Add any global or header lines like #EXTM3U only if not already added
                if line.startswith("#EXTM3U"):
                    # Skip - already added once
                    pass
                elif line and not line.startswith("#EXTINF") and not line.startswith("#EXTVLCOPT"):
                    # Include any global metadata lines outside stream entries, if needed
                    merged_lines.append(line)
                i += 1


    # Write merged playlist
    with open("MergedPlaylist.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(merged_lines))


    print(f"Merged playlist saved as MergedPlaylist.m3u8")


if __name__ == "__main__":
    merge_playlists(playlist_urls)
