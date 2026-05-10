/* ── Admin Fee method selection ──────────────────────────────────────────── */
function selectAdminMethod(method) {
  document.querySelectorAll('.admin-method-box').forEach(b => b.classList.remove('selected'));
  const box = document.querySelector(`.admin-method-box[data-method="${method}"]`);
  if (box) box.classList.add('selected');
  document.getElementById('admin_method').value = method;
  document.querySelectorAll('.admin-rate-fields').forEach(el => el.style.display = 'none');
  const active = document.getElementById(`admin-rate-fields-${method}`);
  if (active) active.style.display = '';
  scheduleCalculate();
  scheduleAutoSave();
}

/* ── Admin pay-periods helper ────────────────────────────────────────────── */
function getAdminPayPeriods() {
  const freq = document.getElementById('payroll_frequency')?.value || 'biweekly';
  const map  = { weekly: 52, biweekly: 26, semimonthly: 24, monthly: 12 };
  return map[freq] || 26;
}

/* ── Locations ───────────────────────────────────────────────────────────── */
function addLocationRow(data) {
  const list = document.getElementById('locations-list');
  const row = document.createElement('div');
  row.className = 'location-row';
  row.innerHTML = `
    <input type="text" placeholder="Address" class="loc-address" value="${(data?.address || '').replace(/"/g, '&quot;')}" />
    <input type="number" placeholder="# Employees" class="loc-employees" min="0" step="1" value="${data?.employees ?? ''}" />
    <button type="button" class="btn-remove-loc" onclick="removeLocationRow(this)">×</button>
  `;
  list.appendChild(row);
}

function removeLocationRow(btn) {
  if (!confirm('Delete this location?')) return;
  btn.closest('.location-row').remove();
}
