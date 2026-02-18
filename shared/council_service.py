"""
Council Service — Multi-Model AI Consensus Engine (Pure REST)
=============================================================
Antigravity Shared Brain | orchestrator/council_service.py

Sends the same prompt to 3 LLMs in parallel via REST APIs (no SDKs).
Requires ≥ 2/3 agreement before accepting a result.
Gracefully degrades if any judge is unavailable.

Judges:
  1. SambaNova  — DeepSeek-R1-Distill-Llama-70B (Reasoning)
  2. Gemini     — Gemini 2.0 Flash (Primary)
  3. Groq       — Llama 3.3 70B (Speed)

Usage:
    from council_service import council
    result = council.consult(prompt)
    verified = council.verify("Is AAPL a buy?", "Yes, strong ORB breakout")
"""

import os
import re
import json
import time
import logging
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from secrets_loader import load_master_env, get_secret

# Load environment
load_master_env()

logger = logging.getLogger("Council")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

# --- Keys ---
GOOGLE_API_KEY    = get_secret("GOOGLE_API_KEY")
SAMBANOVA_API_KEY = get_secret("SAMBANOVA_API_KEY")
GROQ_API_KEY      = get_secret("GROQ_API_KEY")

# --- Audit Log ---
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
COUNCIL_LOG = DATA_DIR / "council_log.json"


# ─────────────────────────────────────────────
# Helper: Robust JSON Extraction
# ─────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """
    Robustly extract JSON from LLM output.
    Handles: <think> blocks, ```json fences, prose around JSON.
    """
    if not text:
        return {"error": "Empty response"}

    # Strip <think>...</think> blocks (DeepSeek R1)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Direct parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find first { ... last }
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    return {"error": "Failed to parse JSON", "raw": text[:300]}


# ─────────────────────────────────────────────
# Judge Callers (Pure REST — No SDKs)
# ─────────────────────────────────────────────

def _call_gemini(prompt: str) -> dict:
    """Judge 1: Google Gemini 2.0 Flash (REST)"""
    if not GOOGLE_API_KEY:
        return {"error": "No GOOGLE_API_KEY"}
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "responseMimeType": "application/json"
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        }
        resp = requests.post(url, json=payload, timeout=25)
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(text)
    except Exception as e:
        return {"error": f"Gemini: {e}"}


def _call_sambanova(prompt: str) -> dict:
    """Judge 2: SambaNova DeepSeek-R1-Distill-Llama-70B (OpenAI-compatible REST)"""
    if not SAMBANOVA_API_KEY:
        return {"error": "No SAMBANOVA_API_KEY"}
    try:
        resp = requests.post(
            "https://api.sambanova.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "DeepSeek-R1-Distill-Llama-70B",
                "messages": [
                    {"role": "system", "content": "You are an expert analyst. Respond ONLY in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6,
                "max_tokens": 1024
            },
            timeout=45
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _extract_json(content)
    except Exception as e:
        return {"error": f"SambaNova: {e}"}


def _call_groq(prompt: str) -> dict:
    """Judge 3: Groq Llama 3.3 70B (OpenAI-compatible REST)"""
    if not GROQ_API_KEY:
        return {"error": "No GROQ_API_KEY"}
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are an expert analyst. Respond ONLY in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 512,
                "response_format": {"type": "json_object"}
            },
            timeout=15
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _extract_json(content)
    except Exception as e:
        return {"error": f"Groq: {e}"}


# ─────────────────────────────────────────────
# Council Engine
# ─────────────────────────────────────────────

class CouncilService:
    """
    Multi-LLM consensus engine.
    Calls all available judges in parallel, then runs a majority vote.
    Pure REST — no SDK dependencies.
    """

    JUDGES = {
        "Gemini":    _call_gemini,
        "SambaNova": _call_sambanova,
        "Groq":      _call_groq,
    }

    def _call_all(self, prompt: str) -> dict:
        """Call all judges in parallel, return raw results dict."""
        results = {}
        threads = []

        def call_judge(name, fn):
            try:
                results[name] = fn(prompt)
            except Exception as e:
                results[name] = {"error": str(e)}

        for name, fn in self.JUDGES.items():
            t = threading.Thread(target=call_judge, args=(name, fn))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=50)

        return results

    def consult(self, prompt: str, vote_key: str = "phase") -> dict:
        """
        General consensus query. All judges answer the same prompt.
        vote_key: the JSON key to use for majority voting (e.g. "phase", "verdict", "answer").

        Returns:
            {
                "answer": "MID_BULL",
                "confidence": 0.85,
                "consensus": True,
                "judges": [{"name": ..., "response": ...}, ...]
            }
        """
        results = self._call_all(prompt)
        return self._vote(results, vote_key)

    def verify(self, question: str, expected_answer: str) -> dict:
        """
        Accuracy verification mode.
        Asks each judge: "Is this answer correct?" and votes on agreement.

        Returns:
            {
                "verified": True/False,
                "confidence": 0.9,
                "judges": [...]
            }
        """
        prompt = f"""
You are an accuracy auditor. A system produced the following answer to a question.
Evaluate whether the answer is CORRECT, PARTIALLY_CORRECT, or INCORRECT.

QUESTION: {question}
ANSWER: {expected_answer}

Respond ONLY in this JSON format:
{{
    "verdict": "CORRECT|PARTIALLY_CORRECT|INCORRECT",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}}
"""
        results = self._call_all(prompt)
        outcome = self._vote(results, vote_key="verdict")

        # Map verdict to boolean
        outcome["verified"] = outcome.get("answer", "").upper() == "CORRECT"
        return outcome

    def _vote(self, results: dict, vote_key: str) -> dict:
        """Majority vote across judge responses."""
        judge_outputs = []
        votes = {}

        for name, res in results.items():
            if "error" in res:
                logger.warning(f"Judge {name} failed: {res['error']}")
                judge_outputs.append({"name": name, "error": res["error"]})
                continue

            answer = str(res.get(vote_key, "")).upper()
            confidence = float(res.get("confidence", 0.5))
            reasoning = res.get("reasoning", "")

            judge_outputs.append({
                "name": name,
                "answer": answer,
                "confidence": confidence,
                "reasoning": reasoning,
                "full_response": res
            })
            votes[answer] = votes.get(answer, 0) + 1

        valid = [j for j in judge_outputs if "error" not in j]
        total = len(valid)
        consensus = False
        winning = "UNKNOWN"
        avg_conf = 0.5

        if total > 0:
            winning = max(votes, key=votes.get)
            winning_count = votes[winning]
            consensus = winning_count >= max(2, (total + 1) // 2)
            matching = [j for j in valid if j["answer"] == winning]
            avg_conf = sum(j["confidence"] for j in matching) / len(matching)

        if not consensus:
            logger.warning(f"⚠️ COUNCIL DISAGREEMENT — votes: {votes}")

        outcome = {
            "answer": winning,
            "confidence": round(avg_conf, 3),
            "consensus": consensus,
            "judges": judge_outputs,
            "votes": votes,
            "timestamp": datetime.utcnow().isoformat()
        }

        self._log(outcome)
        return outcome

    def _log(self, outcome: dict):
        """Append council decision to local audit log."""
        try:
            log = []
            if COUNCIL_LOG.exists():
                log = json.loads(COUNCIL_LOG.read_text())
            log.append(outcome)
            log = log[-90:]  # Keep last 90 sessions
            COUNCIL_LOG.write_text(json.dumps(log, indent=2))
        except Exception as e:
            logger.error(f"Failed to write council log: {e}")


# ─────────────────────────────────────────────
# Shared Singleton
# ─────────────────────────────────────────────
try:
    council = CouncilService()
except Exception as e:
    print(f"⚠️ Failed to initialize CouncilService: {e}")
    council = None


# ─────────────────────────────────────────────
# Standalone Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("\n🏛️  Antigravity Council — Convening...\n")
    print(f"  Judges available:")
    print(f"    Gemini:    {'✅' if GOOGLE_API_KEY else '❌ No key'}")
    print(f"    SambaNova: {'✅' if SAMBANOVA_API_KEY else '❌ No key'}")
    print(f"    Groq:      {'✅' if GROQ_API_KEY else '❌ No key'}")
    print()

    if "--test" in sys.argv or len(sys.argv) == 1:
        test_prompt = """
Assess the current global market regime (February 2026).
Consider: Fed policy, inflation, yield curve, growth outlook.

Respond ONLY in this JSON format:
{
    "phase": "BULL|MID_BULL|NEUTRAL|MID_BEAR|BEAR",
    "confidence": 0.0-1.0,
    "reasoning": "One sentence rationale."
}
"""
        print("📊 Testing: Market Phase Consensus...\n")
        result = council.consult(test_prompt, vote_key="phase")

        for j in result.get("judges", []):
            if "error" in j:
                print(f"  ❌ {j['name']:12s} → FAILED ({j['error'][:60]})")
            else:
                print(f"  ✅ {j['name']:12s} → {j['answer']:10s} (confidence: {j['confidence']:.0%})")
                print(f"     └─ {j.get('reasoning', 'N/A')}")

        print(f"\n🗳️  Vote Tally: {result['votes']}")
        if result["consensus"]:
            print(f"✅ CONSENSUS: {result['answer']} (avg confidence: {result['confidence']:.0%})")
        else:
            print(f"⚠️  NO CONSENSUS — Using plurality: {result['answer']}")

    if "--verify" in sys.argv:
        print("\n🔍 Testing: Verification Mode...\n")
        vresult = council.verify(
            "Is now a good time to buy US equities?",
            "Yes, the market is in a mid-bull phase with strong tech leadership."
        )
        print(f"  Verified: {vresult['verified']}")
        print(f"  Confidence: {vresult['confidence']:.0%}")
        for j in vresult.get("judges", []):
            if "error" not in j:
                print(f"  {j['name']:12s} → {j['answer']} ({j.get('reasoning', '')})")
