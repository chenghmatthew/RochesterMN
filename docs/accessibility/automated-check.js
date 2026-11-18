// Automated accessibility spot-check for What's Open. Not a substitute for axe, WAVE or manual testing.
//
// How to run: open the page, switch to the view you want to check (Map, Cards or List), open the browser
// developer tools console (F12), paste this whole file and press Enter. Record the result in
// ADA-TITLE-II-TESTING.md under "Results log", noting the view and window width.
//
// Checks: page language, title, heading counts, landmarks, images without an alt attribute, buttons and
// clickable elements without a name or role, inputs without a label, and text that fails WCAG contrast
// (4.5:1, or 3:1 for large text). It looks inside shadow DOM, where the photo slots keep their images.
// Hidden inputs (such as the photo file pickers) are listed in inputsNoLabel but are not exposed to
// assistive technology.
(() => {
  const all = (root, selector, found = []) => {
    root.querySelectorAll(selector).forEach(el => found.push(el));
    root.querySelectorAll('*').forEach(el => el.shadowRoot && all(el.shadowRoot, selector, found));
    return found;
  };
  const channel = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const luminance = color => {
    const m = color.match(/[\d.]+/g).map(Number);
    return 0.2126 * channel(m[0]) + 0.7152 * channel(m[1]) + 0.0722 * channel(m[2]);
  };
  const backgroundOf = el => {
    while (el) {
      const color = getComputedStyle(el).backgroundColor, m = color.match(/[\d.]+/g);
      if (m && (m.length < 4 || +m[3] > 0.5)) return color;
      el = el.parentElement;
    }
    return 'rgb(255,255,255)';
  };
  const lowContrast = [];
  all(document, 'body *').forEach(el => {
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return;
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none') return;
    const a = luminance(style.color), b = luminance(backgroundOf(el));
    const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    const size = parseFloat(style.fontSize), bold = +style.fontWeight >= 700;
    const needed = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;
    if (ratio < needed) lowContrast.push([el.textContent.trim().slice(0, 36), style.color, backgroundOf(el), +ratio.toFixed(2), size]);
  });
  const images = all(document, 'img'), buttons = all(document, 'button,[role=button]'), inputs = all(document, 'input,select,textarea');
  return {
    lang: document.documentElement.lang || null,
    title: document.title,
    h1: all(document, 'h1').length, h2: all(document, 'h2').length, h3: all(document, 'h3').length,
    landmarks: all(document, 'main,nav,header,footer,[role=main]').length,
    skipLinks: all(document, 'a[href^="#"]').length,
    imagesWithoutAltAttribute: images.filter(i => !i.hasAttribute('alt')).length,
    imagesWithAltText: images.filter(i => i.alt).length,
    buttonsWithoutName: buttons.filter(b => !(b.textContent.trim() || b.getAttribute('aria-label'))).length,
    clickableWithoutRole: all(document, '[sc-camel-on-click]').filter(e => !e.getAttribute('role') && !/^(BUTTON|A)$/.test(e.tagName)).length,
    inputsNoLabel: inputs.filter(i => !(i.getAttribute('aria-label') || (i.id && document.querySelector('label[for="' + i.id + '"]')) || i.closest('label'))).length,
    contrastFailures: lowContrast.length,
    contrastSamples: lowContrast.slice(0, 10),
  };
})();
