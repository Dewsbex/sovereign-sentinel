"""
Wealth Seeker v0.01 - Macro-Clock System (macro_clock.py)
==========================================================
Market phase detection with sector target allocation.
Uses Gemini Deep Research to analyze macro-economic indicators.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google.generativeai not installed, using fallback mode")


# Phase-Bias Matrix: Sector Target Weights by Market Phase
PHASE_TARGETS = {
    "EARLY_BULL": {
        "Technology": 25.0,
        "Consumer Discretionary": 20.0,
        "Financials": 15.0,
        "Industrials": 10.0,
        "Materials": 8.0,
        "Energy": 7.0,
        "Healthcare": 7.0,
        "Consumer Staples": 5.0,
        "Utilities": 3.0,
        "Cash": 0.0
    },
    "MID_BULL": {
        "Industrials": 18.0,
        "Materials": 15.0,
        "Energy": 15.0,
        "Technology": 15.0,
        "Financials": 12.0,
        "Consumer Discretionary": 10.0,
        "Healthcare": 8.0,
        "Consumer Staples": 5.0,
        "Utilities": 2.0,
        "Cash": 0.0
    },
    "LATE_BULL": {
        "Healthcare": 22.0,
        "Consumer Staples": 20.0,
        "Energy": 15.0,
        "Utilities": 12.0,
        "Materials": 10.0,
        "Industrials": 8.0,
        "Financials": 6.0,
        "Technology": 5.0,
        "Consumer Discretionary": 2.0,
        "Cash": 0.0
    },
    "BEAR": {
        "Cash": 30.0,
        "Utilities": 25.0,
        "Healthcare": 20.0,
        "Consumer Staples": 15.0,
        "Energy": 5.0,
        "Technology": 3.0,
        "Financials": 2.0,
        "Consumer Discretionary": 0.0,
        "Industrials": 0.0,
        "Materials": 0.0
    }
}


class MacroClock:
    """Market phase detector using Gemini Deep Research"""
    
    def __init__(self):
        self.model = None
        if GEMINI_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.model = genai.GenerativeModel('gemini-pro')
        
        self.cache_path = "data/macro_phase_cache.json"
        self.cache_duration_hours = 24  # Refresh once per day
    
    def load_cached_phase(self) -> Tuple[str, bool]:
        """Load cached market phase if fresh"""
        try:
            with open(self.cache_path, 'r') as f:
                cache = json.load(f)
            
            cached_time = datetime.fromisoformat(cache.get("timestamp", "2000-01-01"))
            age = datetime.utcnow() - cached_time
            
            if age < timedelta(hours=self.cache_duration_hours):
                return cache.get("phase", "MID_BULL"), True
            
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        return "MID_BULL", False  # Default fallback
    
    def save_phase_cache(self, phase: str, confidence: float, analysis: str):
        """Save market phase to cache"""
        cache = {
            "phase": phase,
            "confidence": confidence,
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def detect_market_phase(self) -> Dict[str, any]:
        """
        Analyze macro-economic indicators to determine market phase.
        Returns: {"phase": str, "confidence": float, "analysis": str, "cached": bool}
        """
        # Check cache first
        cached_phase, is_fresh = self.load_cached_phase()
        if is_fresh:
            print(f"📦 Using cached phase: {cached_phase}")
            return {
                "phase": cached_phase,
                "confidence": 0.85,
                "analysis": "Cached from previous analysis",
                "cached": True
            }
        
        # Check if Gemini is available
        if not self.model:
            print("⚠️  Gemini unavailable, using MID_BULL fallback")
            return {
                "phase": "MID_BULL",
                "confidence": 0.5,
                "analysis": "Gemini API not configured, using default phase",
                "fortress_alert": False,
                "cached": False
            }
        
        print("🔍 Analyzing macro-economic indicators...")
        
        prompt = f"""
You are a macro-economic analyst. Analyze the current market phase based on available data.

**Your task:** Classify the current market into ONE of these phases:
- EARLY_BULL: Post-recession recovery, low rates, high growth potential
- MID_BULL: Sustained expansion, moderate growth, broad market participation
- LATE_BULL: Late cycle, rising rates, defensive rotation begins
- BEAR: Recession/contraction, negative growth, risk-off sentiment

**Indicators to consider:**
1. Federal Reserve policy (rate trajectory)
2. Inflation trends (CPI)
3. Yield curve (normal vs inverted)
4. Economic growth (GDP estimates)
5. Market breadth and sentiment
6. Unemployment trends

**Today's date:** {datetime.utcnow().strftime('%Y-%m-%d')}

Respond ONLY with valid JSON:
{{
  "phase": "EARLY_BULL|MID_BULL|LATE_BULL|BEAR",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of key factors driving this classification",
  "key_indicators": {{
    "fed_policy": "hawkish|neutral|dovish",
    "inflation_trend": "rising|stable|falling",
    "yield_curve": "normal|flat|inverted",
    "growth_outlook": "strong|moderate|weak|negative"
  }},
  "fortress_alert": true|false
}}

Set "fortress_alert" to true if this represents a shift to LATE_BULL or BEAR that warrants defensive repositioning.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            
            phase = result.get("phase", "MID_BULL")
            confidence = result.get("confidence", 0.5)
            analysis = result.get("reasoning", "Analysis unavailable")
            
            # Validate phase
            if phase not in PHASE_TARGETS:
                print(f"⚠️  Invalid phase '{phase}', defaulting to MID_BULL")
                phase = "MID_BULL"
            
            # Save to cache
            self.save_phase_cache(phase, confidence, analysis)
            
            print(f"✅ Market Phase: {phase} (Confidence: {confidence:.0%})")
            
            return {
                "phase": phase,
                "confidence": confidence,
                "analysis": analysis,
                "key_indicators": result.get("key_indicators", {}),
                "fortress_alert": result.get("fortress_alert", False),
                "cached": False
            }
            
        except Exception as e:
            print(f"❌ Macro-Clock analysis failed: {e}")
            # Fallback to MID_BULL
            return {
                "phase": "MID_BULL",
                "confidence": 0.0,
                "analysis": f"Analysis failed, using default: {str(e)}",
                "fortress_alert": False,
                "cached": False
            }
    
    def get_sector_targets(self, phase: str = None) -> Dict[str, float]:
        """Get sector target weights for a given market phase"""
        if phase is None:
            phase_data = self.detect_market_phase()
            phase = phase_data["phase"]
        
        return PHASE_TARGETS.get(phase, PHASE_TARGETS["MID_BULL"])
    
    def calculate_sector_deltas(self, current_allocation: Dict[str, float], phase: str = None) -> Dict[str, Dict]:
        """
        Calculate delta between current allocation and Macro-Clock targets
        
        Returns: {
            "Technology": {
                "current": 15.2,
                "target": 25.0,
                "delta": -9.8,
                "status": "UNDER"
            },
            ...
        }
        """
        targets = self.get_sector_targets(phase)
        deltas = {}
        
        for sector in targets:
            current = current_allocation.get(sector, 0.0)
            target = targets[sector]
            delta = current - target
            
            deltas[sector] = {
                "current": current,
                "target": target,
                "delta": delta,
                "status": "OVER" if delta > 0 else "UNDER" if delta < 0 else "MATCH"
            }
        
        return deltas


def main():
    """Test the Macro-Clock system"""
    import sys
    
    clock = MacroClock()
    
    if "--test" in sys.argv:
        print("\n🕒 Testing Macro-Clock System\n")
        
        # Test phase detection
        result = clock.detect_market_phase()
        print(f"\nPhase: {result['phase']}")
        print(f"Confidence: {result['confidence']:.0%}")
        print(f"Analysis: {result['analysis']}")
        print(f"Fortress Alert: {result['fortress_alert']}")
        
        # Test sector targets
        print(f"\n📊 Sector Targets for {result['phase']}:")
        targets = clock.get_sector_targets(result['phase'])
        for sector, weight in sorted(targets.items(), key=lambda x: x[1], reverse=True):
            print(f"  {sector:25s} {weight:5.1f}%")
        
        # Test delta calculation
        print(f"\n📈 Example Delta Calculation:")
        sample_allocation = {
            "Technology": 15.0,
            "Healthcare": 10.0,
            "Financials": 8.0,
            "Cash": 5.0
        }
        
        deltas = clock.calculate_sector_deltas(sample_allocation, result['phase'])
        for sector, data in sorted(deltas.items(), key=lambda x: abs(x[1]['delta']), reverse=True):
            if data['current'] > 0 or data['target'] > 0:
                print(f"  {sector:25s} Current: {data['current']:5.1f}% | Target: {data['target']:5.1f}% | {data['status']}")


if __name__ == "__main__":
    main()
