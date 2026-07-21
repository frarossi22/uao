from playwright.sync_api import sync_playwright
import time
import urllib.parse
import os
import base64
import re
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

CHANNELS = [
    {"name": "Sky Cinema Uno", "url": "https://uaznao.com/premium/canalitv/cinema1.php"},
    {"name": "Sky Cinema Stories", "url": "https://uaznao.com/premium/canalitv/cinemastories.php"},
    {"name": "Sky Cinema Family", "url": "https://uaznao.com/premium/canalitv/cinemafamily.php"},
    {"name": "Sky Cinema Comedy", "url": "https://uaznao.com/premium/canalitv/cinemacomedy.php"},
    {"name": "Sky Cinema Action", "url": "https://uaznao.com/premium/canalitv/cinemaaction.php"},
    {"name": "Sky Cinema Suspense", "url": "https://uaznao.com/premium/canalitv/cinemasuspense.php"},
    {"name": "Sky Cinema Collection", "url": "https://uaznao.com/premium/canalitv/cinemacollection.php"},
    {"name": "Sky Cinema Romance", "url": "https://uaznao.com/premium/canalitv/cinemaromance.php"},
    {"name": "Sky Cinema Drama", "url": "https://uaznao.com/premium/canalitv/cinemadrama.php"},
    {"name": "Sky Sport 24", "url": "https://uaznao.com/premium/canalitv/sport24.php"},
    {"name": "Sky Sport Uno", "url": "https://uaznao.com/premium/canalitv/sportuno.php"},
    {"name": "Sky Sport Calcio", "url": "https://uaznao.com/premium/canalitv/calcio.php"},
    {"name": "Sky Sport Arena", "url": "https://uaznao.com/premium/canalitv/arena.php"},
    {"name": "Sky Sport Max", "url": "https://uaznao.com/premium/canalitv/sportmax.php"},
    {"name": "Sky Sport Mix", "url": "https://uaznao.com/premium/canalitv/sportmix.php"},
    {"name": "Sky Sport F1", "url": "https://uaznao.com/premium/canalitv/f1.php"},
    {"name": "Sky Sport MotoGP", "url": "https://uaznao.com/premium/canalitv/motogp.php"},
    {"name": "Sky Sport 251", "url": "https://uaznao.com/premium/canalitv/sport251.php"},
    {"name": "Sky Sport 252", "url": "https://uaznao.com/premium/canalitv/sport252.php"},
    {"name": "Sky Sport 253", "url": "https://uaznao.com/premium/canalitv/sport253.php"},
    {"name": "Sky Uno", "url": "https://uaznao.com/premium/canalitv/uno.php"},
    {"name": "Sky Uno Plus", "url": "https://uaznao.com/premium/canalitv/unoplus.php"},
    {"name": "Sky Atlantic", "url": "https://uaznao.com/premium/canalitv/atlantic.php"},
    {"name": "Sky Serie", "url": "https://uaznao.com/premium/canalitv/serie.php"},
    {"name": "Sky Investigation", "url": "https://uaznao.com/premium/canalitv/investigation.php"},
    {"name": "Sky Crime", "url": "https://uaznao.com/premium/canalitv/crime.php"},
    {"name": "Sky Adventure", "url": "https://uaznao.com/premium/canalitv/adventure.php"},
    {"name": "Sky Nature", "url": "https://uaznao.com/premium/canalitv/nature.php"},
    {"name": "Sky Arte", "url": "https://uaznao.com/premium/canalitv/arte.php"},
    {"name": "Sky Documentaries", "url": "https://uaznao.com/premium/canalitv/documentaries.php"},
]

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    full = f"[{ts}] {msg}"
    print(full)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full + "\n")

def decodifica_chiave(ck_base64):
    try:
        decoded = base64.b64decode(ck_base64).decode('utf-8')
        match = re.search(r'([0-9a-fA-F]{32}):([0-9a-fA-F]{32})', decoded)
        if match:
            return f"{match.group(1)}:{match.group(2)}"
        return None
    except Exception as e:
        log(f"  Errore decodifica: {e}")
        return None

def estrai_mpd(page, url):
    mpd_url = None
    ck_base64 = None
    trovato = False

    def on_request(request):
        nonlocal mpd_url, ck_base64, trovato
        if trovato:
            return
        if ".mpd" in request.url and "ck=" in request.url:
            mpd_url = request.url
            parsed = urllib.parse.urlparse(request.url)
            params = urllib.parse.parse_qs(parsed.query)
            ck = params.get('ck', [None])[0]
            if ck:
                ck_base64 = ck
                trovato = True
                log(f"  ✅ MPD trovato con chiave")

    page.on("request", on_request)

    try:
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)

        content = page.content()
        patterns = [
            r'(https?://[^\s"\']+\.mpd[^\s"\']*ck=[A-Za-z0-9+/=]+[^\s"\']*)',
            r'(https?://[^\s"\']+\.mpd[^\s"\']*)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if "ck=" in match:
                    ck_match = re.search(r'ck=([A-Za-z0-9+/=]+)', match)
                    if ck_match:
                        mpd_url = match
                        ck_base64 = ck_match.group(1)
                        trovato = True
                        log(f"  ✅ MPD trovato nel contenuto")
                        break
            if trovato:
                break

        if not trovato:
            time.sleep(3)

    except Exception as e:
        log(f"  ❌ Errore: {e}")

    try:
        page.remove_listener("request", on_request)
    except:
        pass

    if not trovato:
        log(f"  ⚠️ Nessun MPD trovato")
        return None, None

    return mpd_url, ck_base64

def carica_su_drive(file_path, nome_file, folder_id=None):
    """Carica o aggiorna un file su Google Drive (sovrascrive se esiste)"""
    try:
        creds = Credentials(
            token=None,
            refresh_token=os.environ.get('GDRIVE_REFRESH_TOKEN'),
            client_id=os.environ.get('GDRIVE_CLIENT_ID'),
            client_secret=os.environ.get('GDRIVE_CLIENT_SECRET'),
            token_uri='https://oauth2.googleapis.com/token'
        )
        
        service = build('drive', 'v3', credentials=creds)
        
        # Cerca se il file esiste già
        query = f"name='{nome_file}' and trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        
        media = MediaFileUpload(file_path, resumable=True)
        
        if files:
            # Se esiste, lo aggiorna (sovrascrive)
            file_id = files[0]['id']
            service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
            log(f"✅ File aggiornato su Drive: {nome_file} (ID: {file_id})")
            log(f"🔗 Link: https://drive.google.com/file/d/{file_id}/view")
            return file_id
        else:
            # Se non esiste, lo carica come nuovo
            file_metadata = {'name': nome_file}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            new_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            log(f"✅ File caricato su Drive: {nome_file} (ID: {new_file.get('id')})")
            log(f"🔗 Link: https://drive.google.com/file/d/{new_file.get('id')}/view")
            return new_file.get('id')
    
    except Exception as e:
        log(f"❌ Errore caricamento su Drive: {e}")
        return None

def main():
    log("=" * 60)
    log("🎯 ESTRATTORE MPD CON PLAYWRIGHT")
    log(f"   Canali totali: {len(CHANNELS)}")
    log("=" * 60)

    risultati = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            for idx, canale in enumerate(CHANNELS, 1):
                nome = canale["name"]
                url = canale["url"]
                log(f"\n[{idx}/{len(CHANNELS)}] 🔍 {nome}")

                page = context.new_page()
                mpd, ck = estrai_mpd(page, url)
                page.close()

                if mpd and ck:
                    decoded = decodifica_chiave(ck)
                    if decoded:
                        risultati.append({
                            "name": nome,
                            "mpd": mpd,
                            "ck": ck,
                            "decoded_key": decoded
                        })
                        log(f"  ✅ Chiave: {decoded}")
                    else:
                        log(f"  ❌ Chiave non decodificabile")
                else:
                    log(f"  ❌ MPD non trovato")

                if idx < len(CHANNELS):
                    delay = 3
                    log(f"  ⏳ Attendo {delay}s...")
                    time.sleep(delay)

            browser.close()

    except Exception as e:
        log(f"❌ Errore Playwright: {e}")
        return

    if not risultati:
        log("\n❌ Nessun MPD estratto!")
        return

    # Salva riepilogo txt
    txt_file = f"estrazione_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("RIEPILOGO MPD\n" + "=" * 50 + "\n\n")
        for r in risultati:
            f.write(f"Canale: {r['name']}\n")
            f.write(f"MPD: {r['mpd']}\n")
            f.write(f"CK: {r['ck']}\n")
            f.write(f"Chiave: {r['decoded_key']}\n")
            f.write("-" * 30 + "\n")
    log(f"\n📄 Riepilogo salvato in {txt_file}")

    # Genera playlist M3U
    header = '#EXTM3U url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n'
    lines = [header]
    for r in risultati:
        if "Sport" in r['name']:
            group = "Sport"
        elif "Cinema" in r['name']:
            group = "Film - Serie TV"
        else:
            group = "Intrattenimento"

        tvg_id = r['name'].lower().replace(' ', '.')
        lines.append(f'#EXTINF:-1 group-title="{group}" tvg-id="{tvg_id}" tvg-logo="" ,{r["name"]}\n')
        lines.append('#KODIPROP:inputstream.adaptive.license_type=org.w3.clearkey\n')
        lines.append(f'#KODIPROP:inputstream.adaptive.license_key={r["decoded_key"]}\n')
        lines.append(r['mpd'] + '\n')

    playlist_file = "playlist.m3u"
    with open(playlist_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    log(f"\n✅ playlist.m3u generata ({len(risultati)} canali)")
    log(f"📁 File salvati localmente: {playlist_file}")
    
    # 🔥 CARICA SU GOOGLE DRIVE (SOVRASCRIVE SE ESISTE)
    log("📤 Caricamento playlist.m3u su Google Drive...")
    drive_file_id = carica_su_drive(playlist_file, "playlist.m3u")
    if drive_file_id:
        log(f"✅ Playlist caricata/aggiornata con successo!")
    
    log(f"📝 Log dettagliato: {LOG_FILE}")

if __name__ == "__main__":
    main()
