/* Sign-in page for the hosted guide: email → 6-digit code → session cookie.
   The server (auth.py) owns every rule: code lifetime, attempts, rate limits. */
'use strict';
(function () {
  const $ = id => document.getElementById(id);
  const stepEmail = $('stepEmail'), stepCode = $('stepCode');
  let email = '', resendTimer = null;

  const next = () => {
    // ?next= from the app's 401 handler, or the hash the server's redirect carried over
    const n = new URLSearchParams(location.search).get('next') || location.hash || '';
    return /^#\/[\w\-/%.?=&]*$/.test(n) ? './' + n : './';      // only in-app hash routes
  };

  const show = (el, msg, kind = 'err') => {
    el.textContent = msg || '';
    el.dataset.kind = kind;
    el.hidden = !msg;
  };

  async function post(path, body) {
    const r = await fetch(path, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
    let data = {};
    try { data = await r.json(); } catch (e) { /* empty */ }
    return { ok: r.ok, status: r.status, data };
  }

  function cooldown(seconds) {
    const b = $('resendBtn');
    clearInterval(resendTimer);
    let left = seconds;
    const tick = () => {
      b.disabled = left > 0;
      b.textContent = left > 0 ? `Send a new code (${left}s)` : 'Send a new code';
      left -= 1;
      if (left < -1) clearInterval(resendTimer);
    };
    tick();
    resendTimer = setInterval(tick, 1000);
  }

  async function sendCode(msgEl, btn) {
    btn.disabled = true;
    show(msgEl, '');
    try {
      const r = await post('./api/auth/request-otp', { email });
      if (!r.ok) {
        show(msgEl, r.data.message || 'Could not send a code. Try again.');
        if (r.data.error === 'cooldown') cooldown(r.data.retryAfter || 60);
        return false;
      }
      cooldown(r.data.resendIn || 60);
      return true;
    } catch (e) {
      show(msgEl, 'The server did not answer. Check your connection.');
      return false;
    } finally {
      btn.disabled = false;
    }
  }

  stepEmail.addEventListener('submit', async e => {
    e.preventDefault();
    email = $('email').value.trim().toLowerCase();
    if (!$('email').checkValidity() || !email) {
      show($('emailMsg'), 'Enter a valid email address.');
      return;
    }
    const sent = await sendCode($('emailMsg'), $('sendBtn'));
    if (sent || /just sent/.test($('emailMsg').textContent)) {
      $('sentTo').textContent = email;
      show($('codeMsg'), sent ? '' : $('emailMsg').textContent, 'info');
      stepEmail.hidden = true;
      stepCode.hidden = false;
      $('code').value = '';
      $('code').focus();
    }
  });

  $('code').addEventListener('input', () => {
    $('code').value = $('code').value.replace(/\D/g, '').slice(0, 6);
    if ($('code').value.length === 6) stepCode.requestSubmit();
  });

  stepCode.addEventListener('submit', async e => {
    e.preventDefault();
    const code = $('code').value;
    if (!/^\d{6}$/.test(code)) { show($('codeMsg'), 'The code is 6 digits.'); return; }
    $('verifyBtn').disabled = true;
    show($('codeMsg'), '');
    try {
      const r = await post('./api/auth/verify-otp', { email, code });
      if (r.ok) { location.replace(next()); return; }
      show($('codeMsg'), r.data.message || 'That code did not work.');
      $('code').select();
    } catch (err) {
      show($('codeMsg'), 'The server did not answer. Check your connection.');
    } finally {
      $('verifyBtn').disabled = false;
    }
  });

  $('resendBtn').addEventListener('click', async () => {
    if (await sendCode($('codeMsg'), $('resendBtn'))) show($('codeMsg'), 'A new code is on its way.', 'info');
  });

  $('changeBtn').addEventListener('click', () => {
    stepCode.hidden = true;
    stepEmail.hidden = false;
    show($('emailMsg'), '');
    $('email').focus();
  });
})();
