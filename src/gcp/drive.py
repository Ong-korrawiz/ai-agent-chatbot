from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import json
from src.settings import GOOGLE_API_CRED
import os
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io
from googleapiclient.discovery import build
from pathlib import Path
import shutil
import re
import io

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

load_dotenv()

class GoogleDrive():
    def __init__(self, ):
        self.scope = ['https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(GOOGLE_API_CRED)
        )
        self.service = build('drive', 'v3', credentials=self.creds)

    def download_file(self, file_id: str, target_folder: str):
        results = self.service.files().list(
                q=f"'1fFL7FWeYu1lxeVxg2jc6msngAeFDnvs9' in parents",
                pageSize=10, fields="nextPageToken, files(id, name)",
                pageToken=None
                ).execute()
        items = results.get('files', [])
        if not items:
            print('No files found.')
        else:
            for item in items:
                print(u'{0} ({1})'.format(item['name'], item['id']))


                file_id = item['id']
                request = self.service.files().get_media(fileId=file_id)

                with open(Path(target_folder) / item['name'], 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        print("Download %d%%." % int(status.progress() * 100))

        page_token = results.get('nextPageToken', None)


if __name__ == "__main__":
    google_drive = GoogleDrive()
    file = google_drive.download_file(
        file_id="1fFL7FWeYu1lxeVxg2jc6msngAeFDnvs9",
        target_folder="src/data"
    )