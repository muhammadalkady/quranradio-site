/* The hero mark's light, as the app's player draws FrostedBrandMark: the four discs of light under
   the frost each orbit their home point while that orbit's centre slowly circles too (the app's
   FrostedMarkRecipe.meshBlobs and Drift), so the glass shifts like a mesh gradient. The mark itself
   swells in with CSS. Nothing moves under prefers-reduced-motion, or while the mark is off screen. */
(function () {
  var svg = document.querySelector('.hero__logo svg');
  if (!svg || !window.requestAnimationFrame) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Home point, amplitude (x, y), orbit period and precession period in ms; negative turns the other way.
  var blobs = [
    { id: 'mh-light-0', x: 180, y: 170, ax: 100, ay: 90, period: 6000, precession: 24000 },
    { id: 'mh-light-1', x: 350, y: 350, ax: 90, ay: 90, period: -8000, precession: -24000 },
    { id: 'mh-light-2', x: 365, y: 150, ax: 78, ay: 80, period: 4800, precession: 12000 },
    { id: 'mh-light-3', x: 140, y: 370, ax: 72, ay: 74, period: -6000, precession: -12000 }
  ];
  blobs.forEach(function (b) { b.el = svg.getElementById ? svg.getElementById(b.id) : document.getElementById(b.id); });
  if (blobs.some(function (b) { return !b.el; })) return;

  var CYCLE = 24000, TAU = Math.PI * 2;
  var visible = true, clock = 0, last = null, frame = 0;

  function draw(ms) {
    blobs.forEach(function (b) {
      var orbit = TAU * ms / b.period, precession = TAU * ms / b.precession;
      b.el.setAttribute('cx', (b.x + b.ax / 2 * (Math.sin(orbit) - Math.sin(precession))).toFixed(2));
      b.el.setAttribute('cy', (b.y + b.ay / 2 * (Math.cos(precession) - Math.cos(orbit))).toFixed(2));
    });
  }

  function tick(now) {
    if (last !== null) clock = (clock + Math.min(now - last, 100)) % CYCLE;
    last = now;
    draw(clock);
    frame = visible ? requestAnimationFrame(tick) : 0;
  }

  function start() { if (!frame) { last = null; frame = requestAnimationFrame(tick); } }

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting;
      if (visible) start();
    }).observe(svg);
  }
  start();
})();
