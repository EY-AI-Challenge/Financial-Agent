const API_BASE_URL = 'http://localhost:8000/api';
let mainChartInstance = null;
let userPortfolio = JSON.parse(localStorage.getItem('financial_bros_portfolio')) || {};
let currentPrices = {}; // Store real-time prices

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupNavigation();
    await loadPortfolioSummary();
    
    const assetSelector = document.getElementById('asset-selector');
    if (assetSelector) {
        assetSelector.addEventListener('change', (e) => {
            loadAssetDetails(e.target.value);
        });
    }

    // Setup Portfolio Form
    document.getElementById('add-asset-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const asset = document.getElementById('portfolio-asset-select').value;
        const qty = parseFloat(document.getElementById('portfolio-qty').value);
        if (asset && qty > 0) {
            userPortfolio[asset] = (userPortfolio[asset] || 0) + qty;
            localStorage.setItem('financial_bros_portfolio', JSON.stringify(userPortfolio));
            document.getElementById('portfolio-qty').value = '';
            renderUserPortfolio();
        }
    });

    document.getElementById('btn-portfolio-insight').addEventListener('click', generatePortfolioInsight);
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-links li');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            const viewId = item.dataset.view;
            if (viewId === 'dashboard') {
                document.getElementById('view-dashboard').style.display = 'block';
                document.getElementById('view-portfolio').style.display = 'none';
            } else if (viewId === 'portfolio') {
                document.getElementById('view-dashboard').style.display = 'none';
                document.getElementById('view-portfolio').style.display = 'block';
                renderUserPortfolio();
            } else {
                // Settings / AI Agent placeholders
                alert("This module is locked in the prototype version.");
                document.querySelector('[data-view="dashboard"]').click();
            }
        });
    });
}

async function loadPortfolioSummary() {
    try {
        const response = await fetch(`${API_BASE_URL}/portfolio/summary`);
        const data = await response.json();
        
        renderKPIs(data.metrics);
        renderAssetsTable(data.assets);
        
        // Populate selectors and store prices
        const assetSelector = document.getElementById('asset-selector');
        const portfolioSelect = document.getElementById('portfolio-asset-select');
        
        if (assetSelector) assetSelector.innerHTML = '';
        if (portfolioSelect) portfolioSelect.innerHTML = '';
        
        data.assets.forEach(assetInfo => {
            currentPrices[assetInfo.asset] = assetInfo.current_price;

            const option = document.createElement('option');
            option.value = assetInfo.asset;
            option.textContent = assetInfo.asset;
            if (assetSelector) assetSelector.appendChild(option.cloneNode(true));
            if (portfolioSelect) portfolioSelect.appendChild(option);
        });
        
        // Load first asset
        if (data.assets.length > 0 && assetSelector) {
            loadAssetDetails(data.assets[0].asset);
        }
        
    } catch (error) {
        console.error("Failed to load portfolio summary:", error);
    }
}

function renderUserPortfolio() {
    const tbody = document.getElementById('portfolio-table-body');
    tbody.innerHTML = '';
    
    let totalValue = 0;

    for (const [asset, qty] of Object.entries(userPortfolio)) {
        const price = currentPrices[asset] || 0;
        const value = price * qty;
        totalValue += value;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${asset}</strong></td>
            <td>${qty.toFixed(4)}</td>
            <td>$${price.toFixed(2)}</td>
            <td>$${value.toFixed(2)}</td>
            <td><button class="action-btn" style="border-color: var(--signal-sell); color: var(--signal-sell);" onclick="removeAsset('${asset}')">Remove</button></td>
        `;
        tbody.appendChild(tr);
    }

    if (Object.keys(userPortfolio).length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No assets in portfolio yet.</td></tr>';
    }

    document.getElementById('portfolio-total-value').innerText = `$${totalValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

window.removeAsset = function(asset) {
    delete userPortfolio[asset];
    localStorage.setItem('financial_bros_portfolio', JSON.stringify(userPortfolio));
    renderUserPortfolio();
}

async function generatePortfolioInsight() {
    const btn = document.getElementById('btn-portfolio-insight');
    const originalText = btn.innerText;
    btn.innerText = "Analyzing...";
    btn.disabled = true;

    // Simulate AI insight generation delay or call backend if endpoint existed
    setTimeout(() => {
        let insight = "";
        let total = 0;
        let btcExposure = 0;
        
        for (const [asset, qty] of Object.entries(userPortfolio)) {
            total += (currentPrices[asset] || 0) * qty;
            if (asset === 'BTC-USD' || asset === 'ETH-USD') {
                btcExposure += (currentPrices[asset] || 0) * qty;
            }
        }

        if (total === 0) {
            alert("Your portfolio is empty. Add assets first.");
        } else {
            const cryptoPercentage = (btcExposure / total) * 100;
            if (cryptoPercentage > 50) {
                alert(`⚠️ AI Warning: Your portfolio is highly exposed to crypto (${cryptoPercentage.toFixed(1)}%). Consider diversifying into stable assets like SPY.`);
            } else if (cryptoPercentage === 0) {
                alert(`📈 AI Suggestion: You have 0% exposure to digital assets. Consider adding a small allocation of BTC-USD to improve the Sharpe Ratio.`);
            } else {
                alert(`✅ AI Insight: Your portfolio is well-balanced with a ${cryptoPercentage.toFixed(1)}% crypto allocation. Hold steady and monitor SMA signals.`);
            }
        }

        btn.innerText = originalText;
        btn.disabled = false;
    }, 1500);
}

function renderKPIs(metrics) {
    const container = document.getElementById('kpi-container');
    if(!container) return;
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
    if(!tbody) return;
    tbody.innerHTML = '';
    
    assets.forEach(asset => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${asset.asset}</strong></td>
            <td>$${asset.current_price.toFixed(2)}</td>
            <td><span class="signal-badge ${asset.signal}">${asset.signal}</span></td>
            <td>${(asset.confidence * 100).toFixed(0)}%</td>
            <td><button class="action-btn" onclick="document.querySelector('[data-view=\\'dashboard\\']').click(); loadAssetDetails('${asset.asset}'); window.scrollTo(0,0);">Analyze</button></td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadAssetDetails(assetName) {
    document.getElementById('asset-selector').value = assetName;
    document.getElementById('ai-insight-content').innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const chartRes = await fetch(`${API_BASE_URL}/assets/${assetName}/data?days=180`);
        const chartData = await chartRes.json();
        renderChart(chartData);
        
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
            }
        }
    });
}

function renderAIInsights(insights) {
    const container = document.getElementById('ai-insight-content');
    if(!container) return;
    
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
