const API_BASE_URL = 'http://localhost:8000/api';
let mainChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupNavigation();
    await loadPortfolioSummary();
    
    const assetSelector = document.getElementById('asset-selector');
    assetSelector.addEventListener('change', (e) => {
        loadAssetDetails(e.target.value);
    });
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-links li');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            const view = item.dataset.view;
            document.querySelectorAll('.content-view').forEach(v => v.style.display = 'none');
            const target = document.getElementById(`view-${view}`);
            if (target) target.style.display = 'block';
        });
    });
}

// --- Chat ---

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, 'user');
    input.value = '';
    sendBtn.disabled = true;

    const typingId = showTyping();

    try {
        const res = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await res.json();
        hideTyping(typingId);
        appendMessage(data.response, 'agent');
    } catch {
        hideTyping(typingId);
        appendMessage('Error connecting to the AI agent. Please try again.', 'agent');
    } finally {
        sendBtn.disabled = false;
        input.focus();
    }
}

function appendMessage(text, role) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.innerHTML = `<div class="message-bubble">${text}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function showTyping() {
    const container = document.getElementById('chat-messages');
    const id = `typing-${Date.now()}`;
    const div = document.createElement('div');
    div.className = 'chat-message agent';
    div.id = id;
    div.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function hideTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.activeElement.id === 'chat-input') {
        sendChatMessage();
    }
});

async function loadPortfolioSummary() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/summary`);
        const data = await response.json();
        
        renderKPIs(data.metrics);
        renderAssetsTable(data.assets);
        
        // Populate selector
        const assetSelector = document.getElementById('asset-selector');
        assetSelector.innerHTML = '';
        data.assets.forEach(assetInfo => {
            const option = document.createElement('option');
            option.value = assetInfo.asset;
            option.textContent = assetInfo.asset;
            assetSelector.appendChild(option);
        });
        
        // Load first asset
        if (data.assets.length > 0) {
            loadAssetDetails(data.assets[0].asset);
        }
        
    } catch (error) {
        console.error("Failed to load portfolio summary:", error);
    }
}

function renderKPIs(metrics) {
    const container = document.getElementById('kpi-container');
    container.innerHTML = `
        <div class="glass-card kpi-card">
            <div class="kpi-label">Total Assets Monitored</div>
            <div class="kpi-value">${metrics.total_assets}</div>
            <div style="color: var(--text-secondary); font-size: 0.8rem;">Active Data Feeds</div>
        </div>
        <div class="glass-card kpi-card">
            <div class="kpi-label">Active Buy Signals</div>
            <div class="kpi-value" style="color: var(--signal-buy)">${metrics.signals_distribution.BUY}</div>
            <div style="color: var(--text-secondary); font-size: 0.8rem;">AI Confidence > 60%</div>
        </div>
        <div class="glass-card kpi-card">
            <div class="kpi-label">Active Sell Signals</div>
            <div class="kpi-value" style="color: var(--signal-sell)">${metrics.signals_distribution.SELL}</div>
            <div style="color: var(--text-secondary); font-size: 0.8rem;">Risk Mitigation Suggested</div>
        </div>
    `;
}

function renderAssetsTable(assets) {
    const tbody = document.getElementById('assets-table-body');
    tbody.innerHTML = '';
    
    assets.forEach(asset => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${asset.asset}</strong></td>
            <td>$${asset.current_price.toFixed(2)}</td>
            <td><span class="signal-badge ${asset.signal}">${asset.signal}</span></td>
            <td>${(asset.confidence * 100).toFixed(0)}%</td>
            <td><button class="action-btn" onclick="loadAssetDetails('${asset.asset}')">Analyze</button></td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadAssetDetails(assetName) {
    document.getElementById('asset-selector').value = assetName;
    document.getElementById('ai-insight-content').innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        // Fetch chart data
        const chartRes = await fetch(`${API_BASE_URL}/assets/${assetName}/data?days=180`);
        const chartData = await chartRes.json();
        renderChart(chartData);
        
        // Fetch AI insights
        const insightRes = await fetch(`${API_BASE_URL}/assets/${assetName}/insights`);
        const insightData = await insightRes.json();
        renderAIInsights(insightData.insights);
        
    } catch (error) {
        console.error(`Failed to load details for ${assetName}:`, error);
        document.getElementById('ai-insight-content').innerHTML = '<p style="color:var(--signal-sell)">Error loading insights. Please try again.</p>';
    }
}

function renderChart(data) {
    const ctx = document.getElementById('mainChart').getContext('2d');
    
    if (mainChartInstance) {
        mainChartInstance.destroy();
    }
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(0, 242, 254, 0.5)');
    gradient.addColorStop(1, 'rgba(0, 242, 254, 0.0)');

    mainChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates.map(d => {
                const date = new Date(d);
                return `${date.getMonth()+1}/${date.getDate()}`;
            }),
            datasets: [{
                label: `${data.asset} Price`,
                data: data.closes,
                borderColor: '#00f2fe',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(20, 25, 40, 0.9)',
                    titleColor: '#f0f4f8',
                    bodyColor: '#f0f4f8',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', maxTicksLimit: 10 }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8' }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function renderAIInsights(insights) {
    const container = document.getElementById('ai-insight-content');
    
    let signalClass = '';
    if (insights.signal === 'BUY') signalClass = 'signal-buy';
    else if (insights.signal === 'SELL') signalClass = 'signal-sell';
    else signalClass = 'signal-hold';
    
    container.innerHTML = `
        <div class="insight-signal ${signalClass}">
            ${insights.signal}
        </div>
        <div class="insight-metric">
            <span style="color: var(--text-secondary)">Confidence Score</span>
            <span style="font-weight: 700; color: var(--text-primary)">${(insights.confidence * 100).toFixed(0)}%</span>
        </div>
        <div class="insight-metric">
            <span style="color: var(--text-secondary)">Current Price</span>
            <span style="font-weight: 700; color: var(--text-primary)">$${insights.current_price.toFixed(2)}</span>
        </div>
        <div class="insight-metric">
            <span style="color: var(--text-secondary)">SMA (20-day)</span>
            <span style="font-weight: 600; color: var(--text-primary)">${insights.sma_20 ? '$' + insights.sma_20.toFixed(2) : 'N/A'}</span>
        </div>
        <div class="insight-metric">
            <span style="color: var(--text-secondary)">SMA (50-day)</span>
            <span style="font-weight: 600; color: var(--text-primary)">${insights.sma_50 ? '$' + insights.sma_50.toFixed(2) : 'N/A'}</span>
        </div>
        <div class="insight-reason">
            <strong><i data-lucide="info" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:4px;"></i> Reasoning:</strong><br>
            ${insights.reason}
        </div>
    `;
    lucide.createIcons();
}
