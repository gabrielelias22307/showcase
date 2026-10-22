# Handover: Blender models and photos for Classroom Mystery

You're taking over the art for a 3D classroom mystery game. Students walk
around a large classroom, interview characters, and read charts and maps to
solve a mystery. The questions practice the WorkKeys Graphic Literacy test.

**The game already works.** It uses simple placeholder shapes for the room
and the people. Your job is to replace those placeholders with Blender models
and real photos. You don't need to write code: you export files, put them in
the right folders, and list photos in one settings file.

| | Where |
|---|---|
| Project folder | `classroom-mystery/` in the `showcase` repo, branch `claude/beautiful-wozniak-kle1io` |
| Your folders | `assets/models/` (Blender `.glb` files) and `assets/photos/` (pictures) |
| The one file you edit | `data/assets.js` (file names, sizes and photo placement) |
| Leave alone | `js/`, `vendor/`, `data/mystery.js` (story and layout; see "Moving things" below) |
| More detail | `README.md` (engine), `STANDARDS.md` (the test skills) |

---

## 1. See the game on your computer

The game must be opened through a small local web server. Double-clicking
`index.html` shows an error message instead of the game.

```bash
cd classroom-mystery
npx http-server -p 8080        # needs Node.js
# or, with Python installed:
python3 -m http.server 8080
```

Open http://localhost:8080. Move with **W A S D**, drag the mouse to look,
and press **E** to talk.

After you add a file, reload the page with **Ctrl+Shift+R** (Cmd+Shift+R on
a Mac) so the browser doesn't use an old copy. Open the browser console (F12)
to see messages starting with `[assets]`: they tell you which files loaded,
and which were not found and are still placeholders.

To start the story over while testing, open **Notebook > My progress >
Start over**.

---

## 2. What to make (checklist)

Every file is optional. Anything missing stays a placeholder, so you can
deliver one file at a time.

### Blender models (`assets/models/`)

| File | What it is | Notes |
|---|---|---|
| `classroom.glb` | The whole suite: walls, floor, ceiling, doors, furniture | **Recommended.** Must include `COL_` boxes (section 4). |
| `npc_ortiz.glb` | Mr. Elias, yearbook adviser (teacher) | 1.78 m. **Done** (Gabriel; `tools/gabriel_character.py`) |
| `npc_jordan.glb` | Jordan, hall pass monitor (student) | 1.60 m. **Done** (`tools/student_character.py`, WHO = A) |
| `npc_marcus.glb` | Marcus, photo editor (student) | 1.78 m |
| `npc_priya.glb` | Priya, page designer (student) | 1.62 m |
| `npc_riley.glb` | Riley, staff writer (student) | 1.70 m |
| `npc_sam.glb` | Sam, editor-in-chief (student) | 1.70 m. **Done** (`tools/student_character.py`, WHO = B) |
| `npc_ana.glb` | Ana, library aide visiting the room (student) | 1.60 m |
| `npc_grump.glb` | Mr. Grump, the principal (in the office; a witness, not a suspect) | 1.83 m. **Done** (`tools/principal_character.py`) |
| `npc_student.glb` | A generic student, used for any character above that doesn't have a file yet | optional |

If you'd rather not build the whole room as one file, you can instead make
single pieces: `table.glb` (reused for all 12 student tables),
`trophy_case.glb`, `layout_table.glb` and `desk.glb`. Each piece's origin
must be at its **bottom centre**, with its front facing Blender's Front
view (−Y). The engine puts and turns them in place. Don't do
both: if `classroom.glb` exists, the separate pieces are hidden.

Heights are set in `data/assets.js`. The engine resizes each character to
that height, so your Blender scale for characters doesn't matter.

### Photos (`assets/photos/`)

| Kind | Use | Spec |
|---|---|---|
| Character portraits | Small round photo next to the character's name when students talk to them, and in the notebook | Square crop, about 400 × 400 px, `.jpg`, face centred |
| Wall pictures | Framed pictures on the classroom walls (posters, a team photo, signs) | `.jpg` (or `.png` for graphics with text), longest side ≤ 1600 px, under ~300 KB |
| Textures in Blender | Real photos used as materials (floor tiles, wood, whiteboard, posters painted into the room) | Set these up in Blender; they travel inside the `.glb` (section 6) |

---

## 3. Blender export settings

**File > Export > glTF 2.0 (.glb/.gltf)**:

- **Format:** glTF Binary (`.glb`)
- **Include:** Selected Objects (select what belongs in this file first);
  also tick **Custom Properties** off and **Cameras/Lights** off
- **Transform:** +Y Up (the default)
- **Data > Mesh:** Apply Modifiers ✔
- **Data > Material > Images:** JPEG format (keeps files small)
- **Data > Compression (Draco):** **off.** The game can't open
  Draco-compressed files.
- **Animation:** on for characters, off for the room

Units: **1 Blender unit = 1 meter.** Apply scale on everything
(Ctrl+A > Scale) before exporting.

---

## 4. The classroom (`classroom.glb`)

The layout comes from photos of the real room: a big classroom, with a
computer lab and a small office behind a wall with two open doorways.
**Shortcut:** `tools/classroom_starter.py` builds this whole layout in
Blender (walls, furniture, `COL_` boxes, `SPAWN_` spots, photo textures).
Run it, then model over it.

### Size and directions

The whole suite is **24 m (east–west) × 16 m (north–south)**, with a
**3.4 m** ceiling. The suite's centre on the floor is Blender's origin
(0, 0, 0).

| Direction in the story | In Blender |
|---|---|
| East | +X (X = 12 is the east wall) |
| West | −X (X = −12 is the west wall) |
| North (computer lab side) | +Y (Y = 8 is the north wall) |
| South (classroom side) | −Y (Y = −8 is the south wall) |
| Up | +Z |

Look from Blender's **Top view** (numpad 7): north is at the top of the
screen and east is on the right, the same as the floor-plan clue.

### Rooms and walls

| Part | Where (Blender X, Y) |
|---|---|
| Classroom | Y from −8 to 2, the full width |
| Computer lab | X from −12 to 7, Y from 2 to 8 |
| Office | X from 7 to 12, Y from 2 to 8 |
| Inside wall, classroom ↔ lab and office | Y = 2, 0.15 m thick, two open doorways: X 2.8 to 4.2 (lab) and X 8.3 to 9.3 (office), 2.2 m tall |
| Inside wall, lab ↔ office | X = 7, from Y 2 to 8, no doorway |
| Blue painted wall | Classroom's east wall, Y from −8 to 2 |

There are **no windows** (the real room has none).

### Where things go (Blender X, Y in meters, centre of the object)

These positions match the floor-plan clue that students read, so **the
mystery depends on them**. Small shifts (say 20 cm) are fine. For bigger
moves, see "Moving things" below.

| Object | X | Y | Size (X × Y × height) | Notes |
|---|---|---|---|---|
| Door A (Main) | −12 | −6 | 1.2 wide, 2.2 tall | West wall of the classroom. Wood door with a glass side panel. Label it "Door A (Main)". |
| Door B (Lab) | −9 | 8 | 1.2 wide, 2.2 tall | North wall of the computer lab. Label it "Door B (Lab)". |
| **Trophy case** | −6.8 | 7.55 | 2.2 × 0.8 × 1.9 | Against the lab's north wall, just east of Door B. Glass front faces south. |
| Computer desks | 2.6 | 7.55 | 6.8 × 0.8 × 0.75 | Lab's north wall; monitors, towers, navy chairs |
| Layout table 1 | −2.4 | 4.6 | 3.2 × 1.1 × 0.9 | Yearbook page proofs and a camera on top |
| Layout table 2 | 2.6 | 4.6 | 3.2 × 1.1 × 0.9 | Camera battery charging station |
| Camera cabinet | 6.55 | 6.3 | 0.7 × 1.6 × 2.0 | Grey metal, against the office wall, doors face west |
| Rolling whiteboard | −10.4 | 4.6 | 0.6 × 1.8 × 2.1 | Sticky notes, faces east |
| Sink counter | −11.65 | 6.6 | 0.7 × 1.4 × 0.9 | Lab's west wall |
| Office desk | 10.4 | 7.25 | 1.5 × 0.7 × 0.76 | |
| Filing cabinets (2) | 11.7 | 5.3 and 4.7 | 0.6 × 0.5 × 1.35 each | Black |
| Teacher's desk | −8.6 | 0.95 | 2.0 × 0.8 × 0.76 | Classroom, north-west |
| Tall wood cabinet | −11.45 | 1.55 | 1.0 × 0.7 × 2.2 | Classroom's north-west corner |
| TV on a stand | −5.4 | 1.6 | 1.7 wide, screen centre 1.55 m up | "YEARBOOK" sign above it |
| Whiteboard (north) | −1.2 | 1.9 | 3.4 wide, 1.2 tall | Inside wall; bottom edge 1.0 m up |
| Whiteboard (west) | −11.97 | −1.4 | 4.0 wide, 1.2 tall | Classroom's west wall |
| Drawer cabinet | −11.65 | −4.25 | 0.6 × 1.1 × 0.9 | Beside Door A |
| Hall pass desk | −9.4 | −6 | 0.8 × 1.6 × 0.76 | Just inside Door A; Jordan sits on its east side, facing the door |
| Counter with plants | 11.62 | −3.6 | 0.75 × 7.0 × 0.9 | Blue east wall; upper cabinets above; potted plants at the north end (Y −0.5 to −2.6) |
| Bookshelf | 11.1 | −7.65 | 1.0 × 0.35 × 1.8 | Black, south-east corner |
| Library book cart | 6.5 | −7.3 | 1.2 × 0.6 × 1.0 | Ana's cart |
| Student tables (12) | X = −6, −2.5, 1, 4.5 | Y = −0.6, −3.2, −5.8 | 2 × 0.8 × 0.75 each | Grey tops; two navy chairs per table, on the south (−Y) side |

**Keep this wall space clear:** the game hangs the **floor-plan poster** (a
clue) on the south wall at X = −7.5, centred 1.6 m up and about 1.3 m wide.
The game also hangs three photo pictures (section 6): south wall X = 2.5,
east wall Y = 1.1, and the lab's west wall Y = 6.6.

### Story details the art must show

Students are told these things, so the model has to agree:

- **Trophy case:** glass door closed. **Top shelf empty**, with a small dark
  sensor pad where the trophy stood. **Middle shelf:** ribbons and medals.
  **Bottom shelf:** a couple of small trophies. **Don't model the missing
  championship trophy anywhere in the room.**
- **Doors A and B are closed.** Students can't leave the suite. The two
  inside doorways stay open (no doors in them).
- Jordan's hall pass desk faces Door A. You can't see the trophy case from
  it: the case is in the lab, behind the inside wall (the story relies on
  that).
- Priya's plants are on the counter along the blue wall, in the classroom,
  far from the case.
- **No whiteboard writing with names.** The real whiteboards had students'
  names on them, so keep boards blank or use made-up writing.
- Mr. Grump, the principal, is in the office the whole time (he is a witness,
  not a suspect).
- The room belongs to the **yearbook** staff: layout tables with page proofs
  and cameras, a camera cabinet, a "YEARBOOK" sign. No robotics.
- It's 3:55 PM after school.

### Required helper objects

Add these to `classroom.glb`. They're how the game knows where people can
walk and stand.

1. **Collision boxes: name each one `COL_` + anything** (for example
   `COL_wall_north`, `COL_trophy_case`, `COL_table_03`). Use plain cubes.
   The game makes them invisible and stops the player at them. Add one for
   each outside wall (including both closed doors), each piece of the
   inside walls (**leave the two doorways open**), and each large piece of
   furniture. Only their footprint matters, so height can be rough.
   Rotated boxes are treated as their straight bounding box, so keep them
   aligned to the X and Y axes. If there are **no** `COL_` objects in the
   file, the game uses its own built-in walls.

2. **Standing spots: Empties named `SPAWN_` + name** (Add > Empty > Plain
   Axes). These are optional: if you leave them out, the game uses the
   default spots below.

| Empty name | Who | Default X, Y |
|---|---|---|
| `SPAWN_player` | The student playing | −11.0, −6.0 (just inside Door A) |
| `SPAWN_ortiz` | Mr. Elias | −8.6, −0.2 (in front of her desk) |
| `SPAWN_jordan` | Jordan | −8.6, −6.0 (at the hall pass desk) |
| `SPAWN_marcus` | Marcus | −2.4, 3.5 (lab, by layout table 1) |
| `SPAWN_priya` | Priya | 10.3, −1.4 (by the plants) |
| `SPAWN_riley` | Riley | −0.75, −2.0 (among the student tables) |
| `SPAWN_sam` | Sam | 5.6, 4.6 (lab, east of layout table 2) |
| `SPAWN_ana` | Ana | 6.5, −6.4 (by the book cart) |
| `SPAWN_grump` | Mr. Grump | 9.6, 5.6 (in the office) |

Leave at least 0.8 m of clear floor around each spot so students can walk
up to the person.

---

## 5. Characters (`npc_<name>.glb`)

- **Face the camera in Blender's Front view** (numpad 1). The character
  should look toward −Y.
- **Origin at the feet,** standing on the floor (Z = 0).
- **Animations:** name the actions exactly **`Idle`** (breathing or standing
  loop) and **`Talk`** (talking loop). The game plays Idle normally and
  Talk during conversations. If there's no `Idle`, it plays the first
  animation it finds. Animations are optional.
- One character per file. The game turns them toward the player when they
  talk.
- Each character's colour in the placeholder version (in `data/mystery.js`)
  is a good hint for their main clothing colour: Mr. Elias blue `#3d6fb4`,
  Jordan orange `#c46a2b`, Marcus green `#2f8a5b`, Priya purple `#8a3fa0`,
  Riley red `#b23a48`, Sam gold `#d19a1f`, Ana teal `#2b8f9a`. Matching
  isn't required, but it helps students tell people apart.

---

## 6. Photos

### Character portraits

1. Save as `assets/photos/portrait_<name>.jpg`, for example
   `portrait_sam.jpg`.
2. In `data/assets.js`, add `portrait:` to that character's line:

```js
sam: { url: 'assets/models/npc_sam.glb', height: 1.7, portrait: 'assets/photos/portrait_sam.jpg' },
```

If the photo file is missing, the game shows a coloured dot instead.

### Wall pictures

Add each picture to the `pictures` list at the bottom of `data/assets.js`:

```js
pictures: [
  { url: 'assets/photos/team_photo.jpg', wall: 'north', x: 6, height: 1.7, width: 1.4 },
  { url: 'assets/photos/yearbook_poster.jpg', wall: 'east', y: 6.5, height: 1.6, width: 1.0 }
]
```

- `wall`: `north`, `south`, `east` or `west`
- Position uses the same Blender coordinates as section 4: for `north` and
  `south` walls give `x` (−12 to 12); for `east` and `west` walls give `y`
  (−8 to 8).
- `height`: how high the picture's centre is (1.6 m is eye level).
  `width` is in meters; the picture's height comes from the photo's shape.
- Don't cover the doors, the inside doorways or the floor-plan poster spot
  (south wall, x = −7.5).

### Photos and textures already made from the real room

Photos of the real classroom were turned into ready-to-use files, with
no people or names in them and location data removed:

| File | What it is |
|---|---|
| `assets/textures/tex_block_cream.jpg` | Cream painted block wall (repeats every 2.05 m) |
| `assets/textures/tex_block_blue.jpg` | Blue painted block wall (repeats every 2.05 m) |
| `assets/textures/tex_floor_tile.jpg` | Tile floor with red accent tiles (repeats every 2.44 m) |
| `assets/textures/tex_wood_drawers.jpg` | Wood cabinet drawer fronts |
| `assets/photos/pic_rules_board.jpg` | "Rules" bulletin board (south wall) |
| `assets/photos/pic_rainbow_art.jpg` | Rainbow art (blue east wall) |
| `assets/photos/pic_color_swatches.jpg` | Colour swatch poster (lab's west wall) |

The game already uses them. `tools/classroom_starter.py` uses the textures
too when you set its `TEXTURE_DIR`. The two art prints look like printed
posters; if they came from a publisher, check you're allowed to show them
before you share the game publicly.

### Photo textures inside Blender

Real photos used as materials (wood, floor, a whiteboard with writing, a
poster painted onto a wall) go into the `.glb` with the model. In the export
settings, choose **Images: JPEG**. Resize big photos before you use them:
**1024 px** for most surfaces, **2048 px** only for the floor or a hero
object.

Tip: the game uses simple lighting with no real-time shadows. For a more
realistic room, **bake** lighting and shadows into the room's textures in
Blender (Cycles > Bake) before export.

### Rules for real photos (please read)

- **No photos of real students** (faces, names, ID badges or anything
  identifying them) unless the school has written permission for this use.
  Follow your district's media-release policy. Staff or adult volunteers
  who agree to it, or illustrated or stylized faces, are safer choices.
- Make sure no **real names, schedules, student work with names, or
  screens** show in the background of any photo.
- **Remove location data** from phone photos before adding them to the
  folder (on Windows: Properties > Details > Remove Properties; on Mac:
  Preview > Tools > Show Inspector > GPS > Remove Location Info).
- Only use pictures you took yourself, have permission for, or that are
  licensed for reuse.

---

## 7. Keep it fast on school Chromebooks

| | Budget |
|---|---|
| Whole room (`classroom.glb`) | under ~150,000 triangles; file under ~20 MB |
| Each character | under ~20,000 triangles; one or two 1024 px textures; file under ~5 MB |
| Each wall photo | under ~300 KB |
| Everything together | under ~50 MB |

Tables and chairs repeat 12 times. If you use `table.glb`, keep it simple
(under ~2,000 triangles).

---

## 8. Moving things

The floor-plan clue is drawn from the numbers in `data/mystery.js`, not from
your model. If you move a door, the trophy case or other furniture by more
than about half a meter, the poster and the 3D room will disagree, and
students may get a "wrong" answer that is actually right.

So don't edit `data/mystery.js` yourself. Instead, send the developer a
list of the new positions (Blender X, Y), and they'll update the layout and
the floor-plan clue together. Ask the same way if a story detail in section 4
doesn't work for you.

---

## 9. Before you hand files back

- [ ] File names match `data/assets.js` exactly (lower case, `.glb`)
- [ ] Draco compression was off; scale applied; 1 unit = 1 m
- [ ] `classroom.glb` has `COL_` boxes for every wall and big piece of furniture
- [ ] The player can't walk through walls or Doors A and B, can walk through the two inside doorways, and can reach every character
- [ ] The trophy case's top shelf is empty with a sensor pad; ribbons and medals are on the middle shelf
- [ ] Doors A and B are labelled and closed; the floor-plan poster spot is clear
- [ ] Characters face forward, stand on the floor, and are the right height in the game
- [ ] No `[assets] ... not loaded` messages in the console for files you delivered
- [ ] Photos: permission checked, location data removed, sizes within budget
- [ ] You played the game for a minute: walk around, talk to each person

When you're done, commit the files to the branch above or send them to the
developer, along with any position changes from section 8.
