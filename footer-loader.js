// Loads the shared footer from /footer.html into any element with id="shared-footer"
(function() {
  fetch('/footer.html')
    .then(function(res) { return res.text(); })
    .then(function(html) {
      var el = document.getElementById('shared-footer');
      if (el) el.outerHTML = html;
    })
    .catch(function(err) { console.warn('Footer failed to load:', err); });
})();
