<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>WebTV – Player MPD & ClearKey Definitivo</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/shaka-player/4.12.16/shaka-player.ui.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.1/dist/hls.min.js"></script>

<style>
* { user-select: none; box-sizing: border-box; }
body { font-family: 'Segoe UI', Roboto, Arial; background: #0f0f0f; color: #e0e0e0; margin: 0; display: flex; flex-direction: column; align-items: center; overflow: hidden; height: 100vh; }
.main-container { display: flex; flex-direction: column; width: 100%; flex: 1; overflow: hidden; position: relative; }
.video-section { position: relative; width: 100%; height: 100vh; display: flex; align-items: center; justify-content: center; background: #000; }
video { width: 100%; height: 100%; object-fit: contain; background: #000; }
.channel-left { position: absolute; bottom: 120px; left: 0; z-index: 20; pointer-events: none; transition: opacity 0.3s ease-out; opacity: 1; padding-left: 20px; }
.channel-left.hide { opacity: 0; }
@keyframes slideInLeft { from { transform: translateX(-30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
.channel-name-large { font-size: 3.5rem; font-weight: bold; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); letter-spacing: 1px; margin-bottom: 6px; white-space: nowrap; }
.channel-epg-info { font-size: 1rem; color: rgba(255,255,255,0.8); text-shadow: 1px 1px 2px rgba(0,0,0,0.5); max-width: 400px; white-space: nowrap; }
.nav-hint { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.6); backdrop-filter: blur(5px); padding: 8px 16px; border-radius: 30px; font-size: 0.7rem; color: #aaa; z-index: 30; pointer-events: none; white-space: nowrap; transition: opacity 1s ease-out; opacity: 1; }
.nav-hint.hide { opacity: 0; }
.loading-overlay { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,0,0,0.85); padding: 24px 32px; border-radius: 14px; z-index: 100; display: none; text-align: center; }
.loading-overlay.active { display: block; }
.loading-overlay .spinner { width: 36px; height: 36px; border: 4px solid rgba(0,212,255,0.2); border-top-color: #00d4ff; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 12px; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-overlay .load-text { font-size: 0.9rem; color: #ccc; }
.loading-overlay .load-progress { font-size: 0.75rem; color: #00d4ff; margin-top: 6px; }

.bottom-left { position: fixed; bottom: 20px; left: 20px; z-index: 25; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.group-selector { background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); padding: 8px 15px; border-radius: 30px; border: 1px solid #00d4ff; }
#group-menu { background: transparent; color: #00d4ff; border: none; font-size: 0.9rem; cursor: pointer; outline: none; }
#group-menu option { background: #1a1a1a; color: #e0e0e0; }

.drive-status-box {
    background: rgba(0,40,10,0.95); backdrop-filter: blur(10px); border: 2px solid #28a745; color: #28a745;
    padding: 8px 16px; border-radius: 30px; font-size: 0.8rem; font-weight: bold;
    box-shadow: 0 0 20px rgba(40,167,69,0.3); animation: slideInLeft 0.5s ease-out;
    display: none; white-space: nowrap; cursor: pointer; transition: all 0.3s;
}
.drive-status-box.active { display: block !important; }
.drive-status-box:hover { transform: scale(1.05); box-shadow: 0 0 30px rgba(40,167,69,0.5); }
.drive-status-box.error { border-color: #dc3545; color: #dc3545; background: rgba(40,10,10,0.95); box-shadow: 0 0 20px rgba(220,53,69,0.3); }
.drive-status-box.loading { border-color: #ffc107; color: #ffc107; background: rgba(40,40,10,0.95); box-shadow: 0 0 20px rgba(255,193,7,0.3); }
.drive-status-box .drive-icon { margin-right: 6px; }
.confirm-box {
    background: rgba(0,40,10,0.95); backdrop-filter: blur(10px); border: 2px solid #28a745; color: #28a745;
    padding: 8px 16px; border-radius: 30px; font-size: 0.8rem; font-weight: bold;
    box-shadow: 0 0 20px rgba(40,167,69,0.3); animation: slideInLeft 0.5s ease-out;
    display: none; white-space: nowrap; transition: all 0.3s;
}
.confirm-box.active { display: block !important; }
.status-bar {
    position: fixed; bottom: 60px; left: 50%; transform: translateX(-50%);
    background: rgba(0,0,0,0.7); backdrop-filter: blur(10px);
    padding: 6px 16px; border-radius: 20px; font-size: 0.7rem; color: #888;
    z-index: 25; white-space: nowrap; display: none;
}
.count-badge { position: fixed; top: 20px; left: 20px; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); padding: 6px 12px; border-radius: 20px; font-size: 0.75rem; z-index: 25; }
.reload-btn { position: fixed; bottom: 80px; right: 20px; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); padding: 10px 18px; border-radius: 30px; font-size: 0.75rem; z-index: 25; border: 1px solid #00d4ff; color: #00d4ff; cursor: pointer; transition: all 0.3s; font-weight: bold; }
.reload-btn:hover { background: rgba(0,212,255,0.2); border-color: #00d4ff; box-shadow: 0 0 20px rgba(0,212,255,0.3); }

.log-btn {
    position: fixed; top: 20px; right: 20px; z-index: 40;
    background: rgba(0,0,0,0.75); backdrop-filter: blur(10px);
    border: 1px solid #4ade80; color: #4ade80;
    padding: 8px 14px; border-radius: 20px; font-size: 0.75rem; font-weight: bold;
    cursor: pointer; transition: all 0.3s;
}
.log-btn:hover { background: rgba(74,222,128,0.2); box-shadow: 0 0 20px rgba(74,222,128,0.4); }

.log-panel {
    position: fixed; top: 60px; right: 20px; z-index: 45;
    width: 460px; max-width: 92vw; max-height: 78vh;
    background: rgba(10,10,10,0.97); backdrop-filter: blur(12px);
    border: 2px solid #4ade80; border-radius: 12px;
    box-shadow: 0 0 40px rgba(74,222,128,0.3);
    display: none; overflow: hidden; flex-direction: column;
}
.log-panel.active { display: flex; }
.log-panel-header {
    background: rgba(74,222,128,0.15); padding: 10px 14px;
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid rgba(74,222,128,0.3);
    font-size: 0.85rem; font-weight: bold; color: #4ade80;
}
.log-panel-header button {
    background: transparent; border: none; color: #4ade80;
    font-size: 1rem; cursor: pointer; padding: 0 4px;
}
.log-panel-body {
    padding: 14px 16px;
    overflow-y: auto;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 0.78rem;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-all;
}
.log-line { display: block; }
.log-line .k { color: #ffffff; }
.log-line .v { color: #4ade80; }
.log-title {
    color: #4ade80;
    font-weight: bold;
    font-size: 0.7rem;
    letter-spacing: 1px;
    margin: 0 0 8px 0;
    display: block;
    text-transform: uppercase;
}

@media (max-width: 768px) {
    .channel-name-large { font-size: 2rem; white-space: normal; word-break: break-word; }
    .channel-epg-info { font-size: 0.75rem; max-width: 250px; white-space: normal; }
    .channel-left { left: 0; bottom: 100px; max-width: 85%; padding-left: 15px; }
    .bottom-left { bottom: 15px; left: 10px; gap: 6px; }
    .group-selector { padding: 6px 12px; }
    #group-menu { font-size: 0.75rem; }
    .count-badge { top: 15px; left: 10px; font-size: 0.6rem; padding: 4px 10px; }
    .nav-hint { bottom: 70px; font-size: 0.6rem; padding: 5px 12px; }
    .reload-btn { bottom: 70px; right: 10px; padding: 8px 14px; font-size: 0.65rem; }
    .drive-status-box { font-size: 0.65rem; padding: 6px 12px; }
    .confirm-box { font-size: 0.65rem; padding: 6px 12px; }
    .status-bar { bottom: 50px; font-size: 0.6rem; padding: 4px 12px; }
    .log-btn { top: 15px; right: 10px; font-size: 0.65rem; padding: 6px 10px; }
    .log-panel { top: 50px; right: 8px; left: 8px; width: auto; max-height: 70vh; }
    .log-panel-body { font-size: 0.7rem; }
}
</style>
</head>

<body>

<div class="main-container">
    <div class="video-section">
        <video id="video" controls autoplay preload="metadata"></video>
        <div class="channel-left" id="channelLeft">
            <div class="channel-name-large" id="currentChannelName"></div>
            <div class="channel-epg-info" id="currentChannelEpg">Caricamento canali...</div>
        </div>
    </div>
</div>

<button class="log-btn" id="logBtn" onclick="toggleLog()">📋 LOG</button>

<div class="log-panel" id="logPanel">
    <div class="log-panel-header">
        <span>📋 LOG CANALE</span>
        <button onclick="toggleLog()">✕</button>
    </div>
    <div class="log-panel-body" id="logBody">Nessun canale caricato.</div>
</div>

<div class="bottom-left">
    <div class="group-selector">
        <select id="group-menu">
            <option value="Tutti">Tutti</option>
        </select>
    </div>
    <div class="drive-status-box" id="driveStatusBox" onclick="uploadToDrive()">
        <span class="drive-icon">☁️</span> Invia a Drive
    </div>
    <div class="confirm-box" id="confirmBox">
        ✅ Playlist inviata con successo
    </div>
</div>

<div class="count-badge" id="countBadge">Caricamento...</div>
<button class="reload-btn" onclick="loadAllChannels()">🔄 Ricarica</button>
<div class="status-bar" id="statusBar"></div>

<div class="nav-hint" id="navHint">🖱️ Rotella | ⌨️ Frecce | 👆 Swipe</div>

<div class="loading-overlay" id="loadingOverlay">
    <div class="spinner"></div>
    <div class="load-text" id="loadText">Caricamento canali...</div>
    <div class="load-progress" id="loadProgress"></div>
</div>

<script>
const CLIENT_ID = "360991432021-p5qnc2i8jg8vcnv12o33n74cnjl4bk5q.apps.googleusercontent.com";
const CLIENT_SECRET = "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";
const DRIVE_FILE_ID = "1w6LgRLFOmEYD88fXYlwwhzbBFZ210JG_";
const REFRESH_TOKEN = "1//04SFIkmoK5XT4CgYIARAAGAQSNwF-L9IrfgX8z4LgUKT_jsT1BSaCVZ2DO8k2AqpaLcYMZ_MqQvg5SRj6cSmWE0uG3AtU1Egv1kA";

let ACCESS_TOKEN = "";
let lastM3UContent = '';
let isUploading = false;

const CORS_PROXY = 'https://cors.io/?url=';
const BASE_URL = 'https://uaznao.com/premium/canalitv/';
const EPG_URL = 'https://raw.githubusercontent.com/qwertyuiop8899/TV/refs/heads/main/epg.xml';

const CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

const CHANNEL_MAP = {
    "rai1": { name: "Rai 1", group: "Rai", directUrl: "https://raiuno3-live.akamaized.net/hls/live/2017910/raiuno3/raiuno3/playlist.m3u8" },
    "rai2": { name: "Rai 2", group: "Rai", directUrl: "https://raidue3-live.akamaized.net/hls/live/2017983/raidue3/raidue3/playlist.m3u8" },
    "rai3": { name: "Rai 3", group: "Rai", directUrl: "https://raitre3-live.akamaized.net/hls/live/2018002/raitre3/raitre3/playlist.m3u8" },
    "rete4": { name: "Rete 4", group: "Mediaset", directUrl: "https://live03-col.msf.cdn.mediaset.net/live/ch-r4/r4-clr.isml/manifest.mpd" },
    "canale5": { name: "Canale 5", group: "Mediaset", directUrl: "https://live03-col.msf.cdn.mediaset.net/live/ch-c5/c5-clr.isml/manifest.mpd" },
    "italia1": { name: "Italia 1", group: "Mediaset", directUrl: "https://live03-col.msf.cdn.mediaset.net/live/ch-i1/i1-clr.isml/manifest.mpd" },
    "grandefratello": { name: "Grande Fratello", group: "Mediaset", directUrl: "https://live02-col.msf.cdn.mediaset.net/live/ch-b7/b7-clr.isml/index.m3u8" },

    "rsi1": { name: "RSI La 1 HD", group: "RSI", directUrl: "https://wp3-s-anp31323132-live-ch-prod.prod.cdn.dmdsdp.com/live/disk1/SV09042/stb-dash-fhd-avc/SV09042.mpd", clearKeys: { "09af5f6eb89041ca8f5d164165142e86": "1989cc9c9ce5b2b52cb93edaaefe8420", "d268d810d8a73bd8b7d54a6a087581d2": "1aaf297543168c625e05aa9e27344471" } },
    "rsi2": { name: "RSI La 2 HD", group: "RSI", directUrl: "https://wp2-s-anp31323132-live-ch-prod.prod.cdn.dmdsdp.com/live/disk1/SV09043/stb-dash-fhd-avc/SV09043.mpd", clearKeys: { "117d07fd98cc46ef8e09936d0d37c506": "b9528cb3f23eaad789f0f33bf6b01868", "166b2f0d56fb32d9b46d4b1ca1b5bf16": "d78ee5c91eb3b9b6d37414a4f789bc9b" } },

    "cinema1": { name: "Sky Cinema Uno", group: "Sky Cinema" },
    "cinemastories": { name: "Sky Cinema Stories", group: "Sky Cinema" },
    "cinemafamily": { name: "Sky Cinema Family", group: "Sky Cinema" },
    "cinemacomedy": { name: "Sky Cinema Comedy", group: "Sky Cinema" },
    "cinemaaction": { name: "Sky Cinema Action", group: "Sky Cinema" },
    "cinemasuspense": { name: "Sky Cinema Suspense", group: "Sky Cinema" },
    "cinemaromance": { name: "Sky Cinema Romance", group: "Sky Cinema" },
    "cinemacollection": { name: "Sky Cinema Collection", group: "Sky Cinema" },
    "cinemadrama": { name: "Sky Cinema Drama", group: "Sky Cinema" },

    "sport24": { name: "Sky Sport 24", group: "Sky Sport" },
    "sportuno": { name: "Sky Sport Uno", group: "Sky Sport" },
    "calcio": { name: "Sky Sport Calcio", group: "Sky Sport" },
    "arena": { name: "Sky Sport Arena", group: "Sky Sport" },
    "sportmax": { name: "Sky Sport Max", group: "Sky Sport" },
    "sportmix": { name: "Sky Sport Mix", group: "Sky Sport" },
    "legend": { name: "Sky Sport Legend", group: "Sky Sport" },
    "f1": { name: "Sky Sport F1", group: "Sky Sport" },
    "motogp": { name: "Sky Sport MotoGP", group: "Sky Sport" },
    "tennis": { name: "Sky Sport Tennis", group: "Sky Sport" },
    "basket": { name: "Sky Sport Basket", group: "Sky Sport" },
    "golf": { name: "Sky Sport Golf", group: "Sky Sport" },
    "amazonlive": { name: "Amazon Live", group: "Sky Sport" },
    "sport251": { name: "Sky Sport 251", group: "Sky Sport" },
    "sport252": { name: "Sky Sport 252", group: "Sky Sport" },
    "sport253": { name: "Sky Sport 253", group: "Sky Sport" },
    "sport254": { name: "Sky Sport 254", group: "Sky Sport" },
    "sport255": { name: "Sky Sport 255", group: "Sky Sport" },
    "sport256": { name: "Sky Sport 256", group: "Sky Sport" },
    "sport257": { name: "Sky Sport 257", group: "Sky Sport" },
    "sport258": { name: "Sky Sport 258", group: "Sky Sport" },
    "sport259": { name: "Sky Sport 259", group: "Sky Sport" },

    "uno": { name: "Sky Uno", group: "Intrattenimento" },
    "unoplus": { name: "Sky Uno Plus", group: "Intrattenimento" },
    "atlantic": { name: "Sky Atlantic", group: "Intrattenimento" },
    "serie": { name: "Sky Serie", group: "Intrattenimento" },
    "investigation": { name: "Sky Investigation", group: "Intrattenimento" },
    "crime": { name: "Sky Crime", group: "Intrattenimento" },
    "adventure": { name: "Sky Adventure", group: "Intrattenimento" },
    "nature": { name: "Sky Nature", group: "Intrattenimento" },
    "arte": { name: "Sky Arte", group: "Intrattenimento" },
    "documentaries": { name: "Sky Documentaries", group: "Intrattenimento" },
    "comedycentral": { name: "Comedy Central", group: "Intrattenimento" },
    "deakids": { name: "DeAKids", group: "Intrattenimento" },
    "nickjunior": { name: "Nick Jr", group: "Intrattenimento" },
    "nickeleodeon": { name: "Nickelodeon", group: "Intrattenimento" },
    "cartoonnetwork": { name: "Cartoon Network", group: "Intrattenimento" },
    "boomerang": { name: "Boomerang", group: "Intrattenimento" },

    "daznch/player_event.php?event=1": { name: "DAZN 1", group: "DAZN CH" },
    "daznch/player_event.php?event=2": { name: "DAZN 2", group: "DAZN CH" },
    "daznch/player_event.php?event=3": { name: "DAZN 3", group: "DAZN CH" },
    "daznch/player_event.php?event=4": { name: "DAZN 4", group: "DAZN CH" },
    "daznch/player_event.php?event=5": { name: "DAZN 5", group: "DAZN CH" },
    "daznch/player_event.php?event=6": { name: "DAZN 6", group: "DAZN CH" },
    "daznch/player_event.php?event=7": { name: "DAZN 7", group: "DAZN CH" },
    "daznch/player_event.php?event=8": { name: "DAZN 8", group: "DAZN CH" },
    "daznch/player_event.php?event=9": { name: "DAZN 9", group: "DAZN CH" },
    "daznch/player_event.php?event=10": { name: "DAZN 10", group: "DAZN CH" },

    "blusport/player_event.php?event=1": { name: "Blu Sport 1", group: "BluSport" },
    "blusport/player_event.php?event=2": { name: "Blu Sport 2", group: "BluSport" },
    "blusport/player_event.php?event=3": { name: "Blu Sport 3", group: "BluSport" },
    "blusport/player_event.php?event=4": { name: "Blu Sport 4", group: "BluSport" },
    "blusport/player_event.php?event=5": { name: "Blu Sport 5", group: "BluSport" },
    "blusport/player_event.php?event=6": { name: "Blu Sport 6", group: "BluSport" },
    "blusport/player_event.php?event=7": { name: "Blu Sport 7", group: "BluSport" },
    "blusport/player_event.php?event=8": { name: "Blu Sport 8", group: "BluSport" },
    "blusport/player_event.php?event=9": { name: "Blu Sport 9", group: "BluSport" },
    "blusport/player_event.php?event=10": { name: "Blu Sport 10", group: "BluSport" },

    "premiersports1_uk": { name: "Premier Sports 1 [UK]", group: "Premier Sport", directUrl: "https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/m6sqanvm2m/out/v1/f6beb46c6e9a4132ad739f3ca27df6aa/cenc.mpd?ck=MTQ0NGY0MjM1NTI5ZjE4M2YwYTVhNDg2YmVmZTljZGI6ZTVlM2ZlYzY3YTFiYjM0NzJhMjA4OWM4YTBhMjU1N2Y=" },
    "premiersports2_uk": { name: "Premier Sports 2 [UK]", group: "Premier Sport", directUrl: "https://a151aivottlinear-a.akamaihd.net/OTTB/sin-nitro/live/dash/enc/bcj3iscpd6/out/v1/fcd137b391214f7cb99dd4d7be90ca87/cenc.mpd?ck=MWE1ZGY1MzYwOWViYzk4NTc4OThjNDkwZjQ3MjQ5MTg6NzdmNjI5ODBkNTgyZWM1NDEyODA3OTZhY2Y4YjJkMTk=" },

    "sport1_cz": { 
        name: "SPORT 1 [CZ]", group: "SPORT CZ", 
        directUrl: "https://dash2.antik.sk/stream/nvidia_sport_1/playlist_cbcs.mpd", 
        clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" },
        m3uUrl: "https://dash3.antik.sk/stream/nvidia_sport_1/playlist_cbcs.mpd",
        m3uWidevine: "https://drm.antik.sk/widevine/key"
    },
    "sport2_cz": { 
        name: "SPORT 2 [CZ]", group: "SPORT CZ", 
        directUrl: "https://dash3.antik.sk/stream/nvidia_sport2/playlist_cbcs.mpd", 
        clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" },
        m3uUrl: "https://dash4.antik.sk/stream/nvidia_sport2/playlist_cbcs.mpd",
        m3uWidevine: "https://drm.antik.sk/widevine/key"
    },

    "eleven4k": { name: "Eleven Sport 4K", group: "ELEVEN SPORT", directUrl: "https://lb2.pluscdn.pl/ch/1522637/357/dash/b929c9fb/live.mpd", clearKeys: { "ef5e40e00d43450bbeeb40c6849e0309": "614c349de0e08585c7b503568cacd5a1" } },
    "eleven1": { name: "Eleven Sports 1", group: "ELEVEN SPORT", directUrl: "https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports1/default/index.mpd", clearKeys: { "4853dbe4c4cf51f3ba95424c6e6f69c7": "39c0346198bc9b1614eb319115afdb84", "751db0bb03145084973c6cf9c85fa16e": "6571153c39eed18c29cdc63eb83c553a", "fd9b5f8ae64a51edacd4f245ef515287": "c867d24646b170b5c0e0556b56b291d7" } },
    "eleven2": { name: "Eleven Sports 2", group: "ELEVEN SPORT", directUrl: "https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports2/default/index.mpd", clearKeys: { "a118a928ea39552f976c8fad437f71ad": "f58fb7a53ee86de9d0b9823446ba9756", "78f826af752f54ddbc4ad9959ff2a42d": "c1479ffada263000730d627a989e96ab", "95c2aefadb7e522c9deeed393207f853": "16e857224e16ab01a3c549212cdbdbb8" } },
    "eleven3": { name: "Eleven Sports 3", group: "ELEVEN SPORT", directUrl: "https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports3/default/index.mpd", clearKeys: { "d895d50a5a0f55758d31f247e6743815": "9f4882e56631edb0da1c7bf1e0fa4904", "e3a9d5c27a6d5eac955daf5a1a640c69": "4c2e674f97ff33c5de13032b92e78bc9", "e3dd9d531eee578fbd08c87de8ab84d5": "133e5a170236f4ba5930f5ba4213ee03" } },
    "eleven4": { name: "Eleven Sports 4", group: "ELEVEN SPORT", directUrl: "https://lineartv-cdn.t-mobile.pl/bpk-tv/elevensports4/default/index.mpd", clearKeys: { "37b0bbf897ad5bd5a3ec19b5a91f54f9": "3e84e6b93e19197d5aea59ef8ad9d270", "54a7d8f8dbee564981beb470f22b529b": "a0e341fec141f8733c0805f5480762ba", "14e62b5f16385a139e2a1c747b8b1cc4": "0cece074b5f3fabc76fc9ed109b3819d" } },

    "comotv1": { name: "Como TV 1", group: "COMO TV", directUrl: "https://comofootball.mocdn.tv/out/v1/ac7a76c678594a03a8e05392a796f125/index_L1.m3u8" },
    "comotv2": { name: "Como TV 2", group: "COMO TV", directUrl: "https://comofootball.mocdn.tv/out/v1/c10b9e41c1a34a598cb5e9a345b3a325/index_L1.m3u8" },
    "comotv3": { name: "Como TV 3", group: "COMO TV", directUrl: "https://comofootball.mocdn.tv/out/v1/ffb389a49afc49338e2cc17724a649aa/index_L1.m3u8" },
    "comotv4": { name: "Como TV 4", group: "COMO TV", directUrl: "https://comofootball.mocdn.tv/out/v1/617c01e7d8c241d2b1152decbfa60339/index_L1.m3u8" },
    "comotv5": { name: "Como TV 5", group: "COMO TV", directUrl: "https://comofootball.mocdn.tv/out/v1/e8d4fec57cd24447babe9fbe0151007c/index_L1.m3u8" },

    "cbssport": {
        name: "CbsSport Mpd", group: "CBS Sport",
        directUrl: "https://abfjk4haaaaaaaampv6ofhkihi4r6.bia-cf.live.pv-cdn.net/lhr-nitro/live/clients/dash/enc/rbem8rorcw/out/v1/5318821e2c3c44c2a439681b9aa86e9b/cenc.mpd",
        clearKeys: { "d9623774ac5c8c351aafe97c5fe70267": "5164e6d05164a2d65fa8fcc962aa4861" },
        headers: { "User-Agent": CHROME_UA }
    },

    "foxsport1": { name: "FOXChannel Sport", group: "FOX SPORT", directUrl: "https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/oboxe53wyo/out/v1/f7892a9d706d419a846d738fa22ea33e/cenc.mpd", clearKeys: { "2fbdaa3bea0d0323ae011b318d1db716": "8726ef7eaf5b9dce15fb6aa9f80bd53f" }, headers: { "User-Agent": CHROME_UA } },
    "foxsport2": { name: "FOXChannel Sport 2", group: "FOX SPORT", directUrl: "https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/tepjqej1ys/out/v1/c9c9159baee749a19612b1598495859a/cenc.mpd", clearKeys: { "8836fb04d62dc64c9f8a39ef8640d5eb": "d4f05ce56c5231b7cdf53455bea58621" }, headers: { "User-Agent": CHROME_UA } },
    "foxsport3": { name: "FOXChannel Sport 3", group: "FOX SPORT", directUrl: "https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/wybgz0orr8/out/v1/2f6d1612abd44f5883917f8a585b955f/cenc.mpd", clearKeys: { "11c8c1c2ef0385cf1e64d44bb9c3a395": "5769730ffbdc4b2fd8945929d9ace063" }, headers: { "User-Agent": CHROME_UA } },
    "foxsportpremium": { name: "FOXChannel Sport PREMIUM", group: "FOX SPORT", directUrl: "https://otte.live.fly.ww.aiv-cdn.net/dub-nitro/live/dash/enc/fdx74zqzhu/out/v1/7d7a8c6981a842b98a683e9fbfe51d17/cenc.mpd", clearKeys: { "9f327d24c66fbd84e15ab5c9ead7c7a4": "83837185529c0c4048f81386c2d36426" }, headers: { "User-Agent": CHROME_UA } },

    "goldbet_serieb": {
        name: "GOLD BET LIVE TCD SERIE B", group: "GOLD BET LIVE",
        directUrl: "https://dctv.mocdn.tv/out/v1/53b5ed79722b4b23932dd86262242e03/manifest_L1.mpd",
        clearKeys: { "11c83f71744e40209ed12b1ce234d055": "83279bd86c8f71656440af1abaf43f0a" },
        headers: { "User-Agent": CHROME_UA }
    },

    "playboytv": {
        name: "Playboy TV", group: "Hardcore",
        directUrl: "https://simplitv-live.mdn.ors.at/live/eds/playboy_tv/dash/playboy_tv.mpd",
        clearKeys: { "9fd578695b3c36899b637afc7f21ac13": "f39b08441d41a7c503b1e445555b033d" },
        headers: { "User-Agent": CHROME_UA }
    },
    "desire": {
        name: "Desire", group: "Hardcore",
        directUrl: "https://bpm.tv.delta.nl/dash-cenc/combined/10059/stb.mpd?bk-network=ftth-mobile",
        clearKeys: { "da77348ad6d9c210977817f87112ea74": "2b2ba7d2ce06d7afb98c49449a5064d5" },
        headers: { "User-Agent": CHROME_UA }
    },
    "hc_babes": { name: "Babes Antik", group: "Hardcore", directUrl: "https://dash2.antik.sk/stream/hisi_babes/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_desire": { name: "Desire Antik", group: "Hardcore", directUrl: "https://dash3.antik.sk/stream/hisi_desire/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_true_amateurs": { name: "True Amateurs Antik", group: "Hardcore", directUrl: "https://dash4.antik.sk/stream/hisi_true_amateurs/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_bang_u": { name: "Bang U Antik", group: "Hardcore", directUrl: "https://dash2.antik.sk/stream/hisi_bang_u/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_brazzers_eu": { name: "Brazzers Europe Antik", group: "Hardcore", directUrl: "https://dash3.antik.sk/stream/hisi_brazzers_europe/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_dorcel": { name: "Dorcel Antik", group: "Hardcore", directUrl: "https://dash4.antik.sk/stream/hisi_dorcel/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_dorcel_xxx": { name: "Dorcel Hardcore Antik", group: "Hardcore", directUrl: "https://dash2.antik.sk/stream/hisi_dorcel_xxx/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_leo_tv": { name: "Leo TV Antik", group: "Hardcore", directUrl: "https://dash3.antik.sk/stream/hisi_leo_tv/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_extasy": { name: "Extasy Antik", group: "Hardcore", directUrl: "https://dash4.antik.sk/stream/hisi_extasy/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_leo_gold": { name: "Leo Gold Antik", group: "Hardcore", directUrl: "https://dash2.antik.sk/stream/hisi_leo_gold/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_passion": { name: "Passion Antik", group: "Hardcore", directUrl: "https://dash3.antik.sk/stream/hisi_passion_xxx/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_dusk": { name: "Dusk Antik", group: "Hardcore", directUrl: "https://dash4.antik.sk/stream/hisi_dusk/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_eroxxx": { name: "EroXXX Antik", group: "Hardcore", directUrl: "https://dash4.antik.sk/stream/hisi_eroxxx/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_erox": { name: "EroX Antik", group: "Hardcore", directUrl: "https://dash3.antik.sk/stream/hisi_erox/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_vixen": { name: "Vixen Antik", group: "Hardcore", directUrl: "https://dash4.antik.sk/stream/hisi_vixen/playlist_cbcs.mpd", clearKeys: { "11223344556677889900112233445566": "4b80724d0ef86bcb2c21f7999d67739d" }, m3uWidevineStatic: true },
    "hc_blu3_hustler": { name: "Blu3 Hu5tler", group: "Hardcore", directUrl: "https://v4-pan-n79-cdn-01.live.cdn.cgates.lt/live/dash/560601/index.mpd", clearKeys: { "54393232379c4a57898a8d4d12b6695c": "2305a3f727638465116400f7c422af87" } },

    "serieb/player_serieb.php?event=1": { name: "Serie B 1", group: "Serie B" },
    "serieb/player_serieb.php?event=2": { name: "Serie B 2", group: "Serie B" },
    "serieb/player_serieb.php?event=3": { name: "Serie B 3", group: "Serie B" },
    "serieb/player_serieb.php?event=4": { name: "Serie B 4", group: "Serie B" }
};

const video = document.getElementById('video');
let player = null;
let hlsInstance = null;
let allGroups = {};
let allChannels = [];
let epgData = {};
let currentChannelIndex = 0;
let currentGroup = 'Tutti';
let touchStartY = 0;
let hideTimeout = null;
let isChangingChannel = false;
let currentUserAgent = navigator.userAgent;

function detectDrm(channel) {
    const types = new Set();
    if (!channel) return [];
    const url = ((channel.url) || '').toLowerCase();
    if (channel.drm && channel.drm.clearKeys) types.add('ClearKey');
    if (channel.clearKey) types.add('ClearKey');
    if (url.includes('ck=') || url.includes('clearkey')) types.add('ClearKey');
    if (url.includes('widevine') || url.includes('wv_')) types.add('Widevine');
    if (url.includes('playready') || url.includes('mspr')) types.add('PlayReady');
    if (url.includes('fairplay') || url.includes('skd://')) types.add('FairPlay');
    return Array.from(types);
}
function getWorkerUserAgent(url) {
    const u = (url || '').toLowerCase();
    if (u.includes('rai.it') || u.includes('raiplay')) return { ua: 'HbbTV/1.6.1', ref: 'https://www.raiplay.it/', label: 'Rai' };
    if (u.includes('antik.sk')) return { ua: 'Antik/1.0 (Linux; Android 9; AntikTV)', ref: 'https://antik.sk/', label: 'Sport CZ' };
    return { ua: 'Chrome/120.0.0.0 Safari/537.36', ref: null, label: 'Default' };
}
function getExpectedUserAgent(ch) {
    const group = (ch.group || '').toLowerCase();
    const url = (ch.url || '').toLowerCase();
    if (url.includes('antik.sk') || group.includes('sport cz')) return 'Sport CZ';
    if (url.includes('rai.it') || url.includes('raiplay') || group === 'rai') return 'Rai';
    return 'Default';
}
function toggleLog() {
    const panel = document.getElementById('logPanel');
    if (panel.classList.contains('active')) panel.classList.remove('active');
    else { try { sessionStorage.clear(); } catch (e) {} renderLog(); panel.classList.add('active'); }
}
function renderLog() {
    const body = document.getElementById('logBody');
    const ch = allChannels[currentChannelIndex];
    if (!ch) { body.textContent = 'Nessun canale selezionato.'; return; }
    const url = ch.url || '';
    let kid = '', key = '';
    if (ch.drm && ch.drm.clearKeys) {
        const keys = Object.keys(ch.drm.clearKeys);
        if (keys.length) { kid = keys.join(', '); key = keys.map(k => ch.drm.clearKeys[k]).join(', '); }
    } else if (ch.clearKey) {
        if (ch.clearKey.kid && ch.clearKey.key) { kid = ch.clearKey.kid; key = ch.clearKey.key; }
        else if (typeof ch.clearKey === 'object') {
            const keys = Object.keys(ch.clearKey);
            if (keys.length) { kid = keys.join(', '); key = keys.map(k => ch.clearKey[k]).join(', '); }
        }
    }
    const drmTypes = detectDrm(ch);
    const drmLabel = drmTypes.length ? drmTypes.join(' + ') : 'Nessuno';
    let format = '—';
    if (url.includes('.m3u8')) format = 'HLS (M3U8)';
    else if (url.includes('.mpd')) format = 'MPEG-DASH (MPD)';
    const workerUa = getWorkerUserAgent(url);
    const expectedLabel = getExpectedUserAgent(ch);
    const match = (workerUa.label === expectedLabel);
    const uaStatus = match ? 'OK' : 'Previsto: ' + expectedLabel + ' — Worker: ' + workerUa.label;
    const L = (label, value) => `<span class="log-line"><span class="k">${label.padEnd(14)}</span><span class="v">${value}</span></span>`;
    let html = '';
    html += `<span class="log-title">📡 Canale</span>`;
    html += L('Nome:', ch.name + ' (' + ch.group + ')');
    html += L('DRM:', drmLabel);
    html += L('Formato:', format);
    html += L('URL:', url || '—');
    html += L('KID:', kid || '—');
    html += L('KEY:', key || '—');
    if (ch.m3uWidevine) { html += L('M3U Widevine:', ch.m3uWidevine); html += L('M3U URL:', ch.m3uUrl || url); }
    html += `<span class="log-title" style="margin-top:12px;">🌐 User-Agent</span>`;
    html += L('UA Browser:', currentUserAgent);
    html += L('UA Worker:', workerUa.ua);
    html += L('Referer:', workerUa.ref || '—');
    html += L('Profilo:', workerUa.label);
    html += L('Atteso:', expectedLabel);
    html += L('Stato:', uaStatus);
    html += `<span class="log-title" style="margin-top:12px;">▶️ Player</span>`;
    html += L('Motore:', hlsInstance ? 'HLS.js' : (player ? 'Shaka' : 'nessuno'));
    body.innerHTML = html;
}
async function refreshAccessToken() {
    try {
        const response = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ client_id: CLIENT_ID, client_secret: CLIENT_SECRET, refresh_token: REFRESH_TOKEN, grant_type: 'refresh_token' })
        });
        const data = await response.json();
        if (data.access_token) { ACCESS_TOKEN = data.access_token; return true; }
        return false;
    } catch (e) { return false; }
}
function setDriveStatus(message, type = '') {
    const box = document.getElementById('driveStatusBox');
    box.innerHTML = message;
    box.className = 'drive-status-box active';
    if (type) box.classList.add(type);
}
function showDriveBox() {
    const box = document.getElementById('driveStatusBox');
    box.innerHTML = '<span class="drive-icon">☁️</span> Invia a Drive';
    box.className = 'drive-status-box active';
}
function showConfirmBox(show) {
    const box = document.getElementById('confirmBox');
    if (show) box.className = 'confirm-box active';
    else box.className = 'confirm-box';
}

function generateM3U() {
    if (allChannels.length === 0) return '';
    let m3uContent = '#EXTM3U url-tvg="https://github.com/qwertyuiop8899/TV/raw/refs/heads/main/epg.xml.gz"\n';
    for (const ch of allChannels) {
        if (!ch.url) continue;
        m3uContent += `#EXTINF:-1 group-title="${ch.group}" tvg-id="${ch.tvgId}" tvg-logo="" ,${ch.name}\n`;
        if (ch.m3uWidevine) {
            m3uContent += `#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n`;
            m3uContent += `#KODIPROP:inputstream.adaptive.license_key=${ch.m3uWidevine}\n`;
            m3uContent += `${ch.m3uUrl || ch.url}\n`;
            continue;
        }
        let keysObj = null;
        if (ch.drm && ch.drm.clearKeys) keysObj = ch.drm.clearKeys;
        else if (ch.clearKey) {
            if (ch.clearKey.kid && ch.clearKey.key) keysObj = { [ch.clearKey.kid]: ch.clearKey.key };
            else if (typeof ch.clearKey === 'object') keysObj = ch.clearKey;
        }
        if (keysObj && Object.keys(keysObj).length > 0) {
            const licType = ch.m3uWidevineStatic ? 'com.widevine.alpha' : 'clearkey';
            m3uContent += `#KODIPROP:inputstream.adaptive.license_type=${licType}\n`;
            for (const kid in keysObj) {
                m3uContent += `#KODIPROP:inputstream.adaptive.license_key=${kid}:${keysObj[kid]}\n`;
            }
        }
        m3uContent += `${ch.url}\n`;
    }
    lastM3UContent = m3uContent;
    try { localStorage.setItem('playlist_m3u_backup', m3uContent); } catch (e) {}
    return m3uContent;
}

async function uploadToDrive() {
    if (isUploading) return;
    const content = lastM3UContent || localStorage.getItem('playlist_m3u_backup');
    if (!content || allChannels.length === 0) return;
    isUploading = true;
    showConfirmBox(false);
    setDriveStatus('⏳ Invio in corso...', 'loading');
    try {
        const tokenOk = await refreshAccessToken();
        if (!tokenOk || !ACCESS_TOKEN) throw new Error('Token non valido');
        const response = await fetch(`https://www.googleapis.com/upload/drive/v3/files/${DRIVE_FILE_ID}?uploadType=media`, {
            method: 'PATCH',
            headers: { 'Authorization': 'Bearer ' + ACCESS_TOKEN, 'Content-Type': 'text/plain' },
            body: content
        });
        if (response.ok) {
            document.getElementById('driveStatusBox').className = 'drive-status-box';
            showConfirmBox(true);
            setTimeout(() => { showConfirmBox(false); showDriveBox(); isUploading = false; }, 6000);
        } else {
            const error = await response.json();
            throw new Error(error.error?.message || 'Upload fallito');
        }
    } catch (e) {
        setDriveStatus('❌ ' + e.message, 'error');
        setTimeout(() => { showDriveBox(); isUploading = false; }, 5000);
    }
}

function decodeHtmlEntities(str) {
    if (!str) return str;
    return str.replace(/"/g, '"').replace(/'/g, "'").replace(/&/g, '&');
}
async function destroyShaka() {
    if (!player) return;
    try { await player.unload(); } catch (e) {}
    try { player.detach(); } catch (e) {}
    try { await player.destroy(); } catch (e) {}
    player = null;
}
function resetVideo() { try { video.pause(); video.removeAttribute('src'); video.load(); } catch (e) {} }
function decodeCk(ck) {
    try {
        const pad = ck.length % 4 ? '='.repeat(4 - ck.length % 4) : '';
        const decoded = atob(ck + pad);
        const match = decoded.match(/([0-9a-fA-F]+):([0-9a-fA-F]+)/);
        if (match) return { kid: match[1], key: match[2] };
        return null;
    } catch (e) { return null; }
}
function extractCkFromUrl(rawUrl) {
    try {
        const url = new URL(rawUrl);
        const ck = url.searchParams.get('ck');
        url.searchParams.delete('ck');
        const cleanUrl = url.toString();
        const clearKey = ck ? decodeCk(ck) : null;
        return { cleanUrl: cleanUrl, clearKey: clearKey };
    } catch (e) { return { cleanUrl: rawUrl, clearKey: null }; }
}
function buildDrmConfig(clearKeyInput) {
    if (!clearKeyInput) return null;
    if (clearKeyInput.kid && clearKeyInput.key) return { clearKeys: { [clearKeyInput.kid.toLowerCase()]: clearKeyInput.key.toLowerCase() } };
    if (typeof clearKeyInput === 'object') {
        const clearKeys = {};
        for (const kid in clearKeyInput) {
            if (clearKeyInput.hasOwnProperty(kid)) {
                let k = kid.toLowerCase();
                if (k.length === 31) k = '0' + k;
                clearKeys[k] = clearKeyInput[kid].toLowerCase();
            }
        }
        return Object.keys(clearKeys).length ? { clearKeys: clearKeys } : null;
    }
    if (typeof clearKeyInput === 'string') {
        const parts = clearKeyInput.split(':');
        if (parts.length === 2) {
            let k = parts[0].trim().toLowerCase();
            if (k.length === 31) k = '0' + k;
            return { clearKeys: { [k]: parts[1].trim().toLowerCase() } };
        } else if (parts.length === 4) {
            let k1 = parts[0].trim().toLowerCase();
            let k2 = parts[2].trim().toLowerCase();
            if (k1.length === 31) k1 = '0' + k1;
            if (k2.length === 31) k2 = '0' + k2;
            return { clearKeys: { [k1]: parts[1].trim().toLowerCase(), [k2]: parts[3].trim().toLowerCase() } };
        }
    }
    return null;
}

async function fetchChannelPage(slug, meta) {
    if (meta && meta.directUrl) {
        let rawUrl = meta.directUrl;
        let customHeaders = meta.headers || null;
        if (rawUrl.indexOf('&headers=') !== -1) {
            const parts = rawUrl.split('&headers=');
            rawUrl = parts[0];
            try { customHeaders = JSON.parse(atob(parts[1])); } catch(e) {}
        }
        const extracted = extractCkFromUrl(rawUrl);
        return {
            cleanUrl: extracted.cleanUrl,
            clearKey: extracted.clearKey || meta.clearKeys,
            m3uUrl: meta.m3uUrl || null,
            m3uWidevine: meta.m3uWidevine || null,
            m3uWidevineStatic: meta.m3uWidevineStatic || false,
            headers: customHeaders
        };
    }
    let pageUrl;
    if (slug.indexOf('player_event.php') !== -1 || slug.indexOf('player.php') !== -1 || slug.indexOf('player_serieb.php') !== -1) pageUrl = BASE_URL + slug;
    else pageUrl = BASE_URL + slug + '.php';
    const proxied = CORS_PROXY + pageUrl;
    const res = await fetch(proxied);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const raw = await res.text();
    let body = decodeHtmlEntities(raw);
    try {
        const json = JSON.parse(body);
        if (json.body) body = decodeHtmlEntities(json.body);
        else if (json.contents) body = decodeHtmlEntities(json.contents);
    } catch (e) {}
    const standardMatch = body.match(/const\s+STREAM_URL\s*=\s*"([^"]+)"/);
    if (standardMatch) {
        const rawStreamUrl = standardMatch[1].split('\\/').join('/');
        const extracted = extractCkFromUrl(rawStreamUrl);
        let clearKeyObj = extracted.clearKey;
        if (!clearKeyObj) {
            const keysMatch = body.match(/STREAM_CLEAR_KEYS\s*=\s*(.+?);/is);
            if (keysMatch) {
                let rawKeys = keysMatch[1].trim().replace(/;$/, '').trim();
                let kid = null, key = null;
                try {
                    const parsed = JSON.parse(rawKeys);
                    if (typeof parsed === 'string' && parsed.includes(':')) { const p = parsed.split(':'); kid = p[0].trim().toLowerCase(); key = p[1].trim().toLowerCase(); }
                    else if (Array.isArray(parsed) && parsed.length > 0) {
                        const f = parsed[0];
                        if (typeof f === 'string' && f.includes(':')) { const p = f.split(':'); kid = p[0].trim().toLowerCase(); key = p[1].trim().toLowerCase(); }
                        else if (typeof f === 'object' && f !== null) { kid = f.kid ? String(f.kid).trim().toLowerCase() : null; key = f.key ? String(f.key).trim().toLowerCase() : null; }
                    } else if (typeof parsed === 'object' && parsed !== null) {
                        if (parsed.kid && parsed.key) { kid = String(parsed.kid).trim().toLowerCase(); key = String(parsed.key).trim().toLowerCase(); }
                        else { const e = Object.entries(parsed); if (e.length > 0) { kid = String(e[0][0]).trim().toLowerCase(); key = String(e[0][1]).trim().toLowerCase(); } }
                    }
                } catch (err) {
                    const c = rawKeys.replace(/["']/g, '').trim();
                    if (c.includes(':')) { const p = c.split(':'); kid = p[0].trim().toLowerCase(); key = p[1].trim().toLowerCase(); }
                }
                if (kid && key) clearKeyObj = { kid: kid, key: key };
            }
        }
        return { cleanUrl: extracted.cleanUrl, clearKey: clearKeyObj, m3uUrl: null, m3uWidevine: null, m3uWidevineStatic: false, headers: null };
    }
    const mpdMatch = body.match(/STREAM_URL\s*=\s*["']([^"']*)["']/i);
    if (!mpdMatch) return null;
    const mpdUrl = mpdMatch[1].split('\\/').join('/').trim();
    if (!mpdUrl) return null;
    const keysMatch = body.match(/STREAM_CLEAR_KEYS\s*=\s*(.+?);/is);
    let clearKeyObj = null;
    if (keysMatch) {
        let rawKeys = keysMatch[1].trim().replace(/;$/, '').trim();
        let kid = null, key = null;
        try {
            const parsed = JSON.parse(rawKeys);
            if (typeof parsed === 'string' && parsed.includes(':')) { const p = parsed.split(':'); kid = p[0].trim().toLowerCase(); key = p[1].trim().toLowerCase(); }
            else if (Array.isArray(parsed) && parsed.length > 0) {
                const f = parsed[0];
                if (typeof f === 'string' && f.includes(':')) { const p = f.split(':'); kid = p[0].trim().toLowerCase(); key = p[1].trim().toLowerCase(); }
                else if (typeof f === 'object' && f !== null) { kid = f.kid ? String(f.kid).trim().toLowerCase() : null; key = f.key ? String(f.key).trim().toLowerCase() : null; }
            } else if (typeof parsed === 'object' && parsed !== null) {
                if (parsed.kid && parsed.key) { kid = String(parsed.kid).trim().toLowerCase(); key = String(parsed.key).trim().toLowerCase(); }
                else { const e = Object.entries(parsed); if (e.length > 0) { kid = String(e[0][0]).trim().toLowerCase(); key = String(e[0][1]).trim().toLowerCase(); } }
            }
        } catch (err) {
            const c = rawKeys.replace(/["']/g, '').trim();
            if (c.includes(':')) { const p = c.split(':'); kid = p[0].trim().toLowerCase(); key = p[1].trim().toLowerCase(); }
        }
        if (kid && key) clearKeyObj = { kid: kid, key: key };
    }
    if (mpdUrl.indexOf('ck=') !== -1) {
        const extracted = extractCkFromUrl(mpdUrl);
        return { cleanUrl: extracted.cleanUrl, clearKey: extracted.clearKey || clearKeyObj, m3uUrl: null, m3uWidevine: null, m3uWidevineStatic: false, headers: null };
    }
    return { cleanUrl: mpdUrl, clearKey: clearKeyObj, m3uUrl: null, m3uWidevine: null, m3uWidevineStatic: false, headers: null };
}

async function loadAllChannels() {
    const overlay = document.getElementById('loadingOverlay');
    const loadText = document.getElementById('loadText');
    const loadProgress = document.getElementById('loadProgress');
    overlay.classList.add('active');
    loadText.textContent = 'Scraping canali MPD...';
    allChannels = [];
    allGroups = {};
    for (const slug in CHANNEL_MAP) {
        const meta = CHANNEL_MAP[slug];
        if (meta && meta.group && !allGroups[meta.group]) allGroups[meta.group] = [];
    }
    const slugs = Object.keys(CHANNEL_MAP);
    let done = 0;
    for (const slug of slugs) {
        const meta = CHANNEL_MAP[slug];
        loadProgress.textContent = (done + 1) + '/' + slugs.length + ' – ' + meta.name;
        try {
            const result = await fetchChannelPage(slug, meta);
            if (result && result.cleanUrl) {
                const drm = buildDrmConfig(result.clearKey);
                const ch = { name: meta.name, group: meta.group, tvgId: meta.name, url: result.cleanUrl, clearKey: result.clearKey, drm: drm, m3uUrl: result.m3uUrl, m3uWidevine: result.m3uWidevine, m3uWidevineStatic: result.m3uWidevineStatic || false, headers: result.headers, slug: slug };
                allChannels.push(ch);
                allGroups[meta.group].push(ch);
            } else {
                const ch = { name: meta.name, group: meta.group, tvgId: meta.name, url: null, clearKey: null, drm: null, m3uUrl: null, m3uWidevine: null, m3uWidevineStatic: false, headers: null, slug: slug };
                allChannels.push(ch);
                allGroups[meta.group].push(ch);
            }
        } catch (e) {
            const ch = { name: meta.name, group: meta.group, tvgId: meta.name, url: null, clearKey: null, drm: null, m3uUrl: null, m3uWidevine: null, m3uWidevineStatic: false, headers: null, slug: slug };
            allChannels.push(ch);
            allGroups[meta.group].push(ch);
        }
        done++;
    }
    overlay.classList.remove('active');
    renderGroupMenu();
    updateCountBadge();
    generateM3U();
    showDriveBox();
    showConfirmBox(false);
    setTimeout(() => { uploadToDrive(); }, 300);
    if (allChannels.length > 0) {
        let startGroup = 'Rai';
        if (!allGroups['Rai']) { for (const g in allGroups) { startGroup = g; break; } }
        currentGroup = startGroup;
        const menu = document.getElementById('group-menu');
        if (menu) menu.value = startGroup;
        const filtered = getFilteredChannels();
        let firstPlayable = null;
        for (const c of filtered) { if (c.url) { firstPlayable = c; break; } }
        if (!firstPlayable) firstPlayable = filtered[0];
        currentChannelIndex = allChannels.indexOf(firstPlayable);
        if (currentChannelIndex < 0) currentChannelIndex = 0;
        playChannel(allChannels[currentChannelIndex]);
        updateChannelDisplay();
    }
}

function renderGroupMenu() {
    const menu = document.getElementById('group-menu');
    const prev = menu.value;
    menu.innerHTML = '<option value="Tutti">Tutti</option>';
    const customOrder = ['Rai', 'Mediaset', 'RSI', 'Sky Cinema', 'Sky Sport', 'Serie B', 'DAZN CH', 'CBS Sport', 'GOLD BET LIVE', 'FOX SPORT', 'Premier Sport', 'SPORT CZ', 'ELEVEN SPORT', 'COMO TV', 'BluSport', 'Intrattenimento', 'Hardcore'];
    const sortedGroups = Object.keys(allGroups).sort(function(a, b) {
        let idxA = customOrder.indexOf(a); let idxB = customOrder.indexOf(b);
        if (idxA === -1) idxA = 999; if (idxB === -1) idxB = 999;
        return idxA - idxB;
    });
    for (const grp of sortedGroups) {
        const opt = document.createElement('option');
        opt.value = grp; opt.textContent = grp;
        menu.appendChild(opt);
    }
    if (prev && (prev === 'Tutti' || allGroups[prev])) { menu.value = prev; currentGroup = prev; }
    menu.onchange = function () {
        currentGroup = menu.value;
        updateCountBadge();
        const filtered = getFilteredChannels();
        if (filtered.length > 0) {
            let target = null;
            for (const c of filtered) { if (c.url) { target = c; break; } }
            if (!target) target = filtered[0];
            const idx = allChannels.indexOf(target);
            if (idx !== -1 && idx !== currentChannelIndex) { currentChannelIndex = idx; playChannel(allChannels[currentChannelIndex]); }
            updateChannelDisplay();
        }
    };
}
function updateCountBadge() { document.getElementById('countBadge').textContent = 'Canali: ' + getFilteredChannels().length; }
function getFilteredChannels() { if (currentGroup === 'Tutti') return allChannels; return allGroups[currentGroup] || []; }

async function playChannel(channel) {
    if (!channel) return;
    if (isChangingChannel) return;
    isChangingChannel = true;
    const overlay = document.getElementById('loadingOverlay');
    const loadText = document.getElementById('loadText');
    const loadProgress = document.getElementById('loadProgress');
    if (hlsInstance) { try { hlsInstance.destroy(); } catch (e) {} hlsInstance = null; }
    await destroyShaka();
    resetVideo();
    if (!channel.url) {
        loadText.textContent = 'Canale non disponibile';
        loadProgress.textContent = channel.name + ' (nessun URL)';
        overlay.classList.add('active');
        setTimeout(function () { overlay.classList.remove('active'); }, 1500);
        isChangingChannel = false;
        return;
    }
    const safetyTimeout = setTimeout(function () {
        if (isChangingChannel) { overlay.classList.remove('active'); forceUnlockControls(); }
    }, 25000);
    try {
        loadText.textContent = 'Caricamento...';
        loadProgress.textContent = channel.name;
        overlay.classList.add('active');
        const isHls = (channel.url.indexOf('.m3u8') !== -1);
        if (isHls) {
            if (Hls.isSupported()) {
                hlsInstance = new Hls({ enableWorker: true, lowLatencyMode: true, maxBufferLength: 10, manifestLoadingTimeOut: 4000, manifestLoadingMaxRetry: 1 });
                hlsInstance.loadSource(channel.url);
                hlsInstance.attachMedia(video);
                hlsInstance.on(Hls.Events.MANIFEST_PARSED, function () {
                    video.play().catch(function () {});
                    overlay.classList.remove('active');
                    clearTimeout(safetyTimeout);
                    isChangingChannel = false;
                });
                hlsInstance.on(Hls.Events.ERROR, function (event, data) {
                    if (data.fatal) { overlay.classList.remove('active'); forceUnlockControls(); clearTimeout(safetyTimeout); }
                });
            } else {
                video.src = channel.url;
                await video.play().catch(function () {});
                overlay.classList.remove('active'); clearTimeout(safetyTimeout); isChangingChannel = false;
            }
        } else {
            player = new shaka.Player();
            await player.attach(video);
            player.configure({
                streaming: { lowLatencyMode: true, bufferingGoal: 4, rebufferingGoal: 1, jumpLargeGaps: true, stallEnabled: true, stallThreshold: 1, ignoreTextStreamFailures: true },
                manifest: { dash: { ignoreMinBufferTime: true, autoCorrectDrift: true } }
            });
            if (channel.drm) player.configure({ drm: channel.drm });
            if (channel.headers) {
                player.getNetworkingEngine().registerRequestFilter(function (type, request) {
                    if (type === shaka.net.NetworkingEngine.RequestType.MANIFEST || type === shaka.net.NetworkingEngine.RequestType.SEGMENT) {
                        for (const key in channel.headers) request.headers[key] = channel.headers[key];
                    }
                });
            }
            player.addEventListener('error', function (event) {
                overlay.classList.remove('active'); forceUnlockControls(); clearTimeout(safetyTimeout);
            });
            try { await player.load(channel.url); }
            catch (e) { overlay.classList.remove('active'); forceUnlockControls(); clearTimeout(safetyTimeout); return; }
            try { await video.play(); } catch (err) {}
            overlay.classList.remove('active'); clearTimeout(safetyTimeout); isChangingChannel = false;
        }
    } catch (e) {
        overlay.classList.remove('active'); clearTimeout(safetyTimeout); forceUnlockControls();
    }
}
function forceUnlockControls() {
    isChangingChannel = false;
    document.getElementById('loadingOverlay').classList.remove('active');
}
function nextChannel() {
    if (!allChannels.length || isChangingChannel) return;
    const filtered = getFilteredChannels();
    if (!filtered.length) return;
    const cur = filtered.indexOf(allChannels[currentChannelIndex]);
    const next = filtered[(cur + 1) % filtered.length];
    const idx = allChannels.indexOf(next);
    if (idx !== -1 && idx !== currentChannelIndex) { currentChannelIndex = idx; playChannel(allChannels[currentChannelIndex]); updateChannelDisplay(); }
}
function prevChannel() {
    if (!allChannels.length || isChangingChannel) return;
    const filtered = getFilteredChannels();
    if (!filtered.length) return;
    const cur = filtered.indexOf(allChannels[currentChannelIndex]);
    const prev = filtered[(cur - 1 + filtered.length) % filtered.length];
    const idx = allChannels.indexOf(prev);
    if (idx !== -1 && idx !== currentChannelIndex) { currentChannelIndex = idx; playChannel(allChannels[currentChannelIndex]); updateChannelDisplay(); }
}
function updateChannelDisplay() {
    const ch = allChannels[currentChannelIndex];
    if (!ch) return;
    document.getElementById('currentChannelName').textContent = ch.name;
    const prog = getNowPlaying(ch.tvgId);
    document.getElementById('currentChannelEpg').textContent = prog ? prog.title : '';
    showChannelNameWithAutoHide();
    if (document.getElementById('logPanel').classList.contains('active')) renderLog();
}
function showChannelNameWithAutoHide() {
    const el = document.getElementById('channelLeft');
    el.classList.remove('hide');
    el.style.animation = 'none';
    setTimeout(function () { el.style.animation = 'slideInLeft 0.3s ease-out'; }, 5);
    if (hideTimeout) clearTimeout(hideTimeout);
    hideTimeout = setTimeout(function () { el.classList.add('hide'); }, 6000);
}
function normalizeId(id) {
    if (!id) return "";
    let s = id.toLowerCase();
    s = s.replace(/\[\d+\]\s*/g, '').replace(/\.it$/g, '').replace(/hd$/g, '').replace(/[^a-z0-9]/g, '');
    return s;
}
async function fetchEPG() {
    try {
        const res = await fetch(CORS_PROXY + EPG_URL);
        const raw = await res.text();
        const decoded = decodeHtmlEntities(raw);
        let bodyText = decoded;
        try {
            const json = JSON.parse(decoded);
            bodyText = json.body || json.contents || decoded;
        } catch (e) {}
        const xml = new DOMParser().parseFromString(bodyText, 'text/xml');
        const programs = xml.getElementsByTagName('programme');
        for (let i = 0; i < programs.length; i++) {
            const p = programs[i];
            const rawId = p.getAttribute('channel');
            const id = normalizeId(rawId);
            if (!epgData[id]) epgData[id] = [];
            const titleEl = p.getElementsByTagName('title')[0];
            epgData[id].push({ start: parseEPGDate(p.getAttribute('start')), stop: parseEPGDate(p.getAttribute('stop')), title: titleEl ? titleEl.textContent : '' });
        }
    } catch (e) {}
}
function parseEPGDate(s) {
    if (!s) return new Date();
    return new Date(s.replace(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2}).*/, '$1-$2-$3T$4:$5:$6'));
}
function getNowPlaying(id) {
    const norm = normalizeId(id);
    if (!epgData[norm]) return null;
    const now = new Date();
    for (const p of epgData[norm]) { if (now >= p.start && now < p.stop) return p; }
    return null;
}

document.addEventListener('wheel', function (e) { e.preventDefault(); if (isChangingChannel) return; if (e.deltaY > 0) nextChannel(); else prevChannel(); }, { passive: false });
document.addEventListener('keydown', function (e) {
    if (isChangingChannel) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); nextChannel(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); prevChannel(); }
});
document.addEventListener('touchstart', function (e) { touchStartY = e.touches[0].clientY; }, { passive: false });
document.addEventListener('touchmove', function (e) {
    if (!touchStartY || isChangingChannel) return;
    e.preventDefault();
    const delta = e.touches[0].clientY - touchStartY;
    if (Math.abs(delta) > 50) { if (delta < 0) nextChannel(); else prevChannel(); touchStartY = null; }
}, { passive: false });

window.onload = async function () {
    if (typeof shaka === 'undefined') return;
    shaka.polyfill.installAll();
    if (!shaka.Player.isBrowserSupported()) return;
    await fetchEPG();
    await loadAllChannels();
    setTimeout(forceUnlockControls, 500);
};

setInterval(function () {
    const ch = allChannels[currentChannelIndex];
    if (ch && !isChangingChannel) {
        const epgSpan = document.getElementById('currentChannelEpg');
        const leftDiv = document.getElementById('channelLeft');
        if (epgSpan && leftDiv && !leftDiv.classList.contains('hide')) {
            const prog = getNowPlaying(ch.tvgId);
            if (prog) epgSpan.textContent = prog.title;
        }
    }
}, 60000);
</script>
</body>
</html>
