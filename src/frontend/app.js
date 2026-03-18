/**
 * RITUAL - Hermetic LLM Context Management Portal
 * Frontend Application
 */

const API_BASE = '/api';

// State
let currentView = 'dashboard';
let editingMcmId = null;
let mcmFiles = [];
let sigils = [];

// DOM Elements
const views = document.querySelectorAll('.view');
const navButtons = document.querySelectorAll('.nav-btn');
const modalOverlay = document.getElementById('modal-overlay');
const statusDot = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initModals();
    loadProviders();
    loadMcmFiles();
    loadSigils();
    checkHealth();
});

// Navigation
function initNavigation() {
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
        });
    });
}

function switchView(view) {
    // Update nav buttons
    navButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Update views
    views.forEach(v => {
        v.classList.toggle('active', v.id === view);
    });

    currentView = view;

    // Refresh data when switching views
    if (view === 'grimoire') loadMcmFiles();
    if (view === 'sigils') loadSigils();
}

// API Functions
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        if (data.status === 'ok') {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        }
    } catch (error) {
        statusDot.classList.add('disconnected');
        statusText.textContent = 'Disconnected';
    }
}

async function loadProviders() {
    try {
        const response = await fetch(`${API_BASE}/providers`);
        const data = await response.json();
        renderProviders(data.providers);
    } catch (error) {
        console.error('Error loading providers:', error);
        document.getElementById('providers-list').innerHTML = 
            '<div class="error">Failed to load providers</div>';
    }
}

async function loadMcmFiles() {
    try {
        const response = await fetch(`${API_BASE}/mcm-files`);
        const data = await response.json();
        mcmFiles = data.files;
        renderMcmFiles();
        renderRecentFiles();
    } catch (error) {
        console.error('Error loading MCM files:', error);
    }
}

async function loadSigils() {
    try {
        const response = await fetch(`${API_BASE}/sigils`);
        const data = await response.json();
        sigils = data.sigils;
        renderSigils();
    } catch (error) {
        console.error('Error loading sigils:', error);
    }
}

// Render Functions
function renderProviders(providers) {
    const container = document.getElementById('providers-list');
    
    if (!providers || providers.length === 0) {
        container.innerHTML = '<div class="empty-state">No providers configured</div>';
        return;
    }

    container.innerHTML = providers.map(p => `
        <div class="provider-item">
            <div class="provider-info">
                <span class="provider-status ${p.status}"></span>
                <span class="provider-name">${p.name}</span>
            </div>
            <span class="provider-url">${p.url}</span>
        </div>
    `).join('');
}

function renderMcmFiles() {
    const container = document.getElementById('mcm-files-grid');
    
    if (!mcmFiles || mcmFiles.length === 0) {
        container.innerHTML = '<div class="empty-state">The Grimoire is empty. Create your first entry!</div>';
        return;
    }

    container.innerHTML = mcmFiles.map(file => `
        <div class="mcm-card" data-id="${file.id}">
            <div class="mcm-title">${escapeHtml(file.name)}</div>
            <div class="mcm-preview">${escapeHtml(file.content.substring(0, 150))}...</div>
            <div class="mcm-meta">
                <span>Created: ${formatDate(file.created_at)}</span>
                <span>Updated: ${formatDate(file.updated_at)}</span>
            </div>
            <div class="mcm-actions">
                <button onclick="editMcm('${file.id}')">Edit</button>
                <button class="delete" onclick="deleteMcm('${file.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function renderRecentFiles() {
    const container = document.getElementById('recent-files');
    
    if (!mcmFiles || mcmFiles.length === 0) {
        container.innerHTML = '<div class="empty-state">No contexts yet</div>';
        return;
    }

    const recent = mcmFiles.slice(0, 5);
    container.innerHTML = recent.map(file => `
        <div class="recent-item" onclick="editMcm('${file.id}')">
            <strong>${escapeHtml(file.name)}</strong>
            <div style="font-size: 0.8rem; color: var(--text-muted);">
                ${formatDate(file.updated_at)}
            </div>
        </div>
    `).join('');
}

function renderSigils() {
    const container = document.getElementById('sigils-list');
    
    if (!sigils || sigils.length === 0) {
        container.innerHTML = '<div class="empty-state">No sigils stored. Add your first API key!</div>';
        return;
    }

    container.innerHTML = sigils.map(sigil => `
        <div class="sigil-card">
            <div class="sigil-icon">🗝️</div>
            <div class="sigil-name">${escapeHtml(sigil.name)}</div>
            <div class="sigil-provider">${escapeHtml(sigil.provider)}</div>
            <div class="sigil-created">Created: ${formatDate(sigil.created_at)}</div>
            <div class="mcm-actions">
                <button class="delete" onclick="deleteSigil('${sigil.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

// MCM Actions
function createMcm() {
    editingMcmId = null;
    document.getElementById('mcm-name').value = '';
    document.getElementById('mcm-content').value = '';
    showModal('mcm-modal');
}

function editMcm(id) {
    const file = mcmFiles.find(f => f.id === id);
    if (!file) return;

    editingMcmId = id;
    document.getElementById('mcm-name').value = file.name;
    document.getElementById('mcm-content').value = file.content;
    showModal('mcm-modal');
}

async function saveMcm() {
    const name = document.getElementById('mcm-name').value.trim();
    const content = document.getElementById('mcm-content').value;

    if (!name) {
        alert('Please enter a name');
        return;
    }

    try {
        if (editingMcmId) {
            await fetch(`${API_BASE}/mcm-files/${editingMcmId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, content })
            });
        } else {
            await fetch(`${API_BASE}/mcm-files`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, content })
            });
        }

        hideModal();
        loadMcmFiles();
    } catch (error) {
        console.error('Error saving MCM file:', error);
        alert('Failed to save. Please try again.');
    }
}

async function deleteMcm(id) {
    if (!confirm('Are you sure you want to delete this context?')) return;

    try {
        await fetch(`${API_BASE}/mcm-files/${id}`, { method: 'DELETE' });
        loadMcmFiles();
    } catch (error) {
        console.error('Error deleting MCM file:', error);
        alert('Failed to delete. Please try again.');
    }
}

// Sigil Actions
function createSigil() {
    document.getElementById('sigil-name').value = '';
    document.getElementById('sigil-provider').value = 'lm-studio';
    document.getElementById('sigil-key').value = '';
    showModal('sigil-modal');
}

async function saveSigil() {
    const name = document.getElementById('sigil-name').value.trim();
    const provider = document.getElementById('sigil-provider').value;
    const api_key = document.getElementById('sigil-key').value;

    if (!name || !api_key) {
        alert('Please fill in all fields');
        return;
    }

    try {
        await fetch(`${API_BASE}/sigils`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, provider, api_key })
        });

        hideModal();
        loadSigils();
    } catch (error) {
        console.error('Error saving sigil:', error);
        alert('Failed to save. Please try again.');
    }
}

async function deleteSigil(id) {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    try {
        await fetch(`${API_BASE}/sigils/${id}`, { method: 'DELETE' });
        loadSigils();
    } catch (error) {
        console.error('Error deleting sigil:', error);
        alert('Failed to delete. Please try again.');
    }
}

// Modal Handling
function initModals() {
    // MCM Modal
    document.getElementById('btn-create-mcm').addEventListener('click', createMcm);
    document.getElementById('btn-save-mcm').addEventListener('click', saveMcm);
    document.getElementById('btn-cancel-mcm').addEventListener('click', hideModal);

    // Sigil Modal
    document.getElementById('btn-add-sigil').addEventListener('click', createSigil);
    document.getElementById('btn-save-sigil').addEventListener('click', saveSigil);
    document.getElementById('btn-cancel-sigil').addEventListener('click', hideModal);

    // Close buttons
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', hideModal);
    });

    // Close on overlay click
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) hideModal();
    });

    // Quick actions
    document.getElementById('btn-new-context').addEventListener('click', () => {
        switchView('grimoire');
        createMcm();
    });

    document.getElementById('btn-refresh-providers').addEventListener('click', loadProviders);
}

function showModal(modalId) {
    modalOverlay.classList.remove('hidden');
    document.getElementById(modalId).classList.remove('hidden');
}

function hideModal() {
    modalOverlay.classList.add('hidden');
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
}

// Utilities
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
    });
}

// Make functions available globally
window.editMcm = editMcm;
window.deleteMcm = deleteMcm;
window.deleteSigil = deleteSigil;
