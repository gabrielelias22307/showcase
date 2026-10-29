"""
Classroom Mystery - the big race (and a jetpack finish)
=======================================================
An outdoor running track. Student B (Sam), Mr. Grump and Mr. Elias crouch at
the start line and sprint 40 m. Mr. Elias leads early, Sam passes him and
breaks the finish tape, Mr. Grump comes in last and out of breath. Sam
celebrates, then the jetpack on his back lights up and he flies off over
the track while the camera chases him.

Run with Blender in the background:
  blender -b --factory-startup --python race_jetpack_scene.py -- dir=/path/to/folder
"dir" must hold student_character.py, principal_character.py,
gabriel_character.py and rig_walk.py. Saves race_jetpack_video.blend there.
Renders with EEVEE straight to race_jetpack.mp4 (30 fps).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler, noise
from mathutils.bvhtree import BVHTree

args = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
Z = args.get("dir", os.getcwd())
FPS = 30
rnd = random.Random(21)

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


def add_mesh(op, **kw):
    op(**kw)
    return bpy.context.active_object


def box_obj(name, c, size, mat_):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = mesh_obj(name, bm, [mat_], smooth_shade=False)
    ob.location = c
    return ob


def plain(name, color, rough=0.6, **extra):
    m, n, l, b, _ = new_mat(name)
    inp(b, "Base Color", color); inp(b, "Roughness", rough)
    for k, v in extra.items():
        inp(b, k.replace("_", " "), v)
    return m


def text_obj(name, body, loc, rot, size, mat_, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.size = size; cu.align_x = align; cu.extrude = 0.004
    ob = bpy.data.objects.new(name, cu)
    sc.collection.objects.link(ob)
    ob.location = loc; ob.rotation_euler = rot
    cu.materials.append(mat_)
    return ob


# ---------- 1. the track and the field ----------
LANES = (-1.22, 0.0, 1.22)          # Mr. Elias, Sam, Mr. Grump
FINISH = 40.0

m, n, l, b, out = new_mat("Grass")
wp = coord(n, "WORLD")
fine, big = noise_tex(n, l, wp, 30, 8), noise_tex(n, l, wp, 0.25, 4)
gc = mix_col(n, l, maprange(n, l, fine, 0.3, 0.7, 0, 1), (0.035, 0.08, 0.015, 1), (0.085, 0.16, 0.035, 1))
l.new(gc, b.inputs["Base Color"]); inp(b, "Roughness", 1.0)
bump_chain(n, l, b, [(fine, 0.7, 0.05)])
GRASS_M = m
ground = add_mesh(bpy.ops.mesh.primitive_plane_add, size=3000, location=(0, 0, -0.002))
ground.data.materials.append(GRASS_M)

track_m, n, l, b, out = new_mat("TrackRubber")
wp = coord(n, "WORLD")
speck = noise_tex(n, l, wp, 260, 2)
patch = noise_tex(n, l, wp, 0.6, 3)
tc = mix_col(n, l, maprange(n, l, speck, 0.3, 0.7, 0, 1), (0.32, 0.07, 0.04, 1), (0.48, 0.13, 0.07, 1))
tc = mix_col(n, l, maprange(n, l, patch, 0.5, 0.75, 0, 0.3), tc, (0.26, 0.06, 0.035, 1))
l.new(tc, b.inputs["Base Color"]); inp(b, "Roughness", 0.85)
bump_chain(n, l, b, [(speck, 0.35, 0.002)])
box_obj("Track", (27.5, 0, 0.01), (95, 4.8, 0.02), track_m)
line_m = plain("LinePaint", (0.85, 0.85, 0.82, 1), 0.7)
for y in (-1.83, -0.61, 0.61, 1.83):
    box_obj("LaneLine", (27.5, y, 0.021), (95, 0.05, 0.002), line_m)
box_obj("StartLine", (-0.05, 0, 0.021), (0.08, 3.66, 0.002), line_m)
box_obj("FinishLine", (FINISH, 0, 0.021), (0.12, 3.66, 0.002), line_m)
for i, y in enumerate(LANES):
    text_obj(f"LaneNo_{i + 1}", str(i + 1), (-1.2, y, 0.022), (0, 0, math.radians(-90)), 0.7, line_m)
curb_m = plain("Curb", (0.75, 0.75, 0.73, 1), 0.8)
for y in (-2.45, 2.45):
    box_obj("Curb", (27.5, y, 0.04), (95, 0.1, 0.08), curb_m)

# finish banner, poles and tape
pole_m = plain("Pole", (0.8, 0.8, 0.82, 1), 0.3, Metallic=1.0)
banner_m = plain("Banner", (0.04, 0.12, 0.5, 1), 0.6)
for y in (-2.65, 2.65):
    pl = add_mesh(bpy.ops.mesh.primitive_cylinder_add, radius=0.04, depth=3.3, location=(FINISH, y, 1.65))
    pl.data.materials.append(pole_m)
box_obj("FinishBanner", (FINISH, 0, 2.85), (0.03, 5.3, 0.6), banner_m)
text_obj("FinishText", "FINISH", (FINISH - 0.02, 0, 2.66), (math.radians(90), 0, math.radians(-90)), 0.42, line_m)
text_obj("FinishTextBack", "FINISH", (FINISH + 0.02, 0, 2.66), (math.radians(90), 0, math.radians(90)), 0.42, line_m)
tape_m = plain("Tape", (0.7, 0.05, 0.04, 1), 0.5)
tape_whole = box_obj("FinishTape", (FINISH, 0, 1.12), (0.015, 5.2, 0.03), tape_m)
halves = []
for y, sgn in ((-2.62, 1), (2.62, -1)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.015, (v.co.y + 0.5) * 2.4 * sgn, v.co.z * 0.03))
    h = mesh_obj("TapeHalf", bm, [tape_m], smooth_shade=False)
    h.location = (FINISH, y, 1.12); h.rotation_mode = "XYZ"
    halves.append((h, sgn))

# bleachers behind the track
alu = plain("Aluminum", (0.62, 0.63, 0.65, 1), 0.35, Metallic=0.9)
for k in range(5):
    box_obj("BleacherStep", (25, 8.0 + k * 0.8, 0.22 + k * 0.45), (34, 0.8, 0.06), alu)
    box_obj("BleacherRiser", (25, 8.0 + k * 0.8 - 0.38, 0.11 + k * 0.45), (34, 0.03, 0.22 + 0.45), alu)
box_obj("BleacherRail", (25, 11.6, 2.9), (34, 0.05, 0.05), alu)
box_obj("BleacherBack", (25, 11.65, 1.2), (34, 0.05, 2.4), plain("Frame", (0.25, 0.26, 0.28, 1), 0.5))

# trees and the school in the distance
bark = plain("Bark", (0.12, 0.08, 0.05, 1), 0.95)
crown_m = plain("Leaves", (0.02, 0.05, 0.012, 1), 0.9)
brick = plain("BrickPlain", (0.33, 0.1, 0.06, 1), 0.9)
school = box_obj("School", (25, 46, 6), (70, 12, 12), brick)
win_m = plain("Window", (0.06, 0.09, 0.14, 1), 0.1, Metallic=0.5)
for row in (3.0, 7.5):
    for k in range(-14, 15):
        box_obj("Window", (25 + k * 2.3, 39.95, row), (1.4, 0.1, 1.8), win_m)

hidden = bpy.data.collections.new("Parts (hidden)")
sc.collection.children.link(hidden)
hidden.hide_render = True; hidden.hide_viewport = True

# a clump of 7 grass blades
bm = bmesh.new()
for k in range(7):
    a = k / 7 * 2 * math.pi + rnd.uniform(-0.4, 0.4)
    h = rnd.uniform(0.07, 0.15); w = rnd.uniform(0.004, 0.007); lean = rnd.uniform(0.1, 0.45)
    ox, oy = 0.012 * math.cos(a), 0.012 * math.sin(a)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    rows = []
    for t in (0, 0.35, 0.7, 1.0):
        bend = lean * t * t * h
        cx, cy, cz = ox + dx * bend, oy + dy * bend, h * t
        ww = w * (1 - t) + 0.0004
        if t < 1:
            rows.append((bm.verts.new((cx - px * ww, cy - py * ww, cz)), bm.verts.new((cx + px * ww, cy + py * ww, cz))))
        else:
            rows.append((bm.verts.new((cx, cy, cz)),))
    for r0, r1 in zip(rows, rows[1:]):
        bm.faces.new((r0[0], r0[1], r1[-1], r1[0]) if len(r1) == 2 else (r0[0], r0[1], r1[0]))
clump = mesh_obj("GrassClump", bm, [grass_material()], link=False)
hidden.objects.link(clump)

bm = bmesh.new()                                      # leaf card
vs = [bm.verts.new(p) for p in ((0, -0.055, 0), (0.028, 0, 0), (0, 0.055, 0.004), (-0.028, 0, 0))]
bm.faces.new(vs)
leaf = mesh_obj("Leaf", bm, [leaf_material()], link=False)
hidden.objects.link(leaf)

def scatter_group(name, inst, density, rot_min, rot_max, s_min, s_max, seed=0):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    dist = N.new("GeometryNodeDistributePointsOnFaces")
    dist.inputs["Density"].default_value = density
    dist.inputs["Seed"].default_value = seed
    L.new(gi.outputs[0], dist.inputs["Mesh"])
    info = N.new("GeometryNodeObjectInfo"); info.inputs["Object"].default_value = inst
    rv = N.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT_VECTOR"
    rv.inputs[0].default_value = rot_min; rv.inputs[1].default_value = rot_max
    rs = N.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"
    fs = [s for s in rs.inputs if s.name in ("Min", "Max") and s.type == "VALUE"]
    fs[0].default_value, fs[1].default_value = s_min, s_max
    iop = N.new("GeometryNodeInstanceOnPoints")
    L.new(dist.outputs["Points"], iop.inputs["Points"])
    L.new(info.outputs["Geometry"], iop.inputs["Instance"])
    L.new(rv.outputs[0], iop.inputs["Rotation"])
    fo = [s for s in rs.outputs if s.type == "VALUE"][0]
    L.new(fo, iop.inputs["Scale"])
    jn = N.new("GeometryNodeJoinGeometry")
    L.new(iop.outputs["Instances"], jn.inputs[0])
    L.new(gi.outputs[0], jn.inputs[0])
    L.new(jn.outputs[0], go.inputs[0])
    return ng


leaf_group = scatter_group("Leaves", leaf, 170, (0, 0, 0), (6.283, 6.283, 6.283), 0.8, 1.4, 3)
for x in [-12 + 9 * i + rnd.uniform(-2, 2) for i in range(11)]:
    y = rnd.uniform(16, 24)
    h = rnd.uniform(4, 6)
    tr = add_mesh(bpy.ops.mesh.primitive_cylinder_add, radius=0.2, depth=h, location=(x, y, h / 2)); tr.data.materials.append(bark)
    for k in range(3):
        cr = add_mesh(bpy.ops.mesh.primitive_ico_sphere_add, subdivisions=3, radius=rnd.uniform(1.6, 2.4),
                      location=(x + rnd.uniform(-0.8, 0.8), y + rnd.uniform(-0.8, 0.8), h + rnd.uniform(-0.2, 1.2)))
        cr.data.materials.append(crown_m)
        dm = cr.modifiers.new("lumpy", "DISPLACE"); tx = bpy.data.textures.new("lumps", "CLOUDS"); tx.noise_scale = 0.6
        dm.texture = tx; dm.strength = 0.6
        cr.modifiers.new("LeafCards", "NODES").node_group = leaf_group


def grass_band(name, x0, x1, y0, y1, dens):
    bm = bmesh.new()
    step = 0.5
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    gv = [[bm.verts.new((x0 + i * step, y0 + j * step, 0)) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((gv[i][j], gv[i + 1][j], gv[i + 1][j + 1], gv[i][j + 1]))
    ob = mesh_obj(name, bm, [GRASS_M], smooth_shade=False)
    ob.modifiers.new("Grass", "NODES").node_group = scatter_group("Scatter_" + name, clump, dens,
                                                                   (-0.15, -0.15, 0), (0.15, 0.15, 6.283), 0.7, 1.35, len(name))


grass_band("GrassNear", -14, 72, -14, -2.55, float(args.get("grass", "150")))
grass_band("GrassBack", -14, 72, 2.55, 7.5, float(args.get("grass", "150")) * 0.7)

# ---------- 2. the runners ----------
rig_src = open(os.path.join(Z, "rig_walk.py")).read()
CAST = {}
for key, script, colname, torso, env, lane in (("elias", "gabriel_character.py", "Character_Gabriel", "Torso", None, LANES[0]),
                                               ("sam", "student_character.py", "Character_StudentB", "Top", "B", LANES[1]),
                                               ("grump", "principal_character.py", "Character_Principal", "Shirt", None, LANES[2])):
    if env:
        os.environ["CM_WHO"] = env
    exec(compile(open(os.path.join(Z, script)).read(), script, "exec"), {"__name__": "__main__"})
    src = (rig_src.replace('COLLECTION_PREFIX = "Character_"', f'COLLECTION_PREFIX = "{colname}"')
                  .replace("WALK_FRAMES = 374", "WALK_FRAMES = 2"))
    g = {"__name__": "__main__"}
    exec(compile(src, "rig_walk.py", "exec"), g)
    rig = g["rig"]; rig.name = "Rig_" + key
    rig.animation_data_clear()
    for bn in rig.pose.bones:
        bn.rotation_mode = "XYZ"
    col = bpy.data.collections[colname]
    CAST[key] = {"name": colname, "rig": rig, "col": col, "meshes": [o for o in col.all_objects if o.type == "MESH"],
                 "torso": torso, "x": 0.0, "lane": lane}

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

fabric("GB_ShirtNavy", "Y", 0.0024, 0.25, 0.07, 0.45, 0.45, 0.85)
fabric("GB_PantsBlack", "DIAGONAL", 0.003, 0.3, 0.09, 0.55, 0.55, 0.8, 0.12)
fabric("GB_CapBlack", "DIAGONAL", 0.0025, 0.3, 0.05, 0.15, 0.5, 0.75, 0.1)
fabric("GB_ShoeGreyBrown", None, 1, 0, 0.012, 0.25, 0.7, 0.95, 0.12)
for mname in [m.name for m in bpy.data.materials]:
    low = mname.lower()
    if mname.startswith(("STB_", "PR_")):
        if "hoodie" in low or "pattern" in low:
            fabric(mname, "Y", 0.003, 0.25, 0.08, 0.5, 0.6, 0.9, 0.08)
        elif "pants" in low:
            fabric(mname, "DIAGONAL", 0.003, 0.25, 0.09, 0.5, 0.5, 0.8, 0.08)
        elif "shirt" in low:
            fabric(mname, "X", 0.0012, 0.12, 0.08, 0.35, 0.3, 0.6, 0.03)
        elif "tie" in low:
            fabric(mname, "DIAGONAL", 0.004, 0.35, 0.05, 0.1, 0.6, 0.45, 0.06)
    if mname.startswith(("STB_", "PR_", "GB_")) and low.endswith("_skin"):
        c = base_color(bpy.data.materials[mname])
        m, n, l, b, out = new_mat(mname)
        uvs = coord(n, "UV")
        mott = noise_tex(n, l, uvs, 1 / 0.025, 4)
        l.new(mix_col(n, l, maprange(n, l, mott, 0.35, 0.75, 0, 0.6), c, (c[0] * 1.08, c[1] * 0.9, c[2] * 0.88, 1)),
              b.inputs["Base Color"])
        inp(b, "Roughness", 0.46); inp(b, "Subsurface Weight", 0.3)
        inp(b, "Subsurface Radius", (1.0, 0.4, 0.22)); inp(b, "Subsurface Scale", 0.008)
        bump_chain(n, l, b, [(mott, 0.08, 0.004)])

# ---------- 3. Sam's jetpack ----------
# ---------- jetpacks ----------
metal, n, l, b, _ = new_mat("JetMetal")
oc = coord(n, "Object")
mp = n.new("ShaderNodeMapping"); l.new(oc, mp.inputs["Vector"]); mp.inputs["Scale"].default_value = (300, 300, 4)
brush = noise_tex(n, l, mp.outputs["Vector"], 2, 4)
l.new(tint(n, l, (0.78, 0.79, 0.8, 1), maprange(n, l, brush, 0.3, 0.7, 0.9, 1.05)), b.inputs["Base Color"])
inp(b, "Metallic", 1.0); inp(b, "Roughness", 0.24); inp(b, "Anisotropic", 0.6)
red, n, l, b, _ = new_mat("JetRed")
inp(b, "Base Color", (0.55, 0.03, 0.02, 1)); inp(b, "Roughness", 0.3); inp(b, "Coat Weight", 0.7)
blue, n, l, b, _ = new_mat("JetBlue")
inp(b, "Base Color", (0.03, 0.12, 0.55, 1)); inp(b, "Roughness", 0.3); inp(b, "Coat Weight", 0.7)
darkm, n, l, b, _ = new_mat("JetDark")
inp(b, "Base Color", (0.025, 0.025, 0.027, 1)); inp(b, "Roughness", 0.6); inp(b, "Sheen Weight", 0.4)

def flame_material(name, inner):
    m, n, l, b, out = new_mat(name)
    n.remove(b)
    oc = coord(n, "Object")
    sep = n.new("ShaderNodeSeparateXYZ"); l.new(oc, sep.inputs[0])
    t = n.new("ShaderNodeMath"); t.operation = "MULTIPLY"; t.inputs[1].default_value = -1
    l.new(sep.outputs["Z"], t.inputs[0])
    cr = n.new("ShaderNodeValToRGB")
    els = cr.color_ramp.elements
    if inner:
        els[0].color = (0.85, 0.9, 1.0, 1); els[1].color = (0.3, 0.45, 1.0, 1)
    else:
        els[0].color = (1.0, 0.92, 0.7, 1); els[1].color = (0.6, 0.06, 0.0, 1)
        e = els.new(0.3); e.color = (1.0, 0.5, 0.1, 1)
    l.new(t.outputs[0], cr.inputs["Fac"])
    nz = n.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
    l.new(oc, nz.inputs["Vector"]); inp(nz, "Scale", 4); inp(nz, "Detail", 4)
    dr = nz.inputs["W"].driver_add("default_value"); dr.driver.expression = "frame*0.45"
    fade = maprange(n, l, t.outputs[0], 0.25, 1.0, 1.0, 0.0)
    flick = maprange(n, l, nz.outputs["Fac"], 0.35, 0.65, 0.4, 1.3)
    a = n.new("ShaderNodeMath"); a.operation = "MULTIPLY"; a.use_clamp = True
    l.new(fade, a.inputs[0]); l.new(flick, a.inputs[1])
    em = n.new("ShaderNodeEmission"); l.new(cr.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 30 if inner else 18
    tr = n.new("ShaderNodeBsdfTransparent")
    ms = n.new("ShaderNodeMixShader")
    l.new(a.outputs[0], ms.inputs["Fac"]); l.new(tr.outputs[0], ms.inputs[1]); l.new(em.outputs[0], ms.inputs[2])
    l.new(ms.outputs[0], out.inputs[0])
    return m


FL_OUT, FL_IN = flame_material("Flame", False), flame_material("FlameCore", True)


def add_jetpack(c, stripe):
    meshes, rig = c["meshes"], c["rig"]
    rig.location = (0, 0, 0); bpy.context.view_layer.update()
    top = max((o.matrix_parent_inverse @ o.matrix_basis @ v.co).z for o in meshes for v in o.data.vertices)
    S = top / 1.80
    torso = bpy.data.objects[c["torso"]]
    tmw = torso.matrix_parent_inverse @ torso.matrix_basis
    tverts = [tmw @ v.co for v in torso.data.vertices]
    tree = BVHTree.FromPolygons(tverts, [list(p.vertices) for p in torso.data.polygons])
    back = max(v.y for v in tverts if 1.12 * S < v.z < 1.36 * S)
    J0 = Vector((0, back + 0.075, 1.22 * S))
    bm = bmesh.new()
    for sx in (-0.085, 0.085):
        cyl(bm, (sx, 0, -0.2), 0.07, 0.07, 0.4, 0, 32)
        blob(bm, (sx, 0, 0.2), (0.07, 0.07, 0.07), 0, 3, rough=False)
        cyl(bm, (sx, 0, -0.29), 0.06, 0.04, 0.09, 2, 24)
        cyl(bm, (sx, 0, 0.26), 0.014, 0.014, 0.05, 2, 12)
        for z in (-0.13, 0.1):
            cyl(bm, (sx, 0, z), 0.0715, 0.0715, 0.03, 1, 32)
    cyl(bm, (0, -0.035, -0.18), 0.05, 0.05, 0.34, 2, 4)

    def ribbon(pts, width, axis, mi):
        rows = []
        for p, nrm in pts:
            q = p - J0
            a = bm.verts.new(q - axis * width / 2); cc_ = bm.verts.new(q + axis * width / 2)
            a2 = bm.verts.new(q - axis * width / 2 + nrm * 0.006); c2 = bm.verts.new(q + axis * width / 2 + nrm * 0.006)
            rows.append((a, cc_, c2, a2))
        for r0, r1 in zip(rows, rows[1:]):
            for k in range(4):
                bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k])).material_index = mi

    ctr = Vector((0, 0.0, 1.28 * S))
    for sx in (-0.11, 0.11):
        pts = []
        for a in [math.radians(a) for a in range(-30, 216, 6)]:
            d = Vector((0, math.cos(a), math.sin(a)))
            hit = tree.ray_cast(Vector((sx, ctr.y, ctr.z)) + d * 0.5, -d)
            if hit[0] is not None:
                pts.append((hit[0] + d * 0.007, d))
        ribbon(pts, 0.042, Vector((1, 0, 0)), 2)
    front = []
    for x in [i * 0.01 for i in range(-11, 12)]:
        hit = tree.ray_cast(Vector((x, -0.6, 1.29 * S)), Vector((0, 1, 0)))
        if hit[0] is not None:
            front.append((hit[0] + Vector((0, -0.008, 0)), Vector((0, -1, 0))))
    if front:
        ribbon(front, 0.03, Vector((0, 0, 1)), 2)
    jet = mesh_obj("Jetpack_" + c["name"].split("_")[1], bm, [metal, stripe, darkm])
    c["col"].objects.link(jet); sc.collection.objects.unlink(jet)
    rig.data.pose_position = "REST"; bpy.context.view_layer.update()
    want = rig.matrix_world @ Matrix.Translation(J0)
    jet.parent = rig; jet.parent_type = "BONE"; jet.parent_bone = "chest"
    bpy.context.view_layer.update()
    jet.matrix_world = want
    rig.data.pose_position = "POSE"
    flames, nozzles = [], []
    for sx in (-0.085, 0.085):
        noz = bpy.data.objects.new("Nozzle", None); sc.collection.objects.link(noz)
        noz.parent = jet; noz.location = (sx, 0, -0.29); nozzles.append(noz)
        for mat_, r, inner in ((FL_OUT, 0.055, False), (FL_IN, 0.028, True)):
            fb = bmesh.new()
            ret = bmesh.ops.create_cone(fb, cap_ends=False, segments=24, radius1=0.0, radius2=r, depth=1.0)
            bmesh.ops.translate(fb, verts=ret["verts"], vec=(0, 0, -0.5))
            fo = mesh_obj("Flame", fb, [mat_]); fo.parent = noz; fo.visible_shadow = False
            flames.append((fo, inner))
    glow = bpy.data.objects.new("ThrustLight", bpy.data.lights.new("ThrustLight", "POINT"))
    sc.collection.objects.link(glow); glow.parent = jet; glow.location = (0, 0, -0.6)
    glow.data.color = (1.0, 0.55, 0.2); glow.data.shadow_soft_size = 0.15
    rig.location = (c["x"], 0, 0)
    c.update(flames=flames, nozzles=nozzles, glow=glow)



add_jetpack(CAST["sam"], red)

# ---------- 4. poses ----------
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
               "upperarm.L": (-2.7, 0, 0.25), "forearm.L": (-0.3, 0, 0), "chest": (0.1, 0, 0), "head": (-0.2, 0, 0)})
REACH = mirror({"thigh.L": (-1.55, 0, 0), "shin.L": (0.25, 0, 0), "foot.L": (-0.3, 0, 0),
                "upperarm.L": (-1.3, 0, -0.15), "forearm.L": (-0.2, 0, 0), "chest": (0.55, 0, 0), "head": (-0.4, 0, 0)})
LAND = mirror({"thigh.L": (-1.6, 0, 0), "shin.L": (2.0, 0, 0), "foot.L": (-0.45, 0, 0),
               "upperarm.L": (-1.0, 0, -0.2), "forearm.L": (-0.4, 0, 0), "chest": (0.7, 0, 0), "head": (-0.45, 0, 0)})


def arms_up(f, bounce=0.0):
    s = math.sin(f * 0.55)
    d = mirror({"upperarm.L": (-2.85 + 0.12 * s, 0, 0.35), "forearm.L": (-0.25 - 0.15 * s, 0, 0),
                "chest": (-0.08, 0, 0), "head": (0.15, 0, 0)})
    if bounce:
        d.update(mirror({"thigh.L": (-0.35 * bounce, 0, 0), "shin.L": (0.7 * bounce, 0, 0), "foot.L": (-0.35 * bounce, 0, 0)}))
    return d


def fist_pump(f):
    s = 0.5 + 0.5 * math.sin(f * 0.6)
    d = stand(f)
    d.update({"upperarm.L": (-2.7 + 0.5 * s, 0, 0.3), "forearm.L": (-0.4 - 0.9 * s, 0, 0),
              "upperarm.R": (0.05, 0, 0.35), "forearm.R": (-1.3, 0, 0), "head": (0.1, 0, 0.1 * math.sin(f * 0.2)),
              "chest": (-0.05, 0, 0)})
    return d




SET = {"thigh.L": (-1.05, 0, 0), "shin.L": (1.9, 0, 0), "foot.L": (-0.55, 0, 0),
       "thigh.R": (-0.25, 0, 0), "shin.R": (1.3, 0, 0), "foot.R": (-0.9, 0, 0),
       "upperarm.L": (-0.75, 0, -0.12), "upperarm.R": (-0.75, 0, 0.12), "forearm.L": (-0.1, 0, 0), "forearm.R": (-0.1, 0, 0),
       "chest": (0.95, 0, 0), "head": (-0.55, 0, 0)}
TIRED = mirror({"thigh.L": (-0.35, 0, 0), "shin.L": (0.55, 0, 0), "foot.L": (-0.2, 0, 0),
                "upperarm.L": (-0.75, 0, -0.1), "forearm.L": (-0.5, 0, 0), "chest": (0.75, 0, 0), "head": (-0.35, 0, 0)})
CROUCH = mirror({"thigh.L": (-0.55, 0, 0), "shin.L": (1.05, 0, 0), "foot.L": (-0.5, 0, 0),
                 "upperarm.L": (0.65, 0, -0.1), "forearm.L": (-0.35, 0, 0), "chest": (0.18, 0, 0), "head": (-0.15, 0, 0)})


def flying(f, tilt):
    s = math.sin(f * 0.21)
    return {"thigh.L": (0.1 + 0.07 * s, 0, 0), "thigh.R": (0.1 - 0.07 * s, 0, 0),
            "shin.L": (0.38 - 0.1 * s, 0, 0), "shin.R": (0.38 + 0.1 * s, 0, 0),
            "foot.L": (0.5, 0, 0), "foot.R": (0.5, 0, 0),
            "upperarm.L": (0.42, 0, -0.32), "upperarm.R": (0.42, 0, 0.32),
            "forearm.L": (-0.25, 0, 0), "forearm.R": (-0.25, 0, 0),
            "head": (-0.7 * tilt, 0, 0)}


def look_up(f):
    d = stand(f)
    d["head"] = (-0.45, 0, 0); d["neck"] = (-0.2, 0, 0)
    return d


# ---------- 5. the race ----------
GO = 36
SPEED = {"elias": (7.35, 6.7, 3.0), "sam": (6.8, 7.9, 3.0), "grump": (6.4, 5.95, 2.5)}   # early, late, switch time
plan = {k: {} for k in CAST}
finish_f = {}
stop = {}
for key, (v1, v2, ts) in SPEED.items():
    y = CAST[key]["lane"]
    x, p, f, v = 0.0, 0.0, GO, 0.0
    for fr in range(1, GO):
        plan[key][fr] = (x, y, -0.32 if fr > 8 else -0.32 * smooth(fr / 8), 90, blend(stand(fr), SET, smooth(fr / 8)))
    while True:
        t = (f - GO) / FPS
        if key not in finish_f:
            vt = lerp(v1, v2, smooth((t - ts) / 0.6))
            v = vt * smooth(t / 1.3 + 0.06)
            if x >= FINISH:
                finish_f[key] = f
                v_fin = v
        else:
            k = f - finish_f[key]
            v = v_fin * max(0.0, 1 - k / (2.2 * FPS))
            if v <= 0.01:
                stop[key] = (f, x)
                break
        x += v / FPS
        p += 2 * math.pi * v / 2.6 / FPS
        pose = blend(SET, run(p), (f - GO) / 7)
        if key in finish_f:
            k = f - finish_f[key]
            pose = blend(run(p), walk(p * 0.8, 0.35), smooth(k / (2.0 * FPS)))
        z = lerp(-0.32, -0.03 + 0.06 * abs(math.sin(p)), smooth((f - GO) / 9))
        plan[key][f] = (x, y, z, 90, pose)
        f += 1

S_FIN = finish_f["sam"]
assert S_FIN < finish_f["elias"] < finish_f["grump"], finish_f
sam_stop_f, sam_x = stop["sam"]
CHEER = sam_stop_f + 4
IGNITE = CHEER + 60
LIFT = IGNITE + 20
FLY = 160
END = LIFT + FLY

# after the race: Elias and Grump catch their breath, then watch Sam fly
for key in ("elias", "grump"):
    f0, x0 = stop[key]
    y = CAST[key]["lane"]
    for fr in range(f0, END + 1):
        k = fr - f0
        if key == "grump":
            pose = blend(walk(0.0, 0.0), TIRED, smooth(k / 12))
            if fr > LIFT + 10:
                pose = blend(TIRED, look_up(fr), smooth((fr - LIFT - 10) / 16))
            rot = 90
        else:
            pose = blend(walk(0.0, 0.0), stand(fr), smooth(k / 12))
            if fr > IGNITE:
                pose = blend(stand(fr), look_up(fr), smooth((fr - IGNITE - 6) / 14))
            rot = lerp(90, 40, smooth((fr - IGNITE) / 20)) if fr > IGNITE else 90
        z = 0.0
        plan[key][fr] = (x0, y, z, rot, pose)

# Sam: cheer, light the jetpack, crouch, blast off
def vz(t): return 7.0 * smooth(t / 0.9) if t < 2.4 else lerp(7.0, 2.2, smooth((t - 2.4) / 1.8))
def vx(t): return 5.5 * smooth((t - 1.0) / 1.6)


pos = Vector((sam_x, LANES[1], 0.0))
zc = -0.11
for fr in range(sam_stop_f, END + 1):
    tilt, rot = 0.0, 90.0
    if fr < IGNITE:
        k = fr - sam_stop_f
        rot = lerp(90, 8, smooth(k / 14))
        hop = (k - 10) % 15 / 15 if k >= 10 else 0
        z = 0.25 * 4 * hop * (1 - hop) if 10 <= k < 55 else 0.0
        pose = blend(walk(0.0, 0.0), arms_up(fr), smooth(k / 10))
        if k >= 50:
            pose = blend(arms_up(fr), stand(fr), smooth((k - 50) / 8))
        pos.z = z
    elif fr < LIFT:
        rot = 8
        u = (fr - (LIFT - 8)) / 7
        pose = blend(stand(fr), CROUCH, smooth(u))
        pos.z = -0.11 * smooth(u)
    else:
        t = (fr - LIFT) / FPS
        zc += vz(t) / FPS
        pos.z = zc
        pos.x += vx(t) / FPS
        rot = lerp(8, 90, smooth((t - 0.6) / 1.2))
        tilt = min(math.radians(45), 0.7 * math.atan2(vx(t), max(vz(t), 0.05)))
        if fr < LIFT + 8:
            pose = blend(CROUCH, {}, smooth((fr - LIFT) / 6))
        else:
            pose = blend({}, flying(fr, tilt), smooth((fr - LIFT - 8) / 10))
    plan["sam"][fr] = (pos.x, pos.y, pos.z, rot, pose, tilt)

for key, c in CAST.items():
    rig = c["rig"]
    for fr in range(1, END + 1):
        st = plan[key][fr]
        x, y, z, rot, pose = st[:5]
        tilt = st[5] if len(st) > 5 else 0.0
        rig.location = (x, y, z)
        rig.rotation_euler = (tilt, 0, math.radians(rot))
        rig.keyframe_insert("location", frame=fr); rig.keyframe_insert("rotation_euler", frame=fr)
        for bn in rig.pose.bones:
            bn.rotation_euler = pose.get(bn.name, (0, 0, 0))
            bn.keyframe_insert("rotation_euler", frame=fr)

# the tape breaks when Sam reaches it
def vis(ob, frames):
    for fr, on in frames:
        ob.hide_render = not on; ob.hide_viewport = not on
        ob.keyframe_insert("hide_render", frame=fr); ob.keyframe_insert("hide_viewport", frame=fr)


vis(tape_whole, [(1, True), (S_FIN, False)])
for h, sgn in halves:
    vis(h, [(1, False), (S_FIN, True)])
    for fr, ang in ((S_FIN, 0), (S_FIN + 6, 95), (S_FIN + 11, 70), (S_FIN + 16, 84), (S_FIN + 24, 78)):
        h.rotation_euler = (math.radians(-ang * sgn), 0, 0)
        h.keyframe_insert("rotation_euler", frame=fr)

# ---------- 6. flames and smoke ----------
c = CAST["sam"]
for fr in range(1, END + 1):
    on = fr >= IGNITE
    if fr in (1, IGNITE - 1, IGNITE):
        for fo, inner in c["flames"]:
            fo.hide_render = not on; fo.hide_viewport = not on
            fo.keyframe_insert("hide_render", frame=fr); fo.keyframe_insert("hide_viewport", frame=fr)
    if not on:
        if fr in (1, IGNITE - 1):
            c["glow"].data.energy = 0; c["glow"].data.keyframe_insert("energy", frame=fr)
        continue
    power = (0.3 + 0.45 * rnd.random()) if fr < LIFT else (1.0 + 0.25 * rnd.random())
    for fo, inner in c["flames"]:
        w = 0.9 + 0.2 * rnd.random()
        fo.scale = (w, w, power * (0.75 if inner else 1.5))
        fo.keyframe_insert("scale", frame=fr)
    c["glow"].data.energy = 900 * power
    c["glow"].data.keyframe_insert("energy", frame=fr)

sm, n, l, b, _ = new_mat("Smoke")
oi = n.new("ShaderNodeObjectInfo")
oc = coord(n, "Object")
puffy = noise_tex(n, l, oc, 2.5, 4)
l.new(oi.outputs["Color"], b.inputs["Base Color"]); inp(b, "Roughness", 1.0)
al = n.new("ShaderNodeMath"); al.operation = "MULTIPLY"
l.new(oi.outputs["Alpha"], al.inputs[0]); l.new(maprange(n, l, puffy, 0.35, 0.65, 0.2, 1.0), al.inputs[1])
l.new(al.outputs[0], b.inputs["Alpha"])
bm = bmesh.new()
blob(bm, (0, 0, 0), (1, 1, 1), 0, 3, rough=False)
for v in bm.verts:
    v.co *= 1 + 0.25 * noise.noise(v.co * 2.2)
puff_me = mesh_obj("Puff", bm, [sm], link=False).data
smoke = bpy.data.collections.new("Smoke"); sc.collection.children.link(smoke)


def puff(start, life, p0, vel, s0, s1, a0, color, rise=0.0, drag=0.6):
    o = bpy.data.objects.new("Puff", puff_me); smoke.objects.link(o)
    o.rotation_euler = (rnd.random() * 6, rnd.random() * 6, rnd.random() * 6)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=start)
    o.hide_render = True; o.keyframe_insert("hide_render", frame=start + life)
    for k in range(0, life + 1, 3):
        t = k / FPS
        go = drag * (1 - math.exp(-t / drag))
        o.location = p0 + vel * go + Vector((0, 0, rise * t))
        u = k / life
        sz = lerp(s0, s1, 1 - (1 - u) ** 2)
        o.scale = (sz, sz, sz * 0.85)
        o.color = (color[0], color[1], color[2], a0 * (1 - u) ** 1.5)
        for key in ("location", "scale", "color"):
            o.keyframe_insert(key, frame=start + k)


spot = Vector((sam_x, LANES[1], 0.0))
for i in range(20):
    a = i / 20 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
    d = Vector((math.cos(a), math.sin(a), 0))
    puff(LIFT - 3 + rnd.randint(0, 6), 60, spot + d * 0.35 + Vector((0, 0, 0.12)), d * rnd.uniform(3.0, 4.5),
         0.18, rnd.uniform(0.6, 1.0), 0.4, (0.45, 0.4, 0.36), 0.2, 0.6)
for fr in range(IGNITE, END - 3):
    if fr < LIFT and rnd.random() < 0.75:
        continue
    sc.frame_set(fr)
    noz = c["nozzles"][fr % 2]
    p0 = noz.matrix_world.translation.copy()
    down = (noz.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    spread = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3))) * 0.5
    puff(fr, 36, p0 + down * 0.5, down * 3.0 + spread, 0.08, rnd.uniform(0.55, 0.85), 0.35, (0.62, 0.6, 0.57), 0.3, 0.5)

# ---------- 7. sky, sun, camera ----------
world = bpy.data.worlds.new("Sky"); sc.world = world; world.use_nodes = True
bgn = world.node_tree.nodes["Background"]
sky = world.node_tree.nodes.new("ShaderNodeTexSky")
try:
    sky.sky_type = "NISHITA"
except TypeError:
    pass
for attr, val in (("sun_elevation", math.radians(40)), ("sun_rotation", math.radians(115)), ("altitude", 100), ("dust_density", 1.5)):
    if hasattr(sky, attr):
        setattr(sky, attr, val)
world.node_tree.links.new(sky.outputs["Color"], bgn.inputs["Color"])
bgn.inputs["Strength"].default_value = float(args.get("sky", "0.12"))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = float(args.get("sun", "2.6")); sun.data.angle = math.radians(1.5); sun.data.color = (1.0, 0.96, 0.9)
sun.rotation_euler = Euler((math.radians(50), 0, math.radians(25)))
sc.collection.objects.link(sun)

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 30
cam.rotation_mode = "XYZ"


def P(key, fr):
    st = plan[key][min(fr, END)]
    return Vector((st[0], st[1], st[2]))


def shot_start(fr):
    u = smooth(fr / GO)
    return Vector((7.5 - 1.0 * u, -6.8, 1.35)), Vector((0.2, 0.0, 0.65))


def shot_race(fr):
    xs = [P(k, fr).x for k in CAST]
    lead, last = max(xs), min(xs)
    mid = (lead + last) / 2
    return Vector((mid - 0.5, -8.0 - 0.25 * (lead - last), 1.55)), Vector((mid + 1.2, 0.0, 0.85))


def shot_finish(fr):
    s = P("sam", fr)
    return Vector((s.x + 0.5, -7.0, 1.5)), Vector((s.x - 1.5, 0.2, 1.0))


def shot_lift(fr):
    s = P("sam", fr)
    return Vector((sam_x + 3.2, -6.0, 0.55)), s + Vector((0, 0, 1.0))


def shot_chase(fr):
    s = P("sam", fr)
    return s + Vector((3.6, -5.6, 1.4)), s + Vector((0, 0, 0.3))


segments = [(GO + 4, shot_start, 20), (S_FIN + 14, shot_race, 24), (IGNITE - 4, shot_finish, 18),
            (LIFT + 28, shot_lift, 50), (END + 1, shot_chase, 0)]
prev = Euler((1.4, 0, 0))
for fr in range(1, END + 1):
    i = next(k for k, s_ in enumerate(segments) if fr <= s_[0])
    pos_, look = segments[i][1](fr)
    if i > 0:
        start, shot_prev, bl = segments[i - 1]
        if fr < start + bl:
            w = smooth((fr - start) / bl)
            p0, l0 = shot_prev(fr)
            pos_, look = p0.lerp(pos_, w), l0.lerp(look, w)
    cam.location = pos_
    e = (look - pos_).to_track_quat("-Z", "Y").to_euler("XYZ", prev); prev = e
    cam.rotation_euler = e
    cam.keyframe_insert("location", frame=fr); cam.keyframe_insert("rotation_euler", frame=fr)

# ---------- 8. render settings (fast, straight to MP4) ----------
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
sc.view_settings.exposure = float(args.get("exposure", "-0.5"))
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 100
im = sc.render.image_settings
if hasattr(im, "media_type"):
    im.media_type = "VIDEO"
im.file_format = "FFMPEG"
sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"
sc.render.ffmpeg.constant_rate_factor = "HIGH"; sc.render.ffmpeg.audio_codec = "NONE"
sc.render.filepath = os.path.join(Z, "race_jetpack_rendering.mp4")
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(Z, "race_jetpack_video.blend"))
print(f"[race] scene ready: {END} frames; finish frames {finish_f}; lift-off {LIFT}")
