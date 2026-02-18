from decimal import Decimal, ROUND_DOWN
import logging

logger = logging.getLogger("Normalization")

class Normalizer:
    """
    Handles asset precision and currency normalization.
    Fixes 'The Pence Bug' by using Decimal for all currency calculations.
    """
    
    # Static precision map (In prod, fetch from Kraken AssetPairs endpoint)
    PRECISION_MAP = {
        "BTC/USD": {"price": 1, "amount": 8},
        "ETH/USD": {"price": 2, "amount": 8},
        "BTC/GBP": {"price": 1, "amount": 8}, # GBP often has different rules
        "DOGE/USD": {"price": 5, "amount": 0},
    }

    @staticmethod
    def normalize_amount(symbol: str, amount: float) -> float:
        """
        Normalize order volume to the asset's specific decimals.
        Using Decimal to avoid floating point artifacts.
        """
        precision = Normalizer.PRECISION_MAP.get(symbol, {}).get("amount", 8)
        d_amount = Decimal(str(amount))
        quantizer = Decimal("1." + "0" * precision)
        normalized = d_amount.quantize(quantizer, rounding=ROUND_DOWN)
        return float(normalized)

    @staticmethod
    def normalize_price(symbol: str, price: float) -> float:
        """
        Normalize price to the pair's specific tick size.
        """
        precision = Normalizer.PRECISION_MAP.get(symbol, {}).get("price", 2)
        d_price = Decimal(str(price))
        quantizer = Decimal("1." + "0" * precision)
        normalized = d_price.quantize(quantizer, rounding=ROUND_DOWN)
        return float(normalized)

    @staticmethod
    def fix_pence_bug(raw_balance: float, currency: str) -> float:
        """
        Specific fix for GBP balances that might come as floats impacting penny precision.
        """
        if currency == "GBP":
            # Example logic: ensure 2 decimal places strictly
            return float(Decimal(str(raw_balance)).quantize(Decimal("0.01"), rounding=ROUND_DOWN))
        return raw_balance
