import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

FILE_ID = "1H-RE9As-EY_8_yxkbi791fneCvqsPTG3"
LOCAL_FILE = "now_playlist.m3u"
CREDS_FILE = "service_account.json"

def main():
    if not os.path.exists(LOCAL_FILE):
        print(f"ERRORE: {LOCAL_FILE} non trovato")
        sys.exit(1)
    if not os.path.exists(CREDS_FILE):
        print(f"ERRORE: {CREDS_FILE} non trovato")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE, scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    media = MediaFileUpload(LOCAL_FILE, mimetype="audio/x-mpegurl", resumable=True)
    updated = service.files().update(
        fileId=FILE_ID,
        media_body=media,
        fields="id, name, modifiedTime",
    ).execute()

    print("OK upload:", updated.get("name"), updated.get("modifiedTime"))

if __name__ == "__main__":
    main()
