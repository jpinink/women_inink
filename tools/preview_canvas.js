(function drawPreviewMap() {
  const box = document.getElementById('map');
  const c = document.createElement('canvas');
  box.innerHTML = '';
  box.appendChild(c);
  const note = document.createElement('p');
  note.className = 'pv-note';
  note.textContent = 'Preview: the live site shows a full street map here.';
  box.appendChild(note);
  function draw() {
    const w = box.clientWidth, h = box.clientHeight, dpr = window.devicePixelRatio || 1;
    c.width = w * dpr; c.height = h * dpr; c.style.width = w + 'px'; c.style.height = h + 'px';
    const g = c.getContext('2d'); g.scale(dpr, dpr);
    const lats = SHOPS.map(s => s.lat), lngs = SHOPS.map(s => s.lng);
    const la0 = Math.min(...lats) - 0.4, la1 = Math.max(...lats) + 0.4, lo0 = Math.min(...lngs) - 0.6, lo1 = Math.max(...lngs) + 0.6;
    const k = Math.cos((la0 + la1) / 2 * Math.PI / 180);
    const sx = (w - 32) / ((lo1 - lo0) * k), sy = (h - 32) / (la1 - la0), s = Math.min(sx, sy);
    const ox = (w - (lo1 - lo0) * k * s) / 2, oy = (h - (la1 - la0) * s) / 2;
    g.fillStyle = '#ece6dd'; g.fillRect(0, 0, w, h);
    SHOPS.forEach(p => {
      const x = ox + (p.lng - lo0) * k * s, y = oy + (la1 - p.lat) * s;
      g.beginPath(); g.arc(x, y, 5, 0, Math.PI * 2);
      g.fillStyle = fdSoon[p.slug] ? '#D8B9BC' : '#443473'; g.fill();
      g.lineWidth = 1.5; g.strokeStyle = '#F7F2EC'; g.stroke();
    });
  }
  draw();
  window.addEventListener('resize', draw);
})();
