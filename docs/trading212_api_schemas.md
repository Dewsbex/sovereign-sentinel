# Trading 212 API - Complete Schema Documentation

**Base URL:** `https://live.trading212.com`  
**Authentication:** API Key + Secret (stored in GitHub Secrets)

---

## 1. POSITIONS

**Endpoint:** `GET /api/v0/equity/positions`  
**Returns:** Array of open position objects

```json
[
  {
    "ticker": "AAPL_US_EQ",
    "quantity": 10.5,
    "averagePrice": 150.25,
    "currentPrice": 175.50,
    "ppl": 265.12,
    "fxPpl": -5.20,
    "initialFillDate": "2023-10-27T14:30:00Z",
    "frontend": "GUI",
    "maxBuy": 5000.0,
    "maxSell": 10.5,
    "pieQuantity": 0.0
  }
]
```

**Key Fields:**
- `ppl`: Profit/Loss in account currency
- `fxPpl`: FX-related P/L
- `maxBuy`/`maxSell`: Trading limits

---

## 2. HISTORICAL EVENTS

### A. Dividends

**Endpoint:** `GET /api/v0/equity/history/dividends`

```json
{
  "items": [
    {
      "ticker": "MSFT_US_EQ",
      "amount": 45.20,
      "amountInEuro": 41.15,
      "grossAmount": 50.00,
      "withholdingTax": 4.80,
      "currency": "USD",
      "paidOn": "2024-01-15T10:00:00Z",
      "quantity": 100.0,
      "reference": "DIV-12345"
    }
  ],
  "nextPagePath": "/api/v0/equity/history/dividends?cursor=..."
}
```

### B. Historical Orders

**Endpoint:** `GET /api/v0/equity/history/orders`

```json
{
  "items": [
    {
      "id": 987654321,
      "date": "2024-02-10T14:30:00Z",
      "ticker": "TSLA_US_EQ",
      "type": "MARKET",
      "side": "BUY",
      "quantity": 5.0,
      "filledQuantity": 5.0,
      "filledValue": 950.00,
      "executionPrice": 190.00,
      "limitPrice": null,
      "stopPrice": null,
      "status": "FILLED",
      "taxes": [
        {
          "name": "Stamp Duty",
          "amount": 4.75,
          "currency": "GBP"
        }
      ]
    }
  ],
  "nextPagePath": "..."
}
```

**Order Types:** `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`  
**Order Status:** `FILLED`, `CANCELLED`, `REJECTED`

### C. Transactions

**Endpoint:** `GET /api/v0/equity/history/transactions`

```json
{
  "items": [
    {
      "transactionId": "txn_888999",
      "date": "2024-03-01T09:00:00Z",
      "amount": 1000.00,
      "currency": "USD",
      "type": "DEPOSIT",
      "reference": "Ref: 12345"
    }
  ],
  "nextPagePath": "..."
}
```

**Transaction Types:** `DEPOSIT`, `WITHDRAWAL`, `INTEREST`, `DIVIDEND`

---

## 3. METADATA

### A. Instruments

**Endpoint:** `GET /api/v0/equity/metadata/instruments`

```json
[
  {
    "ticker": "AAPL_US_EQ",
    "isin": "US0378331005",
    "minTradeQuantity": 0.0001,
    "type": "STOCK",
    "workingScheduleId": 5,
    "currencyCode": "USD"
  }
]
```

**Critical Fields:**
- `minTradeQuantity`: Minimum fractional share (0.0001 = supports fractional)
- `workingScheduleId`: Links to exchange trading hours

### B. Exchanges

**Endpoint:** `GET /api/v0/equity/metadata/exchanges`

```json
[
  {
    "id": 5,
    "name": "NASDAQ",
    "workingSchedules": [
      {
        "id": 5,
        "timeEvents": [
          {
            "date": "2024-02-20T14:30:00Z",
            "type": "OPEN"
          },
          {
            "date": "2024-02-20T21:00:00Z",
            "type": "CLOSE"
          }
        ]
      }
    ]
  }
]
```

**Usage:** Map `workingScheduleId` to determine market hours for ORB calculations.

---

## 4. ORDER EXECUTION (TBD)

**Endpoint:** `POST /api/v0/equity/orders` (assumed)

**Expected Payload:**
```json
{
  "ticker": "TSLA_US_EQ",
  "quantity": 5.0,
  "limitPrice": 246.88,
  "side": "BUY",
  "type": "LIMIT",
  "timeValidity": "DAY"
}
```

**Response:** Order ID + confirmation status

---

## Integration Notes

1. **Ticker Format:** All tickers use `{SYMBOL}_{EXCHANGE}_{ASSET_TYPE}` (e.g., `AAPL_US_EQ`)
2. **Currency Handling:** API returns USD values; GBP conversion needed for UK portfolio
3. **Fractional Shares:** Supported via `minTradeQuantity` field
4. **Rate Limiting:** Unknown; implement exponential backoff
5. **Authentication:** API Key in headers (`Authorization: {API_KEY}`)
