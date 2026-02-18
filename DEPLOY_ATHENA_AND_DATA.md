# Sovereign Sentinel: Athena & Alternative Data Deployment Guide

This guide details the steps to deploy **Project Athena** (Persistent Memory) and the **Alternative Data Engine** (Sentiment Analysis) to your Oracle Cloud VPS.

## 1. Prerequisites & API Keys

Before deploying, ensure you have the following credentials:

### A. Google Service Account (Project Athena)
1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project (or use existing).
3.  Enable **Google Drive API** and **Google Docs API**.
4.  Create a **Service Account** -> Keys -> Create New Key (JSON).
5.  Save the file as `credentials.json`.
6.  **Important**: Share your "Inbox" folder and "Master Brain" Doc with the Service Account email address (found in the JSON file) giving it **Editor** access.
7.  Note the `INBOX_FOLDER_ID` (from URL of folder) and `BRAIN_DOC_ID` (from URL of Doc).

### B. Alternative Data Providers
1.  **NewsData.io**: Register at [newsdata.io](https://newsdata.io) (Free Tier). Get API Key.
2.  **Finnhub**: Register at [finnhub.io](https://finnhub.io/) (Free Tier). Get API Key.
3.  **Actually Relevant**: No key needed (Public API).
4.  **PyTrends/Google Trends**: No key needed (Scraper).

## 2. Update Environment Variables

On your Oracle Cloud instance (or locally first):
1.  Edit your `.env` file:
    ```bash
    nano .env
    ```
2.  Add the new keys:
    ```ini
    # Project Athena
    INBOX_FOLDER_ID=your_actual_folder_id_here
    BRAIN_DOC_ID=your_actual_doc_id_here
    GOOGLE_APPLICATION_CREDENTIALS=credentials.json

    # Alternative Data Engine
    NEWSDATA_API_KEY=your_newsdata_key_here
    FINNHUB_API_KEY=your_finnhub_key_here
    ```

3.  Upload `credentials.json` to the root of your project directory (`/home/ubuntu/Sovereign-Sentinel/`).

## 3. Deployment Steps

Run the following commands on your Oracle Cloud VPS:

### Step 1: Update Codebase
Pull the latest changes (files created by Antigravity):
```bash
cd ~/Sovereign-Sentinel
git pull
# Or upload athena_janitor.py, alt_data_engine.py, requirements.txt, and .service files manually if not using git.
```

### Step 2: Install Dependencies
Update the virtual environment with new libraries:
```bash
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Step 3: Configure Systemd Services
Copy the service files to the system directory and enable them:

**Athena Janitor:**
```bash
sudo cp athena_janitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable athena_janitor
sudo systemctl start athena_janitor
```

**Alternative Data Engine:**
```bash
sudo cp alt_data_engine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alt_data_engine
sudo systemctl start alt_data_engine
```

## 4. Verification

Check the status of the services to ensure they are running correctly:

```bash
sudo systemctl status athena_janitor
sudo systemctl status alt_data_engine
```

Check the logs if needed:
```bash
tail -f athena_janitor.log
tail -f alt_data_engine.log
```

## 5. Summary of Components
-   **athena_janitor.py**: Polls Google Drive every 60s, merges docs to Master Brain, deletes originals.
-   **alt_data_engine.py**: Polls NewsData, Finnhub, Google Trends, and Reddit every 60m (snapshot saved to `data/sentiment_snapshot.json`).
