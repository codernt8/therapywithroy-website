/* Shared behaviour for the home page and the service pages:
   booking modals (Acuity iframes load on demand), mobile menu, "Specialisms" dropdown,
   animated FAQ, and the obfuscated email link. Analytics consent stays in /footer-loader.js. */
(function () {
  'use strict';
  document.documentElement.classList.add('js');

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Booking modals ---------- */
  var modals = {
    free: document.getElementById('modalFree'),
    individual: document.getElementById('modalIndividual'),
    couples: document.getElementById('modalCouples')
  };
  var lastTrigger = null;

  // Acuity iframes carry their address in data-src and only load when needed.
  function loadFrame(m) {
    var f = m && m.querySelector('iframe[data-src]');
    if (f && !f.getAttribute('src')) f.setAttribute('src', f.getAttribute('data-src'));
  }
  function openModal(type, trigger) {
    var m = modals[type];
    if (!m) return;
    lastTrigger = trigger || null;
    loadFrame(m);
    m.classList.add('active');
    document.body.classList.add('modal-open');
    var close = m.querySelector('.modal-close');
    if (close) close.focus();
    if (typeof window.gtag === 'function') {
      window.gtag('event', 'booking_modal_opened', { event_category: 'engagement', event_label: type });
    }
  }
  function closeModal(m) {
    m.classList.remove('active');
    document.body.classList.remove('modal-open');
    if (lastTrigger && lastTrigger.focus) lastTrigger.focus();
    lastTrigger = null;
  }

  document.querySelectorAll('[data-modal]').forEach(function (btn) {
    var type = btn.getAttribute('data-modal');
    btn.addEventListener('click', function (e) { e.preventDefault(); openModal(type, btn); });
    // Start loading the booking form as soon as someone shows intent, so it is ready when the modal opens.
    ['mouseenter', 'focus', 'touchstart'].forEach(function (ev) {
      btn.addEventListener(ev, function () { loadFrame(modals[type]); }, { passive: true, once: true });
    });
  });
  var navBook = document.getElementById('navBookBtn');
  if (navBook) {
    navBook.addEventListener('click', function (e) { e.preventDefault(); openModal('free', navBook); });
    ['mouseenter', 'focus', 'touchstart'].forEach(function (ev) {
      navBook.addEventListener(ev, function () { loadFrame(modals.free); }, { passive: true, once: true });
    });
  }
  document.querySelectorAll('.modal-close').forEach(function (btn) {
    btn.addEventListener('click', function () { closeModal(this.closest('.modal-overlay')); });
  });
  document.querySelectorAll('.modal-overlay').forEach(function (m) {
    m.addEventListener('click', function (e) { if (e.target === m) closeModal(m); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') document.querySelectorAll('.modal-overlay.active').forEach(closeModal);
  });

  /* ---------- Email link (kept out of the HTML source) ---------- */
  var emailBtn = document.getElementById('email-btn');
  if (emailBtn) emailBtn.href = 'mailto:' + 'roy' + '@' + 'therapywithroy.co.uk';

  /* ---------- Mobile menu ---------- */
  var menuBtn = document.getElementById('mobile-menu-btn');
  var navList = document.getElementById('nav-links');
  function setMenu(open) {
    navList.classList.toggle('active', open);
    menuBtn.innerHTML = open ? '&times;' : '&#9776;';
    menuBtn.style.fontSize = open ? '2.2rem' : '1.8rem';
    menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  if (menuBtn && navList) {
    menuBtn.setAttribute('aria-expanded', 'false');
    menuBtn.addEventListener('click', function () { setMenu(!navList.classList.contains('active')); });
    navList.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () { setMenu(false); });
    });
  }

  /* ---------- "Specialisms" dropdown ---------- */
  document.querySelectorAll('.has-sub').forEach(function (li) {
    var btn = li.querySelector('.sub-toggle');
    if (!btn) return;
    var desktopHover = window.matchMedia('(hover: hover) and (min-width: 1181px)');
    function setOpen(open) {
      li.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    btn.addEventListener('click', function () { setOpen(!li.classList.contains('open')); });
    li.addEventListener('mouseenter', function () { if (desktopHover.matches) setOpen(true); });
    li.addEventListener('mouseleave', function () { if (desktopHover.matches) setOpen(false); });
    li.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && li.classList.contains('open')) { setOpen(false); btn.focus(); }
    });
    li.addEventListener('focusout', function (e) {
      if (!li.contains(e.relatedTarget)) setOpen(false);
    });
    document.addEventListener('click', function (e) { if (!li.contains(e.target)) setOpen(false); });
  });

  /* ---------- FAQ: native <details>, animated open and close ---------- */
  var faqItems = Array.prototype.slice.call(document.querySelectorAll('.faq-item'));
  var faqToggle = document.getElementById('faq-toggle');

  function faqIsOpen(d) { return d.open && !d.classList.contains('is-closing'); }

  function syncFaqLabel() {
    if (!faqToggle) return;
    var allOpen = faqItems.length > 0 && faqItems.every(faqIsOpen);
    faqToggle.textContent = allOpen ? 'Collapse all' : 'Expand all';
  }

  function setFaq(d, open) {
    var panel = d.querySelector('.faq-a');
    if (!panel || faqIsOpen(d) === open) return;
    // A closed <details> can still report its content height, so only measure when it is showing.
    var from = d.open ? panel.getBoundingClientRect().height : 0;
    if (d._anim) { d._anim.cancel(); d._anim = null; }

    if (reduceMotion || !panel.animate) {
      d.open = open;
      d.classList.remove('is-closing');
      syncFaqLabel();
      return;
    }

    if (open) {
      d.classList.remove('is-closing');
      d.open = true;
      var to = panel.scrollHeight;
      d._anim = panel.animate([{ height: from + 'px' }, { height: to + 'px' }], { duration: 280, easing: 'ease' });
      d._anim.onfinish = function () { d._anim = null; };
    } else {
      d.classList.add('is-closing');
      var anim = panel.animate([{ height: from + 'px' }, { height: '0px' }], { duration: 260, easing: 'ease' });
      d._anim = anim;
      var finishClose = function () {
        if (d._anim !== anim) return;
        d._anim = null;
        d.open = false;
        d.classList.remove('is-closing');
        syncFaqLabel();
      };
      anim.onfinish = finishClose;
      setTimeout(finishClose, 320); // safety net if the browser pauses animations
    }
    syncFaqLabel();
  }

  faqItems.forEach(function (d) {
    var summary = d.querySelector('summary');
    if (!summary) return;
    summary.addEventListener('click', function (e) {
      e.preventDefault();
      setFaq(d, !faqIsOpen(d));
    });
  });

  if (faqToggle && faqItems.length) {
    faqToggle.hidden = false;
    faqToggle.addEventListener('click', function () {
      var open = !faqItems.every(faqIsOpen);
      faqItems.forEach(function (d) { setFaq(d, open); });
    });
    syncFaqLabel();
  }
})();
