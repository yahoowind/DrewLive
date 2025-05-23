input_file = "DaddyLive.m3u"
output_file = "DaddyLive.m3u8"

# New base URL for outside access - change this to your current public URL
base_url = "http://drewlive24.duckdns.org"

new_headers = [
    f'#EXTVLCOPT:http-origin={base_url}',
    f'#EXTVLCOPT:http-referrer={base_url}/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0'
]

with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    lines = infile.readlines()
    
    for line in lines:
        line_strip = line.strip()
        
        if line_strip.startswith("#EXTVLCOPT:"):
            continue
        
        if line_strip.startswith("http"):
            for h in new_headers:
                outfile.write(h + "\n")
            outfile.write(line)
        else:
            outfile.write(line)
