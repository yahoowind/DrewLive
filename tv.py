import asyncio
import re
import urllib.parse
from playwright.async_api import async_playwright

OUTPUT_M3U = "TheTVApp.m3u8"
BASE_URL = "https://thetvapp.to"
CHANNEL_LIST_URL = f"{BASE_URL}/tv"
M3U8_REGEX = re.compile(r"https://[^\s\"']+\.m3u8[^\s\"']*")

channel_names = [
  "A&E HD",
  "A&E SD",
  "ACC Network HD",
  "ACC Network SD",
  "AMC HD",
  "AMC SD",
  "American Heroes Channel HD",
  "American Heroes Channel SD",
  "Animal Planet HD",
  "Animal Planet SD",
  "BBC America HD",
  "BBC America SD",
  "BBC World News HD HD",
  "BBC World News HD SD",
  "BET HD",
  "BET Her HD",
  "BET Her SD",
  "BET SD",
  "Big Ten Network HD",
  "Big Ten Network SD",
  "Bloomberg TV HD",
  "Bloomberg TV SD",
  "Boomerang HD",
  "Boomerang SD",
  "Bravo HD",
  "Bravo SD",
  "CBS Sports Network HD",
  "CBS Sports Network SD",
  "CMT HD",
  "CMT SD",
  "CNBC HD",
  "CNBC SD",
  "CNN HD",
  "CNN SD",
  "CSPAN 2 HD",
  "CSPAN 2 SD",
  "CSPAN HD",
  "CSPAN SD",
  "Cartoon Network HD",
  "Cartoon Network SD",
  "Cinemax HD",
  "Cinemax SD",
  "Comedy Central HD",
  "Comedy Central SD",
  "Cooking Channel HD",
  "Cooking Channel SD",
  "Crime & Investigation HD HD",
  "Crime & Investigation HD SD",
  "Destination America HD",
  "Destination America SD",
  "Discovery Family Channel HD",
  "Discovery Family Channel SD",
  "Discovery HD",
  "Discovery Life HD",
  "Discovery Life SD",
  "Discovery SD",
  "Disney Channel (East) HD",
  "Disney Channel (East) SD",
  "Disney Junior HD",
  "Disney Junior SD",
  "Disney XD HD",
  "Disney XD SD",
  "E! HD",
  "E! SD",
  "ESPN HD",
  "ESPN SD",
  "ESPN2 HD",
  "ESPN2 SD",
  "ESPNU HD",
  "ESPNU SD",
  "ESPNews HD",
  "ESPNews SD",
  "FOX News Channel HD",
  "FOX News Channel SD",
  "FOX Sports 1 HD",
  "FOX Sports 1 SD",
  "FOX Sports 2 HD",
  "FOX Sports 2 SD",
  "FX HD",
  "FX Movie HD",
  "FX Movie SD",
  "FX SD",
  "FXX HD",
  "FXX SD",
  "FYI HD",
  "FYI SD",
  "Food Network HD",
  "Food Network SD",
  "Fox Business Network HD",
  "Fox Business Network SD",
  "Freeform HD",
  "Freeform SD",
  "Fuse HD HD",
  "Fuse HD SD",
  "Golf Channel HD",
  "Golf Channel SD",
  "HBO 2 East HD",
  "HBO 2 East SD",
  "HBO Comedy HD HD",
  "HBO Comedy HD SD",
  "HBO East HD",
  "HBO East SD",
  "HBO Family East HD",
  "HBO Family East SD",
  "HBO Signature HD",
  "HBO Signature SD",
  "HBO Zone HD HD",
  "HBO Zone HD SD",
  "HGTV HD",
  "HGTV SD",
  "HLN HD",
  "HLN SD",
  "Hallmark Drama HD HD",
  "Hallmark Drama HD SD",
  "Hallmark HD",
  "Hallmark Movies & Mysteries HD HD",
  "Hallmark Movies & Mysteries HD SD",
  "Hallmark SD",
  "History HD",
  "History SD",
  "IFC HD",
  "IFC SD",
  "ION Television East HD HD",
  "ION Television East HD SD",
  "Investigation Discovery HD",
  "Investigation Discovery SD",
  "LMN HD",
  "LMN SD",
  "Lifetime HD",
  "Lifetime SD",
  "Logo HD",
  "Logo SD",
  "MLB Network HD",
  "MLB Network SD",
  "MSNBC HD",
  "MSNBC SD",
  "MTV HD",
  "MTV SD",
  "MeTV Toons HD",
  "MeTV Toons SD",
  "MoreMAX HD",
  "MoreMAX SD",
  "MotorTrend HD HD",
  "MotorTrend HD SD",
  "MovieMAX HD",
  "MovieMAX SD",
  "NBA TV HD",
  "NBA TV SD",
  "NFL Network HD",
  "NFL Network SD",
  "NFL Red Zone HD",
  "NFL Red Zone SD",
  "NHL Network HD",
  "NHL Network SD",
  "Nat Geo WILD HD",
  "Nat Geo WILD SD",
  "National Geographic HD",
  "National Geographic SD",
  "Newsmax TV HD",
  "Newsmax TV SD",
  "Nick Jr. HD",
  "Nick Jr. SD",
  "Nickelodeon East HD",
  "Nickelodeon East SD",
  "Nicktoons HD",
  "Nicktoons SD",
  "OWN HD",
  "OWN SD",
  "Outdoor Channel HD",
  "Outdoor Channel SD",
  "Oxygen True Crime HD",
  "Oxygen True Crime SD",
  "PBS 13 (WNET) New York HD",
  "PBS 13 (WNET) New York SD",
  "ReelzChannel HD",
  "ReelzChannel SD",
  "SEC Network HD",
  "SEC Network SD",
  "SHOWTIME 2 HD",
  "SHOWTIME 2 SD",
  "STARZ East HD",
  "STARZ East SD",
  "SYFY HD",
  "SYFY SD",
  "Science HD",
  "Science SD",
  "Showtime (E) HD",
  "Showtime (E) SD",
  "SundanceTV HD HD",
  "SundanceTV HD SD",
  "TBS HD",
  "TBS SD",
  "TCM HD",
  "TCM SD",
  "TLC HD",
  "TLC SD",
  "TNT HD",
  "TNT SD",
  "TV One HD HD",
  "TV One HD SD",
  "TeenNick HD",
  "TeenNick SD",
  "Telemundo East HD",
  "Telemundo East SD",
  "Tennis Channel HD",
  "Tennis Channel SD",
  "The CW (WPIX New York) HD",
  "The CW (WPIX New York) SD",
  "The Movie Channel East HD",
  "The Movie Channel East SD",
  "The Weather Channel HD",
  "The Weather Channel SD",
  "Travel Channel HD",
  "Travel Channel SD",
  "USA Network HD",
  "USA Network SD",
  "Universal Kids HD",
  "Universal Kids SD",
  "Univision East HD",
  "Univision East SD",
  "VH1 HD",
  "VH1 SD",
  "VICE HD",
  "VICE SD",
  "WABC (New York) ABC East HD",
  "WABC (New York) ABC East SD",
  "WCBS (New York) CBS East HD",
  "WCBS (New York) CBS East SD",
  "WE tv HD",
  "WE tv SD",
  "WNBC (New York) NBC East HD",
  "WNBC (New York) NBC East SD",
  "WNYW (New York) FOX East HD",
  "WNYW (New York) FOX East SD",
  "truTV HD",
  "truTV SD"
]

CHANNEL_METADATA = [
  {
    "name": "A&E US Eastern Feed SD",
    "id": "ae-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/a-and-e-us.png?raw=true"
  },
  {
    "name": "A&E US Eastern Feed HD",
    "id": "ae-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/a-and-e-us.png?raw=true"
  },
  {
    "name": "ABC (KABC) Los Angeles SD",
    "id": "abc-kabc-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/abc-logo-2013-garnet-us.png?raw=true"
  },
  {
    "name": "ABC (KABC) Los Angeles HD",
    "id": "abc-kabc-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/abc-logo-2013-garnet-us.png?raw=true"
  },
  {
    "name": "ABC (WABC) New York ",
    "id": "abc-wabc-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/abc-logo-2013-garnet-us.png?raw=true"
  },
  {
    "name": "ABC (WABC) New York",
    "id": "abc-wabc-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/abc-logo-2013-garnet-us.png?raw=true"
  },
  {
    "name": "ACC Network SD",
    "id": "acc-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/acc-network-us.png?raw=true"
  },
  {
    "name": "ACC Network HD",
    "id": "acc-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/acc-network-us.png?raw=true"
  },
  {
    "name": "Altitude Sports Denver SD",
    "id": "altitude-sports-denver",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/altitude-sports-us.png?raw=true"
  },
  {
    "name": "Altitude Sports Denver HD",
    "id": "altitude-sports-denver",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/altitude-sports-us.png?raw=true"
  },
  {
    "name": "AMC Eastern Feed SD",
    "id": "amc-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/amc-us.png?raw=true"
  },
  {
    "name": "AMC Eastern Feed HD",
    "id": "amc-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/amc-us.png?raw=true"
  },
  {
    "name": "American Heroes Channel SD",
    "id": "american-heroes-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/american-heroes-channel-us.png?raw=true"
  },
  {
    "name": "American Heroes Channel HD",
    "id": "american-heroes-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/american-heroes-channel-us.png?raw=true"
  },
  {
    "name": "Animal Planet US East SD",
    "id": "animal-planet-us-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/animal-planet-us.png?raw=true"
  },
  {
    "name": "Animal Planet US East HD",
    "id": "animal-planet-us-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/animal-planet-us.png?raw=true"
  },
  {
    "name": "BBC America East SD",
    "id": "bbc-america-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bbc-america-us.png?raw=true"
  },
  {
    "name": "BBC America East HD",
    "id": "bbc-america-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bbc-america-us.png?raw=true"
  },
  {
    "name": "BBC News North America HD SD",
    "id": "bbc-news-north-america-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bbc-america-hz-us.png?raw=true"
  },
  {
    "name": "BBC News North America HD HD",
    "id": "bbc-news-north-america-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bbc-america-hz-us.png?raw=true"
  },
  {
    "name": "BET Eastern Feed SD",
    "id": "bet-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bet-us.png?raw=true"
  },
  {
    "name": "BET Eastern Feed HD",
    "id": "bet-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bet-us.png?raw=true"
  },
  {
    "name": "BET Her SD",
    "id": "bet-her",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bet-her-us.png?raw=true"
  },
  {
    "name": "BET Her HD",
    "id": "bet-her",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bet-her-us.png?raw=true"
  },
  {
    "name": "Big Ten Network SD",
    "id": "big-ten-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/big-ten-network-us.png?raw=true"
  },
  {
    "name": "Big Ten Network HD",
    "id": "big-ten-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/big-ten-network-us.png?raw=true"
  },
  {
    "name": "Bloomberg TV USA SD",
    "id": "bloomberg-tv-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bloomberg-television-us.png?raw=true"
  },
  {
    "name": "Bloomberg TV USA HD",
    "id": "bloomberg-tv-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bloomberg-television-us.png?raw=true"
  },
  {
    "name": "Boomerang SD",
    "id": "boomerang",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/boomerang-us.png?raw=true"
  },
  {
    "name": "Boomerang HD",
    "id": "boomerang",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/boomerang-us.png?raw=true"
  },
  {
    "name": "Bravo USA Eastern Feed SD",
    "id": "bravo-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bravo-us.png?raw=true"
  },
  {
    "name": "Bravo USA Eastern Feed HD",
    "id": "bravo-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bravo-us.png?raw=true"
  },
  {
    "name": "C-SPAN SD",
    "id": "cspan",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/c-span-1-us.png?raw=true"
  },
  {
    "name": "C-SPAN HD",
    "id": "cspan",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/c-span-1-us.png?raw=true"
  },
  {
    "name": "C-SPAN 2 SD",
    "id": "cspan-2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/c-span-2-us.png?raw=true"
  },
  {
    "name": "C-SPAN 2 HD",
    "id": "cspan-2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/c-span-2-us.png?raw=true"
  },
  {
    "name": "Cartoon Network USA Eastern Feed SD",
    "id": "cartoon-network-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cartoon-network-us.png?raw=true"
  },
  {
    "name": "Cartoon Network USA Eastern Feed HD",
    "id": "cartoon-network-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cartoon-network-us.png?raw=true"
  },
  {
    "name": "CBS (KCBS) Los Angeles SD",
    "id": "cbs-kcbs-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cbs-logo-white-us.png?raw=true"
  },
  {
    "name": "CBS (KCBS) Los Angeles HD",
    "id": "cbs-kcbs-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cbs-logo-white-us.png?raw=true"
  },
  {
    "name": "CBS (WCBS) New York ",
    "id": "cbs-wcbs-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cbs-logo-white-us.png?raw=true"
  },
  {
    "name": "CBS (WCBS) New York ",
    "id": "cbs-wcbs-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cbs-logo-white-us.png?raw=true"
  },
  {
    "name": "CBS Sports Network USA SD",
    "id": "cbs-sports-network-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cbs-sports-network-us.png?raw=true"
  },
  {
    "name": "CBS Sports Network USA HD",
    "id": "cbs-sports-network-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cbs-sports-network-us.png?raw=true"
  },
  {
    "name": "Chicago Sports Network SD",
    "id": "chicago-sports-network",
    "logo": "http://drewlive24.duckdns.org:9000/Logos/ChicagoSportsNetwork.png"
  },
  {
    "name": "Chicago Sports Network HD",
    "id": "chicago-sports-network",
    "logo": "http://drewlive24.duckdns.org:9000/Logos/ChicagoSportsNetwork.png"
  },
  {
    "name": "Cinemax Eastern Feed SD",
    "id": "cinemax-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cinemax-us.png?raw=true"
  },
  {
    "name": "Cinemax Eastern Feed HD",
    "id": "cinemax-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cinemax-us.png?raw=true"
  },
  {
    "name": "CMT US Eastern Feed SD",
    "id": "cmt-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cmt-color-us.png?raw=true"
  },
  {
    "name": "CMT US Eastern Feed HD",
    "id": "cmt-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cmt-color-us.png?raw=true"
  },
  {
    "name": "CNBC USA SD",
    "id": "cnbc-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cnbc-prime-neon-shark-tank-us.png?raw=true"
  },
  {
    "name": "CNBC USA HD",
    "id": "cnbc-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cnbc-prime-neon-shark-tank-us.png?raw=true"
  },
  {
    "name": "CNN US SD",
    "id": "cnn",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cnn-us.png?raw=true"
  },
  {
    "name": "CNN US HD",
    "id": "cnn",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cnn-us.png?raw=true"
  },
  {
    "name": "Comedy Central (US) Eastern Feed SD",
    "id": "comedy-central-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/comedy-central-icon-us.png?raw=true"
  },
  {
    "name": "Comedy Central (US) Eastern Feed HD",
    "id": "comedy-central-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/comedy-central-icon-us.png?raw=true"
  },
  {
    "name": "Crime & Investigation Network USA HD SD",
    "id": "crime-investigation-network-usa-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/crime-and-investigation-us.png?raw=true"
  },
  {
    "name": "Crime & Investigation Network USA HD HD",
    "id": "crime-investigation-network-usa-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/crime-and-investigation-us.png?raw=true"
  },
  {
    "name": "CW (KFMB-TV2) San Diego SD",
    "id": "cw-kfmbtv2-san-diego-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cw-us.png?raw=true"
  },
  {
    "name": "CW (KFMB-TV2) San Diego HD",
    "id": "cw-kfmbtv2-san-diego-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cw-us.png?raw=true"
  },
  {
    "name": "CW (WDCW) District of Columbia SD",
    "id": "cw-wdcw-district-of-columbia",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cw-us.png?raw=true"
  },
  {
    "name": "CW (WDCW) District of Columbia HD",
    "id": "cw-wdcw-district-of-columbia",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cw-us.png?raw=true"
  },
  {
    "name": "Destination America SD",
    "id": "destination-america",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/destination-america-us.png?raw=true"
  },
  {
    "name": "Destination America HD",
    "id": "destination-america",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/destination-america-us.png?raw=true"
  },
  {
    "name": "Discovery Channel (US) Eastern Feed SD",
    "id": "discovery-channel-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-channel-icon-2-us.png?raw=true"
  },
  {
    "name": "Discovery Channel (US) Eastern Feed HD",
    "id": "discovery-channel-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-channel-icon-2-us.png?raw=true"
  },
  {
    "name": "Discovery Family Channel SD",
    "id": "discovery-family-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-family-us.png?raw=true"
  },
  {
    "name": "Discovery Family Channel HD",
    "id": "discovery-family-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-family-us.png?raw=true"
  },
  {
    "name": "Discovery Life Channel SD",
    "id": "discovery-life-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-life-us.png?raw=true"
  },
  {
    "name": "Discovery Life Channel HD",
    "id": "discovery-life-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-life-us.png?raw=true"
  },
  {
    "name": "Disney Eastern Feed SD",
    "id": "disney-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/screen-bug/disney-channel-bug-us.png?raw=true"
  },
  {
    "name": "Disney Eastern Feed HD",
    "id": "disney-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/screen-bug/disney-channel-bug-us.png?raw=true"
  },
  {
    "name": "Disney Junior USA East SD",
    "id": "disney-junior-usa-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/disney-jr-us.png?raw=true"
  },
  {
    "name": "Disney Junior USA East HD",
    "id": "disney-junior-usa-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/disney-jr-us.png?raw=true"
  },
  {
    "name": "Disney XD USA Eastern Feed SD",
    "id": "disney-xd-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/disney-xd-us.png?raw=true"
  },
  {
    "name": "Disney XD USA Eastern Feed HD",
    "id": "disney-xd-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/disney-xd-us.png?raw=true"
  },
  {
    "name": "E! Entertainment USA Eastern Feed SD",
    "id": "e-entertainment-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/e-entertainment-us.png?raw=true"
  },
  {
    "name": "E! Entertainment USA Eastern Feed HD",
    "id": "e-entertainment-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/e-entertainment-us.png?raw=true"
  },
  {
    "name": "ESPN SD",
    "id": "espn",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-icon-us.png?raw=true"
  },
  {
    "name": "ESPN HD",
    "id": "espn",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-icon-us.png?raw=true"
  },
  {
    "name": "ESPN Deportes SD",
    "id": "espn-deportes",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-deportes-us.png?raw=true"
  },
  {
    "name": "ESPN Deportes HD",
    "id": "espn-deportes",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-deportes-us.png?raw=true"
  },
  {
    "name": "ESPN News SD",
    "id": "espn-news",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espnews-us.png?raw=true"
  },
  {
    "name": "ESPN News HD",
    "id": "espn-news",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espnews-us.png?raw=true"
  },
  {
    "name": "ESPN U SD",
    "id": "espn-u",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-u-us.png?raw=true"
  },
  {
    "name": "ESPN U HD",
    "id": "espn-u",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-u-us.png?raw=true"
  },
  {
    "name": "ESPN2 SD",
    "id": "espn2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-2-us.png?raw=true"
  },
  {
    "name": "ESPN2 HD",
    "id": "espn2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-2-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Indiana SD",
    "id": "fanduel-sports-indiana",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-indiana-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Indiana HD",
    "id": "fanduel-sports-indiana",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-indiana-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Detroit SD",
    "id": "fanduel-sports-network-detroit-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-detroit-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Detroit HD",
    "id": "fanduel-sports-network-detroit-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-detroit-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Florida SD",
    "id": "fanduel-sports-network-florida",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-florida-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Florida HD",
    "id": "fanduel-sports-network-florida",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-florida-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Great Lakes SD",
    "id": "fanduel-sports-network-great-lakes",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-great-lakes-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Great Lakes HD",
    "id": "fanduel-sports-network-great-lakes",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-great-lakes-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network North SD",
    "id": "fanduel-sports-network-north",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-north-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network North HD",
    "id": "fanduel-sports-network-north",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-north-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Ohio Cleveland SD",
    "id": "fanduel-sports-network-ohio-cleveland",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-ohio-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Ohio Cleveland HD",
    "id": "fanduel-sports-network-ohio-cleveland",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-ohio-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Oklahoma SD",
    "id": "fanduel-sports-network-oklahoma",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-oklahoma-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Oklahoma HD",
    "id": "fanduel-sports-network-oklahoma",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-oklahoma-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network San Diego SD",
    "id": "fanduel-sports-network-san-diego",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-san-diego-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network San Diego HD",
    "id": "fanduel-sports-network-san-diego",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-san-diego-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Socal SD",
    "id": "fanduel-sports-network-socal",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-socal-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Socal HD",
    "id": "fanduel-sports-network-socal",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-socal-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network South Carolinas SD",
    "id": "fanduel-sports-network-south-carolinas",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/FanDuel_Sports_Network_South_logo.svg/1200px-FanDuel_Sports_Network_South_logo.svg.png"
  },
  {
    "name": "Fanduel Sports Network South Carolinas HD",
    "id": "fanduel-sports-network-south-carolinas",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/FanDuel_Sports_Network_South_logo.svg/1200px-FanDuel_Sports_Network_South_logo.svg.png"
  },
  {
    "name": "Fanduel Sports Network South Tennessee SD",
    "id": "fanduel-sports-network-south-tennessee-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-south-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network South Tennessee HD",
    "id": "fanduel-sports-network-south-tennessee-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-south-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network West SD",
    "id": "fanduel-sports-network-west",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-west-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network West HD",
    "id": "fanduel-sports-network-west",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-west-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Wisconsin SD",
    "id": "fanduel-sports-network-wisconsin",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-wisconsin-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Network Wisconsin HD",
    "id": "fanduel-sports-network-wisconsin",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-wisconsin-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast Georgia SD",
    "id": "fanduel-sports-southeast-georgia",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-southeast-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast Georgia HD",
    "id": "fanduel-sports-southeast-georgia",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-southeast-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast North Carolina SD",
    "id": "fanduel-sports-southeast-north-carolina",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-north-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast North Carolina HD",
    "id": "fanduel-sports-southeast-north-carolina",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-north-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast South Carolina SD",
    "id": "fanduel-sports-southeast-south-carolina",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-south-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast South Carolina HD",
    "id": "fanduel-sports-southeast-south-carolina",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-south-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast Tennessee Nashville SD",
    "id": "fanduel-sports-southeast-tennessee-nashville",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-southeast-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Southeast Tennessee Nashville HD",
    "id": "fanduel-sports-southeast-tennessee-nashville",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-southeast-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Sun SD",
    "id": "bally-sports-sun",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-sun-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Sun HD",
    "id": "bally-sports-sun",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-sun-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Tennessee East SD",
    "id": "fanduel-sports-tennessee-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-southeast-us.png?raw=true"
  },
  {
    "name": "Fanduel Sports Tennessee East HD",
    "id": "fanduel-sports-tennessee-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/bally-sports-southeast-us.png?raw=true"
  },
  {
    "name": "Food Network USA Eastern Feed SD",
    "id": "food-network-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/food-network-us.png?raw=true"
  },
  {
    "name": "Food Network USA Eastern Feed HD",
    "id": "food-network-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/food-network-us.png?raw=true"
  },
  {
    "name": "FOX (KTTV) Los Angeles SD",
    "id": "fox-kttv-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-us.png?raw=true"
  },
  {
    "name": "FOX (KTTV) Los Angeles HD",
    "id": "fox-kttv-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-us.png?raw=true"
  },
  {
    "name": "FOX (WNYW) New York ",
    "id": "fox-wnyw-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-us.png?raw=true"
  },
  {
    "name": "FOX (WNYW) New York",
    "id": "fox-wnyw-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-us.png?raw=true"
  },
  {
    "name": "Fox Business SD",
    "id": "fox-business",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-business-us.png?raw=true"
  },
  {
    "name": "Fox Business HD",
    "id": "fox-business",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-business-us.png?raw=true"
  },
  {
    "name": "Fox News SD",
    "id": "fox-news",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-news-us.png?raw=true"
  },
  {
    "name": "Fox News HD",
    "id": "fox-news",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-news-us.png?raw=true"
  },
  {
    "name": "Fox Sports 1 SD",
    "id": "fox-sports-1",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-sports-1-us.png?raw=true"
  },
  {
    "name": "Fox Sports 1 HD",
    "id": "fox-sports-1",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-sports-1-us.png?raw=true"
  },
  {
    "name": "Fox Sports 2 SD",
    "id": "fox-sports-2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-sports-2-us.png?raw=true"
  },
  {
    "name": "Fox Sports 2 HD",
    "id": "fox-sports-2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fox-sports-2-us.png?raw=true"
  },
  {
    "name": "Freeform East Feed SD",
    "id": "freeform-east-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/freeform-us.png?raw=true"
  },
  {
    "name": "Freeform East Feed HD",
    "id": "freeform-east-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/freeform-us.png?raw=true"
  },
  {
    "name": "FUSE TV Eastern feed SD",
    "id": "fuse-tv-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fuse-us.png?raw=true"
  },
  {
    "name": "FUSE TV Eastern feed HD",
    "id": "fuse-tv-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fuse-us.png?raw=true"
  },
  {
    "name": "FX Movie Channel SD",
    "id": "fx-movie-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fxm-movie-channel-us.png?raw=true"
  },
  {
    "name": "FX Movie Channel HD",
    "id": "fx-movie-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fxm-movie-channel-us.png?raw=true"
  },
  {
    "name": "FX Networks East Coast SD",
    "id": "fx-networks-east-coast",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fx-us.png?raw=true"
  },
  {
    "name": "FX Networks East Coast HD",
    "id": "fx-networks-east-coast",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fx-us.png?raw=true"
  },
  {
    "name": "FXX USA Eastern SD",
    "id": "fxx-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fxx-us.png?raw=true"
  },
  {
    "name": "FXX USA Eastern HD",
    "id": "fxx-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fxx-us.png?raw=true"
  },
  {
    "name": "FYI USA Eastern SD",
    "id": "fyi-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fyi-us.png?raw=true"
  },
  {
    "name": "FYI USA Eastern HD",
    "id": "fyi-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/fyi-us.png?raw=true"
  },
  {
    "name": "Game Show Network East SD",
    "id": "game-show-network-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/game-show-network-us.png?raw=true"
  },
  {
    "name": "Game Show Network East HD",
    "id": "game-show-network-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/game-show-network-us.png?raw=true"
  },
  {
    "name": "Golf Channel USA SD",
    "id": "golf-channel-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbc-golf-us.png?raw=true"
  },
  {
    "name": "Golf Channel USA HD",
    "id": "golf-channel-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbc-golf-us.png?raw=true"
  },
  {
    "name": "Hallmark Eastern Feed SD",
    "id": "hallmark-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hallmark-channel-us.png?raw=true"
  },
  {
    "name": "Hallmark Eastern Feed HD",
    "id": "hallmark-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hallmark-channel-us.png?raw=true"
  },
  {
    "name": "Hallmark Family HD SD",
    "id": "hallmark-family-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hallmark-family-us.png?raw=true"
  },
  {
    "name": "Hallmark Family HD HD",
    "id": "hallmark-family-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hallmark-family-us.png?raw=true"
  },
  {
    "name": "Hallmark Mystery Eastern HD SD",
    "id": "hallmark-mystery-eastern-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hallmark-mystery-us.png?raw=true"
  },
  {
    "name": "Hallmark Mystery Eastern HD HD",
    "id": "hallmark-mystery-eastern-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hallmark-mystery-us.png?raw=true"
  },
  {
    "name": "HBO Eastern Feed SD",
    "id": "hbo-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-us.png?raw=true"
  },
  {
    "name": "HBO Eastern Feed HD",
    "id": "hbo-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-us.png?raw=true"
  },
  {
    "name": "HBO 2 Eastern Feed SD",
    "id": "hbo-2-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-2-us.png?raw=true"
  },
  {
    "name": "HBO 2 Eastern Feed HD",
    "id": "hbo-2-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-2-us.png?raw=true"
  },
  {
    "name": "HBO Comedy HD East SD",
    "id": "hbo-comedy-hd-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-comedy-us.png?raw=true"
  },
  {
    "name": "HBO Comedy HD East HD",
    "id": "hbo-comedy-hd-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-comedy-us.png?raw=true"
  },
  {
    "name": "HBO Family Eastern Feed SD",
    "id": "hbo-family-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-family-us.png?raw=true"
  },
  {
    "name": "HBO Family Eastern Feed HD",
    "id": "hbo-family-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-family-us.png?raw=true"
  },
  {
    "name": "HBO Signature (HBO 3) Eastern SD",
    "id": "hbo-signature-hbo-3-eastern",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/5/5f/HBO_3_logo.png"
  },
  {
    "name": "HBO Signature (HBO 3) Eastern HD",
    "id": "hbo-signature-hbo-3-eastern",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/5/5f/HBO_3_logo.png"
  },
  {
    "name": "HBO Zone HD East SD",
    "id": "hbo-zone-hd-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-zone-us.png?raw=true"
  },
  {
    "name": "HBO Zone HD East HD",
    "id": "hbo-zone-hd-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hbo-zone-us.png?raw=true"
  },
  {
    "name": "HGTV USA Eastern Feed SD",
    "id": "hgtv-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hgtv-us.png?raw=true"
  },
  {
    "name": "HGTV USA Eastern Feed HD",
    "id": "hgtv-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hgtv-us.png?raw=true"
  },
  {
    "name": "History Channel US Eastern Feed SD",
    "id": "history-channel-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/history-channel-us.png?raw=true"
  },
  {
    "name": "History Channel US Eastern Feed HD",
    "id": "history-channel-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/history-channel-us.png?raw=true"
  },
  {
    "name": "HLN SD",
    "id": "hln",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hln-us.png?raw=true"
  },
  {
    "name": "HLN HD",
    "id": "hln",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/hln-us.png?raw=true"
  },
  {
    "name": "Independent Film Channel US SD",
    "id": "independent-film-channel-us",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/ifc-us.png?raw=true"
  },
  {
    "name": "Independent Film Channel US HD",
    "id": "independent-film-channel-us",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/ifc-us.png?raw=true"
  },
  {
    "name": "Investigation Discovery USA Eastern SD",
    "id": "investigation-discovery-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/investigation-discovery-us.png?raw=true"
  },
  {
    "name": "Investigation Discovery USA Eastern HD",
    "id": "investigation-discovery-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/investigation-discovery-us.png?raw=true"
  },
  {
    "name": "ION Eastern Feed SD",
    "id": "ion-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/ion-television-us.png?raw=true"
  },
  {
    "name": "ION Eastern Feed HD",
    "id": "ion-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/ion-television-us.png?raw=true"
  },
  {
    "name": "Lifetime Movies East SD",
    "id": "lifetime-movies-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/lifetime-movies-us.png?raw=true"
  },
  {
    "name": "Lifetime Movies East HD",
    "id": "lifetime-movies-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/lifetime-movies-us.png?raw=true"
  },
  {
    "name": "Lifetime Network US Eastern Feed SD",
    "id": "lifetime-network-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/lifetime-movie-network-us.png?raw=true"
  },
  {
    "name": "Lifetime Network US Eastern Feed HD",
    "id": "lifetime-network-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/lifetime-movie-network-us.png?raw=true"
  },
  {
    "name": "LOGO East SD",
    "id": "logo-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/logo-us.png?raw=true"
  },
  {
    "name": "LOGO East HD",
    "id": "logo-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/logo-us.png?raw=true"
  },
  {
    "name": "Marquee Sports Network SD",
    "id": "marquee-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/marquee-sports-network-us.png?raw=true"
  },
  {
    "name": "Marquee Sports Network HD",
    "id": "marquee-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/marquee-sports-network-us.png?raw=true"
  },
  {
    "name": "MeTV Toons (WJLP2) New Jersey SD",
    "id": "metv-toons-wjlp2-new-jersey",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/me-tv-toons-us.png?raw=true"
  },
  {
    "name": "MeTV Toons (WJLP2) New Jersey HD",
    "id": "metv-toons-wjlp2-new-jersey",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/me-tv-toons-us.png?raw=true"
  },
  {
    "name": "MeTV Wjlp New Jerseynew York SD",
    "id": "metv-wjlp-new-jerseynew-york",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/me-tv-toons-us.png?raw=true"
  },
  {
    "name": "MeTV Wjlp New Jerseynew York HD",
    "id": "metv-wjlp-new-jerseynew-york",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/me-tv-toons-us.png?raw=true"
  },
  {
    "name": "Midatlantic Sports Network SD",
    "id": "midatlantic-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/masn-us.png?raw=true"
  },
  {
    "name": "Midatlantic Sports Network HD",
    "id": "midatlantic-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/masn-us.png?raw=true"
  },
  {
    "name": "MLB Network SD",
    "id": "mlb-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/mlb-network-us.png?raw=true"
  },
  {
    "name": "MLB Network HD",
    "id": "mlb-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/mlb-network-us.png?raw=true"
  },
  {
    "name": "Monumental Sports Network SD",
    "id": "monumental-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/monumental-sports-network-us.png?raw=true"
  },
  {
    "name": "Monumental Sports Network HD",
    "id": "monumental-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/monumental-sports-network-us.png?raw=true"
  },
  {
    "name": "MoreMax Eastern SD",
    "id": "moremax-eastern",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/MoreMax_Logo.svg"
  },
  {
    "name": "MoreMax Eastern HD",
    "id": "moremax-eastern",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c5/MoreMax_Logo.svg"
  },
  {
    "name": "Motor Trend HD SD",
    "id": "motor-trend-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/motor-trend-us.png?raw=true"
  },
  {
    "name": "Motor Trend HD HD",
    "id": "motor-trend-hd",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/motor-trend-us.png?raw=true"
  },
  {
    "name": "MovieMax (Max 6) East SD",
    "id": "moviemax-max-6-east",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/5/52/MovieMax_Logo.svg"
  },
  {
    "name": "MovieMax (Max 6) East HD",
    "id": "moviemax-max-6-east",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/5/52/MovieMax_Logo.svg"
  },
  {
    "name": "MSG Madison Square Gardens SD",
    "id": "msg-madison-square-gardens",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/msg-us.png?raw=true"
  },
  {
    "name": "MSG Madison Square Gardens HD",
    "id": "msg-madison-square-gardens",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/msg-us.png?raw=true"
  },
  {
    "name": "MSG Plus SD",
    "id": "msg-plus",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/msg-plus-us.png?raw=true"
  },
  {
    "name": "MSG Plus HD",
    "id": "msg-plus",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/msg-plus-us.png?raw=true"
  },
  {
    "name": "MSNBC USA SD",
    "id": "msnbc-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/msnbc-hz-us.png?raw=true"
  },
  {
    "name": "MSNBC USA HD",
    "id": "msnbc-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/msnbc-hz-us.png?raw=true"
  },
  {
    "name": "MTV 2 East SD",
    "id": "mtv-2-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/mtv-2-us.png?raw=true"
  },
  {
    "name": "MTV 2 East HD",
    "id": "mtv-2-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/mtv-2-us.png?raw=true"
  },
  {
    "name": "MTV USA Eastern Feed SD",
    "id": "mtv-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/mtv-us.png?raw=true"
  },
  {
    "name": "MTV USA Eastern Feed HD",
    "id": "mtv-usa-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/mtv-us.png?raw=true"
  },
  {
    "name": "National Geographic US Eastern SD",
    "id": "national-geographic-us-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/national-geographic-us.png?raw=true"
  },
  {
    "name": "National Geographic US Eastern HD",
    "id": "national-geographic-us-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/national-geographic-us.png?raw=true"
  },
  {
    "name": "National Geographic Wild SD",
    "id": "national-geographic-wild",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nat-geo-wild-us.png?raw=true"
  },
  {
    "name": "National Geographic Wild HD",
    "id": "national-geographic-wild",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nat-geo-wild-us.png?raw=true"
  },
  {
    "name": "NBA TV USA SD",
    "id": "nba-tv-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nba-tv-icon-us.png?raw=true"
  },
  {
    "name": "NBA TV USA HD",
    "id": "nba-tv-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nba-tv-icon-us.png?raw=true"
  },
  {
    "name": "NBC (KNBC) Los Angeles SD",
    "id": "nbc-knbc-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbc-logo-alt-us.png?raw=true"
  },
  {
    "name": "NBC (KNBC) Los Angeles HD",
    "id": "nbc-knbc-los-angeles-ca",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbc-logo-alt-us.png?raw=true"
  },
  {
    "name": "NBC (WNBC) New York",
    "id": "nbc-wnbc-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbc-logo-alt-us.png?raw=true"
  },
  {
    "name": "NBC (WNBC) New York",
    "id": "nbc-wnbc-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbc-logo-alt-us.png?raw=true"
  },
  {
    "name": "NBC Sports Bay Area SD",
    "id": "nbc-sports-bay-area",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-bay-area-us.png?raw=true"
  },
  {
    "name": "NBC Sports Bay Area HD",
    "id": "nbc-sports-bay-area",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-bay-area-us.png?raw=true"
  },
  {
    "name": "NBC Sports Boston SD",
    "id": "nbc-sports-boston",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-boston-us.png?raw=true"
  },
  {
    "name": "NBC Sports Boston HD",
    "id": "nbc-sports-boston",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-boston-us.png?raw=true"
  },
  {
    "name": "NBC Sports California SD",
    "id": "nbc-sports-california",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-california-us.png?raw=true"
  },
  {
    "name": "NBC Sports California HD",
    "id": "nbc-sports-california",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-california-us.png?raw=true"
  },
  {
    "name": "NBC Sports Philadelphia SD",
    "id": "nbc-sports-philadelphia",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-philadelphia-us.png?raw=true"
  },
  {
    "name": "NBC Sports Philadelphia HD",
    "id": "nbc-sports-philadelphia",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nbcsn-philadelphia-us.png?raw=true"
  },
  {
    "name": "New England Sports Network SD",
    "id": "new-england-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nesn-us.png?raw=true"
  },
  {
    "name": "New England Sports Network HD",
    "id": "new-england-sports-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nesn-us.png?raw=true"
  },
  {
    "name": "NewsMax TV SD",
    "id": "newsmax-tv",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/newsmax-tv-us.png?raw=true"
  },
  {
    "name": "NewsMax TV HD",
    "id": "newsmax-tv",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/newsmax-tv-us.png?raw=true"
  },
  {
    "name": "NFL Network SD",
    "id": "nfl-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-network-us.png?raw=true"
  },
  {
    "name": "NFL Network HD",
    "id": "nfl-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-network-us.png?raw=true"
  },
  {
    "name": "NFL RedZone SD",
    "id": "nfl-redzone",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-red-zone-us.png?raw=true"
  },
  {
    "name": "NFL RedZone HD",
    "id": "nfl-redzone",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nfl-red-zone-us.png?raw=true"
  },
  {
    "name": "NHL Network USA SD",
    "id": "nhl-network-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nhl-network-us.png?raw=true"
  },
  {
    "name": "NHL Network USA HD",
    "id": "nhl-network-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nhl-network-us.png?raw=true"
  },
  {
    "name": "Nick Jr. East SD",
    "id": "nick-jr-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nick-jr-us.png?raw=true"
  },
  {
    "name": "Nick Jr. East HD",
    "id": "nick-jr-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nick-jr-us.png?raw=true"
  },
  {
    "name": "Nickelodeon USA East Feed SD",
    "id": "nickelodeon-usa-east-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nick-us.png?raw=true"
  },
  {
    "name": "Nickelodeon USA East Feed HD",
    "id": "nickelodeon-usa-east-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nick-us.png?raw=true"
  },
  {
    "name": "Nicktoons East SD",
    "id": "nicktoons-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nick-toons-us.png?raw=true"
  },
  {
    "name": "Nicktoons East HD",
    "id": "nicktoons-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/nick-toons-us.png?raw=true"
  },
  {
    "name": "Oprah Winfrey Network USA Eastern SD",
    "id": "oprah-winfrey-network-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/oprah-winfrey-network-us.png?raw=true"
  },
  {
    "name": "Oprah Winfrey Network USA Eastern HD",
    "id": "oprah-winfrey-network-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/oprah-winfrey-network-us.png?raw=true"
  },
  {
    "name": "Outdoor Channel US SD",
    "id": "outdoor-channel-us",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/outdoor-channel-us.png?raw=true"
  },
  {
    "name": "Outdoor Channel US HD",
    "id": "outdoor-channel-us",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/outdoor-channel-us.png?raw=true"
  },
  {
    "name": "Oxygen Eastern Feed SD",
    "id": "oxygen-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/oxygen-us.png?raw=true"
  },
  {
    "name": "Oxygen Eastern Feed HD",
    "id": "oxygen-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/oxygen-us.png?raw=true"
  },
  {
    "name": "PBS (WNET) New York",
    "id": "pbs-wnet-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/pbs-us.png?raw=true"
  },
  {
    "name": "PBS (WNET) New York",
    "id": "pbs-wnet-new-york-ny",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/pbs-us.png?raw=true"
  },
  {
    "name": "ReelzChannel SD",
    "id": "reelzchannel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/reelz-us.png?raw=true"
  },
  {
    "name": "ReelzChannel HD",
    "id": "reelzchannel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/reelz-us.png?raw=true"
  },
  {
    "name": "Science SD",
    "id": "science",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-science-us.png?raw=true"
  },
  {
    "name": "Science HD",
    "id": "science",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/discovery-science-us.png?raw=true"
  },
  {
    "name": "SEC Network SD",
    "id": "sec-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-sec-us.png?raw=true"
  },
  {
    "name": "SEC Network HD",
    "id": "sec-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/espn-sec-us.png?raw=true"
  },
  {
    "name": "Showtime Eastern Feed SD",
    "id": "paramount-with-showtime-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/showtime-us.png?raw=true"
  },
  {
    "name": "Showtime Eastern Feed HD",
    "id": "paramount-with-showtime-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/showtime-us.png?raw=true"
  },
  {
    "name": "Showtime 2 Eastern SD",
    "id": "showtime-2-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/showtime-2-us.png?raw=true"
  },
  {
    "name": "Showtime 2 Eastern HD",
    "id": "showtime-2-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/showtime-2-us.png?raw=true"
  },
  {
    "name": "SNY Sportsnet New York Comcast SD",
    "id": "sny-sportsnet-new-york-comcast",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/sny-us.png?raw=true"
  },
  {
    "name": "SNY Sportsnet New York Comcast HD",
    "id": "sny-sportsnet-new-york-comcast",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/sny-us.png?raw=true"
  },
  {
    "name": "Space City Home Network SD",
    "id": "space-city-home-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/space-city-home-network-us.png?raw=true"
  },
  {
    "name": "Space City Home Network HD",
    "id": "space-city-home-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/space-city-home-network-us.png?raw=true"
  },
  {
    "name": "Spectrum SportsNet LA SD",
    "id": "spectrum-sportsnet-la",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/spectrum-sportsnet-la-us.png?raw=true"
  },
  {
    "name": "Spectrum SportsNet LA HD",
    "id": "spectrum-sportsnet-la",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/spectrum-sportsnet-la-us.png?raw=true"
  },
  {
    "name": "Spectrum Sportsnet Lakers SD",
    "id": "spectrum-sportsnet",
    "logo": "https://cdn.nba.com/manage/2024/10/lalspectrum-1.png"
  },
  {
    "name": "Spectrum Sportsnet Lakers HD",
    "id": "spectrum-sportsnet",
    "logo": "https://cdn.nba.com/manage/2024/10/lalspectrum-1.png"
  },
  {
    "name": "Sportsnet (East) SD",
    "id": "sportsnet-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-sne-ca.png?raw=true"
  },
  {
    "name": "Sportsnet (East) HD",
    "id": "sportsnet-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-sne-ca.png?raw=true"
  },
  {
    "name": "Sportsnet 360 SD",
    "id": "sportsnet-360",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-360-ca.png?raw=true"
  },
  {
    "name": "Sportsnet 360 HD",
    "id": "sportsnet-360",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-360-ca.png?raw=true"
  },
  {
    "name": "Sportsnet One SD",
    "id": "sportsnet-one",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-one-ca.png?raw=true"
  },
  {
    "name": "Sportsnet One HD",
    "id": "sportsnet-one",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-one-ca.png?raw=true"
  },
  {
    "name": "Sportsnet Ontario SD",
    "id": "sportsnet-ontario",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-ontario-ca.png?raw=true"
  },
  {
    "name": "Sportsnet Ontario HD",
    "id": "sportsnet-ontario",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-ontario-ca.png?raw=true"
  },
  {
    "name": "Sportsnet Pacific SD",
    "id": "sportsnet-pacific",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-pacific-ca.png?raw=true"
  },
  {
    "name": "Sportsnet Pacific HD",
    "id": "sportsnet-pacific",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-pacific-ca.png?raw=true"
  },
  {
    "name": "Sportsnet Pittsburgh SD",
    "id": "sportsnet-pittsburgh",
    "logo": "https://static.wikia.nocookie.net/logopedia/images/d/d8/SportsNet_Pittsburgh_2023_stacked.svg/revision/latest?cb=20240728201335"
  },
  {
    "name": "Sportsnet Pittsburgh HD",
    "id": "sportsnet-pittsburgh",
    "logo": "https://static.wikia.nocookie.net/logopedia/images/d/d8/SportsNet_Pittsburgh_2023_stacked.svg/revision/latest?cb=20240728201335"
  },
  {
    "name": "Sportsnet West SD",
    "id": "sportsnet-west",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-snw-ca.png?raw=true"
  },
  {
    "name": "Sportsnet West HD",
    "id": "sportsnet-west",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/sportsnet-snw-ca.png?raw=true"
  },
  {
    "name": "Starz Eastern SD",
    "id": "starz-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/starz-us.png?raw=true"
  },
  {
    "name": "Starz Eastern HD",
    "id": "starz-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/starz-us.png?raw=true"
  },
  {
    "name": "SundanceTV USA East SD",
    "id": "sundancetv-usa-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/sundance-tv-us.png?raw=true"
  },
  {
    "name": "SundanceTV USA East HD",
    "id": "sundancetv-usa-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/sundance-tv-us.png?raw=true"
  },
  {
    "name": "Syfy Eastern Feed SD",
    "id": "syfy-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/syfy-hz-us.png?raw=true"
  },
  {
    "name": "Syfy Eastern Feed HD",
    "id": "syfy-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/syfy-hz-us.png?raw=true"
  },
  {
    "name": "TBS East SD",
    "id": "tbs-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tbs-us.png?raw=true"
  },
  {
    "name": "TBS East HD",
    "id": "tbs-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tbs-us.png?raw=true"
  },
  {
    "name": "TeenNick Eastern SD",
    "id": "teennick-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/teen-nick-us.png?raw=true"
  },
  {
    "name": "TeenNick Eastern HD",
    "id": "teennick-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/teen-nick-us.png?raw=true"
  },
  {
    "name": "Telemundo Eastern Feed SD",
    "id": "telemundo-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/telemundo-us.png?raw=true"
  },
  {
    "name": "Telemundo Eastern Feed HD",
    "id": "telemundo-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/telemundo-us.png?raw=true"
  },
  {
    "name": "The Cooking Channel SD",
    "id": "the-cooking-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cooking-channel-us.png?raw=true"
  },
  {
    "name": "The Cooking Channel HD",
    "id": "the-cooking-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cooking-channel-us.png?raw=true"
  },
  {
    "name": "The Tennis Channel SD",
    "id": "the-tennis-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tennis-channel-hz-us.png?raw=true"
  },
  {
    "name": "The Tennis Channel HD",
    "id": "the-tennis-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tennis-channel-hz-us.png?raw=true"
  },
  {
    "name": "The Weather Channel SD",
    "id": "the-weather-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/weather-channel-us.png?raw=true"
  },
  {
    "name": "The Weather Channel HD",
    "id": "the-weather-channel",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/weather-channel-us.png?raw=true"
  },
  {
    "name": "TLC USA Eastern SD",
    "id": "tlc-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tlc-us.png?raw=true"
  },
  {
    "name": "TLC USA Eastern HD",
    "id": "tlc-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tlc-us.png?raw=true"
  },
  {
    "name": "TMC (US) Eastern Feed SD",
    "id": "tmc-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/the-movie-channel-us.png?raw=true"
  },
  {
    "name": "TMC (US) Eastern Feed HD",
    "id": "tmc-us-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/the-movie-channel-us.png?raw=true"
  },
  {
    "name": "TNT Eastern Feed SD",
    "id": "tnt-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tnt-us.png?raw=true"
  },
  {
    "name": "TNT Eastern Feed HD",
    "id": "tnt-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tnt-us.png?raw=true"
  },
  {
    "name": "Travel US East SD",
    "id": "travel-us-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/travel-channel-us.png?raw=true"
  },
  {
    "name": "Travel US East HD",
    "id": "travel-us-east",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/travel-channel-us.png?raw=true"
  },
  {
    "name": "truTV USA Eastern SD",
    "id": "trutv-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tru-tv-us.png?raw=true"
  },
  {
    "name": "truTV USA Eastern HD",
    "id": "trutv-usa-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tru-tv-us.png?raw=true"
  },
  {
    "name": "TSN1 SD",
    "id": "tsn1",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-1-ca.png?raw=true"
  },
  {
    "name": "TSN1 HD",
    "id": "tsn1",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-1-ca.png?raw=true"
  },
  {
    "name": "TSN2 SD",
    "id": "tsn2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-2-ca.png?raw=true"
  },
  {
    "name": "TSN2 HD",
    "id": "tsn2",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-2-ca.png?raw=true"
  },
  {
    "name": "TSN3 SD",
    "id": "tsn3",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-3-ca.png?raw=true"
  },
  {
    "name": "TSN3 HD",
    "id": "tsn3",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-3-ca.png?raw=true"
  },
  {
    "name": "TSN4 SD",
    "id": "tsn4",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-4-ca.png?raw=true"
  },
  {
    "name": "TSN4 HD",
    "id": "tsn4",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-4-ca.png?raw=true"
  },
  {
    "name": "TSN5 SD",
    "id": "tsn5",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-5-ca.png?raw=true"
  },
  {
    "name": "TSN5 HD",
    "id": "tsn5",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/tsn-5-ca.png?raw=true"
  },
  {
    "name": "Turner Classic Movies USA SD",
    "id": "turner-classic-movies-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tcm-us.png?raw=true"
  },
  {
    "name": "Turner Classic Movies USA HD",
    "id": "turner-classic-movies-usa",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tcm-us.png?raw=true"
  },
  {
    "name": "TV Land Eastern SD",
    "id": "tv-land-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tv-land-us.png?raw=true"
  },
  {
    "name": "TV Land Eastern HD",
    "id": "tv-land-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/tv-land-us.png?raw=true"
  },
  {
    "name": "TV One SD",
    "id": "tv-one",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/0/0c/TV_One_US_2012.png"
  },
  {
    "name": "TV One HD",
    "id": "tv-one",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/0/0c/TV_One_US_2012.png"
  },
  {
    "name": "Universal Kids SD",
    "id": "universal-kids",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/universal-kids-us.png?raw=true"
  },
  {
    "name": "Universal Kids HD",
    "id": "universal-kids",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/universal-kids-us.png?raw=true"
  },
  {
    "name": "Univision Eastern Feed SD",
    "id": "univision-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/univision-us.png?raw=true"
  },
  {
    "name": "Univision Eastern Feed HD",
    "id": "univision-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/univision-us.png?raw=true"
  },
  {
    "name": "USA Network East Feed SD",
    "id": "usa-network-east-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/usa-us.png?raw=true"
  },
  {
    "name": "USA Network East Feed HD",
    "id": "usa-network-east-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/usa-us.png?raw=true"
  },
  {
    "name": "VH1 Eastern Feed SD",
    "id": "vh1-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/vh1-us.png?raw=true"
  },
  {
    "name": "VH1 Eastern Feed HD",
    "id": "vh1-eastern-feed",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/vh1-us.png?raw=true"
  },
  {
    "name": "VICE SD",
    "id": "vice",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/vice-us.png?raw=true"
  },
  {
    "name": "VICE HD",
    "id": "vice",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/vice-us.png?raw=true"
  },
  {
    "name": "WE (Women's Entertainment) Eastern SD",
    "id": "we-womens-entertainment-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/we-tv-us.png?raw=true"
  },
  {
    "name": "WE (Women's Entertainment) Eastern HD",
    "id": "we-womens-entertainment-eastern",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/we-tv-us.png?raw=true"
  },
  {
    "name": "WPIX New York (SUPERSTATION) SD",
    "id": "wpix-new-york-superstation",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/cw-ca.png?raw=true"
  },
  {
    "name": "WPIX New York (SUPERSTATION) HD",
    "id": "wpix-new-york-superstation",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/canada/cw-ca.png?raw=true"
  },
  {
    "name": "Yes Network SD",
    "id": "yes-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/yes-network-us.png?raw=true"
  },
  {
    "name": "Yes Network HD",
    "id": "yes-network",
    "logo": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/yes-network-us.png?raw=true"
  }
]

def extract_real_m3u8(url: str):
    if "ping.gif" in url and "mu=" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        mu = qs.get("mu", [None])[0]
        if mu:
            return urllib.parse.unquote(mu)
    if ".m3u8" in url:
        return url
    return None

def build_extinf(title, metadata, quality, stream_url, is_live_event=False):
    name = f"{title} {quality}"
    # Force group-title="TheTVApp" for scraped channels, keep original for live events
    group_title = "" if is_live_event else ' group-title="TheTVApp"'
    return [
        f'#EXTINF:-1 tvg-name="{metadata.get("tvg-name", name)}" tvg-id="{metadata.get("tvg-id", "")}" tvg-logo="{metadata.get("tvg-logo", "")}"{group_title},{name}',
        stream_url
    ]

async def scrape_thetvapp():
    playlist = ["#EXTM3U"]
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Loading channel list from {CHANNEL_LIST_URL}...")
        await page.goto(CHANNEL_LIST_URL)
        links = await page.locator("ol.list-group a").all()

        for link in links:
            raw_title = (await link.inner_text()).strip()
            # Get main title (before colon), stripped
            title = raw_title.split(":")[0].strip()
            href = await link.get_attribute("href")
            if not href:
                continue
            full_url = BASE_URL + href

            print(f"Processing {title} @ {full_url}")

            sd_url = None
            hd_url = None

            # Find metadata by exact case-insensitive match on 'name' key
            metadata = next(
                (m for m in CHANNEL_METADATA if m["name"].strip().lower() == title.lower()),
                {}
            )

            # SD stream page
            sd_page = await context.new_page()
            async def handle_response_sd(response):
                nonlocal sd_url
                real_url = extract_real_m3u8(response.url)
                if real_url and sd_url is None:
                    sd_url = real_url
            sd_page.on("response", handle_response_sd)
            await sd_page.goto(full_url)
            try:
                await sd_page.get_by_text("Load SD Stream", exact=True).click(timeout=5000)
            except Exception:
                print(f"⚠️ No SD Stream button for {title}")
            await asyncio.sleep(5)
            await sd_page.close()

            # HD stream page
            hd_page = await context.new_page()
            async def handle_response_hd(response):
                nonlocal hd_url
                real_url = extract_real_m3u8(response.url)
                if real_url and hd_url is None:
                    hd_url = real_url
            hd_page.on("response", handle_response_hd)
            await hd_page.goto(full_url)
            try:
                await hd_page.get_by_text("Load HD Stream", exact=True).click(timeout=5000)
            except Exception:
                print(f"⚠️ No HD Stream button for {title}")
            await asyncio.sleep(5)
            await hd_page.close()

            if sd_url:
                playlist += build_extinf(title, metadata, "SD", sd_url, is_live_event=False)
                print(f"  ✅ SD stream: {sd_url}")
            else:
                print(f"  ❌ No SD stream for {title}")

            if hd_url:
                playlist += build_extinf(title, metadata, "HD", hd_url, is_live_event=False)
                print(f"  ✅ HD stream: {hd_url}")
            else:
                print(f"  ❌ No HD stream for {title}")

        await browser.close()

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("\n".join(playlist))
    print(f"\n✅ M3U playlist saved to {OUTPUT_M3U}")

# Helper for live events: build EXTINF lines WITHOUT forcing TheTVApp group-title
def build_live_event_extinf(title, metadata, quality, stream_url):
    return build_extinf(title, metadata, quality, stream_url, is_live_event=True)

if __name__ == "__main__":
    asyncio.run(scrape_thetvapp())
