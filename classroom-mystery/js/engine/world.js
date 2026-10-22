// Builds the classroom. Two modes, chosen per piece:
//   1. Blender model (.glb) listed in data/assets.js, if the file exists.
//   2. A simple placeholder built from mystery.room, if it does not.
// So the game runs today, and each Blender file replaces its placeholder
// as soon as it is dropped into assets/models/.

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

const mat = (color, opts = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.8, metalness: 0, ...opts });

const M = {
  floor: null,
  wall: mat('#e9e4d8'),
  trim: mat('#8c7a5f'),
  ceiling: mat('#f4f4f2'),
  wood: mat('#b88a5a'),
  darkWood: mat('#6e4d31'),
  metal: mat('#9aa3ad', { metalness: 0.5, roughness: 0.4 }),
  blue: mat('#3d6fb4'),
  white: mat('#fbfbfb', { roughness: 0.3 }),
  glass: new THREE.MeshPhysicalMaterial({ color: '#cfe8ff', transparent: true, opacity: 0.25, roughness: 0.05 }),
  door: mat('#5a7da8'),
  green: mat('#3f8f4f'),
  pot: mat('#b5643c'),
  bench: mat('#3b3f46'),
  gold: mat('#d4a73a', { metalness: 0.8, roughness: 0.3 }),
  light: new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#fffbe8', emissiveIntensity: 1 })
};

function floorTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    g.fillStyle = (i + j) % 2 ? '#d8d2c4' : '#cfc8b8';
    g.fillRect(i * 64, j * 64, 64, 64);
  }
  g.strokeStyle = 'rgba(0,0,0,0.08)';
  for (let i = 0; i <= 4; i++) { g.beginPath(); g.moveTo(i * 64, 0); g.lineTo(i * 64, 256); g.moveTo(0, i * 64); g.lineTo(256, i * 64); g.stroke(); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function box(w, h, d, material, x = 0, y = 0, z = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.set(x, y, z);
  return m;
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
  }

  async build() {
    this.addLights();
    this.buildShell();
    await this.buildObjects();
    await this.loadRoomModel();
  }

  addLights() {
    this.scene.add(new THREE.HemisphereLight('#ffffff', '#b8ad98', 1.6));
    const sun = new THREE.DirectionalLight('#fff6e0', 1.4);
    sun.position.set(-14, 10, 4);
    this.scene.add(sun);
    this.scene.add(new THREE.AmbientLight('#ffffff', 0.35));
  }

  addCollider(minX, maxX, minZ, maxZ) { this.colliders.push({ minX, maxX, minZ, maxZ }); }

  // ---------- walls, floor, ceiling ----------
  buildShell() {
    const { width: W, depth: D, height: H } = this.room;
    const g = this.placeholder;
    const ft = floorTexture();
    ft.repeat.set(W / 2, D / 2);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(W, D), mat('#ffffff', { map: ft }));
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(W, D), M.ceiling);
    ceil.rotation.x = Math.PI / 2;
    ceil.position.y = H;
    g.add(ceil);
    // ceiling light panels
    for (let x = -8; x <= 8; x += 4) for (let z = -5; z <= 5; z += 5) {
      const p = box(1.2, 0.04, 0.6, M.light, x, H - 0.03, z);
      g.add(p);
    }

    const T = 0.2; // wall thickness
    const walls = {
      north: { axis: 'x', fixed: -D / 2 - T / 2, len: W },
      south: { axis: 'x', fixed: D / 2 + T / 2, len: W },
      west: { axis: 'z', fixed: -W / 2 - T / 2, len: D },
      east: { axis: 'z', fixed: W / 2 + T / 2, len: D }
    };
    for (const [name, wdef] of Object.entries(walls)) {
      const doors = this.room.doors.filter((d) => d.wall === name).sort((a, b) => a.at - b.at);
      const gaps = doors.map((d) => [d.at - d.width / 2, d.at + d.width / 2]);
      if (this.room.windows && this.room.windows.wall === name) gaps.push(['win', this.room.windows.from, this.room.windows.to]);
      let cursor = -wdef.len / 2;
      const segs = [];
      const doorGaps = gaps.filter((x) => x[0] !== 'win');
      for (const [a, b] of doorGaps) { segs.push([cursor, a]); cursor = b; }
      segs.push([cursor, wdef.len / 2]);
      for (const [a, b] of segs) {
        if (b - a <= 0.01) continue;
        const mid = (a + b) / 2, len = b - a;
        const m = wdef.axis === 'x'
          ? box(len, H, T, M.wall, mid, H / 2, wdef.fixed)
          : box(T, H, len, M.wall, wdef.fixed, H / 2, mid);
        g.add(m);
        if (wdef.axis === 'x') this.addCollider(a, b, wdef.fixed - T, wdef.fixed + T);
        else this.addCollider(wdef.fixed - T, wdef.fixed + T, a, b);
      }
      // door frames, lintels and door leaves
      for (const d of doors) {
        const lintelH = H - 2.2;
        const lintel = wdef.axis === 'x'
          ? box(d.width, lintelH, T, M.wall, d.at, 2.2 + lintelH / 2, wdef.fixed)
          : box(T, lintelH, d.width, M.wall, wdef.fixed, 2.2 + lintelH / 2, d.at);
        g.add(lintel);
        // closed door just outside the wall line, so it reads as a door
        const leaf = wdef.axis === 'x'
          ? box(d.width - 0.05, 2.15, 0.06, M.door, d.at, 1.075, wdef.fixed + Math.sign(wdef.fixed) * 0.02)
          : box(0.06, 2.15, d.width - 0.05, M.door, wdef.fixed + Math.sign(wdef.fixed) * 0.02, 1.075, d.at);
        g.add(leaf);
        // the door is closed: block it
        if (wdef.axis === 'x') this.addCollider(d.at - d.width / 2, d.at + d.width / 2, wdef.fixed - T, wdef.fixed + T);
        else this.addCollider(wdef.fixed - T, wdef.fixed + T, d.at - d.width / 2, d.at + d.width / 2);
        this.addSign(d, wdef);
      }
    }
    // windows: bright panels on the inside of the wall
    if (this.room.windows) {
      const w = this.room.windows;
      const len = w.to - w.from;
      const win = new THREE.Mesh(new THREE.PlaneGeometry(len, 1.4), new THREE.MeshStandardMaterial({ color: '#cfe6ff', emissive: '#9cc8f0', emissiveIntensity: 0.6 }));
      win.position.set(-W / 2 + 0.01, 1.8, (w.from + w.to) / 2);
      win.rotation.y = Math.PI / 2;
      g.add(win);
    }
  }

  addSign(d, wdef) {
    const c = document.createElement('canvas');
    c.width = 512; c.height = 128;
    const x = c.getContext('2d');
    x.fillStyle = '#1f3b63'; x.fillRect(0, 0, 512, 128);
    x.fillStyle = '#fff'; x.font = 'bold 56px Arial'; x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillText(d.label, 256, 66);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
    const sign = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.35), new THREE.MeshBasicMaterial({ map: t }));
    const inset = 0.12;
    if (wdef.axis === 'x') {
      sign.position.set(d.at, 2.5, wdef.fixed - Math.sign(wdef.fixed) * inset);
      sign.rotation.y = wdef.fixed > 0 ? Math.PI : 0;
    } else {
      sign.position.set(wdef.fixed - Math.sign(wdef.fixed) * inset, 2.5, d.at);
      sign.rotation.y = wdef.fixed > 0 ? -Math.PI / 2 : Math.PI / 2;
    }
    this.placeholder.add(sign);
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
          node.rotation.y = spec.rotationY || 0;
          node.position.set(o.x, spec.yOffset || 0, o.z);
          this.scene.add(node);
        }
      }
      if (!node) {
        node = this.placeholderObject(o);
        node.position.x += o.x;
        node.position.z += o.z;
        this.placeholder.add(node);
      }
      if (o.collide) this.addCollider(o.x - o.w / 2, o.x + o.w / 2, o.z - o.d / 2, o.z + o.d / 2);
    }
  }

  placeholderObject(o) {
    const g = new THREE.Group();
    const { w, d, h } = o;
    switch (o.type) {
      case 'table': {
        g.add(box(w, 0.05, d, M.wood, 0, h, 0));
        for (const sx of [-1, 1]) for (const sz of [-1, 1]) g.add(box(0.05, h, 0.05, M.metal, sx * (w / 2 - 0.08), h / 2, sz * (d / 2 - 0.08)));
        // two chairs on the south side
        for (const cx of [-w / 4, w / 4]) {
          g.add(box(0.42, 0.04, 0.42, M.blue, cx, 0.45, d / 2 + 0.35));
          g.add(box(0.42, 0.45, 0.04, M.blue, cx, 0.7, d / 2 + 0.56));
          for (const sx of [-1, 1]) for (const sz of [-1, 1]) g.add(box(0.03, 0.45, 0.03, M.metal, cx + sx * 0.18, 0.225, d / 2 + 0.35 + sz * 0.18));
        }
        break;
      }
      case 'desk':
        g.add(box(w, 0.06, d, M.darkWood, 0, h, 0));
        g.add(box(w, h - 0.06, 0.05, M.darkWood, 0, (h - 0.06) / 2, -d / 2 + 0.03));
        g.add(box(0.05, h, d, M.darkWood, -w / 2 + 0.03, h / 2, 0));
        g.add(box(0.05, h, d, M.darkWood, w / 2 - 0.03, h / 2, 0));
        break;
      case 'board':
        g.add(box(w, h, 0.04, M.white, 0, (o.y || 1) + h / 2, 0));
        g.add(box(w + 0.1, 0.05, 0.12, M.trim, 0, (o.y || 1), 0.04));
        break;
      case 'closet':
        g.add(box(w, h, d, mat('#d9d2c2'), 0, h / 2, 0));
        g.add(box(0.05, 2.1, 1.0, M.door, w / 2 + 0.02, 1.05, 0));
        break;
      case 'shelf':
        g.add(box(w, h, d, M.wood, 0, h / 2, 0));
        for (let i = -d / 2 + 0.4; i < d / 2; i += 0.7) {
          g.add(box(0.25, 0.22, 0.25, M.pot, 0, h + 0.11, i));
          const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 8), M.green);
          leaf.position.set(0, h + 0.38, i);
          g.add(leaf);
        }
        break;
      case 'case': {
        // frame, glass, three shelves. Shelf 1 (top) is empty: that's the mystery.
        g.add(box(w, 0.1, d, M.darkWood, 0, 0.05, 0));
        g.add(box(w, 0.08, d, M.darkWood, 0, h - 0.04, 0));
        g.add(box(0.05, h, d, M.darkWood, w / 2 - 0.03, h / 2, 0));
        const glass = box(0.02, h - 0.2, d - 0.05, M.glass, -w / 2 + 0.02, h / 2, 0);
        g.add(glass);
        for (const y of [0.55, 1.0, 1.45]) g.add(box(w - 0.1, 0.03, d - 0.1, M.glass, 0, y, 0));
        // sensor pad on the empty top shelf
        g.add(box(0.3, 0.02, 0.3, mat('#222'), 0, 1.475, 0));
        // ribbons / medals on shelf 2
        for (const z of [-0.6, -0.2, 0.2, 0.6]) {
          const medal = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.02, 16), M.gold);
          medal.rotation.z = Math.PI / 2; medal.position.set(0, 1.12, z);
          g.add(medal);
        }
        // small trophies on the bottom shelf
        for (const z of [-0.5, 0.5]) {
          const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.04, 0.18, 12), M.gold);
          cup.position.set(0, 0.68, z);
          g.add(cup);
        }
        break;
      }
      case 'bench':
        g.add(box(w, 0.06, d, M.bench, 0, h, 0));
        g.add(box(w - 0.1, h - 0.06, d - 0.1, mat('#5b616b'), 0, (h - 0.06) / 2, 0));
        // robot parts
        g.add(box(0.4, 0.25, 0.4, mat('#c9372c'), -0.8, h + 0.125, 0));
        g.add(box(0.6, 0.12, 0.3, M.metal, 0.5, h + 0.06, 0.1));
        break;
      case 'cabinet':
        g.add(box(w, h, d, mat('#7d8793'), 0, h / 2, 0));
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
  addPoster(canvas, x, z, wall, width = 1.2) {
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    const h = width * (canvas.height / canvas.width);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(width, h), new THREE.MeshBasicMaterial({ map: tex }));
    const off = 0.02;
    const W = this.room.width / 2, D = this.room.depth / 2;
    if (wall === 'south') { m.position.set(x, 1.6, D - off); m.rotation.y = Math.PI; }
    else if (wall === 'north') { m.position.set(x, 1.6, -D + off); }
    else if (wall === 'east') { m.position.set(W - off, 1.6, z); m.rotation.y = -Math.PI / 2; }
    else { m.position.set(-W + off, 1.6, z); m.rotation.y = Math.PI / 2; }
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
