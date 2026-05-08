/* ── app.js — shared utilities for VestedHR Pricing Tool ──────────────────── */

/**
 * Show a dismissing toast notification at bottom-right.
 * @param {string} message
 * @param {'success'|'error'|'info'} type
 */
function showToast(message, type = 'success') {
  const existing = document.querySelectorAll('.toast');
  existing.forEach(t => t.remove());

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 350);
  }, 3200);
}

/**
 * Format a number as currency: $1,234.56
 * @param {number|null|undefined} value
 * @returns {string}
 */
function formatCurrency(value) {
  if (value == null || isNaN(value)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format a decimal fraction as a percentage: 0.062 → "6.20%"
 * @param {number|null|undefined} value
 * @returns {string}
 */
function formatPct(value) {
  if (value == null || isNaN(value)) return '0.00%';
  return (value * 100).toFixed(2) + '%';
}

/**
 * GET request wrapper. Returns parsed JSON. Throws on non-OK status.
 * @param {string} path  e.g. "/clients/1"
 * @returns {Promise<any>}
 */
async function apiGet(path) {
  const res = await fetch(path, {
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * POST request wrapper. Returns parsed JSON. Throws on non-OK status.
 * @param {string} path
 * @param {any} body
 * @returns {Promise<any>}
 */
async function apiPost(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * PUT request wrapper. Returns parsed JSON. Throws on non-OK status.
 * @param {string} path
 * @param {any} body
 * @returns {Promise<any>}
 */
async function apiPut(path, body) {
  const res = await fetch(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PUT ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * DELETE request wrapper. Returns parsed JSON. Throws on non-OK status.
 * @param {string} path
 * @returns {Promise<any>}
 */
async function apiDelete(path) {
  const res = await fetch(path, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`DELETE ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

/* ── Global client search ─────────────────────────────────────────────────── */
(function () {
  const input = document.querySelector('.topnav-search');
  if (!input) return;

  const style = document.createElement('style');
  style.textContent = `
    #vhr-search-dropdown {
      position: fixed;
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 8px 24px rgba(0,0,0,.13), 0 2px 6px rgba(0,0,0,.07);
      border: 1px solid #e2e8f0;
      overflow: hidden;
      z-index: 9999;
      list-style: none;
      padding: 4px 0;
      margin: 0;
      display: none;
      min-width: 240px;
    }
    #vhr-search-dropdown li {
      padding: 8px 14px;
      cursor: pointer;
      user-select: none;
      -webkit-user-select: none;
      border-bottom: 1px solid #f1f5f9;
    }
    #vhr-search-dropdown li:last-child { border-bottom: none; }
    #vhr-search-dropdown li:hover,
    #vhr-search-dropdown li.search-active { background: #f8f9fa; }
    #vhr-search-dropdown .sr-name {
      display: block;
      font-size: .875rem;
      font-weight: 600;
      color: #1e3154;
      line-height: 1.3;
    }
    #vhr-search-dropdown .sr-sub {
      display: block;
      font-size: .75rem;
      color: #94a3b8;
      margin-top: 1px;
      line-height: 1.3;
    }
  `;
  document.head.appendChild(style);

  input.setAttribute('autocomplete', 'off');

  const dropdown = document.createElement('ul');
  dropdown.id = 'vhr-search-dropdown';
  document.body.appendChild(dropdown);

  let searchClients = null;

  function ensureClients() {
    if (searchClients !== null) return Promise.resolve();
    return apiGet('/clients').then(data => { searchClients = data; }).catch(() => { searchClients = []; });
  }

  function positionDropdown() {
    const rect = input.getBoundingClientRect();
    dropdown.style.top   = (rect.bottom + 6) + 'px';
    dropdown.style.left  = rect.left + 'px';
    dropdown.style.width = rect.width + 'px';
  }

  function hideDropdown() {
    dropdown.style.display = 'none';
    dropdown.innerHTML = '';
  }

  function activeItem() {
    return dropdown.querySelector('li.search-active');
  }

  function setActive(li) {
    dropdown.querySelectorAll('li').forEach(el => el.classList.remove('search-active'));
    if (li) li.classList.add('search-active');
  }

  function runFilter(q) {
    if (!q) { hideDropdown(); return; }
    const matches = (searchClients || [])
      .filter(c => (c.legal_name || '').toLowerCase().includes(q.toLowerCase()))
      .slice(0, 8);
    if (matches.length === 0) { hideDropdown(); return; }
    dropdown.innerHTML = '';
    matches.forEach(c => {
      const li = document.createElement('li');
      li.dataset.id = c.id;
      li.innerHTML =
        `<span class="sr-name">${c.legal_name || 'Unnamed'}</span>` +
        (c.consultant_name ? `<span class="sr-sub">${c.consultant_name}</span>` : '');
      li.addEventListener('mousedown', () => {
        window.location.href = `/static/client.html?id=${c.id}`;
      });
      dropdown.appendChild(li);
    });
    positionDropdown();
    dropdown.style.display = 'block';
  }

  function onActivate() {
    ensureClients().then(() => runFilter(input.value.trim()));
  }

  input.addEventListener('focus', onActivate);
  input.addEventListener('input', onActivate);

  input.addEventListener('keydown', e => {
    const items = Array.from(dropdown.querySelectorAll('li'));
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const cur = activeItem();
      const next = cur ? cur.nextElementSibling : items[0];
      if (next) setActive(next);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const cur = activeItem();
      const prev = cur ? cur.previousElementSibling : items[items.length - 1];
      if (prev) setActive(prev);
    } else if (e.key === 'Enter') {
      const cur = activeItem();
      if (cur) window.location.href = `/static/client.html?id=${cur.dataset.id}`;
    } else if (e.key === 'Escape') {
      input.value = '';
      hideDropdown();
    }
  });

  input.addEventListener('blur', () => setTimeout(hideDropdown, 50));
}());
