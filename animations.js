// Render all <i data-lucide="..."> tags into crisp inline SVGs immediately
if (window.lucide) {
  lucide.createIcons();
}

gsap.registerPlugin(CustomEase);

// Smooth Apple Keynote & Viscous Liquid Curves
CustomEase.create("appleFluid", "M0,0 C0.22,1 0.36,1 1,1");
CustomEase.create("appleInOut", "M0,0 C0.65,0 0.35,1 1,1");
CustomEase.create("liquidSnap", "M0,0 C0.18,1.42 0.38,1 1,1");

window.__timelines = window.__timelines || {};

const studioEnv = document.getElementById("studio-env");
const prismPulse = document.getElementById("prismatic-pulse");

/* ==========================================================================
   SCENE 1 (0.0s - 3.2s): 3D Perspective Liquid Glass Dock
   ========================================================================== */
const tl1 = gsap.timeline({ paused: true });

tl1.fromTo("#s1-dock",
    { rotationY: -42, rotationX: 14, scale: 1.35, z: 180 },
    { rotationY: 16, rotationX: 4, scale: 1.0, z: 0, duration: 1.3, ease: "appleFluid" }, 0)
   .from("#s1-label", { y: 24, opacity: 0, filter: "blur(10px)", duration: 0.7, ease: "appleFluid" }, 0.3)

   // At 1.15s: The 3D Parachute Squircle swells like liquid mercury & pops forward
   .to("#s1-liquid-swell", { opacity: 0.9, duration: 0.3, yoyo: true, repeat: 1 }, 1.1)
   .to("#s1-hero-rim", { opacity: 1, duration: 0.4 }, 1.15)
   .to("#s1-icon-hero", {
     z: 130,
     y: -48,
     scale: 1.28,
     boxShadow: "0 45px 90px rgba(0,0,0,0.25), inset 0 6px 12px rgba(255,255,255,1)",
     duration: 0.85,
     ease: "liquidSnap"
   }, 1.2)

   // Prismatic transition out
   .fromTo(prismPulse, { scale: 0.3, opacity: 0 }, { scale: 1.6, opacity: 0.85, duration: 0.45, ease: "power2.out" }, 2.7)
   .to(prismPulse, { opacity: 0, duration: 0.2 }, 3.0)
   .to("#scene-1", { opacity: 0, filter: "blur(16px)", scale: 0.94, duration: 0.35 }, 2.85);

window.__timelines["scene-1"] = tl1;


/* ==========================================================================
   SCENE 2 (3.2s - 6.0s | Local 2.8s): Tactile Vertical Price Slider
   ========================================================================== */
const tl2 = gsap.timeline({ paused: true });

tl2.from("#s2-pill-switch", { scale: 0.86, rotationY: -22, opacity: 0, filter: "blur(16px)", duration: 0.55, ease: "appleFluid" }, 0)
   .from("#s2-label", { y: 20, opacity: 0, duration: 0.5, ease: "appleFluid" }, 0.15)

   // Knob slides down toward $0.99, stretching elastically like viscous water
   .to("#s2-knob", {
     y: 410,
     scaleY: 1.18,
     scaleX: 0.9,
     duration: 0.85,
     ease: "appleInOut"
   }, 0.55)
   .to("#s2-track-glow", { opacity: 0.9, duration: 0.6 }, 0.7)
   .to("#s2-rim", { opacity: 1, duration: 0.3 }, 1.25)

   // Hits price floor & snaps back up to $3.59
   .to("#s2-knob", {
     y: 0,
     scaleY: 1,
     scaleX: 1,
     duration: 0.75,
     ease: "liquidSnap"
   }, 1.45)
   .to("#s2-track-glow", { opacity: 0.3, duration: 0.5 }, 1.55)
   .to("#scene-2", { opacity: 0, filter: "blur(14px)", scale: 1.05, duration: 0.35 }, 2.45);

window.__timelines["scene-2"] = tl2;


/* ==========================================================================
   SCENE 3 (6.0s - 8.8s | Local 2.8s): Outsourced Can & 3D Factory Goo Droplet
   ========================================================================== */
const tl3 = gsap.timeline({ paused: true });

tl3.from("#s3-vessel", { scale: 0.84, opacity: 0, filter: "blur(14px)", duration: 0.55, ease: "appleFluid" }, 0)
   .from("#s3-label", { y: 20, opacity: 0, duration: 0.5, ease: "appleFluid" }, 0.15)

   // 3D Factory droplet stretches & detaches from the glass vessel via SVG #liquid-goo
   .fromTo("#s3-droplet",
     { x: 0, y: -20, scale: 0.5 },
     { x: 255, y: -110, scale: 1, duration: 1.25, ease: "liquidSnap" }, 0.55)
   .to("#s3-vessel", { x: -75, rotation: -4, duration: 1.1, ease: "appleFluid" }, 0.6)
   .to("#scene-3", { opacity: 0, filter: "blur(16px)", duration: 0.35 }, 2.45);

window.__timelines["scene-3"] = tl3;


/* ==========================================================================
   SCENE 4 (8.8s - 11.8s | Local 3.0s): Dark-Mode Grid Room & 30% Flywheel
   ========================================================================== */
const tl4 = gsap.timeline({
  paused: true,
  onUpdate: function() {
    const p = this.progress();
    if (p > 0.01 && p < 0.96) {
      studioEnv.classList.remove("studio-light");
      studioEnv.classList.add("studio-dark");
    } else {
      studioEnv.classList.remove("studio-dark");
      studioEnv.classList.add("studio-light");
    }
  }
});

tl4.from("#s4-ring-card", { scale: 0.78, y: -40, opacity: 0, filter: "blur(18px)", duration: 0.6, ease: "appleFluid" }, 0)
   .from("#s4-label", { y: 20, opacity: 0, duration: 0.5, ease: "appleFluid" }, 0.15)
   .to("#s4-arc", { strokeDashoffset: 448, duration: 1.1, ease: "appleFluid" }, 0.35)

   // Eject the 3 luminous glass icons (3D Trophy, 3D Voltage, Official F1 Logo)
   .from("#s4-node-1", { y: -140, scale: 0.4, opacity: 0, duration: 0.65, ease: "liquidSnap" }, 0.75)
   .from("#s4-node-2", { y: -140, scale: 0.4, opacity: 0, duration: 0.65, ease: "liquidSnap" }, 0.95)
   .from("#s4-node-3", { y: -140, scale: 0.4, opacity: 0, duration: 0.65, ease: "liquidSnap" }, 1.15)
   .to("#scene-4", { opacity: 0, filter: "blur(18px)", scale: 0.92, duration: 0.35 }, 2.65);

window.__timelines["scene-4"] = tl4;


/* ==========================================================================
   SCENE 5 (11.8s - 15.0s | Local 3.2s): Caffeine Atom -> Red Bull Brand Crest
   ========================================================================== */
const tl5 = gsap.timeline({ paused: true });

tl5.set("#s5-brand-monolith", { opacity: 0, scale: 0.75, rotationY: -75 })
   .from("#s5-caffeine-tile", { scale: 0.85, opacity: 0, filter: "blur(14px)", duration: 0.55, ease: "appleFluid" }, 0)
   .from("#s5-label", { y: 20, opacity: 0, duration: 0.5, ease: "appleFluid" }, 0.1)

   // Flip Caffeine Atom away through a prismatic rainbow pulse & reveal Red Bull Crest Monolith
   .to("#s5-caffeine-tile", { rotationY: 75, scale: 0.75, opacity: 0, filter: "blur(18px)", duration: 0.55, ease: "appleInOut" }, 1.2)
   .fromTo(prismPulse, { scale: 0.4, opacity: 0 }, { scale: 1.4, opacity: 0.9, duration: 0.45, ease: "power2.out" }, 1.25)
   .to(prismPulse, { opacity: 0, duration: 0.35 }, 1.65)

   .to("#s5-brand-monolith", {
     opacity: 1,
     scale: 1,
     rotationY: 0,
     duration: 0.85,
     ease: "liquidSnap",
     onStart: () => {
       document.getElementById("s5-label-text").textContent = "Brand Pro";
     }
   }, 1.35)
   .to("#s5-monolith-rim", { opacity: 0.9, duration: 0.5 }, 1.45);

window.__timelines["scene-5"] = tl5;


/* ==========================================================================
   CLEAN AUTO-LOOP FOR NORMAL BROWSER VIEWING (NO SCRUB BAR / NO UI OVERLAY)
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
