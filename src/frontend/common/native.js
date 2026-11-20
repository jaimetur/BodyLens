/* Inside the BodyLens app for Android (window.BodyLensNative): files the page makes (PDF export, backups, CSV) are
   handed to the app, which saves them in Downloads and offers to open or share them; a WebView cannot download a
   file made in the page by itself. Outside the app this file does nothing. */
(function () {
  var N = null;
  try { N = window.BodyLensNative || (parent !== window && parent.BodyLensNative) || null; } catch (e) {}
  if (!N) return;
  window.BL_NATIVE = N;
  document.documentElement.classList.add('inapp');
  var isFile = function (a) { return a && a.hasAttribute && a.hasAttribute('download') && /^(blob:|data:)/.test(a.href || ''); };
  function save(a) {
    var name = a.getAttribute('download') || 'BodyLens';
    fetch(a.href).then(function (r) { return r.blob(); }).then(function (b) {
      var fr = new FileReader();
      fr.onload = function () { N.saveFile(name, b.type || 'application/octet-stream', String(fr.result).split(',')[1] || ''); };
      fr.readAsDataURL(b);
    });
  }
  var click = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () { if (isFile(this)) { save(this); return; } return click.call(this); };
  var dispatch = HTMLAnchorElement.prototype.dispatchEvent;
  HTMLAnchorElement.prototype.dispatchEvent = function (e) {
    if (e && e.type === 'click' && isFile(this)) { save(this); return true; }
    return dispatch.call(this, e);
  };
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[download]');
    if (isFile(a)) { e.preventDefault(); save(a); }
  }, true);
})();
