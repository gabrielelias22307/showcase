"""
Classroom Mystery - Mr. Elias and Mr. Grump blast off in jetpacks
=================================================================
A short, fast-to-render clip: both characters stand on the concrete pad in
front of the school wearing jetpacks. Mr. Elias lights up first, Mr. Grump's
jetpack sputters a beat later, they crouch and rocket straight up while the
sheep look up and the camera tilts after them.

Run with Blender in the background:
  blender -b --factory-startup --python duo_jetpack_scene.py -- dir=/path/to/folder
"dir" must hold gabriel_character.py, principal_character.py and rig_walk.py.
Saves duo_jetpack_video.blend there (frames go to duo_frames/). Uses EEVEE,
so it renders in a few minutes.
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler, noise
from mathutils.bvhtree import BVHTree

args = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
Z = args.get("dir", os.getcwd())
FPS = 24
END = 180
rnd = random.Random(5)

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


# ---------- characters, each with a skeleton ----------
rig_src = open(os.path.join(Z, "rig_walk.py")).read()
CAST = []          # (name, rig, meshes, torso name, x, ignite, lift)
for script, colname, torso_name, x, ign, lift in (("gabriel_character.py", "Character_Gabriel", "Torso", -0.62, 22, 46),
                                                    ("principal_character.py", "Character_Principal", "Shirt", 0.66, 32, 53)):
    exec(compile(open(os.path.join(Z, script)).read(), script, "exec"), {"__name__": "__main__"})
    src = (rig_src.replace('COLLECTION_PREFIX = "Character_"', f'COLLECTION_PREFIX = "{colname}"')
                  .replace("FACE_Y = 1", "FACE_Y = -1").replace("WALK_FRAMES = 374", "WALK_FRAMES = 2"))
    g = {"__name__": "__main__"}
    exec(compile(src, "rig_walk.py", "exec"), g)
    rig = g["rig"]
    rig.name = "Rig_" + colname.split("_")[1]
    rig.animation_data_clear()
    rig.location = (x, 0, 0); rig.rotation_euler = (0, 0, 0)
    col = bpy.data.collections[colname]
    CAST.append({"name": colname, "rig": rig, "col": col, "meshes": [o for o in col.all_objects if o.type == "MESH"],
                 "torso": torso_name, "x": x, "ignite": ign, "lift": lift})

for c in CAST:                                        # texture coordinates in meters
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
fabric("PR_ShirtWhite", "X", 0.0012, 0.12, 0.08, 0.35, 0.3, 0.6, 0.03)
fabric("PR_PantsNavy", "DIAGONAL", 0.0025, 0.2, 0.1, 0.4, 0.4, 0.7, 0.08)
fabric("PR_TieNavy", "DIAGONAL", 0.004, 0.35, 0.05, 0.1, 0.6, 0.45, 0.06)
for name in ("GB_Skin", "PR_Skin"):
    m0 = bpy.data.materials.get(name)
    if not m0:
        continue
    c = base_color(m0)
    m, n, l, b, out = new_mat(name)
    uvs = coord(n, "UV")
    mott = noise_tex(n, l, uvs, 1 / 0.025, 4)
    red = (c[0] * 1.08, c[1] * 0.9, c[2] * 0.88, 1)
    l.new(mix_col(n, l, maprange(n, l, mott, 0.35, 0.75, 0, 0.6), c, red), b.inputs["Base Color"])
    inp(b, "Roughness", 0.46); inp(b, "Subsurface Weight", 0.35)
    inp(b, "Subsurface Radius", (1.0, 0.4, 0.22)); inp(b, "Subsurface Scale", 0.008)
    pores = noise_tex(n, l, uvs, 1 / 0.0016, 2)
    bump_chain(n, l, b, [(mott, 0.08, 0.004), (pores, 0.12, 0.0005)])
for name in ("PR_ShoeBrown",):
    m0 = bpy.data.materials.get(name)
    if m0:
        c = base_color(m0)
        m, n, l, b, out = new_mat(name)
        uvs = coord(n, "UV")
        sp = noise_tex(n, l, uvs, 1 / 0.01, 3)
        l.new(tint(n, l, c, maprange(n, l, sp, 0.3, 0.7, 0.85, 1.1)), b.inputs["Base Color"])
        inp(b, "Roughness", 0.3); inp(b, "Coat Weight", 0.6)
for name, size in (("GB_Stubble", 0.0015), ("GB_HairDark", 0.002), ("PR_BeardWhite", 0.0015), ("PR_HairWhite", 0.002)):
    m0 = bpy.data.materials.get(name)
    if m0:
        c = base_color(m0)
        m, n, l, b, out = new_mat(name)
        uvs = coord(n, "UV")
        sp = noise_tex(n, l, uvs, 1 / size, 2)
        l.new(tint(n, l, c, maprange(n, l, sp, 0.35, 0.65, 0.8, 1.1)), b.inputs["Base Color"])
        inp(b, "Roughness", 0.8); inp(b, "Sheen Weight", 0.5)
        bump_chain(n, l, b, [(sp, 0.3, 0.001)])

# ---------- schoolyard ----------
def add_mesh(op, **kw):
    op(**kw)
    return bpy.context.active_object


m, n, l, b, out = new_mat("Grass")
wp = coord(n, "WORLD")
fine, big = noise_tex(n, l, wp, 30, 8), noise_tex(n, l, wp, 0.25, 4)
gc = mix_col(n, l, maprange(n, l, fine, 0.3, 0.7, 0, 1), (0.035, 0.08, 0.015, 1), (0.085, 0.16, 0.035, 1))
gc = mix_col(n, l, maprange(n, l, big, 0.55, 0.7, 0, 0.5), gc, (0.11, 0.085, 0.05, 1))
l.new(gc, b.inputs["Base Color"]); inp(b, "Roughness", 1.0)
bump_chain(n, l, b, [(fine, 0.7, 0.05)])
GRASS_M = m
ground = add_mesh(bpy.ops.mesh.primitive_plane_add, size=3000, location=(0, 0, -0.002))
ground.data.materials.append(GRASS_M)

m, n, l, b, out = new_mat("Concrete")
wp = coord(n, "WORLD")
c1, c2 = noise_tex(n, l, wp, 3, 6), noise_tex(n, l, wp, 0.4, 3)
vor = n.new("ShaderNodeTexVoronoi"); l.new(wp, vor.inputs["Vector"]); inp(vor, "Scale", 90)
grit = noise_tex(n, l, wp, 220, 2)
cc = mix_col(n, l, maprange(n, l, c1, 0.3, 0.7, 0, 1), (0.30, 0.295, 0.28, 1), (0.42, 0.41, 0.39, 1))
cc = mix_col(n, l, maprange(n, l, c2, 0.5, 0.75, 0, 0.35), cc, (0.2, 0.19, 0.17, 1))
cc = mix_col(n, l, maprange(n, l, vor.outputs["Distance"], 0.0, 0.12, 0.55, 0), cc, (0.12, 0.115, 0.11, 1))
l.new(cc, b.inputs["Base Color"]); inp(b, "Roughness", 0.9)
bump_chain(n, l, b, [(c1, 0.15, 0.02), (vor.outputs["Distance"], 0.25, 0.003), (grit, 0.3, 0.001)])
pad = add_mesh(bpy.ops.mesh.primitive_cylinder_add, radius=3.0, depth=0.06, vertices=64, location=(0, 0, 0))
pad.data.materials.append(m)
walk = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 11.5, 0))
walk.scale = (2.0, 17, 0.058); walk.data.materials.append(m)

m, n, l, b, out = new_mat("Brick")
wp = coord(n, "WORLD")
br = n.new("ShaderNodeTexBrick"); l.new(wp, br.inputs["Vector"])
inp(br, "Scale", 2.2); inp(br, "Mortar Size", 0.018)
inp(br, "Color1", (0.30, 0.09, 0.05, 1)); inp(br, "Color2", (0.46, 0.16, 0.09, 1)); inp(br, "Mortar", (0.5, 0.47, 0.42, 1))
bn = noise_tex(n, l, wp, 25, 6)
l.new(tint(n, l, br.outputs["Color"], maprange(n, l, bn, 0.3, 0.7, 0.8, 1.15)), b.inputs["Base Color"])
inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
l.new(br.outputs["Fac"], inv.inputs[1])
inp(b, "Roughness", 0.92)
bump_chain(n, l, b, [(inv.outputs[0], 0.15, 0.002)])
school = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 25, 5))
school.scale = (50, 10, 10); school.data.materials.append(m)
wm, n, l, b, out = new_mat("Window")
inp(b, "Base Color", (0.08, 0.12, 0.18, 1)); inp(b, "Roughness", 0.08); inp(b, "Metallic", 0.6)
tm, n, l, b, out = new_mat("Trim"); inp(b, "Base Color", (0.8, 0.8, 0.78, 1))
for row in (2.6, 6.4):
    for k in range(-11, 12):
        if abs(k) <= 1 and row < 4:
            continue
        w = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(k * 2.1, 19.95, row))
        w.scale = (1.4, 0.1, 1.8); w.data.materials.append(wm)
door = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 19.95, 1.4))
door.scale = (3.6, 0.12, 2.8); door.data.materials.append(wm)
for z in (0.25, 9.9):
    t = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 19.9, z))
    t.scale = (50, 0.2, 0.5); t.data.materials.append(tm)

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


patch = bmesh.new()
step = 0.3
xs, ys = int(30 / step), int(30 / step)
gv = [[patch.verts.new((-15 + i * step, -12 + j * step, 0)) for j in range(ys + 1)] for i in range(xs + 1)]
for i in range(xs):
    for j in range(ys):
        cx, cy = -15 + (i + 0.5) * step, -12 + (j + 0.5) * step
        if cx * cx + cy * cy > 3.15 ** 2 and not (abs(cx) < 1.1 and cy > 2.5):
            patch.faces.new((gv[i][j], gv[i + 1][j], gv[i + 1][j + 1], gv[i][j + 1]))
bmesh.ops.delete(patch, geom=[v for v in patch.verts if not v.link_faces], context="VERTS")
gp = mesh_obj("GrassNear", patch, [GRASS_M], smooth_shade=False)
md = gp.modifiers.new("Grass", "NODES")
md.node_group = scatter_group("ScatterGrass", clump, float(args.get("grass", "170")), (-0.15, -0.15, 0), (0.15, 0.15, 6.283), 0.7, 1.35, 1)

bark, n, l, b, out = new_mat("Bark"); inp(b, "Base Color", (0.12, 0.08, 0.05, 1)); inp(b, "Roughness", 0.95)
crown_m, n, l, b, out = new_mat("Leaves"); inp(b, "Base Color", (0.02, 0.05, 0.012, 1))
leaf_group = scatter_group("Leaves", leaf, 180, (0, 0, 0), (6.283, 6.283, 6.283), 0.8, 1.4, 3)
for x, y in ((-9, 6), (10, 8), (-14, 14), (15, 15), (-6, 15), (7, 16)):
    h = rnd.uniform(3.5, 5.0)
    tr = add_mesh(bpy.ops.mesh.primitive_cylinder_add, radius=0.17, depth=h, location=(x, y, h / 2)); tr.data.materials.append(bark)
    for k in range(3):
        cr = add_mesh(bpy.ops.mesh.primitive_ico_sphere_add, subdivisions=3, radius=rnd.uniform(1.4, 2.0),
                      location=(x + rnd.uniform(-0.7, 0.7), y + rnd.uniform(-0.7, 0.7), h + rnd.uniform(-0.2, 1.1)))
        cr.data.materials.append(crown_m)
        dm = cr.modifiers.new("lumpy", "DISPLACE"); tx = bpy.data.textures.new("lumps", "CLOUDS"); tx.noise_scale = 0.6
        dm.texture = tx; dm.strength = 0.6
        cr.modifiers.new("LeafCards", "NODES").node_group = leaf_group

# ---------- sheep ----------
# ---------- 4. sheep ----------
def wool_material(name, light, dark):
    m, n, l, b, out = new_mat(name)
    oc = coord(n, "Object")
    vor = n.new("ShaderNodeTexVoronoi"); l.new(oc, vor.inputs["Vector"]); inp(vor, "Scale", 38)
    try:
        vor.feature = "SMOOTH_F1"
    except Exception:
        pass
    clumps = noise_tex(n, l, oc, 9, 5)
    col_ = mix_col(n, l, maprange(n, l, clumps, 0.3, 0.7, 0, 1), dark, light)
    sep = n.new("ShaderNodeSeparateXYZ"); l.new(oc, sep.inputs[0])
    dirt = maprange(n, l, sep.outputs["Z"], 0.62, 0.3, 0, 0.7)
    col_ = mix_col(n, l, dirt, col_, (light[0] * 0.55, light[1] * 0.48, light[2] * 0.36, 1))
    l.new(col_, b.inputs["Base Color"])
    inp(b, "Roughness", 0.95); inp(b, "Sheen Weight", 0.9); inp(b, "Sheen Roughness", 0.5)
    inp(b, "Subsurface Weight", 0.12); inp(b, "Subsurface Radius", (0.6, 0.5, 0.4)); inp(b, "Subsurface Scale", 0.02)
    bump_chain(n, l, b, [(clumps, 0.5, 0.03), (vor.outputs["Distance"], 0.7, 0.008)])
    return m


WOOL = wool_material("SheepWool", (0.78, 0.73, 0.62, 1), (0.52, 0.47, 0.38, 1))
WOOL_DARK = wool_material("SheepWoolDark", (0.12, 0.1, 0.085, 1), (0.05, 0.04, 0.035, 1))
fm_, n, l, b, _ = new_mat("SheepFace")
oc = coord(n, "Object")
fz = noise_tex(n, l, oc, 120, 3)
l.new(tint(n, l, (0.03, 0.022, 0.018, 1), maprange(n, l, fz, 0.3, 0.7, 0.8, 1.3)), b.inputs["Base Color"])
inp(b, "Roughness", 0.65); inp(b, "Sheen Weight", 0.6)
bump_chain(n, l, b, [(fz, 0.2, 0.002)])
FACE = fm_
EYE, n, l, b, _ = new_mat("SheepEye"); inp(b, "Base Color", (0.01, 0.008, 0.006, 1)); inp(b, "Roughness", 0.08)
HOOF, n, l, b, _ = new_mat("SheepHoof"); inp(b, "Base Color", (0.02, 0.018, 0.015, 1)); inp(b, "Roughness", 0.5)


def lump(p, big=0.11, small=0.05):
    return big * abs(noise.noise(p * 9.0)) + small * abs(noise.noise(p * 23.0)) - 0.04


def blob(bm, c, r, mi, subdiv=4, rough=True, rot=None, taper=0.0):
    ret = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    c = Vector(c)
    for v in ret["verts"]:
        p = v.co.copy()
        k = 1 - taper * max(0.0, p.y)
        q = Vector((p.x * r[0] * k, p.y * r[1], p.z * r[2] * k))
        if rot is not None:
            q = rot @ q
        if rough:
            q = q * (1 + lump(c + q))
        v.co = c + q
    for f in {f for v in ret["verts"] for f in v.link_faces}:
        f.material_index = mi


def cyl(bm, base, r0, r1, h, mi, seg=10):
    ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=h)
    bmesh.ops.translate(bm, verts=ret["verts"], vec=Vector(base) + Vector((0, 0, h / 2)))
    for f in {f for v in ret["verts"] for f in v.link_faces}:
        f.material_index = mi


# body (faces +Y): wool 0, face/legs 1, hooves 2
bm = bmesh.new()
blob(bm, (0, 0.0, 0.64), (0.34, 0.5, 0.31), 0, 5)
blob(bm, (0, 0.3, 0.66), (0.3, 0.3, 0.29), 0, 4)
blob(bm, (0, -0.32, 0.67), (0.31, 0.3, 0.29), 0, 4)
blob(bm, (0, -0.6, 0.69), (0.07, 0.06, 0.1), 0, 2)
for sx in (-0.15, 0.15):
    for sy in (-0.36, 0.34):
        cyl(bm, (sx, sy, 0.04), 0.022, 0.032, 0.42, 1)
        cyl(bm, (sx, sy, 0.0), 0.028, 0.024, 0.045, 2)
        blob(bm, (sx, sy, 0.42), (0.08, 0.09, 0.1), 0, 3)
body_me = mesh_obj("SheepBody", bm, [WOOL, FACE, HOOF], link=False).data
body_dark = body_me.copy(); body_dark.materials[0] = WOOL_DARK

# head (around a neck pivot): wool 0, face 1, eyes 2
bm = bmesh.new()
blob(bm, (0, 0.04, 0.0), (0.15, 0.17, 0.17), 0, 4)
tilt = Matrix.Rotation(math.radians(-28), 3, "X")
blob(bm, (0, 0.2, 0.03), (0.085, 0.165, 0.095), 1, 4, rough=False, rot=tilt, taper=0.35)
for sx in (-1, 1):
    blob(bm, (sx * 0.1, 0.14, 0.08), (0.075, 0.032, 0.022), 1, 3, rough=False,
         rot=Matrix.Rotation(math.radians(sx * 20), 3, "Y"))
    blob(bm, (sx * 0.068, 0.2, 0.085), (0.016, 0.016, 0.016), 2, 2, rough=False)
blob(bm, (0, 0.11, 0.13), (0.08, 0.08, 0.055), 0, 3)
head_me = mesh_obj("SheepHead", bm, [WOOL, FACE, EYE], link=False).data
head_dark = head_me.copy(); head_dark.materials[0] = WOOL_DARK


flock = bpy.data.collections.new("Sheep"); sc.collection.children.link(flock)
sheep = []
spots = [(-4.5, 4.0), (-6.0, 7.5), (-3.2, 9.0), (-8.5, 3.0), (5.0, 4.5), (6.8, 6.5), (4.0, 10.0), (8.5, 10.5),
         (-10.5, 9.5), (11.0, 5.0), (-5.0, -2.5), (6.0, -1.5)]
for i, (x, y) in enumerate(spots):
    root = bpy.data.objects.new(f"Sheep_{i:02d}", None); flock.objects.link(root)
    root.location = (x + rnd.uniform(-0.3, 0.3), y + rnd.uniform(-0.3, 0.3), 0)
    root.rotation_euler.z = rnd.uniform(0, 2 * math.pi)
    s_ = rnd.uniform(0.9, 1.07); root.scale = (s_, s_, s_)
    dark = i in (2, 9)
    bo = bpy.data.objects.new(f"Sheep_{i:02d}_body", body_dark if dark else body_me); flock.objects.link(bo); bo.parent = root
    pv = bpy.data.objects.new(f"Sheep_{i:02d}_neck", None); flock.objects.link(pv); pv.parent = root
    pv.location = (0, 0.5, 0.74); pv.rotation_mode = "XYZ"
    ho = bpy.data.objects.new(f"Sheep_{i:02d}_head", head_dark if dark else head_me); flock.objects.link(ho); ho.parent = pv
    sheep.append((root, pv))

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


add_jetpack(CAST[0], red)
add_jetpack(CAST[1], blue)

# ---------- flames ----------
for c in CAST:
    IG, LF = c["ignite"], c["lift"]
    lazy = c["name"].endswith("Principal")
    for f in range(1, END + 1):
        on = f >= IG
        if f in (1, IG - 1, IG):
            for fo, inner in c["flames"]:
                fo.hide_render = not on; fo.hide_viewport = not on
                fo.keyframe_insert("hide_render", frame=f); fo.keyframe_insert("hide_viewport", frame=f)
        if not on:
            if f in (1, IG - 1):
                c["glow"].data.energy = 0; c["glow"].data.keyframe_insert("energy", frame=f)
            continue
        if f < LF:
            cough = lazy and rnd.random() < 0.35
            power = 0.05 if cough else 0.3 + 0.45 * rnd.random()
        else:
            power = 1.0 + 0.25 * rnd.random()
        for fo, inner in c["flames"]:
            w = 0.9 + 0.2 * rnd.random()
            fo.scale = (w, w, power * (0.75 if inner else 1.5))
            fo.keyframe_insert("scale", frame=f)
        c["glow"].data.energy = 900 * power
        c["glow"].data.keyframe_insert("energy", frame=f)

# ---------- poses and flight ----------
def mirror(d):
    out = dict(d)
    for k, v in list(d.items()):
        if k.endswith(".L"):
            out[k[:-2] + ".R"] = (v[0], -v[1], -v[2])
    return out


def pose(rig, frame, d):
    for bn in rig.pose.bones:
        bn.rotation_mode = "XYZ"
        bn.rotation_euler = d.get(bn.name, (0, 0, 0))
        bn.keyframe_insert("rotation_euler", frame=frame)


stand = mirror({"forearm.L": (-0.1, 0, 0), "upperarm.L": (0.02, 0, -0.07)})
crouch = mirror({"thigh.L": (-0.55, 0, 0), "shin.L": (1.05, 0, 0), "foot.L": (-0.5, 0, 0),
                 "upperarm.L": (0.65, 0, -0.1), "forearm.L": (-0.35, 0, 0), "chest": (0.18, 0, 0), "head": (-0.15, 0, 0)})
push = mirror({"thigh.L": (0.05, 0, 0), "shin.L": (0.08, 0, 0), "foot.L": (0.45, 0, 0),
               "upperarm.L": (0.45, 0, -0.15), "forearm.L": (-0.2, 0, 0)})
track = {}
for c in CAST:
    rig, LF, x = c["rig"], c["lift"], c["x"]
    lazy = c["name"].endswith("Principal")
    for f in (1, 12, LF - 8):
        sway = 0.04 * math.sin(f * 0.3)
        d = dict(stand); d["head"] = (0, 0, sway)
        pose(rig, f, d)
    pose(rig, LF - 1, crouch)
    pose(rig, LF + 4, push)
    z, vzv = 0.0, 0.0
    track[c["name"]] = {}
    for f in range(1, END + 1):
        tilt, roll = 0.0, 0.0
        px = x
        if f < LF - 7:
            z = 0.0
        elif f < LF:
            z = -0.11 * smooth((f - (LF - 7)) / 6)
        else:
            t = (f - LF) / FPS
            vzv = 7.0 * smooth(t / 0.9)
            z += vzv / FPS
            px = x + math.copysign(1.0, x) * 0.9 * smooth(t / 3)
            if lazy:                                          # Mr. Grump wobbles a bit
                roll = math.radians(9) * math.sin(t * 7.0) * (1 - 0.5 * smooth(t / 4))
                tilt = math.radians(5) * math.sin(t * 5.3)
        rig.location = (px, 0, z)
        rig.rotation_euler = (tilt, roll, 0)
        rig.keyframe_insert("location", frame=f); rig.keyframe_insert("rotation_euler", frame=f)
        track[c["name"]][f] = Vector((px, 0, z))
        if f >= LF + 10 and (f - LF) % 6 == 0:
            s = math.sin(f * (0.5 if lazy else 0.21))
            flail = 0.35 * s if lazy else 0.0
            pose(rig, f, {"thigh.L": (0.1 + 0.07 * s, 0, 0), "thigh.R": (0.1 - 0.07 * s, 0, 0),
                          "shin.L": (0.38 - 0.1 * s, 0, 0), "shin.R": (0.38 + 0.1 * s, 0, 0),
                          "foot.L": (0.5, 0, 0), "foot.R": (0.5, 0, 0),
                          "upperarm.L": (0.35, 0, -0.35 - flail), "upperarm.R": (0.35, 0, 0.35 + flail),
                          "forearm.L": (-0.3, 0, 0), "forearm.R": (-0.3, 0, 0),
                          "head": (-0.25, 0, 0)})

# ---------- smoke ----------
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


for c in CAST:
    LF = c["lift"]
    spot = track[c["name"]][LF]
    for i in range(18):
        a = i / 18 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
        d = Vector((math.cos(a), math.sin(a), 0))
        puff(LF - 3 + rnd.randint(0, 6), 50, spot + d * 0.35 + Vector((0, 0, 0.12)), d * rnd.uniform(3.0, 4.5),
             0.18, rnd.uniform(0.6, 1.0), 0.4, (0.45, 0.42, 0.36), 0.2, 0.6)
    for f in range(c["ignite"], END - 3):
        if f < LF and rnd.random() < 0.75:
            continue
        sc.frame_set(f)
        noz = c["nozzles"][f % 2]
        p0 = noz.matrix_world.translation.copy()
        down = (noz.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
        spread = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3))) * 0.5
        puff(f, 30, p0 + down * 0.5, down * 3.0 + spread, 0.08, rnd.uniform(0.55, 0.85), 0.35, (0.62, 0.6, 0.57), 0.3, 0.5)

# ---------- sheep: graze, then look up ----------
def key_head(pv, f, pitch, yaw):
    pv.rotation_euler = (math.radians(pitch), 0, math.radians(yaw))
    pv.keyframe_insert("rotation_euler", frame=int(f))


mid = {f: (track[CAST[0]["name"]][f] + track[CAST[1]["name"]][f]) / 2 for f in range(1, END + 1)}
for root, pv in sheep:
    pivot_w = root.matrix_world @ Vector((0, 0.5, 0.74))
    react = 26 + int((pivot_w.xy.length) / 12 * FPS)
    for f in range(1, react, 9):
        key_head(pv, f, -78 + rnd.uniform(-6, 6), rnd.uniform(-8, 8))
    for f in range(react, END + 1, 6):
        dvec = mid[f] + Vector((0, 0, 1.0)) - pivot_w
        phi = math.atan2(-dvec.x, dvec.y)
        rel = (phi - root.rotation_euler.z + math.pi) % (2 * math.pi) - math.pi
        rel = max(-1.4, min(1.4, rel))
        elev = math.atan2(dvec.z, dvec.xy.length) - math.radians(10)
        key_head(pv, f if f > react else react + 5, max(-12, min(48, math.degrees(elev))), math.degrees(rel))

# ---------- sky, sun, camera ----------
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
cam.data.lens = 32
cam.rotation_mode = "XYZ"
prev = Euler((1.4, 0, 0))
LIFT0 = min(c["lift"] for c in CAST)
for f in range(1, END + 1):
    s = smooth((f - 1) / (LIFT0 - 1))
    base = Vector((1.6, -5.6, 1.15)).lerp(Vector((0.7, -4.3, 0.8)), s)
    m_ = mid[f]
    if f <= LIFT0:
        pos, look = base, Vector((0.0, 0, 1.05))
    else:
        rise = max(0.0, m_.z - 2.0) * 0.93
        pos = base + Vector((0.02 * (f - LIFT0), -0.035 * (f - LIFT0), rise))
        look = m_ + Vector((0, 0, 1.0))
    cam.location = pos
    e = (look - pos).to_track_quat("-Z", "Y").to_euler("XYZ", prev); prev = e
    cam.rotation_euler = e
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)

# ---------- render settings (fast) ----------
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
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(Z, "duo_frames", "f_")
sc.render.use_overwrite = False
sc.render.use_placeholder = True
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(Z, "duo_jetpack_video.blend"))
print(f"[duo] scene ready: {END} frames")
