// Active Settings Cache
let currentSettings = {};

// 1. Sidebar Tab Switching Navigation
const navItems = document.querySelectorAll('.nav-item');
const tabContents = document.querySelectorAll('.tab-content');
const tabTitle = document.getElementById('tab-title');
const tabSubtitle = document.getElementById('tab-subtitle');

const tabMeta = {
    status: {
        title: "Status Geral",
        subtitle: "Visão em tempo real das ferramentas de compressão ativas."
    },
    config: {
        title: "Configurações",
        subtitle: "Ajuste os parâmetros de economia de tokens e prompts do sistema."
    },
    metrics: {
        title: "Métricas & Economia",
        subtitle: "Histórico completo e análise visual dos custos e tokens economizados."
    },
    tutorials: {
        title: "Tutoriais & Créditos",
        subtitle: "Guias de integração e agradecimentos aos criadores das ferramentas originais."
    }
};

navItems.forEach(item => {
    item.addEventListener('click', () => {
        const tab = item.getAttribute('data-tab');
        
        // Update nav items active state
        navItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        // Show/hide tab contents
        tabContents.forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`tab-${tab}`).classList.add('active');
        
        // Update Title & Subtitle
        if (tabMeta[tab]) {
            tabTitle.textContent = tabMeta[tab].title;
            tabSubtitle.textContent = tabMeta[tab].subtitle;
        }
        
        // Fetch stats if moving to metrics or status
        if (tab === 'metrics' || tab === 'status') {
            loadStats();
        }
    });
});

// 2. Toggles & UI selectors behavior
const toggleHeadroom = document.getElementById('check-headroom');
const headroomSettings = document.getElementById('headroom-settings');
toggleHeadroom.addEventListener('change', () => {
    headroomSettings.style.display = toggleHeadroom.checked ? 'block' : 'none';
});

// Level selector buttons active toggle
function setupLevelSelectors(containerId) {
    const container = document.getElementById(containerId);
    const buttons = container.querySelectorAll('.level-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}
setupLevelSelectors('caveman-levels');
setupLevelSelectors('ponytail-levels');

// Get active level from button group
function getActiveLevel(containerId) {
    const container = document.getElementById(containerId);
    const activeBtn = container.querySelector('.level-btn.active');
    return activeBtn ? activeBtn.getAttribute('data-level') : 'full';
}

// Set active level in button group
function setActiveLevel(containerId, level) {
    const container = document.getElementById(containerId);
    const buttons = container.querySelectorAll('.level-btn');
    buttons.forEach(btn => {
        if (btn.getAttribute('data-level') === level) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// 3. Load settings from Backend
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        if (!res.ok) throw new Error("Failed to load settings.");
        
        const data = await res.json();
        currentSettings = data;
        
        // Map operation mode (radio)
        const radios = document.getElementsByName('dynamicMode');
        radios.forEach(r => {
            r.checked = r.value === data.dynamicMode;
        });
        
        // Map toggles
        document.getElementById('check-rtk').checked = !!data.rtkEnabled;
        document.getElementById('check-headroom').checked = !!data.headroomEnabled;
        document.getElementById('check-caveman').checked = !!data.cavemanEnabled;
        document.getElementById('check-ponytail').checked = !!data.ponytailEnabled;
        
        // Headroom URL input
        document.getElementById('input-headroom-url').value = data.headroomUrl || '';
        headroomSettings.style.display = data.headroomEnabled ? 'block' : 'none';
        
        // Levels
        setActiveLevel('caveman-levels', data.cavemanLevel || 'full');
        setActiveLevel('ponytail-levels', data.ponytailLevel || 'full');
        
        updateStatusTabBadges(data);
    } catch (e) {
        console.error("Error loading settings:", e);
    }
}

// Update Status indicators in the General Status tab
function updateStatusTabBadges(settings) {
    const badgeRtk = document.getElementById('status-rtk');
    const badgeHeadroom = document.getElementById('status-headroom');
    const badgeCaveman = document.getElementById('status-caveman');
    const badgePonytail = document.getElementById('status-ponytail');
    
    const setBadge = (el, active, text = '') => {
        if (active) {
            el.className = "status-value badge active";
            el.textContent = text || "Ativo";
        } else {
            el.className = "status-value badge disabled";
            el.textContent = "Desativado";
        }
    };
    
    setBadge(badgeRtk, settings.rtkEnabled);
    setBadge(badgeHeadroom, settings.headroomEnabled, `Ativo (${settings.headroomUrl})`);
    setBadge(badgeCaveman, settings.cavemanEnabled, `Ativo (${settings.cavemanLevel})`);
    setBadge(badgePonytail, settings.ponytailEnabled, `Ativo (${settings.ponytailLevel})`);
}

// 4. Save settings to Backend
const saveBtn = document.getElementById('btn-save-settings');
saveBtn.addEventListener('click', async () => {
    // Get active radio mode
    let dynamicMode = 'dynamic';
    const radios = document.getElementsByName('dynamicMode');
    radios.forEach(r => {
        if (r.checked) dynamicMode = r.value;
    });
    
    const updates = {
        dynamicMode: dynamicMode,
        rtkEnabled: document.getElementById('check-rtk').checked,
        headroomEnabled: document.getElementById('check-headroom').checked,
        headroomUrl: document.getElementById('input-headroom-url').value,
        cavemanEnabled: document.getElementById('check-caveman').checked,
        cavemanLevel: getActiveLevel('caveman-levels'),
        ponytailEnabled: document.getElementById('check-ponytail').checked,
        ponytailLevel: getActiveLevel('ponytail-levels')
    };
    
    try {
        saveBtn.textContent = "Salvando...";
        saveBtn.disabled = true;
        
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        if (!res.ok) throw new Error("Failed to save settings.");
        
        const data = await res.json();
        currentSettings = data;
        updateStatusTabBadges(data);
        
        alert("Configurações salvas com sucesso!");
    } catch (e) {
        alert("Erro ao salvar configurações.");
        console.error(e);
    } finally {
        saveBtn.textContent = "Salvar Configurações";
        saveBtn.disabled = false;
    }
});

// Helper: formats token sizes to a friendly format
function formatTokens(count) {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1024) return `${(count / 1000).toFixed(1)}k`;
    return count;
}

// 5. Load and Render stats and dashboard
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        if (!res.ok) throw new Error("Failed to load statistics.");
        
        const stats = await res.json();
        
        // A. General Status tab KPIs
        document.getElementById('kpi-total-saved').textContent = formatTokens(stats.totals.tokens_saved);
        document.getElementById('kpi-compression-rate').textContent = `${stats.totals.compression_rate}%`;
        
        // B. Metrics tab KPIs
        document.getElementById('metric-saved-tokens').textContent = formatTokens(stats.totals.tokens_saved);
        document.getElementById('metric-rate').textContent = `${stats.totals.compression_rate}%`;
        
        // Calculate currency (BRL or USD)
        const dollars = stats.totals.cost_saved_usd;
        const formattedCurrency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(dollars * 5.5); // Estimate 1 USD = 5.5 BRL
        document.getElementById('metric-dollars').textContent = formattedCurrency;
        
        // C. Contribution Chart
        const maxSaved = Math.max(
            stats.by_tool.rtk.saved || 1,
            stats.by_tool.headroom.saved || 1,
            stats.by_tool.caveman.saved || 1,
            stats.by_tool.ponytail.saved || 1
        );
        
        const updateBar = (toolId, saved) => {
            const bar = document.getElementById(`bar-${toolId}`);
            const valLabel = document.getElementById(`val-${toolId}`);
            const pct = maxSaved > 1 ? (saved / maxSaved) * 100 : 0;
            
            bar.style.width = `${pct}%`;
            valLabel.textContent = formatTokens(saved);
        };
        
        updateBar('rtk', stats.by_tool.rtk.saved);
        updateBar('headroom', stats.by_tool.headroom.saved);
        updateBar('caveman', stats.by_tool.caveman.saved);
        updateBar('ponytail', stats.by_tool.ponytail.saved);
        
        // D. Daily saving trend
        const trendList = document.getElementById('trend-list');
        trendList.innerHTML = '';
        const trendDays = Object.keys(stats.daily_trend).sort();
        if (trendDays.length === 0) {
            trendList.innerHTML = `<p class="no-data">Nenhuma atividade recente.</p>`;
        } else {
            trendDays.forEach(day => {
                const count = stats.daily_trend[day];
                const row = document.createElement('div');
                row.className = 'trend-row';
                row.innerHTML = `
                    <span class="date">${formatDateString(day)}</span>
                    <span class="val">+${formatTokens(count)} tokens</span>
                `;
                trendList.appendChild(row);
            });
        }
        
        // E. Recent logs table
        const tbody = document.getElementById('logs-tbody');
        tbody.innerHTML = '';
        if (stats.recent.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">Nenhum evento registrado.</td></tr>`;
        } else {
            stats.recent.forEach(log => {
                const row = document.createElement('tr');
                const time = new Date(log.timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                
                const pctSaved = log.original_tokens > 0 ? ((log.tokens_saved / log.original_tokens) * 100).toFixed(0) : 0;
                
                row.innerHTML = `
                    <td>${time}</td>
                    <td><span class="badge ${log.tool === 'rtk' ? 'active' : 'disabled'}">${log.tool.toUpperCase()}</span></td>
                    <td class="font-mono">${log.action}</td>
                    <td>${log.original_tokens}</td>
                    <td>${log.compressed_tokens}</td>
                    <td class="text-success font-bold">+${log.tokens_saved} (${pctSaved}%)</td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (e) {
        console.error("Error loading stats:", e);
    }
}

function formatDateString(dateStr) {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
        return `${parts[2]}/${parts[1]}`;
    }
    return dateStr;
}

// 6. Clear Logs
document.getElementById('btn-clear-logs').addEventListener('click', async () => {
    if (!confirm("Tem certeza que deseja apagar todo o histórico de compressão? Isso zerará os gráficos.")) {
        return;
    }
    
    try {
        const res = await fetch('/api/clear', { method: 'POST' });
        if (!res.ok) throw new Error("Failed to clear logs.");
        loadStats();
    } catch (e) {
        console.error(e);
    }
});

// Helper: Copy text utility
function copyText(elementId) {
    const code = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(code).then(() => {
        alert("Comando copiado para a área de transferência!");
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadStats();
    
    // Auto-update dashboard metrics every 5 seconds for a dynamic feel
    setInterval(loadStats, 5000);
});
