"""
Classroom Mystery - character: Mr. Grump, the principal (stylized, game-ready)
==============================================================================
Built from reference photos (front, 3/4, side, back): short white hair,
full short white beard and mustache, white dress shirt with a chest pocket,
navy tie with a tie clip, black belt, navy dress pants, brown dress shoes,
a sturdier build. About 1.83 m tall.

- Faces Blender's Front view (looks toward -Y), feet on the floor (Z = 0).
- Everything goes in a "Character_Principal" collection. Running the
  script again rebuilds only that collection.
- Well under the 20,000-triangle budget for game characters.
"""

import math
import bpy
import bmesh

HEIGHT = 1.83
NAME = "Character_Principal"
S = HEIGHT / 1.78          # every number below is for a 1.78 m person


def hexcol(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexc, rough=0.7):
    m = bpy.data.materials.get("PR_" + name) or bpy.data.materials.new("PR_" + name)
    m.use_nodes = True
    rgb = hexcol(hexc)
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


M = {
    "skin": mat("Skin", "#e6b9a3", 0.6),
    "beard": mat("BeardWhite", "#e9e6df", 0.95),
    "hair": mat("HairWhite", "#d9d6cf", 0.95),
    "shirt": mat("ShirtWhite", "#f4f4f1", 0.7),
    "tie": mat("TieNavy", "#1f2b4a", 0.6),
    "clip": mat("TieClip", "#7fb5c9", 0.3),
    "belt": mat("BeltBlack", "#1a1a1a", 0.5),
    "buckle": mat("Buckle", "#b9b9b9", 0.3),
    "pants": mat("PantsNavy", "#24304a", 0.85),
    "shoe": mat("ShoeBrown", "#6b4126", 0.45),
    "sole": mat("ShoeSole", "#2b1d14", 0.8),
    "eye": mat("Eye", "#1c1a19", 0.3),
    "eyewhite": mat("EyeWhite", "#f1ece6", 0.4),
    "brow": mat("Brow", "#cfcac2", 0.9),
    "mouth": mat("Mouth", "#a5675c", 0.7),
    "button": mat("Button", "#e2e0da", 0.4),
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


W = 1.08   # broader than the 1.78 m base build


def sx(v):
    return v * W


# ---------- brown dress shoes ----------
for side in (-1, 1):
    x = side * 0.105
    m = Mesh()
    m.loft([(x, -0.04, 0.0, 0.048, 0.155), (x, -0.04, 0.022, 0.05, 0.157),
            (x, -0.03, 0.05, 0.046, 0.145), (x, 0.0, 0.08, 0.042, 0.1),
            (x, 0.02, 0.1, 0.04, 0.062)], I["shoe"], seg=20)
    m.loft([(x, -0.04, -0.002, 0.05, 0.158), (x, -0.04, 0.018, 0.052, 0.16)], I["sole"], seg=20)
    build(f"Shoe_{'L' if side > 0 else 'R'}", m, MATS, COL)

# ---------- navy dress pants ----------
for side in (-1, 1):
    m = Mesh()
    m.loft([(side * 0.105, 0.01, 0.06, 0.058, 0.06),
            (side * 0.105, 0.01, 0.15, 0.058, 0.06),
            (side * 0.106, 0.008, 0.33, 0.066, 0.066),
            (side * 0.105, 0.0, 0.5, 0.07, 0.07),
            (side * sx(0.1), 0.0, 0.68, sx(0.084), 0.082),
            (side * sx(0.09), -0.005, 0.8, sx(0.096), 0.092),
            (side * sx(0.072), -0.01, 0.92, sx(0.094), 0.085)], I["pants"], seg=20, cap0=False)
    build(f"Leg_{'L' if side > 0 else 'R'}", m, MATS, COL)

# ---------- white dress shirt, tucked in, belt ----------
m = Mesh()
m.loft([(0, -0.008, 0.9, sx(0.178), 0.118), (0, -0.01, 0.95, sx(0.18), 0.124),
        (0, -0.015, 1.05, sx(0.186), 0.134),      # tummy
        (0, -0.012, 1.15, sx(0.19), 0.134),
        (0, -0.008, 1.27, sx(0.195), 0.128),      # chest
        (0, 0.0, 1.37, sx(0.198), 0.118),
        (0, 0.006, 1.43, sx(0.19), 0.104),        # shoulders
        (0, 0.01, 1.47, sx(0.145), 0.084),
        (0, 0.012, 1.5, 0.078, 0.066)], I["shirt"], seg=28, cap0=False, cap1=False)
m.loft([(0, -0.01, 0.92, sx(0.184), 0.124), (0, -0.01, 0.955, sx(0.186), 0.126)], I["belt"], seg=28, cap0=False, cap1=False)
m.box((0, -0.136, 0.937), (0.05, 0.008, 0.032), I["buckle"])
# collar: two small wings either side of the tie knot
for side in (-1, 1):   # collar points either side of the knot
    m.loft([(side * 0.026, -0.058, 1.485, 0.024, 0.012), (side * 0.03, -0.05, 1.525, 0.03, 0.016)], I["shirt"], seg=10)
m.loft([(0, 0.012, 1.49, 0.066, 0.062), (0, 0.012, 1.53, 0.064, 0.06)], I["shirt"], seg=20, cap0=False, cap1=False)
# tie: knot, blade down the front, clip
m.ellipsoid((0, -0.072, 1.49), (0.017, 0.012, 0.02), I["tie"], seg=(10, 6))
m.loft([(0, -0.147, 0.975, 0.024, 0.004), (0, -0.149, 1.06, 0.022, 0.004), (0, -0.148, 1.2, 0.02, 0.004),
        (0, -0.137, 1.33, 0.017, 0.004), (0, -0.105, 1.43, 0.014, 0.004), (0, -0.08, 1.475, 0.012, 0.004)],
       I["tie"], seg=12)
m.box((0, -0.152, 1.2), (0.045, 0.006, 0.006), I["clip"])
m.box((sx(0.08), -0.139, 1.28), (0.06, 0.004, 0.065), I["shirt"])       # chest pocket
build("Shirt", m, MATS, COL)

# ---------- arms: white sleeves with cuffs, hands ----------
for side in (-1, 1):
    m = Mesh()
    m.loft([(side * sx(0.17), 0.008, 1.445, 0.034, 0.044),
            (side * sx(0.192), 0.008, 1.415, 0.056, 0.056),
            (side * sx(0.205), 0.01, 1.33, 0.052, 0.052),
            (side * sx(0.217), 0.005, 1.17, 0.046, 0.046),
            (side * sx(0.226), -0.005, 1.03, 0.042, 0.042),
            (side * sx(0.232), -0.01, 0.91, 0.038, 0.038),
            (side * sx(0.233), -0.01, 0.89, 0.036, 0.036)], I["shirt"], seg=16, cap1=False)
    hx = side * sx(0.233)
    m.loft([(hx, -0.008, 0.803, 0.016, 0.043), (hx, -0.009, 0.83, 0.017, 0.045),
            (hx, -0.009, 0.86, 0.017, 0.04), (hx, -0.008, 0.882, 0.018, 0.03),
            (hx, -0.008, 0.895, 0.02, 0.028)], I["skin"], seg=14)
    for k, length in enumerate((0.076, 0.083, 0.079, 0.063)):
        fy = -0.036 + k * 0.019
        rings = [(hx + side * b, fy, 0.808 - length * t, 0.009 - 0.0012 * t, 0.009 - 0.0012 * t)
                 for t, b in zip((0, 0.33, 0.66, 1.0), (0.0, -0.004, -0.011, -0.02))]
        rings.reverse()
        m.loft(rings, I["skin"], seg=10)
        m.ellipsoid((rings[0][0], fy, 0.808 - length), (0.0078, 0.0078, 0.0084), I["skin"], seg=(10, 6))
    thumb = [(hx - side * 0.013, -0.031, 0.872, 0.0115, 0.0115),
             (hx - side * 0.018, -0.044, 0.85, 0.0102, 0.0102),
             (hx - side * 0.02, -0.052, 0.826, 0.0092, 0.0092)]
    thumb.reverse()
    m.loft(thumb, I["skin"], seg=10)
    m.ellipsoid((hx - side * 0.02, -0.052, 0.824), (0.0086, 0.0086, 0.0094), I["skin"], seg=(10, 6))
    build(f"Arm_{'L' if side > 0 else 'R'}", m, MATS, COL)

# ---------- neck + head ----------
m = Mesh()
m.loft([(0, 0.012, 1.48, 0.058, 0.058), (0, 0.012, 1.57, 0.054, 0.056)], I["skin"], seg=16)
m.ellipsoid((0, 0.0, 1.655), (0.085, 0.1, 0.116), I["skin"], seg=(28, 18))
for side in (-1, 1):
    m.ellipsoid((side * 0.082, 0.014, 1.652), (0.011, 0.02, 0.029), I["skin"], seg=(10, 8))
m.ellipsoid((0, -0.099, 1.642), (0.012, 0.016, 0.021), I["skin"], seg=(10, 8))           # nose
for side in (-1, 1):
    m.ellipsoid((side * 0.033, -0.0925, 1.672), (0.012, 0.006, 0.0068), I["eyewhite"], seg=(10, 6))
    m.ellipsoid((side * 0.033, -0.0975, 1.672), (0.0058, 0.0025, 0.0056), I["eye"], seg=(8, 6))
    # low, slightly frowning brows: that's Mr. Grump
    m.box((side * 0.034, -0.0955, 1.687), (0.032, 0.007, 0.007), I["brow"])
    m.box((side * 0.016, -0.0965, 1.684), (0.012, 0.007, 0.007), I["brow"])
build("Head", m, MATS, COL)

m = Mesh()   # full short white beard + mustache, white hair
m.ellipsoid((0, -0.004, 1.652), (0.0875, 0.103, 0.121), I["beard"], lat=(-90, -6), lon=(195, 345), seg=(22, 10))
m.ellipsoid((0, -0.03, 1.566), (0.046, 0.06, 0.022), I["beard"], seg=(16, 8))           # chin
for side in (-1, 1):                                                                 # mustache
    m.ellipsoid((side * 0.016, -0.1, 1.622), (0.02, 0.008, 0.0075), I["beard"], seg=(10, 6))
m.box((0, -0.101, 1.609), (0.022, 0.004, 0.0035), I["mouth"])
m.ellipsoid((0, 0.002, 1.658), (0.0862, 0.1015, 0.1185), I["hair"], lat=(-12, 90), lon=(-35, 215), seg=(24, 10))
m.ellipsoid((0, 0.002, 1.658), (0.0862, 0.1015, 0.1185), I["hair"], lat=(50, 90), lon=(215, 325), seg=(10, 6))
build("BeardHair", m, MATS, COL)

tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in COL.objects)
print(f"[character] Principal built: {len(COL.objects)} parts, about {tris:,} triangles, height {HEIGHT} m")
