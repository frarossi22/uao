import sys
import re
import base64
import requests

# Credenziali Google Drive
CLIENT_ID = "360991432021-p5qnc2i8jg8vcnv12o33n74cnjl4bk5q.apps.googleusercontent.com"
CLIENT_SECRET = "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"
DRIVE_FILE_ID = "1w6LgRLFOmEYD88fXYlwwhzbBFZ210JG_"
REFRESH_TOKEN = "1//04SFIkmoK5XT4CgYIARAAGAQSNwF-L9IrfgX8z4LgUKT_jsT1BSaCVZ2DO8k2AqpaLcYMZ_MqQvg5SRj6cSmWE0uG3AtU1Egv1kA"

ACCESS_TOKEN = ""
BASE_URL = 'https://uaznao.com/premium/canalitv/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

CHANNEL_MAP = {
    "cinemaaction": {"name": "Sky Cinema Action", "group": "CINEMA"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "CINEMA"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "CINEMA"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "CINEMA"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "CINEMA"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "CINEMA"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "CINEMA"},
    "cinema1": {"name": "Sky Cinema Uno", "group": "CINEMA"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "CINEMA"},
    "sport24": {"name": "Sky Sport 24", "group": "SPORT"},
    "sport251": {"name": "Sky Sport 251", "group": "SPORT"},
    "sport252": {"name": "Sky Sport 252", "group": "SPORT"},
    "sport253": {"name": "Sky Sport 253", "group": "SPORT"},
    "sport254": {"name": "Sky Sport 254", "group": "SPORT"},
    "sport255": {"name": "Sky Sport 255", "group": "SPORT"},
    "sport256": {"name": "Sky Sport 256", "group": "SPORT"},
    "sport257": {"name": "Sky Sport 257", "group": "SPORT"},
    "sport258": {"name": "Sky Sport 258", "group": "SPORT"},
    "sport259": {"name": "Sky Sport 259", "group": "SPORT"},
    "arena": {"name": "Sky Sport Arena", "group": "SPORT"},
    "basket": {"name": "Sky Sport Basket", "group": "SPORT"},
    "calcio": {"name": "Sky Sport Calcio", "group": "SPORT"},
    "f1": {"name": "Sky Sport F1", "group": "SPORT"},
    "golf": {"name": "Sky Sport Golf", "group": "SPORT"},
    "legend": {"name": "Sky Sport Legend", "group": "SPORT"},
    "sportmax": {"name": "Sky Sport Max", "group": "SPORT"},
    "sportmix": {"name": "Sky Sport Mix", "group": "SPORT"},
    "motogp": {"name": "Sky Sport MotoGP", "group": "SPORT"},
    "tennis": {"name": "Sky Sport Tennis", "group": "SPORT"},
    "sportuno": {"name": "Sky Sport Uno", "group": "SPORT"},
    "boomerang": {"name": "Boomerang", "group": "INTRATTENIMENTO"},
    "cartoonnetwork": {"name": "Cartoon Network", "group": "INTRATTENIMENTO"},
    "comedycentral": {"name": "Comedy Central", "group": "INTRATTENIMENTO"},
    "deakids": {"name": "DeAKids", "group": "INTRATTENIMENTO"},
    "nickeleodeon": {"name": "Nickelodeon", "group": "INTRATTENIMENTO"},
    "nickjunior": {"name": "Nick Jr", "group": "INTRATTENIMENTO"},
    "adventure": {"name": "Sky Adventure", "group": "INTRATTENIMENTO"},
    "arte": {"name": "Sky Arte", "group": "INTRATTENIMENTO"},
    "atlantic": {"name": "Sky Atlantic", "group": "INTRATTENIMENTO"},
    "crime": {"name": "Sky Crime", "group": "INTRATTENIMENTO"},
    "documentaries": {"name": "Sky Documentaries", "group": "INTRATTENIMENTO"},
    "nature": {"name": "Sky Nature", "group": "INTRATTENIMENTO"},
    "serie": {"name": "Sky Serie", "group": "INTRATTENIMENTO"},
    "uno": {"name": "Sky Uno", "group": "INTRATTENIMENTO"},
    "unoplus": {"name": "Sky Uno Plus", "group": "INTRATTENIMENTO"},
    "investigation": {"name": "Sky Investigation", "group": "INTRATTENIMENTO"}
}

def refresh_access_token():
    global ACCESS_TOKEN
    try:
        res = requests.post('https://oauth2.googleapis.com/token', data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': REFRESH_TOKEN,
            'grant_type': 'refresh_token'
        })
        data = res.json()
        if 'access_token' in data:
            ACCESS_TOKEN = data['access_token']
            return True
    except Exception:
        pass
    return False

def decode_ck(ck):
    try:
        pad = '=' * (4 - len(ck) % 4) if len(ck) % 4 else ''
        return base64.b64decode(ck + pad).decode('utf-8')
    except Exception:
        return None

def generate_m3u(channels):
    content = '#EXTM3U url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'
    group_map = {'SPORT': 'SkySport', 'CINEMA': 'Film - Serie TV', 'INTRATTENIMENTO': 'SkyEntertainment'}
    for ch in channels:
        grp = group_map.get(ch['group'], ch['group'])
        content += f'#EXTINF:-1 group-title="{grp}" tvg-id="{ch["name"]}",{ch["name"]}\n'
        if ch['clear_key']:
            content += f'#KODIPROP:inputstream.adaptive.license_type=org.w3.clearkey\n'
            content += f'#KODIPROP:inputstream.adaptive.license_key={ch["clear_key"]}\n'
        content += f'{ch["url"]}\n'
    return content

def main():
    channels = []
    total = len(CHANNEL_MAP)
    print("🔄 Avvio operazione scraping su Android...\n")

    for i, (slug, meta) in enumerate(CHANNEL_MAP.items(), 1):
        try:
            page_url = f"{BASE_URL}{slug}.php"
            res = requests.get(page_url, headers=HEADERS, timeout=5)
            if res.status_code == 200:
                match = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', res.text)
                if match:
                    raw_stream = match.group(1).replace(r'\/', '/')
                    clean_url = raw_stream.split('?')[0]
                    ck_match = re.search(r'ck=([^&]+)', raw_stream)
                    clear_key = decode_ck(ck_match.group(1)) if ck_match else None
                    channels.append({
                        'name': meta['name'],
                        'group': meta['group'],
                        'url': clean_url,
                        'clear_key': clear_key
                    })
                    print(f"[{i}/{total}] OK -> {meta['name']}")
                else:
                    print(f"[{i}/{total}] ⚠️ Nessun flusso -> {meta['name']}")
            else:
                print(f"[{i}/{total}] ❌ Errore HTTP {res.status_code} -> {meta['name']}")
        except Exception:
            print(f"[{i}/{total}] ❌ Errore rete -> {meta['name']}")

    if not channels:
        print("\n❌ Nessun canale estratto.")
        return

    print(f"\n✅ trovati {len(channels)} canali.")
    print("☁️ Connessione a Google Drive in corso...\n")

    m3u_content = generate_m3u(channels)

    if refresh_access_token():
        try:
            url = f"https://www.googleapis.com/upload/drive/v3/files/{DRIVE_FILE_ID}?uploadType=media"
            upload_headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'text/plain'
            }
            res = requests.patch(url, headers=upload_headers, data=m3u_content.encode('utf-8'))
            if res.status_code == 200:
                print("🚀 skympd.m3u inviato con successo")
            else:
                print(f"❌ Errore Google Drive: HTTP {res.status_code}")
        except Exception as e:
            print(f"❌ Errore durante l'upload: {e}")
    else:
        print("❌ Errore rinnovo token Google Drive.")

if __name__ == "__main__":
    main()