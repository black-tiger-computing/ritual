/**
 * RITUAL - 4-Tier MCP Memory Portal
 */

const API = '';

let currentUser = null;
let currentView = 'dashboard';
let editingMemoryId = null;
let memories = [];
let keys = [];

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    // Check auth status first
    await checkAuth();
    
    initNavigation();
    initModals();
    initAuth();
    loadAll();
    checkHealth();
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
    document.getElementById('app')?.classList.add('visible');
    
    if (currentUser) {
        document.getElementById('user-info')?.classList.remove('hidden');
        document.getElementById('user-name').textContent = currentUser.username;
        if (currentUser.avatar_url) {
            document.getElementById('user-avatar').src = currentUser.avatar_url;
        }
        document.getElementById('btn-logout')?.classList.remove('hidden');
    }
}

function initAuth() {
    document.getElementById('btn-github-login')?.addEventListener('click', () => {
        window.location.href = '/auth/login';
    });
    
    document.getElementById('btn-skip-login')?.addEventListener('click', () => {
        showApp();
    });
    
    document.getElementById('btn-logout')?.addEventListener('click', async () => {
        await fetch('/auth/logout', {method: 'POST'});
        window.location.reload();
    });
}

function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const view = item.dataset.view;
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.getElementById(view)?.classList.add('active');
            currentView = view;
            if (view === 'memory') loadMemories();
            if (view === 'keys') loadKeys();
            if (view === 'models') loadModels();
        });
    });
}

async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        document.getElementById('connection-badge')?.classList.toggle('connected', data.status === 'ok');
        document.querySelector('.connection-text')?.setAttribute('data-status', data.status === 'ok' ? 'connected' : 'disconnected');
    } catch (error) {}
}

async function loadAll() {
    await loadMCPStats();
    await loadKeys();
}

async function loadMCPStats() {
    try {
        const response = await fetch('/api/mcp/stats');
        const data = await response.json();
        document.getElementById('stat-tier-0').textContent = data.by_tier?.[0] || 0;
        document.getElementById('stat-tier-1').textContent = data.by_tier?.[1] || 0;
        document.getElementById('stat-tier-2').textContent = data.by_tier?.[2] || 0;
        document.getElementById('stat-tier-3').textContent = data.by_tier?.[3] || 0;
    } catch (error) {}
}

async function loadMemories(tier = null) {
    const container = document.getElementById('memories-grid');
    if (!container) return;
    container.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';
    try {
        const url = tier ? `/mcp/memories?tier=${tier}` : '/mcp/memories';
        const response = await fetch(url);
        const data = await response.json();
        memories = data.memories || [];
        renderMemories();
        initFilters();
        
        // Update stats
        const stats = data.by_tier || {};
        document.getElementById('stat-tier-0').textContent = stats[0] || 0;
        document.getElementById('stat-tier-1').textContent = stats[1] || 0;
        document.getElementById('stat-tier-2').textContent = stats[2] || 0;
        document.getElementById('stat-tier-3').textContent = stats[3] || 0;
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><p>Failed to load</p></div>';
    }
}

function renderMemories() {
    const container = document.getElementById('memories-grid');
    if (!container) return;
    if (!memories.length) {
        container.innerHTML = '<div class="empty-state"><p>No memories yet</p><button class="btn-primary" onclick="openMemoryModal()">+ Create First Memory</button></div>';
        return;
    }
    const tierNames = ['Personality', 'Context', 'Frequent', 'Archive'];
    const tierIcons = ['🜃', '☉', '☽', '☄'];
    container.innerHTML = memories.map(m => `
        <div class="memory-card tier-${m.tier}">
            <div class="memory-header">
                <span class="tier-badge tier-${m.tier}">${tierIcons[m.tier]} ${tierNames[m.tier]}</span>
                <div class="memory-actions">
                    <button class="btn-icon-sm" onclick="openMemoryModal('${m.id}')">✎</button>
                    <button class="btn-icon-sm delete" onclick="deleteMemory('${m.id}')">×</button>
                </div>
            </div>
            <h3 class="memory-key">${escapeHtml(m.key)}</h3>
            <p class="memory-content">${escapeHtml(m.content?.substring(0, 150) || '')}${(m.content?.length || 0) > 150 ? '...' : ''}</p>
            ${m.tags?.length ? `<div class="memory-tags">${m.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}</div>` : ''}
            <div class="memory-meta">
                <span>Access: ${m.access_count || 0}</span>
                <span>Score: ${((m.elevation_score || 0) * 100).toFixed(0)}%</span>
            </div>
        </div>
    `).join('');
}

function openMemoryModal(id = null) {
    const modal = document.getElementById('memory-modal');
    const title = document.getElementById('memory-modal-title');
    
    if (id) {
        const memory = memories.find(m => m.id === id);
        if (memory) {
            editingMemoryId = id;
            document.getElementById('memory-key').value = memory.key || '';
            document.getElementById('memory-content').value = memory.content || '';
            document.getElementById('memory-tier').value = memory.tier || 1;
            document.getElementById('memory-tags').value = (memory.tags || []).join(', ');
            title.textContent = 'Edit Memory';
        }
    } else {
        editingMemoryId = null;
        document.getElementById('memory-key').value = '';
        document.getElementById('memory-content').value = '';
        document.getElementById('memory-tier').value = '1';
        document.getElementById('memory-tags').value = '';
        title.textContent = 'New Memory';
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

function initFilters() {
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            loadMemories(chip.dataset.tier === 'all' ? null : parseInt(chip.dataset.tier));
        });
    });
}

async function loadKeys() {
    try {
        const response = await fetch('/keys');
        const data = await response.json();
        keys = data.keys || [];
        const container = document.getElementById('keys-list');
        if (container) {
            container.innerHTML = keys.length ? keys.map(k => `
                <div class="key-card">
                    <span class="key-icon">🗝</span>
                    <div class="key-name">${escapeHtml(k.name || '')}</div>
                    <div class="key-provider">${k.provider || 'Unknown'}</div>
                </div>
            `).join('') : '<div class="empty-state"><p>No API keys</p></div>';
        }
    } catch (error) {}
}

async function loadModels() {
    try {
        const response = await fetch('/models/recommended');
        const data = await response.json();
        const container = document.getElementById('recommended-models');
        if (container && data.recommended) {
            container.innerHTML = data.recommended.slice(0, 6).map(m => `
                <div class="model-card">
                    <h4>${escapeHtml(m.name)}</h4>
                    <p>${escapeHtml(m.use_case)}</p>
                    <span class="model-size">${m.size}</span>
                </div>
            `).join('');
        }
    } catch (error) {}
}

function initModals() {
    // Memory modal
    document.getElementById('btn-create-memory')?.addEventListener('click', () => openMemoryModal());
    document.getElementById('btn-new-memory')?.addEventListener('click', () => openMemoryModal());
    document.getElementById('btn-save-memory')?.addEventListener('click', saveMemory);
    document.getElementById('btn-cancel-memory')?.addEventListener('click', hideModal);
    
    // Key modal
    document.getElementById('btn-add-key')?.addEventListener('click', () => showModal('key-modal'));
    document.getElementById('btn-save-key')?.addEventListener('click', async () => {
        const name = document.getElementById('key-name').value.trim();
        const value = document.getElementById('key-value').value;
        const provider = document.getElementById('key-provider').value;
        if (!name || !value) return;
        await fetch('/keys', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, value, provider, key_type: 'provider_api'})
        });
        hideModal();
        loadKeys();
    });
    document.getElementById('btn-cancel-key')?.addEventListener('click', hideModal);
    
    // Generic close handlers
    document.querySelectorAll('.close-btn').forEach(btn => btn.addEventListener('click', hideModal));
    document.getElementById('modal-overlay')?.addEventListener('click', e => { if (e.target.id === 'modal-overlay') hideModal(); });
}

// Global functions
window.openMemoryModal = openMemoryModal;
window.deleteMemory = deleteMemory;

function showModal(id) {
    document.getElementById('modal-overlay')?.classList.remove('hidden');
    document.getElementById(id)?.classList.remove('hidden');
}

function hideModal() {
    document.getElementById('modal-overlay')?.classList.add('hidden');
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.deleteKey = async function(id) {
    await fetch(`/keys/${id}`, {method: 'DELETE'});
    loadKeys();
};