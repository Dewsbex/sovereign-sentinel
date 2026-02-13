"""
Wealth Seeker v0.01 - Strategic Moat Analysis (strategic_moat.py)
==================================================================
Job A: The Strategic Fortress - 95% Advisory Moat Research
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
# Removed standalone genai import - using consolidated client
import requests
from trading212_client import Trading212Client


class MoatAnalyzer:
    """Analyzes companies for economic moats using UDR framework"""
    
    def __init__(self):
        # Consolidated Client (Trading + AI + Telegram)
        self.client = Trading212Client()
        self.telegram_token = self.client.bot_token
        self.telegram_chat_id = self.client.chat_id
    
    def _query_ai(self, prompt: str) -> str:
        """Wrapper for client's Gemini engine"""
        return self.client.gemini_query(prompt)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Helper to safely parse JSON from AI response"""
        try:
            # Clean markdown code blocks
            cleaned = response_text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON Parse Error: {e}")
            print(f"Raw text: {response_text[:100]}...")
            return {"error": "JSON_PARSE_FAILED", "raw_text": response_text}

    def validate_ticker_against_database(self, ticker: str, company_name: str) -> Dict[str, Any]:
        """
        v1.9.4 TICKER HALLUCINATION GUARD
        
        Prevents research on wrong company due to ticker confusion (e.g., Viatris vs. Vital Farms).
        
        Requirements:
        - Fuzzy match company name against instruments.json entry
        - Similarity must be >= 90%
        - Hard abort if mismatch detected
        """
        from difflib import SequenceMatcher
        
        # Load instruments database
        try:
            with open('data/instruments.json', 'r') as f:
                instruments_data = json.load(f)
            instruments = instruments_data.get('instruments', [])
        except FileNotFoundError:
            raise RuntimeError(
                "TICKER_VALIDATION_FAILED: instruments.json not found\n"
                "Run: python build_universe.py"
            )
        
        # Find ticker in database
        ticker_entry = None
        for instrument in instruments:
            if instrument.get('ticker') == ticker:
                ticker_entry = instrument
                break
        
        if not ticker_entry:
            raise RuntimeError(
                f"TICKER_NOT_FOUND: {ticker} not in instruments.json\n"
                f"This ticker is not available for research."
            )
        
        # Get official company name from database
        official_name = ticker_entry.get('company', '').strip().lower()
        research_name = company_name.strip().lower()
        
        # Calculate fuzzy match similarity (0.0 to 1.0)
        similarity = SequenceMatcher(None, official_name, research_name).ratio()
        similarity_pct = similarity * 100
        
        # v1.9.4 requirement: >= 90% match
        if similarity_pct < 90.0:
            print(f"\n{'='*70}")
            print(f"🚨 TICKER HALLUCINATION DETECTED")
            print(f"{'='*70}")
            print(f"⛔ Company name mismatch for ticker: {ticker}")
            print(f"   Official (instruments.json): {ticker_entry.get('company')}")
            print(f"   Research request: {company_name}")
            print(f"   Similarity: {similarity_pct:.1f}% (threshold: 90%)")
            print(f"\n💡 This prevents researching the wrong company.")
            print(f"   Example: Viatris (VTRS) vs. Vital Farms (VITL)")
            print(f"{'='*70}\n")
            raise RuntimeError(
                f"TICKER_HALLUCINATION: Name mismatch detected\n"
                f"Ticker: {ticker}\n"
                f"Official: {ticker_entry.get('company')}\n"
                f"Requested: {company_name}\n"
                f"Similarity: {similarity_pct:.1f}% (< 90%)"
            )
        
        print(f"✅ Ticker validation passed: {ticker} ({similarity_pct:.1f}% match)")
        
        return {
            "ticker": ticker,
            "official_name": ticker_entry.get('company'),
            "research_name": company_name,
            "similarity_pct": similarity_pct,
            "isa_eligible": ticker_entry.get('isa', False),
            "sector": ticker_entry.get('sector', 'Unknown')
        }

    
    def validate_sector_metrics(self, sector: str, metrics_used: List[str]) -> Dict[str, Any]:
        """
        v1.9.4 SECTOR QUANT LOCK
        
        Enforces sector-specific valuation metrics:
        - REITs: MUST use Price/AFFO (Adjusted Funds From Operations), CANNOT use P/E
        - Pharma: MUST include TAM/LoS (Total Addressable Market / Length of Stay)
        
        Hard abort if invalid metrics detected.
        """
        
        # Define sector-specific requirements
        SECTOR_RULES = {
            'Real Estate': {
                'required': ['Price/AFFO', 'FFO'],
                'forbidden': ['P/E', 'EPS'],
                'rationale': 'REITs distribute 90% of income; earnings metrics are irrelevant'
            },
            'REIT': {
                'required': ['Price/AFFO', 'FFO'],
                'forbidden': ['P/E', 'EPS'],
                'rationale': 'REITs distribute 90% of income; earnings metrics are irrelevant'
            },
            'Pharmaceuticals': {
                'required': ['TAM', 'Pipeline'],
                'recommended': ['LoS', 'R&D %'],
                'rationale': 'Pharma valuation depends on addressable market and drug pipeline'
            },
            'Biotech': {
                'required': ['TAM', 'Pipeline'],
                'recommended': ['LoS', 'R&D %'],
                'rationale': 'Biotech valuation depends on addressable market and drug pipeline'
            }
        }
        
        # Check if sector has specific rules
        if sector not in SECTOR_RULES:
            print(f"✅ Sector '{sector}' has no specialized metric requirements")
            return {"validation_passed": True, "sector": sector}
        
        rules = SECTOR_RULES[sector]
        
        # Check for forbidden metrics (REITs using P/E)
        forbidden_used = []
        if 'forbidden' in rules:
            for forbidden_metric in rules['forbidden']:
                if forbidden_metric in metrics_used:
                    forbidden_used.append(forbidden_metric)
        
        if forbidden_used:
            print(f"\n{'='*70}")
            print(f"🚨 SECTOR QUANT LOCK VIOLATION")
            print(f"{'='*70}")
            print(f"⛔ Invalid metrics for sector: {sector}")
            print(f"   Forbidden metrics used: {', '.join(forbidden_used)}")
            print(f"   Rationale: {rules['rationale']}")
            print(f"\n📋 Required metrics for {sector}:")
            for req in rules.get('required', []):
                print(f"   • {req}")
            print(f"{'='*70}\n")
            raise RuntimeError(
                f"SECTOR_QUANT_VIOLATION: Invalid metrics for {sector}\n"
                f"Forbidden: {', '.join(forbidden_used)}\n"
                f"Required: {', '.join(rules.get('required', []))}"
            )
        
        # Check for required metrics
        missing_required = []
        for required_metric in rules.get('required', []):
            if required_metric not in metrics_used:
                missing_required.append(required_metric)
        
        if missing_required:
            print(f"\n{'='*70}")
            print(f"⚠️  SECTOR QUANT WARNING")
            print(f"{'='*70}")
            print(f"⚡ Missing required metrics for sector: {sector}")
            print(f"   Missing: {', '.join(missing_required)}")
            print(f"   Rationale: {rules['rationale']}")
            print(f"{'='*70}\n")
            # Return warning but don't abort - allow research to continue
            return {
                "validation_passed": False,
                "sector": sector,
                "missing_metrics": missing_required,
                "warning": f"Analysis incomplete - missing {', '.join(missing_required)}"
            }
        
        print(f"✅ Sector quant validation passed for {sector}")
        return {"validation_passed": True, "sector": sector}


    
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
        
        response = self._query_ai(prompt)
        return self._parse_json_response(response)
    
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
        
        response = self._query_ai(prompt)
        return self._parse_json_response(response)
    
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
        
        response = self._query_ai(prompt)
        return self._parse_json_response(response)
    
    def execute_short_seller_debate(self, ticker: str, initial_thesis: str) -> Dict[str, Any]:
        """
        v1.9.4 SHORT-SELLER DEBATE FRAMEWORK (Anti-Flattery Lock)
        
        MANDATORY: Challenge the bull thesis with adversarial arguments.
        AI models have a tendency toward flattery and confirmation bias.
        This method FORCES the AI to assume a cynical, forensic persona.
        
        The AI must argue AGAINST the investment before final approval.
        """
        print(f"\n🔴 Initiating Short-Seller Debate for {ticker}...")
        
        # PHASE 1: Short-Seller Attack
        short_seller_prompt = f"""
You are a PROFESSIONAL SHORT-SELLER analyzing {ticker}.

Your job is to DESTROY the following bull thesis:

{initial_thesis}

Provide 5 critical counterarguments focusing on:
1. Financial statement red flags (revenue quality, accounting tricks, goodwill impairments)
2. Competitive threats (new entrants, disruption, commoditization risk)
3. Management credibility issues (insider selling, compensation structure, capital allocation)
4. Market saturation / TAM exhaustion (growth ceiling, diminishing returns)
5. Regulatory / macro headwinds (policy risk, interest rate sensitivity, geopolitical exposure)

Be CYNICAL. Be FORENSIC. Find the flaws.

Format as JSON:
{{
  "bear_arguments": [
    {{"category": "Financial Red Flags", "argument": "...", "severity": "high|medium|low"}},
    {{"category": "Competitive Threats", "argument": "...", "severity": "high|medium|low"}},
    {{"category": "Management Risk", "argument": "...", "severity": "high|medium|low"}},
    {{"category": "Market Saturation", "argument": "...", "severity": "high|medium|low"}},
    {{"category": "Regulatory Risk", "argument": "...", "severity": "high|medium|low"}}
  ],
  "short_thesis_summary": "..."
}}
"""
        
        try:
            bear_response = self._query_ai(short_seller_prompt)
            bear_case = self._parse_json_response(bear_response)
        except Exception as e:
            print(f"⚠️  Short-seller analysis failed: {e}")
            bear_case = {"bear_arguments": [], "short_thesis_summary": "Analysis failed"}
        
        # PHASE 2: Bull Rebuttal (with data requirement)
        rebuttal_prompt = f"""
Original Bull Thesis:
{initial_thesis}

Short-Seller Counterarguments:
{json.dumps(bear_case, indent=2)}

Now DEFEND the bull thesis. Address each counterargument with DATA.

Rules:
- If you cannot refute a "high severity" bear argument with quantitative data, you MUST downgrade the recommendation.
- Generic statements like "strong brand" or "proven management" are NOT sufficient.
- Provide specific metrics, historical performance, or structural advantages.

If ≥3 of the 5 bear arguments cannot be addressed with data, recommendation must be downgraded:
- "STRONG BUY" → "HOLD"
- "BUY" → "AVOID"

Format as JSON:
{{
  "rebuttals": [
    {{"bear_argument": "...", "rebuttal": "...", "data_provided": true/false}},
    ...
  ],
  "arguments_refuted": <number 0-5>,
  "final_recommendation": "STRONG BUY|BUY|HOLD|AVOID",
  "recommendation_rationale": "..."
}}
"""
        
        try:
            rebuttal_response = self._query_ai(rebuttal_prompt)
            final_thesis = self._parse_json_response(rebuttal_response)
        except Exception as e:
            print(f"⚠️  Bull rebuttal failed: {e}")
            final_thesis = {
                "arguments_refuted": 0,
                "final_recommendation": "HOLD",
                "recommendation_rationale": "Debate process failed - default to HOLD"
            }
        
        # Validate debate outcome
        debate_passed = final_thesis.get("arguments_refuted", 0) >= 3
        
        print(f"✅ Short-Seller Debate complete:")
        print(f"   Arguments refuted: {final_thesis.get('arguments_refuted', 0)}/5")
        print(f"   Final recommendation: {final_thesis.get('final_recommendation', 'HOLD')}")
        
        return {
            "initial_thesis": initial_thesis,
            "bear_case": bear_case,
            "final_thesis": final_thesis,
            "debate_passed": debate_passed
        }

    
    
    def generate_moat_dossier(self, ticker: str, company_name: str = "") -> str:
        """
        v1.9.4: Generate comprehensive moat analysis with Step-Lock and Short-Seller Debate
        
        CRITICAL ENFORCEMENT:
        1. Ticker Guard: 90% fuzzy match between request and instruments.json
        2. Step-Lock: Research plan MUST be written to persistent volume before proceeding
        3. Sector Quant: Enforce sector-specific metrics (Price/AFFO for REITs, TAM/LoS for Pharma)
        4. Short-Seller Debate: AI must challenge its own thesis before final recommendation
        """
        # ========================================================================
        # TICKER HALLUCINATION GUARD (v1.9.4)
        # ========================================================================
        # If company_name is provided, validate against official database
        validation_data = {}
        if company_name:
            validation_data = self.validate_ticker_against_database(ticker, company_name)
        
        print(f"\n{'='*60}")
        print(f"🏰 Generating Moat Dossier for {ticker}")
        if company_name:
            print(f"📊 Company: {validation_data.get('official_name', company_name)}")
        print(f"{'='*60}\n")
        
        # ========================================================================
        # STEP-LOCK PROTOCOL (v1.9.4)
        # ========================================================================
        # CRITICAL: Write research plan to persistent volume BEFORE executing research.
        # If the write fails, ABORT the entire dossier generation.
        # This ensures all research is auditable and prevents "ghost" analysis.
        # ========================================================================
        
        research_plan = f"""
# Moat Research Plan: {ticker}
Generated: {__import__('datetime').datetime.utcnow().isoformat()}Z
Official Name: {validation_data.get('official_name', 'Unknown')}
Sector: {validation_data.get('sector', 'Unknown')}

## Objectives:
1. Analyze ROIC vs WACC spread (5-year consistency)
2. Assess gross margin stability (std dev < 2%)
3. Evaluate pricing power and competitive position

## Methodology:
- Gemini Pro deep research for qualitative analysis
- Quantitative validation of financial metrics
- Short-Seller Debate to challenge bull thesis

## Output:
- Comprehensive moat dossier with bull/bear cases
- Advisory recommendation (no auto-execution)
"""
        
        # Attempt to write research plan
        os.makedirs('data/research_plans', exist_ok=True)
        plan_path = f'data/research_plans/{ticker}_plan.md'
        
        try:
            with open(plan_path, 'w') as f:
                f.write(research_plan)
            print(f"✅ Step-Lock enforced: Plan logged at {plan_path}")
        except Exception as e:
            # ABORT: Cannot enforce Step-Lock
            print(f"\n{'='*60}")
            print(f"🛑 STEP-LOCK FAILURE")
            print(f"{'='*60}")
            print(f"⛔ Cannot write research plan to persistent volume")
            print(f"   Path: {plan_path}")
            print(f"   Error: {e}")
            print(f"\n📋 ENFORCEMENT: No plan = no dossier (Step-Lock Protocol)")
            print(f"{'='*60}\n")
            raise RuntimeError(
                f"STEP_LOCK_FAILURE: Cannot write research plan\n"
                f"Path: {plan_path}\nError: {e}\n"
                f"ABORTING: No plan = no dossier (Step-Lock Protocol)"
            )
        
        # Verify file was actually written
        if not os.path.exists(plan_path):
            raise RuntimeError(f"STEP_LOCK_VERIFICATION_FAILED: Plan file not found at {plan_path}")
        
        # ========================================================================
        # EXECUTE RESEARCH (only after Step-Lock is enforced)
        # ========================================================================
        
        # Run all three analyses
        roic_analysis = self.analyze_roic_vs_wacc(ticker, {})
        margin_analysis = self.analyze_gross_margin_stability(ticker)
        pricing_analysis = self.analyze_pricing_power(ticker)
        
        # ========================================================================
        # SECTOR QUANT LOCK (v1.9.4)
        # ========================================================================
        # Extracted used metrics from pricing analysis (usually contained in analysis text)
        metrics_text = pricing_analysis.get('analysis', '') + " " + str(pricing_analysis.get('investment_thesis', ''))
        
        # Simple detection of metrics mentioned
        metrics_to_check = ['P/E', 'EPS', 'Price/AFFO', 'FFO', 'TAM', 'Pipeline', 'LoS']
        metrics_found = [m for m in metrics_to_check if m in metrics_text]
        
        # Validate for specific sectors
        sector = validation_data.get('sector', 'Unknown')
        self.validate_sector_metrics(sector, metrics_found)

        
        # Generate initial bull thesis
        initial_thesis = pricing_analysis.get('investment_thesis', 'Analysis pending...')
        
        # ========================================================================
        # SHORT-SELLER DEBATE (v1.9.4 Anti-Flattery Lock)
        # ========================================================================
        
        debate_result = self.execute_short_seller_debate(ticker, initial_thesis)
        final_recommendation = debate_result['final_thesis'].get('final_recommendation', 'HOLD')
        
        # Compile dossier with BOTH bull and bear cases
        dossier = f"""
🏰 **MOAT DOSSIER: {ticker}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Generated: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
*Research Plan: {plan_path}*

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**🐂 BULL THESIS (Initial)**
{initial_thesis}

**⚡ Key Advantages**
{chr(10).join(['• ' + adv for adv in pricing_analysis.get('key_advantages', [])])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**🐻 BEAR CASE (Short-Seller Debate)**

{debate_result['bear_case'].get('short_thesis_summary', 'N/A')}

**Critical Counterarguments:**
{chr(10).join(['• [' + arg.get('severity', '?').upper() + '] ' + arg.get('category', '?') + ': ' + arg.get('argument', '?') 
               for arg in debate_result['bear_case'].get('bear_arguments', [])])}

**🔬 Bull Rebuttal:**
• Arguments Refuted: {debate_result['final_thesis'].get('arguments_refuted', 0)}/5
• Debate Outcome: {'PASSED ✅' if debate_result['debate_passed'] else 'FAILED ❌'}

{debate_result['final_thesis'].get('recommendation_rationale', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**📋 FINAL RECOMMENDATION: {final_recommendation}**

**⚠️ Key Risks**
{chr(10).join(['• ' + risk for risk in pricing_analysis.get('key_risks', [])])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*This is an ADVISORY recommendation*
*No auto-execution. Manual review required.*
*Research plan locked at: {plan_path}*
"""
        
        # ========================================================================
        # JOB A -> JOB C HANDOVER: Export Approved Targets to Sniper
        # ========================================================================
        if final_recommendation in ["STRONG BUY", "BUY"]:
            self.export_approved_target(ticker, final_recommendation)

        return dossier

    def export_approved_target(self, ticker: str, recommendation: str):
        """
        Exports STRONG BUY/BUY recommendations to data/targets.json for Sniper execution.
        """
        print(f"🔗 Handing over {ticker} ({recommendation}) to Sniper Engine...")
        
        targets_path = 'data/targets.json'
        targets = []
        
        # Load existing
        if os.path.exists(targets_path):
            try:
                with open(targets_path, 'r') as f:
                    targets = json.load(f)
            except:
                pass
            
        # Deduplicate
        for t in targets:
            if t['ticker'] == ticker:
                print(f"   ⚠️ Target {ticker} already exists. Skipping export.")
                return

        # Fetch current price for trigger setting
        import yfinance as yf
        try:
            current_price = yf.Ticker(ticker).fast_info['last_price']
        except:
            current_price = 100.0 # Fallback
            
        # Set trigger slightly below current price (99%) to catch dips
        trigger_price = current_price * 0.99
        
        # Default quantity (will be checked by Iron Seed / Auditor anyway)
        quantity = 1 
        
        target_entry = {
            "ticker": ticker,
            "quantity": quantity,
            "trigger_price": trigger_price,
            "stop_loss": current_price * 0.90, # 10% Stop Loss
            "added_by": "MoatAnalyzer (Job A)",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        targets.append(target_entry)
        
        with open(targets_path, 'w') as f:
            json.dump(targets, f, indent=2)
            
        print(f"✅ Target exported: {ticker} @ >${trigger_price:.2f}")

    def send_to_telegram(self, dossier: str, ticker: str):
        """Send moat dossier to Telegram with approval link"""
        # Using client methods now
        if not self.telegram_token:
            print("⚠️  Telegram not configured")
            print(dossier)
            return
        
        # Add approval button (would link to dashboard)
        dashboard_url = "https://your-cloudflare-domain.pages.dev"
        message = dossier + f"\n\n[📊 Review Dashboard]({dashboard_url})"
        
        try:
            # We can use the client's send_telegram method directly or custom request
            # Since client.send_telegram is simple text, we'll keep the custom request here 
            # to support the specific prompt format if needed, OR just plain send.
            # Client's method: requests.post(url, data={"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"})
            
            # Reusing client method:
            self.client.send_telegram(message)
            print(f"✅ Moat Dossier sent to Telegram")
        except Exception as e:
            print(f"❌ Failed to send to Telegram: {e}")
            print(dossier)




# ========================================================================
# SECTOR MAPPING LOGIC (JOB B/C ENHANCEMENT)
# ========================================================================

class SectorMapper:
    """
    Maps portfolio tickers to sectors and calculates weight deltas.
    Caches sector data to reduce API calls.
    """
    def __init__(self):
        self.client = Trading212Client()
        self.cache_path = 'data/sector_map.json'
        self.excluded_path = 'data/excluded_tickers.json'
        from macro_clock import MacroClock
        self.macro_clock = MacroClock()
        self.sector_map = self.load_cache()
        self.excluded = self.load_excluded()
        
    def load_cache(self) -> Dict[str, str]:
        """Load sector map from disk"""
        try:
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
            
    def load_excluded(self) -> List[str]:
        """Load excluded tickers from disk"""
        try:
            with open(self.excluded_path, 'r') as f:
                data = json.load(f)
                return data.get('excluded', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
            
    def save_cache(self):
        """Save sector map to disk"""
        os.makedirs('data', exist_ok=True)
        with open(self.cache_path, 'w') as f:
            json.dump(self.sector_map, f, indent=2)

    def get_ticker_sector(self, ticker: str) -> str:
        """Get sector for a single ticker (with caching)"""
        # specialized normalization for T212 tickers like "VOD.L" -> "VOD.L" or "VOD" for yfinance
        # T212 often sends "AAPL_US_EQ", but get_positions usually returns "AAPL"
        
        # Check cache first
        if ticker in self.sector_map:
            return self.sector_map[ticker]
            
        # Fetch from yfinance
        try:
            import yfinance as yf
            # Handle UK tickers for yfinance (e.g. RR.L) if needed
            # Assuming ticker format from T212 is compatible or simple enough
            t = yf.Ticker(ticker)
            sector = t.info.get('sector', 'Unknown')
            # Normalize common sector names if needed (e.g. "Financial Services" -> "Financials")
            # Map yfinance sectors to MacroClock sectors
            sector = self.normalize_sector_name(sector)
            
            self.sector_map[ticker] = sector
            return sector
        except Exception as e:
            print(f"⚠️ Failed to map sector for {ticker}: {e}")
            return "Unknown"

    def normalize_sector_name(self, yf_sector: str) -> str:
        """Map yfinance sector names to MacroClock standard"""
        mapping = {
            "Technology": "Technology",
            "Financial Services": "Financials",
            "Financials": "Financials",
            "Consumer Cyclical": "Consumer Discretionary",
            "Consumer Defensive": "Consumer Staples",
            "Energy": "Energy",
            "Healthcare": "Healthcare",
            "Industrials": "Industrials",
            "Basic Materials": "Materials",
            "Utilities": "Utilities",
            "Real Estate": "Real Estate", # MacroClock might not have RE explicit, usually falls into Financials or separate
            "Communication Services": "Technology" # Optional mapping, or add to MacroClock
        }
        return mapping.get(yf_sector, yf_sector)

    def calculate_portfolio_deltas(self) -> Dict[str, Any]:
        """
        Harvest tickers, map sectors, calculate value-weighted deltas.
        Filters:
        1. Value < £250 (Lab trades)
        2. Ticker in data/excluded_tickers.json
        """
        print("📊 Harvesting portfolio for sector analysis...")
        positions = self.client.get_positions()
        
        if not positions:
            print("⚠️ No open positions found.")
            return {}
            
        # Get Live Cash
        acct = self.client.get_account_info()
        cash = float(acct.get('cash', {}).get('availableToTrade', 0.0))
        
        sector_values = {}
        filtered_equity = 0.0
        ignored_count = 0
        
        # 1. Harvest & Map
        new_mappings = False
        for pos in positions:
            ticker = pos.get('ticker')
            
            # Explicit Exclusion
            if ticker in self.excluded:
                ignored_count += 1
                continue
            
            # Get Value
            qty = float(pos.get('quantity', 0))
            price = float(pos.get('currentPrice', 0))
            
            # Normalize Price (Pence to Pounds for UK)
            if "_UK_EQ" in ticker or ticker.endswith(".L"):
                price = price / 100.0
            
            position_value = qty * price
            
            # Value Filter (Lab Trades)
            if position_value < 250.0:
                ignored_count += 1
                continue
            
            filtered_equity += position_value
            
            # Get Sector
            sector = self.get_ticker_sector(ticker)
            if sector not in self.sector_map: # It was just fetched
                new_mappings = True
            
            sector_values[sector] = sector_values.get(sector, 0.0) + position_value

        if new_mappings:
            self.save_cache()
            
        print(f"📉 Filtered {ignored_count} positions (Lab/Excluded).")
        
        # Use Filtered Equity + Cash for Total Analysis Value
        # This means Lab trades are effectively invisible to the sector clock
        total_portfolio_value = filtered_equity + cash
        
        # Add Cash to sector values
        sector_values['Cash'] = cash
        
        # 2. Calculate Weights
        current_allocation = {}
        for sec, val in sector_values.items():
            weight = (val / total_portfolio_value) * 100
            current_allocation[sec] = weight
            
        # 3. Get Deltas from MacroClock
        # Detect phase first or use cached?
        # MacroClock internal cache handles it.
        deltas = self.macro_clock.calculate_sector_deltas(current_allocation)
        
        return {
            "total_value": total_portfolio_value,
            "allocation": current_allocation,
            "deltas": deltas,
            "phase": self.macro_clock.detect_market_phase()['phase'] # Just to know phase
        }

    def generate_delta_report(self) -> str:
        """Generate text report for Telegram"""
        data = self.calculate_portfolio_deltas()
        if not data:
            return "⚠️ Sector Analysis Unavailable (No Data)"
            
        deltas = data['deltas']
        phase = data['phase']
        
        report = f"⚖️ **SECTOR DELTAS ({phase})**\n"
        
        # Sort by biggest drift (absolute delta)
        sorted_sectors = sorted(deltas.items(), key=lambda x: abs(x[1]['delta']), reverse=True)
        
        for sector, met in sorted_sectors:
            if abs(met['delta']) < 1.0:
                continue # Skip negligible
            
            icon = "🟢" if met['status'] == 'MATCH' else "🔴" if met['status'] == 'OVER' else "🔵"
            status_text = f"{met['delta']:+.1f}% {met['status']}"
            report += f"{icon} **{sector}**: {met['current']:.1f}% ({status_text})\n"
            
        return report

def generate_open_market_brief() -> str:
    """
    Generates the "Market Open Analysis" at 14:30 UTC.
    Scans the FULL Master Universe (100+ Tickers) for top movers.
    """
    print("⚡ Analyzing Market Open (Full Universe)...")
    import yfinance as yf
    import pandas as pd
    
    # 1. Load Universe
    try:
        with open('data/master_universe.json', 'r') as f:
            data = json.load(f)
            tickers = [i['ticker'] for i in data.get('instruments', [])]
    except:
        tickers = ['SPY', 'QQQ', 'NVDA', 'TSLA', 'AMD'] # Fallback
        
    # Ensure Indices are included
    if 'SPY' not in tickers: tickers.append('SPY')
    if 'QQQ' not in tickers: tickers.append('QQQ')

    # 2. Batch Fetch Data (Fast) & Targeted 15m Candle
    # v2.3: We now fetch intraday data to isolate the 14:30-14:45 UTC candle
    # regardless of when this script is run (even hours later)
    try:
        # Fetch 5 days of 15m data to capture "today's open" reliably
        df = yf.download(tickers, period="5d", interval="15m", group_by='ticker', progress=False)
    except Exception as e:
        return f"⚠️ Market Data Fetch Failed: {e}"

    results = []
    
    # Target Open Time: Today at 14:30 UTC
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    # Use pandas compatible string for indexing/search if needed, 
    # but yfinance returns UTC index. 
    
    # 3. Process Each Ticker
    for t in tickers:
        try:
            # Handle MultiIndex dataframe from yfinance
            if len(tickers) > 1:
                t_data = df[t]
            else:
                t_data = df
            
            if t_data.empty: continue
            
            # Find the 14:30-14:45 candle for "Today"
            # Resample or just find the row
            # Index is DatetimeIndex localized to UTC usually
            
            # Filter for today
            today_data = t_data.loc[today_str] 
            
            if today_data.empty: continue
            
            # Find specific 14:30 candle
            # Approx check - take the first candle of the day if it's near 14:30 UTC
            # US Market Open is 14:30 UTC (Standard) or 13:30 (DST). 
            # Best proxy: The very first candle of the session.
            
            first_candle = today_data.iloc[0]
            open_price = float(first_candle['Open'])
            close_price = float(first_candle['Close'])
            
            # Calculate the move in that first 15m
            change = ((close_price - open_price) / open_price) * 100
            
            results.append({
                'ticker': t,
                'price': close_price, # Price at end of 15m
                'change': change
            })
        except:
            continue
            
    # 4. Sort by Movers
    # remove indices from movers list
    movers = [x for x in results if x['ticker'] not in ['SPY', 'QQQ']]
    movers.sort(key=lambda x: x['change'], reverse=True)
    
    top_gainers = movers[:3]
    top_losers = movers[-3:]
    
    # 5. Construct Report
    timestamp = datetime.utcnow().strftime('%H:%M UTC')
    msg = f"🔔 **MARKET OPEN ANALYSIS (15m Recap)**\n"
    msg += f"📅 Data: {today_str} (First 15m Interval)\n"
    msg += f"📡 Scanned {len(results)} Tickers\n\n"
    
    # Indices
    spy = next((x for x in results if x['ticker'] == 'SPY'), {'price':0, 'change':0})
    qqq = next((x for x in results if x['ticker'] == 'QQQ'), {'price':0, 'change':0})
    
    msg += f"**S&P 500:** ${spy['price']:.2f} (15m: {spy['change']:+.2f}%)\n"
    msg += f"**Nasdaq:** ${qqq['price']:.2f} (15m: {qqq['change']:+.2f}%)\n\n"
    
    msg += "**🚀 15m Gainers:**\n"
    for m in top_gainers:
        msg += f"- {m['ticker']}: ${m['price']:.2f} ({m['change']:+.2f}%)\n"
        
    msg += "\n**🔻 15m Losers:**\n"
    for m in sorted(top_losers, key=lambda x: x['change']):
        msg += f"- {m['ticker']}: ${m['price']:.2f} ({m['change']:+.2f}%)\n"
        
    return msg

# ========================================================================
# MORNING BRIEF LOGIC (JOB B - 09:00 UTC)
# ========================================================================

class MorningBrief:
    """The Strategist: Generates data/targets.json for the Sniper Engine."""
    
    def __init__(self):
        from telegram_bot import SovereignAlerts
        self.alerts = SovereignAlerts()
        self.client = Trading212Client()
        self.master_universe_path = 'data/master_universe.json'
        self.targets_path = 'data/targets.json'
        self.mapper = SectorMapper() # Initialize Mapper
        
    def load_watchlist(self) -> List[str]:
        """Load vetted Tier 1 tickers from master_universe.json"""
        try:
            with open(self.master_universe_path, 'r') as f:
                data = json.load(f)
                return [inst['ticker'] for inst in data.get('instruments', [])]
        except Exception as e:
            print(f"⚠️ Failed to load master_universe.json: {e}")
            return ['NVDA', 'TSLA', 'AMD'] # Fallback

    def generate_brief(self):
        """Calculates levels for ALL tickers and saves to JSON"""
        # WEEKEND GUARD
        now = datetime.utcnow()
        if now.weekday() >= 5:
            print("📅 WEEKEND: Skipping Morning Brief.")
            return

        watchlist = self.load_watchlist()
        print(f"📊 Scanning {len(watchlist)} tickers for Morning Brief...")
        
        all_targets = []
        high_prob_setups = []
        
        for ticker in watchlist:
            try:
                import yfinance as yf
                t_obj = yf.Ticker(ticker)
                
                # Fetch recent history to determine ATR-based levels
                hist = t_obj.history(period='5d', interval='1d')
                if hist.empty:
                    continue
                    
                prev_close = float(t_obj.fast_info['previous_close'])
                
                # Dynamic Logic:
                # Trigger = Previous Close + 0.5% (Early breakout)
                # Stop = Previous Close - 1.5% (Protection)
                trigger = prev_close * 1.005
                stop = prev_close * 0.985
                qty = 5  # Default
                
                target_entry = {
                    "ticker": ticker,
                    "trigger_price": round(trigger, 2),
                    "stop_loss": round(stop, 2),
                    "quantity": qty,
                    "prev_close": round(prev_close, 2)
                }
                
                all_targets.append(target_entry)
                
                # Filter for Telegram (Probability Heuristic):
                if ticker in ['NVDA', 'TSLA', 'MSTR'] or (len(high_prob_setups) < 12):
                    high_prob_setups.append(ticker)
                
            except Exception as e:
                # Silently skip errors for bulk scan
                continue
        
        # Save FULL targets array
        os.makedirs('data', exist_ok=True)
        with open(self.targets_path, 'w') as f:
            json.dump(all_targets, f, indent=2)
            
        # Unified Telegram Brief
        timestamp = datetime.utcnow().strftime('%d/%m %H:%M UTC')
        msg = f"📊 **MORNING BRIEF: {len(watchlist)} SCANNED**\n"
        msg += f"📅 *{timestamp}*\n"
        msg += f"Found {len(all_targets)} valid targets. Top {len(high_prob_setups)} high-prob setups identified:\n\n"
        
        # SECTOR DELTAS (Main Holdings Only)
        try:
            sector_report = self.mapper.generate_delta_report()
            msg += f"{sector_report}\n" # Header is already in generate_delta_report
        except Exception as e:
            print(f"⚠️ Sector logic error: {e}")
            msg += "⚠️ Sector Analysis Failed\n\n"
            
        msg += "🔥 **TOP PICK TRIGGERS**\n"
        for t in all_targets:
            if t['ticker'] in high_prob_setups:
                msg += f"- {t['ticker']} > ${t['trigger_price']} (Stop: ${t['stop_loss']})\n"
                
        msg += "\nSniper engine synced. Monitoring active."

        self.alerts.send_message(msg)
        print(f"✅ Full Scan Complete. Brief sent via SovereignAlerts.")

def main():
    """Unified entry point for Moat Analysis and Morning Brief"""
    import argparse
    parser = argparse.ArgumentParser(description='Strategic Moat & Morning Brief')
    parser.add_argument('ticker', nargs='?', help='Ticker for Moat Analysis')
    parser.add_argument('--brief', action='store_true', help='Generate Morning Brief')
    
    args = parser.parse_args()
    
    try:
        if args.brief:
            brief = MorningBrief()
            brief.generate_brief()
        elif args.ticker:
            analyzer = MoatAnalyzer()
            dossier = analyzer.generate_moat_dossier(args.ticker)
            analyzer.send_to_telegram(dossier, args.ticker)
        else:
            parser.print_help()
    except Exception as e:
        print(f"❌ Execution Error: {e}")
        try:
            from telegram_bot import SovereignAlerts
            SovereignAlerts().send_message(f"⚠️ **CRITICAL FAILURE**\nJob: `strategic_moat.py`\nError: `{str(e)}`")
        except:
            pass

if __name__ == "__main__":
    main()

