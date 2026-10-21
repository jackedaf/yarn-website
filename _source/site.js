(() => {
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Frame sequences: one masked layer per frame, only the current one shown.
  const seqs = [...document.querySelectorAll('[data-frames]')].map(el => {
    const srcs = el.dataset.frames.split(/\s+/);
    const box = document.createElement('i');
    box.className = 'layers';
    el.appendChild(box);
    const layers = srcs.map((s, i) => {
      const ink = document.createElement('i');
      ink.className = 'ink' + (i ? ' off' : '');
      ink.style.setProperty('--src', `url(${s})`);
      box.appendChild(ink);
      return ink;
    });
    const ms = +el.dataset.ms, hold = +(el.dataset.hold || 0);
    return { el: box, layers, ms, loop: layers.length * ms + hold, shown: 0, start: 0, bump: el.hasAttribute('data-bump') };
  });

  // Copy buttons (the contact page): copy the text, or select it if copying isn't allowed.
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.copy);
      const done = () => { btn.textContent = 'Copied'; setTimeout(() => { btn.textContent = 'Copy'; }, 1600); };
      const select = () => { const r = document.createRange(); r.selectNodeContents(target); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); };
      try { navigator.clipboard.writeText(target.textContent.trim()).then(done, select); } catch { select(); }
    });
  });

  // With motion turned off, a story shows the scene its data-still names.
  if (still) {
    document.querySelectorAll('[data-scenes][data-still]').forEach(el => {
      el.querySelectorAll('[data-scene]').forEach((sc, i) => { sc.hidden = i !== +el.dataset.still; });
    });
    return;
  }

  // Replays a one-shot CSS animation class.
  const replay = (el, cls) => { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); };

  // Only drawings on screen wobble. Each frame, each one moves to a different
  // wobble at random, so no two move in step and there's no loop to spot.
  const onScreen = new Set();
  const boils = [...document.querySelectorAll('.boil')];
  const seen = new IntersectionObserver(entries => {
    for (const e of entries) e.isIntersecting ? onScreen.add(e.target) : onScreen.delete(e.target);
  });
  boils.forEach(el => seen.observe(el));

  // The app icons round Yarn's head: each moves along an oval the shape of his
  // face, one stop-motion step (11.25deg) at a time, turning as it goes so its
  // trail stays behind it. Positions are in the drawing's own pixels (450 square).
  const orbits = [...document.querySelectorAll('[data-orbit]')].map(el => {
    const [cx, cy, rx, ry, t0] = el.dataset.orbit.split(',').map(Number);
    const icons = [...el.children].map((ink, k) => {
      const [x, y] = ink.dataset.sq.split(',').map(Number);
      return { ink, x, y, start: t0 + 60 * k };
    });
    return { cx, cy, rx, ry, icons };
  });
  const placeOrbits = step => {
    const turn = step * 11.25;
    for (const o of orbits) for (const ic of o.icons) {
      const a = (ic.start + turn) * Math.PI / 180;
      const dx = (o.cx + o.rx * Math.cos(a) - ic.x) / 4.5, dy = (o.cy + o.ry * Math.sin(a) - ic.y) / 4.5;
      ic.ink.style.translate = `${dx.toFixed(2)}% ${dy.toFixed(2)}%`;
      ic.ink.style.rotate = `${turn}deg`;
    }
  };

  // Drawings that play as a short story (the night band, and the reels phone
  // that cuts to Journal to Unlock): each scene held for its own beat.
  const stages = [...document.querySelectorAll('[data-scenes]')].map(el => (
    { scenes: [...el.querySelectorAll('[data-scene]')], i: 0, at: 0 }
  ));

  const t0 = performance.now();
  let frame = -1, orbitStep = -1;
  function tick(now) {
    const t = Math.max(0, now - t0);

    // The logo's own frame rate: a new wobble every 0.15s.
    const f = Math.floor(t / 150);
    if (f !== frame) {
      frame = f;
      for (const el of onScreen) {
        const b = +(el.dataset.b || 0);
        el.dataset.b = (b + 1 + Math.floor(Math.random() * 3)) % 4;
      }
    }

    // The icons round Yarn's head step every 0.24s: about 8 seconds a turn.
    const o = Math.floor(t / 240);
    if (o !== orbitStep) { orbitStep = o; placeOrbits(o % 32); }

    for (const s of seqs) {
      const i = Math.min(Math.floor(((t - s.start) % s.loop) / s.ms), s.layers.length - 1);
      if (i !== s.shown) {
        s.layers[s.shown].classList.add('off');
        s.layers[i].classList.remove('off');
        s.shown = i;
        if (s.bump) replay(s.el, 'bump');
      }
    }

    for (const st of stages) {
      if (t - st.at < +st.scenes[st.i].dataset.scene) continue;
      st.at = t;
      st.scenes[st.i].hidden = true;
      st.i = (st.i + 1) % st.scenes.length;
      st.scenes[st.i].hidden = false;
      // A drawing loop inside the scene (Yarn's typing) starts again from its first drawing.
      for (const s of seqs) if (st.scenes[st.i].contains(s.el)) s.start = t;
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();
