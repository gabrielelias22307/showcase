"""
Classroom Mystery - Field Day long jump in the classroom
========================================================
The classroom (classroom_starter.py) with the tables pushed against the
walls, a taped jumping lane, a takeoff line and a blue landing mat with
meter marks. Student B (Sam) jumps first, then Mr. Grump jumps farther and
wins. Sam cheers anyway. The whiteboard keeps score.

Run with Blender in the background:
  blender -b --factory-startup --python field_day_scene.py -- dir=/path/to/folder tex=/path/to/textures name=Sam
"dir" must hold classroom_starter.py, student_character.py,
principal_character.py and rig_walk.py. "tex" (optional) is the game's
assets/textures folder. "name" is the name shown on the whiteboard for the
student. Saves field_day_video.blend (frames go to field_day_frames/).
Uses EEVEE, so it renders in a few minutes.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler, noise

args = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
Z = args.get("dir", os.getcwd())
TEX = args.get("tex", "")
NAME_A = args.get("name", "Sam")
FPS = 24
rnd = random.Random(8)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene

def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


def lerp(a, b, t):
    return a + (b - a) * t


def inp(node, name, value):
    s = node.inputs.get(name)
    if s is not None:
        s.default_value = value
    return s


def new_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    return m, nt.nodes, nt.links, b, out


def base_color(m, fallback=(0.5, 0.5, 0.5, 1)):
    if m.use_nodes and m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                return tuple(nd.inputs["Base Color"].default_value)
    return tuple(m.diffuse_color) if m else fallback


def coord(n, kind="UV"):
    tc = n.new("ShaderNodeTexCoord")
    if kind == "WORLD":
        geo = n.new("ShaderNodeNewGeometry")
        return geo.outputs["Position"]
    return tc.outputs[kind]


def noise_tex(n, l, vec, scale, detail=6, rough=0.55, distortion=0.0):
    t = n.new("ShaderNodeTexNoise")
    l.new(vec, t.inputs["Vector"])
    inp(t, "Scale", scale); inp(t, "Detail", detail); inp(t, "Roughness", rough); inp(t, "Distortion", distortion)
    return t.outputs["Fac"]


def maprange(n, l, val, a, b, c, d):
    mr = n.new("ShaderNodeMapRange")
    l.new(val, mr.inputs["Value"])
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = a, b
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = c, d
    return mr.outputs["Result"]


def color_mix(n, blend="MIX"):
    mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = blend
    ins = [s for s in mx.inputs if s.type == "RGBA"]
    out = [s for s in mx.outputs if s.type == "RGBA"][0]
    return mx, ins[0], ins[1], out


def feed(l, sock, val):
    if isinstance(val, tuple): sock.default_value = val
    else: l.new(val, sock)


def tint(n, l, color, factor):
    """color * factor (color: tuple or socket, factor: float socket)."""
    mx, a, b, out = color_mix(n, "MULTIPLY")
    mx.inputs["Factor"].default_value = 1.0
    feed(l, a, color)
    cmb = n.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        l.new(factor, cmb.inputs[k])
    l.new(cmb.outputs["Color"], b)
    return out


def mix_col(n, l, fac, a, b):
    mx, sa, sb, out = color_mix(n)
    l.new(fac, mx.inputs["Factor"])
    feed(l, sa, a); feed(l, sb, b)
    return out


def bump_chain(n, l, b, layers):
    """layers: list of (height socket, strength, distance)."""
    prev = None
    for h, s, d in layers:
        bp = n.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = s
        bp.inputs["Distance"].default_value = d
        l.new(h, bp.inputs["Height"])
        if prev is not None:
            l.new(prev, bp.inputs["Normal"])
        prev = bp.outputs["Normal"]
    l.new(prev, b.inputs["Normal"])


def leaf_material():
    m, n, l, b, out = new_mat("LeafCard")
    rndv = n.new("ShaderNodeObjectInfo")
    cr = n.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.03, 0.1, 0.02, 1)
    cr.color_ramp.elements[1].color = (0.2, 0.33, 0.05, 1)
    l.new(rndv.outputs["Random"], cr.inputs["Fac"])
    l.new(cr.outputs["Color"], b.inputs["Base Color"]); inp(b, "Roughness", 0.55)
    tr = n.new("ShaderNodeBsdfTranslucent"); l.new(cr.outputs["Color"], tr.inputs["Color"])
    ms = n.new("ShaderNodeMixShader"); ms.inputs["Fac"].default_value = 0.35
    l.new(b.outputs[0], ms.inputs[1]); l.new(tr.outputs[0], ms.inputs[2]); l.new(ms.outputs[0], out.inputs[0])
    return m


def grass_material():
    m, n, l, b, out = new_mat("GrassBlade")
    gen = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ"); l.new(gen.outputs["Generated"], sep.inputs[0])
    cr = n.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.012, 0.03, 0.006, 1)
    cr.color_ramp.elements[1].color = (0.15, 0.27, 0.05, 1)
    e = cr.color_ramp.elements.new(0.45); e.color = (0.05, 0.12, 0.02, 1)
    l.new(sep.outputs["Z"], cr.inputs["Fac"])
    oi = n.new("ShaderNodeObjectInfo")
    hue = mix_col(n, l, maprange(n, l, oi.outputs["Random"], 0.0, 1.0, 0, 0.45), (1, 1, 1, 1), (1.5, 1.15, 0.55, 1))
    mx, sa, sb, gcol = color_mix(n, "MULTIPLY"); mx.inputs["Factor"].default_value = 1
    l.new(cr.outputs["Color"], sa); l.new(hue, sb)
    l.new(gcol, b.inputs["Base Color"]); inp(b, "Roughness", 0.5)
    tr = n.new("ShaderNodeBsdfTranslucent"); l.new(gcol, tr.inputs["Color"])
    ms = n.new("ShaderNodeMixShader"); ms.inputs["Fac"].default_value = 0.3
    l.new(b.outputs[0], ms.inputs[1]); l.new(tr.outputs[0], ms.inputs[2]); l.new(ms.outputs[0], out.inputs[0])
    return m


def mesh_obj(name, bm, mats, link=True, smooth_shade=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for mt in mats:
        me.materials.append(mt)
    if smooth_shade:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    if link:
        sc.collection.objects.link(ob)
    return ob


def fabric(name, weave, period, weave_str, fold_size, fold_str, sheen, rough, heather=0.08):
    m0 = bpy.data.materials.get(name)
    if m0 is None:
        return
    color = base_color(m0)
    m, n, l, b, out = new_mat(name)
    uvs = coord(n, "UV")
    v1 = noise_tex(n, l, uvs, 1 / 0.004, 2)
    v2 = noise_tex(n, l, uvs, 1 / 0.12, 3)
    f = n.new("ShaderNodeMath"); f.operation = "ADD"
    l.new(maprange(n, l, v1, 0.3, 0.7, 1 - heather, 1 + heather), f.inputs[0])
    l.new(maprange(n, l, v2, 0.3, 0.7, -heather * 0.6, heather * 0.6), f.inputs[1])
    l.new(tint(n, l, color, f.outputs[0]), b.inputs["Base Color"])
    inp(b, "Roughness", rough); inp(b, "Sheen Weight", sheen); inp(b, "Sheen Roughness", 0.4)
    layers = []
    if weave:
        w = n.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = weave
        l.new(uvs, w.inputs["Vector"]); inp(w, "Scale", 0.628 / period); inp(w, "Distortion", 1.5); inp(w, "Detail", 1)
        layers.append((w.outputs["Fac"], weave_str, 0.002))
    folds = noise_tex(n, l, uvs, 1 / fold_size, 3, 0.45, 0.8)
    layers.insert(0, (folds, fold_str, 0.03))
    bump_chain(n, l, b, layers)


# ---------- 1. the classroom ----------
room_src = open(os.path.join(Z, "classroom_starter.py")).read()
if TEX:
    room_src = room_src.replace('TEXTURE_DIR = ""', f'TEXTURE_DIR = {TEX!r}', 1)
exec(compile(room_src, "classroom_starter.py", "exec"), {"__name__": "__main__"})
for cname in ("Classroom_Collision", "Classroom_Spawns", "Guides_DoNotExport"):
    c = bpy.data.collections.get(cname)
    if c:
        c.hide_render = True
        c.hide_viewport = True

# push the student tables and chairs against the north and south walls
north_x = [-6.4, -4.35, -2.3, -0.25, 1.8, 3.85]
south_x = [-6.6, -4.55, -2.5, -0.45, 1.6, 3.65]
for i in range(12):
    n = i + 1
    t = bpy.data.objects.get(f"Table_{n:02d}")
    if t is None:
        continue
    if i < 6:
        tx, ty, flip = north_x[i], 1.35, False
    else:
        tx, ty, flip = south_x[i - 6], -7.45, True
    t.location = (tx, ty, 0)
    for side, dx in (("a", -0.5), ("b", 0.5)):
        ch = bpy.data.objects.get(f"Chair_{n:02d}{side}")
        if ch:
            ch.location = (tx + dx, ty + (0.33 if flip else -0.33), 0)
            ch.rotation_euler = (0, 0, math.pi if flip else 0)

LANE_Y = -3.0
TAKEOFF_X = 1.0

def box_obj(name, c, size, mat_, rot=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = mesh_obj(name, bm, [mat_], smooth_shade=False)
    ob.location = c
    ob.rotation_euler.z = rot
    return ob


tape, n, l, b, _ = new_mat("MaskingTape")
oc = coord(n, "Object")
tn = noise_tex(n, l, oc, 300, 2)
l.new(tint(n, l, (0.78, 0.68, 0.42, 1), maprange(n, l, tn, 0.3, 0.7, 0.9, 1.05)), b.inputs["Base Color"])
inp(b, "Roughness", 0.75)
white_tape, n, l, b, _ = new_mat("WhiteTape"); inp(b, "Base Color", (0.85, 0.85, 0.82, 1)); inp(b, "Roughness", 0.6)
for yy in (LANE_Y - 0.75, LANE_Y + 0.75):
    box_obj("LaneTape", (-1.6, yy, 0.0015), (14.6, 0.045, 0.003), tape)
box_obj("TakeoffLine", (TAKEOFF_X, LANE_Y, 0.002), (0.06, 1.5, 0.004), white_tape)
box_obj("StartLine", (-6.5 - 0.35, LANE_Y, 0.002), (0.05, 1.5, 0.004), tape)

# landing mat: four panels with seams
matm, n, l, b, _ = new_mat("GymMat")
oc = coord(n, "Object")
vn = noise_tex(n, l, oc, 60, 3)
l.new(tint(n, l, (0.03, 0.11, 0.42, 1), maprange(n, l, vn, 0.3, 0.7, 0.92, 1.06)), b.inputs["Base Color"])
inp(b, "Roughness", 0.42); inp(b, "Sheen Weight", 0.2)
bump_chain(n, l, b, [(vn, 0.15, 0.002)])
seam, n, l, b, _ = new_mat("MatSeam"); inp(b, "Base Color", (0.01, 0.03, 0.12, 1)); inp(b, "Roughness", 0.6)
for k in range(4):
    x0 = TAKEOFF_X + 0.25 + k * 1.0
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.985, v.co.y * 1.3, v.co.z * 0.06))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.012, segments=2, affect="EDGES")
    p = mesh_obj("MatPanel", bm, [matm])
    p.location = (x0 + 0.5, LANE_Y, 0.03)
box_obj("MatBase", (TAKEOFF_X + 2.25, LANE_Y, 0.012), (4.0, 1.28, 0.024), seam)
marker_m, n, l, b, _ = new_mat("MarkerBlue"); inp(b, "Base Color", (0.02, 0.06, 0.35, 1)); inp(b, "Roughness", 0.5)
red_m, n, l, b, _ = new_mat("MarkerRed"); inp(b, "Base Color", (0.45, 0.02, 0.02, 1)); inp(b, "Roughness", 0.5)


def text_obj(name, body, loc, rot, size, mat_, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.size = size; cu.align_x = align; cu.extrude = 0.0008
    ob = bpy.data.objects.new(name, cu)
    sc.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    cu.materials.append(mat_)
    return ob


for k in range(1, 5):                                  # meter marks beside the mat
    x = TAKEOFF_X + k
    box_obj("MeterTape", (x, LANE_Y - 0.86, 0.0015), (0.04, 0.22, 0.003), white_tape)
    text_obj(f"Meter_{k}", f"{k} m", (x, LANE_Y - 1.1, 0.004), (0, 0, 0), 0.12, marker_m)

# orange cones at the start of the lane
cone_m, n, l, b, _ = new_mat("Cone"); inp(b, "Base Color", (0.9, 0.22, 0.02, 1)); inp(b, "Roughness", 0.45)
for yy in (LANE_Y - 0.95, LANE_Y + 0.95):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.11, radius2=0.015, depth=0.32)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.16))
    c_ = mesh_obj("Cone", bm, [cone_m]); c_.location = (-8.9, yy, 0)
    box_obj("ConeBase", (-8.9, yy, 0.01), (0.26, 0.26, 0.02), cone_m)

# little flags that mark where each jumper landed
def flag(name, x, mat_):
    bm = bmesh.new()
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.006, radius2=0.006, depth=0.42)
    bmesh.ops.translate(bm, verts=ret["verts"], vec=(0, 0, 0.21))
    v = [bm.verts.new(p) for p in ((0, 0, 0.42), (0.16, 0, 0.36), (0, 0, 0.30))]
    bm.faces.new(v)
    ob = mesh_obj(name, bm, [mat_, mat_], smooth_shade=False)
    ob.location = (x, LANE_Y - 0.72, 0.02)
    return ob


# the whiteboard keeps score
wb = bpy.data.objects.get("Whiteboard_North")
wb_y = 1.86
if wb:
    ys = [(wb.matrix_world @ v.co).y for v in wb.data.vertices]
    wb_y = min(ys) - 0.006
text_obj("WB_Title", "FIELD DAY - LONG JUMP", (-1.2, wb_y, 1.72), (math.radians(90), 0, 0), 0.2, marker_m)

# ceiling lights over the classroom
for x in (-9.0, -5.4, -1.8, 1.8, 5.4, 9.0):
    for y in (-6, -3, 0):
        lt = bpy.data.objects.new("CeilingLight", bpy.data.lights.new("CeilingLight", "AREA"))
        lt.data.shape = "RECTANGLE"; lt.data.size = 1.2; lt.data.size_y = 0.6
        lt.data.energy = float(args.get("light", "170")); lt.data.color = (1.0, 0.97, 0.92)
        lt.location = (x, y, 3.3)
        sc.collection.objects.link(lt)
world = bpy.data.worlds.new("Room"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.55, 0.55, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25

# ---------- 2. the two jumpers ----------
rig_src = open(os.path.join(Z, "rig_walk.py")).read()
CAST = {}
for key, script, colname, env in (("sam", "student_character.py", "Character_StudentB", "B"),
                                  ("grump", "principal_character.py", "Character_Principal", None)):
    if env:
        os.environ["CM_WHO"] = env
    exec(compile(open(os.path.join(Z, script)).read(), script, "exec"), {"__name__": "__main__"})
    src = (rig_src.replace('COLLECTION_PREFIX = "Character_"', f'COLLECTION_PREFIX = "{colname}"')
                  .replace("WALK_FRAMES = 374", "WALK_FRAMES = 2"))
    g = {"__name__": "__main__"}
    exec(compile(src, "rig_walk.py", "exec"), g)
    rig = g["rig"]; rig.name = "Rig_" + key
    rig.animation_data_clear()
    col = bpy.data.collections[colname]
    for bn in rig.pose.bones:
        bn.rotation_mode = "XYZ"
    CAST[key] = {"rig": rig, "meshes": [o for o in col.all_objects if o.type == "MESH"]}

for c in CAST.values():                               # texture coordinates in meters
    for ob in c["meshes"]:
        bm = bmesh.new(); bm.from_mesh(ob.data)
        uv = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
        for f in bm.faces:
            nrm = f.normal
            ax = max(range(3), key=lambda i: abs(nrm[i]))
            for lp in f.loops:
                p = lp.vert.co
                u, v = ((p.y if nrm.x > 0 else -p.y), p.z) if ax == 0 else \
                       ((-p.x if nrm.y > 0 else p.x), p.z) if ax == 1 else (p.x, (p.y if nrm.z > 0 else -p.y))
                lp[uv].uv = (u, v)
        bm.to_mesh(ob.data); bm.free()

for mname in [m.name for m in bpy.data.materials]:
    if mname.startswith(("STB_", "PR_")):
        low = mname.lower()
        if "hoodie" in low or "pattern" in low:
            fabric(mname, "Y", 0.003, 0.25, 0.08, 0.5, 0.6, 0.9, 0.08)
        elif "pants" in low:
            fabric(mname, "DIAGONAL", 0.003, 0.25, 0.09, 0.5, 0.5, 0.8, 0.08)
        elif "shirt" in low:
            fabric(mname, "X", 0.0012, 0.12, 0.08, 0.35, 0.3, 0.6, 0.03)
        elif "tie" in low:
            fabric(mname, "DIAGONAL", 0.004, 0.35, 0.05, 0.1, 0.6, 0.45, 0.06)
        elif low.endswith("_skin"):
            c = base_color(bpy.data.materials[mname])
            m, n, l, b, out = new_mat(mname)
            uvs = coord(n, "UV")
            mott = noise_tex(n, l, uvs, 1 / 0.025, 4)
            l.new(mix_col(n, l, maprange(n, l, mott, 0.35, 0.75, 0, 0.6), c, (c[0] * 1.08, c[1] * 0.9, c[2] * 0.88, 1)),
                  b.inputs["Base Color"])
            inp(b, "Roughness", 0.46); inp(b, "Subsurface Weight", 0.3)
            inp(b, "Subsurface Radius", (1.0, 0.4, 0.22)); inp(b, "Subsurface Scale", 0.008)
            bump_chain(n, l, b, [(mott, 0.08, 0.004)])
        elif "hair" in low or "beard" in low:
            c = base_color(bpy.data.materials[mname])
            m, n, l, b, out = new_mat(mname)
            uvs = coord(n, "UV")
            sp = noise_tex(n, l, uvs, 1 / 0.002, 2)
            l.new(tint(n, l, c, maprange(n, l, sp, 0.35, 0.65, 0.8, 1.15)), b.inputs["Base Color"])
            inp(b, "Roughness", 0.8); inp(b, "Sheen Weight", 0.5)
            bump_chain(n, l, b, [(sp, 0.35, 0.001)])

# ---------- 3. poses ----------
def mirror(d):
    out = dict(d)
    for k, v in list(d.items()):
        if k.endswith(".L"):
            out[k[:-2] + ".R"] = (v[0], -v[1], -v[2])
    return out


def blend(a, b, t):
    t = max(0.0, min(1.0, t))
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, (0, 0, 0)), b.get(k, (0, 0, 0))
        out[k] = tuple(x + (y - x) * t for x, y in zip(va, vb))
    return out


def stand(f, wiggle=0.0):
    s = math.sin(f * 0.11 + wiggle)
    return mirror({"upperarm.L": (0.03 * s, 0, -0.08), "forearm.L": (-0.12, 0, 0), "chest": (0.015 * s, 0, 0)})


READY = {"thigh.L": (-0.35, 0, 0), "shin.L": (0.6, 0, 0), "foot.L": (-0.25, 0, 0),
         "thigh.R": (0.15, 0, 0), "shin.R": (0.45, 0, 0), "foot.R": (-0.3, 0, 0),
         "upperarm.L": (0.5, 0, -0.1), "upperarm.R": (-0.4, 0, 0.1), "forearm.L": (-1.0, 0, 0), "forearm.R": (-1.0, 0, 0),
         "chest": (0.3, 0, 0), "head": (-0.2, 0, 0)}


def run(p):
    d = {"chest": (0.2, 0, 0.08 * math.sin(p)), "head": (-0.15, 0, 0)}
    for sfx, off in (("L", 0.0), ("R", math.pi)):
        q = p + off
        a = 0.8 * math.sin(q)
        knee = 0.25 + 1.45 * max(0.0, math.cos(q)) ** 1.1
        d[f"thigh.{sfx}"] = (-a, 0, 0)
        d[f"shin.{sfx}"] = (knee, 0, 0)
        d[f"foot.{sfx}"] = (0.45 * a - 0.45 * knee + 0.2, 0, 0)
        sgn = -1 if sfx == "L" else 1
        d[f"upperarm.{sfx}"] = (0.95 * math.sin(q), 0, 0.1 * sgn)
        d[f"forearm.{sfx}"] = (-1.45, 0, 0)
    return d


def walk(p, amp=0.4):
    d = {}
    for sfx, off in (("L", 0.0), ("R", math.pi)):
        q = p + off
        a = amp * math.sin(q)
        knee = 0.1 + 0.6 * amp * max(0.0, math.cos(q))
        d[f"thigh.{sfx}"] = (-a, 0, 0); d[f"shin.{sfx}"] = (knee, 0, 0); d[f"foot.{sfx}"] = (0.5 * a - 0.5 * knee, 0, 0)
        d[f"upperarm.{sfx}"] = (0.6 * a, 0, -0.08 if sfx == "L" else 0.08); d[f"forearm.{sfx}"] = (-0.25, 0, 0)
    return d


DRIVE = {"thigh.L": (-1.25, 0, 0), "shin.L": (1.7, 0, 0), "foot.L": (-0.4, 0, 0),
         "thigh.R": (0.45, 0, 0), "shin.R": (0.25, 0, 0), "foot.R": (0.5, 0, 0),
         "upperarm.L": (0.7, 0, -0.15), "upperarm.R": (-2.2, 0, 0.15), "forearm.L": (-1.2, 0, 0), "forearm.R": (-0.5, 0, 0),
         "chest": (0.05, 0, 0), "head": (-0.25, 0, 0)}
SAIL = mirror({"thigh.L": (-1.1, 0, 0), "shin.L": (1.3, 0, 0), "foot.L": (-0.2, 0, 0),
               "upperarm.L": (-2.7, 0, -0.25), "forearm.L": (-0.3, 0, 0), "chest": (0.1, 0, 0), "head": (-0.2, 0, 0)})
REACH = mirror({"thigh.L": (-1.55, 0, 0), "shin.L": (0.25, 0, 0), "foot.L": (-0.3, 0, 0),
                "upperarm.L": (-1.3, 0, -0.15), "forearm.L": (-0.2, 0, 0), "chest": (0.55, 0, 0), "head": (-0.4, 0, 0)})
LAND = mirror({"thigh.L": (-1.6, 0, 0), "shin.L": (2.0, 0, 0), "foot.L": (-0.45, 0, 0),
               "upperarm.L": (-1.0, 0, -0.2), "forearm.L": (-0.4, 0, 0), "chest": (0.7, 0, 0), "head": (-0.45, 0, 0)})


def arms_up(f, bounce=0.0):
    s = math.sin(f * 0.55)
    d = mirror({"upperarm.L": (-2.85 + 0.12 * s, 0, -0.35), "forearm.L": (-0.25 - 0.15 * s, 0, 0),
                "chest": (-0.08, 0, 0), "head": (0.15, 0, 0)})
    if bounce:
        d.update(mirror({"thigh.L": (-0.35 * bounce, 0, 0), "shin.L": (0.7 * bounce, 0, 0), "foot.L": (-0.35 * bounce, 0, 0)}))
    return d


def fist_pump(f):
    s = 0.5 + 0.5 * math.sin(f * 0.6)
    d = stand(f)
    d.update({"upperarm.L": (-2.7 + 0.5 * s, 0, -0.3), "forearm.L": (-0.4 - 0.9 * s, 0, 0),
              "upperarm.R": (0.05, 0, 0.35), "forearm.R": (-1.3, 0, 0), "head": (0.1, 0, 0.1 * math.sin(f * 0.2)),
              "chest": (-0.05, 0, 0)})
    return d


# ---------- 4. the jumps ----------
class Plan:
    def __init__(self):
        self.frames = {}                                     # f -> (x, y, z, rotz_deg, pose)


def run_and_jump(plan, start_f, x0, vmax, dist, flight, height, pre_ready=12):
    """Ready, run to the takeoff line, fly `dist` meters, land and stand up. Returns (takeoff, land, end frame, end x)."""
    f, x, p = start_f, x0, 0.0
    for k in range(pre_ready):
        plan.frames[start_f - pre_ready + k] = (x0, LANE_Y, -0.06 * smooth(k / pre_ready), 90, blend(stand(f), READY, k / pre_ready))
    while x < TAKEOFF_X:
        t = (f - start_f) / FPS
        v = vmax * smooth(t / 0.9 + 0.08)
        x += v / FPS
        p += 2 * math.pi * v / 2.6 / FPS
        pose = blend(READY, run(p), (f - start_f) / 6)
        z = -0.03 + 0.06 * abs(math.sin(p)) * smooth(t / 0.6)
        plan.frames[f] = (min(x, TAKEOFF_X), LANE_Y, z, 90, pose)
        f += 1
    takeoff = f
    last = run(p)
    for k in range(flight + 1):
        u = k / flight
        xx = TAKEOFF_X + dist * u
        zz = 4 * height * u * (1 - u)
        if u < 0.15:
            pose = blend(last, DRIVE, u / 0.15)
        elif u < 0.5:
            pose = blend(DRIVE, SAIL, (u - 0.15) / 0.35)
        elif u < 0.85:
            pose = blend(SAIL, REACH, (u - 0.5) / 0.35)
        else:
            pose = REACH
        plan.frames[takeoff + k] = (xx, LANE_Y, zz, 90, pose)
    land = takeoff + flight
    xl = TAKEOFF_X + dist
    for k in range(1, 9):                                    # soak up the landing
        u = k / 8
        plan.frames[land + k] = (xl + 0.22 * smooth(u), LANE_Y, -0.55 * smooth(u) + 0.06, 90, blend(REACH, LAND, u))
    for k in range(1, 17):                                   # stand back up
        u = k / 16
        plan.frames[land + 8 + k] = (xl + 0.22 + 0.08 * smooth(u), LANE_Y, lerp(-0.49, 0.0, smooth(u)), 90,
                                     blend(LAND, stand(land + 8 + k), smooth(u)))
    return takeoff, land, land + 24, xl + 0.3


sam, grump = Plan(), Plan()
S_RUN = 30
s_to, s_land, s_up, s_x = run_and_jump(sam, S_RUN, -6.5, 5.6, 2.4, 18, 0.5)
# Sam walks off the mat to the north side of the lane and turns to watch
f = s_up
WALK_N = 30
for k in range(1, WALK_N + 1):
    u = k / WALK_N
    sam.frames[f + k] = (lerp(s_x, 3.55, smooth(u)), lerp(LANE_Y, -1.75, smooth(u)), 0.0,
                         lerp(90, 180, smooth(min(1, u * 1.6))), blend(walk(k * 0.45), stand(f + k), smooth((u - 0.8) / 0.2)))
f += WALK_N
for k in range(1, 13):
    sam.frames[f + k] = (3.55, -1.75, 0.0, lerp(180, 270, smooth(k / 12)), stand(f + k))
s_watch = f + 12

G_RUN = s_watch + 20
g_to, g_land, g_up, g_x = run_and_jump(grump, G_RUN, -8.0, 5.0, 3.3, 21, 0.6, pre_ready=14)
END = g_land + 100

# fill in the waiting and celebrating frames
for fr in range(1, END + 1):
    if fr not in sam.frames:
        if fr < S_RUN:
            sam.frames[fr] = (-6.5, LANE_Y, 0.0, 90, stand(fr))
        elif fr < g_land + 6:
            sam.frames[fr] = (3.55, -1.75, 0.0, 270, stand(fr))
        else:                                                # he lost, but he cheers!
            k = fr - (g_land + 6)
            rot = lerp(270, 380, smooth(k / 12))
            hop = k // 16
            u = (k % 16) / 16
            if hop < 4 and k >= 10:
                z = 0.28 * 4 * u * (1 - u)
                pose = arms_up(fr, bounce=1 - 4 * u * (1 - u) if u < 0.25 or u > 0.75 else 0)
            else:
                z = 0.0
                pose = blend(stand(fr), arms_up(fr), smooth(k / 10)) if k < 10 else arms_up(fr)
            sam.frames[fr] = (3.55, -1.75, z, rot, pose)
    if fr not in grump.frames:
        if fr < G_RUN:
            grump.frames[fr] = (-8.0, LANE_Y, 0.0, 90, stand(fr, 1.3))
        else:                                                # winner
            k = fr - g_up
            rot = lerp(90, 0, smooth(k / 14))
            if k < 16:
                pose = blend(stand(fr), arms_up(fr), smooth(k / 16))
            elif k < 46:
                pose = arms_up(fr)
            else:
                pose = blend(arms_up(fr), fist_pump(fr), smooth((k - 46) / 10))
            grump.frames[fr] = (g_x, LANE_Y, 0.0, rot, pose)

for key, plan in (("sam", sam), ("grump", grump)):
    rig = CAST[key]["rig"]
    for fr in range(1, END + 1):
        x, y, z, rot, pose = plan.frames[fr]
        rig.location = (x, y, z)
        rig.rotation_euler = (0, 0, math.radians(rot))
        rig.keyframe_insert("location", frame=fr); rig.keyframe_insert("rotation_euler", frame=fr)
        for bn in rig.pose.bones:
            bn.rotation_euler = pose.get(bn.name, (0, 0, 0))
            bn.keyframe_insert("rotation_euler", frame=fr)

# flags and scores appear after each jump
def show_from(ob, fr):
    ob.hide_render = True; ob.hide_viewport = True
    ob.keyframe_insert("hide_render", frame=1); ob.keyframe_insert("hide_viewport", frame=1)
    ob.hide_render = False; ob.hide_viewport = False
    ob.keyframe_insert("hide_render", frame=fr); ob.keyframe_insert("hide_viewport", frame=fr)


show_from(flag("Flag_Sam", TAKEOFF_X + 2.4, red_m), s_land + 30)
show_from(flag("Flag_Grump", TAKEOFF_X + 3.3, marker_m), g_land + 30)
show_from(text_obj("WB_Score1", f"{NAME_A}:  2.4 m", (-1.2, wb_y, 1.38), (math.radians(90), 0, 0), 0.16, red_m), s_land + 36)
show_from(text_obj("WB_Score2", "Mr. Grump:  3.3 m   WINNER!", (-1.2, wb_y, 1.1), (math.radians(90), 0, 0), 0.16, marker_m),
          g_land + 36)

# ---------- 5. camera ----------
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 26
cam.data.clip_start = 0.05
cam.rotation_mode = "XYZ"


def shot_open(fr):
    return Vector((-3.0, -6.55, 1.7)), Vector((-5.6, -2.5, 1.0))


def shot_track(plan):
    def f_(fr):
        x = plan.frames[fr][0]
        return Vector((x - 0.4, -6.5, 1.15)), Vector((x + 0.6, LANE_Y, 0.85))
    return f_


def shot_mid(fr):
    return Vector((2.4, -6.55, 1.55)), Vector((2.8, -2.4, 0.9))


def shot_final(fr):
    u = smooth((fr - (g_land + 30)) / 80)
    return Vector((4.1, -6.55 + 0.6 * u, 1.45 - 0.05 * u)), Vector((4.1, -2.4, 1.05))


segments = [  # (until frame, shot, blend frames into the next)
    (S_RUN - 4, shot_open, 14),
    (s_land + 22, shot_track(sam), 18),
    (G_RUN - 6, shot_mid, 16),
    (g_land + 14, shot_track(grump), 18),
    (END + 1, shot_final, 0),
]
prev = Euler((1.4, 0, 0))
for fr in range(1, END + 1):
    i = next(k for k, s in enumerate(segments) if fr <= s[0])
    pos, look = segments[i][1](fr)
    if i > 0:
        start, shot_prev, bl = segments[i - 1][0], segments[i - 1][1], segments[i - 1][2]
        if fr < start + bl:
            w = smooth((fr - start) / bl)
            p0, l0 = shot_prev(fr)
            pos, look = p0.lerp(pos, w), l0.lerp(look, w)
    cam.location = pos
    e = (look - pos).to_track_quat("-Z", "Y").to_euler("XYZ", prev); prev = e
    cam.rotation_euler = e
    cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_euler", frame=fr)

# ---------- 6. render settings (fast) ----------
sc.frame_start, sc.frame_end = 1, END
sc.render.fps = FPS
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        continue
sc.eevee.taa_render_samples = int(args.get("samples", "48"))
for attr, val in (("use_shadows", True), ("use_raytracing", True), ("use_gtao", True), ("shadow_ray_count", 2)):
    if hasattr(sc.eevee, attr):
        try:
            setattr(sc.eevee, attr, val)
        except Exception:
            pass
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.4
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = float(args.get("exposure", "0"))
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(Z, "field_day_frames", "f_")
sc.render.use_overwrite = False
sc.render.use_placeholder = True
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(Z, "field_day_video.blend"))
print(f"[fieldday] scene ready: {END} frames; sam jumps at {s_to}, grump at {g_to}")
