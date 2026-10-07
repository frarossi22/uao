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
    "DAZN CH","DAZN PT","Sportv PT","Premier Sport","Sport cz",
    "ELEVEN SPORT","COMO TV","BluSport","Intrattenimento"
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
    # ---- DAZN PT ----
    "dazn1_pt":{"name":"DAZN 1 PT","group":"DAZN PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$521/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MzliY2JjOTQxOGFhNGQ2MmI5NmI2YTNlYWUyZjZkZjA6YThmOTY4YjZhOGVkN2JmYjE3YmY3ODdiNmM5MzBjN2U="},
    "dazn2_pt":{"name":"DAZN 2 PT","group":"DAZN PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$522/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MzgwNWNkNTMzYzEzNDFhNzkzNGQxMzYyOWViN2EzNGU6MjU0MjU2NDkyOGNiOGUzZmU0NTk1YWI4ZGNmZDZlNzc="},
    "dazn3_pt":{"name":"DAZN 3 PT","group":"DAZN PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$523/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=NzIyNGYyYTZhMTRhNGQ4ODg3NGQxMGRkOTUzYzg4ZGM6OTcxOWVhMjM4ZDNkZTY2ZWIwNzNjZTg0MjgxNGY0NjQ="},
    "dazn4_pt":{"name":"DAZN 4 PT","group":"DAZN PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$524/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MGI2ZTVmZTViMWQxNDBiMDkyZTIyY2M2NjIwODgyNzY6NmJkZDc2YWRiYzViYjI1MDg5OTgzYjI1MDBkZGU3Y2E="},
    "dazn5_pt":{"name":"DAZN 5 PT","group":"DAZN PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$525/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ZDkzMWQ2NzE4ODQxNDVkZmIzOTJiZTBjYWRlNTA4OGM6YmVlZTM5NTZiNzY5YzM5ZjAwZmEzY2U4NGEyZWZhYmE="},
    # ---- Sportv PT ----
    "sportv1_pt":{"name":"Sport TV 1 [PT]","group":"Sportv PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$151/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=YzJiYWM5YzM5M2YxNDVmYzkyNGNlNTcyY2E5OTE1NmY6NDVmNjYzN2VlZjgwZWFmYmU3ZTYzMDIzMTEzOWRmNWI="},
    "sportv2_pt":{"name":"Sport TV 2 [PT]","group":"Sportv PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$152/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MGQyOGVkZjRmMDU1NDA5YmIxMmQ2ZDAyNjBiMjZiNmI6YmY2OWY4YTMzYzM5YzMxZjVmZjA2YWI1MjAxMmUyN2M="},
    "sportv3_pt":{"name":"Sport TV 3 [PT]","group":"Sportv PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$153/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MjA2ZmVjNTZmNWI3NDFlNWFhODExMjQ4OTVkOWI1OTI6MjdiOTE1MDVhYTY5MjZmNTkxOTljODI4YmMyNzc2N2I="},
    "sportv4_pt":{"name":"Sport TV 4 [PT]","group":"Sportv PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$10/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=Y2MwYjdhYzMxYjVlNDJmOGJmOTM0Zjk5YWNmNzFhOGE6ZDc2NDI0ZDY0NGEzNjAwNTY1NjdhMjQ4ZDhiODliNmM="},
    "sportv5_pt":{"name":"Sport TV 5 [PT]","group":"Sportv PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$112/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ODFjYTQzNGM5MzFhNDAzZTk1MGRmM2Q4MDhjMjRjNDE6MTg1NDgxOTBjZjNjODI5NDA5NmFmOGEyMTQ2ZTMyYTU="},
    "sportv6_pt":{"name":"Sport TV 6 [PT]","group":"Sportv PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$566/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ZDMxOWFhYjAyYTgzNDIyNDhjY2ViMGZkZjA2MGJjNTQ6YjM2NjY4YTgzNmIxNTA1NWJlMWYwNGI4ZDhhOGNjNzA="},
    "sportv7_pt":{"name":"Sport TV 7 [PT]","group":"Sportv PT","directUrl":"https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$597/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=NDAwOTU3YWM2OGQ1NDlmYmJiYmM2NjhkM2E5ZWI3MDk6M2RkMzUxZjE4NzViMGRkNDBhNGUzOTJmMDZhMjliMjk="},
    # ---- Premier Sport ----
    "premiersports1_uk":{"name":"Premier Sports 1 [UK]","group":"Premier Sport","directUrl":"https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/m6sqanvm2m/out/v1/f6beb46c6e9a4132ad739f3ca27df6aa/cenc.mpd?ck=MTQ0NGY0MjM1NTI5ZjE4M2YwYTVhNDg2YmVmZTljZGI6ZTVlM2ZlYzY3YTFiYjM0NzJhMjA4OWM4YTBhMjU1N2Y="},
    "premiersports2_uk":{"name":"Premier Sports 2 [UK]","group":"Premier Sport","directUrl":"https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/bcj3iscpd6/out/v1/fcd137b391214f7cb99dd4d7be90ca87/cenc.mpd?ck=MWE1ZGY1MzYwOWViYzk4NTc4OThjNDkwZjQ3MjQ5MTg6NzdmNjI5ODBkNTgyZWM1NDEyODA3OTZhY2Y4YjJkMTk="},
    # ---- Sport cz (Widevine) ----
    "sport1_cz":{"name":"Sport 1","group":"Sport cz","directUrl":"https://dash3.antik.sk/stream/nvidia_sport_1/playlist_cbcs.mpd","widevineUrl":"https://drm.antik.sk/widevine/key"},
    "sport2_cz":{"name":"Sport 2","group":"Sport cz","directUrl":"https://dash4.antik.sk/stream/nvidia_sport2/playlist_cbcs.mpd","widevineUrl":"https://drm.antik.sk/widevine/key"},
    # ---- ELEVEN SPORT ----
    "eleven4k":{"name":"Eleven Sport 4K","group":"ELEVEN SPORT","directUrl":"https://lb2.pluscdn.pl/ch/1522637/357/dash/b929c9fb/live.mpd","clearKeys":{"ef5e40e00d43450bbeeb40c6849e0309":"614c349de0e08585c7b503568cacd5a1"}},
    "eleven1":{"name":"Eleven Channel Sport 1","group":"ELEVEN SPORT","directUrl":"https://lb2.pluscdn.pl/ch/1457744/147/dash/4867711b/live.mpd","clearKeys":{"525a9da2120045a6973709dbcd685609":"d8a7578d81ce754755a503ad8ac98ec0"}},
    "eleven2":{"name":"Eleven Channel Sport 2","group":"ELEVEN SPORT","directUrl":"https://cdn-s-lb2.pluscdn.pl/ch/1457734/144/dash/0be7047a/live.mpd","clearKeys":{"2cd12eaca5c14b30a3280b1a89484809":"e2c14f6cc245c1a5ebbce8c8c704fc6c"}},
    "eleven3":{"name":"Eleven Channel Sport 3","group":"ELEVEN SPORT","directUrl":"https://lb2.pluscdn.pl/ch/1457736/145/dash/58566515/live.mpd","clearKeys":{"e006dab396714c0b9dd6228255c1b709":"2cdf44e960bbc4d276968012fe659272"}},
    "eleven4":{"name":"Eleven Channel Sport 4","group":"ELEVEN SPORT","directUrl":"https://cdn-s-lb2.pluscdn.pl/ch/1457740/146/dash/e653c27f/live.mpd","clearKeys":{"3e943ad288964c77917cc654fc60d109":"18cf07106507f411210c4a26d901a9e4"}},
    # ---- COMO TV ----
    "comotv1":{"name":"Como TV 1","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/ac7a76c678594a03a8e05392a796f125/index_L1.m3u8"},
    "comotv2":{"name":"Como TV 2","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/c10b9e41c1a34a598cb5e9a345b3a325/index_L1.m3u8"},
    "comotv3":{"name":"Como TV 3","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/ffb389a49afc49338e2cc17724a649aa/index_L1.m3u8"},
    "comotv4":{"name":"Como TV 4","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/617c01e7d8c241d2b1152decbfa60339/index_L1.m3u8"},
    "comotv5":{"name":"Como TV 5","group":"COMO TV","directUrl":"https://comofootball.mocdn.tv/out/v1/e8d4fec57cd24447babe9fbe0151007c/index_L1.m3u8"},
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

def build_clear_key_string(ck):
    if not ck: return None
    if isinstance(ck, dict):
        if 'kid' in ck and 'key' in ck:
            return f"{str(ck['kid']).lower()}:{str(ck['key']).lower()}"
        k, v = next(iter(ck.items()))
        return f"{str(k).lower()}:{str(v).lower()}"
    if isinstance(ck, str):
        return ck.strip().lower()
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
                "clear_key": build_clear_key_string(ck),
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

    return {"url": clean, "clear_key": build_clear_key_string(ck),
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
                out += f'#KODIPROP:inputstream.adaptive.license_key={ch["clear_key"]}\n'
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
