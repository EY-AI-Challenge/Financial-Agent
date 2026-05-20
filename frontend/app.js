const API = 'http://localhost:8000/api';
let chartInstance = null;
let allAssets = [];
let currentPrices = {};
let userPortfolio = JSON.parse(localStorage.getItem('fb_portfolio') || '{}');
let currentFilter = 'ALL';

// ── Init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupClock();
    setupNav();
    checkOllamaStatus();
    loadDashboard();
    setupPortfolioForm();
    setupChat();
    setupSearch();
    setInterval(checkOllamaStatus, 30000);
});

function setupClock() {
    const el = document.getElementById('topbar-time');
    const tick = () => {
        const now = new Date();
        el.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    };
    tick();
    setInterval(tick, 1000);
}

// ── Ollama Status ─────────────────────────────────────────────────────────
async function checkOllamaStatus() {
    const badge = document.getElementById('ai-status-badge');
    try {
        const r = await fetch(`${API}/status`);
        const data = await r.json();
        if (data.ollama === 'online') {
            badge.className = 'ai-status online';
            const model = data.models[0] || 'llama3';
            badge.innerHTML = `<div class="status-dot online"></div><span>AI Online · ${model}</span>`;
        } else {
            throw new Error('offline');
        }
    } catch {
        badge.className = 'ai-status';
        badge.innerHTML = `<div class="status-dot offline"></div><span>AI Offline</span>`;
    }
}

// ── Navigation ────────────────────────────────────────────────────────────
function setupNav() {
    const items = document.querySelectorAll('.nav-links li');
    const pageTitles = {
        dashboard: 'Strategic Command Center',
        portfolio: 'My Portfolio',
        news: 'Market Intelligence',
        chat: 'AI Advisor Chat'
    };

    items.forEach(item => {
        item.addEventListener('click', () => {
            items.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            const view = item.dataset.view;
            document.querySelectorAll('.content-view').forEach(v => v.classList.add('hidden'));
            document.getElementById(`view-${view}`).classList.remove('hidden');
            document.getElementById('page-title').textContent = pageTitles[view] || view;

            if (view === 'news') loadNews();
            if (view === 'portfolio') renderPortfolio();
        });
    });
}

// ── Dashboard ─────────────────────────────────────────────────────────────
async function loadDashboard() {
    try {
        const r = await fetch(`${API}/portfolio/summary`);
        const data = await r.json();
        allAssets = data.assets;

        renderKPIs(data.metrics);
        renderTable(data.assets);
        populateSelectors(data.assets);

        if (data.assets.length > 0) {
            loadAssetDetails(data.assets[0].asset);
        }
    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}

function renderKPIs(metrics) {
    const c = document.getElementById('kpi-container');
    const buyPct = metrics.total_assets > 0 ? ((metrics.signals_distribution.BUY / metrics.total_assets) * 100).toFixed(0) : 0;
    c.innerHTML = `
        <div class="glass-card kpi-card">
            <div class="kpi-label">Assets Monitored</div>
            <div class="kpi-value" style="background: linear-gradient(135deg, var(--accent-1), var(--accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${metrics.total_assets}</div>
            <div class="kpi-sub">Live data feeds</div>
        </div>
        <div class="glass-card kpi-card">
            <div class="kpi-label">Buy Signals</div>
            <div class="kpi-value" style="color: var(--buy)">${metrics.signals_distribution.BUY}</div>
            <div class="kpi-sub kpi-trend" style="color:var(--buy)">↑ ${buyPct}% of portfolio</div>
        </div>
        <div class="glass-card kpi-card">
            <div class="kpi-label">Sell Signals</div>
            <div class="kpi-value" style="color: var(--sell)">${metrics.signals_distribution.SELL}</div>
            <div class="kpi-sub">Risk mitigation active</div>
        </div>
        <div class="glass-card kpi-card">
            <div class="kpi-label">Hold Signals</div>
            <div class="kpi-value" style="color: var(--hold)">${metrics.signals_distribution.HOLD}</div>
            <div class="kpi-sub">Awaiting momentum</div>
        </div>
    `;
}

function populateSelectors(assets) {
    const sel = document.getElementById('asset-selector');
    const portSel = document.getElementById('portfolio-asset-select');
    sel.innerHTML = '';
    portSel.innerHTML = '';

    assets.forEach(a => {
        currentPrices[a.asset] = a.current_price;
        const o = document.createElement('option');
        o.value = a.asset;
        o.textContent = a.asset;
        sel.appendChild(o.cloneNode(true));
        portSel.appendChild(o);
    });

    sel.addEventListener('change', e => loadAssetDetails(e.target.value));
}

function renderTable(assets) {
    const tbody = document.getElementById('assets-table-body');
    const filtered = currentFilter === 'ALL' ? assets : assets.filter(a => a.signal === currentFilter);
    tbody.innerHTML = '';
    filtered.forEach(a => {
        const tr = document.createElement('tr');
        const confColor = a.signal === 'BUY' ? 'var(--buy)' : a.signal === 'SELL' ? 'var(--sell)' : 'var(--hold)';
        const confPct = (a.confidence * 100).toFixed(0);
        tr.innerHTML = `
            <td><strong>${a.asset}</strong></td>
            <td>$${a.current_price.toFixed(2)}</td>
            <td><span class="signal-pill pill-${a.signal.toLowerCase()}">${a.signal}</span></td>
            <td>
                <div style="font-size:0.82rem;font-weight:600;color:${confColor}">${confPct}%</div>
                <div class="conf-bar"><div class="conf-fill" style="width:${confPct}%;background:${confColor}"></div></div>
            </td>
            <td><button class="action-btn" onclick="analyzeAsset('${a.asset}')">Analyze</button></td>
        `;
        tbody.appendChild(tr);
    });

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderTable(allAssets);
        });
    });
}

window.analyzeAsset = function(asset) {
    // Switch to dashboard
    document.querySelectorAll('.nav-links li').forEach(i => i.classList.remove('active'));
    document.querySelector('[data-view="dashboard"]').classList.add('active');
    document.querySelectorAll('.content-view').forEach(v => v.classList.add('hidden'));
    document.getElementById('view-dashboard').classList.remove('hidden');
    document.getElementById('asset-selector').value = asset;
    loadAssetDetails(asset);
    window.scrollTo(0, 0);
};

// ── Asset Details ─────────────────────────────────────────────────────────
async function loadAssetDetails(assetName) {
    document.getElementById('asset-selector').value = assetName;
    const ic = document.getElementById('ai-insight-content');
    ic.innerHTML = '<div class="loading-spinner"></div>';

    // Load chart (fast)
    try {
        const r = await fetch(`${API}/assets/${assetName}/data?days=180`);
        const data = await r.json();
        renderChart(data);
    } catch (e) {
        console.error('Chart load error:', e);
    }

    // Load AI insight (may be slow with Ollama)
    try {
        const r = await fetch(`${API}/assets/${assetName}/insights`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        renderInsight(data.insights);
    } catch (e) {
        console.error('Insight load error:', e);
        ic.innerHTML = `<p style="color:var(--sell);font-size:0.85rem;padding:1rem">Error loading insights: ${e.message}</p>`;
    }
}

function renderChart(data) {
    const ctx = document.getElementById('mainChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    const grad = ctx.createLinearGradient(0, 0, 0, 350);
    grad.addColorStop(0, 'rgba(0, 242, 254, 0.3)');
    grad.addColorStop(1, 'rgba(0, 242, 254, 0.0)');

    const labels = data.dates.map(d => {
        const dt = new Date(d);
        return `${dt.getMonth()+1}/${dt.getDate()}`;
    });

    const datasets = [{
        label: `${data.asset}`,
        data: data.closes,
        borderColor: 'rgba(0, 242, 254, 0.9)',
        backgroundColor: grad,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5,
        fill: true,
        tension: 0.4,
        order: 3
    }];

    if (data.sma_20) {
        datasets.push({
            label: 'SMA 20',
            data: data.sma_20,
            borderColor: 'rgba(245, 158, 11, 0.8)',
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
            tension: 0.4,
            borderDash: [],
            order: 2
        });
    }
    if (data.sma_50) {
        datasets.push({
            label: 'SMA 50',
            data: data.sma_50,
            borderColor: 'rgba(167, 139, 250, 0.8)',
            borderWidth: 1.5,
            pointRadius: 0,
            fill: false,
            tension: 0.4,
            order: 1
        });
    }

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#64748b', font: { size: 11 }, boxWidth: 20, padding: 12 }
                },
                tooltip: {
                    backgroundColor: 'rgba(13, 17, 23, 0.95)',
                    titleColor: '#e2e8f0',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.03)' },
                    ticks: { color: '#475569', maxTicksLimit: 8, font: { size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { color: '#475569', font: { size: 11 } }
                }
            }
        }
    });
}

function renderInsight(ins) {
    const ic = document.getElementById('ai-insight-content');
    const signal = ins.signal;
    const badgeClass = signal === 'BUY' ? 'badge-buy' : signal === 'SELL' ? 'badge-sell' : 'badge-hold';
    const confColor = signal === 'BUY' ? 'var(--buy)' : signal === 'SELL' ? 'var(--sell)' : 'var(--hold)';

    ic.innerHTML = `
        <div class="insight-signal-badge ${badgeClass}">${signal}</div>
        <div class="insight-row"><span class="label">Confidence</span><span class="val" style="color:${confColor}">${(ins.confidence*100).toFixed(0)}%</span></div>
        <div class="insight-row"><span class="label">Current Price</span><span class="val">$${ins.current_price.toFixed(2)}</span></div>
        <div class="insight-row"><span class="label">SMA 20-day</span><span class="val" style="color:var(--hold)">${ins.sma_20 ? '$'+ins.sma_20.toFixed(2) : 'N/A'}</span></div>
        <div class="insight-row"><span class="label">SMA 50-day</span><span class="val" style="color:var(--accent-3)">${ins.sma_50 ? '$'+ins.sma_50.toFixed(2) : 'N/A'}</span></div>
        <div class="insight-reason-box">${ins.reason}</div>
    `;
}

// ── Portfolio ─────────────────────────────────────────────────────────────
function setupPortfolioForm() {
    document.getElementById('add-asset-form').addEventListener('submit', e => {
        e.preventDefault();
        const asset = document.getElementById('portfolio-asset-select').value;
        const qty = parseFloat(document.getElementById('portfolio-qty').value);
        if (asset && qty > 0) {
            userPortfolio[asset] = (userPortfolio[asset] || 0) + qty;
            localStorage.setItem('fb_portfolio', JSON.stringify(userPortfolio));
            document.getElementById('portfolio-qty').value = '';
            renderPortfolio();
            lucide.createIcons();
        }
    });
    document.getElementById('btn-portfolio-insight').addEventListener('click', portfolioInsight);
}

function renderPortfolio() {
    const tbody = document.getElementById('portfolio-table-body');
    tbody.innerHTML = '';
    let total = 0;

    Object.entries(userPortfolio).forEach(([asset, qty]) => {
        const price = currentPrices[asset] || 0;
        const val = price * qty;
        total += val;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${asset}</strong></td>
            <td>${qty.toFixed(4)}</td>
            <td>$${price.toFixed(2)}</td>
            <td><strong>$${val.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})}</strong></td>
            <td><button class="action-btn danger" onclick="removeAsset('${asset}')">Remove</button></td>
        `;
        tbody.appendChild(tr);
    });

    if (!Object.keys(userPortfolio).length) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-2);padding:2rem">No holdings yet. Add assets above.</td></tr>';
    }

    document.getElementById('portfolio-total-value').textContent =
        `$${total.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
}

window.removeAsset = function(asset) {
    delete userPortfolio[asset];
    localStorage.setItem('fb_portfolio', JSON.stringify(userPortfolio));
    renderPortfolio();
};

async function portfolioInsight() {
    const btn = document.getElementById('btn-portfolio-insight');
    btn.disabled = true;
    btn.textContent = 'Analyzing...';

    let total = 0, cryptoVal = 0;
    Object.entries(userPortfolio).forEach(([a, q]) => {
        const v = (currentPrices[a] || 0) * q;
        total += v;
        if (a.includes('USD') || a === 'BTC-USD' || a === 'ETH-USD') cryptoVal += v;
    });

    if (total === 0) {
        alert('Your portfolio is empty. Add assets first.');
    } else {
        const cryptoPct = ((cryptoVal / total) * 100).toFixed(1);
        let msg = '';
        if (cryptoPct > 50) msg = `⚠️ High crypto exposure (${cryptoPct}%). Consider diversifying into stable equities like SPY or MSFT.`;
        else if (cryptoPct == 0) msg = `📈 0% crypto. Consider a small BTC-USD allocation (5-10%) to improve portfolio Sharpe ratio.`;
        else msg = `✅ Balanced allocation with ${cryptoPct}% crypto. Monitor SMA crossover signals for timing entries/exits.`;
        alert(msg);
    }

    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="brain-circuit"></i> Generate AI Insight';
    lucide.createIcons();
}

// ── News ──────────────────────────────────────────────────────────────────
async function loadNews(q = 'stocks finance market') {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '<div class="news-loading"><div class="loading-spinner"></div><p>Fetching market intelligence...</p></div>';

    try {
        const r = await fetch(`${API}/news?q=${encodeURIComponent(q)}`);
        const data = await r.json();
        renderNews(data.articles);
    } catch (e) {
        console.error('News load error:', e);
        grid.innerHTML = `<div class="news-loading">
            <p style="color:var(--sell)">Failed to load news.</p>
            <p style="font-size: 0.75rem; color:var(--text-3); margin-top:0.5rem; word-break: break-all;">Error: ${e.message}</p>
        </div>`;
    }
}

function renderNews(articles) {
    const grid = document.getElementById('news-grid');
    grid.innerHTML = '';

    if (!articles || !Array.isArray(articles) || articles.length === 0) {
        grid.innerHTML = '<div class="news-loading"><p>No articles found.</p></div>';
        return;
    }

    articles.forEach(a => {
        const date = new Date(a.publishedAt).toLocaleDateString('en-US', {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'});
        const card = document.createElement('a');
        card.href = a.url;
        card.target = '_blank';
        card.className = 'news-card';
        card.innerHTML = `
            <div class="news-img">
                ${a.urlToImage
                    ? `<img src="${a.urlToImage}" alt="" onerror="this.parentElement.innerHTML='<div class=news-placeholder><svg xmlns=http://www.w3.org/2000/svg viewBox=\\'0 0 24 24\\'><path fill=currentColor d=\\'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z\\'/></svg></div>'">`
                    : '<div class="news-placeholder"><i data-lucide="newspaper"></i></div>'
                }
            </div>
            <div class="news-body">
                <div class="news-source-row">
                    <span class="news-source">${a.source || 'Financial News'}</span>
                    <span class="news-date">${date}</span>
                </div>
                <div class="news-title">${a.title}</div>
                ${a.description ? `<div class="news-desc">${a.description.slice(0, 120)}${a.description.length > 120 ? '...' : ''}</div>` : ''}
            </div>
        `;
        grid.appendChild(card);
    });

    lucide.createIcons();
}

// News filter tags
document.querySelectorAll('.news-tag').forEach(tag => {
    tag.addEventListener('click', () => {
        document.querySelectorAll('.news-tag').forEach(t => t.classList.remove('active'));
        tag.classList.add('active');
        loadNews(tag.dataset.q);
    });
});

// ── Chat ──────────────────────────────────────────────────────────────────
function setupChat() {
    const input = document.getElementById('chat-input');
    const btn = document.getElementById('chat-send');

    const send = async () => {
        const msg = input.value.trim();
        if (!msg) return;
        input.value = '';
        appendChat('user', msg);
        const thinking = appendThinking();

        try {
            const r = await fetch(`${API}/chat`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            });
            const data = await r.json();
            thinking.remove();
            appendChat('assistant', data.response);
        } catch (e) {
            thinking.remove();
            console.error('Chat error:', e);
            appendChat('assistant', `Error: ${e.message}. Please check if the backend is running and Ollama is responsive.`);
        }
    };

    btn.addEventListener('click', send);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
}

function appendChat(role, text) {
    const msgs = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    div.innerHTML = `
        <div class="chat-avatar"><i data-lucide="${role === 'user' ? 'user' : 'bot'}"></i></div>
        <div class="chat-bubble">${text}</div>
    `;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    lucide.createIcons();
    return div;
}

function appendThinking() {
    const msgs = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-msg assistant';
    div.innerHTML = `
        <div class="chat-avatar"><i data-lucide="bot"></i></div>
        <div class="chat-bubble chat-thinking"><span></span><span></span><span></span></div>
    `;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    lucide.createIcons();
    return div;
}

// ── Search ────────────────────────────────────────────────────────────────
function setupSearch() {
    document.getElementById('search-input').addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        if (!q) { renderTable(allAssets); return; }
        renderTable(allAssets.filter(a => a.asset.toLowerCase().includes(q)));
    });
}
