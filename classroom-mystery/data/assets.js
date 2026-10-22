// Blender asset manifest.
//
// Export each Blender file as glTF Binary (.glb) into assets/models/ using
// the file names below. Any file that is missing is replaced by a simple
// placeholder, so you can add models one at a time.
// See README.md > "Adding your Blender files" for export settings and the
// COL_ / SPAWN_ naming rules.

export default {
  // Whole classroom (walls, floor, furniture). Optional.
  // Add boxes named COL_<anything> for walls/furniture the player can't walk
  // through, and empties named SPAWN_player, SPAWN_ortiz, SPAWN_sam ... to
  // place the player and characters. Units: 1 Blender unit = 1 meter.
  room: {
    url: 'assets/models/classroom.glb',
    scale: 1,
    position: [0, 0, 0],
    rotationY: 0,
    hidePlaceholder: true
  },

  // Single furniture pieces, matched by object id first, then by type
  // (see mystery.room.objects). One table.glb is reused for all 16 tables.
  // Origin should be at the bottom-centre of the object.
  objects: {
    table: { url: 'assets/models/table.glb' },
    trophyCase: { url: 'assets/models/trophy_case.glb', rotationY: 0 },
    bench: { url: 'assets/models/robotics_bench.glb' },
    desk: { url: 'assets/models/desk.glb' }
  },

  // Characters. Model them facing the camera in Blender's Front view
  // (the character faces -Y); that exports as facing forward here.
  // Animation clips named "Idle" and "Talk" play automatically.
  // Leave out `scale` to auto-fit the model to `height` meters.
  npcs: {
    ortiz: { url: 'assets/models/npc_ortiz.glb', height: 1.72 },
    jordan: { url: 'assets/models/npc_jordan.glb', height: 1.68 },
    marcus: { url: 'assets/models/npc_marcus.glb', height: 1.78 },
    priya: { url: 'assets/models/npc_priya.glb', height: 1.62 },
    riley: { url: 'assets/models/npc_riley.glb', height: 1.7 },
    sam: { url: 'assets/models/npc_sam.glb', height: 1.75 },
    ana: { url: 'assets/models/npc_ana.glb', height: 1.6 }
  },

  // Used for any NPC above whose own file is missing. Set to null to use
  // the coloured placeholder figures instead.
  npcFallback: { url: 'assets/models/npc_student.glb', height: 1.7 }
};
