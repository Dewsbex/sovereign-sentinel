import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("AthenaVerify")

def verify():
    load_dotenv()
    
    INBOX_FOLDER_ID = os.getenv('INBOX_FOLDER_ID')
    BRAIN_DOC_ID = os.getenv('BRAIN_DOC_ID')
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

    print("--- Project Athena Verification ---")
    print(f"Inbox Folder ID: {INBOX_FOLDER_ID}")
    print(f"Brain Doc ID: {BRAIN_DOC_ID}")
    print(f"Credentials File: {SERVICE_ACCOUNT_FILE}")

    if not INBOX_FOLDER_ID or not BRAIN_DOC_ID:
        print("❌ FAILED: Missing Folder/Doc IDs in .env")
        return

    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)

        # 1. Test Drive Access (Listing files in Inbox)
        print("\nChecking Inbox access...")
        query = f"'{INBOX_FOLDER_ID}' in parents and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        print(f"✅ SUCCESS: Connected to Drive. Found {len(files)} files in Inbox.")

        # 2. Test Doc Access (Reading Brain Doc metadata)
        print("\nChecking Brain Doc access...")
        doc = docs_service.documents().get(documentId=BRAIN_DOC_ID).execute()
        print(f"✅ SUCCESS: Connected to Docs. Brain Doc Title: '{doc.get('title')}'")

        print("\n🎉 ATHENA IS READY TO GO!")

    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        print("\nTip: Make sure you shared the folder and doc with the service account email.")

if __name__ == "__main__":
    verify()
