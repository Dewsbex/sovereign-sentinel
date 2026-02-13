/**
 * Sovereign Sentinel Frontend Configuration
 * Environment-aware API endpoint configuration
 */

const CONFIG = {
    // API Base URL - automatically detects environment
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'  // Local development
        : 'https://felt-herbs-extremely-third.trycloudflare.com',  // Quick Tunnel (Live Backend)
    
    // Polling intervals
    DASHBOARD_REFRESH_INTERVAL: 30000,  // 30 seconds
    
    // UI Settings
    MAX_SEARCH_RESULTS: 50,
    TOAST_DURATION: 3000,  // 3 seconds
    
    // Feature flags
    ENABLE_LIVE_UPDATES: true,
    DEBUG_MODE: window.location.hostname === 'localhost'
};

// Export for use in app.js
window.SOVEREIGN_CONFIG = CONFIG;

// Log configuration in debug mode
if (CONFIG.DEBUG_MODE) {
    console.log('🛡️ Sovereign Sentinel Config:', CONFIG);
}
