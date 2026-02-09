/**
 * Sovereign Sentinel Frontend Application
 * Client-side JavaScript for dashboard data fetching and rendering
 */

// Get configuration
const CONFIG = window.SOVEREIGN_CONFIG;
const API = CONFIG.API_BASE_URL;

// State management
let dashboardData = {
    total_wealth: 0,
    session_pnl: 0,
    cash: 0,
    positions: [],
    market_phase: 'LOADING',
    connectivity_status: 'CONNECTING',
    job_c_candidates: []
};

let charts = {
    heatmap: null,
    curve: null,
    donut: null,
    sectors: null
};

/**
 * Initialize application on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🛡️ Sovereign Sentinel v1.9.4 - Initializing...');
    loadDashboard();
    
    // Set up auto-refresh if enabled
    if (CONFIG.ENABLE_LIVE_UPDATES) {
        setInterval(loadDashboard, CONFIG.DASHBOARD_REFRESH_INTERVAL);
    }
});

/**
 * Fetch dashboard data from backend API
 */
async function loadDashboard() {
    try {
        const response = await fetch(`${API}/api/dashboard`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        dashboardData = data;
        
        renderDashboard();
    } catch (error) {
        console.error('❌ Dashboard load failed:', error);
        dashboardData.connectivity_status = 'OFFLINE';
        dashboardData.market_phase = 'ERROR';
        renderDashboard();
    }
}

/**
 * Render all dashboard components
 */
function renderDashboard() {
    updateHeader();
    renderHeatmap();
    renderGrowthCurve();
    renderAssetDonut();
    renderSectorBars();
    renderOrbTable();
}

/**
 * Update header metrics
 */
function updateHeader() {
    document.getElementById('total-wealth').textContent = `£${dashboardData.total_wealth.toLocaleString('en-GB', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    const sessionPnlEl = document.getElementById('session-pnl');
    sessionPnlEl.textContent = `£${dashboardData.session_pnl >= 0 ? '+' : ''}${dashboardData.session_pnl.toLocaleString('en-GB', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    sessionPnlEl.className = `metric-value ${dashboardData.session_pnl >= 0 ? 'positive' : 'negative'}`;
    
    document.getElementById('market-phase').textContent = dashboardData.market_phase;
    document.getElementById('t212-status').textContent = dashboardData.connectivity_status;
}

/**
 * Render performance heatmap (treemap)
 */
function renderHeatmap() {
    const heatmapData = dashboardData.positions.map(p => ({
        x: p.ticker,
        y: Math.abs(p.pnl || 0),
        pnl_raw: p.pnl || 0,
        pnl_pct: p.pnl_percent || 0
    }));
    
    const options = {
        series: [{ data: heatmapData }],
        chart: {
            height: 550,
            type: 'treemap',
            toolbar: { show: false }
        },
        colors: [function({ value, seriesIndex, dataPointIndex, w }) {
            const pnl_pct = w.config.series[seriesIndex].data[dataPointIndex].pnl_pct;
            if (pnl_pct > 3) return '#bbf7d0';
            if (pnl_pct > 0.1) return '#f0fdf4';
            if (pnl_pct > -3) return '#fff1f2';
            return '#fecaca';
        }],
        plotOptions: {
            treemap: {
                distributed: true,
                enableShades: false
            }
        },
        dataLabels: {
            enabled: true,
            style: {
                colors: ['#000'],
                fontSize: '12px',
                fontFamily: 'JetBrains Mono'
            },
            formatter: function(text, op) {
                return [text, op.value.toFixed(2)];
            }
        }
    };
    
    if (charts.heatmap) {
        charts.heatmap.destroy();
    }
    charts.heatmap = new ApexCharts(document.querySelector("#performance-heatmap"), options);
    charts.heatmap.render();
}

/**
 * Render equity growth curve
 */
function renderGrowthCurve() {
    const options = {
        series: [{
            name: 'Equity',
            data: dashboardData.equity_history || [1000, 1020, 1015, 1040, 1050, 1045, 1060]
        }],
        chart: {
            height: 250,
            type: 'area',
            toolbar: { show: false }
        },
        colors: ['#000'],
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.1,
                opacityTo: 0.05,
            }
        },
        dataLabels: { enabled: false },
        stroke: { curve: 'straight', width: 2 },
        xaxis: { labels: { show: false } },
        yaxis: {
            labels: {
                style: { fontFamily: 'JetBrains Mono' },
                formatter: (val) => '£' + val
            }
        }
    };
    
    if (charts.curve) {
        charts.curve.destroy();
    }
    charts.curve = new ApexCharts(document.querySelector("#equity-curve"), options);
    charts.curve.render();
}

/**
 * Render asset allocation donut
 */
function renderAssetDonut() {
    const options = {
        series: dashboardData.asset_allocation?.values || [65, 15, 10, 5, 5],
        chart: { height: 350, type: 'donut' },
        labels: dashboardData.asset_allocation?.labels || ['Tech', 'Energy', 'Finance', 'Health', 'Cash'],
        colors: ['#000', '#333', '#666', '#999', '#ccc'],
        legend: { position: 'bottom', fontFamily: 'JetBrains Mono' },
        dataLabels: { enabled: false }
    };
    
    if (charts.donut) {
        charts.donut.destroy();
    }
    charts.donut = new ApexCharts(document.querySelector("#asset-donut"), options);
    charts.donut.render();
}

/**
 * Render sector exposure bars
 */
function renderSectorBars() {
    const options = {
        series: [{
            name: 'Net Exposure',
            data: dashboardData.sector_exposure?.values || [15, -5, 10, -12, 8]
        }],
        chart: { height: 350, type: 'bar', toolbar: { show: false } },
        plotOptions: {
            bar: {
                colors: {
                    ranges: [
                        { from: -100, to: 0, color: '#fecaca' }, 
                        { from: 1, to: 100, color: '#bbf7d0' }
                    ]
                }
            }
        },
        xaxis: {
            categories: dashboardData.sector_exposure?.labels || ['Tech', 'Energy', 'Finance', 'Health', 'Retail'],
            labels: { style: { fontFamily: 'JetBrains Mono' } }
        },
        yaxis: { labels: { style: { fontFamily: 'JetBrains Mono' } } }
    };
    
    if (charts.sectors) {
        charts.sectors.destroy();
    }
    charts.sectors = new ApexCharts(document.querySelector("#sector-bar-chart"), options);
    charts.sectors.render();
}

/**
 * Render ORB tracker table
 */
function renderOrbTable() {
    const tbody = document.getElementById('orb-table-body');
    tbody.innerHTML = '';
    
    if (dashboardData.job_c_candidates && dashboardData.job_c_candidates.length > 0) {
        dashboardData.job_c_candidates.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.ticker}</td>
                <td>$${item.orb_high.toFixed(2)}</td>
                <td>$${item.target_entry.toFixed(2)}</td>
                <td>$${item.stop_loss.toFixed(2)}</td>
                <td>${item.rvol}x</td>
                <td><span class="status-badge ${item.status.toLowerCase()}">${item.status}</span></td>
                <td><button class="btn" onclick="triggerResearch('${item.ticker}')">RESEARCH</button></td>
            `;
            tbody.appendChild(tr);
        });
    } else {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--slate-gray); padding: 40px;">
                    NO ACTIVE SNIPER SIGNALS DETECTED
                </td>
            </tr>
        `;
    }
}

/**
 * Execute instrument search
 */
async function executeSearch() {
    const query = document.getElementById('instrument-search').value;
    if (!query) return;
    
    showToast("Searching Global Map...");
    
    try {
        const response = await fetch(`${API}/api/instruments?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        const container = document.getElementById('search-results');
        container.innerHTML = `<h4>FOUND ${data.count} MATCHES</h4>`;
        
        if (data.instruments && data.instruments.length > 0) {
            const table = document.createElement('table');
            table.className = 'sniper-table';
            table.style.marginTop = '10px';
            table.innerHTML = '<thead><tr><th>TICKER</th><th>NAME</th><th>ACTION</th></tr></thead>';
            
            const tbody = document.createElement('tbody');
            data.instruments.forEach(inst => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${inst.ticker}</td>
                    <td>${inst.company}</td>
                    <td><button class="btn btn-outline" onclick="triggerResearch('${inst.ticker}', '${inst.company}')">RESEARCH</button></td>
                `;
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            container.appendChild(table);
        }
    } catch (error) {
        console.error('Search failed:', error);
        showToast('SEARCH ERROR');
    }
}

/**
 * Trigger forensic research
 */
async function triggerResearch(ticker, companyName = '') {
    const output = document.getElementById('research-output');
    output.innerHTML = '<div style="position:relative; height:100px;"><div class="spinner"></div><div style="text-align:center; padding-top:60px;">ENGAGING STEP-LOCK PROTOCOL...</div></div>';
    
    showToast("Locking Plan: " + ticker);
    
    try {
        const response = await fetch(`${API}/api/research`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker, company: companyName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            output.innerHTML = data.dossier;
            showToast("Research Complete");
        } else {
            output.innerHTML = `<div style="color:#dc2626;">🛑 RESEARCH ABORTED: ${data.message}</div>`;
            showToast("ABORTED");
        }
    } catch (error) {
        console.error('Research failed:', error);
        output.innerHTML = '<div style="color:#dc2626;">❌ SYSTEM ERROR</div>';
        showToast("ERROR");
    }
}

/**
 * Show toast notification
 */
function showToast(msg) {
    const toast = document.getElementById('feedback-toast');
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, CONFIG.TOAST_DURATION);
}
