const API = {
  BASE: '',
  TOKEN: localStorage.getItem('bridge_token') || 'dev-token'
};

const el = (id) => document.getElementById(id);

async function createMirror(name, passphrase) {
  const encoder = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));

  const baseKey = await crypto.subtle.importKey(
    'raw', encoder.encode(passphrase), 'PBKDF2', false, ['deriveKey']
  );

  const key = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );

  localStorage.setItem('mirror_active', 'true');
  localStorage.setItem('mirror_name', name);

  el('create-view').classList.add('hidden');
  el('dashboard-view').classList.remove('hidden');
  el('mirrorDisplayName').textContent = name;
}

async function checkBridge() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    el('bridgeState').textContent = 'Connected';
    el('bridgeDetail').textContent = data.status;
  } catch {
    el('bridgeState').textContent = 'Offline';
  }
}

function init() {
  const active = localStorage.getItem('mirror_active');
  if (active) {
    el('create-view').classList.add('hidden');
    el('dashboard-view').classList.remove('hidden');
    el('mirrorDisplayName').textContent = localStorage.getItem('mirror_name') || 'JJ';
  }

  document.getElementById('createMirrorForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await createMirror(el('mirrorName').value, el('mirrorPassphrase').value);
  });

  checkBridge();
}

window.addEventListener('DOMContentLoaded', init);
