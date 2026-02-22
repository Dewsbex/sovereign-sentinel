#!/usr/bin/env python3
"""
Athena Brain Updater
Daily job to scan project repositories, analyze changes with Gemini, and update the Brain Doc.
"""
import os
import sys
import json
import subprocess
import datetime
import requests
from googleapiclient.discovery import build
import logging
from credentials_manager import get_secret
from audit_log import AuditLogger

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("brain_updater.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BrainUpdater")

# Import shared logic from janitor
# Ensure current dir is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from athena_janitor import authenticate, append_to_brain
except ImportError:
    logger.error("Could not import athena_janitor. Ensure it is in the same directory.")
    sys.exit(1)

# Configuration
PROJECT_ROOTS = [
    "/home/ubuntu/Sovereign-Sentinel",
    "/home/ubuntu/famplan-ai",
    "/home/ubuntu/Krypto",
    "/home/ubuntu/News",
    "/home/ubuntu/athena"
]
STATE_FILE = "brain_state.json"
GEMINI_API_KEY = get_secret('GOOGLE_API_KEY')

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_git_changes(repo_path, last_update):
    """Get git log since last update"""
    if not os.path.exists(os.path.join(repo_path, ".git")):
        logger.warning(f"No git repo found at {repo_path}")
        return ""
    
    cmd = ["git", "-C", repo_path, "log", "--pretty=format:%h - %an: %s", f"--since={last_update}"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Git error in {repo_path}: {e}")
        return ""

def analyze_with_gemini(changes_text):
    """Send changes to Gemini for summary"""
    if not GEMINI_API_KEY:
        logger.error("GOOGLE_API_KEY not set.")
        return "Error: No AI Key"

    model = "gemini-2.0-flash" 
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    You are the Chief AI Engineer of Project Athena.
    Analyze the following chronological git commit logs from our subsystems: Sovereign-Sentinel, FamPlanAI, Krypto, News Intelligence Portal, and Athena.
    
    1. SUMMARY: Generate a concise, high-level "Daily Engineering Log" for the Master Brain detailing major architectural changes and critical fixes. Ignore minor typos.
    2. PROACTIVE SYNERGY: You MUST analyze the collective capabilities built today and aggressively suggest cross-pollination. Identify at least one concrete opportunity where one project's new code, infrastructure, or AI agent can be directly plugged into or drastically benefit another active project.

    Format the final output beautifully in Markdown.
    
    COMMITS:
    {changes_text}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=30)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            logger.error(f"Gemini API Error: {res.text}")
            return f"AI Analysis Failed: {res.status_code}"
    except Exception as e:
        logger.error(f"Gemini Request Failed: {e}")
        return f"AI Analysis Failed: {e}"

def main():
    audit = AuditLogger("SS001-BrainUpdate")
    audit.log("JOB_START", "System", "Starting Daily Brain Update")
    logger.info("Starting Daily Brain Update...")
    
    # 1. State & Time
    state = load_state()
    now = datetime.datetime.now()
    # Default to 24 hours ago if no state
    last_run = state.get('last_run', (now - datetime.timedelta(days=1)).isoformat())
    
    all_changes = []
    has_changes = False
    
    # 2. Scan Projects
    for project in PROJECT_ROOTS:
        name = os.path.basename(project)
        logger.info(f"Scanning {name}...")
        changes = get_git_changes(project, last_run)
        
        if changes:
            has_changes = True
            all_changes.append(f"### {name}\n{changes}\n")
        else:
            logger.info(f"No changes in {name}.")

    # 3. Process
    if not has_changes:
        logger.info("No significant changes today. Skipping verification update.")
        # Minimal heartbeat? Or just update state.
        # Let's verify we update state so we don't re-scan old stuff if we run again.
        # Actually, if we skip, next time we want to scan since last *successful* update?
        # Let's only update state if we successfully processed or decided nothing needed processing.
        state['last_run'] = now.isoformat()
        save_state(state)
        audit.log("JOB_COMPLETE", "System", "No changes today, state updated", "SUCCESS")
        return

    combined_log = "\n".join(all_changes)
    
    # 4. Analyze
    logger.info("Analyzing with Gemini...")
    summary = analyze_with_gemini(combined_log)
    
    final_entry = f"**DAILY ENGINEERING LOG** ({now.strftime('%Y-%m-%d')})\n\n{summary}"
    
    # 5. Push to Brain
    creds = authenticate()
    if creds:
        service = build('docs', 'v1', credentials=creds)
        append_to_brain(service, final_entry)
        logger.info("Brain updated successfully.")
        audit.log("JOB_COMPLETE", "System", "Brain doc updated with today's changes", "SUCCESS")
        
        # Update State
        state['last_run'] = now.isoformat()
        save_state(state)
    else:
        logger.error("Authentication failed. Cannot update Brain.")
        audit.log("JOB_ERROR", "System", "Google auth failed", "ERROR")

if __name__ == "__main__":
    main()
