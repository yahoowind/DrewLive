def main():
    tv_ids = load_mapping(TVIDS_FILE)
    logos = load_mapping(LOGOS_FILE)
    print(f"[DEBUG] Loaded {len(tv_ids)} tv_ids and {len(logos)} logos")

    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    lines = response.text.splitlines()

    result = ['#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"']
    i = 0
    count = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXTINF'):
            if ',' not in line:
                i += 2
                continue
            display_name = line.split(',', 1)[1].strip()

            group = get_group_title(display_name, tv_ids)
            if not group:
                i += 2
                continue

            if 'group-title="' in line:
                line = re.sub(r'group-title="[^"]*"', f'group-title="{group}"', line)
            else:
                parts = line.split(',', 1)
                line = parts[0] + f' group-title="{group}",' + parts[1]

            line = update_extinf(line, tv_ids, logos)
            stream_url = unwrap_url(lines[i + 1].strip())
            result.append(line)
            result.append(stream_url)

            count += 1
            i += 2
        else:
            i += 1

    print("[DEBUG] First 5 lines of updated playlist:")
    for l in result[:5]:
        print(l)

    with open(os.path.join(BASE_DIR, OUTPUT_FILE), 'w', encoding='utf-8') as f:
        f.write('\n'.join(result))

    print(f"[+] Processed and wrote {count} channels to {OUTPUT_FILE}")
