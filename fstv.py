import asyncio
from playwright.async_api import async_playwright
import re
import sys
import json

# Your channel mapping (keep names, logos, tv_ids if desired)
CHANNEL_MAPPING = {
    "ori2usaunanetwork": {"name": "USA Network", "tv_id": "USA.Network.-.East.Feed.us", "group": "USA"},
    "ori2usacbslosangeles": {"name": "CBS Los Angeles", "tv_id": "CBS.(KCBS).Los.Angeles,.CA.us", "logo": "http://drewlive24.duckdns.org:9000/Logos/CBS.png", "group": "USA"},
    "ori2usacbsgolazocdnsv2": {"name": "CBS Sports Golazo!", "tv_id": "plex.tv.CBS.Sports.Golazo.Network.plex", "group": "USA Sports"},
    "ori2cdnusnfl": {"name": "NFL Network", "tv_id": "The.NFL.Network.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-network-hz-us.png?raw=true", "group": "USA Sports"},
    "ori2cdnusredzone": {"name": "NFL RedZone", "tv_id": "NFL.RedZone.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-red-zone-hz-us.png?raw=true", "group": "USA Sports"},
    "ori2usespn": {"name": "ESPN", "tv_id": "ESPN.us", "group": "USA Sports"},
    "ori2usespn2": {"name": "ESPN2", "tv_id": "ESPN2.us", "group": "USA Sports"},
    "ori2cdnusuespn": {"name": "ESPNU", "tv_id": "ESPN.U.us", "group": "USA Sports"},
    "ori2usespnnews": {"name": "ESPNews", "tv_id": "ESPN.News.us", "group": "USA Sports"},
    "ori2usaespnsecnetwork": {"name": "SEC Network", "tv_id": "SEC.Network.us", "group": "USA Sports"},
    "ori2usespndeportes": {"name": "ESPN Deportes", "tv_id": "ESPN.Deportes.us", "group": "USA Sports"},
    "ori2usafs1": {"name": "FS1", "tv_id": "Fox.Sports.1.us", "group": "USA Sports"},
    "ori2usafs2": {"name": "FS2", "tv_id": "Fox.Sports.2.us", "group": "USA Sports"},
    "ori2usanbcnewyork": {"name": "NBC News", "tv_id": "plex.tv.NBC.News.NOW.plex", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbc-news-flat-us.png?raw=true", "group": "USA"},
    "ori2usagolf": {"name": "Golf Channel", "tv_id": "Golf.Channel.USA.us", "group": "USA Sports"},
    "ori2cdnustennistv": {"name": "Tennis Channel", "tv_id": "The.Tennis.Channel.us", "group": "USA Sports"},
    "ori2cdnustennistv2": {"name": "Tennis Channel 2", "tv_id": "The.Tennis.Channel.us", "group": "USA Sports"},
    "ori2usaunirso": {"name": "NBC Universo", "tv_id": "NBC.Universo.-.Eastern.feed.us", "group": "USA"},
    "ori2usnbc": {"name": "NBC", "tv_id": "NBC.(WNBC).New.York,.NY.us", "group": "USA"},
    "ori2usmsnbc": {"name": "MSNBC", "tv_id": "MSNBC.USA.us", "group": "USA"},
    "ori2usacnbc": {"name": "CNBC", "tv_id": "CNBC.USA.us", "group": "USA"},
    "ori22uktnfsport1": {"name": "TNT Sports 1", "tv_id": "TNT.Sports.1.HD.uk", "group": "UK Sports"},
    "ori22uktnfsport2": {"name": "TNT Sports 2", "tv_id": "TNT.Sports.2.HD.uk", "group": "UK Sports"},
    "ori22uktnfsport3": {"name": "TNT Sports 3", "tv_id": "TNT.Sports.3.HD.uk", "group": "UK Sports"},
    "ori22uktnfsport5": {"name": "TNT Sports 5", "tv_id": "TNT.Sports.Ultimate.uk", "group": "UK Sports"},
    "ori22uktnfsport4": {"name": "TNT Sports 4", "tv_id": "TNT.Sports.4.HD.uk", "group": "UK Sports"},
    "ori23cdnukeurosport1": {"name": "Eurosport 1 UK", "tv_id": "Eurosport.es", "group": "UK Sports"},
    "ori23cdnukeurosport2": {"name": "Eurosport 2 UK", "tv_id": "Eurosport.2.es", "group": "UK Sports"},
    "ori21ukskysportgolf": {"name": "Sky Sport Golf UK", "tv_id": "SkySp.Golf.HD.uk", "group": "UK Sports"},
    "ori21ukskysporttennis": {"name": "Sky Sport Tennis UK", "tv_id": "SkySp.Tennis.HD.uk", "group": "UK Sports"},
    "ori2cdnukmutv": {"name": "MUTV UK", "tv_id": "MUTV.HD.uk", "group": "UK Sports"},
    "ori2sv3uklaliga": {"name": "La Liga UK", "tv_id": "LA.LIGA.za", "group": "UK Sports"},
    "ori2uksv2skysportplus": {"name": "Sky Sport Plus UK", "tv_id": "SkySp.PL.HD.uk", "group": "UK Sports"}, # Key fixed
    "ori21cdnsv3ukfootball": {"name": "Sky Sport Football", "tv_id": "SkySp.Fball.HD.uk", "group": "UK Sports"},
    "ori21ukskysportpremierleague": {"name": "Sky Sport Premier League UK", "tv_id": "SkyPremiereHD.uk", "group": "UK Sports"},
    "ori2skysportmix": {"name": "Sky Sport Mix UK", "tv_id": "SkySp.Mix.HD.uk", "group": "UK Sports"},
    "ori21cdnsv3ukmainent": {"name": "Sky Sport Main", "tv_id": "SkySpMainEvHD.uk", "group": "UK Sports"},
    "ori21cdnukskysportracing": {"name": "Sky Sport Racing UK", "tv_id": "SkySp.Racing.HD.uk", "group": "UK Sports"},
    "ori23ukpremiersport1": {"name": "Premier Sport 1 UK", "tv_id": "Premier.Sports.1.HD.uk", "group": "UK Sports"},
    "ori23ukpremiersport2": {"name": "Premier Sport 2 UK", "tv_id": "Premier.Sports.2.HD.uk", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-kingdom/premier-sports-2-uk.png?raw=true", "group": "UK Sports"},
    "ori2ukracingtv": {"name": "Racing TV UK", "tv_id": "Racing.TV.HD.uk", "group": "UK Sports"},
    "ori2ukskysportf1": {"name": "Sky Sport F1 UK", "tv_id": "SkySp.F1.HD.uk", "group": "UK Sports"},
    "ori2skysportarena": {"name": "Sky Sport Arena UK", "tv_id": "Sky.Sports+.Dummy.us", "group": "UK Sports"},
    "ori21cdnukskysportaction": {"name": "Sky Sports Action UK", "tv_id": "SkySp.ActionHD.uk", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-kingdom/sky-sports-action-hz-uk.png?raw=true", "group": "UK Sports"},
    "ori2ukskysportcricket": {"name": "Sky Sport Cricket UK", "tv_id": "SkySpCricket.HD.uk", "group": "UK Sports"},
    "ori21ukskysportnews": {"name": "Sky Sport News UK", "tv_id": "SkySp.News.HD.uk", "group": "UK Sports"},
    "ukskysportdarts": {"name": "Sky Sport Darts UK", "tv_id": "Sky.Sports+.Dummy.us", "group": "UK Sports"},
    "ori2usabeinsportd": {"name": "BeIN Sports USA", "tv_id": "beIN.Sport.USA.us", "group": "USA Sports"},
    "ori2usabeinsportxtra": {"name": "BeIN Sports Xtra USA", "tv_id": "beIN.Sports.Xtra.(KSKJ-CD).Los.Angeles,.CA.us", "group": "USA Sports"},
    "ori2usabeinsportespanol": {"name": "BeIN Sports Español", "tv_id": "613759", "group": "USA Sports"},
    "ori2usabeinespanolxtra": {"name": "BeIN Sports Español Xtra", "tv_id": "613759", "group": "USA Sports"},
    "ori23ukitv1": {"name": "ITV 1 UK", "tv_id": "ITV1.HD.uk", "group": "UK"},
    "ori23ukitv2": {"name": "ITV 2 UK", "tv_id": "ITV2.HD.uk", "group": "UK"},
    "ori23ukitv3": {"name": "ITV 3 UK", "tv_id": "ITV3.HD.uk", "group": "UK"},
    "ori23ukitv4": {"name": "ITV 4 UK", "tv_id": "ITV4.HD.uk", "group": "UK"},
    "ori2cdnuklfctv": {"name": "LFC TV UK", "tv_id": "LFCTV.HD.uk", "group": "UK Sports"},
    "ori2usafubosport": {"name": "Fubo Sports USA", "tv_id": "Fubo.Sports.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fubo-sports-network-us.png?raw=true", "group": "USA Sports"},
    "ori2ukdazn": {"name": "DAZN 1 UK", "tv_id": "DAZN.Dummy.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/germany/dazn1-de.png?raw=true", "group": "UK Sports"},
    "ori2ionusa": {"name": "ION USA", "tv_id": "ION..-.Eastern.Feed.us", "group": "USA"},
    "ori2usafoxsoccerplus": {"name": "Fox Soccer Plus", "tv_id": "FOX.Soccer.Plus.us", "group": "USA Sports"},
    "ori2usatycsport": {"name": "TyC Sports", "tv_id": "TyC.Sports.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/argentina/tyc-sports-ar.png?raw=true", "group": "USA Sports"},
    "ori2usamarqueesportnetwork": {"name": "Marquee Sports Network", "tv_id": "Marquee.Sports.Network.us", "group": "USA Sports"},
    "ori2yesusa": {"name": "YES Network USA", "tv_id": "YES.Network.us", "group": "USA Sports"},
    "ori2usaabc": {"name": "ABC", "tv_id": "ABC.(KABC).Los.Angeles,.CA.us", "group": "USA"},
    "ori2usatudn": {"name": "TUDN", "tv_id": "TUDN.us", "group": "USA Sports"},
    "ori2usafoxchannel": {"name": "Fox Los Angeles", "tv_id": "FOX.(KTTV).Los.Angeles,.CA.us", "logo": "http://drewlive24.duckdns.org:9000/Logos/FOX.png", "group": "USA"},
    "ori2usatelemundo": {"name": "Telemundo", "tv_id": "Telemundo.(KVEA).Los.Angeles,.CA.us", "group": "USA"},
    "ori2usaunimas": {"name": "UniMás", "tv_id": "UniMas.(KFTH).Houston,.TX.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/unimas-us.png?raw=true", "group": "USA"},
    "ori2cdnusnhlnetwork": {"name": "NHL Network", "tv_id": "NHL.Network.USA.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nhl-network-us.png?raw=true", "group": "USA Sports"},
    "ori2uswillowhd": {"name": "Willow Cricket HD", "tv_id": "Willow.Cricket.HDTV.(WILLOWHD).us", "group": "USA Sports"},
    "ori2uswillowxtra": {"name": "Willow Xtra", "tv_id": "Willow.Xtra.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/willow-xtra-us.png?raw=true", "group": "USA Sports"},
    "ori2cdnusnbatv": {"name": "NBA TV", "tv_id": "NBA.TV.USA.us", "logo": "http://drewlive24.duckdns.org:9000/Logos/NBATV.png", "group": "USA Sports"},
    "ori2usmlbnetwork": {"name": "MLB Network", "tv_id": "MLB.Network.us", "group": "USA Sports"},
    "ori2uscnn": {"name": "CNN", "tv_id": "CNN.us", "group": "USA"},
    "ori2cdnuswnetwork": {"name": "W Network", "tv_id": "W.Network.Canada.East.(WTN).ca", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/w-network-ca.png?raw=true", "group": "Canada"},
    "ori2cdnusaccnetwork": {"name": "ACC Network", "tv_id": "ACC.Network.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/acc-network-us.png?raw=true", "group": "USA"},
    "ori2usafoxnews": {"name": "Fox News", "tv_id": "Fox.News.us", "group": "USA"},
    "ori2cdnuswfn": {"name": "World Fishing Network", "tv_id": "World.Fishing.Network.(US).(WFN).us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/world-fishing-network-us.png?raw=true", "group": "USA"},
    "ori2usfightnetwork": {"name": "The Fight Network", "tv_id": "The.Fight.Network.(United.States).(TFN).us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fight-network-us.png?raw=true", "group": "USA"},
    "ori2tntusa": {"name": "TNT", "tv_id": "TNT.-.Eastern.Feed.us", "group": "USA"},
    "ori2trutv": {"name": "truTV", "tv_id": "truTV.USA.-.Eastern.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tru-tv-us.png?raw=true", "group": "USA"},
    "oriaxstv": {"name": "AXS TV", "tv_id": "AXS.TV.USA.HD.us", "group": "USA"},
    "ori2ukbbcone": {"name": "BBC One UK", "tv_id": "BBC.One.EastHD.uk", "group": "UK"},
    "ori2ukbbctwo": {"name": "BBC Two UK", "tv_id": "BBC.Two.HD.uk", "group": "UK"},
    "ori2ukbbcnews": {"name": "BBC News UK", "tv_id": "BBC.NEWS.HD.uk", "group": "UK"},
    "ori2foxdeportes": {"name": "Fox Deportes", "tv_id": "Fox.Deportes.us", "group": "USA Sports"},
    "ori2paramountnetwork": {"name": "Paramount Network", "tv_id": "Paramount.Network.USA.-.Eastern.Feed.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/paramount-network-hz-us.png?raw=true", "group": "USA"},
    "ori2caonesoccer": {"name": "OneSoccer Canada", "tv_id": "One.Soccer.ca", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/one-soccer-ca.png?raw=true", "group": "Canada Sports"},
    "ori2dedazn1": {"name": "DAZN 1 Germany", "tv_id": "DAZN.1.de", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/germany/dazn1-de.png?raw=true", "group": "Germany"},
    "ori2deskydeevent": {"name": "Sky DE Top Event", "tv_id": "Sky.Sport.Top.Event.de", "group": "Germany Sports"},
    "eplskydepre": {"name": "Sky Sport Premier League DE", "tv_id": "Sky.Sport.Premier.League.de", "group": "Germany Sports"},
    "ori2dedazn2": {"name": "DAZN 2 Germany", "tv_id": "DAZN.2.de", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/germany/dazn2-de.png?raw=true", "group": "Germany"},
    "ori2desportdigital": {"name": "SportDigital Germany", "tv_id": "sportdigital.Fussball.de", "group": "Germany Sports"},
    "ori2deskydenews": {"name": "Sky Sport News DE", "tv_id": "Sky.Sport.News.de", "group": "Germany Sports"},
    "ori2deskydeMix": {"name": "Sky Mix DE", "tv_id": "Sky.Sport.Mix.de", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-kingdom/sky-mix-uk.png?raw=true", "group": "Germany Sports"},
    "ori2debundesliga1": {"name": "Bundesliga 1 Germany", "tv_id": "Sky.Sport.Bundesliga.de", "group": "Germany Sports"},
    "ori2fox502": {"name": "Fox Sports 502 AU", "tv_id": "FoxCricket.au", "group": "Australia Sports"},
    "ori2zentdiscory": {"name": "Discovery Channel", "tv_id": "Discovery.Channel.(US).-.Eastern.Feed.us", "group": "Entertainment"},
    "ori2zentcinemax": {"name": "Cinemax", "tv_id": "Cinemax.-.Eastern.Feed.us", "group": "Movies"},
    "ori2usahbo": {"name": "HBO", "tv_id": "HBO.-.Eastern.Feed.us", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-us.png?raw=true", "group": "Movies"},
    "ori2tbs": {"name": "TBS", "tv_id": "TBS.-.East.us", "group": "Entertainment"},
    "ori2goltv": {"name": "GOL TV", "tv_id": "Gol.TV.USA.us", "group": "USA Sports"},
    "ori2tsn1": {"name": "TSN 1", "tv_id": "TSN1.ca", "group": "Canada Sports"},
    "ori2tsn2": {"name": "TSN 2", "tv_id": "TSN2.ca", "group": "Canada Sports"},
    "ori2tsn3": {"name": "TSN 3", "tv_id": "TSN3.ca", "group": "Canada Sports"},
    "ori2tsn4": {"name": "TSN 4", "tv_id": "TSN4.ca", "group": "Canada Sports"},
    "ori2tsn5": {"name": "TSN 5", "tv_id": "TSN5.ca", "group": "Canada Sports"},
    "ori2ptbenfica": {"name": "Benfica TV", "tv_id": "Benfica.TV.fr", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Logo_Benfica_TV.png/1200px-Logo_Benfica_TV.png", "group": "Portugal Sports"},
    "ori2ptsporttv1": {"name": "Sport TV1 Portugal", "tv_id": "SPORT.TV1.HD.pt", "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/portugal/sport-tv-1-pt.png?raw=true", "group": "Portugal Sports"},
}

def normalize_channel_name(name: str) -> str:
    """Normalize channel name to use as mapping key"""
    cleaned_name = re.sub(r'[^a-zA-Z0-9]', '', name)
    return cleaned_name.strip().lower()

def prettify_name(raw: str) -> str:
    """Prettify raw channel name for display"""
    raw = re.sub(r'VE[-\s]*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\([^)]*\)', '', raw)
    raw = re.sub(r'[^a-zA-Z0-9\s]', '', raw)
    return re.sub(r'\s+', ' ', raw.strip()).title()

MIRRORS = [
    "https://fstv.zip/live-tv.html?timezone=America%2FDenver",
    "https://fstv.online/live-tv.html?timezone=America%2FDenver",
    "https://fstv.space/live-tv.html?timezone=America%2FDenver",
]

async def fetch_fstv_channels():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"
        )
        page = await context.new_page()
        context.on("page", lambda popup: asyncio.create_task(popup.close()))
        channels_data = []
        visited_urls = set()

        for url in MIRRORS:
            try:
                print(f"🌐 Trying {url}...", flush=True)
                await page.goto(url, timeout=90000, wait_until="domcontentloaded")
                await page.wait_for_selector(".item-channel", timeout=15000)
                
                num_channels = len(await page.query_selector_all(".item-channel"))
                if num_channels == 0:
                    print(f"⚠️ No channels found on {url}, trying next mirror.", flush=True)
                    continue

                for i in range(num_channels):
                    all_elements_on_page = await page.query_selector_all(".item-channel")
                    if i >= len(all_elements_on_page):
                        print("Fewer elements than expected after reload, breaking loop.")
                        break
                    
                    channel_element = all_elements_on_page[i]

                    raw_name = await channel_element.get_attribute("title")
                    if not raw_name:
                        continue

                    normalized_name = normalize_channel_name(raw_name)
                    mapped_info = CHANNEL_MAPPING.get(normalized_name, {})
                    new_name = mapped_info.get("name", prettify_name(raw_name))
                    tv_id = mapped_info.get("tv_id", "")
                    logo = mapped_info.get("logo", await channel_element.get_attribute("data-logo"))
                    group_title = "FSTV"

                    m3u8_url = None
                    request_captured = asyncio.Event()

                    async def handle_request(request):
                        nonlocal m3u8_url
                        if ".m3u8" in request.url and "auth_key" in request.url:
                            m3u8_url = request.url
                            if not request_captured.is_set():
                                request_captured.set()

                    page.on("request", handle_request)
                    print(f"👆 Clicking on {new_name} ({i+1}/{num_channels})...", flush=True)
                    await channel_element.click(force=True, timeout=10000)

                    # ✅ KEY FIX: Pause for 2 seconds to give the stream request time to start.
                    await asyncio.sleep(2)

                    try:
                        await asyncio.wait_for(request_captured.wait(), timeout=15.0)
                    except asyncio.TimeoutError:
                        print(f"⚠️ Timeout: no valid .m3u8 URL found for {new_name}", flush=True)

                    page.remove_listener("request", handle_request)

                    if m3u8_url and m3u8_url not in visited_urls:
                        channels_data.append({
                            "url": m3u8_url, "logo": logo, "name": new_name,
                            "tv_id": tv_id, "group": group_title
                        })
                        visited_urls.add(m3u8_url)
                        print(f"✅ Added {new_name}", flush=True)
                    else:
                        print(f"❌ Skipping {new_name}: No URL or already processed", flush=True)

                    if i < num_channels - 1:
                        await page.goto(url, wait_until="domcontentloaded")
                        await page.wait_for_selector(".item-channel", timeout=15000)

                print(f"🎉 Successfully processed all channels from {url}", flush=True)
                await browser.close()
                return channels_data

            except Exception as e:
                print(f"❌ Failed on {url}: {e}", flush=True)
                continue

        await browser.close()
        raise Exception("❌ All mirrors failed")

def build_playlist(channels_data):
    lines = ["#EXTM3U\n"]
    for ch in channels_data:
        tvg_id = f' tvg-id="{ch["tv_id"]}"' if ch["tv_id"] else ""
        logo = f' tvg-logo="{ch["logo"]}"' if ch["logo"] else ""
        group = f' group-title="{ch["group"]}"'
        lines.append(f'#EXTINF:-1{tvg_id}{logo}{group},{ch["name"]}\n')
        lines.append(
            '#EXTVLCOPT:http-origin=https://fstv.space/\n'
            '#EXTVLCOPT:http-referrer=https://fstv.space/\n'
            '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0\n'
        )
        lines.append(ch["url"] + "\n")
    return lines

async def main():
    try:
        print("🚀 Starting FSTV scraping...", flush=True)
        channels_data = await fetch_fstv_channels()
        if channels_data:
            playlist = build_playlist(channels_data)
            with open("FSTV24.m3u8", "w", encoding="utf-8") as f:
                f.writelines(playlist)
            print("🎯 Playlist created: FSTV24.m3u8", flush=True)
        else:
            print("🚫 No channels were scraped. Playlist not generated.", flush=True)
    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
