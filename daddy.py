input_file = "DaddyLive.m3u"
output_file = "DaddyLive.m3u8"

# Your OG headers (replace these with the exact headers needed)
new_headers = [
    '#EXTVLCOPT:http-origin=http://drewlive24.duckdns.org',
    '#EXTVLCOPT:http-referrer=http://drewlive24.duckdns.org/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0'
]

with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    lines = infile.readlines()

    for line in lines:
        stripped = line.strip()
        
        # Skip all existing #EXTVLCOPT lines to avoid duplicates
        if stripped.startswith("#EXTVLCOPT:"):
            continue
        
        # When you hit a stream URL line (starts with http), inject your clean headers right before it
        if stripped.startswith("http"):
            for header in new_headers:
                outfile.write(header + "\n")
            outfile.write(line)
        else:
            # Write all other lines as is (including original #EXTINF and group titles)
            outfile.write(line)
