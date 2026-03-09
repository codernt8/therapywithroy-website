// Loads the shared footer and initialises cookie banner + GA logic after injection
(function() {
  var GA_ID = 'G-EZDPQG16PQ';
  var CONSENT_KEY = 'cookie-consent';

  function loadGA() {
    if (window._gaLoaded) return;
    window._gaLoaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    function gtag(){ dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', GA_ID, { 'anonymize_ip': true });
  }

  // Fire GA immediately if already accepted (e.g. returning visitor)
  if (localStorage.getItem(CONSENT_KEY) === 'accepted') {
    loadGA();
  }

  fetch('/footer.html')
    .then(function(res) { return res.text(); })
    .then(function(html) {
      var el = document.getElementById('shared-footer');
      if (!el) return;
      el.outerHTML = html;
      // Scripts inside innerHTML are not executed by the browser,
      // so we set the obfuscated email href here after injection.
      var emailLink = document.getElementById('footer-email-link');
      if (emailLink) emailLink.href = 'mailto:' + 'roy' + '@' + 'therapywithroy.co.uk';
      initCookieBanner();
    })
    .catch(function(err) { console.warn('Footer failed to load:', err); });

  function initCookieBanner() {
    var banner = document.getElementById('cookie-banner');
    if (!banner) return;

    var consent = localStorage.getItem(CONSENT_KEY);

    // Also migrate any old key variants so returning visitors aren't re-prompted
    if (!consent) {
      var legacy = localStorage.getItem('cookie_consent');
      if (legacy) {
        localStorage.setItem(CONSENT_KEY, legacy);
        consent = legacy;
      }
    }

    if (consent) {
      banner.style.display = 'none';
      return;
    }

    banner.style.display = 'flex';

    var acceptBtn = banner.querySelector('.cookie-accept');
    var declineBtn = banner.querySelector('.cookie-decline');

    if (acceptBtn) {
      acceptBtn.addEventListener('click', function() {
        localStorage.setItem(CONSENT_KEY, 'accepted');
        banner.style.display = 'none';
        loadGA();
      });
    }

    if (declineBtn) {
      declineBtn.addEventListener('click', function() {
        localStorage.setItem(CONSENT_KEY, 'declined');
        banner.style.display = 'none';
      });
    }
  }
})();
