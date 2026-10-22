// Builds the classroom. Two modes, chosen per piece:
//   1. Blender model (.glb) listed in data/assets.js, if the file exists.
//   2. A simple placeholder built from mystery.room, if it does not.
// So the game runs today, and each Blender file replaces its placeholder
// as soon as it is dropped into assets/models/.
//
// The placeholder room can be a suite: outside walls with doors, plus
// inside walls (room.walls) with walk-through openings, painted accent
// walls (room.paint) and real photo textures (data/assets.js > textures).

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const cache = new Map(); // url -> Promise<gltf|null>; callers clone the scene

export function loadGLB(url) {
  if (!url) return Promise.resolve(null);
  if (!cache.has(url)) {
    cache.set(url, loader.loadAsync(url).catch((e) => {
      console.info(`[assets] ${url} not loaded, using placeholder.`, e?.message || '');
      return null;
    }));
  }
  return cache.get(url);
}

const texLoader = new THREE.TextureLoader();
async function loadTexture(url) {
  if (!url) return null;
  try {
    const t = await texLoader.loadAsync(url);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.anisotropy = 4;
    return t;
  } catch (e) {
    console.info(`[assets] texture ${url} not loaded, using a plain colour.`);
    return null;
  }
}
function tiled(tex, rx, ry) {
  const t = tex.clone();
  t.repeat.set(rx, ry);
  t.needsUpdate = true;
  return t;
}

const mat = (color, opts = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.8, metalness: 0, ...opts });

// Colours measured from the real room photos.
const C = {
  wall: '#e3dcc6',      // cream painted block
  accent: '#8fa3c2',    // blue painted block
  frame: '#7d93b5',     // blue door frames
  base: '#3f5f99',      // blue rubber baseboard
  wood: '#a8763e',      // casework and doors
  top: '#4b4f4f',       // dark counter tops
  table: '#c9cccc',     // grey table tops
  chair: '#1c2533',     // navy chairs
  floor: '#ddd8cb'
};

const M = {
  trim: mat(C.frame),
  base: mat(C.base),
  ceiling: mat('#f4f4f2', { emissive: '#d9d8d2', emissiveIntensity: 0.55 }),   // lit tiles, like the photos
  wood: mat(C.wood),
  darkWood: mat('#6e4d31'),
  top: mat(C.top, { roughness: 0.5 }),
  tableTop: mat(C.table, { roughness: 0.5 }),
  chair: mat(C.chair, { roughness: 0.6 }),
  metal: mat('#9aa3ad', { metalness: 0.5, roughness: 0.4 }),
  black: mat('#1d1f22', { roughness: 0.5 }),
  white: mat('#fbfbfb', { roughness: 0.3 }),
  screen: mat('#0d0f12', { roughness: 0.2 }),
  glass: new THREE.MeshPhysicalMaterial({ color: '#cfe8ff', transparent: true, opacity: 0.25, roughness: 0.05 }),
  door: mat(C.wood),
  green: mat('#3f8f4f'),
  pot: mat('#b5643c'),
  bench: mat('#3b3f46'),
  gold: mat('#d4a73a', { metalness: 0.8, roughness: 0.3 }),
  light: new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#fffbe8', emissiveIntensity: 1 })
};

const BLOCK = 2.05;  // the block textures cover 2.05 m x 2.05 m
const TILE = 2.44;   // the floor texture covers 8 x 30.5 cm tiles

function box(w, h, d, material, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.set(x, y, z);
  return m;
}

// Rotation that turns an object built facing south (+z) to face `face`.
const FACE = { south: 0, east: Math.PI / 2, north: Math.PI, west: -Math.PI / 2 };

function textPlane(text, w, h, { bg = 'rgba(0,0,0,0)', fg = '#1f3b63', font = 'bold 120px Arial' } = {}) {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = Math.round(1024 * h / w);
  const x = c.getContext('2d');
  x.fillStyle = bg; x.fillRect(0, 0, c.width, c.height);
  x.fillStyle = fg; x.font = font; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(text, c.width / 2, c.height / 2 + 4);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: t, transparent: true }));
}

export class World {
  constructor(scene, mystery, assets) {
    this.scene = scene;
    this.mystery = mystery;
    this.assets = assets;
    this.room = mystery.room;
    this.colliders = [];        // { minX, maxX, minZ, maxZ }
    this.spawns = {};           // name -> THREE.Vector3 (from SPAWN_ empties in Blender)
    this.placeholder = new THREE.Group();
    this.placeholder.name = 'placeholder-room';
    scene.add(this.placeholder);
    this.usingRoomModel = false;
    this.tex = {};
  }

  async build() {
    await this.loadTextures();
    this.addLights();
    this.buildShell();
    await this.buildObjects();
    await this.loadRoomModel();
  }

  async loadTextures() {
    const t = this.assets.textures || {};
    const [wall, accent, floor, wood] = await Promise.all([t.wall, t.accent, t.floor, t.wood].map(loadTexture));
    this.tex = { wall, accent, floor, wood };
  }

  // A material for a wall surface len x height, tiled with a block texture.
  surface(kind, len, height) {
    const tex = this.tex[kind];
    const color = kind === 'accent' ? C.accent : C.wall;
    if (!tex) return mat(color, { roughness: 0.9 });
    return new THREE.MeshStandardMaterial({ map: tiled(tex, len / BLOCK, height / BLOCK), roughness: 0.9 });
  }

  addLights() {
    this.scene.add(new THREE.HemisphereLight('#ffffff', '#b8ad98', 1.6));
    const sun = new THREE.DirectionalLight('#fff6e0', 1.2);
    sun.position.set(-14, 10, 4);
    this.scene.add(sun);
    this.scene.add(new THREE.AmbientLight('#ffffff', 0.4));
  }

  addCollider(minX, maxX, minZ, maxZ) { this.colliders.push({ minX, maxX, minZ, maxZ }); }

  // ---------- walls, floor, ceiling ----------
  buildShell() {
    const { width: W, depth: D, height: H } = this.room;
    const g = this.placeholder;
    const floorMat = this.tex.floor
      ? new THREE.MeshStandardMaterial({ map: tiled(this.tex.floor, W / TILE, D / TILE), roughness: 0.35 })
      : mat(C.floor, { roughness: 0.4 });
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(W, D), floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(W, D), M.ceiling);
    ceil.rotation.x = Math.PI / 2;
    ceil.position.y = H;
    g.add(ceil);
    // 2 x 4 ft ceiling light panels
    for (let x = -9; x <= 9; x += 3.6) for (let z = -6; z <= 6; z += 3) g.add(box(1.22, 0.04, 0.61, M.light, x, H - 0.03, z));

    const T = 0.2; // outside wall thickness
    const outer = [
      { name: 'north', axis: 'x', fixed: -D / 2 - T / 2, from: -W / 2, to: W / 2, inward: 1 },
      { name: 'south', axis: 'x', fixed: D / 2 + T / 2, from: -W / 2, to: W / 2, inward: -1 },
      { name: 'west', axis: 'z', fixed: -W / 2 - T / 2, from: -D / 2, to: D / 2, inward: 1 },
      { name: 'east', axis: 'z', fixed: W / 2 + T / 2, from: -D / 2, to: D / 2, inward: -1 }
    ];
    for (const w of outer) {
      const gaps = this.room.doors.filter((d) => d.wall === w.name)
        .map((d) => ({ a: d.at - d.width / 2, b: d.at + d.width / 2, door: d }));
      this.wallLine({ ...w, T, gaps });
    }

    // Inside walls: straight, axis-aligned, with walk-through openings.
    for (const iw of this.room.walls || []) {
      const [x1, z1] = iw.from, [x2, z2] = iw.to;
      const axis = Math.abs(z1 - z2) < 1e-6 ? 'x' : 'z';
      const fixed = axis === 'x' ? z1 : x1;
      const from = axis === 'x' ? Math.min(x1, x2) : Math.min(z1, z2);
      const to = axis === 'x' ? Math.max(x1, x2) : Math.max(z1, z2);
      const gaps = (iw.openings || []).map((o) => ({ a: o.at - o.width / 2, b: o.at + o.width / 2, opening: o }));
      this.wallLine({ axis, fixed, from, to, T: iw.thickness || 0.15, gaps, inward: 0 });
    }

    // Painted accent walls: a thin textured layer on the inside face.
    for (const p of this.room.paint || []) {
      const len = p.to - p.from, mid = (p.from + p.to) / 2;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(len, H), this.surface('accent', len, H));
      const off = 0.006;
      if (p.wall === 'east') { m.position.set(W / 2 - off, H / 2, mid); m.rotation.y = -Math.PI / 2; }
      else if (p.wall === 'west') { m.position.set(-W / 2 + off, H / 2, mid); m.rotation.y = Math.PI / 2; }
      else if (p.wall === 'north') { m.position.set(mid, H / 2, -D / 2 + off); }
      else { m.position.set(mid, H / 2, D / 2 - off); m.rotation.y = Math.PI; }
      g.add(m);
    }

    // Paper pennant banners along the top of the walls.
    if (this.room.bunting) this.addBunting(this.room.bunting);

    // Windows (optional): bright panels on the inside of the wall
    if (this.room.windows) {
      const w = this.room.windows;
      const len = w.to - w.from;
      const win = new THREE.Mesh(new THREE.PlaneGeometry(len, 1.4), new THREE.MeshStandardMaterial({ color: '#cfe6ff', emissive: '#9cc8f0', emissiveIntensity: 0.6 }));
      win.position.set(-W / 2 + 0.01, 1.8, (w.from + w.to) / 2);
      win.rotation.y = Math.PI / 2;
      g.add(win);
    }
  }

  // One straight wall with gaps. A gap is a closed outside door (blocked,
  // labelled) or an inside opening (open, you can walk through).
  wallLine({ axis, fixed, from, to, T, gaps, inward }) {
    const H = this.room.height;
    const g = this.placeholder;
    const seg = (a, b, y0, y1) => {
      const len = b - a, mid = (a + b) / 2, h = y1 - y0;
      const m = axis === 'x'
        ? box(len, h, T, this.surface('wall', len, h), mid, (y0 + y1) / 2, fixed)
        : box(T, h, len, this.surface('wall', len, h), fixed, (y0 + y1) / 2, mid);
      g.add(m);
      return m;
    };
    const along = (a, b, y0, y1, thick, material, offset = 0) => {
      const len = b - a, mid = (a + b) / 2, h = y1 - y0;
      return axis === 'x'
        ? box(len, h, thick, material, mid, (y0 + y1) / 2, fixed + offset)
        : box(thick, h, len, material, fixed + offset, (y0 + y1) / 2, mid);
    };
    gaps.sort((p, q) => p.a - q.a);
    let cursor = from;
    const solid = [];
    for (const gp of gaps) { solid.push([cursor, gp.a]); cursor = gp.b; }
    solid.push([cursor, to]);
    for (const [a, b] of solid) {
      if (b - a <= 0.01) continue;
      seg(a, b, 0, H);
      // blue rubber baseboard on both faces
      g.add(along(a, b, 0, 0.1, T + 0.03, M.base));
      if (axis === 'x') this.addCollider(a, b, fixed - T, fixed + T);
      else this.addCollider(fixed - T, fixed + T, a, b);
    }
    for (const gp of gaps) {
      const headH = 2.2;
      seg(gp.a, gp.b, headH, H);
      // blue frame: two jambs and a head, on both faces
      g.add(along(gp.a - 0.05, gp.a, 0, headH + 0.05, T + 0.06, M.trim));
      g.add(along(gp.b, gp.b + 0.05, 0, headH + 0.05, T + 0.06, M.trim));
      g.add(along(gp.a - 0.05, gp.b + 0.05, headH, headH + 0.05, T + 0.06, M.trim));
      if (gp.door) {
        // closed wooden door just inside the wall line, so it reads as a door
        g.add(along(gp.a + 0.02, gp.b - 0.02, 0, 2.15, 0.05, M.door, inward * (T / 2 + 0.01)));
        if (axis === 'x') this.addCollider(gp.a, gp.b, fixed - T, fixed + T);
        else this.addCollider(fixed - T, fixed + T, gp.a, gp.b);
        this.addSign(gp.door, axis, fixed, inward, T);
      }
    }
  }

  addSign(d, axis, fixed, inward, T) {
    const sign = textPlane(d.label, 1.4, 0.35, { bg: '#1f3b63', fg: '#ffffff', font: 'bold 150px Arial' });
    const pos = fixed + inward * (T / 2 + 0.03);
    if (axis === 'x') {
      sign.position.set(d.at, 2.55, pos);
      sign.rotation.y = inward > 0 ? 0 : Math.PI;
    } else {
      sign.position.set(pos, 2.55, d.at);
      sign.rotation.y = inward > 0 ? Math.PI / 2 : -Math.PI / 2;
    }
    this.placeholder.add(sign);
  }

  // runs: [{ from:[x,z], to:[x,z], side: 1 | -1 }] - side is the offset
  // direction away from the wall (+1 = towards +x or +z).
  addBunting(runs) {
    const colors = ['#e94b3c', '#f2c12e', '#3b7dd8', '#4caf50', '#e86fa5', '#7b5bc4'].map((c) => new THREE.Color(c));
    const pos = [], col = [];
    let k = 0;
    for (const r of runs) {
      const [x1, z1] = r.from, [x2, z2] = r.to;
      const len = Math.hypot(x2 - x1, z2 - z1);
      const ux = (x2 - x1) / len, uz = (z2 - z1) / len;
      const nx = Math.abs(ux) < 0.5 ? r.side : 0, nz = Math.abs(ux) < 0.5 ? 0 : r.side;
      const off = 0.04, size = 0.26, gap = 0.55, top = 2.95;
      for (let s = 0.3; s + size < len; s += gap) {
        const sag = Math.sin(((s % 2.2) / 2.2) * Math.PI) * 0.12;
        const ax = x1 + ux * s + nx * off, az = z1 + uz * s + nz * off;
        const bx = ax + ux * size, bz = az + uz * size;
        const tx = ax + ux * size / 2, tz = az + uz * size / 2;
        pos.push(ax, top - sag, az, bx, top - sag, bz, tx, top - sag - 0.3, tz);
        const c = colors[k++ % colors.length];
        for (let i = 0; i < 3; i++) col.push(c.r, c.g, c.b);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    geo.computeVertexNormals();
    this.placeholder.add(new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: 0.9 })));
  }

  // ---------- furniture ----------
  async buildObjects() {
    const overrides = this.assets.objects || {};
    for (const o of this.room.objects) {
      const spec = overrides[o.id] || overrides[o.type];
      let node = null;
      if (spec?.url) {
        const gltf = await loadGLB(spec.url);
        if (gltf) {
          node = gltf.scene.clone(true);
          if (spec.scale) node.scale.setScalar(spec.scale);
          node.rotation.y = (spec.rotationY || 0) + (FACE[o.face] ?? 0);
          node.position.set(o.x, spec.yOffset || 0, o.z);
          this.scene.add(node);
        }
      }
      if (!node) {
        node = this.placeholderObject(o);
        node.rotation.y = FACE[o.face] ?? 0;
        node.position.set(o.x, 0, o.z);
        this.placeholder.add(node);
      }
      if (o.collide) this.addCollider(o.x - o.w / 2, o.x + o.w / 2, o.z - o.d / 2, o.z + o.d / 2);
    }
  }

  // Each placeholder is built facing south (+z, its front towards +z) and
  // then turned to o.face. w and d in the data are the footprint in the
  // room (x and z), so they swap for objects that face east or west.
  placeholderObject(o) {
    const g = new THREE.Group();
    const sideways = o.face === 'east' || o.face === 'west';
    const w = sideways ? o.d : o.w, d = sideways ? o.w : o.d, h = o.h;
    const woodMat = this.tex.wood ? new THREE.MeshStandardMaterial({ map: tiled(this.tex.wood, Math.max(1, Math.round(w / 1.2)), 1), roughness: 0.6 }) : M.wood;
    switch (o.type) {
      case 'table': {
        g.add(box(w, 0.04, d, M.tableTop, 0, h, 0));
        for (const sx of [-1, 1]) for (const sz of [-1, 1]) g.add(box(0.04, h, 0.04, M.metal, sx * (w / 2 - 0.08), h / 2, sz * (d / 2 - 0.08)));
        // two navy chairs on the south side
        for (const cx of [-w / 4, w / 4]) {
          g.add(box(0.44, 0.05, 0.42, M.chair, cx, 0.45, d / 2 + 0.35));
          g.add(box(0.44, 0.4, 0.05, M.chair, cx, 0.72, d / 2 + 0.57));
          for (const sx of [-1, 1]) for (const sz of [-1, 1]) g.add(box(0.025, 0.45, 0.025, M.metal, cx + sx * 0.18, 0.225, d / 2 + 0.35 + sz * 0.18));
        }
        break;
      }
      case 'desk':
        g.add(box(w, 0.05, d, M.tableTop, 0, h, 0));
        g.add(box(w * 0.35, h - 0.05, d - 0.05, M.metal, w * 0.3, (h - 0.05) / 2, 0));
        g.add(box(w, h * 0.6, 0.03, M.metal, 0, h * 0.6, -d / 2 + 0.02));
        for (const sx of [-1]) g.add(box(0.04, h, d - 0.05, M.metal, sx * (w / 2 - 0.03), h / 2, 0));
        break;
      case 'board':
        g.add(box(w, h, 0.03, M.white, 0, (o.y || 1) + h / 2, 0));
        g.add(box(w + 0.08, 0.04, 0.1, M.metal, 0, (o.y || 1), 0.04));
        break;
      case 'counter': {
        // wood base cabinets, dark top, optional upper cabinets and plants
        g.add(box(w, h - 0.04, d - 0.04, woodMat, 0, (h - 0.04) / 2, 0.02));
        g.add(box(w + 0.02, 0.04, d, M.top, 0, h - 0.02, 0));
        if (o.uppers) g.add(box(w, 0.75, 0.35, woodMat, 0, 1.85, -d / 2 + 0.175));
        for (const px of o.plants || []) {
          g.add(box(0.22, 0.2, 0.22, M.pot, px, h + 0.1, 0));
          const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.2, 10, 8), M.green);
          leaf.position.set(px, h + 0.36, 0);
          g.add(leaf);
        }
        break;
      }
      case 'tallcab':
        g.add(box(w, h, d, woodMat, 0, h / 2, 0));
        break;
      case 'tv':
        g.add(box(w, w * 0.56, 0.06, M.screen, 0, 1.55, 0));
        for (const sx of [-1, 1]) g.add(box(0.05, 1.3, 0.05, M.white, sx * w * 0.35, 0.65, -0.1));
        g.add(box(w * 0.8, 0.05, d, M.white, 0, 0.05, -0.1));
        break;
      case 'computers': {
        g.add(box(w, 0.04, d, woodMat, 0, h, 0));
        for (const sx of [-1, 1]) g.add(box(0.05, h, d - 0.05, M.wood, sx * (w / 2 - 0.03), h / 2, 0));
        for (let x = -w / 2 + 0.7; x < w / 2 - 0.3; x += 1.4) {
          g.add(box(0.55, 0.34, 0.03, M.screen, x, h + 0.33, -d / 2 + 0.2));
          g.add(box(0.06, 0.16, 0.06, M.black, x, h + 0.1, -d / 2 + 0.18));
          g.add(box(0.2, 0.4, 0.42, M.black, x + 0.45, h + 0.2, -d / 2 + 0.25));
          g.add(box(0.44, 0.05, 0.42, M.chair, x, 0.48, d / 2 + 0.3));
          g.add(box(0.44, 0.4, 0.05, M.chair, x, 0.75, d / 2 + 0.5));
        }
        break;
      }
      case 'filing':
        g.add(box(w, h, d, M.black, 0, h / 2, 0));
        for (let y = 0.3; y < h; y += 0.33) g.add(box(0.12, 0.03, 0.02, M.metal, 0, y, d / 2 + 0.01));
        break;
      case 'bookshelf':
        g.add(box(w, h, 0.03, M.black, 0, h / 2, -d / 2 + 0.015));
        for (const sx of [-1, 1]) g.add(box(0.03, h, d, M.black, sx * (w / 2 - 0.015), h / 2, 0));
        for (let y = 0.02; y <= h; y += h / 4) g.add(box(w, 0.03, d, M.black, 0, y, 0));
        break;
      case 'easel': {
        // rolling whiteboard covered with sticky notes
        g.add(box(w, 1.05, 0.04, M.white, 0, 1.55, 0));
        for (const sx of [-1, 1]) g.add(box(0.05, 2.05, 0.05, M.white, sx * (w / 2 + 0.02), 1.03, 0));
        g.add(box(w + 0.1, 0.05, d, M.white, 0, 0.12, 0));
        const notes = ['#ffe45c', '#ffb3d9', '#8fd3ff', '#b8f28a'];
        for (let i = 0; i < 26; i++) {
          const nx = -w / 2 + 0.15 + ((i * 37) % 100) / 100 * (w - 0.3), ny = 1.15 + ((i * 53) % 100) / 100 * 0.8;
          g.add(box(0.075, 0.075, 0.005, mat(notes[i % 4]), nx, ny, 0.025));
        }
        break;
      }
      case 'sink':
        g.add(box(w, h - 0.04, d - 0.04, M.metal, 0, (h - 0.04) / 2, 0));
        g.add(box(w, 0.04, d, M.top, 0, h - 0.02, 0));
        g.add(box(w * 0.5, 0.02, d * 0.6, M.metal, 0, h + 0.005, 0.05));
        break;
      case 'sign': {
        const s = textPlane(o.text || '', w, 0.35, { fg: '#1f3b63', font: 'bold 170px Arial' });
        s.position.set(0, o.y || 2.4, 0.01);
        g.add(s);
        break;
      }
      case 'case': {
        // frame, glass front, three shelves. Shelf 1 (top) is empty: that's the mystery.
        g.add(box(w, 0.1, d, M.darkWood, 0, 0.05, 0));
        g.add(box(w, 0.08, d, M.darkWood, 0, h - 0.04, 0));
        g.add(box(w, h, 0.05, M.darkWood, 0, h / 2, -d / 2 + 0.03));
        for (const sx of [-1, 1]) g.add(box(0.05, h, d, M.darkWood, sx * (w / 2 - 0.03), h / 2, 0));
        g.add(box(w - 0.05, h - 0.2, 0.02, M.glass, 0, h / 2, d / 2 - 0.02));
        for (const y of [0.55, 1.0, 1.45]) g.add(box(w - 0.1, 0.03, d - 0.1, M.glass, 0, y, 0));
        g.add(box(0.3, 0.02, 0.3, mat('#222'), 0, 1.475, 0));          // sensor pad, top shelf
        for (const x of [-0.6, -0.2, 0.2, 0.6]) {                         // medals, middle shelf
          const medal = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.02, 16), M.gold);
          medal.rotation.x = Math.PI / 2; medal.position.set(x, 1.12, -d / 2 + 0.1);
          g.add(medal);
        }
        for (const x of [-0.5, 0.5]) {                                     // small trophies, bottom shelf
          const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.04, 0.18, 12), M.gold);
          cup.position.set(x, 0.68, 0);
          g.add(cup);
        }
        break;
      }
      case 'bench': {
        // yearbook layout table: page proofs spread out, a camera, a cutting mat
        g.add(box(w, 0.06, d, M.bench, 0, h, 0));
        g.add(box(w - 0.1, h - 0.06, d - 0.1, mat('#5b616b'), 0, (h - 0.06) / 2, 0));
        g.add(box(0.9, 0.005, 0.6, mat('#3f7d5a'), 0.9, h + 0.033, 0));            // cutting mat
        const proof = mat('#fbfbf6'), photo = [mat('#6a8fbf'), mat('#c98a5a'), mat('#7aa36b'), mat('#b5687d')];
        for (let i = 0; i < 6; i++) {
          const px = -1.25 + (i % 3) * 0.42, pz = -0.2 + Math.floor(i / 3) * 0.36;
          g.add(box(0.36, 0.004, 0.28, proof, px, h + 0.034 + i * 0.001, pz));      // proof page
          g.add(box(0.15, 0.002, 0.11, photo[i % 4], px - 0.07, h + 0.04 + i * 0.001, pz - 0.05));
          g.add(box(0.12, 0.002, 0.09, photo[(i + 1) % 4], px + 0.09, h + 0.04 + i * 0.001, pz + 0.06));
        }
        g.add(box(0.14, 0.09, 0.07, M.black, 0.6, h + 0.075, -0.25));              // camera body
        const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.07, 16), M.black);
        lens.rotation.x = Math.PI / 2; lens.position.set(0.6, h + 0.075, -0.19);
        g.add(lens);
        break;
      }
      case 'cabinet':
        g.add(box(w, h, d, mat('#c4c7cb'), 0, h / 2, 0));
        g.add(box(0.01, h - 0.1, 0.02, M.metal, 0, h / 2, d / 2 + 0.01));
        break;
      case 'cart':
        g.add(box(w, 0.04, d, M.metal, 0, 0.35, 0));
        g.add(box(w, 0.04, d, M.metal, 0, 0.9, 0));
        for (let i = 0; i < 8; i++) g.add(box(0.06, 0.24, 0.18, mat(['#a33', '#36a', '#3a6', '#a83'][i % 4]), -w / 2 + 0.1 + i * 0.13, 1.04, 0));
        break;
      default:
        g.add(box(w, h, d, mat('#cccccc'), 0, h / 2, 0));
    }
    return g;
  }


  // Wall poster with an evidence graphic (canvas) on it.
  // Real photos (data/assets.js > pictures). x / y are Blender floor
  // coordinates (Blender Y = -world z); height is the centre above the floor.
  // A missing file is skipped.
  async addPicture(p) {
    const img = new Image();
    const ok = await new Promise((res) => { img.onload = () => res(true); img.onerror = () => res(false); img.src = p.url; });
    if (!ok) { console.info(`[assets] picture ${p.url} not loaded, skipped.`); return; }
    const c = document.createElement('canvas');
    const max = 1024, s = Math.min(1, max / Math.max(img.width, img.height));
    c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    this.addPoster(c, p.x ?? 0, -(p.y ?? 0), p.wall, p.width || 1.2, p.height || 1.6);
  }

  addPoster(canvas, x, z, wall, width = 1.2, y = 1.6) {
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    const h = width * (canvas.height / canvas.width);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(width, h), new THREE.MeshBasicMaterial({ map: tex }));
    const off = 0.02;
    const W = this.room.width / 2, D = this.room.depth / 2;
    if (wall === 'south') { m.position.set(x, y, D - off); m.rotation.y = Math.PI; }
    else if (wall === 'north') { m.position.set(x, y, -D + off); }
    else if (wall === 'east') { m.position.set(W - off, y, z); m.rotation.y = -Math.PI / 2; }
    else { m.position.set(-W + off, y, z); m.rotation.y = Math.PI / 2; }
    const frame = box(width + 0.08, h + 0.08, 0.02, M.trim);
    frame.position.copy(m.position); frame.rotation.copy(m.rotation);
    frame.translateZ(-0.012);
    this.scene.add(frame, m);
  }

  // ---------- full classroom from Blender ----------
  async loadRoomModel() {
    const spec = this.assets.room;
    if (!spec?.url) return;
    const gltf = await loadGLB(spec.url);
    if (!gltf) return;
    const root = gltf.scene;
    if (spec.scale) root.scale.setScalar(spec.scale);
    if (spec.position) root.position.set(...spec.position);
    if (spec.rotationY) root.rotation.y = spec.rotationY;
    this.scene.add(root);
    root.updateMatrixWorld(true);

    const cols = [];
    root.traverse((n) => {
      const name = n.name || '';
      if (/^COL_/i.test(name) && n.isMesh) {
        const b = new THREE.Box3().setFromObject(n);
        cols.push({ minX: b.min.x, maxX: b.max.x, minZ: b.min.z, maxZ: b.max.z });
        n.visible = false;
      } else if (/^SPAWN_/i.test(name)) {
        this.spawns[name.slice(6).toLowerCase()] = n.getWorldPosition(new THREE.Vector3());
      }
    });
    this.usingRoomModel = true;
    if (spec.hidePlaceholder !== false) this.placeholder.visible = false;
    // COL_ boxes from Blender replace the placeholder walls/furniture colliders.
    if (cols.length) this.colliders = cols;
    console.info(`[assets] classroom model loaded: ${cols.length} colliders, spawns: ${Object.keys(this.spawns).join(', ') || 'none'}`);
  }
}
