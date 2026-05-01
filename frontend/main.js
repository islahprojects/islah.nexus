const API = {
  BASE: '',
  TOKEN: localStorage.getItem('bridge_token') || 'dev-local-token-change-me'
};

const el = (id) => document.getElementById(id);
const authHeaders = () => ({ Authorization: `Bearer ${API.TOKEN}` });

function shortHash(value, size = 12) {
  if (!value) return 'pending';
  return `${String(value).slice(0, size)}…${String(value).slice(-6)}`;
}

function setDot(state) {
  const dot = el('breathingDot');
  const label = el('dotLabel');
  if (!dot || !label) return;
  dot.classList.remove('cyan', 'green', 'amber', 'red');
  dot.classList.add(state);
  label.textContent = state === 'green' ? 'synced and secure' : state === 'cyan' ? 'mirror active' : state === 'red' ? 'seal failed' : 'local-only';
}

async function createMirror(name, passphrase) {
  const encoder = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));

  const baseKey = await crypto.subtle.importKey(
    'raw', encoder.encode(passphrase), 'PBKDF2', false, ['deriveKey']
  );

  await crypto.subtle.deriveKey(
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
  setDot('cyan');
  await checkBridge();
  await refreshWal();
}

async function checkBridge() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    el('bridgeState').textContent = 'Connected';
    el('bridgeDetail').textContent = data.status;
    setDot('green');
  } catch {
    el('bridgeState').textContent = 'Offline';
    el('bridgeDetail').textContent = 'Local mirror can still operate.';
    setDot('amber');
  }
}

async function refreshWal() {
  try {
    const verify = await fetch('/wal/verify');
    const verifyData = await verify.json();
    el('walValid').textContent = verifyData.valid ? 'valid' : 'broken';
    el('walValid').className = verifyData.valid ? 'ok' : 'bad';
    el('walCount').textContent = verifyData.count ?? 0;
    el('walHead').textContent = shortHash(verifyData.head, 18);

    const tail = await fetch('/wal/tail?n=8', { headers: authHeaders() });
    if (!tail.ok) throw new Error('wal tail blocked');
    const tailData = await tail.json();
    renderWalEntries(tailData.entries || []);
  } catch (error) {
    el('walValid').textContent = 'local-only';
    el('walCount').textContent = '—';
    el('walHead').textContent = 'API token required or node offline';
    renderWalEntries([]);
  }
}

function renderWalEntries(entries) {
  const list = el('walEntries');
  if (!list) return;
  list.innerHTML = '';
  if (!entries.length) {
    const empty = document.createElement('li');
    empty.className = 'wal-empty';
    empty.textContent = 'No WAL entries visible yet. Seal or sync a mirror action to open the trail.';
    list.appendChild(empty);
    return;
  }
  entries.slice().reverse().forEach((entry) => {
    const li = document.createElement('li');
    const proof = entry.proof || {};
    const payload = entry.payload || {};
    li.innerHTML = `
      <div class="wal-row-top">
        <strong>${payload.type || 'sealed.payload'}</strong>
        <span>${new Date(proof.timestamp_ms || Date.now()).toLocaleString()}</span>
      </div>
      <code>proof ${shortHash(proof.proof_hash, 16)}</code>
      <code>prev ${shortHash(proof.prev_hash, 16)}</code>
    `;
    list.appendChild(li);
  });
}

async function syncNow() {
  const payload = {
    dot_id_hash: 'jj',
    source: 'browser_mirror',
    kind: 'mirror_event',
    ciphertext: btoa(`mirror:${Date.now()}`),
    commitment_hash: crypto.randomUUID().replaceAll('-', ''),
    consent: {
      allowed: true,
      purpose: 'mirror_sync',
      retention: 'local_first'
    }
  };

  try {
    const res = await fetch('/bridge/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('sync failed');
    setDot('green');
    await refreshWal();
  } catch {
    setDot('amber');
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

  el('syncNow')?.addEventListener('click', syncNow);
  el('refreshWal')?.addEventListener('click', refreshWal);
  document.querySelectorAll('[data-action="sync_now"]').forEach((btn) => btn.addEventListener('click', syncNow));

  checkBridge();
  refreshWal();
}

window.addEventListener('DOMContentLoaded', init);
