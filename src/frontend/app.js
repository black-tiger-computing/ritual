/**
 * RITUAL - 4-Tier MCP Memory Portal
 */

let currentUser = null;
let currentView = 'dashboard';
let editingMemoryId = null;
let memories = [];
let keys = [];

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    await checkAuth();
    initNavigation();
    initModals();
    initAuth();
    loadAll();
}

async function checkAuth() {
    const splash = document.getElementById('splash');
    const login = document.getElementById('login');
    const app = document.getElementById('app');

    try {
        const res = await fetch('/auth/status');
        const data = await res.json();
        splash.classList.add('fade-out');

        if (data.authenticated) {
            currentUser = data;
            showApp();
        } else if (data.configured) {
            login.classList.remove('hidden');
        } else {
            document.getElementById('login-hint')?.classList.remove('hidden');
            document.getElementById('btn-github-login')?.classList.add('hidden');
            login.classList.remove('hidden');
        }
    } catch (error) {
        splash.classList.add('fade-out');
        showApp();
    }
}

function showApp() {
    document.getElementById('app')?.classList.remove('hidden');
    document.getElementById('login')?.classList.add('hidden');
}

function initAuth() {
    document.getElementById('btn-github-login')?.addEventListener('click', () => {
        window.location.href = '/auth/login';
    });

    document.getElementById('btn-skip-login')?.addEventListener('click', () => {
        showApp();
    });
}

function initNavigation() {
    document.querySelectorAll('.nav-btn[data-view]').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            document.querySelectorAll('.nav-btn[data-view]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
            document.getElementById('view-' + view)?.classList.remove('hidden');
            currentView = view;
            if (view === 'memory') loadMemories();
            if (view === 'keys') loadKeys();
            if (view === 'models') loadModels();
        });
    });
}

function initModals() {
    // Memory modal
    document.getElementById('btn-save-memory')?.addEventListener('click', saveMemory);
    document.getElementById('btn-new-memory')?.addEventListener('click', () => openMemoryModal());
    document.getElementById('btn-new-memory-dash')?.addEventListener('click', () => {
        switchView('memory');
        openMemoryModal();
    });
    
    // Key modal
    document.getElementById('btn-save-key')?.addEventListener('click', saveKey);
    document.getElementById('btn-add-key')?.addEventListener('click', () => showModal('key-modal'));
    document.getElementById('btn-add-key-dash')?.addEventListener('click', () => {
        switchView('keys');
        showModal('key-modal');
    });
    
    // Models
    document.getElementById('btn-browse-models-dash')?.addEventListener('click', () => switchView('models'));
    
    // Filter chips
    document.querySelectorAll('.filter-chip[data-tier]').forEach(chip => {
        chip.addEventListener('click', () => {
            const tier = chip.dataset.tier;
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            loadMemories(tier === '' ? null : parseInt(tier));
        });
    });
    
    // Engineer chat
    document.getElementById('btn-engineer-send')?.addEventListener('click', sendToEngineer);
    document.getElementById('engineer-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendToEngineer();
    });
}

function switchView(view) {
    document.querySelectorAll('.nav-btn[data-view]').forEach(b => b.classList.remove('active'));
    document.querySelector(`.nav-btn[data-view="${view}"]`)?.classList.add('active');
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById('view-' + view)?.classList.remove('hidden');
    currentView = view;
}

async function loadAll() {
    await loadMCPStats();
}

async function loadMCPStats() {
    try {
        const res = await fetch('/api/mcp/stats');
        const data = await res.json();
        document.getElementById('stat-tier-0').textContent = data.by_tier?.[0] || 0;
        document.getElementById('stat-tier-1').textContent = data.by_tier?.[1] || 0;
        document.getElementById('stat-tier-2').textContent = data.by_tier?.[2] || 0;
        document.getElementById('stat-tier-3').textContent = data.by_tier?.[3] || 0;
    } catch (error) {
        console.error('Failed to load stats');
    }
}

async function loadMemories(tier = null) {
    const container = document.getElementById('memories-grid');
    if (!container) return;
    container.innerHTML = '<p class="text-muted">Loading...</p>';
    
    try {
        const url = tier ? `/mcp/memories?tier=${tier}` : '/mcp/memories';
        const res = await fetch(url);
        const data = await res.json();
        memories = data.memories || [];
        renderMemories();
    } catch (error) {
        container.innerHTML = '<p class="text-muted">Failed to load memories</p>';
    }
}

function renderMemories() {
    const container = document.getElementById('memories-grid');
    if (!container) return;
    
    if (!memories.length) {
        container.innerHTML = '<p class="text-muted">No memories yet</p>';
        return;
    }
    
    const tierNames = ['Personality', 'Context', 'Frequent', 'Archive'];
    container.innerHTML = memories.map(m => `
        <div class="memory-card">
            <div class="memory-header">
                <span class="tier-badge">${tierNames[m.tier]}</span>
                <div>
                    <button class="btn-secondary" onclick="openMemoryModal('${m.id}')" style="padding: 4px 8px; font-size: 12px;">Edit</button>
                    <button class="btn-secondary" onclick="deleteMemory('${m.id}')" style="padding: 4px 8px; font-size: 12px;">×</button>
                </div>
            </div>
            <div class="memory-key">${escapeHtml(m.key)}</div>
            <div class="memory-content">${escapeHtml(m.content?.substring(0, 120) || '')}${(m.content?.length || 0) > 120 ? '...' : ''}</div>
        </div>
    `).join('');
}

function openMemoryModal(id = null) {
    if (id) {
        const memory = memories.find(m => m.id === id);
        if (memory) {
            editingMemoryId = id;
            document.getElementById('memory-key').value = memory.key || '';
            document.getElementById('memory-content').value = memory.content || '';
            document.getElementById('memory-tier').value = memory.tier || 1;
            document.getElementById('memory-tags').value = (memory.tags || []).join(', ');
            document.getElementById('memory-modal-title').textContent = 'Edit Memory';
        }
    } else {
        editingMemoryId = null;
        document.getElementById('memory-key').value = '';
        document.getElementById('memory-content').value = '';
        document.getElementById('memory-tier').value = '1';
        document.getElementById('memory-tags').value = '';
        document.getElementById('memory-modal-title').textContent = 'New Memory';
    }
    showModal('memory-modal');
}

async function saveMemory() {
    const key = document.getElementById('memory-key').value.trim();
    const content = document.getElementById('memory-content').value;
    const tier = parseInt(document.getElementById('memory-tier').value);
    const tags = document.getElementById('memory-tags').value.split(',').map(t => t.trim()).filter(Boolean);
    
    if (!key) {
        alert('Please enter a key');
        return;
    }

    try {
        if (editingMemoryId) {
            await fetch(`/mcp/memories/${editingMemoryId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key, content, tier, tags})
            });
        } else {
            await fetch('/mcp/memories', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key, content, tier, tags, source: 'user'})
            });
        }
        hideModal();
        loadMemories();
        loadMCPStats();
    } catch (error) {
        alert('Failed to save memory');
    }
}

async function deleteMemory(id) {
    if (!confirm('Delete this memory?')) return;
    try {
        await fetch(`/mcp/memories/${id}`, {method: 'DELETE'});
        loadMemories();
        loadMCPStats();
    } catch (error) {
        alert('Failed to delete memory');
    }
}

async function loadKeys() {
    const container = document.getElementById('keys-list');
    if (!container) return;
    container.innerHTML = '<p class="text-muted">Loading...</p>';
    
    try {
        const res = await fetch('/keys');
        const data = await res.json();
        keys = data.keys || [];
        renderKeys();
    } catch (error) {
        container.innerHTML = '<p class="text-muted">Failed to load keys</p>';
    }
}

function renderKeys() {
    const container = document.getElementById('keys-list');
    if (!container) return;
    
    if (!keys.length) {
        container.innerHTML = '<p class="text-muted">No API keys configured</p>';
        return;
    }
    
    container.innerHTML = keys.map(k => `
        <div class="key-item">
            <div>
                <div class="key-name">${escapeHtml(k.name)}</div>
                <div class="key-provider">${escapeHtml(k.provider)}</div>
            </div>
            <button class="btn-secondary" onclick="deleteKey('${k.id}')" style="padding: 4px 8px;">×</button>
        </div>
    `).join('');
}

async function saveKey() {
    const name = document.getElementById('key-name').value.trim();
    const value = document.getElementById('key-value').value;
    const provider = document.getElementById('key-provider').value;
    
    if (!name || !value) {
        alert('Please fill in all fields');
        return;
    }

    try {
        await fetch('/keys', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, value, provider, key_type: 'provider_api'})
        });
        hideModal();
        loadKeys();
    } catch (error) {
        alert('Failed to save key');
    }
}

async function deleteKey(id) {
    if (!confirm('Delete this key?')) return;
    try {
        await fetch(`/keys/${id}`, {method: 'DELETE'});
        loadKeys();
    } catch (error) {
        alert('Failed to delete key');
    }
}

async function loadModels() {
    const container = document.getElementById('models-grid');
    if (!container) return;
    container.innerHTML = '<p class="text-muted">Loading models...</p>';
    
    try {
        const res = await fetch('/models/recommended');
        const data = await res.json();
        const models = data.models || [];
        renderModels(models);
    } catch (error) {
        container.innerHTML = '<p class="text-muted">Failed to load models</p>';
    }
}

function renderModels(models) {
    const container = document.getElementById('models-grid');
    if (!container) return;
    
    if (!models.length) {
        container.innerHTML = '<p class="text-muted">No models found</p>';
        return;
    }
    
    container.innerHTML = models.slice(0, 12).map(m => `
        <div class="model-card">
            <div class="model-name">${escapeHtml(m.name || m.id)}</div>
            <div class="model-meta">${escapeHtml(m.provider || 'Local')}</div>
        </div>
    `).join('');
}

async function sendToEngineer() {
    const input = document.getElementById('engineer-input');
    const chat = document.getElementById('engineer-chat');
    const message = input.value.trim();
    if (!message) return;
    
    chat.innerHTML += `<p><strong>You:</strong> ${escapeHtml(message)}</p>`;
    input.value = '';
    
    try {
        const res = await fetch('/assistant/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message})
        });
        const data = await res.json();
        chat.innerHTML += `<p><strong>Engineer:</strong> ${escapeHtml(data.response || 'No response')}</p>`;
    } catch (error) {
        chat.innerHTML += `<p class="text-muted">Failed to get response</p>`;
    }
}

// Modal functions
function showModal(id) {
    document.getElementById('modal-overlay')?.classList.remove('hidden');
    document.getElementById(id)?.classList.remove('hidden');
}

function hideModal() {
    document.getElementById('modal-overlay')?.classList.add('hidden');
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
}

// Utility
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global
window.openMemoryModal = openMemoryModal;
window.deleteMemory = deleteMemory;
window.deleteKey = deleteKey;
