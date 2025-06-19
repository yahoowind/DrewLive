RAW_FILE = "DaddyLiveRAW.m3u8"
OUTPUT_FILE = "DaddyLive.m3u8"
PROXY_URL = "https://tinyurl.com/DrewProxy2423"

def process_m3u():
    with open(RAW_FILE, "r", encoding="utf-8") as infile:
        lines = [line.strip() for line in infile if line.strip()]

    output_lines = []
    for i in range(len(lines)):
        line = lines[i]
        if line.startswith("#"):
            output_lines.append(line)
        elif line.startswith("http://") or line.startswith("https://"):
            # Replace actual stream with proxy only
            output_lines.append(PROXY_URL)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write("\n".join(output_lines) + "\n")

    print(f"✅ Proxy playlist saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_m3u()
