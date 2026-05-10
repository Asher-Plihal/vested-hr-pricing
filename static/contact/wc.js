/* ── WC helpers ──────────────────────────────────────────────────────────── */

/* ── Toggle explain input on Yes ─────────────────────────────────────────── */
function toggleQExplain(sel) {
  const explain = sel.parentElement.querySelector('.q-explain');
  if (!explain) return;
  explain.style.display = sel.value === 'true' ? 'block' : 'none';
}

/* ── Toggle inline note ──────────────────────────────────────────────────── */
function toggleInlineNote(sel, noteId) {
  const note = document.getElementById(noteId);
  if (!note) return;
  note.style.display = sel.value === 'true' ? 'block' : 'none';
}

/* ── WC Carve-Out Toggle ─────────────────────────────────────────────────── */
function toggleWcCarveout(sel) {
  const wrapper = document.getElementById('wc-sections-wrapper');
  const note = document.getElementById('wc-carveout-note');
  if (sel.value === 'true') {
    wrapper.style.display = 'none';
    note.style.display = 'block';
  } else {
    wrapper.style.display = '';
    note.style.display = 'none';
  }
}

/* ── Generic remove-mode factory ─────────────────────────────────────────── */
function makeRemoveMode(tbodyId, addBtnId, removeBtnId, addBtnLabel, onRemove) {
  let active = false;
  function enter() {
    active = true;
    document.getElementById(removeBtnId).textContent = 'Remove Selected';
    document.getElementById(removeBtnId).style.background = '#fee2e2';
    document.getElementById(addBtnId).textContent = 'Cancel';
    document.getElementById(tbodyId).classList.add('remove-mode');
  }
  function exit(doRemove) {
    active = false;
    const tbody = document.getElementById(tbodyId);
    if (doRemove) {
      tbody.querySelectorAll('tr.tbl-row-selected').forEach(r => r.remove());
      if (onRemove) onRemove();
    } else {
      tbody.querySelectorAll('tr.tbl-row-selected').forEach(r => r.classList.remove('tbl-row-selected'));
    }
    tbody.classList.remove('remove-mode');
    document.getElementById(removeBtnId).textContent = '− Remove Row';
    document.getElementById(removeBtnId).style.background = '';
    document.getElementById(addBtnId).textContent = addBtnLabel;
  }
  return { isActive: () => active, toggle: () => active ? exit(true) : enter(), cancel: () => exit(false) };
}

function addRowRemoveModeClick(tr, rm) {
  tr.addEventListener('click', () => { if (rm.isActive()) tr.classList.toggle('tbl-row-selected'); });
}

/* ── WC Codes Table ──────────────────────────────────────────────────────── */
const STATE_ABBRS = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'];

function applyFlagStyle(input, val) {
  if (val === 'EXCLD') {
    input.style.background = '#fee2e2';
    input.style.color = '#dc2626';
  } else if (val === 'RSTD') {
    input.style.background = '#fef3c7';
    input.style.color = '#d97706';
  } else {
    input.style.background = '#f5f5f5';
    input.style.color = 'inherit';
  }
}

function addWCCodeRow(data) {
  const tbody = document.getElementById('wc-codes-body');
  const idx = tbody.rows.length;
  const tr = document.createElement('tr');
  tr.dataset.wcIdx = idx;
  const stateOpts = STATE_ABBRS.map(s =>
    `<option value="${s}"${s === (data?.state || '') ? ' selected' : ''}>${s}</option>`
  ).join('');
  tr.innerHTML = `
    <td><select name="wc_state_${idx}" style="font-size:0.8rem;">
        <option value="">—</option>${stateOpts}
      </select></td>
    <td><input type="text" name="wc_code_${idx}" placeholder="8810" value="${data?.wc_code || ''}" /></td>
    <td><input type="text" name="wc_desc_${idx}" placeholder="—" style="background:#f5f5f5;cursor:not-allowed;" value="${data?.wc_description || ''}" readonly /></td>
    <td><input type="text" name="wc_hazard_${idx}" placeholder="—" style="background:#f5f5f5;cursor:not-allowed;" value="${data?.hazard_group || ''}" readonly /></td>
    <td><input type="text" name="wc_flag_${idx}" placeholder="—" style="background:#f5f5f5;cursor:not-allowed;" value="${data?.flag_100k || ''}" readonly /></td>
    <td><input type="number" name="wc_payroll_${idx}" step="0.01" min="0" placeholder="0.00" value="${data?.annual_gw || ''}" /></td>
    <td><input type="number" name="wc_fte_${idx}" step="1" min="0" placeholder="0" value="${data?.ftes || ''}" /></td>
    <td><input type="number" name="wc_pte_${idx}" step="1" min="0" placeholder="0" value="${data?.ptes || ''}" /></td>
    <td><input type="number" name="wc_cur_rate_${idx}" step="0.01" min="0" placeholder="0.00" value="${data?.current_client_rate || ''}" /></td>
    <td><input type="text" name="wc_rate_${idx}" placeholder="—" value="${data?.manual_rate ? parseFloat(data.manual_rate).toFixed(2) + '%' : ''}" readonly style="background:#f5f5f5;cursor:not-allowed;text-align:center;" /></td>
  `;
  tr.querySelectorAll('input, select').forEach(inp => {
    inp.addEventListener('input', () => { updateWCTotals(); scheduleCalculate(); });
    inp.addEventListener('change', () => { updateWCTotals(); scheduleCalculate(); });
  });

  // Auto-populate rate and description from WC table when state or code changes
  const stateSelect  = tr.querySelector(`select[name="wc_state_${idx}"]`);
  const codeInput    = tr.querySelector(`input[name="wc_code_${idx}"]`);
  const descInput    = tr.querySelector(`input[name="wc_desc_${idx}"]`);
  const hazardInput  = tr.querySelector(`input[name="wc_hazard_${idx}"]`);
  const flagInput    = tr.querySelector(`input[name="wc_flag_${idx}"]`);
  const rateInput    = tr.querySelector(`input[name="wc_rate_${idx}"]`);

  // Apply color to initial value if loaded from DB
  applyFlagStyle(flagInput, flagInput.value);

  async function lookupWCRate() {
    const s = stateSelect.value;
    const c = codeInput.value.trim();
    if (!s || !c) return;
    try {
      const data = await apiGet(`/wc-rate?state=${encodeURIComponent(s)}&code=${encodeURIComponent(c)}`);
      rateInput.value   = data.rate != null ? parseFloat(data.rate).toFixed(2) + '%' : '';
      descInput.value   = data.description || '';
      hazardInput.value = data.hazard_group || '';
      flagInput.value   = data.flag_100k || '';
      applyFlagStyle(flagInput, flagInput.value);
      rateInput.placeholder = '—';
      stateSelect.style.borderColor = '';
      codeInput.style.borderColor   = '';
    } catch (_) {
      rateInput.value   = '';
      descInput.value   = '';
      hazardInput.value = '';
      flagInput.value   = '';
      applyFlagStyle(flagInput, '');
      rateInput.placeholder = '—';
      stateSelect.style.borderColor = '#f87171';
      codeInput.style.borderColor   = '#f87171';
    }
    updateWCTotals();
    scheduleCalculate();
  }

  stateSelect.addEventListener('change', lookupWCRate);
  codeInput.addEventListener('blur',   lookupWCRate);
  codeInput.addEventListener('change', lookupWCRate);

  addRowRemoveModeClick(tr, wcCodesRM);

  tbody.appendChild(tr);
  reapplyCardLock(tbody);
  updateWCTotals();

  // Always re-run the lookup on DB load — validates the code and shows red border if not found.
  if (data?.state && data?.wc_code) {
    lookupWCRate();
  }
}

function updateWCTotals() {
  const tbody = document.getElementById('wc-codes-body');
  let totalPayroll = 0, totalFTE = 0, totalPTE = 0;
  tbody.querySelectorAll('tr').forEach(tr => {
    totalPayroll += parseFloat(tr.querySelector('input[name^="wc_payroll_"]')?.value || 0) || 0;
    totalFTE     += parseFloat(tr.querySelector('input[name^="wc_fte_"]')?.value || 0) || 0;
    totalPTE     += parseFloat(tr.querySelector('input[name^="wc_pte_"]')?.value || 0) || 0;
  });
  document.getElementById('wc-total-payroll').textContent = '$' + Math.round(totalPayroll).toLocaleString();
  document.getElementById('wc-total-fte').textContent = totalFTE;
  document.getElementById('wc-total-pte').textContent = totalPTE;
}

/* wcCodesRM and wcLossRM are declared here; button listeners attached in init() */
let wcCodesRM;
let wcLossRM;

function addWCLossRow(data) {
  const tbody = document.getElementById('wc-losses-body');
  const i = tbody.rows.length;
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><input type="date" name="loss_start_${i}" value="${data?.coverage_period_start || ''}" /></td>
    <td><input type="date" name="loss_end_${i}" value="${data?.coverage_period_end || ''}" /></td>
    <td><input type="number" name="loss_total_${i}" step="0.01" min="0" placeholder="0.00" value="${data?.total_losses_incurred || ''}" /></td>
    <td><input type="number" name="loss_claims_${i}" step="1" min="0" placeholder="0" value="${data?.num_claims || ''}" /></td>
    <td><input type="number" name="loss_months_${i}" step="1" min="0" placeholder="0" value="${data?.months_in_policy || ''}" /></td>
    <td><input type="number" name="loss_open_${i}" step="1" min="0" placeholder="0" value="${data?.open_claims || ''}" /></td>
  `;
  addRowRemoveModeClick(tr, wcLossRM);
  tbody.appendChild(tr);
  reapplyCardLock(tbody);
}

function toggleQExplainNote(sel, noteId) {
  const note = document.getElementById(noteId);
  if (!note) return;
  note.style.display = sel.value === 'true' ? 'block' : 'none';
}

function toggleMedNote(sel, triggerValue, noteId) {
  document.getElementById(noteId).style.display = sel.value === triggerValue ? 'block' : 'none';
}

function onMedCarveOut(sel) {
  const isCarveOut = sel.value === 'true';
  document.getElementById('med-carveout-note').style.display = isCarveOut ? 'block' : 'none';
  document.getElementById('benefits-sections-wrapper').style.display = isCarveOut ? 'none' : '';
}
