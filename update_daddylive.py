import asyncio
from playwright.async_api import async_playwright, Request
import random
import re

INPUT_FILE = "DaddyLive.m3u8"
OUTPUT_FILE = "DaddyLive.m3u8"

CHANNELS_TO_PROCESS = {
"ABC USA": "51", "A&E USA": "302", "AMC USA": "303", "Animal Planet": "304", "ACC Network USA": "664", "Adult Swim": "295", "AXS TV USA": "742", "ABCNY USA": "766", "beIN SPORTS Australia 1": "491", "beIN SPORTS Australia 2": "492", "beIN SPORTS Australia 3": "493", "beIN Sports MENA English 1": "61", "beIN Sports MENA English 2": "90", "beIN Sports MENA English 3": "46", "BeIN SPORTS USA": "425", "beIN SPORTS en Espa単ol": "372", "Boomerang": "648", "BBC America (BBCA)": "305", "BET USA": "306", "Bravo USA": "307", "BBC News Channel HD": "349", "BBC One UK": "356", "BBC Two UK": "357", "BBC Three UK": "358", "BBC Four UK": "359", "BIG TEN Network (BTN USA)": "397", "Channel 4 UK": "354", "Channel 5 UK": "355", "CBS Sports Network (CBSSN)": "308", "COZI TV USA": "748", "CMT USA": "647", "CBS USA": "52", "CW USA": "300", "CNBC USA": "309", "Comedy Central": "310", "Cartoon Network": "339", "CNN USA": "345", "Cinemax USA": "374", "CTV Canada": "602", "CTV 2 Canada": "838", "Crime+ Investigation USA": "669", "Comet USA": "696", "Cooking Channel USA": "697", "Cleo TV": "715", "C SPAN 1": "750", "CBSNY USA": "767", "Citytv": "831", "CBC CA": "699", "Discovery Life Channel": "311", "Disney Channel": "312", "Discovery Channel": "313", "Discovery Family": "657", "Disney XD": "314", "Destination America": "651", "Disney JR": "652", "Dave": "348", "ESPN USA": "44", "ESPN2 USA": "45", "ESPNU USA": "316", "ESPN Deportes": "375", "ESPNews": "288", "E! Entertainment Television": "315", "E4 Channel": "363", "Fox Sports 1 USA": "39", "Fox Sports 2 USA": "758", "FOX Soccer Plus": "756", "Fox Cricket": "369", "FOX Deportes USA": "643", "FOX Sports 502 AU": "820", "FOX Sports 503 AU": "821", "FOX Sports 504 AU": "822", "FOX Sports 505 AU": "823", "FOX Sports 506 AU": "824", "FOX Sports 507 AU": "825", "Fight Network": "757", "Fox Business": "297", "FOX HD Bulgaria": "483", "FOX USA": "54", "FX USA": "317", "FXX USA": "298", "Freeform": "301", "Fox News": "347", "FX Movie Channel": "381", "FYI": "665", "Film4 UK": "688", "Fashion TV": "744", "FETV - Family Entertainment Television": "751", "FOXNY USA": "768", "Fox Weather Channel": "775", "GOLF Channel USA": "318", "Game Show Network": "319", "Gold UK": "687", "Galavisi贸n USA": "743", "Grit Channel": "752", "Global CA": "836", "The Hallmark Channel": "320", "Hallmark Movies & Mysterie": "296", "HBO USA": "321", "HBO2 USA": "689", "HBO Comedy USA": "690", "HBO Family USA": "691", "HBO Latino USA": "692", "HBO Signature USA": "693", "HBO Zone USA": "694", "History USA": "322", "Headline News": "323", "HGTV": "382", "ITV 1 UK": "350", "ITV 2 UK": "351", "ITV 3 UK": "352", "ITV 4 UK": "353", "Investigation Discovery (ID USA)": "324", "ION USA": "325", "IFC TV USA": "656", "Liverpool TV (LFC TV)": "826", "Lifetime Network": "326", "Lifetime Movies Network": "389", "Longhorn Network USA": "667", "MSG USA": "765", "MSNBC": "327", "Magnolia Network": "299", "MTV UK": "367", "MTV USA": "371", "MUTV UK": "377", "MAVTV USA": "646", "Marquee Sports Network": "770", "MLB Network USA": "399", "MASN USA": "829", "MY9TV USA": "654", "Motor Trend": "661", "METV USA": "662", "NHL Network USA": "663", "NESN USA": "762", "NBC USA": "53", "NBA TV USA": "404", "NBC Sports Chicago": "776", "NBC Sports Philadelphia": "777", "NBC Sports Washington": "778", "NFL Network": "405", "NBC Sports Bay Area": "753", "NBC Sports Boston": "754", "NBC Sports California": "755", "NBCNY USA": "769", "National Geographic (NGC)": "328", "NICK JR": "329", "NICK": "330", "Nick Music": "666", "Nicktoons": "649", "NewsNation USA": "292", "Newsmax USA": "613", "Nat Geo Wild USA": "745", "Noovo CA": "835", "CWPIX 11": "771", "Oxygen True Crime": "332", "Paramount Network": "334", "POP TV USA": "653", "RTE 1": "364", "RTE 2": "365", "RDS CA": "839", "RDS 2 CA": "840", "RDS Info CA": "841", "Racing Tv UK": "555", "Reelz Channel": "293", "Sky Sports Football UK": "35", "Sky Sports Arena UK": "36", "Sky Sports Action UK": "37", "Sky Sports Main Event": "38", "Sky sports Premier League": "130", "Sky Sports F1 UK": "60", "Sky Sports Cricket": "65", "Sky Sports Golf UK": "70", "Sky Sports News UK": "366", "Sky Sports MIX UK": "449", "SportsNet New York (SNY)": "759", "Sky Sports Racing UK": "554", "Sky Sport 1 NZ": "588", "Sky Sport 2 NZ": "589", "Sky Sport 3 NZ": "590", "Sky Sport 4 NZ": "591", "Sky Sport 5 NZ": "592", "Sky Sport 6 NZ": "593", "Sky Sport 7 NZ": "594", "Sky Sport 8 NZ": "595", "Sky Sport 9 NZ": "596", "Sky Sport Select NZ": "587", "SEC Network USA": "385", "Sportsnet Ontario": "406", "Sportsnet One": "411", "Sportsnet West": "407", "Sportsnet East": "408", "Sportsnet 360": "409", "Sportsnet World": "410", "SuperSport Grandstand": "412", "SuperSport PSL": "413", "SuperSport Premier league": "414", "SuperSport LaLiga": "415", "SuperSport Variety 1": "416", "SuperSport Variety 2": "417", "SuperSport Variety 3": "418", "SuperSport Variety 4": "419", "SuperSport Action": "420", "SuperSport Rugby": "421", "SuperSport Golf": "422", "SuperSport Tennis": "423", "SuperSport Motorsport": "424", "Supersport Football": "56", "SuperSport Cricket": "368", "SuperSport MaXimo 1": "572", "S4C UK": "670", "Sky Cinema Premiere UK": "671", "Sky Cinema Select UK": "672", "Sky Cinema Hits UK": "673", "Sky Cinema Greats UK": "674", "Sky Cinema Animation UK": "675", "Sky Cinema Family UK": "676", "Sky Cinema Action UK": "677", "The Hallmark": "680", "Sky Cinema Thriller UK": "679", "Sky Cinema Sci-Fi Horror UK": "681", "Sky Showcase UK": "682", "Sky Arts UK": "683", "Sky Comedy UK": "684", "Sky Crime": "685", "Sky History": "686", "Science Channel": "294", "Showtime USA": "333", "Showtime SHOxBET USA": "685", "Starz": "335", "Sky Witness HD": "361", "SYFY USA": "373", "Sundance TV": "658", "Smithsonian Channel": "603", "TNT Sports 1 UK": "31", "TNT Sports 2 UK": "32", "TNT Sports 3 UK": "33", "TNT Sports 4 UK": "34", "TSN1": "111", "TSN2": "112", "TSN3": "113", "TSN4": "114", "TSN5": "115", "Tennis Channel": "40", "TUDN USA": "66", "Telemundo": "131", "TBS USA": "336", "TLC": "337", "TNT USA": "338", "TVA Sports": "833", "TVA Sports 2": "834", "Travel Channel": "340", "TruTV USA": "341", "TVLAND": "342", "TCM USA": "644", "TMC Channel USA": "698", "The Food Network": "384", "The Weather Channel": "394", "TeenNick": "650", "TV ONE USA": "660", "TVO CA": "842", "Tennis+ 1": "700", "Tennis+ 2": "701", "Tennis+ 3": "702", "Tennis+ 4": "703", "Tennis+ 5": "704", "Tennis+ 6": "705", "Tennis+ 7": "706", "Tennis+ 8": "707", "Tennis+ 9": "708", "Tennis+ 10": "709", "Tennis+ 11": "710", "Tennis+ 12": "711", "Tennis+ 13": "712", "Tennis+ 14": "713", "Tennis+ 15": "714", "USA Network": "343", "Universal Kids USA": "668", "Univision": "132", "Unimas": "133", "Viaplay Sports 1 UK": "451", "Viaplay Sports 2 UK": "550", "Viaplay Xtra UK": "597", "VH1 USA": "344", "VICE TV": "659", "Willow Cricket": "346", "Willow XTRA": "598", "WWE Network": "376", "WETV USA": "655", "YES Network USA": "763", "Yes TV CA": "837", "5 USA": "360", "Altitude Sports": "923", "beIN SPORTS en Español": "372", "Bally Sports Arizona": "890", "Bally Sports Detroit": "891", "Bally Sports Florida": "892", "Bally Sports Great Lakes": "893", "Bally Sports Indiana": "894", "Bally Sports Kansas City": "895", "Bally Sports Midwest": "896", "Bally Sports New Orleans": "897", "Bally Sports North": "898", "Bally Sports Ohio": "899", "Bally Sports Oklahoma": "900", "Bally Sports San Diego": "901", "Bally Sports SoCal": "902", "Bally Sports South": "903", "Bally Sports Southeast": "904", "Bally Sports Sun": "905", "Bally Sports West": "906", "Bally Sports Wisconsin": "907", "CW PIX 11 USA": "280", "CBS Sports Golazo": "910", "Court TV USA": "281", "DAZN 1 UK": "230", "Discovery Velocity CA": "285", "FUSE TV USA": "279", "Galavisión USA": "743", "LaLigaTV UK": "276", "Law & Crime Network": "278", "Monumental Sports Network": "924", "MGM+ USA / Epix": "79", "NBC10 Philadelphia": "277", "Pac-12 Network USA": "287", "PBS USA USA": "210", "PDC TV": "43", "Rally Tv": "607", "Root Sports Northwest": "920", "Sky Sports Tennis UK": "46", "Sky Cinema Comedy UK": "678", "Sky Cinema Drama UK": "680", "Showtime 2 USA (SHO2) USA": "792", "Showtime Showcase USA": "793", "Showtime Extreme USA": "794", "Showtime Family Zone (SHO Family Zone) USA": "795", "Showtime Next (SHO Next) USA": "796", "Showtime Women USA": "797", "Space City Home Network": "921", "SportsNet Pittsburgh": "922", "YTV CA": "296",

}

VLC_OPT_LINES = [
    '#EXTVLCOPT:http-origin=https://veplay.top',
    '#EXTVLCOPT:http-referrer=https://veplay.top/',
    '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0)',
]

def parse_m3u_playlist(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    entries = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTM3U"):
            entries.append({"meta": '#EXTM3U url-tvg="https://tinyurl.com/merged2423-epg"', "headers": [], "url": None})
            i += 1
        elif line.startswith("#EXTINF:"):
            meta = line
            headers = []
            i += 1
            while i < len(lines) and lines[i].startswith("#EXTVLCOPT"):
                headers.append(lines[i])
                i += 1
            url = lines[i] if i < len(lines) else ""
            entries.append({"meta": meta, "headers": headers, "url": url})
            i += 1
        else:
            i += 1
    return entries

def extract_channel_name(meta_line):
    match = re.search(r",(.+)$", meta_line)
    return match.group(1).strip() if match else None

async def fetch_updated_urls():
    urls = {}
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for name, cid in CHANNELS_TO_PROCESS.items():
            stream_urls = []

            def capture_m3u8(request: Request):
                if ".m3u8" in request.url.lower():
                    print(f"🔍 Found stream for {name}: {request.url}")
                    stream_urls.append(request.url)

            page.on("request", capture_m3u8)

            try:
                print(f"\n🔄 Scraping {name}...")
                await page.goto(f"https://thedaddy.click/stream/stream-{cid}.php", timeout=60000)
                tries = 0
                while not stream_urls and tries < 3:
                    await asyncio.sleep(5)
                    tries += 1
                    print(f"⏳ Waiting for {name}... ({tries})")
            except Exception as e:
                print(f"❌ Failed for {name}: {e}")

            page.remove_listener("request", capture_m3u8)

            if stream_urls:
                urls[name] = random.choice(stream_urls)
                print(f"✅ Final stream for {name}")
            else:
                print(f"⚠️ No streams found for {name}")

        await browser.close()
    return urls

def update_playlist(entries, new_urls):
    updated_entries = []

    for entry in entries:
        if entry["meta"].startswith("#EXTM3U"):
            updated_entries.append(entry)
            continue

        name = extract_channel_name(entry["meta"])

        # Always apply or append the VLC headers
        existing_headers = entry.get("headers", [])
        combined_headers = existing_headers[:]
        for vlc_line in VLC_OPT_LINES:
            if vlc_line not in combined_headers:
                combined_headers.append(vlc_line)

        updated_entries.append({
            "meta": entry["meta"],
            "headers": combined_headers,
            "url": new_urls.get(name, entry["url"])  # Use updated URL if available
        })

    return updated_entries

def save_playlist(entries, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for entry in entries:
            if entry["meta"]:
                f.write(entry["meta"] + "\n")
            if "headers" in entry:
                for h in entry["headers"]:
                    f.write(h + "\n")
            if entry["url"]:
                f.write(entry["url"] + "\n")
    print(f"\n✅ Saved updated playlist to {filepath}")

async def main():
    print("📥 Loading playlist...")
    entries = parse_m3u_playlist(INPUT_FILE)

    print("\n🌐 Scraping updated stream URLs...")
    new_urls = await fetch_updated_urls()

    print("\n🛠️ Rebuilding playlist with fresh streams and headers...")
    updated_entries = update_playlist(entries, new_urls)

    save_playlist(updated_entries, OUTPUT_FILE)

if __name__ == "__main__":
    asyncio.run(main())
