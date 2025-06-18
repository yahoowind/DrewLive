import requests

UPSTREAM_URL = "https://tinyurl.com/DaddyLive824"
OUTPUT_FILE = "DaddyLive.m3u8"

# Shared headers for both locked channels
FORCED_HEADERS = [
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
]

# Locked channels and their direct stream URLs
LOCKED_CHANNELS = {
    "TNT Sports 1 UK": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MWU2NjUwNmQwZTE3LWNhYWEtMWRlNC1kYTdiLTlhNWEyY2M0/master.m3u8?md5=4soseisT-1VJHwpL0Q-NZw&expires=1750240697&t=1750197497",
    "Discovery Channel": "https://hipaf6u2j3pwygg.nice-flower.store/v4/variant/VE1gTdz0mLzRnLv52bt9SMhFjdtM3ajFmc09SMkVDZldTMjRmM1UWL4gzY40yYyYDNtM2YhFTL4QTYxcDMwM2L.m3u8?md5=P_ZRKSUAQTEs1klzlorEJQ&expires=1750248906&t=1750205706",
    "Discovery Life Channel": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ODhlZDkzOTA2MzJhLTQ5YmEtZjg1NC04NTU3LTk2NzEwMTI1/master.m3u8?md5=XktZkv3c_ytZI_JZBEzzkg&expires=1750250162&t=1750206962",
    "Disney Channel": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NWExNTMwNzQ3NzMyLTdkYjgtMGQ5NC0zNDkwLWI4YThkYzk1/master.m3u8?md5=KO3sVCpU1airg_ymD2eVVg&expires=1750250481&t=1750207281",
    "Disney XD": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NWNmYmE3M2Q4Y2UxLTEwYjktN2IxNC01ZGE1LTY4ZmE1NTU5/master.m3u8?md5=E65aRLZRBc2eJbPhoWOaxQ&expires=1750251145&t=1750207945",
    "E! Entertainment": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NTlkNmFmMTI0ZjA0LThmOTgtMGRmNC1iOTg1LWM5MmMyMTg3/master.m3u8?md5=Gm626FWMGQElXeT0E22tZw&expires=1750251209&t=1750208009",
    "ESPN Deportes": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MzE5ZWM0NGYxNWExLTEzOTktMTllNC03MDAxLWQ1ZGM1YzFm/master.m3u8?md5=45wiyaAEGRzKX9xH-kqlWw&expires=1750251311&t=1750208111",
    "ESPN USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1Yzc1NzQ2MmVkOGViLTUyYTgtNTc2NC0xNzVjLWE2MmQyOGE4/master.m3u8?md5=hDThTRzjr2pxCz77uL3lAA&expires=1750251420&t=1750208220",
    "ESPN2 USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NDJlMzQ4NzNiMGYzLTA2OTgtYWQ1NC1lN2VmLTlkZWQ3YTQy/master.m3u8?md5=FAr8MitrGdCukq9CJcurUg&expires=1750251703&t=1750208503",
    "ESPNews": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1N2U1ODA1MmJmNDA5LTVhZjktNDI1NC0xNmJmLTA0ZTVkZGE5/master.m3u8?md5=jKgUIMiX8G-4MTA1YaxdgQ&expires=1750251749&t=1750208549",
    "ESPNU USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NDJlY2IxMDVhM2ZmLWUzMDgtMWI4NC00OTVmLTQzM2YyZjY0/master.m3u8?md5=jZ38qAx5e3b4CGIh6L70wg&expires=1750253927&t=1750210727",
    "Fox Business": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ODNkYmE0NjVlNGJmLTAxZDktOTkyNC1iMjJhLTkxYWY4ZmQ4/master.m3u8?md5=xodEYia7GO0QHWOU04ynug&expires=1750255897&t=1750212697",
    "Fox News": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ZmYyZDIyYzcxMGQyLWM5OGItOTgyNC1hNzhlLTU0NmEzZjdl/master.m3u8?md5=YT262RT2QKxmhyV5EQyJcQ&expires=1750255986&t=1750212786",
    "Fox Sports 1": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1N2EwODYxNTMyNTBmLTU1MmItMGE1NC0xODQzLWM0OWIzMWFm/master.m3u8?md5=pjkxHKX2KJLBMp9TtBk1Uw&expires=1750256102&t=1750212902",
    "FOX USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MjczMGJkYzRlNTA1LTBhMzgtOTAzNC1jMDQ5LTBhOTYxNjI0/master.m3u8?md5=mYDk3aCJhsL1iwrOsDdWLA&expires=1750256197&t=1750212997",
    "Freeform": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1YjA1OTQxYzQ4NmQ5LTllMGEtOWQ3NC1mZGUyLTVmNjM5Zjkx/master.m3u8?md5=qxoVJuYUYn7n4vnIMngfkA&expires=1750256528&t=1750213328",
    "Fuse": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MjczMGJkYzRlNTA1LTBhMzgtOTAzNC1jMDQ5LTBhOTYxNjI0/master.m3u8?md5=mYDk3aCJhsL1iwrOsDdWLA&expires=1750256197&t=1750212997",
    "FOX USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MjczMGJkYzRlNTA1LTBhMzgtOTAzNC1jMDQ5LTBhOTYxNjI0/master.m3u8?md5=mYDk3aCJhsL1iwrOsDdWLA&expires=1750256197&t=1750212997",
    "FUSE TV USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MTM4YjJmNjg3NWE0LTJkZmEtNWIwNC1lZTQ1LWExYTAyNmJh/master.m3u8?md5=jWKvHLHYPzV0lWDzV7bFcg&expires=1750258460&t=1750215260",
    "FX Movie Channel": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NzlkZTFlNzliOTM1LWMzOTgtY2Q3NC0yYWFkLTQ5ZWJlNDUz/master.m3u8?md5=_lKYGa196CYjscVE1b368A&expires=1750256673&t=1750213473",
    "FX USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1YjY5YzA0MWE0Y2VjLTY2ZWEtMzQxNC0xZDMyLTFiODM4M2Q3/master.m3u8?md5=pYohYRs5UBNjakCjnMB2Rw&expires=1750256629&t=1750213429",
    "FXX USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MDk2MTUzM2NjYzFiLWE0YTktYjYxNC1hNDUzLTkwNThmNzgy/master.m3u8?md5=JjuFPb5zDIywLGfWj6SZJA&expires=1750256711&t=1750213511",
    "Game Show Network": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1YzNhYjE3ODdmZTQ1LTJkY2EtZjk3NC00MjMwLTA5YTA3Y2Uw/master.m3u8?md5=DzTEjF7WR6pt-az2P0hqrA&expires=1750256927&t=1750213727",
    "GOLF Channel USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1YmRlMmJjMjQ1OWIzLWE0ODgtZjUxNC1hY2JiLTJjZGI0N2I5/master.m3u8?md5=7ZeoAI34QtGFoUZaXuOzVQ&expires=1750256964&t=1750213764",
    "Hallmark Movies & Mysteries": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MWUwNDJiZDI4OWRhLTJmOWItZDg1NC0xNDBhLWQ3ODhmZTMz/master.m3u8?md5=Kxxg34iXygt99sOhyfpwbA&expires=1750257174&t=1750213974",
    "HBO USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1YmU1YjI5NjI3OTVjLWYwY2EtNTIzNC0yM2ZkLTU2Y2QyNDc1/master.m3u8?md5=RFN5KK9J7FaYydDvbrWHHw&expires=1750259043&t=1750215843",
    "Headline News": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ZWU1NDA1ZTlhZTYzLTc4NzgtMWQxNC0yZDQyLTMzYjcyYjk3/master.m3u8?md5=jVwuTyfZjQw-uFRKl_SJFw&expires=1750259167&t=1750215967",
    "HGTV": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1YjM3N2ZiODlmYzI2LTFhNjktNDRkNC02NjMzLTMyZDU5MjA1/master.m3u8?md5=D9LFA5miuXNlWNUUlPCjww&expires=1750259277&t=1750216077",
    "History USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MmU4M2UyYjIzOGYzLWNmZWEtNDc2NC0zMWM2LWM4NGQ3Yjlh/master.m3u8?md5=NtIcO2ueoGVnBNJUa6rcxQ&expires=1750259483&t=1750216283",
    "Investigation Discovery (ID USA)": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MGMxNDk1Nzg2MWJjLTc1ZmEtZTMyNC05NzE1LWMxMjZkZmMy/master.m3u8?md5=ugjGows6WVXJqblNFBc7Xg&expires=1750260326&t=1750217126",
    "ION USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MjViOWU1N2E3MDQwLTMwZjktMjhlNC1lYjQ1LTMwODdmMjZh/master.m3u8?md5=rPbHS3QFNyD4qhCFLIQTZw&expires=1750260385&t=1750217185",
    "Law & Crime Network": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NzAyMWIwZWZhNGRkLTczZmItNjYwNC0zNjMzLWU0NGVjOGNi/master.m3u8?md5=Mb0hlvyWXXoWnhqFLnt_lw&expires=1750260432&t=1750217232",
    "Lifetime Movies Network": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NTA3ZGIyZjlkNDEzLTgzNWItYTc0NC1kZWFhLWQ2ZDY5MGM2/master.m3u8?md5=6eHzr1is2Kj70T5cQFtayA&expires=1750262083&t=1750218883",
    "Lifetime Network": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1MmY5ZjdlOWYzNTcyLTJlMzktM2E0NC1hN2IwLTQxZWIyNTM4/master.m3u8?md5=wBKzqm-TQPurE5mjszCTZw&expires=1750262141&t=1750218941",
    "Magnolia Network": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ZmU1NjNiMGM0NTdhLWRjNmEtNTc5NC1lYmZmLTUxNTlmNjEz/master.m3u8?md5=oXISZdBdP_g3zU8iErH1Gw&expires=1750262174&t=1750218974",
    "MSNBC": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NmIyMzc5ZTZhZTgxLTg5ZWEtZWYwNC0wMmU4LTM2YTNkZWU5/master.m3u8?md5=wE4tk9ltqFf7TlixY1VClw&expires=1750266601&t=1750223401",
    "MTV USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ZWZkMzFkZDkzYzJiLTRkMjgtMzExNC1kMjc4LWJlMzkxYzdj/master.m3u8?md5=1u5wnvmD4b7LqF7AhDYvTQ&expires=1750266646&t=1750223446",
    "National Geographic (NGC)": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ZWNkODlhMTNmYTM5LWQzNWItMTUyNC00ODVjLWM3MjY1Yzlk/master.m3u8?md5=mpHv1Jy_er5S5RBFTz3TpA&expires=1750266833&t=1750223633",
    "NBC Sports Philadelphia": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1ZjBjNDBhYmIzY2M2LWJmMTktZTBjNC03MmYyLWYyMGQ5YjMy/master.m3u8?md5=tqdvjxdGLAWMj8n-UwsZ0Q&expires=1750267729&t=1750224529",
    "NBC USA": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1NThlZWIyNzVhNTg1LTZkMjgtODczNC00NmE0LWNkOWY1YTEy/master.m3u8?md5=ttglz7Vx7rm8MkSo0f4mBQ&expires=1750267909&t=1750224709"
    "NBC10 Philadelphia": "https://hipaf6u2j3pwygg.nice-flower.store/v3/director/VE1OTM5ODRjNDBkMjhlLTVmYTktNGUyNC01ZjM4LWUyMzdmMzhm/master.m3u8?md5=8ByuJ9RMr3SDZpqsqAYHbQ&expires=1750267964&t=1750224764"
}

def update_playlist():
    try:
        response = requests.get(UPSTREAM_URL, timeout=20)
        response.raise_for_status()
        lines = response.text.splitlines()
        output = []
        i = 0

        while i < len(lines):
            line = lines[i]

            matched = None
            for channel_name in LOCKED_CHANNELS:
                if line.startswith("#EXTINF") and channel_name in line:
                    matched = channel_name
                    break

            if matched:
                output.append(line)
                i += 1

                # Skip existing headers
                while i < len(lines) and lines[i].startswith("#EXTVLCOPT:"):
                    i += 1

                # Insert shared headers
                output.extend(FORCED_HEADERS)

                # Replace URL
                output.append(LOCKED_CHANNELS[matched])

                # Skip original URL if it's still present
                if i < len(lines) and not lines[i].startswith("#"):
                    i += 1
            else:
                output.append(line)
                i += 1

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output) + "\n")

        print("✅ Playlist updated with locked streams and headers.")

    except Exception as e:
        print(f"❌ Error updating playlist: {e}")

if __name__ == "__main__":
    update_playlist()
