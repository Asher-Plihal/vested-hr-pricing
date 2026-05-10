/* ── State ──────────────────────────────────────────────────────────────── */
const clientId = new URLSearchParams(window.location.search).get('id');
let calcDebounceTimer = null;
let autoSaveTimer = null;
let isPopulating = false;
let _avgAnnualLoss = null;
let systemConfig = {};

/* ── Autosave ────────────────────────────────────────────────────────────── */
function scheduleAutoSave() {
  if (!clientId || isPopulating) return;
  clearTimeout(autoSaveTimer);
  autoSaveTimer = setTimeout(doAutoSave, 600);
}

async function doAutoSave() {
  if (!clientId) return;
  const payload = collectClientPayload();
  const saveBody = {
    ...payload.client,
    wc_lines:   payload.wc_lines,
    suta_lines: payload.suta_lines,
    wc_losses:  collectWCLosses(),
  };
  try {
    await apiPut('/clients/' + clientId, saveBody);
  } catch (e) {
    showToast('Autosave failed: ' + e.message, 'error');
  }
}

/* ── Calculate ───────────────────────────────────────────────────────────── */
function scheduleCalculate() {
  clearTimeout(calcDebounceTimer);
  calcDebounceTimer = setTimeout(runCalculate, 500);
}

async function runCalculate() {
  const payload = collectClientPayload();
  const hasData = payload.wc_lines.some(l => l.annual_gw > 0) || payload.suta_lines.length > 0;
  if (!hasData) return;

  // CalculateRequest expects flat fields — spread client fields to top level
  const calcPayload = {
    ...payload.client,
    wc_lines:   payload.wc_lines,
    suta_lines: payload.suta_lines,
  };

  document.getElementById('summary-calculating').style.display = 'block';
  document.getElementById('summary-content').style.opacity = '0.4';

  try {
    const result = await apiPost('/calculate', calcPayload);
    renderSummary(result);
  } catch (e) {
    console.error('Calculate error:', e);
  } finally {
    document.getElementById('summary-calculating').style.display = 'none';
    document.getElementById('summary-content').style.opacity = '1';
  }
}

/* ── Collect helpers ─────────────────────────────────────────────────────── */
function collectWCLines() {
  const lines = [];
  const tbody = document.getElementById('wc-codes-body');
  tbody.querySelectorAll('tr').forEach(tr => {
    const state               = tr.querySelector('select[name^="wc_state_"]')?.value?.trim() || null;
    const wc_code             = tr.querySelector('input[name^="wc_code_"]')?.value?.trim() || null;
    const wc_description      = tr.querySelector('input[name^="wc_desc_"]')?.value?.trim() || null;
    const hazard_group        = tr.querySelector('input[name^="wc_hazard_"]')?.value?.trim() || null;
    const flag_100k           = tr.querySelector('input[name^="wc_flag_"]')?.value?.trim() || null;
    const annual_gw           = parseFloat(tr.querySelector('input[name^="wc_payroll_"]')?.value) || 0;
    const ftes                = parseFloat(tr.querySelector('input[name^="wc_fte_"]')?.value) || 0;
    const ptes                = parseFloat(tr.querySelector('input[name^="wc_pte_"]')?.value) || 0;
    const current_client_rate = parseFloat(tr.querySelector('input[name^="wc_cur_rate_"]')?.value) || 0;
    const manual_rate         = parseFloat(tr.querySelector('input[name^="wc_rate_"]')?.value) || 0;
    lines.push({ state, wc_code, wc_description, hazard_group, flag_100k, annual_gw, ftes, ptes, current_client_rate, manual_rate });
  });
  return lines;
}

function collectSutaLines() {
  const lines = [];
  const wcLines = collectWCLines();
  const tbody = document.getElementById('suta-body');
  tbody.querySelectorAll('tr').forEach(tr => {
    const state       = tr.querySelector('select[name^="suta_state_"]')?.value?.trim() || null;
    const rateRaw     = parseFloat(tr.querySelector('input[name^="suta_rate_"]')?.value) || 0;
    const currRateRaw = parseFloat(tr.querySelector('input[name^="suta_current_rate_"]')?.value) || 0;
    const stateWCLines = state ? wcLines.filter(l => l.state === state) : [];
    const gws        = stateWCLines.reduce((sum, l) => sum + (l.annual_gw || 0), 0);
    const total_wses = stateWCLines.reduce((sum, l) => sum + (l.ftes || 0) + 0.75 * (l.ptes || 0), 0);
    lines.push({
      state,
      gws,
      total_wses,
      current_client_rate: currRateRaw / 100,
      billing_rate: rateRaw / 100,
      cost_rate: sutaMinRates[state]   || 0,
      threshold: sutaThresholds[state] || 0,
      turnover_pct: 0.1,
    });
  });
  return lines;
}

function collectWCLosses() {
  const losses = [];
  document.getElementById('wc-losses-body').querySelectorAll('tr').forEach(tr => {
    const start  = tr.querySelector('input[name^="loss_start_"]')?.value || null;
    const end    = tr.querySelector('input[name^="loss_end_"]')?.value || null;
    const total  = parseFloat(tr.querySelector('input[name^="loss_total_"]')?.value) || 0;
    const claims = parseInt(tr.querySelector('input[name^="loss_claims_"]')?.value) || 0;
    const months = parseInt(tr.querySelector('input[name^="loss_months_"]')?.value) || 0;
    const open   = parseInt(tr.querySelector('input[name^="loss_open_"]')?.value) || 0;
    losses.push({
      coverage_period_start: start,
      coverage_period_end:   end,
      total_losses_incurred: total,
      num_claims:   claims,
      months_in_policy: months,
      open_claims:  open,
    });
  });
  return losses;
}

function collectClientPayload() {
  const adminMethod  = getIntVal('admin_method') || 1;

  const internal = getNumVal('internal_commission_pct') || 0;
  const external  = getNumVal('external_commission_pct') || 0;
  const brokerWC  = getNumVal('broker_wc_commission_pct') || 0;

  const client = {
    legal_name:             getVal('legal_name'),
    consultant_name:        getVal('consultant_name'),
    consultant_name_split:  getVal('consultant_name_split'),
    date:                   getVal('date'),
    dba:                    getVal('dba'),
    referral_partner_business: getVal('referral_partner_business'),
    referral_partner_name:  getVal('referral_partner_name'),
    main_address:           getVal('main_address'),
    city:                   getVal('city'),
    state:                  getVal('state'),
    zip:                    getVal('zip'),
    county:                 getVal('county'),
    fein:                   getVal('fein'),
    website:                getVal('website'),
    org_structure:          getVal('org_structure'),
    naics:                  getVal('naics'),
    sic:                    getVal('sic'),
    years_in_business:      getIntVal('years_in_business'),
    num_locations:          getIntVal('num_locations'),
    main_phone:             getVal('main_phone'),
    owner_name:             getVal('owner_name'),
    owner_phone:            getVal('owner_phone'),
    owner_email:            getVal('owner_email'),
    owner_cell:             getVal('owner_cell'),
    contact_name:           getVal('contact_name'),
    contact_phone:          getVal('contact_phone'),
    contact_cell:           getVal('contact_cell'),
    contact_email:          getVal('contact_email'),
    states_operating:       getSelectedStatePills(),
    locations:              getLocations(),
    description_of_operations: getVal('description_of_operations'),

    // Compliance (select-based)
    eeoc_violations:        getSelectBool('eeoc_violations'),
    eeoc_explanation:       getValByName('eeoc_explanation'),
    active_claims:          getSelectBool('active_claims'),
    active_claims_explanation: getValByName('active_claims_explanation'),
    cobra_continuation:     getSelectBool('cobra_continuation'),
    cobra_explanation:      getValByName('cobra_explanation'),
    past_layoffs:           getSelectBool('past_layoffs'),
    past_layoffs_explanation: getValByName('past_layoffs_explanation'),
    future_layoffs:         getSelectBool('future_layoffs'),
    future_layoffs_explanation: getValByName('future_layoffs_explanation'),
    leave_of_absence:       getSelectBool('leave_of_absence'),
    leave_explanation:      getValByName('leave_explanation'),

    // Medical (select-based)
    medical_carve_out:              getSelectBool('medical_carve_out'),
    enrolled_over_50:               getSelectBool('enrolled_over_50'),
    enrolled_under_10:              getSelectBool('enrolled_under_10'),
    level_funded_plan:              getSelectBool('level_funded_plan'),
    currently_has_health_insurance: getSelectBool('currently_has_health_insurance'),
    census_available:               getSelectBool('census_available'),
    cobra_expected:                 getSelectBool('cobra_expected'),

    // Ancillary
    offers_ancillary_benefits: getSelectBool('offers_ancillary_benefits'),
    wants_ancillary_benefits:  getSelectBool('wants_ancillary_benefits'),
    current_contribution_strategy: getVal('current_contribution_strategy'),
    new_contribution_strategy:     getVal('new_contribution_strategy'),

    // Payroll
    payroll_frequency:          getVal('payroll_frequency'),
    pay_cycle_start:            getVal('pay_cycle_start'),
    pay_cycle_end:              getVal('pay_cycle_end'),
    pay_date:                   getVal('pay_date'),
    method_of_payment:          getVal('method_of_payment'),
    requested_payroll_delivery: getVal('requested_payroll_delivery'),
    effective_date:             getVal('effective_date'),

    // WC
    wc_carve_out:        getSelectBool('wc_carve_out'),
    proposed_mod:        getNumVal('pricing_proposed_mod'),
    shared_claim_fee:    getNumVal('shared_claim_fee'),
    min_wc_fee_per_week: getNumVal('min_wc_fee_per_week'),
    new_company:         getSelectBool('new_company'),
    gaps_in_coverage:    getSelectBool('gaps_in_coverage'),

    // Pricing — each method stores its rate independently
    admin_method:              adminMethod,
    admin_rate:                (getNumVal('admin_rate') || 0) / 100,
    admin_rate_2:              getNumVal('admin_rate_2') || 0,
    admin_rate_3:              getNumVal('admin_rate_3') || 0,
    current_admin_rate:        getNumVal('current_admin_rate') || 0,
    current_admin_rate_2:      getNumVal('current_admin_rate_2') || 0,
    current_admin_rate_3:      getNumVal('current_admin_rate_3') || 0,
    implementation_fee:        getNumVal('implementation_fee'),
    epli_rate:                 getNumVal('epli_rate'),
    internal_commission_pct:   internal / 100,
    external_commission_pct:   external / 100,
    broker_wc_commission_pct:  brokerWC / 100,
    futa_turnover_rate:        getNumVal('futa_turnover_rate'),
    card_lock_states:          collectCardLockStates(),
  };

  return {
    client,
    wc_lines:   collectWCLines(),
    suta_lines: collectSutaLines(),
  };
}

/* ── Render Summary ──────────────────────────────────────────────────────── */
function renderSummary(r) {
  const ao = r.admin_overview   || {};
  const wo = r.wc_overview      || {};
  const to = r.taxes_overview   || {};
  const oi = r.other_items      || {};
  const co = r.commissions      || {};

  setDS('s-total-wses',   ao.total_wses != null ? Math.round(ao.total_wses) : '0');
  setDS('s-total-gws',    formatCurrency(ao.total_gws));
  setDS('s-avg-wage',     formatCurrency(ao.avg_wage));
  setDS('s-admin-margin', formatCurrency(ao.admin_margin));
  const adminPct    = ao.total_gws  > 0 ? ao.admin_margin / ao.total_gws  : null;
  const adminPerWse = ao.total_wses > 0 ? ao.admin_margin / ao.total_wses : null;
  const elAdminPct    = document.getElementById('s-admin-margin-pct');
  const elAdminPerWse = document.getElementById('s-admin-margin-per-wse');
  if (elAdminPct)    elAdminPct.textContent    = adminPct    != null ? formatPct(adminPct)                   : '—';
  if (elAdminPerWse) elAdminPerWse.textContent = adminPerWse != null ? formatCurrency(adminPerWse) + '/WSE'  : '—';

  setDS('s-wc-billed',      formatCurrency(wo.wc_billed));
  setDS('s-wc-fixed-cost',  formatCurrency(wo.wc_fixed_cost));
  setDS('s-wc-loss-fund',   formatCurrency(wo.wc_loss_fund));
  setDS('s-total-wc-cost',  formatCurrency(wo.total_wc_cost));
  setPnlDS('s-wc-profit-loss',  wo.wc_profit_loss);
  const wcMod = parseFloat(document.getElementById('pricing_proposed_mod')?.value);
  const wcBilledRate = ao.total_gws > 0 ? wo.wc_billed / ao.total_gws : null;
  const elWcMod = document.getElementById('s-wc-mod');
  const elWcBilledRate = document.getElementById('s-wc-billed-rate');
  if (elWcMod)       elWcMod.textContent       = !isNaN(wcMod) ? 'Mod: ' + wcMod.toFixed(2)                  : '—';
  if (elWcBilledRate) elWcBilledRate.textContent = wcBilledRate != null ? formatPct(wcBilledRate) + ' of GWs'  : '—';

  setDS('s-suta-billed',      formatCurrency(to.suta_billed));
  setDS('s-suta-cost',        formatCurrency(to.suta_cost));
  setPnlDS('s-suta-profit-loss',  to.suta_profit_loss);
  setDS('s-fica-total',   formatCurrency(to.fica_total));
  setDS('s-futa-total',   formatCurrency(to.futa_total));

  setDS('s-tlm',             formatCurrency(oi.tlm));
  setDS('s-epli',            formatCurrency(oi.epli));
  setDS('s-reverse-wire',    formatCurrency(oi.wire_ach_fee));
  setDS('s-impl-fee',        formatCurrency(oi.implementation_fee));
  setDS('s-total-ancillary', formatCurrency(oi.total_ancillary));
  const elTotalPL = document.getElementById('s-total-profit-loss');
  if (elTotalPL) {
    elTotalPL.textContent = formatCurrency(oi.total_profit_loss);
    elTotalPL.style.color = (oi.total_profit_loss || 0) > 0 ? '#16a34a' : (oi.total_profit_loss || 0) < 0 ? '#dc2626' : '#1e3154';
  }

  setDS('s-consultant-upfront-pct', formatPct(co.consultant_upfront_rate));
  setDS('s-consultant-upfront',     formatCurrency(co.consultant_upfront));
  setDS('s-consultant-ongoing-pct', formatPct(co.consultant_ongoing_rate));
  setDS('s-consultant-ongoing',     formatCurrency(co.consultant_ongoing));
  setDS('s-broker-wc-pct',          formatPct(co.broker_wc_pct));
  setDS('s-broker-wc-amt',          formatCurrency(co.broker_wc_commission));
  setDS('s-broker-admin-pct',       formatPct(co.broker_admin_pct));
  setDS('s-broker-admin-amt',       formatCurrency(co.broker_admin_amt));
  setDS('s-admin-net-ongoing',      formatCurrency(co.admin_net_ongoing));
  setDS('s-admin-net-year1',        formatCurrency(co.admin_net_year1));
  const netOngoingPct    = ao.total_gws  > 0 ? co.admin_net_ongoing / ao.total_gws  : null;
  const netOngoingPerWse = ao.total_wses > 0 ? co.admin_net_ongoing / ao.total_wses : null;
  const elNetOngoingPct    = document.getElementById('s-admin-net-ongoing-pct');
  const elNetOngoingPerWse = document.getElementById('s-admin-net-ongoing-per-wse');
  if (elNetOngoingPct)    elNetOngoingPct.textContent    = netOngoingPct    != null ? formatPct(netOngoingPct)                  : '—';
  if (elNetOngoingPerWse) elNetOngoingPerWse.textContent = netOngoingPerWse != null ? formatCurrency(netOngoingPerWse) + '/WSE' : '—';
  const netYear1Pct    = ao.total_gws  > 0 ? co.admin_net_year1 / ao.total_gws  : null;
  const netYear1PerWse = ao.total_wses > 0 ? co.admin_net_year1 / ao.total_wses : null;
  const elNetYear1Pct    = document.getElementById('s-admin-net-year1-pct');
  const elNetYear1PerWse = document.getElementById('s-admin-net-year1-per-wse');
  if (elNetYear1Pct)    elNetYear1Pct.textContent    = netYear1Pct    != null ? formatPct(netYear1Pct)                  : '—';
  if (elNetYear1PerWse) elNetYear1PerWse.textContent = netYear1PerWse != null ? formatCurrency(netYear1PerWse) + '/WSE' : '—';
  setDS('s-cash-flow-after-comm', formatCurrency(co.cash_flow_after_comm));
  const cfPct    = ao.total_gws  > 0 ? co.cash_flow_after_comm / ao.total_gws  : null;
  const cfPerWse = ao.total_wses > 0 ? co.cash_flow_after_comm / ao.total_wses : null;
  const elCfPct    = document.getElementById('s-cash-flow-after-comm-pct');
  const elCfPerWse = document.getElementById('s-cash-flow-after-comm-per-wse');
  if (elCfPct)    elCfPct.textContent    = cfPct    != null ? formatPct(cfPct)                  : '—';
  if (elCfPerWse) elCfPerWse.textContent = cfPerWse != null ? formatCurrency(cfPerWse) + '/WSE' : '—';
  setDS('s-total-comm-pct',         formatPct(co.total_comm_rate));
  setDS('s-total-comm',             formatCurrency(co.total_comm));

  renderProposal(r);
  renderBillingAnalysis(r);
  renderLossAnalysis(ao.total_gws || 0, wo.wc_fixed_cost || 0, wo.wc_loss_fund || 0, wo.wc_billed || 0, co.broker_wc_commission || 0);

  const cfEl = ao.total_gws > 0 && _avgAnnualLoss != null;
  const cfElVal = cfEl
    ? ao.admin_margin + (wo.wc_billed - wo.wc_fixed_cost) + to.suta_profit_loss + oi.total_ancillary - co.total_comm - _avgAnnualLoss
    : null;
  setDS('s-cash-flow-est-losses', cfElVal != null ? formatCurrency(cfElVal) : '—');
  const cfElPct    = cfElVal != null && ao.total_gws  > 0 ? cfElVal / ao.total_gws  : null;
  const cfElPerWse = cfElVal != null && ao.total_wses > 0 ? cfElVal / ao.total_wses : null;
  const elCfElPct    = document.getElementById('s-cash-flow-est-losses-pct');
  const elCfElPerWse = document.getElementById('s-cash-flow-est-losses-per-wse');
  if (elCfElPct)    elCfElPct.textContent    = cfElPct    != null ? formatPct(cfElPct)                  : '—';
  if (elCfElPerWse) elCfElPerWse.textContent = cfElPerWse != null ? formatCurrency(cfElPerWse) + '/WSE' : '—';
}

/* ── Proposal ────────────────────────────────────────────────────────────── */
function renderProposal(r) {
  const ao = r.admin_overview || {};
  const wo = r.wc_overview    || {};
  const to = r.taxes_overview || {};

  const proposedMod = parseFloat(document.getElementById('pricing_proposed_mod')?.value) || 0;
  const wcLines     = collectWCLines().filter(l => l.wc_code || l.annual_gw > 0);
  const sutaLines   = collectSutaLines().filter(l => l.state);

  const ficaRate     = (systemConfig.ss_rate || 0) + (systemConfig.medicare_rate || 0);
  const futaRate     = systemConfig.futa_rate || 0;
  const adminMethod  = getIntVal('admin_method') || 1;
  const adminRateRaw = adminMethod === 1
    ? (getNumVal('admin_rate') || 0)
    : (getNumVal('admin_rate_' + adminMethod) || 0);
  const payPeriods   = getAdminPayPeriods();
  const adminHeaders = { 1: 'Admin', 2: 'Admin<br>per EE<br>per Check', 3: 'Admin<br>per EE<br>per Month' };
  const adminDisplay = adminMethod === 1
    ? (adminRateRaw ? adminRateRaw.toFixed(2) + '%' : '—')
    : (adminRateRaw ? '$' + adminRateRaw.toFixed(2) : '—');
  document.getElementById('proposal-admin-th').innerHTML = adminHeaders[adminMethod] || 'Admin';
  const sutaRateMap = {};
  sutaLines.forEach(l => { sutaRateMap[l.state] = l.billing_rate; });

  // WC table
  const wcBody = document.getElementById('proposal-wc-body');
  wcBody.innerHTML = '';
  let sumWses = 0, sumGws = 0;
  if (wcLines.length === 0) {
    wcBody.innerHTML = `<tr><td colspan="12" style="text-align:center;color:#a0aec0;">—</td></tr>`;
  } else {
    wcLines.forEach(line => {
      const wses     = Math.round((line.ftes || 0) + 0.75 * (line.ptes || 0));
      const gw       = line.annual_gw || 0;
      const rate     = line.manual_rate || 0;
      const desc     = line.wc_description || '—';
      const sutaRate = sutaRateMap[line.state];
      const isClientReporting = CLIENT_REPORTING_STATES.has(line.state);
      const sutaDisplay = isClientReporting
        ? 'PT'
        : (sutaRate != null ? (sutaRate * 100).toFixed(2) + '%' : '—');

      const sutaPct = (!isClientReporting && sutaRate != null) ? sutaRate * 100 : 0;
      let adminPct = 0;
      if (adminMethod === 1) {
        adminPct = adminRateRaw;
      } else if (gw > 0) {
        const adminCost = adminMethod === 2
          ? adminRateRaw * wses * payPeriods
          : adminRateRaw * wses * 12;
        adminPct = (adminCost / gw) * 100;
      }
      const costBeforePct = rate + (ficaRate * 100) + (futaRate * 100) + sutaPct + adminPct;
      const costAfterPct  = costBeforePct - (futaRate * 100) - sutaPct;
      const costBeforeDisplay = gw > 0 ? costBeforePct.toFixed(2) + '%' : '—';
      const costAfterDisplay  = gw > 0 ? costAfterPct.toFixed(2)  + '%' : '—';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${line.state || '—'}</td>
        <td>${line.wc_code || '—'}</td>
        <td title="${desc}">${desc}</td>
        <td style="text-align:right;">${wses || '—'}</td>
        <td style="text-align:right;">${gw ? formatDollars(gw) : '—'}</td>
        <td style="text-align:right;">${rate ? rate.toFixed(2) + '%' : '—'}</td>
        <td style="text-align:right;">${ficaRate ? (ficaRate * 100).toFixed(2) + '%' : '—'}</td>
        <td style="text-align:right;">${futaRate ? (futaRate * 100).toFixed(2) + '%' : '—'}</td>
        <td style="text-align:right;">${sutaDisplay}</td>
        <td style="text-align:right;">${adminDisplay}</td>
        <td style="text-align:right;">${costBeforeDisplay}</td>
        <td style="text-align:right;">${costAfterDisplay}</td>`;
      sumWses += wses;
      sumGws  += gw;
      wcBody.appendChild(tr);
    });
  }

  // WC totals footer
  document.getElementById('p-total-wses').textContent = sumWses || '—';
  document.getElementById('p-total-gws').textContent  = sumGws  ? formatDollars(sumGws)         : '—';
  document.getElementById('p-wc-billed').textContent  = wo.wc_billed   != null ? formatCurrency(wo.wc_billed)   : '—';
  document.getElementById('p-admin-total').textContent = ao.admin_margin != null ? formatCurrency(ao.admin_margin) : '—';

}

/* ── Annual Billing Analysis ─────────────────────────────────────────────── */
function renderBillingAnalysis(r) {
  const ao = r.admin_overview || {};

  const proposedMod     = parseFloat(document.getElementById('pricing_proposed_mod')?.value) || 0;
  const wcLines         = collectWCLines().filter(l => l.wc_code || l.annual_gw > 0);
  const adminMethod     = getIntVal('admin_method') || 1;
  const adminSuffix     = adminMethod === 1 ? '' : '_' + adminMethod;
  const curAdminRateRaw = getNumVal('current_admin_rate' + adminSuffix) || 0;
  const adminRateRaw    = getNumVal('admin_rate' + adminSuffix) || 0;
  const totalGWs        = ao.total_gws  || 0;
  const totalWses       = ao.total_wses || 0;
  const payPeriods      = getAdminPayPeriods();

  // Admin rate display strings (rate, not dollar total)
  const curAdminDisplay = adminMethod === 1
    ? (curAdminRateRaw ? curAdminRateRaw.toFixed(2) + '%' : '—')
    : (curAdminRateRaw ? '$' + curAdminRateRaw.toFixed(2) : '—');
  const vhrAdminDisplay = adminMethod === 1
    ? (adminRateRaw ? adminRateRaw.toFixed(2) + '%' : '—')
    : (adminRateRaw ? '$' + adminRateRaw.toFixed(2) : '—');

  // SUTA rate map from form inputs (for rate display per row)
  const sutaRateMap = {};
  collectSutaLines().filter(l => l.state).forEach(l => { sutaRateMap[l.state] = l; });

  function savCls(v) { return v > 0 ? 'positive' : v < 0 ? 'negative' : ''; }

  // ── WC rows ──
  const wcBody = document.getElementById('analysis-wc-body');
  wcBody.innerHTML = '';
  let sumGws = 0, sumWcSavings = 0, sumCurAdmin = 0, sumVhrAdmin = 0, sumSutaSavings = 0;
  if (wcLines.length === 0) {
    wcBody.innerHTML = `<tr><td colspan="13" style="text-align:center;color:#a0aec0;">—</td></tr>`;
  } else {
    wcLines.forEach(line => {
      const wses    = Math.round((line.ftes || 0) + 0.75 * (line.ptes || 0));
      const gw      = line.annual_gw || 0;
      const vhrRate = line.manual_rate || 0;
      const curRate = line.current_client_rate || 0;
      const savings = (curRate - vhrRate) * proposedMod * gw / 100;
      sumGws       += gw;
      sumWcSavings += savings;

      // Admin: per-row savings dollar amount; display shows rate
      let curAdminRow = 0, vhrAdminRow = 0;
      if (adminMethod === 1) {
        curAdminRow = (curAdminRateRaw / 100) * gw;
        vhrAdminRow = (adminRateRaw    / 100) * gw;
      } else if (adminMethod === 2) {
        curAdminRow = curAdminRateRaw * wses * payPeriods;
        vhrAdminRow = adminRateRaw    * wses * payPeriods;
      } else if (adminMethod === 3) {
        curAdminRow = curAdminRateRaw * wses * 12;
        vhrAdminRow = adminRateRaw    * wses * 12;
      }
      const adminSavRow = curAdminRow - vhrAdminRow;
      sumCurAdmin += curAdminRow;
      sumVhrAdmin += vhrAdminRow;

      // SUTA: show rate for every matching row; savings = rate diff × gw
      const sr = sutaRateMap[line.state];
      let curSutaDisplay = '—', vhrSutaDisplay = '—', sutaSavTxt = '—', sutaSavCls = '';
      if (sr) {
        const curSutaRate = sr.current_client_rate || 0;
        const vhrSutaRate = sr.billing_rate        || 0;
        const sutaSavAmt  = (curSutaRate - vhrSutaRate) * gw;
        curSutaDisplay = curSutaRate ? (curSutaRate * 100).toFixed(2) + '%' : '—';
        vhrSutaDisplay = vhrSutaRate ? (vhrSutaRate * 100).toFixed(2) + '%' : '—';
        sutaSavTxt     = formatDollars(sutaSavAmt);
        sutaSavCls     = savCls(sutaSavAmt);
        sumSutaSavings += sutaSavAmt;
      }

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${line.state || '—'}</td>
        <td>${line.wc_code || '—'}</td>
        <td style="text-align:right;">${wses || '—'}</td>
        <td style="text-align:right;">${gw ? formatDollars(gw) : '—'}</td>
        <td style="text-align:right;">${curRate ? curRate.toFixed(2) + '%' : '—'}</td>
        <td style="text-align:right;">${vhrRate ? vhrRate.toFixed(2) + '%' : '—'}</td>
        <td style="text-align:right;" class="${savCls(savings)}">${gw ? formatDollars(savings) : '—'}</td>
        <td style="text-align:right;">${curAdminDisplay}</td>
        <td style="text-align:right;">${vhrAdminDisplay}</td>
        <td style="text-align:right;" class="${savCls(adminSavRow)}">${gw ? formatDollars(adminSavRow) : '—'}</td>
        <td style="text-align:right;">${curSutaDisplay}</td>
        <td style="text-align:right;">${vhrSutaDisplay}</td>
        <td style="text-align:right;" class="${sutaSavCls}">${sutaSavTxt}</td>`;
      wcBody.appendChild(tr);
    });
  }

  // ── Admin and SUTA totals (accumulated from per-row) ──
  const adminSavings = sumCurAdmin - sumVhrAdmin;

  // ── Totals row ──
  const hasData = sumGws > 0;

  const wcSavEl = document.getElementById('a-wc-savings');
  wcSavEl.textContent = sumGws ? formatDollars(sumWcSavings) : '—';
  wcSavEl.className   = sumGws ? savCls(sumWcSavings) : '';

  const adminSavEl = document.getElementById('a-admin-savings');
  adminSavEl.textContent = sumGws ? formatDollars(adminSavings) : '—';
  adminSavEl.className   = sumGws ? savCls(adminSavings) : '';

  const sutaSavEl = document.getElementById('a-suta-savings');
  sutaSavEl.textContent = sumGws ? formatDollars(sumSutaSavings) : '—';
  sutaSavEl.className   = sumGws ? savCls(sumSutaSavings) : '';

  // ── Grand total ──
  const grandSavings = sumWcSavings + adminSavings + sumSutaSavings;
  const grandEl = document.getElementById('a-grand-total-savings');
  grandEl.textContent = hasData ? formatDollars(grandSavings) : '—';
  grandEl.className   = hasData ? savCls(grandSavings) : '';
}

/* ── Loss Analysis ───────────────────────────────────────────────────────── */
function renderLossAnalysis(totalGws, wcFixedCost, wcLossFund, wcBilled, brokerWcComm) {
  const allLosses = collectWCLosses().filter(
    l => l.total_losses_incurred > 0 || l.num_claims > 0 || l.months_in_policy > 0
  );
  const losses = allLosses;

  const blank = ['la-total-losses','la-total-claims','la-total-months','la-open-claims',
                 'la-total-losses-detail','la-total-retention','la-net-losses','la-avg-annual','la-proposed-mod'];

  if (losses.length === 0) {
    blank.forEach(id => { document.getElementById(id).textContent = '—'; });
    renderBillingCommissions(0, wcFixedCost || 0, wcLossFund || 0, wcBilled || 0, brokerWcComm || 0);
    return;
  }

  let sumLosses = 0, sumClaims = 0, sumMonths = 0, sumOpen = 0;
  losses.forEach(l => {
    sumLosses += l.total_losses_incurred;
    sumClaims += l.num_claims;
    sumMonths += l.months_in_policy;
    sumOpen   += l.open_claims;
  });

  // Totals summary row
  document.getElementById('la-total-losses').textContent = formatCurrency(sumLosses);
  document.getElementById('la-total-claims').textContent = sumClaims;
  document.getElementById('la-total-months').textContent = sumMonths;
  document.getElementById('la-open-claims').textContent  = sumOpen;

  // Derived metrics
  const sharedClaimFee = parseFloat(document.getElementById('shared_claim_fee')?.value) || 0;
  const totalRetention = sumClaims * (sharedClaimFee / 2);
  const netLosses      = sumLosses - totalRetention;
  const avgAnnual      = sumMonths > 0 ? (netLosses / sumMonths) * 12 : null;
  _avgAnnualLoss = avgAnnual;
  const proposedMod    = parseFloat(document.getElementById('pricing_proposed_mod')?.value);

  document.getElementById('la-total-losses-detail').textContent = formatCurrency(sumLosses);
  document.getElementById('la-total-retention').textContent     = formatCurrency(totalRetention);
  document.getElementById('la-net-losses').textContent          = formatCurrency(netLosses);
  document.getElementById('la-avg-annual').textContent          = avgAnnual != null ? formatCurrency(avgAnnual) : '—';
  document.getElementById('la-proposed-mod').textContent        = isNaN(proposedMod) ? '—' : proposedMod.toFixed(2);

  renderBillingCommissions(netLosses, wcFixedCost || 0, wcLossFund || 0, wcBilled || 0, brokerWcComm || 0);
}

/* ── Billing & Commissions ───────────────────────────────────────────────── */
function renderBillingCommissions(netLosses, wcFixedCost, wcLossFund, wcBilled, brokerWcComm) {
  const netBilling  = wcBilled - brokerWcComm;
  const leftover    = netBilling - wcFixedCost;
  const leftoverPct = netBilling > 0 ? (leftover / netBilling * 100) : null;

  document.getElementById('bc-my-billing').textContent   = formatCurrency(wcBilled);
  document.getElementById('bc-commissions').textContent  = formatCurrency(brokerWcComm);
  document.getElementById('bc-net-billing').textContent  = formatCurrency(netBilling);
  document.getElementById('bc-wc-fixed').textContent     = formatCurrency(wcFixedCost);
  document.getElementById('bc-leftover-amt').textContent = formatCurrency(leftover);
  document.getElementById('bc-leftover-pct').textContent = leftoverPct != null
    ? `(${leftoverPct.toFixed(1)}% remaining)`
    : '';
  document.getElementById('bc-net-billing').textContent = formatCurrency(netBilling);
}

/* ── Populate form from API ──────────────────────────────────────────────── */
function setSelectBoolByName(name, value) {
  if (value == null) return;
  const el = document.querySelector(`select[name="${name}"]`);
  if (!el) return;
  el.value = value === true ? 'true' : 'false';
  // Fire change event for togglers
  el.dispatchEvent(new Event('change'));
}

function populateForm(client) {
  document.getElementById('page-title').textContent = client.legal_name || 'New Client';
  document.getElementById('page-sub').textContent = 'Consultant: ' + (client.consultant_name || '—');
  document.title = 'VestedHR — ' + (client.legal_name || 'New Client');

  // General
  ['consultant_name','consultant_name_split','date','legal_name','dba',
   'referral_partner_business','referral_partner_name',
   'main_address','city','state','zip','county',
   'fein','website','org_structure','naics','sic','years_in_business','num_locations',
   'main_phone',
   'owner_name','owner_phone','owner_email','owner_cell',
   'contact_name','contact_phone','contact_cell','contact_email',
   'description_of_operations'].forEach(f => setField(f, client[f]));

  // States operating (pill picker)
  if (client.states_operating) {
    try {
      const states = JSON.parse(client.states_operating);
      document.querySelectorAll('.state-pill').forEach(pill => {
        if (states.includes(pill.dataset.abbr)) pill.classList.add('selected');
      });
      const count = states.length;
      document.getElementById('state-count').innerHTML =
        `<strong>${count}</strong> state${count !== 1 ? 's' : ''} selected`;
    } catch(e) {}
  }

  // Locations
  if (client.locations) {
    try {
      const locs = JSON.parse(client.locations);
      locs.forEach(loc => addLocationRow(loc));
    } catch(e) {}
  }

  // Compliance
  [
    ['eeoc_violations', 'eeoc_explanation'],
    ['active_claims',   'active_claims_explanation'],
    ['cobra_continuation', 'cobra_explanation'],
    ['past_layoffs',    'past_layoffs_explanation'],
    ['future_layoffs',  'future_layoffs_explanation'],
    ['leave_of_absence','leave_explanation'],
  ].forEach(([field, explField]) => {
    setSelectBoolByName(field, client[field]);
    const explEl = document.querySelector(`[name="${explField}"]`);
    if (explEl && client[explField]) {
      explEl.value = client[explField];
      if (client[field] === true) explEl.style.display = 'block';
    }
  });

  // Medical
  ['medical_carve_out','enrolled_over_50','enrolled_under_10','level_funded_plan',
   'currently_has_health_insurance','census_available','cobra_expected'].forEach(f => {
    setSelectBoolByName(f, client[f]);
  });
  onMedCarveOut(document.querySelector('[name="medical_carve_out"]'));
  toggleMedNote(document.querySelector('[name="enrolled_over_50"]'),    'true',  'med-note-over50');
  toggleMedNote(document.querySelector('[name="enrolled_under_10"]'),   'true',  'med-note-under10');
  toggleMedNote(document.querySelector('[name="level_funded_plan"]'),   'true',  'med-note-levelfunded');
  toggleMedNote(document.querySelector('[name="currently_has_health_insurance"]'), 'true', 'med-note-hasinsurance');
  toggleMedNote(document.querySelector('[name="census_available"]'),    'false', 'med-note-nocensus');

  // Ancillary
  ['offers_ancillary_benefits','wants_ancillary_benefits'].forEach(f => {
    setSelectBoolByName(f, client[f]);
  });
  setField('current_contribution_strategy', client.current_contribution_strategy);
  setField('new_contribution_strategy',     client.new_contribution_strategy);

  // Payroll
  ['payroll_frequency','pay_cycle_start','pay_cycle_end','pay_date',
   'method_of_payment','requested_payroll_delivery','effective_date'].forEach(f => setField(f, client[f]));

  // WC carve-out
  if (client.wc_carve_out != null) {
    const wcSel = document.getElementById('wc_carve_out_sel');
    wcSel.value = client.wc_carve_out ? 'true' : 'false';
    toggleWcCarveout(wcSel);
  }
  setField('proposed_mod',        client.proposed_mod);
  setField('pricing_proposed_mod',client.proposed_mod);
  setField('shared_claim_fee',    client.shared_claim_fee);
  setField('min_wc_fee_per_week', client.min_wc_fee_per_week);

  if (client.new_company != null) {
    const sel = document.getElementById('new_company_sel');
    sel.value = client.new_company ? 'true' : 'false';
    if (client.new_company) document.getElementById('note-new-co').style.display = 'block';
  }
  if (client.gaps_in_coverage != null) {
    const sel = document.getElementById('gaps_in_coverage_sel');
    sel.value = client.gaps_in_coverage ? 'true' : 'false';
    if (client.gaps_in_coverage) document.getElementById('note-gaps').style.display = 'block';
  }

  // WC Lines
  document.getElementById('wc-codes-body').innerHTML = '';
  if (client.wc_lines && client.wc_lines.length) {
    client.wc_lines.forEach(l => addWCCodeRow(l));
  } else {
    addWCCodeRow();
  }

  // SUTA Lines
  if (client.suta_lines && client.suta_lines.length) {
    client.suta_lines.forEach(l => addSutaRow(l));
  }

  // WC Losses
  if (client.wc_losses && client.wc_losses.length) {
    document.getElementById('wc-losses-body').innerHTML = '';
    client.wc_losses.forEach(loss => addWCLossRow(loss));
  }

  // Pricing — populate all per-method rate fields then select active method
  setField('admin_rate',          ((client.admin_rate   || 0) * 100).toFixed(4));
  setField('admin_rate_2',        client.admin_rate_2   || 0);
  setField('admin_rate_3',        client.admin_rate_3   || 0);
  setField('current_admin_rate',  client.current_admin_rate   || 0);
  setField('current_admin_rate_2', client.current_admin_rate_2 || 0);
  setField('current_admin_rate_3', client.current_admin_rate_3 || 0);
  selectAdminMethod(client.admin_method || 1);

  setField('implementation_fee',       client.implementation_fee);
  setField('epli_rate',                client.epli_rate);
  setField('broker_wc_commission_pct',  ((client.broker_wc_commission_pct || 0) * 100).toFixed(4));
  setField('internal_commission_pct',   ((client.internal_commission_pct || 0) * 100).toFixed(4));
  setField('external_commission_pct',   ((client.external_commission_pct || 0) * 100).toFixed(4));
  setField('futa_turnover_rate', client.futa_turnover_rate);

  scheduleCalculate();
}

/* ── Init ────────────────────────────────────────────────────────────────── */
async function init() {
  await loadSutaMinRates();
  try { systemConfig = await apiGet('/config'); } catch (e) { /* non-fatal */ }

  // ── Wire up panel DOM listeners (panels now loaded) ─────────────────── //

  // State picker
  document.getElementById('state-picker').addEventListener('click', function(e) {
    const pill = e.target.closest('.state-pill');
    if (!pill) return;
    pill.classList.toggle('selected');
    const count = document.querySelectorAll('.state-pill.selected').length;
    document.getElementById('state-count').innerHTML =
      `<strong>${count}</strong> state${count !== 1 ? 's' : ''} selected`;
    scheduleAutoSave();
  });

  // Location add button
  document.getElementById('btn-add-location').addEventListener('click', () => addLocationRow());

  // WC Loss remove mode
  wcLossRM = makeRemoveMode('wc-losses-body', 'btn-add-wc-loss', 'btn-remove-wc-loss', '+ Add Row', scheduleAutoSave);
  document.getElementById('btn-remove-wc-loss').addEventListener('click', () => wcLossRM.toggle());
  document.getElementById('btn-add-wc-loss').addEventListener('click', () => {
    wcLossRM.isActive() ? wcLossRM.cancel() : addWCLossRow();
  });
  addWCLossRow();

  // WC Codes remove mode
  wcCodesRM = makeRemoveMode('wc-codes-body', 'btn-add-wc-code', 'btn-remove-wc-rows', '+ Add Row', () => { updateWCTotals(); scheduleCalculate(); scheduleAutoSave(); });
  document.getElementById('btn-add-wc-code').addEventListener('click', () => {
    wcCodesRM.isActive() ? wcCodesRM.cancel() : addWCCodeRow();
  });
  document.getElementById('btn-remove-wc-rows').addEventListener('click', () => wcCodesRM.toggle());

  // SUTA remove mode
  sutaRM = makeRemoveMode('suta-body', 'btn-add-suta', 'btn-remove-suta', '+ Add State', () => { scheduleCalculate(); scheduleAutoSave(); });
  document.getElementById('btn-add-suta').addEventListener('click', () => {
    sutaRM.isActive() ? sutaRM.cancel() : addSutaRow();
  });
  document.getElementById('btn-remove-suta').addEventListener('click', () => sutaRM.toggle());

  // Pricing mod sync
  const pricingMod = document.getElementById('pricing_proposed_mod');
  const wcMod = document.getElementById('proposed_mod');
  pricingMod.addEventListener('input', () => {
    wcMod.value = pricingMod.value;
    scheduleCalculate();
  });
  wcMod.addEventListener('input', () => {
    pricingMod.value = wcMod.value;
  });

  // Pricing inputs → trigger recalculate
  ['admin_method', 'admin_rate', 'admin_rate_2', 'admin_rate_3',
   'current_admin_rate', 'current_admin_rate_2', 'current_admin_rate_3',
   'pricing_proposed_mod', 'implementation_fee',
   'epli_rate', 'broker_wc_commission_pct', 'internal_commission_pct',
   'external_commission_pct', 'futa_turnover_rate'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', scheduleCalculate);
      el.addEventListener('input', scheduleCalculate);
    }
  });

  // Admin method initial selection
  selectAdminMethod(1);

  // Save Quote button
  document.getElementById('btn-save').addEventListener('click', async () => {
    if (!clientId) { showToast('No client ID — open via dashboard', 'error'); return; }

    const payload = collectClientPayload();
    const saveBody = {
      ...payload.client,
      wc_lines:   payload.wc_lines,
      suta_lines: payload.suta_lines,
      wc_losses:  collectWCLosses(),
    };

    const name = saveBody.legal_name;
    if (name) {
      document.getElementById('page-title').textContent = name;
      document.title = 'VestedHR — ' + name;
      document.getElementById('page-sub').textContent =
        'Consultant: ' + (saveBody.consultant_name || '—');
    }

    try {
      await apiPut('/clients/' + clientId, saveBody);
      showToast('Quote saved successfully', 'success');
    } catch (e) {
      showToast('Save failed: ' + e.message, 'error');
    }
  });

  // ── Load client data ─────────────────────────────────────────────────── //
  if (clientId) {
    try {
      const client = await apiGet('/clients/' + clientId);
      isPopulating = true;
      populateForm(client);
      isPopulating = false;
      restoreCardLockStates(client.card_lock_states);
    } catch (e) {
      isPopulating = false;
      showToast('Failed to load client: ' + e.message, 'error');
      addWCCodeRow();
      document.querySelectorAll('.card[data-card-id]').forEach(c => applyCardLock(c, false));
    }
  } else {
    addWCCodeRow();
    document.querySelectorAll('.card[data-card-id]').forEach(c => applyCardLock(c, false));
  }
}

loadPanels().then(() => init());
