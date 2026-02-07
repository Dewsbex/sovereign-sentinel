# Trading 212 API Integration - Setup Guide

## Prerequisites

1. **API Credentials**: Trading 212 API Key (already added to GitHub Secrets)
2. **Dependencies**: `requests` library (already installed)

## Local Development Setup

1. Create `.env` file with your API key:
```bash
cp .env.example .env
# Edit .env and add your actual API key
```

2. Test API connection:
```bash
python test_trading212.py
```

## Testing the Integration

### 1. Connection Test
```bash
python -c "from trading212_client import test_connection; test_connection()"
```

### 2. Full Test Suite
```bash
python test_trading212.py
```

Expected output:
- ✅ Authentication
- ✅ Position Retrieval
- ✅ Instrument Metadata  
- ✅ Max Buy Calculation

## Next Steps

1. **Phase 3**: Integrate with `generate_ui.py` Flask endpoint
2. **Phase 4**: Wire live data from yfinance for ORB/ATR calculations
3. **Phase 5**: Test order execution with small quantities

## Security Notes

- API key is stored in GitHub Secrets for Cloudflare deployment
- Never commit `.env` file to version control
- All API calls use HTTPS with authentication headers
- Exponential backoff prevents rate limit violations
