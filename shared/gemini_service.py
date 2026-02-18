"""
Gemini Service — Centralized AI orchestration for Antigravity.
Uses lightweight REST API (requests) to avoid grpcio/protobuf dependency hell on Windows ARM64.
"""
import os
import json
import time
import requests
import logging
from typing import Optional, Dict, List, Any
from secrets_loader import load_master_env, get_secret

# Load environment
load_master_env()
API_KEY = get_secret("GOOGLE_API_KEY")

DEFAULT_MODEL = "gemini-2.0-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]


class GeminiService:
    def __init__(self, model_name=DEFAULT_MODEL):
        if not API_KEY:
            raise ValueError("GOOGLE_API_KEY not found in master.env")
        self.model_name = model_name
        self.api_key = API_KEY
        self.session = requests.Session()

    def _post(self, endpoint, data):
        url = f"{BASE_URL}/{self.model_name}:{endpoint}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        try:
            response = self.session.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ Gemini API HTTP Error: {e.response.text}")
        except Exception as e:
            print(f"❌ Gemini API Connection Error: {e}")
        return None

    def generate_text(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """Generate plain text response via REST API."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
            "safetySettings": SAFETY_SETTINGS
        }
        
        result = self._post("generateContent", payload)
        if result:
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                print(f"⚠️ Unexpected Gemini response structure: {result}")
        return None

    def generate_json(self, prompt: str, schema: Optional[Dict] = None) -> Optional[Dict]:
        """Generate structured JSON response via REST API."""
        sys_instruction = "You must respond with valid JSON only. No markdown formatting."
        if schema:
            sys_instruction += f"\nSchema: {json.dumps(schema)}"

        full_prompt = f"{sys_instruction}\n\nUser: {prompt}"

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            },
            "safetySettings": SAFETY_SETTINGS
        }
        
        result = self._post("generateContent", payload)
        if result:
            try:
                text = result['candidates'][0]['content']['parts'][0]['text']
                # Clean markdown if present
                if text.strip().startswith("```json"):
                    text = text.strip()[7:-3]
                return json.loads(text)
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                 print(f"⚠️ JSON parsing failed: {e}")
        return None

# Shared Singleton Instance
try:
    gemini = GeminiService()
except Exception as e:
    print(f"⚠️ Failed to initialize shared GeminiService: {e}")
    gemini = None


if __name__ == "__main__":
    print("=== Gemini Service Test (REST) ===")
    if gemini:
        print("✅ Service Initialized")
        
        # Test Text
        print("\n📝 Testing Text Generation...")
        resp = gemini.generate_text("Explain quantum entanglement in one sentence.")
        print(f"   Response: {resp}")
        
        # Test JSON
        print("\n📊 Testing JSON Generation...")
        schema = {"tickers": ["str"], "sentiment": "str"}
        json_resp = gemini.generate_json("Analyze sentiment for AAPL and TSLA: Bullish on tech.", schema)
        print(f"   Response: {json_resp}")
    else:
        print("❌ Service Unavailable")
