"""
Classroom Mystery - character: Gabriel (stylized, game-ready)
=============================================================
Built from four reference photos (front, 3/4, back, side):
black baseball cap, short dark hair and stubble, navy long-sleeve tee,
black joggers with cuffs, grey-brown hiking shoes.

- Faces Blender's Front view (looks toward -Y), feet on the floor (Z = 0).
- About 1.78 m tall (change HEIGHT below; the game also rescales to the
  height in data/assets.js).
- Smooth, simple shapes, well under the 20,000-triangle budget.
- Everything goes in a "Character_Gabriel" collection. Running the
  script again rebuilds only that collection.

Next steps (later): add an armature and "Idle" / "Talk" animations,
then export npc_<name>.glb (HANDOVER.md section 5).
"""

import math
import bpy
import bmesh

HEIGHT = 1.78
NAME = "Character_Gabriel"
S = HEIGHT / 1.78          # every number below is for a 1.78 m person


def hexcol(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexc, rough=0.7):
    m = bpy.data.materials.get("GB_" + name) or bpy.data.materials.new("GB_" + name)
    m.use_nodes = True
    rgb = hexcol(hexc)
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


M = {
    "skin": mat("Skin", "#d8a98c", 0.6),
    "stubble": mat("Stubble", "#b39580", 0.95),
    "hair": mat("HairDark", "#3a2f28", 0.9),
    "cap": mat("CapBlack", "#1b1c1f", 0.8),
    "shirt": mat("ShirtNavy", "#4b6487", 0.9),
    "pants": mat("PantsBlack", "#1f2023", 0.9),
    "shoe": mat("ShoeGreyBrown", "#6e695f", 0.8),
    "sole": mat("ShoeSole", "#2a2a2a", 0.9),
    "lace": mat("ShoeLace", "#3b3833", 0.9),
    "eye": mat("Eye", "#1c1a19", 0.3),
    "eyewhite": mat("EyeWhite", "#f1ece6", 0.4),
    "brow": mat("Brow", "#3a2d24", 0.9),
}


class Mesh:
    def __init__(self):
        self.v, self.f, self.m = [], [], []

    def loft(self, rings, mi, seg=24, cap0=True, cap1=True):
        """rings: [(cx, cy, z, rx, ry)] from bottom to top -> smooth tube."""
        base = len(self.v)
        for cx, cy, z, rx, ry in rings:
            for i in range(seg):
                a = 2 * math.pi * i / seg
                self.v.append((S * (cx + rx * math.cos(a)), S * (cy + ry * math.sin(a)), S * z))
        for r in range(len(rings) - 1):
            for i in range(seg):
                j = (i + 1) % seg
                a, b = base + r * seg + i, base + r * seg + j
                self.f.append((a, b, b + seg, a + seg))
                self.m.append(mi)
        for idx, cap in ((0, cap0), (len(rings) - 1, cap1)):
            if not cap:
                continue
            cx, cy, z, rx, ry = rings[idx]
            c = len(self.v)
            self.v.append((S * cx, S * cy, S * z))
            for i in range(seg):
                j = (i + 1) % seg
                a, b = base + idx * seg + i, base + idx * seg + j
                self.f.append((c, b, a) if idx == 0 else (c, a, b))
                self.m.append(mi)
        return self

    def ellipsoid(self, c, r, mi, lat=(-90, 90), lon=(0, 360), seg=(24, 16)):
        """Ellipsoid (or a piece of one). lat/lon in degrees; lon 270 = front (-Y)."""
        nu, nv = seg
        base = len(self.v)
        full = (lon[1] - lon[0]) >= 360
        cols = nu if full else nu + 1
        for j in range(nv + 1):
            la = math.radians(lat[0] + (lat[1] - lat[0]) * j / nv)
            for i in range(cols):
                lo = math.radians(lon[0] + (lon[1] - lon[0]) * i / nu)
                self.v.append((S * (c[0] + r[0] * math.cos(la) * math.cos(lo)),
                               S * (c[1] + r[1] * math.cos(la) * math.sin(lo)),
                               S * (c[2] + r[2] * math.sin(la))))
        for j in range(nv):
            for i in range(nu):
                i2 = (i + 1) % cols if full else i + 1
                a, b = base + j * cols + i, base + j * cols + i2
                self.f.append((a, b, b + cols, a + cols))
                self.m.append(mi)
        return self

    def box(self, c, size, mi):
        x0, x1 = c[0] - size[0] / 2, c[0] + size[0] / 2
        y0, y1 = c[1] - size[1] / 2, c[1] + size[1] / 2
        z0, z1 = c[2] - size[2] / 2, c[2] + size[2] / 2
        n = len(self.v)
        self.v += [(S * x, S * y, S * z) for x, y, z in
                   ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.f.append(tuple(n + i for i in f))
            self.m.append(mi)
        return self


def build(name, mesh, mats, coll, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(mesh.v, [], mesh.f)
    for m in mats:
        me.materials.append(m)
    for p, mi in zip(me.polygons, mesh.m):
        p.material_index = mi
        p.use_smooth = smooth
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


# ---------- fresh collection ----------
old = bpy.data.collections.get(NAME)
if old:
    for ob in list(old.all_objects):
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    bpy.data.collections.remove(old)
COL = bpy.data.collections.new(NAME)
bpy.context.scene.collection.children.link(COL)
MATS = list(M.values())
I = {k: i for i, k in enumerate(M)}

# ---------- shoes (grey-brown hikers, dark soles, laces) ----------
for side in (-1, 1):
    x = side * 0.105
    m = Mesh()
    m.loft([(x, -0.035, 0.0, 0.058, 0.155), (x, -0.035, 0.035, 0.062, 0.158),
            (x, -0.025, 0.07, 0.058, 0.145), (x, 0.0, 0.105, 0.048, 0.095),
            (x, 0.02, 0.13, 0.045, 0.062)], I["shoe"], seg=20)
    m.loft([(x, -0.035, -0.002, 0.059, 0.155), (x, -0.035, 0.022, 0.061, 0.157)], I["sole"], seg=20)
    for k in range(4):
        m.box((x, -0.09 + k * 0.028, 0.092 + k * 0.009), (0.05, 0.008, 0.008), I["lace"])
    build(f"Shoe_{'L' if side > 0 else 'R'}", m, MATS, COL)

# ---------- legs: black joggers, cuffed at the ankle ----------
for side in (-1, 1):
    m = Mesh()
    m.loft([(side * 0.103, 0.015, 0.11, 0.05, 0.05),     # cuff
            (side * 0.103, 0.015, 0.16, 0.052, 0.052),
            (side * 0.104, 0.012, 0.20, 0.058, 0.058),
            (side * 0.104, 0.008, 0.33, 0.066, 0.064),    # calf
            (side * 0.103, 0.0, 0.50, 0.062, 0.062),      # knee
            (side * 0.100, 0.0, 0.68, 0.078, 0.076),      # thigh
            (side * 0.088, 0.0, 0.80, 0.09, 0.085),
            (side * 0.07, 0.0, 0.88, 0.085, 0.07)], I["pants"], seg=20)
    m.loft([(side * 0.103, 0.015, 0.105, 0.054, 0.054), (side * 0.103, 0.015, 0.15, 0.056, 0.056)], I["pants"], seg=20)
    build(f"Leg_{'L' if side > 0 else 'R'}", m, MATS, COL)

# ---------- torso: navy long-sleeve tee ----------
m = Mesh()
m.loft([(0, 0.0, 0.855, 0.182, 0.108),
        (0, 0.0, 0.90, 0.18, 0.106),
        (0, 0.0, 1.02, 0.17, 0.103),
        (0, -0.003, 1.15, 0.170, 0.106),
        (0, -0.005, 1.27, 0.182, 0.112),    # chest
        (0, 0.0, 1.37, 0.192, 0.11),
        (0, 0.006, 1.43, 0.185, 0.098),     # shoulders
        (0, 0.01, 1.47, 0.14, 0.08),
        (0, 0.012, 1.495, 0.075, 0.06),
        (0, 0.012, 1.505, 0.06, 0.054)], I["shirt"], seg=28, cap1=False)
build("Torso", m, MATS, COL)
for side in (-1, 1):
    m = Mesh()
    m.loft([(side * 0.17, 0.008, 1.445, 0.03, 0.04),
            (side * 0.192, 0.008, 1.415, 0.052, 0.052),
            (side * 0.204, 0.01, 1.33, 0.047, 0.047),
            (side * 0.215, 0.005, 1.17, 0.04, 0.042),       # elbow
            (side * 0.225, -0.005, 1.03, 0.036, 0.036),
            (side * 0.232, -0.01, 0.90, 0.032, 0.032),      # sleeve end
            (side * 0.233, -0.01, 0.885, 0.03, 0.03)], I["shirt"], seg=16, cap1=False)
    m.loft([(side * 0.233, -0.01, 0.80, 0.022, 0.034),      # hand (relaxed, palm in)
            (side * 0.234, -0.012, 0.84, 0.026, 0.044),
            (side * 0.233, -0.01, 0.875, 0.026, 0.033),
            (side * 0.233, -0.01, 0.895, 0.024, 0.026)], I["skin"], seg=14)
    m.ellipsoid((side * 0.233, -0.012, 0.795), (0.021, 0.034, 0.03), I["skin"], seg=(12, 8))
    build(f"Arm_{'L' if side > 0 else 'R'}", m, MATS, COL)

# ---------- neck + head ----------
m = Mesh()
m.loft([(0, 0.012, 1.47, 0.052, 0.052), (0, 0.012, 1.57, 0.05, 0.052)], I["skin"], seg=16)
m.ellipsoid((0, 0.0, 1.655), (0.082, 0.098, 0.115), I["skin"], seg=(28, 18))          # head
for side in (-1, 1):
    m.ellipsoid((side * 0.079, 0.014, 1.65), (0.01, 0.019, 0.027), I["skin"], seg=(10, 8))   # ears
m.ellipsoid((0, -0.096, 1.638), (0.01, 0.013, 0.019), I["skin"], seg=(10, 8))        # nose
build("Head", m, MATS, COL)

m = Mesh()   # short stubble beard on the lower face (jaw, cheeks, chin, upper lip)
m.ellipsoid((0, 0.0, 1.655), (0.0838, 0.0995, 0.1165), I["stubble"], lat=(-85, -22), lon=(200, 340), seg=(20, 8))
m.ellipsoid((0, 0.0, 1.611), (0.026, 0.1, 0.007), I["stubble"], lat=(-90, 90), lon=(245, 295), seg=(8, 4))
build("Stubble", m, MATS, COL)

m = Mesh()   # short dark hair at the back and sides, under the cap
m.ellipsoid((0, 0.0, 1.655), (0.0842, 0.0995, 0.1168), I["hair"], lat=(-22, 30), lon=(30, 150), seg=(16, 6))
build("Hair", m, MATS, COL)

m = Mesh()   # eyes and eyebrows
for side in (-1, 1):
    m.ellipsoid((side * 0.032, -0.0905, 1.668), (0.0125, 0.006, 0.0075), I["eyewhite"], seg=(10, 6))
    m.ellipsoid((side * 0.032, -0.0958, 1.668), (0.006, 0.0025, 0.006), I["eye"], seg=(8, 6))
    m.box((side * 0.033, -0.0935, 1.686), (0.03, 0.006, 0.0055), I["brow"])
m.box((0, -0.0985, 1.614), (0.026, 0.004, 0.0035), I["brow"])                    # mouth
build("Face", m, MATS, COL)

# ---------- black baseball cap ----------
m = Mesh()
m.ellipsoid((0, 0.006, 1.70), (0.088, 0.103, 0.088), I["cap"], lat=(0, 90), seg=(28, 10))   # crown
m.loft([(0, 0.006, 1.694, 0.0885, 0.1035), (0, 0.006, 1.71, 0.089, 0.104)], I["cap"], seg=28, cap0=False, cap1=False)
m.ellipsoid((0, 0.006, 1.788), (0.008, 0.008, 0.005), I["cap"], seg=(8, 6))              # button
# brim: a curved, solid half-disc sticking out to the front (-Y), tipped down a little
pts = []
for k in range(13):
    a = math.radians(200 + 140 * k / 12)
    ox, oy = 0.092 * math.cos(a), 0.006 + 0.17 * math.sin(a)
    tip = 1 - abs(ox) / 0.092
    pts.append(((ox, oy, 1.692 - 0.016 * tip), (ox * 0.97, 0.006 + (oy - 0.006) * 0.45, 1.699)))
base = len(m.v)
for (o, inn) in pts:                       # top outer, top inner, bottom outer, bottom inner
    for (x, y, z) in (o, inn, (o[0], o[1], o[2] - 0.008), (inn[0], inn[1], inn[2] - 0.008)):
        m.v.append((S * x, S * y, S * z))
for k in range(12):
    a, b = base + 4 * k, base + 4 * (k + 1)
    for f in ((a, b, b + 1, a + 1), (a + 3, b + 3, b + 2, a + 2), (a + 2, b + 2, b, a)):
        m.f.append(f)
        m.m.append(I["cap"])
build("Cap", m, MATS, COL)

tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in COL.objects)
print(f"[character] Gabriel built: {len(COL.objects)} parts, about {tris:,} triangles, height {HEIGHT} m")
