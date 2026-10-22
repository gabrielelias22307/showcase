"""
Classroom Mystery - Blender starter script (v2: the real Room 210 suite)
=======================================================================
Builds a blocked-out version of the real classroom from the photos:
  - Classroom (south part) with a blue painted east wall, a counter with
    plants and upper cabinets, whiteboards, TV, hall pass desk, 12 tables.
  - Computer lab (north-west) with the trophy case beside Door B,
    computer desks, two yearbook layout tables, a camera cabinet, a rolling
    whiteboard and a sink.
  - Small office (north-east) with a desk and filing cabinets.
  - Cream painted block walls, blue door frames, blue baseboard, tile
    floor with red accent tiles, paper pennant banners.
  - COL_ collision boxes (wireframes) and SPAWN_ standing spots.

Positions match data/mystery.js and HANDOVER.md section 4.
Blender X = east, Blender Y = north. The room centre is (0, 0, 0).

HOW TO USE
  1. Open Blender and go to the Scripting tab.
  2. Click New, paste this whole script, then click Run Script (Alt+P).
  3. Switch the viewport to Material Preview to see colours and textures.
  4. Top view (numpad 7): north is up, east is right - same as the floor plan.

PHOTO TEXTURES (optional)
  Set TEXTURE_DIR below to the game's  classroom-mystery/assets/textures
  folder. The walls, blue wall, floor and wood then use the textures made
  from the real room photos. Leave it empty to use plain colours.

RUNNING IT AGAIN rebuilds everything inside the "Classroom" collections
from scratch. Anything you modelled INSIDE those collections is deleted,
so save first, or move your own work into a different collection.

WHAT GETS EXPORTED
  Only the "Classroom" collection (Room + Collision + Spawns).
  "Guides_DoNotExport" marks the floor-plan poster spot (keep it clear).
  To export by hand: right-click the "Classroom" collection in the
  Outliner > Select Objects, then File > Export > glTF 2.0 with the
  settings in HANDOVER.md section 3.
  Or fill in EXPORT_PATH below and the script exports for you.
"""

import math
import os
import bpy

# Optional: full path to save the file, for example
#   r"C:\Users\you\showcase\classroom-mystery\assets\models\classroom.glb"
EXPORT_PATH = ""

# Optional: folder with the photo textures, for example
#   r"C:\Users\you\showcase\classroom-mystery\assets\textures"
TEXTURE_DIR = ""

TEXTURES = {   # file name, and how many meters one copy of it covers
    "wall": ("tex_block_cream.jpg", 2.05),
    "accent": ("tex_block_blue.jpg", 2.05),
    "floor": ("tex_floor_tile.jpg", 2.44),
    "wood": ("tex_wood_drawers.jpg", 1.2),
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def hexcol(h):
    """'#rrggbb' -> linear RGB (what Blender materials expect)."""
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexc, alpha=1.0, rough=0.6, metal=0.0, image=None, emit=0.0, double=False):
    m = bpy.data.materials.get("CM_" + name) or bpy.data.materials.new("CM_" + name)
    m.use_nodes = True
    rgb = hexcol(hexc)
    nodes = m.node_tree.nodes
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    for n in [n for n in nodes if n.type == "TEX_IMAGE"]:
        nodes.remove(n)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
        bsdf.inputs["Alpha"].default_value = alpha
        if emit:
            for key in ("Emission Color", "Emission"):
                if key in bsdf.inputs:
                    bsdf.inputs[key].default_value = (*rgb, 1.0)
                    break
            bsdf.inputs["Emission Strength"].default_value = emit
        if image is not None:
            tex = nodes.new("ShaderNodeTexImage")
            tex.image = image
            m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    m.diffuse_color = (*rgb, alpha)
    m.use_backface_culling = not double
    if alpha < 1.0:
        for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
    return m


def load_image(key):
    if not TEXTURE_DIR:
        return None
    path = os.path.join(TEXTURE_DIR, TEXTURES[key][0])
    if not os.path.exists(path):
        print("[classroom] texture not found, using a colour:", path)
        return None
    return bpy.data.images.load(path, check_existing=True)


class Shape:
    """Collects boxes and cylinders into one mesh, with texture coordinates
    in meters divided by `tile` (so textures keep their real size)."""

    def __init__(self):
        self.verts, self.faces, self.mats, self.uvs = [], [], [], []

    def box(self, cx, cy, z0, sx, sy, sz, mi=0, tile=1.0):
        """Box centred on (cx, cy), bottom at z0, size sx * sy * sz (meters)."""
        x0, x1 = cx - sx / 2, cx + sx / 2
        y0, y1 = cy - sy / 2, cy + sy / 2
        z1 = z0 + sz
        n = len(self.verts)
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        self.verts += v
        # bottom, top, south, east, north, west; uv axes for each face
        for f, axes in (((0, 3, 2, 1), (0, 1)), ((4, 5, 6, 7), (0, 1)), ((0, 1, 5, 4), (0, 2)),
                        ((1, 2, 6, 5), (1, 2)), ((2, 3, 7, 6), (0, 2)), ((3, 0, 4, 7), (1, 2))):
            self.faces.append(tuple(n + i for i in f))
            self.mats.append(mi)
            self.uvs.append([(v[i][axes[0]] / tile, v[i][axes[1]] / tile) for i in f])
        return self

    def cyl(self, cx, cy, z0, r, h, mi=0, r_top=None, seg=16):
        """Upright cylinder (or cone if r_top differs), bottom at z0."""
        r_top = r if r_top is None else r_top
        n = len(self.verts)
        for rad, z in ((r, z0), (r_top, z0 + h)):
            for i in range(seg):
                a = 2 * math.pi * i / seg
                self.verts.append((cx + rad * math.cos(a), cy + rad * math.sin(a), z))
        for i in range(seg):
            j = (i + 1) % seg
            self.faces.append((n + i, n + j, n + seg + j, n + seg + i))
            self.mats.append(mi)
            self.uvs.append([(i / seg, 0), (j / seg, 0), (j / seg, 1), (i / seg, 1)])
        top = tuple(n + seg + i for i in range(seg))
        bottom = tuple(n + i for i in reversed(range(seg)))
        for f in (top, bottom):
            self.faces.append(f)
            self.mats.append(mi)
            self.uvs.append([(0.5, 0.5)] * seg)
        return self

    def tri(self, a, b, c, mi=0):
        n = len(self.verts)
        self.verts += [a, b, c]
        self.faces.append((n, n + 1, n + 2))
        self.mats.append(mi)
        self.uvs.append([(0, 0), (1, 0), (0.5, 1)])
        return self


def build(name, shape, mats, loc=(0, 0, 0), coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(shape.verts, [], shape.faces)
    for m in mats:
        me.materials.append(m)
    uv = me.uv_layers.new(name="UVMap")
    for poly, mi, uvs in zip(me.polygons, shape.mats, shape.uvs):
        poly.material_index = mi
        for li, coord in zip(poly.loop_indices, uvs):
            uv.data[li].uv = coord
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    (coll or ROOM).objects.link(ob)
    return ob


def label(name, text, loc, rot_deg, size, material, coll=None):
    """Flat 3D text, turned into a mesh so it exports to .glb."""
    cu = bpy.data.curves.new(name + "_text", "FONT")
    cu.body = text
    cu.size = size
    cu.extrude = 0.004
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    ROOM.objects.link(tmp)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)
    me.name = name
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    (coll or ROOM).objects.link(ob)
    return ob


def col_box(name, cx, cy, sx, sy, h=1.2):
    """Invisible-in-game collision box. Only the footprint matters."""
    ob = build("COL_" + name, Shape().box(0, 0, 0, sx, sy, h), [], (cx, cy, 0), COLL)
    ob.display_type = "WIRE"
    ob.hide_render = True
    return ob


def spawn(name, x, y):
    ob = bpy.data.objects.new("SPAWN_" + name, None)
    ob.empty_display_type = "PLAIN_AXES"
    ob.empty_display_size = 0.5
    ob.location = (x, y, 0)
    SPAWNS.objects.link(ob)
    return ob


# ------------------------------------------------------------------
# Fresh start (only touches this script's own collections)
# ------------------------------------------------------------------

try:
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
except Exception:
    pass

OUR_COLLECTIONS = ("Classroom", "Classroom_Room", "Classroom_Collision",
                   "Classroom_Spawns", "Guides_DoNotExport")
for cname in OUR_COLLECTIONS:
    old = bpy.data.collections.get(cname)
    if old:
        for ob in list(old.all_objects):
            data = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)
for cname in OUR_COLLECTIONS:
    old = bpy.data.collections.get(cname)
    if old:
        bpy.data.collections.remove(old)

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0


def new_coll(name, parent):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c


ROOT = new_coll("Classroom", scene.collection)
ROOM = new_coll("Classroom_Room", ROOT)
COLL = new_coll("Classroom_Collision", ROOT)
SPAWNS = new_coll("Classroom_Spawns", ROOT)
GUIDES = new_coll("Guides_DoNotExport", scene.collection)

# ------------------------------------------------------------------
# Materials - colours measured from the real room photos
# ------------------------------------------------------------------

IMG = {k: load_image(k) for k in TEXTURES}
TILE = {k: (TEXTURES[k][1] if IMG[k] else 1.0) for k in TEXTURES}

M = {
    "wall": mat("WallBlock", "#e3dcc6", rough=0.9, image=IMG["wall"]),
    "accent": mat("BlueBlock", "#8fa3c2", rough=0.9, image=IMG["accent"]),
    "floor": mat("FloorTile", "#ddd8cb", rough=0.35, image=IMG["floor"]),
    "wood": mat("WoodCasework", "#a8763e", rough=0.6, image=IMG["wood"]),
    "ceiling": mat("Ceiling", "#f4f4f2", rough=0.9),
    "light": mat("LightPanel", "#ffffff", emit=2.0),
    "frame": mat("BlueFrame", "#7d93b5", rough=0.5),
    "base": mat("BlueBaseboard", "#3f5f99", rough=0.7),
    "door": mat("WoodDoor", "#a8763e", rough=0.5),
    "metal": mat("Metal", "#9aa3ad", rough=0.4, metal=0.6),
    "label": mat("LabelText", "#1f3b63"),
    "darkwood": mat("DarkWood", "#5e4026"),
    "glass": mat("Glass", "#bfe3f2", alpha=0.25, rough=0.05),
    "sensor": mat("SensorPad", "#111114", rough=0.3),
    "gold": mat("Gold", "#d4a62a", rough=0.3, metal=1.0),
    "silver": mat("Silver", "#c8ccd2", rough=0.3, metal=1.0),
    "ribbon_blue": mat("RibbonBlue", "#2b5fb4"),
    "ribbon_red": mat("RibbonRed", "#b23a48"),
    "whiteboard": mat("Whiteboard", "#f7f7f7", rough=0.15),
    "counter": mat("CounterTop", "#4b4f4f", rough=0.5),
    "pot": mat("Pot", "#b5603a"),
    "plant": mat("Plant", "#3f8a3a"),
    "tabletop": mat("TableTop", "#c9cccc", rough=0.5),
    "chair": mat("NavyChair", "#1c2533", rough=0.6),
    "black": mat("Black", "#1d1f22", rough=0.5),
    "screen": mat("Screen", "#0d0f12", rough=0.2),
    "bench": mat("BenchTop", "#3b3f46", rough=0.5),
    "cabinet": mat("GreyCabinet", "#c4c7cb"),
    "proof": mat("ProofPaper", "#fbfbf6"),
    "photo1": mat("ProofPhoto1", "#6a8fbf"),
    "photo2": mat("ProofPhoto2", "#c98a5a"),
    "mat": mat("CuttingMat", "#3f7d5a"),
    "white": mat("WhiteFrame", "#fbfbfb", rough=0.3),
    "book1": mat("Book1", "#3a6ea5"),
    "book2": mat("Book2", "#c4533a"),
    "book3": mat("Book3", "#4f8a4b"),
    "guide": mat("GUIDE_KeepClear", "#ff2a2a", alpha=0.35),
}
PENNANT = [mat(f"Pennant{i}", c, double=True) for i, c in
           enumerate(("#e94b3c", "#f2c12e", "#3b7dd8", "#4caf50", "#e86fa5", "#7b5bc4"))]
NOTES = [mat(f"StickyNote{i}", c) for i, c in enumerate(("#ffe45c", "#ffb3d9", "#8fd3ff", "#b8f28a"))]

H = 3.4        # ceiling height
HEAD = 2.2     # top of doors and openings

# ------------------------------------------------------------------
# Floor, ceiling, light panels
# ------------------------------------------------------------------

build("Floor", Shape().box(0, 0, -0.1, 24, 16, 0.1, tile=TILE["floor"]), [M["floor"]])
build("Ceiling", Shape().box(0, 0, H, 24.4, 16.4, 0.1), [M["ceiling"]])
s = Shape()
x = -9.0
while x <= 9.01:
    for y in (-6, -3, 0, 3, 6):
        s.box(x, y, H - 0.03, 1.22, 0.61, 0.03)
    x += 3.6
build("CeilingLights", s, [M["light"]])

# ------------------------------------------------------------------
# Walls. A wall runs along X ("x") or Y ("y"). Gaps are doors/openings.
# ------------------------------------------------------------------


def wall(name, axis, fixed, a, b, thick, gaps, col_name=None):
    """Straight wall from a to b, centred on `fixed`, with gaps (lo, hi)."""
    s = Shape()
    trim = Shape()
    pieces = []
    cur = a
    for lo, hi in sorted(gaps):
        pieces.append((cur, lo))
        cur = hi
    pieces.append((cur, b))

    def add(sh, p, q, z0, z1, t, mi=0, tile=1.0):
        mid, ln = (p + q) / 2, q - p
        if axis == "x":
            sh.box(mid, fixed, z0, ln, t, z1 - z0, mi, tile)
        else:
            sh.box(fixed, mid, z0, t, ln, z1 - z0, mi, tile)

    for p, q in pieces:
        if q - p > 0.01:
            add(s, p, q, 0, H, thick, 0, TILE["wall"])
            add(trim, p, q, 0, 0.1, thick + 0.03, 1)              # blue baseboard
            if col_name:
                c = (p + q) / 2
                if axis == "x":
                    col_box(f"{col_name}_{len(COLL.objects)}", c, fixed, q - p, thick + 0.3, H)
                else:
                    col_box(f"{col_name}_{len(COLL.objects)}", fixed, c, thick + 0.3, q - p, H)
    for lo, hi in gaps:
        add(s, lo, hi, HEAD, H, thick, 0, TILE["wall"])           # wall above the gap
        add(trim, lo - 0.05, lo, 0, HEAD + 0.05, thick + 0.06)    # blue frame
        add(trim, hi, hi + 0.05, 0, HEAD + 0.05, thick + 0.06)
        add(trim, lo - 0.05, hi + 0.05, HEAD, HEAD + 0.05, thick + 0.06)
    build(name, s, [M["wall"]])
    build(name + "_Trim", trim, [M["frame"], M["base"]])


# Outside walls (inside faces at X = +-12 and Y = +-8). Doors are closed,
# so their gaps are covered by collision boxes below.
wall("Wall_North", "x", 8.1, -12.2, 12.2, 0.2, [(-9.6, -8.4)])           # Door B
wall("Wall_South", "x", -8.1, -12.2, 12.2, 0.2, [])
wall("Wall_West", "y", -12.1, -8, 8, 0.2, [(-6.6, -5.4)])                 # Door A
wall("Wall_East", "y", 12.1, -8, 8, 0.2, [])
col_box("wall_north", 0, 8.25, 25, 0.5, H)
col_box("wall_south", 0, -8.25, 25, 0.5, H)
col_box("wall_east", 12.25, 0, 0.5, 17, H)
col_box("wall_west", -12.25, 0, 0.5, 17, H)

# Inside walls with open doorways: lab opening (x 2.8-4.2), office (8.3-9.3)
wall("Wall_LabClassroom", "x", 2.0, -12, 12, 0.15, [(2.8, 4.2), (8.3, 9.3)], col_name="lab_wall")
wall("Wall_LabOffice", "y", 7.0, 2.075, 8, 0.15, [], col_name="office_wall")

# Blue painted east wall of the classroom (Y -8 to 2)
build("BlueWall_East", Shape().box(11.995, -3, 0, 0.01, 10, H, tile=TILE["accent"]), [M["accent"]])

# ------------------------------------------------------------------
# Doors (closed, wooden) + labels
# ------------------------------------------------------------------

s = Shape()
s.box(-9, 7.97, 0, 1.16, 0.05, 2.15, 0, TILE["wood"])
s.box(-8.6, 7.92, 1.0, 0.14, 0.04, 0.03, 1)
build("Door_B_Lab", s, [M["door"], M["metal"]])
label("Label_Door_B", "Door B (Lab)", (-9, 7.94, 2.5), (90, 0, 0), 0.2, M["label"])

s = Shape()
s.box(-11.97, -6, 0, 0.05, 1.16, 2.15, 0, TILE["wood"])
s.box(-11.92, -5.6, 1.0, 0.04, 0.14, 0.03, 1)
s.box(-11.96, -5.15, 0.9, 0.04, 0.35, 1.25, 2)                 # glass side panel
build("Door_A_Main", s, [M["door"], M["metal"], M["glass"]])
label("Label_Door_A", "Door A (Main)", (-11.94, -6, 2.5), (90, 0, 90), 0.2, M["label"])

# ------------------------------------------------------------------
# Paper pennant banners along the tops of the walls
# ------------------------------------------------------------------


def bunting(s, x1, y1, x2, y2, nx, ny, k0=0):
    ln = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / ln, (y2 - y1) / ln
    k, d = k0, 0.3
    while d + 0.26 < ln:
        sag = math.sin(((d % 2.2) / 2.2) * math.pi) * 0.12
        ax, ay = x1 + ux * d + nx * 0.04, y1 + uy * d + ny * 0.04
        bx, by = ax + ux * 0.26, ay + uy * 0.26
        tx, ty = ax + ux * 0.13, ay + uy * 0.13
        s.tri((ax, ay, 2.95 - sag), (bx, by, 2.95 - sag), (tx, ty, 2.65 - sag), k % 6)
        k += 1
        d += 0.55
    return k


s = Shape()
k = 0
for run in (((-12, -8, 12, -8), (0, 1)), ((-12, 1.925, 12, 1.925), (0, -1)),
            ((-12, 2, -12, -8), (1, 0)), ((12, 2, 12, -8), (-1, 0)),
            ((-12, 8, 7, 8), (0, -1)), ((-12, 2.075, 6.925, 2.075), (0, 1)),
            ((-12, 8, -12, 2), (1, 0)), ((6.925, 8, 6.925, 2.075), (-1, 0))):
    (x1, y1, x2, y2), (nx, ny) = run
    k = bunting(s, x1, y1, x2, y2, nx, ny, k)
build("Pennants", s, PENNANT)

# ------------------------------------------------------------------
# CLASSROOM (south part)
# ------------------------------------------------------------------

# Tall wood cabinet in the north-west corner (the flag stands beside it)
build("TallCabinet", Shape().box(0, 0, 0, 1.0, 0.7, 2.2, 0, TILE["wood"]), [M["wood"]], (-11.45, 1.55, 0))
col_box("tall_cabinet", -11.45, 1.55, 1.0, 0.7, 2.2)

# Teacher's desk (grey top, metal body)
s = Shape()
s.box(0, 0, 0.71, 2.0, 0.8, 0.05, 0)
s.box(0.6, 0, 0, 0.7, 0.75, 0.71, 1)
s.box(-0.97, 0, 0, 0.04, 0.75, 0.71, 1)
s.box(0, 0.38, 0.3, 2.0, 0.03, 0.41, 1)
build("TeacherDesk", s, [M["tabletop"], M["metal"]], (-8.6, 0.95, 0))
col_box("teacher_desk", -8.6, 0.95, 2.0, 0.8, 0.76)

# TV on a stand + YEARBOOK sign above it
s = Shape()
s.box(0, 0, 1.08, 1.7, 0.06, 0.95, 0)
s.box(-0.6, 0.1, 0, 0.05, 0.05, 1.3, 1)
s.box(0.6, 0.1, 0, 0.05, 0.05, 1.3, 1)
s.box(0, 0.1, 0, 1.4, 0.5, 0.05, 1)
build("TV", s, [M["screen"], M["white"]], (-5.4, 1.6, 0))
col_box("tv", -5.4, 1.6, 1.7, 0.5, 1.9)
label("Sign_Yearbook", "YEARBOOK", (-5.4, 1.91, 2.65), (90, 0, 0), 0.3, M["label"])

# Whiteboards (no writing - the real boards had student names on them)
s = Shape()
s.box(0, 0, 1.0, 3.4, 0.03, 1.2, 0)
s.box(0, -0.04, 0.97, 3.4, 0.08, 0.03, 1)
build("Whiteboard_North", s, [M["whiteboard"], M["metal"]], (-1.2, 1.9, 0))
s = Shape()
s.box(0, 0, 1.0, 0.03, 4.0, 1.2, 0)
s.box(0.04, 0, 0.97, 0.08, 4.0, 0.03, 1)
build("Whiteboard_West", s, [M["whiteboard"], M["metal"]], (-11.97, -1.4, 0))

# Drawer cabinet beside Door A
s = Shape()
s.box(0, 0, 0, 0.6, 1.1, 0.86, 0, TILE["wood"])
s.box(0, 0, 0.86, 0.62, 1.12, 0.04, 1)
build("DrawerCabinet", s, [M["wood"], M["counter"]], (-11.65, -4.25, 0))
col_box("drawers", -11.65, -4.25, 0.6, 1.1, 0.9)

# Hall pass desk just inside Door A (Jordan sits on its east side, facing the door)
s = Shape()
s.box(0, 0, 0.71, 0.8, 1.6, 0.05, 0)
for dx in (-0.35, 0.35):
    for dy in (-0.75, 0.75):
        s.box(dx, dy, 0, 0.04, 0.04, 0.71, 1)
s.box(-0.38, 0, 0.3, 0.03, 1.5, 0.41, 1)            # front panel facing the door
s.box(0, 0.3, 0.76, 0.23, 0.31, 0.01, 2)            # sign-out clipboard
build("HallPassDesk", s, [M["tabletop"], M["metal"], M["whiteboard"]], (-9.4, -6, 0))
col_box("hall_pass_desk", -9.4, -6, 0.8, 1.6, 0.76)

# Counter along the blue east wall: wood base, dark top, upper cabinets, plants
s = Shape()
s.box(0, 0, 0, 0.71, 7.0, 0.86, 0, TILE["wood"])
s.box(0, 0, 0.86, 0.75, 7.02, 0.04, 1)
s.box(0.2, 0, 1.475, 0.35, 7.0, 0.75, 0, TILE["wood"])    # upper cabinets on the wall
for dy in (3.1, 2.4, 1.7, 1.0):                               # plants at the north end
    s.cyl(0, dy, 0.9, 0.11, 0.2, 2, r_top=0.14)
    s.cyl(0, dy, 1.1, 0.19, 0.3, 3, r_top=0.06)
build("PlantCounter", s, [M["wood"], M["counter"], M["pot"], M["plant"]], (11.62, -3.6, 0))
col_box("plant_counter", 11.62, -3.6, 0.75, 7.0, 0.9)

# Black bookshelf in the south-east corner
s = Shape()
s.box(0, 0.16, 0, 1.0, 0.03, 1.8)
s.box(-0.485, 0, 0, 0.03, 0.35, 1.8)
s.box(0.485, 0, 0, 0.03, 0.35, 1.8)
for z in (0.02, 0.47, 0.92, 1.37, 1.77):
    s.box(0, 0, z, 1.0, 0.35, 0.03)
build("Bookshelf", s, [M["black"]], (11.1, -7.65, 0))
col_box("bookshelf", 11.1, -7.65, 1.0, 0.35, 1.8)

# Library book cart (Ana's)
s = Shape()
for z in (0.35, 0.9):
    s.box(0, 0, z, 1.2, 0.6, 0.04, 0)
for dx in (-0.58, 0.58):
    for dy in (-0.28, 0.28):
        s.box(dx, dy, 0, 0.04, 0.04, 1.0, 0)
for i in range(8):
    s.box(-0.49 + i * 0.14, 0, 0.94, 0.09, 0.22, 0.22 + 0.03 * (i % 3), 1 + i % 3)
build("BookCart", s, [M["metal"], M["book1"], M["book2"], M["book3"]], (6.5, -7.3, 0))
col_box("book_cart", 6.5, -7.3, 1.2, 0.6, 1.0)

# Student tables: grey tops, navy chairs on the south side. 4 columns x 3 rows.
table = Shape()
table.box(0, 0, 0.71, 2.0, 0.8, 0.04, 0)
for dx in (-0.92, 0.92):
    for dy in (-0.32, 0.32):
        table.box(dx, dy, 0, 0.04, 0.04, 0.71, 1)
chair = Shape()
chair.box(0, 0, 0.43, 0.44, 0.42, 0.05, 0)
chair.box(0, -0.21, 0.48, 0.44, 0.05, 0.4, 0)
for dx in (-0.18, 0.18):
    for dy in (-0.18, 0.18):
        chair.box(dx, dy, 0, 0.025, 0.025, 0.43, 1)
n = 0
for ty in (-0.6, -3.2, -5.8):
    for tx in (-6, -2.5, 1, 4.5):
        n += 1
        build(f"Table_{n:02d}", table, [M["tabletop"], M["metal"]], (tx, ty, 0))
        for side, dx in (("a", -0.5), ("b", 0.5)):
            build(f"Chair_{n:02d}{side}", chair, [M["chair"], M["metal"]], (tx + dx, ty - 0.55, 0))
        col_box(f"table_{n:02d}", tx, ty, 2.0, 0.8, 0.75)

# ------------------------------------------------------------------
# COMPUTER LAB (north-west)
# ------------------------------------------------------------------

# Trophy case against the north wall, right next to Door B. Glass faces south.
TC = (-6.8, 7.55, 0)
s = Shape()
s.box(0, 0, 0, 2.2, 0.8, 0.15)                   # base (bottom shelf surface 0.15)
s.box(0, 0.38, 0.15, 2.2, 0.04, 1.71)            # back panel (against the wall)
s.box(-1.08, 0, 0.15, 0.04, 0.8, 1.71)           # sides
s.box(1.08, 0, 0.15, 0.04, 0.8, 1.71)
s.box(0, 0, 1.86, 2.2, 0.8, 0.04)                # top
s.box(0, 0.02, 0.72, 2.12, 0.72, 0.03)           # middle shelf (surface 0.75)
s.box(0, 0.02, 1.27, 2.12, 0.72, 0.03)           # top shelf (surface 1.30)
build("TrophyCase", s, [M["darkwood"]], TC)
build("TrophyCase_GlassDoor", Shape().box(0, -0.39, 0.15, 2.12, 0.02, 1.71), [M["glass"]], TC)
# Top shelf: EMPTY except the dark sensor pad where the trophy stood
build("TrophyCase_SensorPad", Shape().box(0, 0, 1.30, 0.3, 0.3, 0.012), [M["sensor"]], TC)
# Middle shelf: ribbons on the back + medals. Bottom shelf: two small trophies.
s = Shape()
for x, mi in ((-0.7, 0), (-0.1, 1), (0.5, 0)):
    s.box(x, 0.34, 0.85, 0.07, 0.01, 0.22, mi)
    s.box(x, 0.335, 1.05, 0.14, 0.012, 0.14, mi)
for x, mi in ((-0.85, 2), (-0.4, 3), (0.25, 2), (0.8, 3)):
    s.cyl(x, -0.05, 0.75, 0.04, 0.008, mi)
for x, sc in ((-0.5, 1.0), (0.5, 0.8)):
    s.box(x, 0.05, 0.15, 0.12 * sc, 0.12 * sc, 0.06 * sc, 4)
    s.cyl(x, 0.05, 0.15 + 0.06 * sc, 0.015, 0.10 * sc, 2)
    s.cyl(x, 0.05, 0.15 + 0.16 * sc, 0.035 * sc, 0.10 * sc, 2, r_top=0.06 * sc)
build("TrophyCase_Contents", s,
      [M["ribbon_blue"], M["ribbon_red"], M["gold"], M["silver"], M["darkwood"]], TC)
col_box("trophy_case", -6.8, 7.55, 2.2, 0.8, 1.9)

# Computer desks along the north wall
s = Shape()
s.box(0, 0, 0.71, 6.8, 0.8, 0.04, 0, TILE["wood"])
s.box(-3.37, 0, 0, 0.05, 0.75, 0.71, 0, TILE["wood"])
s.box(3.37, 0, 0, 0.05, 0.75, 0.71, 0, TILE["wood"])
x = -2.7
while x < 3.1:
    s.box(x, 0.2, 0.9, 0.55, 0.03, 0.34, 1)                  # monitor
    s.box(x, 0.22, 0.75, 0.06, 0.06, 0.15, 2)                # stand
    s.box(x + 0.45, 0.15, 0.75, 0.2, 0.42, 0.4, 2)          # tower
    s.box(x, -0.7, 0.43, 0.44, 0.42, 0.05, 3)                # chair seat
    s.box(x, -0.91, 0.48, 0.44, 0.05, 0.4, 3)                # chair back
    x += 1.4
build("ComputerDesks", s, [M["wood"], M["screen"], M["black"], M["chair"]], (2.6, 7.55, 0))
col_box("computer_desks", 2.6, 7.55, 6.8, 0.8, 0.75)

# Two yearbook layout tables: page proofs, a camera, a cutting mat
for i, bx in ((1, -2.4), (2, 2.6)):
    s = Shape()
    s.box(0, 0, 0.86, 3.2, 1.1, 0.04, 0)
    s.box(0, 0, 0, 3.1, 1.0, 0.86, 1)
    s.box(0.9, 0, 0.9, 0.9, 0.6, 0.005, 5)                       # cutting mat
    for k in range(6):                                            # proof pages with photos
        px, py = -1.25 + (k % 3) * 0.42, 0.2 - (k // 3) * 0.36
        s.box(px, py, 0.9 + k * 0.001, 0.36, 0.28, 0.004, 2)
        s.box(px - 0.07, py + 0.05, 0.905 + k * 0.001, 0.15, 0.11, 0.002, 3)
        s.box(px + 0.09, py - 0.06, 0.905 + k * 0.001, 0.12, 0.09, 0.002, 4)
    if i == 1:                                                    # camera
        s.box(0.6, 0.25, 0.9, 0.14, 0.07, 0.09, 6)
        s.cyl(0.6, 0.19, 0.91, 0.035, 0.07, 6)
    build(f"LayoutTable_{i}", s, [M["bench"], M["metal"], M["proof"], M["photo1"], M["photo2"], M["mat"], M["black"]], (bx, 4.6, 0))
    col_box(f"layout_table_{i}", bx, 4.6, 3.2, 1.1, 0.9)

# Grey metal camera cabinet against the office wall, doors facing west
s = Shape()
s.box(0, 0, 0, 0.7, 1.6, 2.0, 0)
s.box(-0.36, 0, 0.05, 0.02, 0.01, 1.9, 1)
build("CameraCabinet", s, [M["cabinet"], M["metal"]], (6.55, 6.3, 0))
col_box("camera_cabinet", 6.55, 6.3, 0.7, 1.6, 2.0)

# Rolling whiteboard covered in sticky notes (facing east)
s = Shape()
s.box(0, 0, 1.03, 0.04, 1.8, 1.05, 0)
s.box(0, -0.92, 0, 0.05, 0.05, 2.05, 0)
s.box(0, 0.92, 0, 0.05, 0.05, 2.05, 0)
s.box(0, 0, 0.1, 0.6, 1.9, 0.05, 0)
for i in range(26):
    ny = -0.75 + ((i * 37) % 100) / 100 * 1.5
    nz = 1.15 + ((i * 53) % 100) / 100 * 0.8
    s.box(0.025, ny, nz, 0.005, 0.075, 0.075, 1 + i % 4)
build("RollingWhiteboard", s, [M["white"]] + NOTES, (-10.4, 4.6, 0))
col_box("rolling_whiteboard", -10.4, 4.6, 0.6, 1.8, 2.1)

# Sink counter on the west wall
s = Shape()
s.box(0, 0, 0, 0.66, 1.4, 0.86, 0)
s.box(0, 0, 0.86, 0.7, 1.42, 0.04, 1)
s.box(0.05, 0, 0.9, 0.42, 0.7, 0.01, 0)
build("Sink", s, [M["metal"], M["counter"]], (-11.65, 6.6, 0))
col_box("sink", -11.65, 6.6, 0.7, 1.4, 0.9)

# ------------------------------------------------------------------
# OFFICE (north-east)
# ------------------------------------------------------------------

s = Shape()
s.box(0, 0, 0.71, 1.5, 0.7, 0.05, 0)
s.box(0.45, 0, 0, 0.5, 0.65, 0.71, 1)
s.box(-0.72, 0, 0, 0.04, 0.65, 0.71, 1)
build("OfficeDesk", s, [M["tabletop"], M["metal"]], (10.4, 7.25, 0))
col_box("office_desk", 10.4, 7.25, 1.5, 0.7, 0.76)
for i, fy in ((1, 5.3), (2, 4.7)):
    s = Shape()
    s.box(0, 0, 0, 0.6, 0.5, 1.35, 0)
    for z in (0.3, 0.63, 0.96, 1.29):
        s.box(-0.31, 0, z - 0.1, 0.02, 0.12, 0.03, 1)
    build(f"FilingCabinet_{i}", s, [M["black"], M["metal"]], (11.7, fy, 0))
    col_box(f"filing_{i}", 11.7, fy, 0.6, 0.5, 1.35)

# ------------------------------------------------------------------
# Standing spots (SPAWN_) - Blender X, Y
# ------------------------------------------------------------------

for who, sx, sy in (("player", -11.0, -6.0), ("ortiz", -8.6, -0.2), ("jordan", -8.6, -6.0),
                    ("marcus", -2.4, 3.5), ("priya", 10.3, -1.4), ("riley", -0.75, -2.0),
                    ("sam", 5.6, 4.6), ("ana", 6.5, -6.4), ("grump", 9.6, 5.6)):
    spawn(who, sx, sy)

# ------------------------------------------------------------------
# Guide (NOT exported): floor-plan poster spot - keep this wall clear
# ------------------------------------------------------------------

g = build("GUIDE_FloorPlanPoster_KeepClear",
          Shape().box(-7.5, -7.97, 1.1, 1.3, 0.04, 1.0), [M["guide"]], coll=GUIDES)
g.hide_render = True

# ------------------------------------------------------------------
# Optional export
# ------------------------------------------------------------------

if EXPORT_PATH:
    for ob in bpy.context.view_layer.objects:
        ob.select_set(False)
    for ob in ROOT.all_objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=EXPORT_PATH,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
        export_extras=False,
        export_draco_mesh_compression_enable=False,
        export_image_format="JPEG",
        export_animations=False,
    )
    print("[classroom] exported to", EXPORT_PATH)

tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons)
           for ob in ROOM.all_objects if ob.type == "MESH")
print(f"[classroom] built: {len(ROOM.objects)} room objects, "
      f"{len(COLL.objects)} COL_ boxes, {len(SPAWNS.objects)} SPAWN_ spots, "
      f"about {tris:,} triangles, textures: {'on' if any(IMG.values()) else 'off'}")
