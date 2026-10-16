/* ==========================================================================
   CLEAN AUTO-LOOP FOR NORMAL BROWSER VIEWING (NO SCRUB BAR / NO UI OVERLAY)
   Automatically disabled when HyperFrames / Puppeteer drives the virtual clock.
   Kept in this separate file because hyperframes lint bans rAF and
   performance.now() inside the composition's inline script.
   (Shares the global lexical scope with the inline script above, so tl1-tl5
   are visible here.)
   ========================================================================== */
if (!navigator.webdriver && !window.location.search.includes("hyperframes")) {
  const scenes = [
    { el: document.getElementById("scene-1"), start: 0.0, end: 3.2, tl: tl1 },
    { el: document.getElementById("scene-2"), start: 3.2, end: 6.0, tl: tl2 },
    { el: document.getElementById("scene-3"), start: 6.0, end: 8.8, tl: tl3 },
    { el: document.getElementById("scene-4"), start: 8.8, end: 11.8, tl: tl4 },
    { el: document.getElementById("scene-5"), start: 11.8, end: 15.0, tl: tl5 }
  ];

  function fitScreen() {
    const root = document.getElementById("root");
    const scale = Math.min(window.innerWidth / 1080, window.innerHeight / 1920);
    document.body.style.display = "flex";
    document.body.style.alignItems = "center";
    document.body.style.justifyContent = "center";
    document.body.style.width = "100vw";
    document.body.style.height = "100vh";
    root.style.transform = `scale(${scale})`;
    root.style.transformOrigin = "center center";
  }
  window.addEventListener("resize", fitScreen);
  fitScreen();

  let startClock = performance.now();
  function loop(now) {
    const t = ((now - startClock) / 1000) % 15.0;
    scenes.forEach(s => {
      if (t >= s.start && t < s.end) {
        s.el.style.visibility = "visible";
        s.tl.seek(t - s.start, false);
      } else {
        s.el.style.visibility = "hidden";
      }
    });
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
}
