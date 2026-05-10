/* ── Formatting helpers ── */
function formatDollars(value) {
  if (value == null || isNaN(value)) return '$0';
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD',
    minimumFractionDigits: 0, maximumFractionDigits: 0,
  }).format(value);
}

/* ── Tab Navigation ─────────────────────────────────────────────────────── */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tabName = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + tabName).classList.add('active');
  });
});

/* ── Helper: get value helpers ───────────────────────────────────────────── */
function getVal(id) {
  const el = document.getElementById(id);
  return el ? (el.value.trim() || null) : null;
}

function getValByName(name) {
  const el = document.querySelector(`[name="${name}"]`);
  return el ? (el.value.trim() || null) : null;
}

function getNumVal(id) {
  const el = document.getElementById(id);
  if (!el || el.value === '' || el.value == null) return null;
  const n = parseFloat(el.value);
  return isNaN(n) ? null : n;
}

function getIntVal(id) {
  const el = document.getElementById(id);
  if (!el || el.value === '' || el.value == null) return null;
  const n = parseInt(el.value, 10);
  return isNaN(n) ? null : n;
}

function getSelectBool(name) {
  const el = document.querySelector(`select[name="${name}"]`);
  if (!el || el.value === '') return null;
  return el.value === 'true';
}

function getSelectedStatePills() {
  const selected = Array.from(document.querySelectorAll('.state-pill.selected')).map(p => p.dataset.abbr);
  return selected.length ? JSON.stringify(selected) : null;
}

function getLocations() {
  const rows = document.querySelectorAll('.location-row');
  const locs = [];
  rows.forEach(row => {
    const address = row.querySelector('.loc-address').value.trim();
    const emp = row.querySelector('.loc-employees').value;
    if (address || emp) {
      locs.push({ address, employees: emp === '' ? null : parseInt(emp, 10) });
    }
  });
  return JSON.stringify(locs);
}

/* ── DS render helpers ───────────────────────────────────────────────────── */
function pnlClass(v) {
  if (v > 0) return 'positive';
  if (v < 0) return 'negative';
  return '';
}

function setDS(id, val) {
  const el = document.getElementById(id);
  if (el) { el.textContent = val; el.className = 'ds-value'; }
}

function setPnlDS(id, val) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = formatCurrency(val);
    el.className = 'ds-value ' + pnlClass(val || 0);
  }
}

function setField(id, value) {
  const el = document.getElementById(id);
  if (!el || value == null) return;
  el.value = value;
}

/* ── Card Lock ───────────────────────────────────────────────────────────── */
function applyCardLock(card, locked) {
  card.dataset.locked = locked ? 'true' : 'false';
  card.querySelectorAll('input, select, textarea, button:not(.card-lock-btn):not(.btn-add-row)').forEach(el => {
    el.disabled = locked;
  });
  const btn = card.querySelector('.card-lock-btn');
  if (btn) {
    btn.textContent = locked ? '🔒' : '🔓';
    btn.title = locked ? 'Unlock to edit' : 'Lock';
  }
}

function toggleCardLock(btn) {
  const card = btn.closest('.card');
  const locked = card.dataset.locked !== 'false';
  applyCardLock(card, !locked);
  scheduleAutoSave();
}

function restoreCardLockStates(json) {
  let states = null;
  if (json) { try { states = JSON.parse(json); } catch (_) {} }
  const hasStates = states !== null;
  document.querySelectorAll('.card[data-card-id]').forEach(card => {
    const id = card.dataset.cardId;
    const locked = hasStates ? (id in states ? states[id] : true) : false;
    applyCardLock(card, locked);
  });
}

function reapplyCardLock(tbody) {
  const card = tbody.closest('.card[data-card-id]');
  if (card) applyCardLock(card, card.dataset.locked !== 'false');
}

function collectCardLockStates() {
  const states = {};
  document.querySelectorAll('.card[data-card-id]').forEach(card => {
    states[card.dataset.cardId] = card.dataset.locked !== 'false';
  });
  return JSON.stringify(states);
}

/* ── loadPanels ──────────────────────────────────────────────────────────── */
async function loadPanels() {
  const panels = ['general','wc','admin','taxes','benefits','proposal','analysis'];
  await Promise.all(panels.map(async name => {
    const res = await fetch(`/static/partials/panel-${name}.html`);
    const html = await res.text();
    document.getElementById(`panel-${name}`).innerHTML = html;
  }));
}

/* ── Document-level input/change listeners ───────────────────────────────── */
document.addEventListener('input',  e => { if (e.isTrusted && e.target.closest('.tab-panel')) { scheduleAutoSave(); scheduleCalculate(); } });
document.addEventListener('change', e => { if (e.isTrusted && e.target.closest('.tab-panel')) { scheduleAutoSave(); scheduleCalculate(); } });
