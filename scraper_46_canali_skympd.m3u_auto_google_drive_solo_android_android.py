import base64
import re
import requests
import time
import os

# Credenziali Google Drive
CLIENT_ID = os.environ.get("CLIENT_ID", "360991432021-p5qnc2i8jg8vcnv12o33n74cnjl4bk5q.apps.googleusercontent.com")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "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")
DRIVE_FILE_ID = os.environ.get("DRIVE_FILE_ID", "1w6LgRLFOmEYD88fXYlwwhzbBFZ210JG_")
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN", "1//04SFIkmoK5XT4CgYIARAAGAQSNwF-L9IrfgX8z4LgUKT_jsT1BSaCVZ2DO8k2AqpaLcYMZ_MqQvg5SRj6cSmWE0uG3AtU1Egv1kA")

ACCESS_TOKEN = ""
BASE_URL = "https://uaznao.com/premium/canalitv/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CHANNEL_MAP = {
    # SKY CINEMA
    "cinemaaction": {"name": "Sky Cinema Action", "group": "CINEMA"},
    "cinemacollection": {"name": "Sky Cinema Collection", "group": "CINEMA"},
    "cinemacomedy": {"name": "Sky Cinema Comedy", "group": "CINEMA"},
    "cinemadrama": {"name": "Sky Cinema Drama", "group": "CINEMA"},
    "cinemaromance": {"name": "Sky Cinema Romance", "group": "CINEMA"},
    "cinemastories": {"name": "Sky Cinema Stories", "group": "CINEMA"},
    "cinemasuspense": {"name": "Sky Cinema Suspense", "group": "CINEMA"},
    "cinema1": {"name": "Sky Cinema Uno", "group": "CINEMA"},
    "cinemafamily": {"name": "Sky Cinema Family", "group": "CINEMA"},
    # SKY SPORT
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
    # DAZN
    "daznch/player_event.php?event=1": {"name": "DAZN 1", "group": "DAZN"},
    "daznch/player_event.php?event=2": {"name": "DAZN 2", "group": "DAZN"},
    "daznch/player_event.php?event=3": {"name": "DAZN 3", "group": "DAZN"},
    "daznch/player_event.php?event=4": {"name": "DAZN 4", "group": "DAZN"},
    "daznch/player_event.php?event=5": {"name": "DAZN 5", "group": "DAZN"},
    "daznch/player_event.php?event=6": {"name": "DAZN 6", "group": "DAZN"},
    "daznch/player_event.php?event=7": {"name": "DAZN 7", "group": "DAZN"},
    "daznch/player_event.php?event=8": {"name": "DAZN 8", "group": "DAZN"},
    "daznch/player_event.php?event=9": {"name": "DAZN 9", "group": "DAZN"},
    "daznch/player_event.php?event=10": {"name": "DAZN 10", "group": "DAZN"},
    # INTRATTENIMENTO
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
    "investigation": {"name": "Sky Investigation", "group": "INTRATTENIMENTO"},
}


def refresh_access_token():
    global ACCESS_TOKEN
    try:
        res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
        )
        data = res.json()
        if "access_token" in data:
            ACCESS_TOKEN = data["access_token"]
            return True
    except Exception:
        pass
    return False


def decode_ck(ck):
    try:
        pad = "=" * (4 - len(ck) % 4) if len(ck) % 4 else ""
        return base64.b64decode(ck + pad).decode("utf-8")
    except Exception:
        return None


def decode_z32(mpd_url):
    try:
        match = re.search(r"z32=([^&]+)", mpd_url)
        if match:
            encoded_str = match.group(1)
            padding = len(encoded_str) % 4
            if padding:
                encoded_str += "=" * (4 - padding)
            decoded_bytes = base64.b64decode(encoded_str)
            decoded_hex = decoded_bytes.hex()
            if len(decoded_hex) >= 64:
                kid = decoded_hex[:32]
                key = decoded_hex[32:64]
                return f"{kid}:{key}"
    except Exception:
        pass
    return None


def generate_m3u(channels):
    content = (
        "#EXTM3U"
        ' url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'
    )
    group_map = {
        "SPORT": "SkySport",
        "CINEMA": "Film - Serie TV",
        "INTRATTENIMENTO": "SkyEntertainment",
        "DAZN": "DAZN",
    }
    
    for ch in channels:
        grp = group_map.get(ch["group"], ch["group"])
        content += f'#EXTINF:-1 group-title="{grp}" tvg-id="{ch["name"]}",{ch["name"]}\n'

        if ch["group"] == "DAZN":
            content += "#KODIPROP:inputstream.adaptive.license_type=playready\n"
            if ch["license_key"]:
                content += f'#KODIPROP:inputstream.adaptive.license_key={ch["license_key"]}\n'
        else:
            if ch["clear_key"]:
                content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
                content += f'#KODIPROP:inputstream.adaptive.license_key={ch["clear_key"]}\n'

        content += f'{ch["url"]}\n'
    return content


def main():
    channels = []
    total = len(CHANNEL_MAP)
    print("🔄 Avvio operazione scraping...\n")

    for i, (path, meta) in enumerate(CHANNEL_MAP.items(), 1):
        try:
            if path.startswith("daznch/"):
                page_url = f"{BASE_URL}{path}"
            else:
                page_url = f"{BASE_URL}{path}.php"

            print(f"[{i}/{total}] 📡 {meta['name']}")
            
            res = requests.get(page_url, headers=HEADERS, timeout=10)
            
            if res.status_code == 200:
                if meta["group"] == "DAZN":
                    mpd_match = re.search(
                        r'https?://[^\s"\'<>]+?\.mpd[^\s"\'<>]*', res.text
                    )
                    if mpd_match:
                        mpd_url = mpd_match.group(0)
                        license_key = decode_z32(mpd_url)
                        channels.append({
                            "name": meta["name"],
                            "group": meta["group"],
                            "url": mpd_url,
                            "clear_key": None,
                            "license_key": license_key,
                        })
                        if license_key:
                            print(f"  ✅ OK (DAZN) -> kid:key estratto")
                        else:
                            print(f"  ✅ OK (DAZN) -> senza kid:key (offline?)")
                    else:
                        print(f"  ⚠️ Nessun MPD DAZN -> {meta['name']}")
                else:
                    match = re.search(r'const\s+STREAM_URL\s*=\s*"([^"]+)"', res.text)
                    if match:
                        raw_stream = match.group(1).replace(r"\/", "/")
                        clean_url = raw_stream.split("?")[0]
                        ck_match = re.search(r"ck=([^&]+)", raw_stream)
                        clear_key = decode_ck(ck_match.group(1)) if ck_match else None
                        channels.append({
                            "name": meta["name"],
                            "group": meta["group"],
                            "url": clean_url,
                            "clear_key": clear_key,
                            "license_key": None,
                        })
                        print(f"  ✅ OK")
                    else:
                        print(f"  ⚠️ Nessun flusso -> {meta['name']}")
            else:
                print(f"  ❌ Errore HTTP {res.status_code}")
                
        except Exception as e:
            print(f"  ❌ Errore rete: {e}")
        
        time.sleep(0.3)

    if not channels:
        print("\n❌ Nessun canale estratto.")
        return

    print(f"\n✅ Trovati {len(channels)} canali.")
    print("☁️ Connessione a Google Drive in corso...\n")

    m3u_content = generate_m3u(channels)

    if refresh_access_token():
        try:
            url = f"https://www.googleapis.com/upload/drive/v3/files/{DRIVE_FILE_ID}?uploadType=media"
            upload_headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "text/plain",
            }
            res = requests.patch(
                url, headers=upload_headers, data=m3u_content.encode("utf-8")
            )
            if res.status_code == 200:
                print("=" * 55)
                print("✅ skympd.m3u inviato con successo su Google Drive!")
                print("=" * 55)
            else:
                print(f"❌ Errore Google Drive: HTTP {res.status_code}")
        except Exception as e:
            print(f"❌ Errore durante l'upload: {e}")
    else:
        print("❌ Errore rinnovo token Google Drive.")


if __name__ == "__main__":
    main()
