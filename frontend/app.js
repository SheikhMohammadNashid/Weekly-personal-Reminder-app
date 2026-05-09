/* ═══════════════════════════════════════════════════════════
   REMINDR — Frontend Application Logic
   ═══════════════════════════════════════════════════════════ */

// Use a relative URL so the browser always hits the same origin (nginx).
// nginx proxies /api/ → backend:8000/api/ — no hardcoded IPs or ports.
const API = '/api';

// ── State ─────────────────────────────────────────────────────
let state = {
  currentReminder: null,
  reminders: [],
  categories: [],
  configs: [],
  history: [],
};

// ── Utilities ─────────────────────────────────────────────────

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API error');
  }
  return res.json();
}

function toast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => el.classList.add('hidden'), 4000);
}

function priorityLabel(p) {
  return { 1: 'LOW', 2: 'MED', 3: 'HIGH' }[p] || 'MED';
}

function priorityClass(p) {
  return { 1: 'p1', 2: 'p2', 3: 'p3' }[p] || 'p2';
}

function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false,
  });
}

function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ── Clock ─────────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById('header-clock');
  function tick() {
    const now = new Date();
    el.textContent = now.toLocaleTimeString('en-IN', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    });
  }
  tick();
  setInterval(tick, 1000);
}

// ── Health / Status ───────────────────────────────────────────
async function checkHealth() {
  const pill = document.getElementById('status-pill');
  const text = document.getElementById('status-text');
  try {
    await fetch('/health');
    pill.className = 'status-pill online';
    text.textContent = 'ONLINE';
  } catch {
    pill.className = 'status-pill offline';
    text.textContent = 'OFFLINE';
  }
}

// ── Tab Navigation ────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${tab}`).classList.add('active');
      // Lazy-load tab data
      if (tab === 'reminders') loadRemindersTable();
      if (tab === 'channels')  loadChannels();
      if (tab === 'history')   loadHistory();
    });
  });
}

// ── DASHBOARD ─────────────────────────────────────────────────
async function loadDashboardStats() {
  // Use allSettled so a single failing endpoint (e.g. empty history on fresh
  // install) doesn't wipe ALL stat cards — each one updates independently.
  const [remindersRes, catsRes, histRes] = await Promise.allSettled([
    apiFetch('/reminders/'),
    apiFetch('/reminders/categories'),
    apiFetch('/notifications/history?limit=100'),
  ]);

  if (remindersRes.status === 'fulfilled') {
    const all = remindersRes.value;
    document.getElementById('stat-total').textContent  = all.length;
    document.getElementById('stat-active').textContent = all.filter(r => r.active).length;
  } else {
    console.warn('Stats: reminders fetch failed —', remindersRes.reason?.message);
  }

  if (catsRes.status === 'fulfilled') {
    document.getElementById('stat-cats').textContent = catsRes.value.length;
  } else {
    console.warn('Stats: categories fetch failed —', catsRes.reason?.message);
  }

  if (histRes.status === 'fulfilled') {
    const cutoff = Date.now() - 30 * 86400 * 1000;
    document.getElementById('stat-sent').textContent = histRes.value.filter(
      h => new Date(h.sent_at).getTime() > cutoff && h.status === 'sent'
    ).length;
  } else {
    document.getElementById('stat-sent').textContent = '—';
    console.warn('Stats: history fetch failed —', histRes.reason?.message);
  }
}

async function loadRandomReminder() {
  const card = document.getElementById('dispatch-card');
  const actions = document.getElementById('dispatch-actions');
  card.innerHTML = `<div class="dispatch-loading"><span class="mono-blink">█</span> Pulling from database...</div>`;
  actions.style.display = 'none';

  try {
    const r = await apiFetch('/reminders/random');
    state.currentReminder = r;
    renderDispatchCard(r);
    actions.style.display = 'flex';
  } catch (e) {
    card.innerHTML = `<div class="dispatch-loading" style="color:var(--red)">ERR: ${escHtml(e.message)}</div>`;
  }
}

function renderDispatchCard(r) {
  const card = document.getElementById('dispatch-card');
  const pClass = priorityClass(r.priority);
  card.innerHTML = `
    <div class="dispatch-meta">
      ${r.category ? `<span class="dispatch-tag cat">${escHtml(r.category.name.toUpperCase())}</span>` : ''}
      <span class="dispatch-tag ${pClass}">PRIORITY ${priorityLabel(r.priority)}</span>
      ${(r.tags || []).map(t => `<span class="dispatch-tag">${escHtml(t)}</span>`).join('')}
    </div>
    <h2 class="dispatch-title">${escHtml(r.title)}</h2>
    <p class="dispatch-body">${escHtml(r.body)}</p>
    ${r.author ? `<p class="dispatch-author">${escHtml(r.author)}</p>` : ''}
  `;
}

document.getElementById('btn-randomize').addEventListener('click', loadRandomReminder);

document.getElementById('btn-send-now').addEventListener('click', async () => {
  const btn = document.getElementById('btn-send-now');
  const resultsEl = document.getElementById('send-results');
  btn.disabled = true;
  btn.textContent = '↻ DISPATCHING...';
  resultsEl.innerHTML = '';

  try {
    const remId = state.currentReminder?.id;
    const url = remId ? `/notifications/send-now?reminder_id=${remId}` : '/notifications/send-now';
    const res = await apiFetch(url, { method: 'POST' });

    res.results.forEach(r => {
      const badge = document.createElement('span');
      badge.className = `send-badge ${r.status}`;
      badge.textContent = `${r.channel.toUpperCase()} ${r.status.toUpperCase()}`;
      badge.title = r.message || '';
      resultsEl.appendChild(badge);
    });

    toast('Dispatch complete.', 'success');
  } catch (e) {
    toast(`Dispatch failed: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '▶ DISPATCH NOW';
  }
});

// ── REMINDER TABLE ────────────────────────────────────────────
async function loadRemindersTable() {
  const tbody = document.getElementById('reminders-tbody');
  tbody.innerHTML = '<tr><td colspan="7" class="table-loading">Loading...</td></tr>';

  try {
    const activeOnly = document.getElementById('filter-active').checked;
    const catId = document.getElementById('filter-cat').value;
    let url = `/reminders/?active_only=${activeOnly}`;
    if (catId) url += `&category_id=${catId}`;
    state.reminders = await apiFetch(url);
    renderRemindersTable(state.reminders);
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="table-loading" style="color:var(--red)">ERR: ${escHtml(e.message)}</td></tr>`;
  }
}

function renderRemindersTable(reminders) {
  const tbody = document.getElementById('reminders-tbody');
  if (!reminders.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="table-loading">No reminders found.</td></tr>';
    return;
  }
  tbody.innerHTML = reminders.map(r => `
    <tr data-id="${r.id}">
      <td style="color:var(--text-3)">#${r.id}</td>
      <td style="color:var(--text); max-width:280px;">${escHtml(r.title)}</td>
      <td>${r.category ? `<span class="badge">${escHtml(r.category.name)}</span>` : '—'}</td>
      <td class="${priorityClass(r.priority)}">
        <span class="priority-dot"></span>${priorityLabel(r.priority)}
      </td>
      <td style="color:var(--text-3)">${r.send_count}</td>
      <td><span class="badge ${r.active ? 'active' : 'inactive'}">${r.active ? 'ACTIVE' : 'INACTIVE'}</span></td>
      <td style="white-space:nowrap">
        <button class="btn-icon" onclick="openEditForm(${r.id})">EDIT</button>
        <button class="btn-icon del" onclick="toggleActive(${r.id}, ${r.active})">${r.active ? 'DEACTIVATE' : 'ACTIVATE'}</button>
        <button class="btn-icon del" onclick="deleteReminder(${r.id}, '${escHtml(r.title).replace(/'/g, "\\'")}')">DELETE</button>
      </td>
    </tr>
  `).join('');
}

async function toggleActive(id, currentlyActive) {
  try {
    await apiFetch(`/reminders/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ active: !currentlyActive }),
    });
    toast(`Reminder ${!currentlyActive ? 'activated' : 'deactivated'}.`, 'success');
    // Refresh both the table AND the dashboard stat counters (active count changes)
    loadRemindersTable();
    loadDashboardStats();
  } catch (e) {
    toast(`Failed: ${e.message}`, 'error');
  }
}

async function deleteReminder(id, title) {
  if (!confirm(`Permanently delete "${title}"?\n\nThis cannot be undone.`)) return;
  try {
    await apiFetch(`/reminders/${id}`, { method: 'DELETE' });
    toast('Reminder deleted.', 'success');
    loadRemindersTable();
    loadDashboardStats();
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

// ── Category filter for table ─────────────────────────────────
async function populateCategoryFilters() {
  try {
    state.categories = await apiFetch('/reminders/categories');
    const filterCat = document.getElementById('filter-cat');
    const fieldCat  = document.getElementById('field-cat');

    state.categories.forEach(c => {
      filterCat.insertAdjacentHTML('beforeend', `<option value="${c.id}">${c.name.toUpperCase()}</option>`);
      fieldCat.insertAdjacentHTML('beforeend', `<option value="${c.id}">${c.name}</option>`);
    });
  } catch {}
}

document.getElementById('filter-active').addEventListener('change', loadRemindersTable);
document.getElementById('filter-cat').addEventListener('change', loadRemindersTable);

// ── Add/Edit Form ─────────────────────────────────────────────
function openAddForm() {
  document.getElementById('form-title').textContent = 'ADD REMINDER';
  document.getElementById('form-reminder-id').value = '';
  document.getElementById('field-title').value  = '';
  document.getElementById('field-body').value   = '';
  document.getElementById('field-author').value = '';
  document.getElementById('field-tags').value   = '';
  document.getElementById('field-cat').value    = '';
  document.getElementById('field-priority').value = '2';
  document.getElementById('reminder-form-wrap').classList.remove('hidden');
}

function openEditForm(id) {
  const r = state.reminders.find(x => x.id === id);
  if (!r) return;
  document.getElementById('form-title').textContent   = 'EDIT REMINDER';
  document.getElementById('form-reminder-id').value   = r.id;
  document.getElementById('field-title').value        = r.title;
  document.getElementById('field-body').value         = r.body;
  document.getElementById('field-author').value       = r.author || '';
  document.getElementById('field-tags').value         = (r.tags || []).join(', ');
  document.getElementById('field-cat').value          = r.category?.id || '';
  document.getElementById('field-priority').value     = r.priority;
  document.getElementById('reminder-form-wrap').classList.remove('hidden');
}

function closeForm() {
  document.getElementById('reminder-form-wrap').classList.add('hidden');
}

document.getElementById('btn-add-reminder').addEventListener('click', openAddForm);
document.getElementById('btn-close-form').addEventListener('click', closeForm);
document.getElementById('btn-cancel-form').addEventListener('click', closeForm);

document.getElementById('btn-save-reminder').addEventListener('click', async () => {
  const id       = document.getElementById('form-reminder-id').value;
  const title    = document.getElementById('field-title').value.trim();
  const body     = document.getElementById('field-body').value.trim();
  const author   = document.getElementById('field-author').value.trim();
  const tagsRaw  = document.getElementById('field-tags').value.trim();
  const catId    = document.getElementById('field-cat').value;
  const priority = parseInt(document.getElementById('field-priority').value);

  if (!title || !body) { toast('Title and body are required.', 'error'); return; }

  const payload = {
    title, body,
    author: author || null,
    tags: tagsRaw ? tagsRaw.split(',').map(t => t.trim()).filter(Boolean) : null,
    category_id: catId ? parseInt(catId) : null,
    priority,
  };

  try {
    if (id) {
      await apiFetch(`/reminders/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
      toast('Reminder updated.', 'success');
    } else {
      await apiFetch('/reminders/', { method: 'POST', body: JSON.stringify(payload) });
      toast('Reminder created.', 'success');
    }
    closeForm();
    loadRemindersTable();
    loadDashboardStats();
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  }
});

// ── CHANNELS ──────────────────────────────────────────────────
async function loadChannels() {
  const grid = document.getElementById('channels-grid');
  grid.innerHTML = '<div class="table-loading">Loading channel config...</div>';

  try {
    state.configs = await apiFetch('/notifications/config');
    grid.innerHTML = state.configs.map(cfg => renderChannelCard(cfg)).join('');
    // Attach save handlers
    state.configs.forEach(cfg => {
      document.getElementById(`save-${cfg.channel}`)
        .addEventListener('click', () => saveChannel(cfg.channel));
    });
  } catch (e) {
    grid.innerHTML = `<div class="table-loading" style="color:var(--red)">ERR: ${escHtml(e.message)}</div>`;
  }
}

function renderChannelCard(cfg) {
  const ch = cfg.channel;
  const isEmail = ch === 'email';
  const isTwilio = ch === 'sms' || ch === 'whatsapp';

  const sendTimeStr = typeof cfg.send_time === 'string'
    ? cfg.send_time.slice(0, 5)
    : '08:00';

  return `
  <div class="channel-card" id="card-${ch}">
    <div class="channel-header">
      <span class="channel-name">${ch.toUpperCase()} CHANNEL</span>
      <label class="toggle-switch">
        <input type="checkbox" id="enabled-${ch}" ${cfg.enabled ? 'checked' : ''} />
        <span class="track"></span>
        <span class="knob"></span>
      </label>
    </div>

    <div class="channel-fields">
      <label class="field-label">RECIPIENT ${isEmail ? 'EMAIL' : 'PHONE (E.164)'}
        <input class="mono-input" id="${ch}-recipient" type="text"
          value="${escHtml(cfg.recipient || '')}"
          placeholder="${isEmail ? 'you@example.com' : '+919876543210'}" />
      </label>

      ${isEmail ? `
        <label class="field-label">SMTP HOST
          <input class="mono-input" id="${ch}-smtp_host" value="${escHtml(cfg.smtp_host || '')}"
            placeholder="smtp.gmail.com" />
        </label>
        <div class="schedule-row">
          <label class="field-label">SMTP PORT
            <input class="mono-input" id="${ch}-smtp_port" type="number"
              value="${cfg.smtp_port || 587}" placeholder="587" />
          </label>
          <label class="field-label">TLS
            <select class="mono-select" id="${ch}-smtp_tls">
              <option value="true"  ${cfg.smtp_tls ? 'selected' : ''}>STARTTLS</option>
              <option value="false" ${!cfg.smtp_tls ? 'selected' : ''}>SSL</option>
            </select>
          </label>
        </div>
        <label class="field-label">SMTP USER
          <input class="mono-input" id="${ch}-smtp_user" value="${escHtml(cfg.smtp_user || '')}"
            placeholder="you@gmail.com" />
        </label>
        <label class="field-label">SMTP PASSWORD
          <input class="mono-input" id="${ch}-smtp_password" type="password" placeholder="••••••••" />
        </label>
      ` : ''}

      ${isTwilio ? `
        <label class="field-label">TWILIO ACCOUNT SID
          <input class="mono-input" id="${ch}-twilio_account_sid"
            value="${escHtml(cfg.twilio_account_sid || '')}"
            placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
        </label>
        <label class="field-label">TWILIO AUTH TOKEN
          <input class="mono-input" id="${ch}-twilio_auth_token" type="password" placeholder="••••••••" />
        </label>
        <label class="field-label">FROM NUMBER ${ch === 'whatsapp' ? '(WhatsApp sandbox)' : ''}
          <input class="mono-input" id="${ch}-twilio_from_number"
            value="${escHtml(cfg.twilio_from_number || '')}"
            placeholder="${ch === 'whatsapp' ? '+14155238886' : '+12015550123'}" />
        </label>
      ` : ''}

      <div class="schedule-row" style="margin-top:12px">
        <label class="field-label">SEND DAY
          <select class="mono-select" id="${ch}-send_day">
            ${['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
              .map(d => `<option value="${d}" ${cfg.send_day === d ? 'selected' : ''}>${d.toUpperCase()}</option>`)
              .join('')}
          </select>
        </label>
        <label class="field-label">SEND TIME
          <input class="mono-input" id="${ch}-send_time" type="time" value="${sendTimeStr}" />
        </label>
      </div>
    </div>

    <div class="channel-footer">
      <button class="btn-primary" id="save-${ch}">SAVE</button>
    </div>
  </div>`;
}

async function saveChannel(ch) {
  const val = id => {
    const el = document.getElementById(`${ch}-${id}`);
    return el ? el.value.trim() : undefined;
  };
  const checkVal = id => {
    const el = document.getElementById(id);
    return el ? el.checked : undefined;
  };

  const payload = {
    enabled: checkVal(`enabled-${ch}`),
    recipient: val('recipient') || null,
    send_day: val('send_day'),
    send_time: val('send_time') || undefined,
  };

  if (ch === 'email') {
    payload.smtp_host     = val('smtp_host') || null;
    payload.smtp_port     = parseInt(val('smtp_port')) || null;
    payload.smtp_user     = val('smtp_user') || null;
    payload.smtp_password = val('smtp_password') || undefined;
    payload.smtp_tls      = val('smtp_tls') === 'true';
  }

  if (ch === 'sms' || ch === 'whatsapp') {
    payload.twilio_account_sid  = val('twilio_account_sid') || null;
    payload.twilio_auth_token   = val('twilio_auth_token') || undefined;
    payload.twilio_from_number  = val('twilio_from_number') || null;
  }

  // Remove undefined keys
  Object.keys(payload).forEach(k => payload[k] === undefined && delete payload[k]);

  try {
    await apiFetch(`/notifications/config/${ch}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    toast(`${ch.toUpperCase()} channel saved.`, 'success');
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  }
}

// ── HISTORY ───────────────────────────────────────────────────
async function loadHistory() {
  const tbody = document.getElementById('history-tbody');
  tbody.innerHTML = '<tr><td colspan="5" class="table-loading">Loading...</td></tr>';

  try {
    state.history = await apiFetch('/notifications/history?limit=50');
    if (!state.history.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="table-loading">No history yet.</td></tr>';
      return;
    }
    tbody.innerHTML = state.history.map(h => `
      <tr>
        <td style="color:var(--text-3);white-space:nowrap">${formatDateTime(h.sent_at)}</td>
        <td style="max-width:260px">${escHtml(h.reminder?.title || '—')}</td>
        <td><span class="badge">${h.channel.toUpperCase()}</span></td>
        <td><span class="badge ${h.status === 'sent' ? 'active' : 'inactive'}">${h.status.toUpperCase()}</span></td>
        <td style="color:var(--text-3);font-size:11px">${escHtml(h.error_message || '—')}</td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" class="table-loading" style="color:var(--red)">ERR: ${escHtml(e.message)}</td></tr>`;
  }
}

document.getElementById('btn-refresh-history').addEventListener('click', loadHistory);

// ── INIT ──────────────────────────────────────────────────────
async function init() {
  startClock();
  initTabs();
  await checkHealth();
  await populateCategoryFilters();
  await loadDashboardStats();
  await loadRandomReminder();

  // Periodic health check + dashboard stat refresh
  setInterval(checkHealth, 30_000);
  setInterval(loadDashboardStats, 60_000); // keep counters live on the dashboard
}

init().catch(console.error);
