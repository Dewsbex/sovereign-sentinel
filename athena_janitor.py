import os
import time
import datetime
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("athena_janitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AthenaJanitor")

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
SERVICE_ACCOUNT_FILE = 'credentials.json'
INBOX_FOLDER_ID = os.getenv('INBOX_FOLDER_ID')
BRAIN_DOC_ID = os.getenv('BRAIN_DOC_ID')

def authenticate():
    """Authenticates using the Service Account."""
    creds = None
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    else:
        logger.error(f"Credentials file not found: {SERVICE_ACCOUNT_FILE}")
        return None
    return creds

def get_inbox_files(service):
    """Retrieves files from the Inbox folder."""
    query = f"'{INBOX_FOLDER_ID}' in parents and trashed = false and mimeType = 'application/vnd.google-apps.document'"
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        return items
    except HttpError as error:
        logger.error(f"An error occurred listing files: {error}")
        return []

def read_doc_content(docs_service, file_id):
    """Reads the full text content of a Google Doc."""
    try:
        doc = docs_service.documents().get(documentId=file_id).execute()
        content = doc.get('body').get('content')
        full_text = ""
        for element in content:
            if 'paragraph' in element:
                elements = element.get('paragraph').get('elements')
                for elem in elements:
                    if 'textRun' in elem:
                        full_text += elem.get('textRun').get('content')
        return full_text
    except HttpError as error:
        logger.error(f"An error occurred reading doc {file_id}: {error}")
        return ""

def append_to_brain(docs_service, text):
    """Appends text to the Master Brain Doc."""
    if not text:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n\n--- NEW MEMORY ({timestamp}) ---\n"
    content_to_insert = header + text

    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1, # Insert at the beginning or end? Spec says "appends this content to the end".
                                # To append to end, we need the end index. 
                                # Using 'endOfSegmentLocation' is better for appending.
                },
                'text': content_to_insert
            }
        }
    ]
    
    # Correct approach for appending to the end: use endOfSegmentLocation
    requests = [
        {
            'insertText': {
                'endOfSegmentLocation': {
                    'segmentId': '' # Body
                },
                'text': content_to_insert
            }
        }
    ]

    try:
        docs_service.documents().batchUpdate(documentId=BRAIN_DOC_ID, body={'requests': requests}).execute()
        logger.info("Successfully appended content to Brain.")
    except HttpError as error:
        logger.error(f"An error occurred appending to Brain: {error}")

def trash_file(drive_service, file_id):
    """Moves a file to the trash."""
    try:
        drive_service.files().update(fileId=file_id, body={'trashed': True}).execute()
        logger.info(f"Trashed file {file_id}")
    except HttpError as error:
        logger.error(f"An error occurred trashing file {file_id}: {error}")

def main():
    logger.info("Starting Athena Janitor...")
    if not INBOX_FOLDER_ID or not BRAIN_DOC_ID:
        logger.error("Environment variables INBOX_FOLDER_ID or BRAIN_DOC_ID not set.")
        return

    creds = authenticate()
    if not creds:
        return

    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)

    while True:
        try:
            logger.info("Polling Inbox...")
            files = get_inbox_files(drive_service)
            
            if not files:
                logger.info("No new files found.")
            
            for file in files:
                logger.info(f"Processing file: {file['name']} ({file['id']})")
                content = read_doc_content(docs_service, file['id'])
                if content:
                    append_to_brain(docs_service, content)
                    trash_file(drive_service, file['id'])
                else:
                    logger.warning(f"File {file['id']} was empty or unreadable.")
            
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        
        time.sleep(60)

if __name__ == '__main__':
    main()
