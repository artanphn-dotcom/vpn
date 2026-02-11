// Multi-step wizard with vendor-specific fields and preview/download helpers
(function() {
  const steps = Array.from(document.querySelectorAll('.step'));
  const vendorCard = document.getElementById('vendor-specific-card');
  const form = document.getElementById('wizard-form');
  let current = 0;

  function show(i) {
    steps.forEach((s, idx) => s.classList.toggle('active', idx === i));
    current = i;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function next() { if (current < steps.length - 1) show(current + 1); }
  function prev() { if (current > 0) show(current - 1); }

  function updateVendorCard() {
    const v = document.querySelector('input[name="vendor"]:checked').value;
    if (!vendorCard) return;
    vendorCard.style.display = (v === 'paloalto' || v === 'cisco') ? 'block' : 'none';
  }

  function formPost(path, fd) {
    return fetch(path, { method: 'POST', body: fd });
  }

  function submitPreview() {
    const fd = new FormData(form);
    fd.set('include_psk', '0');
    formPost('/generate', fd).then(r => r.text()).then(html => {
      const w = window.open('about:blank', '_blank');
      w.document.write(html);
      w.document.close();
    });
  }

  function submitDownload(includePsk) {
    const fd = new FormData(form);
    fd.set('include_psk', includePsk ? '1' : '0');
    fetch('/download', { method: 'POST', body: fd }).then(r => {
      if (!r.ok) return r.text().then(t => alert('Download failed:\n' + t));
      return r.blob();
    }).then(blob => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'vpn-config.txt';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });
  }

  function isIPv4(addr) {
    const re = /^(25[0-5]|2[0-4]\d|[01]?\d\d?)(\.(25[0-5]|2[0-4]\d|[01]?\d\d?)){3}$/;
    return re.test(addr);
  }
  function isCIDR(cidr) {
    try {
      const parts = cidr.split('/');
      if (parts.length !== 2) return false;
      return isIPv4(parts[0]) && Number(parts[1]) >= 0 && Number(parts[1]) <= 32;
    } catch (e) { return false; }
  }

  function validateCurrentStep() {
    // clear previous errors
    document.querySelectorAll('.error-text').forEach(e => e.remove());
    document.querySelectorAll('.input-error').forEach(i => i.classList.remove('input-error'));

    let valid = true;
    if (current === 1) { // general step
      const gw = document.querySelector('input[name="remote_gw"]').value.trim();
      if (!isIPv4(gw)) {
        const el = document.querySelector('input[name="remote_gw"]');
        el.classList.add('input-error');
        el.insertAdjacentHTML('afterend', '<div class="error-text">Enter a valid IPv4 address</div>');
        valid = false;
      }
    }
    if (current === 2) { // phase2 step
      const l = document.querySelector('input[name="local_subnet"]').value.trim();
      const r = document.querySelector('input[name="remote_subnet"]').value.trim();
      if (!isCIDR(l)) {
        const el = document.querySelector('input[name="local_subnet"]');
        el.classList.add('input-error');
        el.insertAdjacentHTML('afterend', '<div class="error-text">Enter local subnet in CIDR (e.g. 10.0.0.0/24)</div>');
        valid = false;
      }
      if (!isCIDR(r)) {
        const el = document.querySelector('input[name="remote_subnet"]');
        el.classList.add('input-error');
        el.insertAdjacentHTML('afterend', '<div class="error-text">Enter remote subnet in CIDR (e.g. 192.168.1.0/24)</div>');
        valid = false;
      }
    }
    if (current === 3) { // vendor specific
      const v = document.querySelector('input[name="vendor"]:checked').value;
      if ((v === 'paloalto' || v === 'cisco')) {
        const tl = document.querySelector('input[name="tunnel_local_ip"]').value.trim();
        const tr = document.querySelector('input[name="tunnel_remote_ip"]').value.trim();
        if (!isCIDR(tl)) {
          const el = document.querySelector('input[name="tunnel_local_ip"]');
          el.classList.add('input-error');
          el.insertAdjacentHTML('afterend', '<div class="error-text">Enter tunnel local IP in CIDR</div>');
          valid = false;
        }
        if (!isIPv4(tr)) {
          const el = document.querySelector('input[name="tunnel_remote_ip"]');
          el.classList.add('input-error');
          el.insertAdjacentHTML('afterend', '<div class="error-text">Enter tunnel remote IP</div>');
          valid = false;
        }
      }
    }

    return valid;
  }

  // wire validation into navigation
  window.nextStep = function() { if (validateCurrentStep()) next(); }
  window.submitPreview = function() { if (validateCurrentStep()) submitPreviewOrig(); }
  window.submitDownload = function(includePsk) { if (validateCurrentStep()) submitDownloadOrig(includePsk); }

  // keep original functions under new names
  const submitPreviewOrig = window.submitPreview;
  const submitDownloadOrig = window.submitDownload;

  window.nextStep = next;
  window.prevStep = prev;
  window.submitPreview = submitPreview;
  window.submitDownload = submitDownload;

  window.setEnvironment = function(env) {
    document.getElementById('environment').value = env;
    document.querySelectorAll('.env-btn').forEach(b => b.classList.remove('active'));
    const btn = Array.from(document.querySelectorAll('.env-btn')).find(b => b.textContent.toLowerCase() === env);
    if (btn) btn.classList.add('active');
  }

  window.addEventListener('load', () => {
    show(0);
    updateVendorCard();
    document.querySelectorAll('input[name="vendor"]').forEach(el => el.addEventListener('change', updateVendorCard));
  });

  // Presets loader
  function loadPresets() {
    fetch('/static/presets.json').then(r => r.json()).then(json => {
      window._presets = json;
      const sel = document.getElementById('preset-select');
      if (!sel) return;
      // populate options grouped by vendor
      Object.keys(json).forEach(vendor => {
        const group = document.createElement('optgroup');
        group.label = vendor;
        Object.keys(json[vendor]).forEach(name => {
          const opt = document.createElement('option');
          opt.value = vendor + '||' + name;
          opt.innerText = name + ' (' + vendor + ')';
          group.appendChild(opt);
        });
        sel.appendChild(group);
      });
    }).catch(() => {/* ignore */});
  }

  window.applyPreset = function() {
    const sel = document.getElementById('preset-select');
    if (!sel || !sel.value) return;
    const [vendor, name] = sel.value.split('||');
    const preset = window._presets[vendor][name];
    if (!preset) return;
    // apply known fields
    if (preset.phase1_proposal) document.querySelector('select[name="phase1_proposal"]').value = preset.phase1_proposal;
    if (preset.phase2_proposal) document.querySelector('select[name="phase2_proposal"]').value = preset.phase2_proposal;
    if (preset.dhgrp) document.querySelector('select[name="dhgrp"]').value = preset.dhgrp;
    if (preset.interface) document.querySelector('input[name="interface"]').value = preset.interface;
  }

  // call presets loader on init
  loadPresets();
})();
