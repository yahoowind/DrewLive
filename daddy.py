input_file = "DaddyLive.m3u"
output_file = "DaddyLive.m3u8"

new_headers = [
    '#EXTVLCOPT:http-origin=http://drewlive24.duckdns.org',
    '#EXTVLCOPT:http-referrer=http://drewlive24.duckdns.org/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0'
]

with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    lines = infile.readlines()

    for i, line in enumerate(lines):
        line_strip = line.strip()

        # Remove any existing origin or referrer EXT lines (case-insensitive)
        if line_strip.lower().startswith("#extvlcopt:http-origin=") or line_strip.lower().startswith("#extvlcopt:http-referrer="):
            continue

        # When hitting a stream URL line, insert new headers before the URL line
        if line_strip.startswith("http"):
            for h in new_headers:
                outfile.write(h + "\n")
            outfile.write(line)
        else:
            # Write all other lines as-is (including other #EXTVLCOPT lines like user-agent)
            outfile.write(line)
