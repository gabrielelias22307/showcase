"""
Classroom Mystery - student characters (stylized, game-ready)
=============================================================
Two students, built from reference photos (with parent permission):

  WHO = "A"  long wavy hair with bangs, black zip-up hoodie open over a
             camo tank top, baggy black sweatpants, white sneakers
  WHO = "B"  short curly hair with faded sides, grey/white patterned
             pullover hoodie with a front pocket, light grey sweatpants,
             black sneakers

- Faces Blender's Front view (looks toward -Y), feet on the floor (Z = 0).
- Each goes in its own collection ("Character_StudentA" / "...B").
  Running the script again rebuilds only that collection.
- Well under the 20,000-triangle budget for game characters.

Next steps (later): armature + "Idle" / "Talk" animations, then export
npc_<name>.glb (HANDOVER.md section 5).
"""

import math
import os
import bpy
import bmesh

WHO = os.environ.get("CM_WHO", "A")     # change to "B" to build the other student

STYLES = {
    "A": dict(height=1.60, width=0.92, skin="#c99777", hair="#2b211c", hair_style="long",
              top="hoodie_open", hoodie="#1d1e21", inner="camo", pants="#202124", pants_fit="baggy",
              shoe="#f2f1ee", sole="#e2e0dc", lace="#d8d6d2"),
    "B": dict(height=1.70, width=0.97, skin="#c4936f", hair="#231b17", hair_style="curly",
              top="hoodie_pullover", hoodie="#b9b5ad", pattern=("#8f8b84", "#d7d4cd", "#a29e96"),
              pants="#c5c4bf", pants_fit="straight", shoe="#1c1c1e", sole="#3a3a3c", lace="#2a2a2c"),
}
P = STYLES[WHO]
NAME = f"Character_Student{WHO}"
S = P["height"] / 1.78            # body numbers below are for a 1.78 m person
WX = P["width"]                   # slimmer shoulders/hips for younger students


def hexcol(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def mat(name, hexc, rough=0.8):
    key = f"ST{WHO}_{name}"
    m = bpy.data.materials.get(key) or bpy.data.materials.new(key)
    m.use_nodes = True
    rgb = hexcol(hexc)
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


M = {
    "skin": mat("Skin", P["skin"], 0.6),
    "hair": mat("Hair", P["hair"], 0.9),
    "fade": mat("HairFade", "#5a4a40", 0.95),
    "hoodie": mat("Hoodie", P["hoodie"], 0.95),
    "pants": mat("Pants", P["pants"], 0.95),
    "shoe": mat("Shoe", P["shoe"], 0.7),
    "sole": mat("Sole", P["sole"], 0.8),
    "lace": mat("Lace", P["lace"], 0.8),
    "eye": mat("Eye", "#1c1a19", 0.3),
    "eyewhite": mat("EyeWhite", "#f1ece6", 0.4),
    "brow": mat("Brow", "#2a201b", 0.9),
    "lip": mat("Mouth", "#8a4f45", 0.7),
    "camo1": mat("Camo1", "#6f6c4c", 0.9),
    "camo2": mat("Camo2", "#4a4a34", 0.9),
    "camo3": mat("Camo3", "#a39c7a", 0.9),
    "pat1": mat("Pattern1", P.get("pattern", ("#888888",) * 3)[0], 0.95),
    "pat2": mat("Pattern2", P.get("pattern", ("#888888",) * 3)[1], 0.95),
    "pat3": mat("Pattern3", P.get("pattern", ("#888888",) * 3)[2], 0.95),
    "zip": mat("Zip", "#8c8c8c", 0.4),
}
MATS = list(M.values())
I = {k: i for i, k in enumerate(M)}


def V(x, y, z, body=True):
    """Scale to this person. Body parts are also made slimmer side to side."""
    return (S * x * (WX if body else 1.0), S * y * (WX if body else 1.0) ** 0.5, S * z)


class Mesh:
    def __init__(self, body=True):
        self.v, self.f, self.m, self.body = [], [], [], body

    def loft(self, rings, mi, seg=24, cap0=True, cap1=True, gap=None, wave=None):
        """rings: [(cx, cy, z, rx, ry)] bottom to top. gap=(centre_deg, half_width_deg)
        leaves an opening (no caps then); wave=(amp, count) makes a wavy edge."""
        base = len(self.v)
        if gap:
            a0, a1 = gap[0] + gap[1], gap[0] + 360 - gap[1]
            angles = [math.radians(a0 + (a1 - a0) * i / seg) for i in range(seg + 1)]
            cap0 = cap1 = False
        else:
            angles = [2 * math.pi * i / seg for i in range(seg)]
        n = len(angles)
        for r, (cx, cy, z, rx, ry) in enumerate(rings):
            for a in angles:
                k = 1.0
                if wave:
                    k += wave[0] * math.sin(wave[1] * a + r * 1.7)
                self.v.append(V(cx + rx * k * math.cos(a), cy + ry * k * math.sin(a), z, self.body))
        for r in range(len(rings) - 1):
            for i in range(n if not gap else n - 1):
                j = (i + 1) % n
                a, b = base + r * n + i, base + r * n + j
                self.f.append((a, b, b + n, a + n))
                self.m.append(mi)
        for idx, cap in ((0, cap0), (len(rings) - 1, cap1)):
            if not cap:
                continue
            cx, cy, z, rx, ry = rings[idx]
            c = len(self.v)
            self.v.append(V(cx, cy, z, self.body))
            for i in range(n):
                j = (i + 1) % n
                a, b = base + idx * n + i, base + idx * n + j
                self.f.append((c, b, a) if idx == 0 else (c, a, b))
                self.m.append(mi)
        return self

    def ellipsoid(self, c, r, mi, lat=(-90, 90), lon=(0, 360), seg=(24, 16)):
        nu, nv = seg
        base = len(self.v)
        full = (lon[1] - lon[0]) >= 360
        cols = nu if full else nu + 1
        for j in range(nv + 1):
            la = math.radians(lat[0] + (lat[1] - lat[0]) * j / nv)
            for i in range(cols):
                lo = math.radians(lon[0] + (lon[1] - lon[0]) * i / nu)
                self.v.append(V(c[0] + r[0] * math.cos(la) * math.cos(lo),
                                c[1] + r[1] * math.cos(la) * math.sin(lo),
                                c[2] + r[2] * math.sin(la), self.body))
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
        self.v += [V(x, y, z, self.body) for x, y, z in
                   ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                    (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.f.append(tuple(n + i for i in f))
            self.m.append(mi)
        return self


def build(name, mesh, coll):
    me = bpy.data.meshes.new(f"{name}_{WHO}")
    me.from_pydata(mesh.v, [], mesh.f)
    for m in MATS:
        me.materials.append(m)
    for p, mi in zip(me.polygons, mesh.m):
        p.material_index = mi
        p.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(f"{name}_{WHO}", me)
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

# ---------- sneakers ----------
for side in (-1, 1):
    x = side * 0.105
    m = Mesh()
    m.loft([(x, -0.03, 0.0, 0.054, 0.15), (x, -0.03, 0.028, 0.057, 0.152),
            (x, -0.022, 0.06, 0.052, 0.138), (x, 0.005, 0.09, 0.044, 0.09),
            (x, 0.02, 0.11, 0.042, 0.058)], I["shoe"], seg=20)
    m.loft([(x, -0.03, -0.002, 0.058, 0.154), (x, -0.03, 0.03, 0.06, 0.156)], I["sole"], seg=20)
    for k in range(4):
        m.box((x, -0.085 + k * 0.026, 0.083 + k * 0.007), (0.046, 0.008, 0.007), I["lace"])
    build(f"Shoe_{'L' if side > 0 else 'R'}", m, COL)

# ---------- sweatpants ----------
for side in (-1, 1):
    m = Mesh()
    if P["pants_fit"] == "baggy":       # wide legs that pool over the shoes
        rings = [(side * 0.106, 0.0, 0.06, 0.082, 0.086),
                 (side * 0.106, 0.0, 0.14, 0.078, 0.08),
                 (side * 0.105, 0.0, 0.33, 0.08, 0.08),
                 (side * 0.103, 0.0, 0.52, 0.082, 0.082),
                 (side * 0.1, 0.0, 0.68, 0.088, 0.086),
                 (side * 0.088, 0.0, 0.8, 0.094, 0.088),
                 (side * 0.07, 0.0, 0.9, 0.088, 0.074)]
    else:                               # straight, slightly tapered
        rings = [(side * 0.104, 0.008, 0.075, 0.056, 0.058),
                 (side * 0.104, 0.008, 0.13, 0.058, 0.06),
                 (side * 0.104, 0.006, 0.33, 0.066, 0.065),
                 (side * 0.103, 0.0, 0.5, 0.066, 0.066),
                 (side * 0.1, 0.0, 0.68, 0.08, 0.078),
                 (side * 0.088, 0.0, 0.8, 0.09, 0.085),
                 (side * 0.07, 0.0, 0.9, 0.086, 0.072)]
    m.loft(rings, I["pants"], seg=20, cap0=(P["pants_fit"] != "baggy"))
    build(f"Leg_{'L' if side > 0 else 'R'}", m, COL)

# ---------- top: hoodie (open zip over a tank top, or pullover) ----------
torso = [(0, 0.0, 0.85, 0.19, 0.114), (0, 0.0, 0.875, 0.192, 0.116),    # ribbed hem
         (0, 0.0, 0.9, 0.186, 0.112), (0, 0.0, 1.02, 0.18, 0.11),
         (0, -0.003, 1.15, 0.182, 0.112), (0, -0.005, 1.27, 0.19, 0.117),
         (0, 0.0, 1.37, 0.198, 0.115), (0, 0.006, 1.43, 0.19, 0.104),
         (0, 0.01, 1.47, 0.145, 0.086), (0, 0.012, 1.495, 0.08, 0.064)]
m = Mesh()
if P["top"] == "hoodie_open":
    # tank top underneath, camo patches on the front
    m.loft([(0, 0.0, 0.88, 0.172, 0.1), (0, -0.003, 1.15, 0.17, 0.104),
            (0, -0.006, 1.27, 0.178, 0.11), (0, 0.0, 1.4, 0.15, 0.095),
            (0, 0.01, 1.46, 0.09, 0.07)], I["camo1"], seg=24, cap0=False, cap1=False)
    for k, (px, pz, mi) in enumerate(((-0.05, 1.3, "camo2"), (0.04, 1.22, "camo3"), (-0.02, 1.12, "camo2"),
                                     (0.06, 1.05, "camo2"), (-0.07, 0.98, "camo3"), (0.01, 1.36, "camo3"),
                                     (0.07, 1.32, "camo2"), (-0.03, 0.92, "camo2"))):
        m.ellipsoid((px, -0.106 if pz > 1.2 else -0.1, pz), (0.03, 0.006, 0.022), I[mi], seg=(10, 6))
    m.loft(torso, I["hoodie"], seg=28, gap=(270, 34))      # open front
    for side in (-1, 1):                                    # zip edges
        a = math.radians(270 + side * 34)
        for z0, z1, rx, ry in ((0.86, 1.15, 0.186, 0.112), (1.15, 1.42, 0.19, 0.116)):
            m.box((rx * math.cos(a), ry * math.sin(a) - 0.004, (z0 + z1) / 2), (0.008, 0.008, z1 - z0), I["zip"])
else:
    m.loft(torso, I["hoodie"], seg=28, cap1=False)
    m.ellipsoid((0, -0.108, 0.99), (0.12, 0.012, 0.07), I["hoodie"], seg=(16, 8))   # front pocket
    for k, (px, pz, mi, rr) in enumerate(((-0.1, 1.3, "pat1", 0.05), (0.06, 1.22, "pat2", 0.06),
                                         (-0.04, 1.08, "pat3", 0.05), (0.11, 1.05, "pat1", 0.04),
                                         (-0.12, 0.95, "pat2", 0.045), (0.02, 1.35, "pat3", 0.04),
                                         (0.12, 1.36, "pat2", 0.035), (-0.02, 0.93, "pat1", 0.04))):
        m.ellipsoid((px, -0.115 if pz > 1.1 else -0.118, pz), (rr, 0.003, rr * 0.7), I[mi], seg=(10, 6))
        m.ellipsoid((px * 0.9, 0.114, pz + 0.02), (rr, 0.003, rr * 0.7), I[mi], seg=(10, 6))  # back
# hood, lying down behind the neck
m.ellipsoid((0, 0.085, 1.45), (0.125, 0.045, 0.075), I["hoodie"], lat=(-60, 80), seg=(18, 10))
m.loft([(0, 0.02, 1.47, 0.092, 0.078), (0, 0.025, 1.53, 0.088, 0.075)], I["hoodie"], seg=20,
       gap=(270, 40) if P["top"] == "hoodie_open" else None, cap0=False, cap1=False)
build("Top", m, COL)

# ---------- arms: hoodie sleeves with cuffs, hands ----------
for side in (-1, 1):
    m = Mesh()
    m.loft([(side * 0.17, 0.008, 1.445, 0.034, 0.044),
            (side * 0.195, 0.008, 1.415, 0.058, 0.058),
            (side * 0.208, 0.01, 1.33, 0.054, 0.054),
            (side * 0.22, 0.005, 1.17, 0.05, 0.05),
            (side * 0.23, -0.005, 1.03, 0.046, 0.046),
            (side * 0.234, -0.01, 0.93, 0.04, 0.04),
            (side * 0.235, -0.01, 0.9, 0.036, 0.036),      # cuff
            (side * 0.235, -0.01, 0.885, 0.034, 0.034)], I["hoodie"], seg=16, cap1=False)
    hx = side * 0.235
    m.loft([(hx, -0.008, 0.803, 0.014, 0.038), (hx, -0.009, 0.83, 0.015, 0.04),
            (hx, -0.009, 0.86, 0.015, 0.036), (hx, -0.008, 0.882, 0.016, 0.026),
            (hx, -0.008, 0.895, 0.018, 0.024)], I["skin"], seg=14)
    for k, length in enumerate((0.068, 0.075, 0.071, 0.056)):
        fy = -0.032 + k * 0.017
        top = 0.808
        rings = [(hx + side * b, fy, top - length * t, 0.0078 - 0.0011 * t, 0.0078 - 0.0011 * t)
                 for t, b in zip((0, 0.33, 0.66, 1.0), (0.0, -0.004, -0.01, -0.018))]
        rings.reverse()
        m.loft(rings, I["skin"], seg=10)
        m.ellipsoid((rings[0][0], fy, top - length), (0.0068, 0.0068, 0.0074), I["skin"], seg=(10, 6))
    thumb = [(hx - side * 0.011, -0.028, 0.87, 0.01, 0.01),
             (hx - side * 0.016, -0.04, 0.85, 0.009, 0.009),
             (hx - side * 0.018, -0.047, 0.828, 0.008, 0.008)]
    thumb.reverse()
    m.loft(thumb, I["skin"], seg=10)
    m.ellipsoid((hx - side * 0.018, -0.047, 0.826), (0.0076, 0.0076, 0.0082), I["skin"], seg=(10, 6))
    build(f"Arm_{'L' if side > 0 else 'R'}", m, COL)

# ---------- head (not slimmed: heads stay full size) ----------
m = Mesh(body=False)
m.loft([(0, 0.012, 1.48, 0.05, 0.05), (0, 0.012, 1.57, 0.048, 0.05)], I["skin"], seg=16)
m.ellipsoid((0, 0.0, 1.655), (0.08, 0.096, 0.113), I["skin"], seg=(28, 18))
for side in (-1, 1):
    m.ellipsoid((side * 0.078, 0.014, 1.65), (0.01, 0.018, 0.026), I["skin"], seg=(10, 8))
m.ellipsoid((0, -0.095, 1.638), (0.01, 0.012, 0.017), I["skin"], seg=(10, 8))           # nose
for side in (-1, 1):
    m.ellipsoid((side * 0.031, -0.0885, 1.668), (0.0125, 0.006, 0.0078), I["eyewhite"], seg=(10, 6))
    m.ellipsoid((side * 0.031, -0.0938, 1.668), (0.0062, 0.0026, 0.0062), I["eye"], seg=(8, 6))
    m.box((side * 0.032, -0.0915, 1.689), (0.028, 0.006, 0.005), I["brow"])
m.ellipsoid((0, -0.093, 1.612), (0.018, 0.004, 0.0045), I["lip"], seg=(10, 6))           # smile
build("Head", m, COL)

m = Mesh(body=False)
if P["hair_style"] == "long":
    # wavy, shoulder-length hair with bangs
    m.ellipsoid((0, 0.004, 1.662), (0.087, 0.103, 0.12), I["hair"], lat=(-10, 90), lon=(-45, 225), seg=(24, 10))
    m.ellipsoid((0, 0.004, 1.662), (0.087, 0.103, 0.12), I["hair"], lat=(30, 90), lon=(225, 315), seg=(10, 6))
    m.ellipsoid((0, 0.0, 1.705), (0.084, 0.1015, 0.045), I["hair"], lat=(-35, 40), lon=(228, 312), seg=(14, 6), )  # bangs
    m.loft([(0, 0.02, 1.36, 0.13, 0.115), (0, 0.02, 1.44, 0.12, 0.112), (0, 0.015, 1.53, 0.105, 0.112),
            (0, 0.008, 1.6, 0.096, 0.11), (0, 0.004, 1.66, 0.09, 0.106)],
           I["hair"], seg=26, gap=(270, 62), wave=(0.07, 7))
else:
    # short curly top, faded sides
    m.ellipsoid((0, 0.0, 1.655), (0.0815, 0.0975, 0.1148), I["fade"], lat=(-8, 40), lon=(-28, 208), seg=(22, 6))
    m.ellipsoid((0, 0.004, 1.672), (0.084, 0.1, 0.112), I["hair"], lat=(28, 90), seg=(24, 8))
    k = 0
    for la in (35, 50, 64, 78):
        n = {35: 14, 50: 12, 64: 9, 78: 5}[la]
        for i in range(n):
            lo = math.radians(i * 360 / n + la)
            lr = math.radians(la)
            cx, cy = 0.088 * math.cos(lr) * math.cos(lo), 0.004 + 0.104 * math.cos(lr) * math.sin(lo)
            cz = 1.672 + 0.114 * math.sin(lr)
            m.ellipsoid((cx, cy, cz), (0.019, 0.019, 0.017), I["hair"], seg=(8, 5))
            k += 1
build("Hair", m, COL)

tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in COL.objects)
print(f"[character] Student {WHO} built: {len(COL.objects)} parts, about {tris:,} triangles, height {P['height']} m")
