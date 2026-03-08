// Loads the shared footer and initialises cookie banner logic after injection
(function() {
  fetch('/footer.html')
    .then(function(res) { return res.text(); })
    .then(function(html) {
      var el = document.getElementById('shared-footer');
      if (!el) return;
      el.outerHTML = html;
      initCookieBanner();
    })
    .catch(function(err) { console.warn('Footer failed to load:', err); });

  function initCookieBanner() {
    var banner = document.getElementById('cookie-banner');
    if (!banner) return;

    // Hide banner if consent already given
    if (localStorage.getItem('cookie-consent')) {
      banner.style.display = 'none';
      return;
    }

    banner.style.display = 'flex';

    var acceptBtn = banner.querySelector('.cookie-accept');
    var declineBtn = banner.querySelector('.cookie-decline');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', function() {
        localStorage.setItem('cookie-consent', 'accepted');
        banner.style.display = 'none';
        // Enable GA if it was deferred
        if (typeof gtag === 'function') {
          gtag('consent', 'update', { analytics_storage: 'granted' });
        }
      });
    }

    if (declineBtn) {
      declineBtn.addEventListener('click', function() {
        localStorage.setItem('cookie-consent', 'declined');
        banner.style.display = 'none';
      });
    }
  }
})();
