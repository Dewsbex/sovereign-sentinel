# Sovereign Sentinel: Credential Acquisition Guide

This guide explains what each credential is, why it's needed, and exactly how to get it.

## 1. Google Service Account (Project Athena)
**What is it?** A file named `credentials.json` that acts as a secure "digital keycard," allowing the Athena script to access your Google Drive and Docs without needing you to log in manually via browser every time.

**How to get it:**
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  If you don't have a project, click "Select a project" -> "New Project" -> Name it "Sovereign-Sentinel" -> Create.
3.  In the left sidebar, go to **APIs & Services > Library**.
4.  Search for and ENABLE these two APIs:
    *   **Google Drive API**
    *   **Google Docs API**
5.  Go to **APIs & Services > Credentials**.
6.  Click **Create Credentials** and select **Service Account**.
7.  Name it "Athena Janitor" -> Click **Create and Continue**.
8.  Role: Select **Editor** -> Click **Continue** -> Click **Done**.
9.  Click on the newly created Service Account (email looks like `athena-janitor@project-id.iam.gserviceaccount.com`).
10. Go to the **Keys** tab -> **Add Key** -> **Create new key** -> **JSON**.
11. A file will automatically download to your computer. **This is your `credentials.json`.**

## 2. Inbox Folder ID & Brain Doc ID
**What are they?** These are the specific addresses of the folders and documents in your Google Drive. Project Athena needs these to know *where* to look for new notes and *where* to save them.

**How to get them:**
1.  **Create the Inbox Folder:**
    *   Go to Google Drive.
    *   Create a new folder named `Athena Inbox`.
    *   Open the folder.
    *   Look at the URL in your browser: `drive.google.com/drive/folders/1a2b3c4d5e6f...`
    *   The long string of random characters at the end is your **Inbox Folder ID**.
2.  **Create the Master Brain Doc:**
    *   Create a new Google Doc named `Master Brain`.
    *   Open the document.
    *   Look at the URL: `docs.google.com/document/d/1x2y3z4a5b6c.../edit`
    *   The long string between `/d/` and `/edit` is your **Brain Doc ID**.
3.  **CRITICAL STEP: SHARE ACCESS**
    *   Go back to your `credentials.json` file on your computer. Open it with Notepad.
    *   Find the `client_email` address inside (e.g., `athena-janitor@...`).
    *   Go to your `Athena Inbox` folder in Drive -> Right Click -> Share -> Paste that email -> **Editor**.
    *   Go to your `Master Brain` doc -> Share -> Paste that email -> **Editor**.
    *   *Without this step, the script cannot see your files!*

## 3. NewsData.io API Key
**What is it?** Allows the system to fetch global news headlines for sentiment analysis.
**How to get it:**
1.  Go to [NewsData.io](https://newsdata.io/).
2.  Click "Get API Key" or Sign Up.
3.  Register for the **Free Plan** (Permanent Free).
4.  Copy the API Key from your dashboard.

## 4. Finnhub API Key
**What is it?** Provides market sentiment scores and news for specific stocks.
**How to get it:**
1.  Go to [Finnhub.io](https://finnhub.io/).
2.  Click "Get free API key".
3.  Register.
4.  Your API key will be displayed on the dashboard.

---
**Once you have these:**
Please paste the contents of `credentials.json` and the other IDs/Keys into the chat, or let me know if you'd prefer to paste them directly into a file yourself.
