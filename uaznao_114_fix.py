import base64
import re
import json
import os
import sys
import time
import requests
from datetime import datetime

# ============================================================
# COLORI ANSI
# ============================================================
class C:
    RESET='\033[0m'; BOLD='\033[1m'; DIM='\033[2m'
    RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
    BLUE='\033[94m'; CYAN='\033[96m'; WHITE='\033[97m'

def clr(): os.system('cls' if os.name=='nt' else 'clear')
def ts(): return datetime.now().strftime('%H:%M:%S')

def log(msg, color=None, bold=False):
    body = (C.BOLD if bold else '') + ((color or '') + msg) + C.RESET
    print(f"{C.DIM}[{ts()}]{C.RESET} {body}", flush=True)

def banner():
    print(f"{C.CYAN}{'='*50}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}📺 Uaznao Scraper - Canali Aggiornati{C.RESET}")
    print(f"{C.CYAN}{'='*50}{C.RESET}")

# ============================================================
# CONFIGURAZIONE
# ============================================================
CORS_PROXY = 'https://proxyshaka.erciciola.workers.dev/?url='
BASE_URL   = 'https://uaznao.com/premium/canalitv/'
EPG_URL    = 'https://raw.githubusercontent.com/qwertyuiop8899/TV/refs/heads/main/epg.xml'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# ============================================================
# CREDENZIALI GOOGLE DRIVE
# ============================================================
CLIENT_ID     = "360991432021-p5qnc2i8jg8vcnv12o33n74cnjl4bk5q.apps.googleusercontent.com"
CLIENT_SECRET = "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"
DRIVE_FILE_ID = "1w6LgRLFOmEYD88fXYlwwhzbBFZ210JG_"
REFRESH_TOKEN = "1//04SFIkmoK5XT4CgYIARAAGAQSNwF-L9IrfgX8z4LgUKT_jsT1BSaCVZ2DO8k2AqpaLcYMZ_MqQvg5SRj6cSmWE0uG3AtU1Egv1kA"

ACCESS_TOKEN = ""

# ============================================================
# ORDINE GRUPPI
# ============================================================
GROUP_ORDER = [
    "Rai","Mediaset","RSI","Sky Cinema","Sky Sport","Serie B",
    "DAZN CH","CBS Sport","GOLD BET LIVE","FOX SPORT","Premier Sport","Sport cz",
    "ELEVEN SPORT","COMO TV","BluSport","Intrattenimento","Hardcore"
]

# ============================================================
# MAPPA CANALI
# ============================================================
CHANNEL_MAP = {
    # ---- Rai ----
    "rai1": {"name":"Rai 1","group":"Rai","directUrl":"https://raiuno3-live.akamaized.net/hls/live/2017910/raiuno3/raiuno3/playlist.m3u8"},
    "rai2": {"name":"Rai 2","group":"Rai","directUrl":"https://raidue3-live.akamaized.net/hls/live/2017983/raidue3/raidue3/playlist.m3u8"},
    "rai3": {"name":"Rai 3","group":"Rai","directUrl":"https://raitre3-live.akamaized.net/hls/live/2018002/raitre3/raitre3/playlist.m3u8"},
    # ---- Mediaset ----
    "rete4":          {"name":"Rete 4","group":"Mediaset","directUrl":"https://live03-col.msf.cdn.mediaset.net/live/ch-r4/r4-clr.isml/manifest.mpd"},
    "canale5":        {"name":"Canale 5","group":"Mediaset","directUrl":"https://live03-col.msf.cdn.mediaset.net/live/ch-c5/c5-clr.isml/manifest.mpd"},
    "italia1":        {"name":"Italia 1","group":"Mediaset","directUrl":"https://live03-col.msf.cdn.mediaset.net/live/ch-i1/i1-clr.isml/manifest.mpd"},
    "grandefratello": {"name":"Grande Fratello","group":"Mediaset","directUrl":"https://live02-col.msf.cdn.mediaset.net/live/ch-b7/b7-clr.isml/index.m3u8"},
    # ---- RSI ----
    "rsi1": {"name":"RSI La 1 HD","group":"RSI",
             "directUrl":"https://wp3-s-anp31323132-live-ch-prod.prod.cdn.dmdsdp.com/live/disk1/SV09042/stb-dash-fhd-avc/SV09042.mpd",
             "clearKeys":{"09af5f6eb89041ca8f5d164165142e86":"1989cc9c9ce5b2b52cb93edaaefe8420","d268d810d8a73bd8b7d54a6a087581d2":"1aaf297543168c625e05aa9e27344471"}},
    "rsi2": {"name":"RSI La 2 HD","group":"RSI",
             "directUrl":"https://wp2-s-anp31323132-live-ch-prod.prod.cdn.dmdsdp.com/live/disk1/SV09043/stb-dash-fhd-avc/SV09043.mpd",
             "clearKeys":{"117d07fd98cc46ef8e09936d0d37c506":"b9528cb3f23eaad789f0f33bf6b01868","166b2f0d56fb32d9b46d4b1ca1b5bf16":"d78ee5c91eb3b9b6d37414a4f789bc9b"}},
    # ---- Sky Cinema ----
    "cinema1":{"name":"Sky Cinema Uno","group":"Sky Cinema"},
    "cinemastories":{"name":"Sky Cinema Stories","group":"Sky Cinema"},
    "cinemafamily":{"name":"Sky Cinema Family","group":"Sky Cinema"},
    "cinemacomedy":{"name":"Sky Cinema Comedy","group":"Sky Cinema"},
    "cinemaaction":{"name":"Sky Cinema Action","group":"Sky Cinema"},
    "cinemasuspense":{"name":"Sky Cinema Suspense","group":"Sky Cinema"},
    "cinemaromance":{"name":"Sky Cinema Romance","group":"Sky Cinema"},
    "cinemacollection":{"name":"Sky Cinema Collection","group":"Sky Cinema"},
    "cinemadrama":{"name":"Sky Cinema Drama","group":"Sky Cinema"},
    # ---- Sky Sport ----
    "sport24":{"name":"Sky Sport 24","group":"Sky Sport"},
    "sportuno":{"name":"Sky Sport Uno","group":"Sky Sport"},
    "calcio":{"name":"Sky Sport Calcio","group":"Sky Sport"},
    "arena":{"name":"Sky Sport Arena","group":"Sky Sport"},
    "sportmax":{"name":"Sky Sport Max","group":"Sky Sport"},
    "sportmix":{"name":"Sky Sport Mix","group":"Sky Sport"},
    "legend":{"name":"Sky Sport Legend","group":"Sky Sport"},
    "f1":{"name":"Sky Sport F1","group":"Sky Sport"},
    "motogp":{"name":"Sky Sport MotoGP","group":"Sky Sport"},
    "tennis":{"name":"Sky Sport Tennis","group":"Sky Sport"},
    "basket":{"name":"Sky Sport Basket","group":"Sky Sport"},
    "golf":{"name":"Sky Sport Golf","group":"Sky Sport"},
    "amazonlive":{"name":"Amazon Live","group":"Sky Sport"},
    "sport251":{"name":"Sky Sport 251","group":"Sky Sport"},
    "sport252":{"name":"Sky Sport 252","group":"Sky Sport"},
    "sport253":{"name":"Sky Sport 253","group":"Sky Sport"},
    "sport254":{"name":"Sky Sport 254","group":"Sky Sport"},
    "sport255":{"name":"Sky Sport 255","group":"Sky Sport"},
    "sport256":{"name":"Sky Sport 256","group":"Sky Sport"},
    "sport257":{"name":"Sky Sport 257","group":"Sky Sport"},
    "sport258":{"name":"Sky Sport 258","group":"Sky Sport"},
    "sport259":{"name":"Sky Sport 259","group":"Sky Sport"},
    # ---- Intrattenimento ----
    "uno":{"name":"Sky Uno","group":"Intrattenimento"},
    "unoplus":{"name":"Sky Uno Plus","group":"Intrattenimento"},
    "atlantic":{"name":"Sky Atlantic","group":"Intrattenimento"},
    "serie":{"name":"Sky Serie","group":"Intrattenimento"},
    "investigation":{"name":"Sky Investigation","group":"Intrattenimento"},
    "crime":{"name":"Sky Crime","group":"Intrattenimento"},
    "adventure":{"name":"Sky Adventure","group":"Intrattenimento"},
    "nature":{"name":"Sky Nature","group":"Intrattenimento"},
    "arte":{"name":"Sky Arte","group":"Intrattenimento"},
    "documentaries":{"name":"Sky Documentaries","group":"Intrattenimento"},
    "comedycentral":{"name":"Comedy Central","group":"Intrattenimento"},
    "deakids":{"name":"DeAKids","group":"Intrattenimento"},
    "nickjunior":{"name":"Nick Jr","group":"Intrattenimento"},
    "nickeleodeon":{"name":"Nickelodeon","group":"Intrattenimento"},
    "cartoonnetwork":{"name":"Cartoon Network","group":"Intrattenimento"},
    "boomerang":{"name":"Boomerang","group":"Intrattenimento"},
    # ---- DAZN CH ----
    "daznch/player_event.php?event=1":{"name":"DAZN 1","group":"DAZN CH"},
    "daznch/player_event.php?event=2":{"name":"DAZN 2","group":"DAZN CH"},
    "daznch/player_event.php?event=3":{"name":"DAZN 3","group":"DAZN CH"},
    "daznch/player_event.php?event=4":{"name":"DAZN 4","group":"DAZN CH"},
    "daznch/player_event.php?event=5":{"name":"DAZN 5","group":"DAZN CH"},
    "daznch/player_event.php?event=6":{"name":"DAZN 6","group":"DAZN CH"},
    "daznch/player_event.php?event=7":{"name":"DAZN 7","group":"DAZN CH"},
    "daznch/player_event.php?event=8":{"name":"DAZN 8","group":"DAZN CH"},
    "daznch/player_event.php?event=9":{"name":"DAZN 9","group":"DAZN CH"},
    "daznch/player_event.php?event=10":{"name":"DAZN 10","group":"DAZN CH"},
    # ---- BluSport ----
    "blusport/player_event.php?event=1":{"name":"Blu Sport 1","group":"BluSport"},
    "blusport/player_event.php?event=2":{"name":"Blu Sport 2","group":"BluSport"},
    "blusport/player_event.php?event=3":{"name":"Blu Sport 3","group":"BluSport"},
    "blusport/player_event.php?event=4":{"name":"Blu Sport 4","group":"BluSport"},
    "blusport/player_event.php?event=5":{"name":"Blu Sport 5","group":"BluSport"},
    "blusport/player_event.php?event=6":{"name":"Blu Sport 6","group":"BluSport"},
    "blusport/player_event.php?event=7":{"name":"Blu Sport 7","group":"BluSport"},
    "blusport/player_event.php?event=8":{"name":"Blu Sport 8","group":"BluSport"},
    "blusport/player_event.php?event=9":{"name":"Blu Sport 9","group":"BluSport"},
    "blusport/player_event.php?event=10":{"name":"Blu Sport 10","group":"BluSport"},
    # ---- Premier Sport ----
    "premiersports1_uk":{"name":"Premier Sports 1 [UK]","group":"Premier Sport","directUrl":"https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/m6sqanvm2m/out/v1/f6beb46c6e9a4132ad739f3ca27df6aa/cenc.mpd?ck=MTQ0NGY0MjM1NTI5ZjE4M2YwYTVhNDg2YmVmZTljZGI6ZTVlM2ZlYzY3YTFiYjM0NzJhMjA4OWM4YTBhMjU1N2Y="},
    "premiersports2_uk":{"name":"Premier Sports 2 [UK]","group":"Premier Sport","directUrl":"https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/bcj3iscpd6/out/v1/fcd137b391214f7cb99dd4d7be90ca87/cenc.mpd?ck=MWE1ZGY1MzYwOWViYzk4NTc4OThjNDkwZjQ3MjQ5MTg6NzdmNjI5ODBkNTgyZWM1NDEyODA3OTZhY2Y4YjJkMTk="},
    # ---- Sport cz (Widevine) ----
    "sport1_cz":{"name":"Sport 1","group":"Sport cz","directUrl":"https://dash3.antik.sk/stream/nvidia_sport_1/playlist_cbcs.mpd","widevineUrl":"https://drm.antik.sk/widevine/key"},
    "sport2_cz":{"name":"Sport 2","group":"Sport cz","directUrl":"https://dash4.antik.sk/stream/nvidia_sport2/playlist_cbcs.mpd","widevineUrl":"https://drm.antik.sk/widevine/key"},
    # ---- ELEVEN SPORT (aggiornati: URL + 3 KID:KEY ciascuno) ----
    "eleven4k":{"name":"Eleven Sport 4K","group":"ELEVEN SPORT","directUrl":"https://lb2.pluscdn.pl/ch/1522637/357/dash/b929c9fb/live.mpd","clearKeys":{"ef5e40e00d43450bbeeb40c6849e0309":"614c349de0e08585c7b503568cacd5a1"}},
    "eleven1":{"name":"Eleven Sports 1","group":"ELEVEN SPORT","directUrl":"https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports1/default/index.mpd","clearKeys":{"4853dbe4c4cf51f3ba95424c6e6f69c7":"39c0346198bc9b1614eb319115afdb84","751db0bb03145084973c6cf9c85fa16e":"6571153c39eed18c29cdc63eb83c553a","fd9b5f8ae64a51edacd4f245ef515287":"c867d24646b170b5c0e0556b56b291d7"}},
    "eleven2":{"name":"Eleven Sports 2","group":"ELEVEN SPORT","directUrl":"https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports2/default/index.mpd","clearKeys":{"a118a928ea39552f976c8fad437f71ad":"f58fb7a53ee86de9d0b9823446ba9756","78f826af752f54ddbc4ad9959ff2a42d":"c1479ffada263000730d627a989e96ab","95c2aefadb7e522c9deeed393207f853":"16e857224e16ab01a3c549212cdbdbb8"}},
    "eleven3":{"name":"Eleven Sports 3","group":"ELEVEN SPORT","directUrl":"https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports3/default/index.mpd","clearKeys":{"d895d50a5a0f55758d31f247e6743815":"9f4882e56631edb0da1c7bf1e0fa4904","e3a9d5c27a6d5eac955daf5a1a640c69":"4c2e674f97ff33c5de13032b92e78bc9","e3dd9d531eee578fbd08c87de8ab84d5":"133e5a170236f4ba5930f5ba4213ee03"}},
    "eleven4":{"name":"Eleven Sports 4","group":"ELEVEN SPORT","directUrl":"https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports4/default/index.mpd","clearKeys":{"37b0bbf897ad5bd5a3ec19b5a91f54f9":"3e84e6b93e19197d5aea59ef8ad9d270","54a7d8f8dbee564981beb470f22b529b":"a0e341fec141f8733c0805f5480762ba","14e62b5f16385a139e2a1c747b8b1cc4":"0cece074b5f3fabc76fc9ed109b3819d"}},
    # ---- COMO TV ----
    "comotv1":{"name":"Como TV 1","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/ac7a76c678594a03a8e05392a796f125/index_L1.m3u8"},
    "comotv2":{"name":"Como TV 2","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/c10b9e41c1a34a598cb5e9a345b3a325/index_L1.m3u8"},
    "comotv3":{"name":"Como TV 3","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/ffb389a49afc49338e2cc17724a649aa/index_L1.m3u8"},
    "comotv4":{"name":"Como TV 4","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/617c01e7d8c241d2b1152decbfa60339/index_L1.m3u8"},
    "comotv5":{"name":"Como TV 5","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/e8d4fec57cd24447babe9fbe0151007c/index_L1.m3u8"},
    # ---- CBS Sport ----
    "cbssport":{"name":"CbsSport Mpd","group":"CBS Sport",
                "directUrl":"https://abfjk4haaaaaaaampv6ofhkihi4r6.bia-cf.live.pv-cdn.net/lhr-nitro/live/clients/dash/enc/rbem8rorcw/out/v1/5318821e2c3c44c2a439681b9aa86e9b/cenc.mpd",
                "clearKeys":{"d9623774ac5c8c351aafe97c5fe70267":"5164e6d05164a2d65fa8fcc962aa4861"}},
    # ---- FOX SPORT ----
    "foxsport1":{"name":"FOXChannel Sport","group":"FOX SPORT",
                 "directUrl":"https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/oboxe53wyo/out/v1/f7892a9d706d419a846d738fa22ea33e/cenc.mpd",
                 "clearKeys":{"2fbdaa3bea0d0323ae011b318d1db716":"8726ef7eaf5b9dce15fb6aa9f80bd53f"}},
    "foxsport2":{"name":"FOXChannel Sport 2","group":"FOX SPORT",
                 "directUrl":"https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/tepjqej1ys/out/v1/c9c9159baee749a19612b1598495859a/cenc.mpd",
                 "clearKeys":{"8836fb04d62dc64c9f8a39ef8640d5eb":"d4f05ce56c5231b7cdf53455bea58621"}},
    "foxsport3":{"name":"FOXChannel Sport 3","group":"FOX SPORT",
                 "directUrl":"https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/wybgz0orr8/out/v1/2f6d1612abd44f5883917f8a585b955f/cenc.mpd",
                 "clearKeys":{"11c8c1c2ef0385cf1e64d44bb9c3a395":"5769730ffbdc4b2fd8945929d9ace063"}},
    "foxsportpremium":{"name":"FOXChannel Sport PREMIUM","group":"FOX SPORT",
                 "directUrl":"https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/fdx74zqzhu/out/v1/7d7a8c6981a842b98a683e9fbfe51d17/cenc.mpd",
                 "clearKeys":{"9f327d24c66fbd84e15ab5c9ead7c7a4":"83837185529c0c4048f81386c2d36426"}},
    # ---- GOLD BET LIVE ----
    "goldbet_serieb":{"name":"GOLD BET LIVE TCD SERIE B","group":"GOLD BET LIVE",
                      "directUrl":"https://dctv.mocdn.tv/out/v1/53b5ed79722b4b23932dd86262242e03/manifest_L1.mpd",
                      "clearKeys":{"11c83f71744e40209ed12b1ce234d055":"83279bd86c8f71656440af1abaf43f0a"}},
    # ---- HARDCORE ----
    # 1) PlayboyTV
    "playboytv":{"name":"PlayboyTV","group":"Hardcore",
                 "directUrl":"https://simplitv-live.mdn.ors.at/live/eds/playboy_tv/dash/playboy_tv.mpd",
                 "clearKeys":{"9fd578695b3c36899b637afc7f21ac13":"f39b08441d41a7c503b1e445555b033d"}},
    # 2) Desire
    "desire":{"name":"Desire","group":"Hardcore",
              "directUrl":"https://bpm.tv.delta.nl/dash-cenc/combined/10059/stb.mpd?bk-network=ftth-mobile",
              "clearKeys":{"da77348ad6d9c210977817f87112ea74":"2b2ba7d2ce06d7afb98c49449a5064d5"}},
    # 3-17) 15 canali Antik con KID:KEY statica condivisa
    "hc_babes":{"name":"Babes Antik","group":"Hardcore",
                "directUrl":"https://dash2.antik.sk/stream/hisi_babes/playlist_cbcs.mpd",
                "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_desire":{"name":"Desire Antik","group":"Hardcore",
                 "directUrl":"https://dash3.antik.sk/stream/hisi_desire/playlist_cbcs.mpd",
                 "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_true_amateurs":{"name":"True Amateurs Antik","group":"Hardcore",
                        "directUrl":"https://dash4.antik.sk/stream/hisi_true_amateurs/playlist_cbcs.mpd",
                        "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_bang_u":{"name":"Bang U Antik","group":"Hardcore",
                 "directUrl":"https://dash2.antik.sk/stream/hisi_bang_u/playlist_cbcs.mpd",
                 "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_brazzers_eu":{"name":"Brazzers Europe Antik","group":"Hardcore",
                      "directUrl":"https://dash3.antik.sk/stream/hisi_brazzers_europe/playlist_cbcs.mpd",
                      "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_dorcel":{"name":"Dorcel Antik","group":"Hardcore",
                 "directUrl":"https://dash4.antik.sk/stream/hisi_dorcel/playlist_cbcs.mpd",
                 "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_dorcel_xxx":{"name":"Dorcel Hardcore Antik","group":"Hardcore",
                     "directUrl":"https://dash2.antik.sk/stream/hisi_dorcel_xxx/playlist_cbcs.mpd",
                     "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_leo_tv":{"name":"Leo TV Antik","group":"Hardcore",
                 "directUrl":"https://dash3.antik.sk/stream/hisi_leo_tv/playlist_cbcs.mpd",
                 "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_extasy":{"name":"Extasy Antik","group":"Hardcore",
                 "directUrl":"https://dash4.antik.sk/stream/hisi_extasy/playlist_cbcs.mpd",
                 "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_leo_gold":{"name":"Leo Gold Antik","group":"Hardcore",
                   "directUrl":"https://dash2.antik.sk/stream/hisi_leo_gold/playlist_cbcs.mpd",
                   "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_passion":{"name":"Passion Antik","group":"Hardcore",
                  "directUrl":"https://dash3.antik.sk/stream/hisi_passion_xxx/playlist_cbcs.mpd",
                  "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_dusk":{"name":"Dusk Antik","group":"Hardcore",
               "directUrl":"https://dash4.antik.sk/stream/hisi_dusk/playlist_cbcs.mpd",
               "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_eroxxx":{"name":"EroXXX Antik","group":"Hardcore",
                 "directUrl":"https://dash4.antik.sk/stream/hisi_eroxxx/playlist_cbcs.mpd",
                 "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_erox":{"name":"EroX Antik","group":"Hardcore",
               "directUrl":"https://dash3.antik.sk/stream/hisi_erox/playlist_cbcs.mpd",
               "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    "hc_vixen":{"name":"Vixen Antik","group":"Hardcore",
                "directUrl":"https://dash4.antik.sk/stream/hisi_vixen/playlist_cbcs.mpd",
                "clearKeys":{"11223344556677889900112233445566":"4b80724d0ef86bcb2c21f7999d67739d"}},
    # 18) Blu3 Hu5tler
    "hc_blu3_hustler":{"name":"Blu3 Hu5tler","group":"Hardcore",
                       "directUrl":"https://v4-pan-n79-cdn-01.live.cdn.cgates.lt/live/dash/560601/index.mpd",
                       "clearKeys":{"54393232379c4a57898a8d4d12b6695c":"2305a3f727638465116400f7c422af87"}},
    # ---- Serie B ----
    "serieb/player_serieb.php?event=1":{"name":"Serie B 1","group":"Serie B"},
    "serieb/player_serieb.php?event=2":{"name":"Serie B 2","group":"Serie B"},
    "serieb/player_serieb.php?event=3":{"name":"Serie B 3","group":"Serie B"},
    "serieb/player_serieb.php?event=4":{"name":"Serie B 4","group":"Serie B"},
}

# ============================================================
# GOOGLE DRIVE
# ============================================================
def refresh_access_token():
    global ACCESS_TOKEN
    try:
        r = requests.post("https://oauth2.googleapis.com/token",
            data={"client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,
                  "refresh_token":REFRESH_TOKEN,"grant_type":"refresh_token"}, timeout=30)
        d = r.json()
        if "access_token" in d:
            ACCESS_TOKEN = d["access_token"]
            return True
    except Exception:
        pass
    return False

def upload_to_drive(content):
    if not content: return False
    if not refresh_access_token():
        log("❌ Token Google Drive non valido", C.RED); return False
    try:
        url = f"https://www.googleapis.com/upload/drive/v3/files/{DRIVE_FILE_ID}?uploadType=media"
        r = requests.patch(url, headers={"Authorization":f"Bearer {ACCESS_TOKEN}",
                          "Content-Type":"text/plain"}, data=content.encode("utf-8"), timeout=30)
        if r.status_code == 200:
            log("✅ Playlist inviata su Google Drive!", C.GREEN, bold=True)
            return True
        log(f"❌ Errore Drive HTTP {r.status_code}", C.RED)
    except Exception as e:
        log(f"❌ Errore upload: {e}", C.RED)
    return False

# ============================================================
# KEY EXTRACTION
# ============================================================
def decode_ck(ck):
    try:
        pad = '=' * ((4 - len(ck) % 4) % 4)
        dec = base64.b64decode(ck + pad).decode('utf-8', errors='ignore')
        m = re.search(r'([0-9a-fA-F]+):([0-9a-fA-F]+)', dec)
        if m: return {"kid":m.group(1).lower(), "key":m.group(2).lower()}
    except Exception: pass
    return None

def extract_ck_from_url(raw):
    try:
        if 'ck=' in raw:
            head, tail = raw.split('ck=', 1)
            clean = head.rstrip('&?')
            ck = tail.split('&')[0]
            return clean, decode_ck(ck)
    except Exception: pass
    return raw, None

def parse_clear_keys(raw):
    if not raw: return None
    raw = raw.strip().rstrip(';').strip()
    try:
        p = json.loads(raw)
    except Exception:
        cleaned = raw.strip("\"'").strip()
        if ':' in cleaned:
            a,b = cleaned.split(':',1)
            return {"kid":a.strip().lower(),"key":b.strip().lower()}
        return None
    if isinstance(p,str) and ':' in p:
        a,b = p.split(':',1); return {"kid":a.strip().lower(),"key":b.strip().lower()}
    if isinstance(p,list) and p:
        f = p[0]
        if isinstance(f,str) and ':' in f:
            a,b = f.split(':',1); return {"kid":a.strip().lower(),"key":b.strip().lower()}
        if isinstance(f,dict) and 'kid' in f and 'key' in f:
            return {"kid":str(f['kid']).lower(),"key":str(f['key']).lower()}
    if isinstance(p,dict):
        if 'kid' in p and 'key' in p:
            return {"kid":str(p['kid']).lower(),"key":str(p['key']).lower()}
        if p:
            k,v = next(iter(p.items()))
            return {"kid":str(k).lower(),"key":str(v).lower()}
    return None

def build_clear_keys(ck):
    """
    Converte una struttura di chiavi in una LISTA di stringhe "kid:key".
    Supporta:
      - None
      - dict {kid: key, kid2: key2, ...}       -> tutte le coppie
      - dict {"kid": "...", "key": "..."}      -> singola coppia
      - stringa "kid:key"                      -> singola coppia
    Restituisce None se non c'è nulla.
    """
    if not ck: return None
    if isinstance(ck, dict):
        if 'kid' in ck and 'key' in ck:
            return [f"{str(ck['kid']).lower()}:{str(ck['key']).lower()}"]
        return [f"{str(k).lower()}:{str(v).lower()}" for k, v in ck.items()]
    if isinstance(ck, str):
        return [ck.strip().lower()]
    return None

# ============================================================
# FETCH CANALE
# ============================================================
def fetch_channel(slug, meta):
    if meta.get('directUrl'):
        raw = meta['directUrl']
        clean, ck = extract_ck_from_url(raw)
        if not ck and meta.get('clearKeys'):
            ck = meta['clearKeys']
        return {"url": clean,
                "clear_key": build_clear_keys(ck),
                "widevine": meta.get('widevineUrl'),
                "headers": None}

    if any(x in slug for x in ('player_event.php','player.php','player_serieb.php')):
        page_url = BASE_URL + slug
    else:
        page_url = BASE_URL + slug + '.php'

    r = requests.get(page_url, headers=HEADERS, timeout=12)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}"}

    body = r.text
    try:
        j = json.loads(body)
        body = j.get('body') or j.get('contents') or body
    except Exception: pass

    m = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', body)
    if not m:
        m = re.search(r'STREAM_URL\s*=\s*["\']([^"\']*)["\']', body, re.IGNORECASE)
    if not m:
        return {"waiting": True}

    raw_url = m.group(1).replace('\\/', '/').strip()
    if not raw_url:
        return {"waiting": True}

    clean, ck = extract_ck_from_url(raw_url)
    if not ck:
        km = re.search(r'STREAM_CLEAR_KEYS\s*=\s*(.+?);', body, re.IGNORECASE|re.DOTALL)
        if km:
            ck = parse_clear_keys(km.group(1))

    return {"url": clean, "clear_key": build_clear_keys(ck),
            "widevine": None, "headers": None}

# ============================================================
# SCRAPING
# ============================================================
def scrape_all():
    channels = []
    total = len(CHANNEL_MAP)
    log("Avvio...", C.WHITE)
    log(f"📡 Scraping e estrazione di tutti i {total} canali...", C.CYAN, bold=True)
    time.sleep(0.2)

    for i,(slug,meta) in enumerate(CHANNEL_MAP.items(),1):
        name = meta['name']; group = meta['group']
        direct = 'directUrl' in meta
        suffix = " (Diretto)" if direct else ""
        log(f"[{i}/{total}] 📡 {name}{suffix}...", C.WHITE)

        entry = {"name":name,"group":group,"tvgId":name,"url":None,
                 "clear_key":None,"widevine":None,"headers":None}
        try:
            res = fetch_channel(slug, meta)
            if res is None:
                log("  ⏳ In attesa dell'url", C.YELLOW)
            elif res.get('error'):
                log(f"  ❌ {res['error']}", C.RED)
            elif res.get('waiting'):
                log("  ⏳ In attesa dell'url", C.YELLOW)
            elif res.get('url'):
                entry['url'] = res['url']
                entry['clear_key'] = res.get('clear_key')
                entry['widevine'] = res.get('widevine')
                entry['headers'] = res.get('headers')
                log("  ✅ OK", C.GREEN)
            else:
                log("  ⏳ In attesa dell'url", C.YELLOW)
        except Exception as e:
            log(f"  ❌ Errore: {e}", C.RED)
        channels.append(entry)
        time.sleep(0.05)

    return channels

# ============================================================
# M3U
# ============================================================
def generate_m3u(channels):
    out = '#EXTM3U url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'
    for grp in GROUP_ORDER:
        for ch in channels:
            if ch['group'] != grp or not ch['url']:
                continue
            out += f'#EXTINF:-1 group-title="{grp}" tvg-id="{ch["tvgId"]}",{ch["name"]}\n'
            if ch.get('widevine'):
                out += "#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n"
                out += f'#KODIPROP:inputstream.adaptive.license_key={ch["widevine"]}\n'
            elif ch['clear_key']:
                out += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                for k in ch['clear_key']:
                    out += f'#KODIPROP:inputstream.adaptive.license_key={k}\n'
            out += f'{ch["url"]}\n'
    return out

# ============================================================
# MAIN
# ============================================================
def main():
    clr(); banner()

    channels = scrape_all()
    if not channels:
        log("❌ Nessun canale!", C.RED); sys.exit(1)

    log(f"✅ {len(channels)} canali elaborati.", C.GREEN, bold=True)

    log("📝 Generazione M3U...", C.CYAN)
    m3u = generate_m3u(channels)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'skympd.m3u')
    try:
        with open(out_path,'w',encoding='utf-8') as f:
            f.write(m3u)
        log(f"📁 Salvato: {out_path}", C.GREEN)
    except Exception as e:
        log(f"❌ Errore salvataggio: {e}", C.RED)

    log("☁️ Invio a Google Drive...", C.CYAN)
    upload_to_drive(m3u)

    print()
    log("🎉 Operazione completata!", C.GREEN, bold=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(); log("👋 Interrotto.", C.YELLOW)
