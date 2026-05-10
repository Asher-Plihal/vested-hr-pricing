/* ── SUTA Table ──────────────────────────────────────────────────────────── */
let sutaMinRates  = {};
let sutaThresholds = {};
let sutaCostRates  = {};

const CLIENT_REPORTING_STATES = new Set([
  'AK','CT','DE','IA','KS','KY','MA','ME','MI','MN','MS','MT',
  'NE','NV','OH','PA','RI','SC','SD','TN','VT','WA'
]);

async function loadSutaMinRates() {
  try {
    const rates = await apiGet('/suta-rates');
    rates.forEach(r => {
      if (!r.state) return;
      if (r.vhr_min_rate != null) sutaMinRates[r.state]   = r.vhr_min_rate;
      if (r.threshold    != null) sutaThresholds[r.state] = r.threshold;
      if (r.our_cost     != null) sutaCostRates[r.state]  = r.our_cost;
    });
  } catch (e) { /* silent */ }
}

function sutaClientReporting(state) {
  if (!state) return '—';
  return CLIENT_REPORTING_STATES.has(state) ? 'Y' : 'N';
}

function addSutaRow(data) {
  const tbody = document.getElementById('suta-body');
  const idx = tbody.rows.length;
  const state = data?.state || '';
  const minRate   = (state && sutaMinRates[state])   ? formatPct(sutaMinRates[state])        : '—';
  const threshold = (state && sutaThresholds[state]) ? formatCurrency(sutaThresholds[state]) : '—';
  const clientRep = sutaClientReporting(state);
  const wcLns     = collectWCLines();
  const stateWC   = state ? wcLns.filter(l => l.state === state) : [];
  const stateGws  = stateWC.reduce((s, l) => s + (l.annual_gw || 0), 0);
  const stateWses = stateWC.reduce((s, l) => s + (l.ftes || 0) + 0.75 * (l.ptes || 0), 0);
  const wsesWithTurnover = stateWses * 1.1;
  const thresh    = sutaThresholds[state] || 0;
  const taxableGws = Math.min(stateGws, thresh * wsesWithTurnover);
  const tr = document.createElement('tr');
  tr.dataset.sutaIdx = idx;
  tr.innerHTML = `
    <td><input type="text" name="suta_client_rep_${idx}" readonly style="background:#f7fafc;color:#718096;" value="${clientRep}" /></td>
    <td>
      <select name="suta_state_${idx}" onchange="onSutaStateChange(this)">
        <option value="">—</option>
        ${STATE_ABBRS.map(s => `<option value="${s}"${s === state ? ' selected' : ''}>${s}</option>`).join('')}
      </select>
    </td>
    <td><input type="text" name="suta_min_${idx}" readonly style="background:#f7fafc;color:#718096;" value="${minRate}" /></td>
    <td><input type="number" name="suta_rate_${idx}" step="0.01" min="0" max="100" placeholder="0.00" value="${data?.billing_rate != null ? (data.billing_rate * 100).toFixed(2) : ''}" /></td>
    <td><input type="number" name="suta_current_rate_${idx}" step="0.01" min="0" max="100" placeholder="0.00" value="${data?.current_client_rate != null ? (data.current_client_rate * 100).toFixed(2) : ''}" /></td>
    <td><input type="text" name="suta_threshold_${idx}" readonly style="background:#f7fafc;color:#718096;" value="${threshold}" /></td>
    <td><input type="text" name="suta_wses_turnover_${idx}" readonly style="background:#f7fafc;color:#718096;" value="${wsesWithTurnover ? Math.round(wsesWithTurnover) : '—'}" /></td>
    <td><input type="text" name="suta_taxable_gws_${idx}" readonly style="background:#f7fafc;color:#718096;" value="${taxableGws ? formatCurrency(taxableGws) : '—'}" /></td>
  `;
  tr.querySelectorAll('input, select').forEach(el => {
    el.addEventListener('change', scheduleCalculate);
    el.addEventListener('input', scheduleCalculate);
  });
  addRowRemoveModeClick(tr, sutaRM);
  tbody.appendChild(tr);
  reapplyCardLock(tbody);
}

function onSutaStateChange(sel) {
  const tr = sel.closest('tr');
  const state = sel.value;
  tr.querySelector('input[name^="suta_min_"]').value =
    (state && sutaMinRates[state])  ? formatPct(sutaMinRates[state])        : '—';
  tr.querySelector('input[name^="suta_client_rep_"]').value = sutaClientReporting(state);
  tr.querySelector('input[name^="suta_threshold_"]').value =
    (state && sutaThresholds[state]) ? formatCurrency(sutaThresholds[state]) : '—';
  const wcLns   = collectWCLines();
  const stateWC = state ? wcLns.filter(l => l.state === state) : [];
  const gws     = stateWC.reduce((s, l) => s + (l.annual_gw || 0), 0);
  const wses    = stateWC.reduce((s, l) => s + (l.ftes || 0) + 0.75 * (l.ptes || 0), 0);
  const wsesT   = wses * 1.1;
  const thresh  = sutaThresholds[state] || 0;
  const taxGws  = Math.min(gws, thresh * wsesT);
  tr.querySelector('input[name^="suta_wses_turnover_"]').value  = wsesT ? Math.round(wsesT)      : '—';
  tr.querySelector('input[name^="suta_taxable_gws_"]').value   = taxGws ? formatCurrency(taxGws) : '—';
}

function updateSutaRows() {
  const tbody = document.getElementById('suta-body');
  if (!tbody) return;
  tbody.querySelectorAll('tr').forEach(tr => {
    const stateEl = tr.querySelector('select[name^="suta_state_"]');
    if (!stateEl) return;
    const state = stateEl.value;
    const wcLns   = collectWCLines();
    const stateWC = state ? wcLns.filter(l => l.state === state) : [];
    const gws     = stateWC.reduce((s, l) => s + (l.annual_gw || 0), 0);
    const wses    = stateWC.reduce((s, l) => s + (l.ftes || 0) + 0.75 * (l.ptes || 0), 0);
    const wsesT   = wses * 1.1;
    const thresh  = sutaThresholds[state] || 0;
    const taxGws  = Math.min(gws, thresh * wsesT);
    const wsesEl  = tr.querySelector('input[name^="suta_wses_turnover_"]');
    const taxEl   = tr.querySelector('input[name^="suta_taxable_gws_"]');
    if (wsesEl) wsesEl.value = wsesT ? Math.round(wsesT) : '—';
    if (taxEl)  taxEl.value  = taxGws ? formatCurrency(taxGws) : '—';
  });
}

/* sutaRM declared here; button listeners attached in init() */
let sutaRM;
