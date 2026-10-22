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

  // Photo textures for the placeholder room. Made from photos of the real
  // classroom (location data removed). Each one repeats seamlessly:
  // wall/accent = 2.05 m of painted block, floor = 8 x 30.5 cm tiles.
  // Delete a line to fall back to a plain colour.
  textures: {
    wall: 'assets/textures/tex_block_cream.jpg',
    accent: 'assets/textures/tex_block_blue.jpg',
    floor: 'assets/textures/tex_floor_tile.jpg',
    wood: 'assets/textures/tex_wood_drawers.jpg'
  },

  // Single furniture pieces, matched by object id first, then by type
  // (see mystery.room.objects). One table.glb is reused for all 12 tables.
  // Origin at the bottom-centre; model the front facing Blender's Front
  // view (-Y). The engine turns each piece to face the way the room needs.
  objects: {
    table: { url: 'assets/models/table.glb' },
    trophyCase: { url: 'assets/models/trophy_case.glb', rotationY: 0 },
    bench: { url: 'assets/models/robotics_bench.glb' },
    desk: { url: 'assets/models/desk.glb' }
  },

  // Optional on each character: portrait: 'assets/photos/portrait_sam.jpg'
  // (a square photo shown in the dialogue box and notebook).
  // Characters. Model them facing the camera in Blender's Front view
  // (the character faces -Y); that exports as facing forward here.
  // Animation clips named "Idle" and "Talk" play automatically.
  // Leave out `scale` to auto-fit the model to `height` meters.
  npcs: {
    ortiz: { url: 'assets/models/npc_ortiz.glb', height: 1.78, portrait: 'assets/photos/portrait_ortiz.jpg' },   // Mr. Elias
    jordan: { url: 'assets/models/npc_jordan.glb', height: 1.6, portrait: 'assets/photos/portrait_jordan.jpg' },
    marcus: { url: 'assets/models/npc_marcus.glb', height: 1.78 },
    priya: { url: 'assets/models/npc_priya.glb', height: 1.62 },
    riley: { url: 'assets/models/npc_riley.glb', height: 1.7 },
    sam: { url: 'assets/models/npc_sam.glb', height: 1.7, portrait: 'assets/photos/portrait_sam.jpg' },
    ana: { url: 'assets/models/npc_ana.glb', height: 1.6 }
  },

  // Used for any NPC above whose own file is missing. Set to null to use
  // the coloured placeholder figures instead.
  npcFallback: { url: 'assets/models/npc_student.glb', height: 1.7 },

  // Real photos hung on the walls as framed pictures. wall: north | south |
  // east | west. Position in Blender floor coordinates (meters from the
  // room centre): x for north/south walls, y for east/west walls.
  // height = centre of the picture above the floor. Missing files are
  // skipped. Example:
  //   { url: 'assets/photos/team_photo.jpg', wall: 'north', x: 6, height: 1.7, width: 1.4 }
  pictures: [
    // From the real room photos: no people, no names, location data removed.
    { url: 'assets/photos/pic_rules_board.jpg', wall: 'south', x: 2.5, height: 1.55, width: 0.85 },
    { url: 'assets/photos/pic_rainbow_art.jpg', wall: 'east', y: 1.1, height: 1.7, width: 0.7 },
    { url: 'assets/photos/pic_color_swatches.jpg', wall: 'west', y: 6.6, height: 1.85, width: 1.2 }
  ]
};
