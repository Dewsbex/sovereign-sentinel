"""
LLM Review Panel — AI-powered pre-trade validation for Krypto.
Uses the Council Service (3-LLM consensus) to review trade signals before execution.
Falls back to Gemini-only if Council unavailable.
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("LLMReview")

# Try to import Council Service from Sovereign-Sentinel shared/
# On VPS: /home/ubuntu/Sovereign-Sentinel/shared/
# On Windows: C:\Users\steve\Sovereign-Sentinel\shared\
SENTINEL_PATHS = [
    Path("/home/ubuntu/Sovereign-Sentinel"),
    Path(r"C:\Users\steve\Sovereign-Sentinel"),
]

for p in SENTINEL_PATHS:
    shared_path = p / "shared"
    if shared_path.exists() and str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
        # Also add parent so secrets_loader can be found
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

# Attempt imports
COUNCIL_AVAILABLE = False
GEMINI_AVAILABLE = False

try:
    from council_service import CouncilService
    COUNCIL_AVAILABLE = True
    logger.info("Council Service (3-LLM) loaded")
except ImportError:
    logger.warning("Council Service not available")

try:
    from gemini_service import gemini as gemini_instance
    if gemini_instance:
        GEMINI_AVAILABLE = True
        logger.info("Gemini Service loaded as fallback")
except ImportError:
    logger.warning("Gemini Service not available")


# ─── Trade Review Prompt ───
REVIEW_PROMPT_TEMPLATE = """You are an expert crypto trading analyst reviewing a trade signal.

SIGNAL DETAILS:
- Asset: {asset}
- Direction: {direction}
- Entry Price: {entry_price}
- Stop Loss: {stop_loss}
- Take Profit: {take_profit}
- Risk:Reward Ratio: {rr_ratio}
- Strategy: {strategy}

MARKET CONTEXT:
- Fear & Greed Index: {fear_greed}
- Session: {session}
- Recent Headlines: {headlines}

Evaluate this trade. Respond in JSON format:
{{
    "verdict": "APPROVE" or "REJECT",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "risk_adjustment": 1.0 (keep as-is) or 0.5-0.75 (reduce size) or 0.0 (reject)
}}

Rules:
- APPROVE if risk:reward >= 1.5 and conditions support the direction
- REJECT if you see clear reasons the trade will fail (against trend, bad R:R, extreme conditions)
- Be decisive. Brief reasoning only.
"""


def review_trade(signal: dict, context: dict = None) -> dict:
    """
    Submit a trade signal for AI review before execution.
    
    Args:
        signal: {"type": "BUY", "price": ..., "stop_loss": ..., "take_profit": ..., "asset": ...}
        context: {"fear_greed": 45, "session": "NY", "headlines": [...]}
    
    Returns:
        {"approved": True/False, "confidence": 0.85, "reasoning": "...", "risk_adjustment": 1.0}
    """
    if not COUNCIL_AVAILABLE and not GEMINI_AVAILABLE:
        logger.warning("No AI service available — auto-approving trade")
        return {"approved": True, "confidence": 0.0, "reasoning": "No AI service", "risk_adjustment": 1.0}
    
    context = context or {}
    
    # Build the prompt
    entry = signal.get("price", 0)
    sl = signal.get("stop_loss", 0)
    tp = signal.get("take_profit", 0)
    risk = abs(entry - sl) if sl else 1
    rr = abs(tp - entry) / risk if risk > 0 else 0
    
    headlines = context.get("headlines", [])
    headline_text = "; ".join(headlines[:5]) if headlines else "No headlines available"
    
    prompt = REVIEW_PROMPT_TEMPLATE.format(
        asset=signal.get("asset", "BTC/GBP"),
        direction=signal.get("type", "BUY"),
        entry_price=f"£{entry:.2f}" if entry else "N/A",
        stop_loss=f"£{sl:.2f}" if sl else "N/A",
        take_profit=f"£{tp:.2f}" if tp else "N/A",
        rr_ratio=f"{rr:.2f}",
        strategy=signal.get("strategy", "ORB Breakout"),
        fear_greed=context.get("fear_greed", "N/A"),
        session=context.get("session", "Unknown"),
        headlines=headline_text
    )
    
    try:
        result = None
        
        # Primary: Council (3-LLM consensus)
        if COUNCIL_AVAILABLE:
            logger.info("Submitting trade to LLM Council for review...")
            council = CouncilService()
            council_result = council.consult(prompt, vote_key="verdict")
            
            if council_result and council_result.get("answer"):
                verdict = council_result["answer"].upper()
                confidence = council_result.get("confidence", 0.5)
                consensus = council_result.get("consensus", False)
                
                # Extract reasoning from judges
                judges = council_result.get("judges", [])
                reasoning_parts = []
                risk_adjustments = []
                for j in judges:
                    resp = j.get("response", {})
                    if isinstance(resp, dict):
                        reasoning_parts.append(resp.get("reasoning", ""))
                        ra = resp.get("risk_adjustment", 1.0)
                        try:
                            risk_adjustments.append(float(ra))
                        except (ValueError, TypeError):
                            pass
                
                avg_risk_adj = sum(risk_adjustments) / len(risk_adjustments) if risk_adjustments else 1.0
                
                result = {
                    "approved": verdict == "APPROVE",
                    "confidence": confidence,
                    "consensus": consensus,
                    "reasoning": "; ".join(r for r in reasoning_parts if r)[:200],
                    "risk_adjustment": round(avg_risk_adj, 2),
                    "source": "Council (3-LLM)"
                }
        
        # Fallback: Gemini only
        if result is None and GEMINI_AVAILABLE:
            logger.info("Submitting trade to Gemini for review...")
            schema = {"verdict": "str", "confidence": "float", "reasoning": "str", "risk_adjustment": "float"}
            gemini_result = gemini_instance.generate_json(prompt, schema)
            
            if gemini_result:
                result = {
                    "approved": gemini_result.get("verdict", "").upper() == "APPROVE",
                    "confidence": float(gemini_result.get("confidence", 0.5)),
                    "reasoning": gemini_result.get("reasoning", "")[:200],
                    "risk_adjustment": float(gemini_result.get("risk_adjustment", 1.0)),
                    "source": "Gemini (single)"
                }
        
        if result:
            logger.info(f"LLM REVIEW: {'APPROVED' if result['approved'] else 'REJECTED'} "
                       f"(confidence={result['confidence']:.0%}, adj={result['risk_adjustment']}) "
                       f"— {result.get('source', 'unknown')}")
            return result
        
    except Exception as e:
        logger.error(f"LLM Review failed: {e}")
    
    # Fail open — if AI review fails, don't block the trade
    logger.warning("LLM Review inconclusive — fail open (approving)")
    return {"approved": True, "confidence": 0.0, "reasoning": "Review failed — fail open", "risk_adjustment": 1.0}


if __name__ == "__main__":
    print("=== LLM Review Panel Test ===")
    
    test_signal = {
        "type": "BUY",
        "price": 82500.00,
        "stop_loss": 82000.00,
        "take_profit": 83250.00,
        "asset": "BTC/GBP"
    }
    
    test_context = {
        "fear_greed": 55,
        "session": "NY",
        "headlines": ["Bitcoin breaks above key resistance", "Fed signals rate pause"]
    }
    
    result = review_trade(test_signal, test_context)
    print(f"Approved: {result['approved']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Risk Adjustment: {result['risk_adjustment']}")
    print(f"Reasoning: {result['reasoning']}")
