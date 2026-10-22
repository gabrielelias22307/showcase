// SVG renderers for evidence graphics. Each returns an SVG string.
// Types: floorplan, table, flowchart, bar, line, pie.
// Charts use direct value labels so colour is never the only cue.

const INK = '#1f2430';
const MUTED = '#5b6474';
const GRID = '#d9dde5';
const SERIES = ['#2a6fdb', '#d9730d', '#2f8a5b', '#8a3fa0'];

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function svg(w, h, title, body) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}" font-family="Lato, Helvetica, Arial, sans-serif">
<rect width="${w}" height="${h}" fill="#ffffff"/>${body}</svg>`;
}

function text(x, y, s, opts = {}) {
  const { size = 13, anchor = 'middle', weight = 400, fill = INK, rotate } = opts;
  const t = rotate ? ` transform="rotate(${rotate} ${x} ${y})"` : '';
  return `<text x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}" font-weight="${weight}" fill="${fill}"${t}>${esc(s)}</text>`;
}

function legend(series, x, y) {
  return series.map((s, i) => {
    const lx = x + i * 170;
    return `<rect x="${lx}" y="${y - 10}" width="14" height="14" rx="2" fill="${SERIES[i % SERIES.length]}"/>` +
      text(lx + 20, y + 1, s.name, { anchor: 'start', size: 13 });
  }).join('');
}

// ---------- Floor plan (drawn from mystery.room) ----------
export function floorplan(ev, room) {
  const W = 760, H = 560, pad = 40;
  const sx = (W - pad * 2) / room.width;
  const sz = (H - pad * 2 - 30) / room.depth;
  const s = Math.min(sx, sz);
  const ox = (W - room.width * s) / 2, oz = pad;
  const X = (x) => ox + (x + room.width / 2) * s;
  const Z = (z) => oz + (z + room.depth / 2) * s;
  let b = '';
  // walls
  b += `<rect x="${X(-room.width / 2)}" y="${Z(-room.depth / 2)}" width="${room.width * s}" height="${room.depth * s}" fill="#f7f6f2" stroke="${INK}" stroke-width="5"/>`;
  // windows
  if (room.windows) {
    const w = room.windows;
    b += `<line x1="${X(-room.width / 2)}" y1="${Z(w.from)}" x2="${X(-room.width / 2)}" y2="${Z(w.to)}" stroke="#7fb3e6" stroke-width="7"/>`;
    b += text(X(-room.width / 2) - 12, Z((w.from + w.to) / 2), 'Windows', { size: 12, rotate: -90, fill: MUTED });
  }
  // inside walls, with gaps for the walk-through openings
  for (const iw of room.walls || []) {
    const [x1, z1] = iw.from, [x2, z2] = iw.to;
    const horiz = Math.abs(z1 - z2) < 1e-6;
    const lo = horiz ? Math.min(x1, x2) : Math.min(z1, z2), hi = horiz ? Math.max(x1, x2) : Math.max(z1, z2);
    const gaps = (iw.openings || []).map((o) => [o.at - o.width / 2, o.at + o.width / 2]).sort((p, q) => p[0] - q[0]);
    let cur = lo;
    const parts = [];
    for (const [ga, gb] of gaps) { parts.push([cur, ga]); cur = gb; }
    parts.push([cur, hi]);
    for (const [pa, pb] of parts) {
      if (pb - pa <= 0.01) continue;
      const [ax, az, bx, bz] = horiz ? [pa, z1, pb, z1] : [x1, pa, x1, pb];
      b += `<line x1="${X(ax)}" y1="${Z(az)}" x2="${X(bx)}" y2="${Z(bz)}" stroke="${INK}" stroke-width="4" stroke-linecap="square"/>`;
    }
  }
  // objects
  for (const o of room.objects) {
    if (!o.plan) continue;
    const fill = o.type === 'case' ? '#ffe2a8' : o.type === 'closet' ? '#e4e0d6' : o.type === 'table' ? '#ffffff' : '#eef1f6';
    const stroke = o.type === 'case' ? '#a86800' : '#8a93a3';
    b += `<rect x="${X(o.x - o.w / 2)}" y="${Z(o.z - o.d / 2)}" width="${o.w * s}" height="${o.d * s}" fill="${fill}" stroke="${stroke}" stroke-width="${o.type === 'case' ? 2.5 : 1.2}"/>`;
    if (o.label) {
      const vertical = o.d > o.w * 1.5 && o.type !== 'closet';
      // vertical labels go on the side facing the middle of the room
      const lx = vertical ? (o.x < 0 ? X(o.x + o.w / 2) + 16 : X(o.x - o.w / 2) - 10) : X(o.x);
      const ly = vertical ? Z(o.z) : (o.type === 'board' ? Z(o.z) + 18 : Z(o.z) + 4);
      b += text(lx, ly, o.label, { size: o.type === 'case' ? 14 : 12, weight: o.type === 'case' ? 700 : 400, rotate: vertical ? -90 : 0, fill: o.type === 'case' ? '#7a4a00' : INK });
    }
  }
  // room names
  for (const ar of room.areas || []) b += text(X(ar.x), Z(ar.z), ar.label.toUpperCase(), { size: 13, weight: 700, fill: '#9aa3b2' });
  // doors (gaps in walls)
  for (const d of room.doors) {
    let x1, y1, x2, y2, lx, ly;
    if (d.wall === 'south') { x1 = X(d.at - d.width / 2); x2 = X(d.at + d.width / 2); y1 = y2 = Z(room.depth / 2); lx = (x1 + x2) / 2; ly = y1 + 22; }
    else if (d.wall === 'north') { x1 = X(d.at - d.width / 2); x2 = X(d.at + d.width / 2); y1 = y2 = Z(-room.depth / 2); lx = (x1 + x2) / 2; ly = y1 - 10; }
    else if (d.wall === 'east') { y1 = Z(d.at - d.width / 2); y2 = Z(d.at + d.width / 2); x1 = x2 = X(room.width / 2); lx = x1 + 16; ly = (y1 + y2) / 2; }
    else if (d.wall === 'west') { y1 = Z(d.at - d.width / 2); y2 = Z(d.at + d.width / 2); x1 = x2 = X(-room.width / 2); lx = x1 - 16; ly = (y1 + y2) / 2; }
    else { continue; }
    b += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#ffffff" stroke-width="8"/>`;
    b += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#c0392b" stroke-width="3" stroke-dasharray="6 4"/>`;
    const vert = d.wall === 'east' || d.wall === 'west';
    b += text(lx, ly, d.label, { size: 13, weight: 700, fill: '#c0392b', rotate: vert ? (d.wall === 'east' ? 90 : -90) : 0 });
  }
  // compass + scale
  b += text(W - 30, H - 52, 'N', { size: 14, weight: 700 });
  b += `<path d="M ${W - 30} ${H - 84} l -7 16 l 7 -5 l 7 5 z" fill="${INK}"/>`;
  b += `<line x1="${pad}" y1="${H - 22}" x2="${pad + 4 * s}" y2="${H - 22}" stroke="${INK}" stroke-width="2"/>`;
  b += text(pad + 2 * s, H - 8, '4 meters', { size: 11, fill: MUTED });
  b += `<line x1="${W / 2 - 40}" y1="${H - 22}" x2="${W / 2 - 10}" y2="${H - 22}" stroke="#c0392b" stroke-width="3" stroke-dasharray="6 4"/>`;
  b += text(W / 2 - 4, H - 18, '= exit / door', { size: 12, anchor: 'start', fill: MUTED });
  return svg(W, H, ev.title, b);
}

// ---------- Table ----------
export function table(ev) {
  const { columns, rows } = ev.data;
  const colW = 170, rowH = 40, W = columns.length * colW + 20, H = (rows.length + 1) * rowH + 30;
  let b = '';
  columns.forEach((c, i) => {
    b += `<rect x="${10 + i * colW}" y="10" width="${colW}" height="${rowH}" fill="#2b3a55"/>`;
    b += text(10 + i * colW + colW / 2, 10 + rowH / 2 + 5, c, { size: 15, weight: 700, fill: '#ffffff' });
  });
  rows.forEach((r, ri) => {
    const y = 10 + (ri + 1) * rowH;
    r.forEach((cell, ci) => {
      b += `<rect x="${10 + ci * colW}" y="${y}" width="${colW}" height="${rowH}" fill="${ri % 2 ? '#f3f5f9' : '#ffffff'}" stroke="${GRID}"/>`;
      b += text(10 + ci * colW + colW / 2, y + rowH / 2 + 5, cell, { size: 15 });
    });
  });
  const note = ev.data.note ?? 'Times are PM. Sign out when you leave; sign in when you return.';
  if (note) b += text(W / 2, H - 6, note, { size: 12, fill: MUTED });
  return svg(W, H, ev.title, b);
}

// ---------- Flowchart / checklist ----------
export function flowchart(ev) {
  const steps = ev.data.steps;
  const boxW = 300, boxH = 46, gap = 22, W = 560, H = steps.length * (boxH + gap) + 20;
  const x = (W - boxW) / 2 - 40;
  let b = '';
  steps.forEach((st, i) => {
    const y = 10 + i * (boxH + gap);
    const fill = st.missing ? '#fff4d6' : '#eef3fb';
    const stroke = st.missing ? '#d08b00' : '#5b7bb5';
    b += `<rect x="${x}" y="${y}" width="${boxW}" height="${boxH}" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="2" ${st.missing ? 'stroke-dasharray="7 5"' : ''}/>`;
    b += text(x + 22, y + boxH / 2 + 5, `${i + 1}`, { size: 15, weight: 700, fill: stroke });
    b += text(x + boxW / 2 + 10, y + boxH / 2 + 5, st.text, { size: 15, weight: st.missing ? 700 : 400 });
    // check box
    const cx = x + boxW + 30, cy = y + boxH / 2;
    b += `<rect x="${cx - 12}" y="${cy - 12}" width="24" height="24" rx="3" fill="#fff" stroke="${INK}" stroke-width="1.5"/>`;
    if (st.done) b += `<path d="M ${cx - 7} ${cy} l 5 6 l 10 -12" stroke="#1d6b3a" stroke-width="3.5" fill="none"/>`;
    if (st.time) b += text(cx + 22, cy + 5, st.time, { size: 13, anchor: 'start', fill: MUTED });
    if (i < steps.length - 1) {
      const ay = y + boxH;
      b += `<line x1="${x + boxW / 2}" y1="${ay + 2}" x2="${x + boxW / 2}" y2="${ay + gap - 4}" stroke="${MUTED}" stroke-width="2"/>`;
      b += `<path d="M ${x + boxW / 2 - 5} ${ay + gap - 9} l 5 7 l 5 -7 z" fill="${MUTED}"/>`;
    }
  });
  return svg(W, H, ev.title, b);
}

// ---------- Bar (grouped) ----------
export function bar(ev) {
  const { categories, series, yLabel, categoryNote } = ev.data;
  const W = 760, H = 420, L = 70, R = 20, T = 50, B = 80;
  const max = Math.max(1, ...series.flatMap((s) => s.values));
  const yMax = Math.ceil(max + 1);
  const pw = W - L - R, ph = H - T - B;
  const groupW = pw / categories.length;
  const barW = Math.min(46, (groupW * 0.7) / series.length);
  let b = '';
  for (let v = 0; v <= yMax; v++) {
    const y = T + ph - (v / yMax) * ph;
    b += `<line x1="${L}" y1="${y}" x2="${W - R}" y2="${y}" stroke="${GRID}"/>`;
    b += text(L - 10, y + 4, v, { size: 12, anchor: 'end', fill: MUTED });
  }
  categories.forEach((c, ci) => {
    const gx = L + ci * groupW + (groupW - barW * series.length) / 2;
    series.forEach((s, si) => {
      const v = s.values[ci];
      const h = (v / yMax) * ph;
      const x = gx + si * barW;
      b += `<rect x="${x + 2}" y="${T + ph - h}" width="${barW - 4}" height="${h}" fill="${SERIES[si % SERIES.length]}"/>`;
      b += text(x + barW / 2, T + ph - h - 6, v, { size: 12, weight: 700 });
    });
    b += text(L + ci * groupW + groupW / 2, T + ph + 20, c, { size: 13 });
  });
  b += `<line x1="${L}" y1="${T + ph}" x2="${W - R}" y2="${T + ph}" stroke="${INK}" stroke-width="1.5"/>`;
  b += text(18, T + ph / 2, yLabel, { size: 13, rotate: -90, fill: MUTED });
  b += text(L + pw / 2, T + ph + 42, 'Start of 10-minute block (PM)', { size: 13, fill: MUTED });
  if (categoryNote) b += text(L + pw / 2, H - 12, categoryNote, { size: 12, fill: MUTED });
  b += legend(series, L, 26);
  return svg(W, H, ev.title, b);
}

// ---------- Line ----------
export function line(ev) {
  const d = ev.data;
  const W = 760, H = 420, L = 70, R = 30, T = 50, B = 70;
  const pw = W - L - R, ph = H - T - B;
  const X = (x) => L + ((x - d.xMin) / (d.xMax - d.xMin)) * pw;
  const Y = (y) => T + ph - ((y - d.yMin) / (d.yMax - d.yMin)) * ph;
  const fmt = (x) => d.xFormat === 'minutesAfter3' ? `3:${String(x).padStart(2, '0')}` : x;
  let b = '';
  for (let y = d.yMin; y <= d.yMax; y += d.yStep) {
    b += `<line x1="${L}" y1="${Y(y)}" x2="${W - R}" y2="${Y(y)}" stroke="${GRID}"/>`;
    b += text(L - 10, Y(y) + 4, y, { size: 12, anchor: 'end', fill: MUTED });
  }
  for (let x = d.xMin; x <= d.xMax; x += d.xStep) {
    b += `<line x1="${X(x)}" y1="${T}" x2="${X(x)}" y2="${T + ph}" stroke="${GRID}" stroke-dasharray="3 4"/>`;
    b += text(X(x), T + ph + 20, fmt(x), { size: 13 });
  }
  // minor ticks every 2 minutes so readers can estimate times
  for (let x = d.xMin; x <= d.xMax; x += 2) b += `<line x1="${X(x)}" y1="${T + ph}" x2="${X(x)}" y2="${T + ph + 5}" stroke="${MUTED}"/>`;
  b += `<line x1="${L}" y1="${T + ph}" x2="${W - R}" y2="${T + ph}" stroke="${INK}" stroke-width="1.5"/>`;
  d.series.forEach((s, i) => {
    const pts = s.points.map(([x, y]) => `${X(x)},${Y(y)}`).join(' ');
    const dash = i === 1 ? ' stroke-dasharray="10 5"' : '';
    b += `<polyline points="${pts}" fill="none" stroke="${SERIES[i]}" stroke-width="3.5"${dash}/>`;
    s.points.forEach(([x, y]) => { b += `<circle cx="${X(x)}" cy="${Y(y)}" r="4" fill="${SERIES[i]}"/>`; });
  });
  b += text(18, T + ph / 2, d.yLabel, { size: 13, rotate: -90, fill: MUTED });
  b += text(L + pw / 2, H - 18, `${d.xLabel}. Small ticks = 2 minutes.`, { size: 13, fill: MUTED });
  b += legend(d.series, L, 26);
  return svg(W, H, ev.title, b);
}

// ---------- Pie ----------
export function pie(ev) {
  const { slices, total } = ev.data;
  const W = 640, H = 380, cx = 200, cy = 190, r = 150;
  let a0 = -Math.PI / 2, b = '';
  slices.forEach((s, i) => {
    const frac = s.value / total;
    const a1 = a0 + frac * Math.PI * 2;
    const large = frac > 0.5 ? 1 : 0;
    const p = (a) => `${cx + r * Math.cos(a)} ${cy + r * Math.sin(a)}`;
    b += `<path d="M ${cx} ${cy} L ${p(a0)} A ${r} ${r} 0 ${large} 1 ${p(a1)} Z" fill="${SERIES[i % SERIES.length]}" stroke="#fff" stroke-width="2"/>`;
    const am = (a0 + a1) / 2;
    b += text(cx + r * 0.62 * Math.cos(am), cy + r * 0.62 * Math.sin(am) + 5, `${Math.round(frac * 100)}%`, { size: 16, weight: 700, fill: '#ffffff' });
    const ly = 90 + i * 40;
    b += `<rect x="400" y="${ly - 14}" width="18" height="18" rx="3" fill="${SERIES[i % SERIES.length]}"/>`;
    b += text(428, ly, `${s.name}: ${s.value} votes`, { size: 15, anchor: 'start' });
    a0 = a1;
  });
  b += text(400, 90 + slices.length * 40 + 10, `Total: ${total} votes`, { size: 14, anchor: 'start', weight: 700 });
  return svg(W, H, ev.title, b);
}

const RENDERERS = { floorplan, table, flowchart, bar, line, pie };

export function renderGraphic(ev, room) {
  const fn = RENDERERS[ev.type];
  if (!fn) return `<p>Unknown graphic type: ${esc(ev.type)}</p>`;
  return fn(ev, room);
}

// Rasterise an SVG string to a canvas (used for in-world posters).
export function svgToCanvas(svgString, width = 1024) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const ratio = img.height / img.width || 0.75;
      const c = document.createElement('canvas');
      c.width = width; c.height = Math.round(width * ratio);
      const g = c.getContext('2d');
      g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
      g.drawImage(img, 0, 0, c.width, c.height);
      resolve(c);
    };
    img.onerror = () => resolve(null);
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgString);
  });
}
