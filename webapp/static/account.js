/* ============================================================================
   Account, plans and paywall (hosted mode and the static free preview).

   The server decides access (entitlements.py); this file only shows it:
     - the plan badge and account menu in the top bar (sign out lives there)
     - lock badges on module rows, cards and DSA problems the plan does not include
     - the paywall card drawn where a locked page would have been, and the plans
       dialog that compares Free, Base, Pro and Pro Max
   In the local app (`make app`) bootstrap has no `account`, and nothing here runs.
   ========================================================================= */
'use strict';

window.EGAccount = (function () {
  let acct = null;
  const H = s => String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LOCK = '<svg class="eg-lock-ico" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>';
  const tierName = t => (acct && acct.tierNames && acct.tierNames[t]) || t;
  const rank = t => (acct ? acct.tiers.indexOf(t) : 0);
  const anonymous = () => !!(acct && acct.anonymous);

  function upgradeHref() {
    const u = window.EG_UPGRADE_URL || '';
    return /^https:\/\//.test(u) ? u : '';
  }

  /* ------------------------------------------------------------ badges -- */
  const lockBadge = tier => acct
    ? `<span class="eg-lock" title="Part of the ${H(tierName(tier))} plan">${LOCK}<span>${H(tierName(tier))}</span></span>`
    : '';

  function moduleBadge(key) {
    const m = acct && acct.modules && acct.modules[key];
    return m && !m.full ? lockBadge(m.requires) : '';
  }

  /* ----------------------------------------------------------- plans UI -- */
  function planCards(highlight) {
    return `<div class="eg-plans">${acct.plans.map(p => {
      const current = p.id === acct.tier;
      const hi = p.id === highlight;
      return `<div class="eg-plan${current ? ' is-current' : ''}${hi ? ' is-hi' : ''}">
        <div class="eg-plan-head"><h3>${H(p.name)}</h3>
          ${current ? '<span class="eg-chip">Your plan</span>' : hi ? '<span class="eg-chip eg-chip-hi">Unlocks this</span>' : ''}</div>
        <p class="eg-plan-sum">${H(p.summary)}</p>
        <ul>${p.includes.map(i => `<li>${H(i)}</li>`).join('')}</ul>
        <p class="eg-plan-dev">${p.devices} signed-in device${p.devices > 1 ? 's' : ''}</p>
      </div>`;
    }).join('')}</div>`;
  }

  function upgradeAction(required) {
    if (anonymous()) {
      return upgradeHref()
        ? `<a class="btn btn-primary" href="${H(upgradeHref())}" rel="noopener">Get ${H(tierName(required))}</a>`
        : '<p class="eg-note">This free preview has no accounts. Paid plans are on the hosted guide.</p>';
    }
    return upgradeHref()
      ? `<a class="btn btn-primary" href="${H(upgradeHref())}?plan=${encodeURIComponent(required)}" rel="noopener">Upgrade to ${H(tierName(required))}</a>`
      : `<p class="eg-note">To upgrade, ask the guide's administrator to move <b>${H(acct.email)}</b> to ${H(tierName(required))}. It applies on your next page load.</p>`;
  }

  function paywallHtml(info) {
    if (!acct) return '';
    const req = info.requires || 'pro';
    return `<div class="eg-paywall" role="region" aria-label="Upgrade required">
      <div class="eg-paywall-ico">${LOCK}</div>
      <h2>Part of the ${H(tierName(req))} plan</h2>
      <p>${H(info.message || '')}</p>
      <div class="eg-paywall-actions">
        ${upgradeAction(req)}
        <button class="btn btn-ghost" type="button" data-eg-plans="${H(req)}">Compare plans</button>
      </div>
    </div>`;
  }

  let dialog = null, returnFocus = null;
  function closeDialog() {
    if (!dialog) return;
    dialog.remove();
    dialog = null;
    returnFocus?.focus?.();
  }
  function openPlans(highlight, info) {
    if (!acct) return;
    closeDialog();
    returnFocus = document.activeElement;
    dialog = document.createElement('div');
    dialog.className = 'eg-dialog';
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-labelledby', 'egDialogTitle');
    dialog.innerHTML = `<div class="eg-dialog-scrim" data-eg-close></div>
      <div class="eg-dialog-box">
        <button class="icon-btn eg-dialog-x" type="button" data-eg-close aria-label="Close">
          <svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
        <h2 id="egDialogTitle">${info ? `This page is part of ${H(tierName(highlight))}` : 'Plans'}</h2>
        <p class="eg-dialog-sub">${info ? H(info.message) : `You are on <b>${H(tierName(acct.tier))}</b>${acct.tierExpiresAt ? `, renewing or ending ${new Date(acct.tierExpiresAt * 1000).toLocaleDateString()}` : ''}.`}</p>
        ${planCards(highlight)}
        ${highlight && rank(highlight) > rank(acct.tier) ? `<div class="eg-dialog-actions">${upgradeAction(highlight)}</div>` : ''}
      </div>`;
    document.body.appendChild(dialog);
    dialog.querySelector('.eg-dialog-x').focus();
  }
  const paywall = info => openPlans(info.requires, info);

  /* ------------------------------------------------------- account menu -- */
  function mountMenu() {
    const right = document.querySelector('.topbar-right');
    if (!right || document.getElementById('egAccount')) return;
    const wrap = document.createElement('div');
    wrap.className = 'eg-account';
    wrap.id = 'egAccount';
    const initial = anonymous() ? '?' : (acct.email || '?')[0].toUpperCase();
    wrap.innerHTML = `
      <button class="eg-account-btn" type="button" aria-haspopup="true" aria-expanded="false"
              title="${anonymous() ? 'Free preview' : H(acct.email)}">
        <span class="eg-avatar" aria-hidden="true">${H(initial)}</span>
        <span class="eg-tier t-${H(acct.tier)}">${anonymous() ? 'Preview' : H(acct.tierName)}</span>
      </button>
      <div class="eg-menu" role="menu" hidden>
        ${anonymous() ? '<div class="eg-menu-who">Free preview<small>No account: progress stays in this browser</small></div>'
          : `<div class="eg-menu-who">${H(acct.email)}<small>${H(acct.tierName)} plan${acct.tierExpiresAt ? ` · until ${new Date(acct.tierExpiresAt * 1000).toLocaleDateString()}` : ''}</small></div>`}
        <button type="button" role="menuitem" data-eg-plans="">Plans &amp; upgrade</button>
        ${anonymous() ? '' : '<button type="button" role="menuitem" data-eg-signout>Sign out</button>'}
      </div>`;
    right.appendChild(wrap);
    const btn = wrap.querySelector('.eg-account-btn'), menu = wrap.querySelector('.eg-menu');
    const setOpen = open => { menu.hidden = !open; btn.setAttribute('aria-expanded', String(open)); };
    btn.addEventListener('click', e => { e.stopPropagation(); setOpen(menu.hidden); });
    document.addEventListener('click', e => { if (!wrap.contains(e.target)) setOpen(false); });
    wrap.addEventListener('keydown', e => { if (e.key === 'Escape') { setOpen(false); btn.focus(); } });
  }

  async function signOut() {
    try {
      await fetch('./api/auth/logout', { method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' }, body: '{}' });
    } finally {
      try { localStorage.removeItem('eg-progress-v1'); } catch (e) { /* private mode */ }
      location.replace('./login.html');
    }
  }

  /* One delegated listener for every plans / sign-out control the module draws. */
  document.addEventListener('click', e => {
    const plans = e.target.closest('[data-eg-plans]');
    if (plans) { e.preventDefault(); document.querySelector('#egAccount .eg-menu')?.setAttribute('hidden', '');
      openPlans(plans.dataset.egPlans || null); return; }
    if (e.target.closest('[data-eg-close]')) { closeDialog(); return; }
    if (e.target.closest('[data-eg-signout]')) signOut();
  });
  document.addEventListener('keydown', e => { if (dialog && e.key === 'Escape') { e.stopPropagation(); closeDialog(); } }, true);

  function init(account) {
    if (!account) return;              // local app: everything open, no account
    acct = account;
    document.documentElement.dataset.egTier = acct.tier;
    mountMenu();
    if (!anonymous() && window.EGProtect) EGProtect.watermark(acct.email);
    if (typeof renderSidebar === 'function') renderSidebar();
  }

  return { init, lockBadge, moduleBadge, paywall, paywallHtml, openPlans, get account() { return acct; } };
})();
