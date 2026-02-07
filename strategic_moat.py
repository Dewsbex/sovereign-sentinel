"""
Wealth Seeker v0.01 - Strategic Moat Analysis (strategic_moat.py)
==================================================================
Job A: The Strategic Fortress - 95% Advisory Moat Research
"""

import json
import os
from typing import Dict, List, Any
import google.generativeai as genai
import requests


class MoatAnalyzer:
    """Analyzes companies for economic moats using UDR framework"""
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    def analyze_roic_vs_wacc(self, ticker: str, financials: Dict[str, Any]) -> Dict[str, Any]:
        """
        ROIC vs WACC Moat Indicator
        Requirement: ROIC must exceed WACC by at least 2% for 5 consecutive years
        """
        # This would typically fetch real financial data
        # For now, we'll use Gemini to analyze available data
        
        prompt = f"""
Analyze the Return on Invested Capital (ROIC) vs Weighted Average Cost of Capital (WACC) for {ticker}.

Requirements for a strong moat:
- ROIC must exceed WACC by at least 2 percentage points
- This spread must be maintained for at least 5 consecutive years

Please provide:
1. Current ROIC vs WACC spread
2. Historical trend over past 5 years
3. Whether the company meets the moat criteria
4. Key drivers of capital efficiency

Format response as JSON:
{{
  "current_roic": <number>,
  "current_wacc": <number>,
  "spread": <number>,
  "five_year_consistent": <boolean>,
  "moat_score": <1-10>,
  "analysis": "<text>"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip())
        except Exception as e:
            print(f"⚠️  ROIC/WACC analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_gross_margin_stability(self, ticker: str) -> Dict[str, Any]:
        """
        Gross Margin Stability Indicator
        Requirement: Standard deviation of Gross Margin < 2%
        """
        prompt = f"""
Analyze the gross margin stability for {ticker} over the past 5 years.

Requirements for a strong moat:
- Standard deviation of gross margins must be < 2%
- Indicates pricing power and consistent competitive advantage

Please provide:
1. Gross margin trend (last 5 years)
2. Standard deviation of gross margins
3. Whether margins are expanding, stable, or contracting
4. Key factors affecting margin stability

Format response as JSON:
{{
  "gross_margins_5yr": [<array of yearly %s>],
  "std_deviation": <number>,
  "trend": "<expanding|stable|contracting>",
  "meets_criteria": <boolean>,
  "moat_score": <1-10>,
  "analysis": "<text>"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip())
        except Exception as e:
            print(f"⚠️  Margin stability analysis failed: {e}")
            return {"error": str(e)}
    
    def analyze_pricing_power(self, ticker: str) -> Dict[str, Any]:
        """
        Pricing Power via Gemini Deep Research
        Analyzes competitive landscape and ability to raise prices
        """
        prompt = f"""
Conduct a deep competitive analysis of {ticker} to assess pricing power.

Evaluate:
1. Market position and competitive advantages
2. Brand strength and customer loyalty
3. Switching costs for customers
4. Historical ability to pass costs to consumers
5. Competitive intensity in the industry
6. Barriers to entry for new competitors

Provide a comprehensive moat dossier assessing pricing power.

Format response as JSON:
{{
  "pricing_power_score": <1-10>,
  "competitive_position": "<leader|strong|moderate|weak>",
  "key_advantages": [<array of strings>],
  "key_risks": [<array of strings>],
  "moat_width": "<wide|moderate|narrow|none>",
  "investment_thesis": "<text>",
  "recommendation": "<strong_buy|buy|hold|avoid>"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            return json.loads(response.text.strip())
        except Exception as e:
            print(f"⚠️  Pricing power analysis failed: {e}")
            return {"error": str(e)}
    
    def generate_moat_dossier(self, ticker: str) -> str:
        """
        Generate comprehensive moat analysis report
        Combines all three indicators into a strategic recommendation
        """
        print(f"\n{'='*60}")
        print(f"🏰 Generating Moat Dossier for {ticker}")
        print(f"{'='*60}\n")
        
        # Run all three analyses
        roic_analysis = self.analyze_roic_vs_wacc(ticker, {})
        margin_analysis = self.analyze_gross_margin_stability(ticker)
        pricing_analysis = self.analyze_pricing_power(ticker)
        
        # Compile dossier
        dossier = f"""
🏰 **MOAT DOSSIER: {ticker}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Generated: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*

**📊 ROIC vs WACC Analysis**
• Current Spread: {roic_analysis.get('spread', 'N/A')}%
• 5-Year Consistency: {'✅' if roic_analysis.get('five_year_consistent') else '❌'}
• Moat Score: {roic_analysis.get('moat_score', 'N/A')}/10

**📈 Gross Margin Stability**
• Std Deviation: {margin_analysis.get('std_deviation', 'N/A')}%
• Trend: {margin_analysis.get('trend', 'N/A').title()}
• Criteria Met: {'✅' if margin_analysis.get('meets_criteria') else '❌'}
• Moat Score: {margin_analysis.get('moat_score', 'N/A')}/10

**💪 Pricing Power Assessment**
• Power Score: {pricing_analysis.get('pricing_power_score', 'N/A')}/10
• Position: {pricing_analysis.get('competitive_position', 'N/A').title()}
• Moat Width: {pricing_analysis.get('moat_width', 'N/A').title()}

**🎯 Investment Thesis**
{pricing_analysis.get('investment_thesis', 'Analysis pending...')}

**⚡ Key Advantages**
{chr(10).join(['• ' + adv for adv in pricing_analysis.get('key_advantages', [])])}

**⚠️ Key Risks**
{chr(10).join(['• ' + risk for risk in pricing_analysis.get('key_risks', [])])}

**📋 RECOMMENDATION: {pricing_analysis.get('recommendation', 'HOLD').upper()}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*This is an ADVISORY recommendation*
*No auto-execution. Manual review required.*
"""
        
        return dossier
    
    def send_to_telegram(self, dossier: str, ticker: str):
        """Send moat dossier to Telegram with approval link"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("⚠️  Telegram not configured")
            print(dossier)
            return
        
        # Add approval button (would link to dashboard)
        dashboard_url = "https://your-cloudflare-domain.pages.dev"
        message = dossier + f"\n\n[📊 Review Dashboard]({dashboard_url})"
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print(f"✅ Moat Dossier sent to Telegram")
        except Exception as e:
            print(f"❌ Failed to send to Telegram: {e}")
            print(dossier)


def main():
    """Entry point for strategic_moat.py"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python strategic_moat.py <TICKER>")
        sys.exit(1)
    
    ticker = sys.argv[1]
    
    analyzer = MoatAnalyzer()
    dossier = analyzer.generate_moat_dossier(ticker)
    analyzer.send_to_telegram(dossier, ticker)
    
    print("\n✅ Moat analysis complete")


if __name__ == "__main__":
    main()
