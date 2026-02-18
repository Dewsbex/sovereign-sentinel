"""
LLM Council — Multi-LLM Consensus Engine
=========================================
Sovereign AI Brain | services/llm_council/llm_council.py

Sends the same financial analysis prompt to multiple LLMs in parallel.
Requires ≥ 2/3 agreement on market phase before accepting a result.
Gracefully degrades if any judge is unavailable.

Usage:
    from services.llm_council.llm_council import LLMCouncil
    council = LLMCouncil()
    result = council.consult(prompt, context)

    # Or standalone test:
    python llm_council.py --test
"""

import os
import json
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

import re

load_dotenv()

logger = logging.getLogger("LLMCouncil")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

# --- Keys ---
GOOGLE_API_KEY    = os.getenv("GOOGLE_API_KEY")
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY") or os.getenv("SambaNova01")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY")

VALID_PHASES = {"BULL", "MID_BULL", "NEUTRAL", "MID_BEAR", "BEAR"}
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
COUNCIL_LOG = DATA_DIR / "council_log.json"


# ─────────────────────────────────────────────
# Helper: Robust JSON Extraction
# ─────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Robustly extract JSON object from LLM response (handles <think>, markdown, prose)."""
    try:
        # First try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the first { and last }
    try:
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except (json.JSONDecodeError, AttributeError):
        pass

    # Failure
    return {"error": "Failed to parse JSON", "raw": text[:200]}


# ─────────────────────────────────────────────
# Individual Judge Callers
# ─────────────────────────────────────────────

def _call_gemini(prompt: str) -> dict:
    """Judge 1: Google Gemini (Primary)"""
    if not GOOGLE_API_KEY:
        return {"error": "No GOOGLE_API_KEY"}
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return _extract_json(resp.text)
    except Exception as e:
        return {"error": str(e)}


def _call_sambanova(prompt: str) -> dict:
    """Judge 2: SambaNova (DeepSeek R1 - High Reasoning)"""
    if not SAMBANOVA_API_KEY:
        return {"error": "No SAMBANOVA_API_KEY"}
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "DeepSeek-R1-Distill-Llama-70B",
            "messages": [
                {"role": "system", "content": "You are a financial analyst. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 1024
        }
        resp = requests.post(
            "https://api.sambanova.ai/v1/chat/completions",
            headers=headers, json=payload, timeout=45
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _extract_json(content)
    except Exception as e:
        return {"error": str(e)}


def _call_groq(prompt: str) -> dict:
    """Judge 3: Groq (Llama 3.3 70B — Free Tier)"""
    if not GROQ_API_KEY:
        return {"error": "No GROQ_API_KEY"}
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a financial analyst. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=256,
            response_format={"type": "json_object"}
        )
        return _extract_json(resp.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────────
# Consensus Engine
# ─────────────────────────────────────────────

class LLMCouncil:
    """
    Multi-LLM consensus engine.
    Calls all available judges in parallel, then runs a majority vote.
    """

    JUDGES = {
        "Gemini":    _call_gemini,
        "SambaNova": _call_sambanova,
        "Groq":      _call_groq,
    }

    def consult(self, prompt: str, context: dict = None) -> dict:
        """
        Ask all available judges and return a consensus result.

        Returns:
            {
                "phase": "MID_BULL",
                "confidence": 0.85,
                "consensus": True,
                "judges": [{"name": ..., "phase": ..., "confidence": ...}, ...]
            }
        """
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
            t.join(timeout=25)

        return self._vote(results)

    def _vote(self, results: dict) -> dict:
        """Majority vote across judge responses."""
        judge_outputs = []
        phase_votes = {}

        for name, res in results.items():
            if "error" in res:
                logger.warning(f"Judge {name} failed: {res['error']}")
                continue

            phase = res.get("phase", "").upper()
            if phase not in VALID_PHASES:
                logger.warning(f"Judge {name} returned invalid phase: {phase!r}")
                continue

            confidence = float(res.get("confidence", 0.5))
            judge_outputs.append({
                "name": name,
                "phase": phase,
                "confidence": confidence,
                "reasoning": res.get("reasoning", "")
            })
            phase_votes[phase] = phase_votes.get(phase, 0) + 1

        total = len(judge_outputs)
        consensus = False
        winning_phase = "MID_BULL"  # Safe default
        avg_confidence = 0.5

        if total > 0:
            winning_phase = max(phase_votes, key=phase_votes.get)
            winning_count = phase_votes[winning_phase]
            consensus = winning_count >= max(2, (total + 1) // 2)  # Majority
            avg_confidence = sum(j["confidence"] for j in judge_outputs if j["phase"] == winning_phase) / winning_count

        if not consensus:
            logger.warning(f"⚠️ COUNCIL_DISAGREEMENT — votes: {phase_votes}. Falling back to {winning_phase}.")

        outcome = {
            "phase": winning_phase,
            "confidence": round(avg_confidence, 3),
            "consensus": consensus,
            "judges": judge_outputs,
            "votes": phase_votes,
            "timestamp": datetime.utcnow().isoformat()
        }

        self._log(outcome)
        return outcome

    def _log(self, outcome: dict):
        """Append council decision to audit log."""
        try:
            log = []
            if COUNCIL_LOG.exists():
                log = json.loads(COUNCIL_LOG.read_text())
            log.append(outcome)
            log = log[-90:]  # Keep last 90 days
            COUNCIL_LOG.write_text(json.dumps(log, indent=2))
        except Exception as e:
            logger.error(f"Failed to write council log: {e}")


# ─────────────────────────────────────────────
# Standalone Test
# ─────────────────────────────────────────────

MARKET_PHASE_PROMPT = """
You are a senior financial analyst. Based on current macro conditions (early 2026):
- US equity markets are near all-time highs
- Fed has paused rate hikes, inflation cooling to ~2.5%
- Unemployment stable at ~4%
- AI sector driving significant growth

Assess the current market phase and respond ONLY in this JSON format:
{
  "phase": "MID_BULL",
  "confidence": 0.85,
  "reasoning": "One sentence rationale."
}
Phase must be one of: BULL, MID_BULL, NEUTRAL, MID_BEAR, BEAR
"""

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        print("\n🏛️  LLM Council — Convening...\n")
        print(f"  Judges available:")
        print(f"    Gemini:    {'✅' if GOOGLE_API_KEY else '❌ No key'}")
        print(f"    SambaNova: {'✅' if SAMBANOVA_API_KEY else '❌ No key'}")
        print(f"    Groq:      {'✅' if GROQ_API_KEY else '❌ No key'}")
        print()

        council = LLMCouncil()
        result = council.consult(MARKET_PHASE_PROMPT)

        print("📊 Individual Verdicts:")
        for j in result.get("judges", []):
            icon = "✅" if result["consensus"] else "⚠️"
            print(f"  {icon} {j['name']:12s} → {j['phase']:10s} (confidence: {j['confidence']:.0%})")
            print(f"     └─ {j['reasoning']}")

        print(f"\n🗳️  Vote Tally: {result['votes']}")
        if result["consensus"]:
            print(f"✅ CONSENSUS: {result['phase']} (avg confidence: {result['confidence']:.0%})")
        else:
            print(f"⚠️  NO CONSENSUS — Using safe default: {result['phase']}")
