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
| `classroom.glb` | The whole room: walls, floor, ceiling, windows, doors, furniture | **Recommended.** Must include `COL_` boxes (section 4). |
| `npc_ortiz.glb` | Ms. Ortiz, robotics coach (teacher) | 1.72 m |
| `npc_jordan.glb` | Jordan, hall pass monitor (student) | 1.68 m |
| `npc_marcus.glb` | Marcus, lab assistant (student) | 1.78 m |
| `npc_priya.glb` | Priya, robotics club programmer (student) | 1.62 m |
| `npc_riley.glb` | Riley, robotics club member (student) | 1.70 m |
| `npc_sam.glb` | Sam, team captain (student) | 1.75 m |
| `npc_ana.glb` | Ana, library aide visiting the room (student) | 1.60 m |
| `npc_student.glb` | A generic student, used for any character above that doesn't have a file yet | optional |

If you'd rather not build the whole room as one file, you can instead make
single pieces: `table.glb` (reused for all 16 student tables),
`trophy_case.glb`, `robotics_bench.glb` and `desk.glb`. Each piece's origin
must be at its **bottom centre**. The engine puts them in place. Don't do
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

### Size and directions

The room is **24 m (east–west) × 16 m (north–south)**, with a **3.4 m**
ceiling. The room's centre on the floor is Blender's origin (0, 0, 0).

| Direction in the story | In Blender |
|---|---|
| East | +X (X = 12 is the east wall) |
| West | −X (X = −12 is the west wall) |
| North (whiteboard wall) | +Y (Y = 8 is the north wall) |
| South (Door A wall) | −Y (Y = −8 is the south wall) |
| Up | +Z |

Look from Blender's **Top view** (numpad 7): north is at the top of the
screen and east is on the right, the same as the floor-plan clue.

### Where things go (Blender X, Y in meters, centre of the object)

These positions match the floor-plan clue that students read, so **the
mystery depends on them**. Small shifts (say 20 cm) are fine. For bigger
moves, see "Moving things" below.

| Object | X | Y | Size (X × Y × height) | Notes |
|---|---|---|---|---|
| Door A (Main) | −6 | −8 | 1.6 wide, 2.2 tall | South wall. Label it "Door A". |
| Door B (East) | 12 | 4 | 1.6 wide, 2.2 tall | East wall. Label it "Door B". |
| **Trophy case** | 11.55 | 1.4 | 0.8 × 2.2 × 1.9 | Against the east wall, just south of Door B. Glass front faces west (into the room). |
| Teacher's desk | −1 | 5.8 | 2.2 × 0.9 × 0.78 | |
| Whiteboard | −1 | 7.9 | 6 wide, 1.2 tall | North wall; bottom edge 1.0 m off the floor |
| Storage closet | −10.5 | 6.6 | 3 × 2.8, floor to ceiling | Northwest corner; its door faces east |
| Plant shelf | −11.6 | −0.5 | 0.7 × 4 × 0.9 | West wall, with potted plants |
| Windows | west wall, Y from −6 to 2 | | about 1.4 tall, centred 1.8 m up | |
| Hall pass desk | −4 | −6.6 | 1.6 × 0.8 × 0.78 | Just inside Door A |
| Robotics bench 1 | 7.5 | −3.2 | 3.2 × 1.1 × 0.9 | Robot parts on top |
| Robotics bench 2 | 7.5 | −6.2 | 3.2 × 1.1 × 0.9 | |
| Parts cabinet | 11.6 | −5.5 | 0.7 × 2.5 × 2.0 | East wall |
| Library book cart | 2.6 | −7.1 | 1.2 × 0.6 × 1.0 | Ana's cart |
| Student tables (16) | X = −7, −4, −1, 2 | Y = 2.6, 0.2, −2.2, −4.6 | 2 × 0.8 × 0.75 each | Two chairs per table, on the south (−Y) side |

**Keep this wall space clear:** the game hangs the **floor-plan poster** (a
clue) on the south wall at X = −2.6, centred 1.6 m up and about 1.3 m wide.

### Story details the art must show

Students are told these things, so the model has to agree:

- **Trophy case:** glass door closed. **Top shelf empty**, with a small dark
  sensor pad where the trophy stood. **Middle shelf:** ribbons and medals.
  **Bottom shelf:** a couple of small trophies. **Don't model the missing
  championship trophy anywhere in the room.**
- **Doors A and B are closed.** Students can't leave the room.
- Jordan's hall pass desk faces Door A. You can't see the trophy case from
  it (the story relies on that).
- The plant shelf (Priya) is on the far west side, away from the case.
- It's 3:55 PM after school: daylight through the west windows is fine.

### Required helper objects

Add these to `classroom.glb`. They're how the game knows where people can
walk and stand.

1. **Collision boxes: name each one `COL_` + anything** (for example
   `COL_wall_north`, `COL_trophy_case`, `COL_table_03`). Use plain cubes.
   The game makes them invisible and stops the player at them. Add one for
   each wall (including both closed doors) and each large piece of
   furniture. Only their footprint matters, so height can be rough.
   Rotated boxes are treated as their straight bounding box, so keep them
   aligned to the X and Y axes. If there are **no** `COL_` objects in the
   file, the game uses its own built-in walls.

2. **Standing spots: Empties named `SPAWN_` + name** (Add > Empty > Plain
   Axes). These are optional: if you leave them out, the game uses the
   default spots below.

| Empty name | Who | Default X, Y |
|---|---|---|
| `SPAWN_player` | The student playing | −6, −6.2 (just inside Door A) |
| `SPAWN_ortiz` | Ms. Ortiz | −1, 4.9 (in front of her desk) |
| `SPAWN_jordan` | Jordan | −4, −5.8 (at the hall pass desk) |
| `SPAWN_marcus` | Marcus | 6.2, −2.3 (by robotics bench 1) |
| `SPAWN_priya` | Priya | −10.5, −0.5 (by the plant shelf) |
| `SPAWN_riley` | Riley | −1, −1.2 (among the student tables) |
| `SPAWN_sam` | Sam | 8.9, −4.7 (between the robotics benches) |
| `SPAWN_ana` | Ana | 3.8, −6.6 (by the book cart) |

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
  is a good hint for their main clothing colour: Ortiz blue `#3d6fb4`,
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
sam: { url: 'assets/models/npc_sam.glb', height: 1.75, portrait: 'assets/photos/portrait_sam.jpg' },
```

If the photo file is missing, the game shows a coloured dot instead.

### Wall pictures

Add each picture to the `pictures` list at the bottom of `data/assets.js`:

```js
pictures: [
  { url: 'assets/photos/team_photo.jpg', wall: 'north', x: 6, height: 1.7, width: 1.4 },
  { url: 'assets/photos/robot_poster.jpg', wall: 'east', y: 6.5, height: 1.6, width: 1.0 }
]
```

- `wall`: `north`, `south`, `east` or `west`
- Position uses the same Blender coordinates as section 4: for `north` and
  `south` walls give `x` (−12 to 12); for `east` and `west` walls give `y`
  (−8 to 8).
- `height`: how high the picture's centre is (1.6 m is eye level).
  `width` is in meters; the picture's height comes from the photo's shape.
- Don't cover the doors, the windows or the floor-plan poster spot
  (south wall, x = −2.6).

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

Tables and chairs repeat 16 times. If you use `table.glb`, keep it simple
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
- [ ] The player can't walk through walls or doors, and can reach every character
- [ ] The trophy case's top shelf is empty with a sensor pad; ribbons and medals are on the middle shelf
- [ ] Doors A and B are labelled and closed; the floor-plan poster spot is clear
- [ ] Characters face forward, stand on the floor, and are the right height in the game
- [ ] No `[assets] ... not loaded` messages in the console for files you delivered
- [ ] Photos: permission checked, location data removed, sizes within budget
- [ ] You played the game for a minute: walk around, talk to each person

When you're done, commit the files to the branch above or send them to the
developer, along with any position changes from section 8.
