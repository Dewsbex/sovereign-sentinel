"""
Flask CORS Configuration for Sovereign Sentinel
Allows Cloudflare Pages frontend to communicate with VPS API
"""

ALLOWED_ORIGINS = [
    'https://sovereign-sentinel.pages.dev',
    'https://api.sovereign-sentinel.pages.dev',
    'http://localhost:8080',  # Local testing
    'http://localhost:5000',  # Local Flask dev
    'http://127.0.0.1:5000',
]

CORS_CONFIG = {
    'origins': ALLOWED_ORIGINS,
    'methods': ['GET', 'POST', 'OPTIONS'],
    'allow_headers': ['Content-Type', 'Authorization'],
    'supports_credentials': False,
    'max_age': 3600
}
