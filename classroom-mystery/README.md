# Classroom Mystery: a 3D Graphic Literacy game engine

Students walk around a large 3D classroom, interview the people in it, and
collect workplace-style graphics (tables, charts, a floor plan and a
flowchart). Each graphic has one question written to a WorkKeys Graphic
Literacy level (3 to 7). The answers add up to the solution of a mystery.
See [STANDARDS.md](STANDARDS.md) for the research and the skill map.

The first mystery included is **The Case of the Missing Robotics Trophy**.

The game runs now with simple placeholder models. Each Blender file replaces
its placeholder when you add it to `assets/models/`.

## Run it

Browsers won't load the 3D modules from a `file://` page, so serve the
folder:

```bash
cd classroom-mystery
npx http-server -p 8080     # or: python3 -m http.server 8080
```

Then open http://localhost:8080.

To share it with students, upload the whole `classroom-mystery` folder to any
static host, such as GitHub Pages or Netlify, and link to `index.html`. To
put it in Canvas, embed that hosted URL in an iframe. The game uses about
1 MB plus your models, and nothing is loaded from a CDN, so it works on
school networks that block CDNs.

**Controls:** W A S D or the arrow keys to move, drag the mouse to look, E to
talk or examine, N for the notebook, number keys to pick answers. On phones
and tablets there is a joystick on the left; drag on the right to look.

## Extra practice: other WorkKeys tests (optional)

Two optional question banks practice the other two tests in the ACT
National Career Readiness Certificate:

| Bank | File | Tasks |
|---|---|---|
| 📐 Applied Math | `data/banks/applied-math.js` | 10 (two per level, 3-7), with a formula sheet |
| 📄 Workplace Documents | `data/banks/workplace-documents.js` | 10 (two per level, 3-7), each with a memo, notice, rule or policy |

When a bank is on, the people in the room offer extra "Math task" and
"Reading task" choices when you talk to them. These tasks never change the
mystery or the case review. They show up in the notebook (Extra practice
tab), in the on-screen counter, and as their own level-by-level sections in
the student report.

**Students** turn the banks on or off on the start screen or in
Notebook > My progress.

**Teachers** can set them in the link instead. The switches are then hidden:

| Link | What students get |
|---|---|
| `index.html?practice=math` | Applied Math tasks |
| `index.html?practice=docs` | Workplace Documents tasks |
| `index.html?practice=all` | Both |
| `index.html?practice=none` | Neither (Graphic Literacy only) |

To add another bank, copy one of the bank files, give it a new `id` and new
item ids, and list it in `data/banks/index.js`. See
[STANDARDS.md](STANDARDS.md) for how each task maps to the test levels.

## Adding your Blender files

**Artists: start with [HANDOVER.md](HANDOVER.md).** It has the room layout in
Blender coordinates, the file checklist, photo rules and size budgets.

Export each file with **File > Export > glTF 2.0** and these settings:

- Format: **glTF Binary (.glb)**
- Include: check **Selected Objects** if you only want part of the scene
- Transform: **+Y Up** (the default)
- Mesh: **Apply Modifiers**
- Animation: on, if the character has clips
- Compression (Draco): **off** (the engine doesn't include the Draco decoder)

Save the files in `assets/models/` with the names listed in
[`data/assets.js`](data/assets.js). Missing files fall back to placeholders,
so you can add them one at a time. To use different file names, edit that
file.

### Option A: one file for the whole classroom (`classroom.glb`)

Use 1 Blender unit = 1 meter. The default room is 24 m × 16 m with its
centre at the origin. **X** runs west to east (−12 to +12), Blender's **+Y**
is north (the whiteboard wall), and Blender's **−Y** is south (Door A). Inside the file, use these names:

| Object name in Blender | What the engine does |
|---|---|
| `COL_anything` (a box mesh) | Becomes an invisible wall the player can't walk through. Add one per wall and per large piece of furniture. |
| `SPAWN_player` (an empty) | Where the player starts |
| `SPAWN_ortiz`, `SPAWN_sam`, … (empties) | Where each character stands (ids are in `data/mystery.js`) |

If the file has no `COL_` objects, the engine keeps the placeholder room's
walls. When `classroom.glb` loads, the placeholder room is hidden; set
`hidePlaceholder: false` in `data/assets.js` to keep both.

The floor-plan clue is drawn from `room` in `data/mystery.js`. If you move
the trophy case or the doors in Blender, update their numbers there too so
the floor plan matches the 3D room.

### Option B: individual furniture models

`table.glb`, `trophy_case.glb`, `robotics_bench.glb` and `desk.glb` replace
those placeholder pieces wherever the layout puts them. Put each model's
origin at its bottom centre.

### Photos

Real photos go in `assets/photos/`. Wall pictures are listed under
`pictures` in `data/assets.js`. A character's dialogue portrait is set
with `portrait:` on that character's line. See HANDOVER.md, section 6.

### Characters (`npc_<id>.glb`)

- Model the character facing Blender's Front view (the character faces −Y).
- The engine scales each model to the `height` in `data/assets.js` unless
  you give it a `scale`.
- Animation clips named **`Idle`** and **`Talk`** play automatically. If
  there's no `Idle` clip, the first clip plays.
- `npc_student.glb` is used for any character whose own file is missing.

## Writing a new mystery

Everything about the story lives in `data/mystery.js`:

- `room`: size, doors, windows and furniture (used for both the 3D room and
  the floor plan)
- `npcs`: name, role, colour, position and a dialogue tree. A dialogue
  choice can `give` evidence, `set` flags, `requires` or `requiresNot` flags,
  or run `action: 'accuse'`.
- `props`: things to examine; a `poster` shows a graphic on the wall
- `evidence`: one graphic plus one leveled question each. The graphic types
  are `floorplan`, `table`, `flowchart`, `bar`, `line` and `pie`, and each
  needs an `alt` text description.
- `readyWhen`: the flags needed before the case review opens
- `review`: the final multi-graphic questions, then `culprit`,
  `wrongCulprit` and `ending`

The engine sets these flags automatically: `has:E1` (collected),
`solved:E1` (answered correctly), `talked:<npcId>`, and `ready`.

## Files

```
index.html            page shell and import map
css/style.css
js/main.js            startup and game loop
js/engine/world.js    room builder and .glb loading (COL_ / SPAWN_ rules)
js/engine/npc.js      characters, animation, name tags
js/engine/player.js   movement, look and collision
js/engine/ui.js       dialogue, evidence viewer, notebook, case review, report
js/engine/graphics.js SVG chart renderers
js/engine/state.js    flags, scoring and save (localStorage)
data/mystery.js       the story
data/assets.js        list of Blender files
data/banks/           optional Applied Math and Workplace Documents tasks
vendor/three/         three.js r160 (MIT), stored locally
```

## Student report

Progress saves in the browser automatically. At the end (or from
Notebook > My progress > Teacher report), students see a level-by-level
summary showing which questions they got right on the first try. They can
copy it, download it as `.txt`, or print it to PDF to turn in.
