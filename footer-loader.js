// Loads the shared footer and initialises cookie banner + Google tag consent logic after injection
(function() {
  var GA_ID = 'G-EZDPQG16PQ';
  var ADS_ID = 'AW-18385023405';
  var CONSENT_KEY = 'cookie-consent';

  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  window.gtag = gtag;

  // Consent Mode v2: everything starts denied. Until the visitor accepts, Google
  // tags send cookieless pings only and set no cookies.
  gtag('consent', 'default', {
    'ad_storage': 'denied',
    'analytics_storage': 'denied',
    'ad_user_data': 'denied',
    'ad_personalization': 'denied'
  });

  // Accept grants analytics and ad measurement. ad_personalization is never
  // granted, so no remarketing audiences are built from visits to a therapy site.
  function grantConsent() {
    gtag('consent', 'update', {
      'ad_storage': 'granted',
      'analytics_storage': 'granted',
      'ad_user_data': 'granted'
    });
  }

  // Returning visitor who already accepted: grant before the tag configures
  if (localStorage.getItem(CONSENT_KEY) === 'accepted') {
    grantConsent();
  }

  var s = document.createElement('script');
  s.async = true;
  s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
  document.head.appendChild(s);
  gtag('js', new Date());
  gtag('config', GA_ID, { 'anonymize_ip': true });
  gtag('config', ADS_ID, { 'allow_ad_personalization_signals': false });

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
        grantConsent();
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
