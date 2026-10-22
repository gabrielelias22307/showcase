// First-person player: keyboard to move, drag to look, touch joystick on
// phones/tablets. Collides with axis-aligned boxes from the World.

import * as THREE from 'three';

const EYE = 1.6;
const RADIUS = 0.3;
const SPEED = 3.2;
const TURN = 2.2; // rad/s for arrow keys

export class Player {
  constructor(camera, dom, world) {
    this.camera = camera;
    this.dom = dom;
    this.world = world;
    this.pos = new THREE.Vector3();
    this.yaw = 0;
    this.pitch = -0.05;
    this.keys = new Set();
    this.enabled = true;
    this.touchMove = { x: 0, y: 0 };
    this.bind();
  }

  place(x, z, yaw = 0) {
    this.pos.set(x, 0, z);
    this.yaw = yaw;
    this.sync();
  }

  bind() {
    addEventListener('keydown', (e) => {
      if (e.target.closest?.('input, textarea')) return;
      this.keys.add(e.code);
    });
    addEventListener('keyup', (e) => this.keys.delete(e.code));
    addEventListener('blur', () => this.keys.clear());

    // drag to look (mouse + touch on the right half)
    let dragging = null;
    this.dom.addEventListener('pointerdown', (e) => {
      if (!this.enabled) return;
      if (e.pointerType === 'touch' && e.clientX < innerWidth / 2) return; // left half = joystick
      dragging = { id: e.pointerId, x: e.clientX, y: e.clientY };
      this.dom.setPointerCapture(e.pointerId);
    });
    this.dom.addEventListener('pointermove', (e) => {
      if (!dragging || dragging.id !== e.pointerId) return;
      const dx = e.clientX - dragging.x, dy = e.clientY - dragging.y;
      dragging.x = e.clientX; dragging.y = e.clientY;
      this.yaw -= dx * 0.005;
      this.pitch = THREE.MathUtils.clamp(this.pitch - dy * 0.004, -1.1, 1.0);
    });
    const end = (e) => { if (dragging && dragging.id === e.pointerId) dragging = null; };
    this.dom.addEventListener('pointerup', end);
    this.dom.addEventListener('pointercancel', end);
  }

  // Left-half virtual joystick, created by main.js on touch devices.
  attachJoystick(el, knob) {
    let id = null, cx = 0, cy = 0;
    const R = 50;
    el.addEventListener('pointerdown', (e) => {
      id = e.pointerId; el.setPointerCapture(id);
      const r = el.getBoundingClientRect(); cx = r.left + r.width / 2; cy = r.top + r.height / 2;
      move(e);
    });
    const move = (e) => {
      if (e.pointerId !== id) return;
      let dx = e.clientX - cx, dy = e.clientY - cy;
      const l = Math.hypot(dx, dy);
      if (l > R) { dx *= R / l; dy *= R / l; }
      knob.style.transform = `translate(${dx}px, ${dy}px)`;
      this.touchMove.x = dx / R; this.touchMove.y = dy / R;
    };
    el.addEventListener('pointermove', move);
    const up = (e) => { if (e.pointerId !== id) return; id = null; knob.style.transform = ''; this.touchMove.x = this.touchMove.y = 0; };
    el.addEventListener('pointerup', up);
    el.addEventListener('pointercancel', up);
  }

  forward() { return new THREE.Vector3(-Math.sin(this.yaw), 0, -Math.cos(this.yaw)); }

  update(dt) {
    if (this.enabled) {
      const k = this.keys;
      if (k.has('ArrowLeft')) this.yaw += TURN * dt;
      if (k.has('ArrowRight')) this.yaw -= TURN * dt;
      let f = 0, s = 0;
      if (k.has('KeyW') || k.has('ArrowUp')) f += 1;
      if (k.has('KeyS') || k.has('ArrowDown')) f -= 1;
      if (k.has('KeyA')) s -= 1;
      if (k.has('KeyD')) s += 1;
      f -= this.touchMove.y; s += this.touchMove.x;
      const len = Math.hypot(f, s);
      if (len > 0.05) {
        const n = Math.min(1, len);
        f /= len; s /= len;
        const fw = this.forward();
        const rt = new THREE.Vector3(-fw.z, 0, fw.x);
        const step = SPEED * dt * n;
        this.tryMove(fw.x * f * step + rt.x * s * step, fw.z * f * step + rt.z * s * step);
      }
    }
    this.sync();
  }

  // Move on each axis separately so the player slides along walls.
  tryMove(dx, dz) {
    if (!this.blocked(this.pos.x + dx, this.pos.z)) this.pos.x += dx;
    if (!this.blocked(this.pos.x, this.pos.z + dz)) this.pos.z += dz;
  }

  blocked(x, z) {
    for (const c of this.world.colliders) {
      if (x + RADIUS > c.minX && x - RADIUS < c.maxX && z + RADIUS > c.minZ && z - RADIUS < c.maxZ) return true;
    }
    for (const r of this.world.dynamicColliders || []) {
      if (Math.hypot(x - r.x, z - r.z) < RADIUS + r.r) return true;
    }
    return false;
  }

  sync() {
    this.camera.position.set(this.pos.x, EYE, this.pos.z);
    this.camera.rotation.set(this.pitch, this.yaw, 0, 'YXZ');
  }

  lookAt(target, dt) {
    const dx = target.x - this.pos.x, dz = target.z - this.pos.z;
    const want = Math.atan2(-dx, -dz);
    let d = want - this.yaw;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    this.yaw += d * Math.min(1, dt * 5);
    this.pitch += (-0.08 - this.pitch) * Math.min(1, dt * 5);
  }
}
