#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📺 Uaznao Scraper - Canali Aggiornati
Versione Python con grafica terminale
"""

import os
import sys
import re
import json
import time
import base64
from datetime import datetime
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Installa 'requests': pip install requests")
    sys.exit(1)

# ============================================================
# COLORI ANSI
# ============================================================
RESET  = '\033[0m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
BLUE   = '\033[94m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
CYAN   = '\033[96m'
GRAY   = '\033[90m'
WHITE  = '\033[97m'

# ============================================================
# CONFIGURAZIONE
# ============================================================
BASE_URL  = 'https://uaznao.com/premium/canalitv/'
OUTPUT_M3U = 'uaznao.m3u'

# Google Drive
CLIENT_ID     = "360991432021-p5qnc2i8jg8vcnv12o33n74cnjl4bk5q.apps.googleusercontent.com"
CLIENT_SECRET = "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"
DRIVE_FILE_ID = "1w6LgRLFOmEYD88fXYlwwhzbBFZ210JG_"
REFRESH_TOKEN = "1//04SFIkmoK5XT4CgYIARAAGAQSNwF-L9IrfgX8z4LgUKT_jsT1BSaCVZ2DO8k2AqpaLcYMZ_MqQvg5SRj6cSmWE0uG3AtU1Egv1kA"

# ============================================================
# CHANNEL_MAP
# ============================================================
CHANNEL_MAP = {
    # --- Rai ---
    "rai1": {"name": "Rai 1", "group": "Rai", "directUrl": "https://raiuno3-live.akamaized.net/hls/live/2017910/raiuno3/raiuno3/playlist.m3u8"},
    "rai2": {"name": "Rai 2", "group": "Rai", "directUrl": "https://raidue3-live.akamaized.net/hls/live/2017983/raidue3/raidue3/playlist.m3u8"},
    "rai3": {"name": "Rai 3", "group": "Rai", "directUrl": "https://raitre3-live.akamaized.net/hls/live/2018002/raitre3/raitre3/playlist.m3u8"},

    # --- Mediaset ---
    "rete4": {"name": "Rete 4", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-r4/r4-clr.isml/manifest.mpd"},
    "canale5": {"name": "Canale 5", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-c5/c5-clr.isml/manifest.mpd"},
    "italia1": {"name": "Italia 1", "group": "Mediaset", "directUrl": "https://live03-col.msf.cdn.mediaset.net/live/ch-i1/i1-clr.isml/manifest.mpd"},
    "grandefratello": {"name": "Grande Fratello", "group": "Mediaset", "directUrl": "https://live02-col.msf.cdn.mediaset.net/live/ch-b7/b7-clr.isml/index.m3u8"},

    # --- RSI ---
    "rsi1": {"name": "RSI La 1 HD", "group": "RSI",
             "directUrl": "https://wp3-s-anp31323132-live-ch-prod.prod.cdn.dmdsdp.com/live/disk1/SV09042/stb-dash-fhd-avc/SV09042.mpd",
             "clearKeys": {"09af5f6eb89041ca8f5d164165142e86": "1989cc9c9ce5b2b52cb93edaaefe8420",
                           "d268d810d8a73bd8b7d54a6a087581d2": "1aaf297543168c625e05aa9e27344471"}},
    "rsi2": {"name": "RSI La 2 HD", "group": "RSI",
             "directUrl": "https://wp2-s-anp31323132-live-ch-prod.prod.cdn.dmdsdp.com/live/disk1/SV09043/stb-dash-fhd-avc/SV09043.mpd",
             "clearKeys": {"117d07fd98cc46ef8e09936d0d37c506": "b9528cb3f23eaad789f0f33bf6b01868",
                           "166b2f0d56fb32d9b46d4b1ca1b5bf16": "d78ee5c91eb3b9b6d37414a4f789bc9b"}},

    # --- Sky Cinema ---
    "cinema1": {"name": "Sky Cinema Uno", "group": "Sky Cinema"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "Sky Cinema"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "Sky Cinema"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "Sky Cinema"},
    "cinemaaction": {"name": "Sky Cinema Action", "group": "Sky Cinema"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "Sky Cinema"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "Sky Cinema"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "Sky Cinema"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "Sky Cinema"},

    # --- Sky Sport ---
    "sport24": {"name": "Sky Sport 24", "group": "Sky Sport"},
    "sportuno": {"name": "Sky Sport Uno", "group": "Sky Sport"},
    "calcio": {"name": "Sky Sport Calcio", "group": "Sky Sport"},
    "arena": {"name": "Sky Sport Arena", "group": "Sky Sport"},
    "sportmax": {"name": "Sky Sport Max", "group": "Sky Sport"},
    "sportmix": {"name": "Sky Sport Mix", "group": "Sky Sport"},
    "legend": {"name": "Sky Sport Legend", "group": "Sky Sport"},
    "f1": {"name": "Sky Sport F1", "group": "Sky Sport"},
    "motogp": {"name": "Sky Sport MotoGP", "group": "Sky Sport"},
    "tennis": {"name": "Sky Sport Tennis", "group": "Sky Sport"},
    "basket": {"name": "Sky Sport Basket", "group": "Sky Sport"},
    "golf": {"name": "Sky Sport Golf", "group": "Sky Sport"},
    "amazonlive": {"name": "Amazon Live", "group": "Sky Sport"},
    "sport251": {"name": "Sky Sport 251", "group": "Sky Sport"},
    "sport252": {"name": "Sky Sport 252", "group": "Sky Sport"},
    "sport253": {"name": "Sky Sport 253", "group": "Sky Sport"},
    "sport254": {"name": "Sky Sport 254", "group": "Sky Sport"},
    "sport255": {"name": "Sky Sport 255", "group": "Sky Sport"},
    "sport256": {"name": "Sky Sport 256", "group": "Sky Sport"},
    "sport257": {"name": "Sky Sport 257", "group": "Sky Sport"},
    "sport258": {"name": "Sky Sport 258", "group": "Sky Sport"},
    "sport259": {"name": "Sky Sport 259", "group": "Sky Sport"},

    # --- Intrattenimento ---
    "uno": {"name": "Sky Uno", "group": "Intrattenimento"},
    "unoplus": {"name": "Sky Uno Plus", "group": "Intrattenimento"},
    "atlantic": {"name": "Sky Atlantic", "group": "Intrattenimento"},
    "serie": {"name": "Sky Serie", "group": "Intrattenimento"},
    "investigation": {"name": "Sky Investigation", "group": "Intrattenimento"},
    "crime": {"name": "Sky Crime", "group": "Intrattenimento"},
    "adventure": {"name": "Sky Adventure", "group": "Intrattenimento"},
    "nature": {"name": "Sky Nature", "group": "Intrattenimento"},
    "arte": {"name": "Sky Arte", "group": "Intrattenimento"},
    "documentaries": {"name": "Sky Documentaries", "group": "Intrattenimento"},
    "comedycentral": {"name": "Comedy Central", "group": "Intrattenimento"},
    "deakids": {"name": "DeAKids", "group": "Intrattenimento"},
    "nickjunior": {"name": "Nick Jr", "group": "Intrattenimento"},
    "nickeleodeon": {"name": "Nickelodeon", "group": "Intrattenimento"},
    "cartoonnetwork": {"name": "Cartoon Network", "group": "Intrattenimento"},
    "boomerang": {"name": "Boomerang", "group": "Intrattenimento"},

    # --- DAZN CH ---
    "daznch/player_event.php?event=1": {"name": "DAZN 1", "group": "DAZN CH"},
    "daznch/player_event.php?event=2": {"name": "DAZN 2", "group": "DAZN CH"},
    "daznch/player_event.php?event=3": {"name": "DAZN 3", "group": "DAZN CH"},
    "daznch/player_event.php?event=4": {"name": "DAZN 4", "group": "DAZN CH"},
    "daznch/player_event.php?event=5": {"name": "DAZN 5", "group": "DAZN CH"},
    "daznch/player_event.php?event=6": {"name": "DAZN 6", "group": "DAZN CH"},
    "daznch/player_event.php?event=7": {"name": "DAZN 7", "group": "DAZN CH"},
    "daznch/player_event.php?event=8": {"name": "DAZN 8", "group": "DAZN CH"},
    "daznch/player_event.php?event=9": {"name": "DAZN 9", "group": "DAZN CH"},
    "daznch/player_event.php?event=10": {"name": "DAZN 10", "group": "DAZN CH"},

    # --- BluSport ---
    "blusport/player_event.php?event=1": {"name": "Blu Sport 1", "group": "BluSport"},
    "blusport/player_event.php?event=2": {"name": "Blu Sport 2", "group": "BluSport"},
    "blusport/player_event.php?event=3": {"name": "Blu Sport 3", "group": "BluSport"},
    "blusport/player_event.php?event=4": {"name": "Blu Sport 4", "group": "BluSport"},
    "blusport/player_event.php?event=5": {"name": "Blu Sport 5", "group": "BluSport"},
    "blusport/player_event.php?event=6": {"name": "Blu Sport 6", "group": "BluSport"},
    "blusport/player_event.php?event=7": {"name": "Blu Sport 7", "group": "BluSport"},
    "blusport/player_event.php?event=8": {"name": "Blu Sport 8", "group": "BluSport"},
    "blusport/player_event.php?event=9": {"name": "Blu Sport 9", "group": "BluSport"},
    "blusport/player_event.php?event=10": {"name": "Blu Sport 10", "group": "BluSport"},

    # --- DAZN PT ---
    "dazn1_pt": {"name": "DAZN 1 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$521/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MzliY2JjOTQxOGFhNGQ2MmI5NmI2YTNlYWUyZjZkZjA6YThmOTY4YjZhOGVkN2JmYjE3YmY3ODdiNmM5MzBjN2U="},
    "dazn2_pt": {"name": "DAZN 2 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$522/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MzgwNWNkNTMzYzEzNDFhNzkzNGQxMzYyOWViN2EzNGU6MjU0MjU2NDkyOGNiOGUzZmU0NTk1YWI4ZGNmZDZlNzc="},
    "dazn3_pt": {"name": "DAZN 3 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$523/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=NzIyNGYyYTZhMTRhNGQ4ODg3NGQxMGRkOTUzYzg4ZGM6OTcxOWVhMjM4ZDNkZTY2ZWIwNzNjZTg0MjgxNGY0NjQ="},
    "dazn4_pt": {"name": "DAZN 4 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$524/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MGI2ZTVmZTViMWQxNDBiMDkyZTIyY2M2NjIwODgyNzY6NmJkZDc2YWRiYzViYjI1MDg5OTgzYjI1MDBkZGU3Y2E="},
    "dazn5_pt": {"name": "DAZN 5 PT", "group": "DAZN PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$525/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ZDkzMWQ2NzE4ODQxNDVkZmIzOTJiZTBjYWRlNTA4OGM6YmVlZTM5NTZiNzY5YzM5ZjAwZmEzY2U4NGEyZWZhYmE="},

    # --- Sportv PT ---
    "sportv1_pt": {"name": "Sport TV 1 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$151/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=YzJiYWM5YzM5M2YxNDVmYzkyNGNlNTcyY2E5OTE1NmY6NDVmNjYzN2VlZjgwZWFmYmU3ZTYzMDIzMTEzOWRmNWI="},
    "sportv2_pt": {"name": "Sport TV 2 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$152/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MGQyOGVkZjRmMDU1NDA5YmIxMmQ2ZDAyNjBiMjZiNmI6YmY2OWY4YTMzYzM5YzMxZjVmZjA2YWI1MjAxMmUyN2M="},
    "sportv3_pt": {"name": "Sport TV 3 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$153/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=MjA2ZmVjNTZmNWI3NDFlNWFhODExMjQ4OTVkOWI1OTI6MjdiOTE1MDVhYTY5MjZmNTkxOTljODI4YmMyNzc2N2I="},
    "sportv4_pt": {"name": "Sport TV 4 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$10/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=Y2MwYjdhYzMxYjVlNDJmOGJmOTM0Zjk5YWNmNzFhOGE6ZDc2NDI0ZDY0NGEzNjAwNTY1NjdhMjQ4ZDhiODliNmM="},
    "sportv5_pt": {"name": "Sport TV 5 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$112/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ODFjYTQzNGM5MzFhNDAzZTk1MGRmM2Q4MDhjMjRjNDE6MTg1NDgxOTBjZjNjODI5NDA5NmFmOGEyMTQ2ZTMyYTU="},
    "sportv6_pt": {"name": "Sport TV 6 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$566/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=ZDMxOWFhYjAyYTgzNDIyNDhjY2ViMGZkZjA2MGJjNTQ6YjM2NjY4YTgzNmIxNTA1NWJlMWYwNGI4ZDhhOGNjNzA="},
    "sportv7_pt": {"name": "Sport TV 7 [PT]", "group": "Sportv PT", "directUrl": "https://rr.cdn.vodafone.pt/LIVE/sdash/LIVE$597/index.mpd/Manifest.mpd?start=LIVE&end=END&device=DASH_AVC_HD&ck=NDAwOTU3YWM2OGQ1NDlmYmJiYmM2NjhkM2E5ZWI3MDk6M2RkMzUxZjE4NzViMGRkNDBhNGUzOTJmMDZhMjliMjk="},

    # --- Premier Sport ---
    "premiersports1_uk": {"name": "Premier Sports 1 [UK]", "group": "Premier Sport", "directUrl": "https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/m6sqanvm2m/out/v1/f6beb46c6e9a4132ad739f3ca27df6aa/cenc.mpd?ck=MTQ0NGY0MjM1NTI5ZjE4M2YwYTVhNDg2YmVmZTljZGI6ZTVlM2ZlYzY3YTFiYjM0NzJhMjA4OWM4YTBhMjU1N2Y="},
    "premiersports2_uk": {"name": "Premier Sports 2 [UK]", "group": "Premier Sport", "directUrl": "https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/bcj3iscpd6/out/v1/fcd137b391214f7cb99dd4d7be90ca87/cenc.mpd?ck=MWE1ZGY1MzYwOWViYzk4NTc4OThjNDkwZjQ3MjQ5MTg6NzdmNjI5ODBkNTgyZWM1NDEyODA3OTZhY2Y4YjJkMTk="},

    # --- SPORT CZ ---
    "sport1_cz": {"name": "SPORT 1 [CZ]", "group": "SPORT CZ",
                  "directUrl": "https://dash2.antik.sk/stream/nvidia_sport_1/playlist_cbcs.mpd",
                  "clearKeys": {"11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d"}},
    "sport2_cz": {"name": "SPORT 2 [CZ]", "group": "SPORT CZ",
                  "directUrl": "https://dash3.antik.sk/stream/nvidia_sport2/playlist_cbcs.mpd",
                  "clearKeys": {"11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d"}},

    # --- ELEVEN SPORT ---
    "eleven4k": {"name": "Eleven Sport 4K", "group": "ELEVEN SPORT",
                 "directUrl": "https://lb2.pluscdn.pl/ch/1522637/357/dash/b929c9fb/live.mpd",
                 "clearKeys": {"ef5e40e00d43450bbeeb40c6849e0309": "614c349de0e08585c7b503568cacd5a1"}},
    "eleven1": {"name": "Eleven Channel Sport 1", "group": "ELEVEN SPORT",
                "directUrl": "https://lb2.pluscdn.pl/ch/1457744/147/dash/4867711b/live.mpd",
                "clearKeys": {"525a9da2120045a6973709dbcd685609": "d8a7578d81ce754755a503ad8ac98ec0"}},
    "eleven2": {"name": "Eleven Channel Sport 2", "group": "ELEVEN SPORT",
                "directUrl": "https://cdn-s-lb2.pluscdn.pl/ch/1457734/144/dash/0be7047a/live.mpd",
                "clearKeys": {"2cd12eaca5c14b30a3280b1a89484809": "e2c14f6cc245c1a5ebbce8c8c704fc6c"}},
    "eleven3": {"name": "Eleven Channel Sport 3", "group": "ELEVEN SPORT",
                "directUrl": "https://lb2.pluscdn.pl/ch/1457736/145/dash/58566515/live.mpd",
                "clearKeys": {"e006dab396714c0b9dd6228255c1b709": "2cdf44e960bbc4d276968012fe659272"}},
    "eleven4": {"name": "Eleven Channel Sport 4", "group": "ELEVEN SPORT",
                "directUrl": "https://cdn-s-lb2.pluscdn.pl/ch/1457740/146/dash/e653c27f/live.mpd",
                "clearKeys": {"3e943ad288964c77917cc654fc60d109": "18cf07106507f411210c4a26d901a9e4"}},

    # --- COMO TV ---
    "comotv1": {"name": "Como TV 1", "group": "COMO TV", "directUrl": "https://comofootball.mocdn.tv/out/v1/ac7a76c678594a03a8e05392a796f125/index_L1.m3u8"},
    "comotv2": {"name": "Como TV 2", "group": "COMO TV", "directUrl": "https://comofootball.mocdn.tv/out/v1/c10b9e41c1a34a598cb5e9a345b3a325/index_L1.m3u8"},
    "comotv3": {"name": "Como TV 3", "group": "COMO TV", "directUrl": "https://comofootball.mocdn.tv/out/v1/ffb389a49afc49338e2cc17724a649aa/index_L1.m3u8"},
    "comotv4": {"name": "Como TV 4", "group": "COMO TV", "directUrl": "https://comofootball.mocdn.tv/out/v1/617c01e7d8c241d2b1152decbfa60339/index_L1.m3u8"},
    "comotv5": {"name": "Como TV 5", "group": "COMO TV", "directUrl": "https://comofootball.mocdn.tv/out/v1/e8d4fec57cd24447babe9fbe0151007c/index_L1.m3u8"},

    # --- Serie B ---
    "serieb/player_serieb.php?event=1": {"name": "Serie B 1", "group": "Serie B"},
    "serieb/player_serieb.php?event=2": {"name": "Serie B 2", "group": "Serie B"},
    "serieb/player_serieb.php?event=3": {"name": "Serie B 3", "group": "Serie B"},
    "serieb/player_serieb.php?event=4": {"name": "Serie B 4", "group": "Serie B"},
}

# ============================================================
# STAMPA GRAFICA TERMINALE
# ============================================================
def print_header():
    line = '═' * 44
    print(f'{BLUE}{line}{RESET}')
    print(f'{BLUE}📺 Uaznao Scraper - Canali Aggiornati{RESET}')
    print(f'{BLUE}{line}{RESET}')
    print()

def ts():
    return datetime.now().strftime('%H:%M:%S')

def log_msg(msg):
    print(f'{GRAY}[{ts()}]{RESET} {msg}')

def log_progress(idx, total, name, direct=False):
    tag = f'{YELLOW} (Diretto){RESET}' if direct else ''
    print(f'{GRAY}[{ts()}]{RESET} [{idx}/{total}] {CYAN}🛰️  {name}{tag}...{RESET}')

def log_ok():
    print(f'{GRAY}[{ts()}]{RESET}   {GREEN}✅ OK{RESET}')

def log_err(reason=''):
    print(f'{GRAY}[{ts()}]{RESET}   {RED}❌ {reason or "ERRORE"}{RESET}')

def log_warn(msg):
    print(f'{GRAY}[{ts()}]{RESET}   {YELLOW}⚠️  {msg}{RESET}')

# ============================================================
# ESTRATTORE ck= → kid:key
# ============================================================
def decode_ck(ck):
    try:
        pad = '=' * ((4 - len(ck) % 4) % 4)
        decoded = base64.b64decode(ck + pad).decode('utf-8', errors='ignore')
        m = re.search(r'([0-9a-fA-F]+):([0-9a-fA-F]+)', decoded)
        if m:
            return {'kid': m.group(1).lower(), 'key': m.group(2).lower()}
    except Exception:
        pass
    return None

def extract_ck_from_url(raw_url):
    try:
        if 'ck=' not in raw_url:
            return raw_url, None
        clean_url = raw_url.split('?')[0]
        m = re.search(r'[?&]ck=([^&]+)', raw_url)
        if not m:
            return clean_url, None
        ck = m.group(1)
        return clean_url, decode_ck(ck)
    except Exception:
        return raw_url, None

# ============================================================
# SCRAPING DI UN CANALE
# ============================================================
def fetch_channel(slug, meta):
    # Canale con directUrl
    if meta.get('directUrl'):
        raw = meta['directUrl']
        clean_url, ck = extract_ck_from_url(raw)
        return {
            'url': clean_url,
            'clearKey': ck or meta.get('clearKeys'),
            'direct': True
        }

    # Scraping pagina
    if 'player_event.php' in slug or 'player.php' in slug or 'player_serieb.php' in slug:
        page_url = BASE_URL + slug
    else:
        page_url = BASE_URL + slug + '.php'

    r = requests.get(page_url, timeout=10)
    if r.status_code != 200:
        raise Exception(f'HTTP {r.status_code}')

    body = r.text
    # Rimuovi eventuale JSON wrapper
    try:
        j = json.loads(body)
        if 'body' in j:
            body = j['body']
        elif 'contents' in j:
            body = j['contents']
    except Exception:
        pass

    # Cerca STREAM_URL
    m = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', body)
    if not m:
        m = re.search(r'STREAM_URL\s*=\s*["\']([^"\']*)["\']', body, re.IGNORECASE)
    if not m:
        return None

    raw_url = m.group(1).replace('\\/', '/')
    clean_url, ck = extract_ck_from_url(raw_url)

    # Cerca STREAM_CLEAR_KEYS se non c'è ck=
    if not ck:
        km = re.search(r'STREAM_CLEAR_KEYS\s*=\s*(.+?);', body, re.IGNORECASE | re.DOTALL)
        if km:
            raw_keys = km.group(1).strip().rstrip(';').strip()
            try:
                parsed = json.loads(raw_keys)
                if isinstance(parsed, str) and ':' in parsed:
                    kid, key = parsed.split(':', 1)
                    ck = {'kid': kid.strip().lower(), 'key': key.strip().lower()}
                elif isinstance(parsed, list) and parsed:
                    first = parsed[0]
                    if isinstance(first, str) and ':' in first:
                        kid, key = first.split(':', 1)
                        ck = {'kid': kid.strip().lower(), 'key': key.strip().lower()}
                    elif isinstance(first, dict):
                        ck = {'kid': str(first.get('kid', '')).lower(),
                              'key': str(first.get('key', '')).lower()}
                elif isinstance(parsed, dict):
                    if 'kid' in parsed and 'key' in parsed:
                        ck = {'kid': str(parsed['kid']).lower(),
                              'key': str(parsed['key']).lower()}
                    else:
                        k = list(parsed.keys())[0]
                        ck = {'kid': str(k).lower(), 'key': str(parsed[k]).lower()}
            except Exception:
                cleaned = raw_keys.replace('"', '').replace("'", '').strip()
                if ':' in cleaned:
                    kid, key = cleaned.split(':', 1)
                    ck = {'kid': kid.strip().lower(), 'key': key.strip().lower()}

    return {'url': clean_url, 'clearKey': ck, 'direct': False}

# ============================================================
# GENERAZIONE M3U
# ============================================================
def generate_m3u(channels):
    lines = ['#EXTM3U url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"']
    for ch in channels:
        if not ch.get('url'):
            continue
        lines.append(f'#EXTINF:-1 group-title="{ch["group"]}" tvg-id="{ch["name"]}" tvg-logo="" ,{ch["name"]}')

        ck = ch.get('clearKey')
        if ck and ck.get('kid') and ck.get('key'):
            lines.append('#KODIPROP:inputstream.adaptive.license_type=clearkey')
            lines.append(f'#KODIPROP:inputstream.adaptive.license_key={ck["kid"]}:{ck["key"]}')

        lines.append(ch['url'])
    return '\n'.join(lines) + '\n'

# ============================================================
# UPLOAD GOOGLE DRIVE
# ============================================================
def refresh_access_token():
    try:
        r = requests.post('https://oauth2.googleapis.com/token', data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        }, timeout=15)
        data = r.json()
        return data.get('access_token')
    except Exception:
        return None

def upload_to_drive(content):
    token = refresh_access_token()
    if not token:
        log_err('Token Drive non valido')
        return False
    url = f'https://www.googleapis.com/upload/drive/v3/files/{DRIVE_FILE_ID}?uploadType=media'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/plain'
    }
    try:
        r = requests.patch(url, headers=headers, data=content.encode('utf-8'), timeout=30)
        return r.status_code == 200
    except Exception as e:
        log_err(f'Upload: {e}')
        return False

# ============================================================
# MAIN
# ============================================================
def main():
    print_header()

    total = len(CHANNEL_MAP)
    log_msg('Avvio...')
    log_msg(f'🔍 Scraping e estrazione di tutti i {total} canali...')

    channels = []
    ok_count = 0
    err_count = 0

    for idx, (slug, meta) in enumerate(CHANNEL_MAP.items(), start=1):
        name = meta['name']
        is_direct = bool(meta.get('directUrl'))
        log_progress(idx, total, name, direct=is_direct)

        try:
            result = fetch_channel(slug, meta)
            if result and result.get('url'):
                channel = {
                    'name': name,
                    'group': meta['group'],
                    'tvgId': name,
                    'url': result['url'],
                    'clearKey': result.get('clearKey')
                }
                channels.append(channel)
                log_ok()
                ok_count += 1
            else:
                log_err('Nessun URL')
                err_count += 1
        except Exception as e:
            log_err(str(e)[:40])
            err_count += 1

        # Piccolo delay per rispettare i tempi della grafica
        time.sleep(0.05)

    # ============================================================
    # SALVA M3U LOCALE
    # ============================================================
    print()
    log_msg(f'📝 Generazione playlist M3U ({len(channels)} canali)...')
    m3u_content = generate_m3u(channels)

    try:
        with open(OUTPUT_M3U, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        log_ok()
    except Exception as e:
        log_err(str(e))

    # ============================================================
    # INVIO AUTOMATICO A GOOGLE DRIVE
    # ============================================================
    print()
    log_msg('☁️  Invio automatico a Google Drive...')
    if upload_to_drive(m3u_content):
        log_ok()
    else:
        log_err('Upload fallito')

    # ============================================================
    # RIEPILOGO
    # ============================================================
    print()
    line = '─' * 44
    print(f'{BLUE}{line}{RESET}')
    print(f'{BOLD}📊 RIEPILOGO{RESET}')
    print(f'{BLUE}{line}{RESET}')
    print(f'   Canali totali:  {WHITE}{total}{RESET}')
    print(f'   {GREEN}OK:{RESET}             {GREEN}{ok_count}{RESET}')
    print(f'   {RED}Errori:{RESET}         {RED}{err_count}{RESET}')
    print(f'   Playlist:       {CYAN}{OUTPUT_M3U}{RESET}')
    print(f'{BLUE}{line}{RESET}')
    print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\n{YELLOW}Interrotto dall\'utente.{RESET}')
        sys.exit(0)