# kodi.py

input_file = "MergedPlaylist.m3u8"
output_file = "MergedPlaylist_Kodi.m3u8"

def convert_to_kodi_format(lines):
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            result.append(line)
            i += 1
            while i < len(lines) and lines[i].strip().startswith("#EXTVLCOPT:"):
                header_line = lines[i].strip().replace("#EXTVLCOPT:", "#KODIPROP:")
                result.append(header_line)
                i += 1
            if i < len(lines):
                result.append(lines[i].strip())  # the stream URL
        else:
            result.append(line)
        i += 1
    return result

with open(input_file, "r", encoding="utf-8") as infile:
    lines = infile.readlines()

converted = convert_to_kodi_format(lines)

with open(output_file, "w", encoding="utf-8") as outfile:
    outfile.write("\n".join(converted))
