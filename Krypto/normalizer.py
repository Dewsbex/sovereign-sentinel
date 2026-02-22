import logging
import math

class DataNormalizer:
    """
    Sanitizes and normalizes market data to prevent the 'Pence Bug' and ensure 
    consistent floating-point precision across the application.
    """
    def __init__(self):
        self.logger = logging.getLogger('system_logger')

    def normalize_price(self, price, symbol, source="kraken"):
        """
        Normalizes price data to standard GBP.
        
        Args:
            price (float/str): The raw price from the API.
            symbol (str): The ticker symbol (e.g., 'XXBTZGBP').
            source (str): The data source identifier.
        
        Returns:
            float: Normalized price in GBP.
        """
        try:
            clean_price = float(price)

            # --- THE PENCE BUG GUARD ---
            # Heuristic: If valid BTC price > £1,000,000, it's likely in Pence (GBX).
            # Current BTC ~ £80,000. 
            # If we see 8,000,000, it's GBX.
            if "GBP" in symbol or source == "yahoo":
                if clean_price > 5000000 and "BTC" in symbol: 
                     # This is a safety heuristic.
                     # In a real rigorous system, we'd use metadata flags.
                     # But for this specific bug, this is the patch.
                     self.logger.warning(f"Normalization Triggered: Converted {clean_price} (Likely GBX) to {clean_price / 100} GBP for {symbol}")
                     clean_price = clean_price / 100.0
            
            return clean_price

        except (ValueError, TypeError) as e:
            self.logger.error(f"Normalization Error for {symbol}: {e}")
            return 0.0

    def normalize_volume(self, volume):
        """Standardizes volume to float."""
        try:
            return float(volume)
        except (ValueError, TypeError):
            return 0.0

if __name__ == "__main__":
    # Test
    dn = DataNormalizer()
    print(f"Test GBX Check: 8000000 -> {dn.normalize_price(8000000, 'XXBTZGBP', 'yahoo')}")
    print(f"Test Normal Check: 80000 -> {dn.normalize_price(80000, 'XXBTZGBP', 'kraken')}")
