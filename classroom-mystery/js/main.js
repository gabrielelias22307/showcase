// Boots the game: renderer, world, NPCs, props, player, UI and the loop.

import * as THREE from 'three';
import mystery from '../data/mystery.js';
import assets from '../data/assets.js';
import { World } from './engine/world.js';
import { NPC } from './engine/npc.js';
import { Player } from './engine/player.js';
import { GameState } from './engine/state.js';
import { UI } from './engine/ui.js';
import { renderGraphic, svgToCanvas } from './engine/graphics.js';

const INTERACT_RANGE = 2.4;

const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
const scene = new THREE.Scene();
scene.background = new THREE.Color('#dfe6ee');
const camera = new THREE.PerspectiveCamera(70, 1, 0.05, 100);

function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener('resize', resize);
resize();

const state = new GameState(mystery);
const hadSave = state.flags.size > 0;
const loading = document.getElementById('loading');

const world = new World(scene, mystery, assets);
await world.build();

// Posters: evidence graphics hung on the wall in the 3D room.
for (const p of mystery.props.filter((p) => p.poster)) {
  const c = await svgToCanvas(renderGraphic(mystery.evidence[p.poster], mystery.room), 1024);
  if (c) world.addPoster(c, p.position[0], p.position[1], p.wall, 1.3);
}

// NPCs
const npcs = {};
await Promise.all(mystery.npcs.map(async (def) => {
  const n = new NPC(def);
  await n.load([assets.npcs?.[def.id], assets.npcFallback], world.spawns[def.id]);
  scene.add(n.root);
  npcs[def.id] = n;
}));
world.dynamicColliders = Object.values(npcs).map((n) => ({ x: n.position.x, z: n.position.z, r: 0.35 }));

// Interactables: NPCs and examinable props.
const interactables = [
  ...Object.values(npcs).map((n) => ({ kind: 'npc', ref: n, label: `Talk to ${n.name}`, pos: n.position })),
  ...mystery.props.map((p) => ({ kind: 'prop', ref: p, label: p.prompt, pos: new THREE.Vector3(p.position[0], 0, p.position[1]) }))
];

// Player
const player = new Player(camera, canvas, world);
const sp = world.spawns.player;
if (sp) player.place(sp.x, sp.z, mystery.player.yaw);
else player.place(mystery.player.spawn[0], mystery.player.spawn[1], mystery.player.yaw);

// UI
const prompt = document.getElementById('prompt');
const objective = document.getElementById('objective');
const ui = new UI({
  mystery, state, npcs,
  onAction(action) {
    if (action === 'accuse') ui.openReview(0);
    refreshHud();
  }
});

function refreshHud() {
  const ids = Object.keys(mystery.evidence);
  const have = ids.filter((id) => state.has(`has:${id}`)).length;
  const keySolved = mystery.readyWhen.filter((f) => state.has(f)).length;
  let text;
  if (state.solved) text = 'Case closed. Open your notebook to see your report.';
  else if (state.has('ready')) text = 'You have the key facts. Tell Ms. Ortiz what happened.';
  else if (!state.has('talked:ortiz')) text = 'Talk to Ms. Ortiz at the front of the room.';
  else text = `Collect graphics and answer their questions. Key facts: ${keySolved} / ${mystery.readyWhen.length}`;
  objective.innerHTML = `<strong>Goal:</strong> ${text}<br><span class="muted">Evidence collected: ${have} / ${ids.length}</span>`;
}
state.on((type) => { if (type !== 'answer') refreshHud(); });
state.on((type) => { if (type === 'ready') ui.toast('<strong>You have all the key facts!</strong> Go tell Ms. Ortiz what happened.', 6000); });
refreshHud();

document.getElementById('btn-notebook').onclick = () => ui.openNotebook();
document.getElementById('btn-help').onclick = () => ui.openHelp();
prompt.onclick = () => interact();

let focus = null;
function findFocus() {
  const fw = player.forward();
  let best = null, bestScore = Infinity;
  for (const it of interactables) {
    const dx = it.pos.x - player.pos.x, dz = it.pos.z - player.pos.z;
    const d = Math.hypot(dx, dz);
    if (d > INTERACT_RANGE) continue;
    const facing = (dx * fw.x + dz * fw.z) / (d || 1);
    if (facing < 0.35) continue;
    const score = d - facing; // prefer close and centred
    if (score < bestScore) { bestScore = score; best = it; }
  }
  return best;
}

function interact() {
  if (!focus || ui.open) return;
  if (focus.kind === 'npc') {
    focus.ref.startTalking(player.pos);
    ui.openDialogue(focus.ref);
  } else {
    ui.openExamine(focus.ref);
  }
}

addEventListener('keydown', (e) => {
  if (e.target.closest?.('input, textarea')) return;
  if (ui.open) return;
  if (e.target.closest?.('button') && (e.code === 'Enter' || e.code === 'Space')) return;
  if (e.code === 'KeyE' || e.code === 'Enter' || e.code === 'Space') { e.preventDefault(); interact(); }
  else if (e.code === 'KeyN') ui.openNotebook();
  else if (e.code === 'KeyH') ui.openHelp();
});

// Touch joystick only on touch devices.
if (matchMedia('(pointer: coarse)').matches) {
  const joy = document.getElementById('joystick');
  joy.hidden = false;
  player.attachJoystick(joy, joy.querySelector('.knob'));
}

loading.remove();
ui.openIntro(hadSave);

// Loop
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);
  player.enabled = !ui.open;
  player.update(dt);
  if (ui.modal === 'dialogue' && ui.dialogueNpc) player.lookAt(ui.dialogueNpc.position, dt);
  for (const n of Object.values(npcs)) n.update(dt);

  focus = ui.open ? null : findFocus();
  if (focus) {
    prompt.hidden = false;
    prompt.innerHTML = `<kbd>E</kbd> ${focus.label}`;
  } else prompt.hidden = true;

  renderer.render(scene, camera);
});

// Handy for testing in the browser console.
window.game = { state, ui, player, npcs, world, mystery };
