import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import io
import argparse
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import get_google_creds

def main():
    parser = argparse.ArgumentParser(description='Download a file from Google Drive')
    parser.add_argument('--file_id', required=True, help='The ID of the file to download')
    parser.add_argument('--output', required=True, help='The output file path')
    parser.add_argument('--mime_type', help='MIME type to export Google Docs to (default application/pdf for documents)')
    args = parser.parse_args()

    creds = get_google_creds()
    if not creds:
        print("Error: No valid credentials. Please run 'python scripts/auth.py' first.")
        return

    service = build('drive', 'v3', credentials=creds)

    try:
        # Get file metadata to check mimeType
        file_meta = service.files().get(fileId=args.file_id).execute()
        mime_type = file_meta.get('mimeType')
        name = file_meta.get('name')
        print(f"Downloading '{name}' (Type: {mime_type})...")

        request = None
        if mime_type.startswith('application/vnd.google-apps.'):
            # Export
            export_mime = args.mime_type
            if not export_mime:
                # Default mappings
                if 'spreadsheet' in mime_type:
                    export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' # xlsx
                elif 'document' in mime_type:
                    export_mime = 'application/pdf'
                elif 'presentation' in mime_type:
                    export_mime = 'application/pdf'
                else:
                    export_mime = 'application/pdf' # Fallback
            
            print(f"Exporting Google format to {export_mime}...")
            request = service.files().export_media(fileId=args.file_id, mimeType=export_mime)
        else:
            # Download binary
            print("Downloading binary content...")
            request = service.files().get_media(fileId=args.file_id)

        fh = io.FileIO(args.output, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}%.")

        print(f"Successfully saved to: {args.output}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
