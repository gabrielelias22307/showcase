// NPCs: a Blender character (.glb) if one is listed in data/assets.js,
// otherwise a simple coloured placeholder figure. Plays "Idle" / "Talk"
// animation clips when the model has them.

import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { loadGLB } from './world.js';

function nameTag(name, role) {
  const c = document.createElement('canvas');
  c.width = 512; c.height = 160;
  const g = c.getContext('2d');
  g.fillStyle = 'rgba(20,24,34,0.82)';
  g.beginPath(); g.roundRect(8, 8, 496, 144, 28); g.fill();
  g.fillStyle = '#fff'; g.font = 'bold 60px Arial'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(name, 256, 62);
  g.fillStyle = '#c9d3e6'; g.font = '34px Arial';
  g.fillText(role, 256, 118);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, transparent: true }));
  s.scale.set(0.8, 0.25, 1);
  s.renderOrder = 10;
  return s;
}

function placeholderFigure(color) {
  const g = new THREE.Group();
  const body = new THREE.MeshStandardMaterial({ color, roughness: 0.7 });
  const skin = new THREE.MeshStandardMaterial({ color: '#e0b48f', roughness: 0.7 });
  const pants = new THREE.MeshStandardMaterial({ color: '#2d3442', roughness: 0.8 });
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 0.5, 4, 12), body);
  torso.position.y = 1.15;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.17, 18, 14), skin);
  head.position.y = 1.62;
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 6), skin);
  nose.position.set(0, 1.6, 0.17); // +Z is "forward", same as glTF
  for (const sx of [-1, 1]) {
    const leg = new THREE.Mesh(new THREE.CapsuleGeometry(0.08, 0.6, 4, 8), pants);
    leg.position.set(sx * 0.1, 0.4, 0);
    g.add(leg);
    const arm = new THREE.Mesh(new THREE.CapsuleGeometry(0.06, 0.5, 4, 8), body);
    arm.position.set(sx * 0.3, 1.1, 0);
    arm.rotation.z = sx * 0.12;
    g.add(arm);
  }
  g.add(torso, head, nose);
  g.userData.head = head;
  return g;
}

export class NPC {
  constructor(def) {
    this.def = def;
    this.id = def.id;
    this.name = def.name;
    this.root = new THREE.Group();
    this.root.name = `npc-${def.id}`;
    this.root.position.set(def.position[0], 0, def.position[1]);
    this.homeYaw = def.yaw || 0;
    this.root.rotation.y = this.homeYaw;
    this.targetYaw = this.homeYaw;
    this.mixer = null;
    this.actions = {};
    this.talking = false;
    this.t = Math.random() * 10;
    this.height = 1.75;
  }

  // specs: list of asset specs to try in order (own model, then fallback).
  async load(specs, spawnOverride) {
    if (spawnOverride) this.root.position.set(spawnOverride.x, 0, spawnOverride.z);
    let model = null;
    for (const spec of specs) {
      if (model || !spec?.url) continue;
      const gltf = await loadGLB(spec.url);
      if (gltf) {
        model = cloneSkinned(gltf.scene);
        // Fit to a target height unless an exact scale is given.
        if (spec.scale) model.scale.setScalar(spec.scale);
        else {
          const b = new THREE.Box3().setFromObject(model);
          const h = b.max.y - b.min.y;
          if (h > 0) model.scale.setScalar((spec.height || 1.7) / h);
          const b2 = new THREE.Box3().setFromObject(model);
          model.position.y -= b2.min.y;
        }
        if (spec.rotationY) model.rotation.y = spec.rotationY;
        if (gltf.animations?.length) {
          this.mixer = new THREE.AnimationMixer(model);
          const find = (n) => gltf.animations.find((a) => a.name.toLowerCase() === String(n).toLowerCase());
          const idle = find(spec.idle || 'Idle') || gltf.animations[0];
          const talk = find(spec.talk || 'Talk');
          if (idle) this.actions.idle = this.mixer.clipAction(idle);
          if (talk) this.actions.talk = this.mixer.clipAction(talk);
          this.actions.idle?.play();
        }
        const b = new THREE.Box3().setFromObject(model);
        this.height = b.max.y - b.min.y;
      }
    }
    if (!model) model = placeholderFigure(this.def.color || '#888');
    this.model = model;
    this.root.add(model);
    this.tag = nameTag(this.def.name, this.def.role || '');
    this.tag.position.y = this.height + 0.35;
    this.root.add(this.tag);
  }

  get position() { return this.root.position; }

  startTalking(playerPos) {
    this.talking = true;
    this.tag.visible = false;
    const dx = playerPos.x - this.root.position.x;
    const dz = playerPos.z - this.root.position.z;
    this.targetYaw = Math.atan2(dx, dz);
    if (this.actions.talk) {
      this.actions.talk.reset().fadeIn(0.25).play();
      this.actions.idle?.fadeOut(0.25);
    }
  }

  stopTalking() {
    this.talking = false;
    this.tag.visible = true;
    this.targetYaw = this.homeYaw;
    if (this.actions.talk) {
      this.actions.idle?.reset().fadeIn(0.25).play();
      this.actions.talk.fadeOut(0.25);
    }
  }

  update(dt) {
    this.t += dt;
    if (this.mixer) this.mixer.update(dt);
    else if (this.model) {
      // simple breathing bob for placeholders
      this.model.position.y = Math.sin(this.t * 2) * 0.01;
      if (this.talking && this.model.userData.head) this.model.userData.head.position.y = 1.62 + Math.abs(Math.sin(this.t * 9)) * 0.015;
    }
    // ease toward target yaw (shortest way round)
    let d = this.targetYaw - this.root.rotation.y;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    this.root.rotation.y += d * Math.min(1, dt * 6);
  }
}
