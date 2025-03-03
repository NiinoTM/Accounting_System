import os
import io
import hashlib
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account

# Configuration
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Your service account credentials file
SCOPES = ['https://www.googleapis.com/auth/drive']
# Replace with your actual Google Drive folder ID (the long alphanumeric string)
DRIVE_FOLDER_ID = '1ZqSLWL7POqp0gufYuMxFdyHX0sjDKMtJ'
LOCAL_DIR = 'data'  # Local directory with files to sync

# Authenticate with Google Drive
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def get_remote_file(file_name, folder_id):
    """
    Returns remote file metadata (including MD5 checksum) for a given file name in the specified folder.
    If the file does not exist remotely, returns None.
    """
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name, md5Checksum)").execute()
    items = results.get('files', [])
    return items[0] if items else None

def get_local_md5(file_path):
    """
    Computes the MD5 hash for the local file.
    """
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()

def upload_or_update_file(local_file_path, folder_id):
    """
    Uploads a new file or updates an existing one on Google Drive.
    """
    file_name = os.path.basename(local_file_path)
    remote_file = get_remote_file(file_name, folder_id)
    media = MediaFileUpload(local_file_path, resumable=True)
    if remote_file:
        print(f"Updating file on Drive: {file_name}")
        drive_service.files().update(fileId=remote_file['id'], media_body=media).execute()
    else:
        print(f"Uploading new file to Drive: {file_name}")
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

def download_file(remote_file, local_file_path):
    """
    Downloads a file from Google Drive and writes it to the local path.
    """
    request = drive_service.files().get_media(fileId=remote_file['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Downloading {os.path.basename(local_file_path)}: {int(status.progress() * 100)}% complete")
    with open(local_file_path, "wb") as f:
        f.write(fh.getvalue())
    print(f"Downloaded and updated local file: {os.path.basename(local_file_path)}")

def main():
    # Collect files that are different between local and remote
    modified_files = []
    
    for file in os.listdir(LOCAL_DIR):
        local_file_path = os.path.join(LOCAL_DIR, file)
        if os.path.isfile(local_file_path):
            local_md5 = get_local_md5(local_file_path)
            remote_file = get_remote_file(file, DRIVE_FOLDER_ID)
            if remote_file:
                remote_md5 = remote_file.get('md5Checksum')
                if local_md5 != remote_md5:
                    modified_files.append((file, remote_file))
            else:
                # Consider file modified if it does not exist in the cloud.
                modified_files.append((file, None))
    
    if modified_files:
        print("The following files have differences between local and cloud:")
        for file, remote in modified_files:
            if remote:
                print(f"- {file} (local and cloud contents differ)")
            else:
                print(f"- {file} (not found on cloud)")
                
        action = input("Enter 'U' to upload local files to Cloud or 'D' to download from Cloud to local: ").strip().upper()
        if action == 'U':
            for file, _ in modified_files:
                local_file_path = os.path.join(LOCAL_DIR, file)
                upload_or_update_file(local_file_path, DRIVE_FOLDER_ID)
            print("Upload completed.")
        elif action == 'D':
            for file, remote in modified_files:
                if remote:
                    local_file_path = os.path.join(LOCAL_DIR, file)
                    download_file(remote, local_file_path)
                else:
                    print(f"File '{file}' not found on Cloud. Skipping download.")
            print("Download completed.")
        else:
            print("No valid action chosen. Exiting without changes.")
    else:
        print("No modifications detected between local and Google Drive files.")

if __name__ == '__main__':
    main()
