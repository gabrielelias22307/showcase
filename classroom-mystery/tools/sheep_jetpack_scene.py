"""
Classroom Mystery - walking video with sheep and a jetpack ending
=================================================================
Builds on walk_video_scene.py (character, walk, schoolyard, swoop and three
camera circles) and adds:

  - a flock of woolly sheep grazing on both sides of the sidewalk; when the
    jetpack starts, their heads pop up and they watch him fly
  - real-looking surfaces: knit shirt, twill pants and cap, suede shoes,
    skin with a soft glow, thousands of grass blades, leafy trees,
    speckled concrete, brick with sunken mortar
  - a jetpack on his back; at the end he stops, the flames light, he
    crouches, blasts off and flies up high over the sheep while the
    camera chases him

Run with Blender in the background:
  blender -b --factory-startup --python sheep_jetpack_scene.py -- dir=/path/to/folder
"dir" must hold walk_video_scene.py, gabriel_character.py and rig_walk.py.
Saves gabriel_jetpack_video.blend there (frames go to jetpack_frames/).
"""
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix, Euler, noise
from mathutils.bvhtree import BVHTree

args = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
Z = args.get("dir", os.getcwd())
GRASS = float(args.get("grass", "1"))          # grass thickness (lower = faster)

# ---------- 1. the walking scene ----------
src = open(os.path.join(Z, "walk_video_scene.py")).read()
src = src.replace("bpy.ops.wm.save_as_mainfile(", "pass  # (")
g = {"__name__": "__main__"}
exec(compile(src, "walk_video_scene.py", "exec"), g)
sc = bpy.context.scene
RIG = bpy.data.objects["Rig"]
cam, target, path = g["cam"], g["target"], g["path"]
FPS, WALK = g["FPS"], g["FRAMES"]          # walk ends at frame WALK (374)
IGNITE, LIFT = WALK + 4, WALK + 21          # flames on, blast off
END = WALK + 192                            # 8 more seconds
rnd = random.Random(11)
col = next(c for c in bpy.data.collections if c.name.startswith("Character_"))
meshes = [o for o in col.all_objects if o.type == "MESH"]


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


# ---------- 2. his clothes and skin ----------
# texture coordinates in meters, projected from each face's main direction
for ob in meshes:
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


fabric("GB_ShirtNavy", "Y", 0.0024, 0.25, 0.07, 0.45, 0.45, 0.85)
fabric("GB_PantsBlack", "DIAGONAL", 0.003, 0.3, 0.09, 0.55, 0.55, 0.8, 0.12)
fabric("GB_CapBlack", "DIAGONAL", 0.0025, 0.3, 0.05, 0.15, 0.5, 0.75, 0.1)
fabric("GB_ShoeGreyBrown", None, 1, 0, 0.012, 0.25, 0.7, 0.95, 0.12)
fabric("GB_ShoeSole", None, 1, 0, 0.004, 0.15, 0.0, 0.9)
fabric("GB_ShoeLace", "X", 0.002, 0.3, 0.02, 0.1, 0.3, 0.9)

skin0 = bpy.data.materials.get("GB_Skin")
if skin0:
    c = base_color(skin0)
    m, n, l, b, out = new_mat("GB_Skin")
    uvs = coord(n, "UV")
    mott = noise_tex(n, l, uvs, 1 / 0.025, 4)
    red = (c[0] * 1.08, c[1] * 0.9, c[2] * 0.88, 1)
    l.new(mix_col(n, l, maprange(n, l, mott, 0.35, 0.75, 0, 0.6), c, red), b.inputs["Base Color"])
    inp(b, "Roughness", 0.46); inp(b, "Subsurface Weight", 0.35)
    inp(b, "Subsurface Radius", (1.0, 0.4, 0.22)); inp(b, "Subsurface Scale", 0.008)
    pores = noise_tex(n, l, uvs, 1 / 0.0016, 2)
    bump_chain(n, l, b, [(mott, 0.08, 0.004), (pores, 0.12, 0.0005)])
for name, size in (("GB_Stubble", 0.0015), ("GB_HairDark", 0.002), ("GB_Brow", 0.0015)):
    m0 = bpy.data.materials.get(name)
    if m0:
        c = base_color(m0)
        m, n, l, b, out = new_mat(name)
        uvs = coord(n, "UV")
        sp = noise_tex(n, l, uvs, 1 / size, 2)
        l.new(tint(n, l, c, maprange(n, l, sp, 0.35, 0.65, 0.75, 1.2)), b.inputs["Base Color"])
        inp(b, "Roughness", 0.8); inp(b, "Sheen Weight", 0.5)
        bump_chain(n, l, b, [(sp, 0.3, 0.001)])

# ---------- 3. the schoolyard surfaces ----------
# ground under the grass: dense dark undergrowth with a few dirt patches
m, n, l, b, out = new_mat("Grass")
wp = coord(n, "WORLD")
fine, big = noise_tex(n, l, wp, 30, 8), noise_tex(n, l, wp, 0.25, 4)
gc = mix_col(n, l, maprange(n, l, fine, 0.3, 0.7, 0, 1), (0.035, 0.08, 0.015, 1), (0.085, 0.16, 0.035, 1))
gc = mix_col(n, l, maprange(n, l, big, 0.55, 0.7, 0, 0.5), gc, (0.11, 0.085, 0.05, 1))
l.new(gc, b.inputs["Base Color"]); inp(b, "Roughness", 1.0)
bump_chain(n, l, b, [(fine, 0.7, 0.05)])

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
j, nj, lj, bj, _ = new_mat("Joint")
inp(bj, "Base Color", (0.06, 0.058, 0.055, 1)); inp(bj, "Roughness", 1.0)
for o in bpy.data.objects:
    if o.type == "MESH" and abs(o.scale.y - 0.02) < 1e-4 and abs(o.scale.x - 2.0) < 1e-4:
        o.data.materials.clear(); o.data.materials.append(j); o.scale.z = 0.006

m, n, l, b, out = new_mat("Brick")
wp = coord(n, "WORLD")
br = n.new("ShaderNodeTexBrick"); l.new(wp, br.inputs["Vector"])
inp(br, "Scale", 2.2); inp(br, "Mortar Size", 0.018); inp(br, "Bias", 0.0)
inp(br, "Color1", (0.30, 0.09, 0.05, 1)); inp(br, "Color2", (0.46, 0.16, 0.09, 1)); inp(br, "Mortar", (0.5, 0.47, 0.42, 1))
bn = noise_tex(n, l, wp, 25, 6)
l.new(tint(n, l, br.outputs["Color"], maprange(n, l, bn, 0.3, 0.7, 0.8, 1.15)), b.inputs["Base Color"])
inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1
l.new(br.outputs["Fac"], inv.inputs[1])
inp(b, "Roughness", 0.92)
bump_chain(n, l, b, [(inv.outputs[0], 0.6, 0.01), (bn, 0.25, 0.003)])

m, n, l, b, out = new_mat("Bark")
wp = coord(n, "WORLD")
mp = n.new("ShaderNodeMapping"); l.new(wp, mp.inputs["Vector"]); mp.inputs["Scale"].default_value = (6, 6, 0.8)
bk = noise_tex(n, l, mp.outputs["Vector"], 4, 8, 0.6, 1.2)
l.new(mix_col(n, l, bk, (0.05, 0.035, 0.022, 1), (0.2, 0.15, 0.1, 1)), b.inputs["Base Color"])
inp(b, "Roughness", 0.95)
bump_chain(n, l, b, [(bk, 0.9, 0.02)])

m, n, l, b, out = new_mat("Leaves")                 # tree crowns: dark, shaded inside
inp(b, "Base Color", (0.02, 0.05, 0.012, 1)); inp(b, "Roughness", 0.9)


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

bm = bmesh.new()                                      # little flower
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.012)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.09))
fm, fn, fl, fb, _ = new_mat("Flower")
oi = fn.new("ShaderNodeObjectInfo")
fl.new(mix_col(fn, fl, oi.outputs["Random"], (0.95, 0.75, 0.05, 1), (0.95, 0.95, 0.9, 1)), fb.inputs["Base Color"])
flower = mesh_obj("Flower", bm, [fm], link=False)
hidden.objects.link(flower)


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


def grass_patch(name, x0, x1, y0, y1, step, keep):
    bm = bmesh.new()
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    grid = [[bm.verts.new((x0 + i * step, y0 + j * step, 0.0)) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            cx, cy = x0 + (i + 0.5) * step, y0 + (j + 0.5) * step
            if keep(cx, cy):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    return mesh_obj(name, bm, [bpy.data.materials["Grass"]], smooth_shade=False)


def off_paths(x, y):
    on_pad = x * x + y * y < 3.3 ** 2
    on_walk = abs(x) < 1.08 and 2.9 < y < 37.2
    under_school = y > 36.8
    return not (on_pad or on_walk or under_school)


inner = grass_patch("GrassNear", -10, 10, -12, 37, 0.25, off_paths)
middle = grass_patch("GrassMid", -22, 22, -24, 37, 0.5,
                     lambda x, y: off_paths(x, y) and not (-10 < x < 10 and -12 < y < 37))
outer = grass_patch("GrassFar", -60, 60, -60, 37, 1.0,
                    lambda x, y: off_paths(x, y) and not (-22 < x < 22 and -24 < y < 37))
for ob, dens, seed in ((inner, 260 * GRASS, 1), (middle, 170 * GRASS, 2), (outer, 60 * GRASS, 4)):
    ob.location.z = 0.0
    md = ob.modifiers.new("Grass", "NODES")
    md.node_group = scatter_group(f"Scatter_{ob.name}", clump, dens, (-0.15, -0.15, 0), (0.15, 0.15, 6.283), 0.7, 1.35, seed)
    mf = ob.modifiers.new("Flowers", "NODES")
    mf.node_group = scatter_group(f"Flowers_{ob.name}", flower, 0.5, (0, 0, 0), (0, 0, 0), 0.7, 1.3, seed + 7)

# leaves on every tree crown
leaf_group = scatter_group("Leaves", leaf, 180, (0, 0, 0), (6.283, 6.283, 6.283), 0.8, 1.4, 3)
trunks = []
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.data.materials and o.data.materials[0].name == "Leaves":
        md = o.modifiers.new("LeafCards", "NODES"); md.node_group = leaf_group
    if o.type == "MESH" and o.data.materials and o.data.materials[0].name == "Bark":
        trunks.append(Vector((o.location.x, o.location.y)))

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

flock = bpy.data.collections.new("Sheep")
sc.collection.children.link(flock)
spots = []
clusters = [((9, 4), 9, 2.6), ((-10, 9), 8, 2.6), ((0, 28.5), 11, 3.4), ((11.5, 20), 6, 2.2),
            ((-8.5, -6), 6, 2.2), ((-13, 24), 5, 2.4)]


def ok_spot(x, y):
    if y < 21.5 and abs(x) < 5.6: return False
    if x * x + y * y < 4.8 ** 2: return False
    if y > 35.3 or y < -14 or abs(x) > 21: return False
    if any((Vector((x, y)) - t).length < 2.2 for t in trunks): return False
    return all((Vector((x, y)) - s).length > 1.5 for s in spots)


for (cx, cy), count, spread in clusters:
    made, tries = 0, 0
    while made < count and tries < 400:
        tries += 1
        x, y = rnd.gauss(cx, spread), rnd.gauss(cy, spread)
        if ok_spot(x, y):
            spots.append(Vector((x, y))); made += 1
dark_ids = {3, 17, 30}
sheep = []
for i, s in enumerate(spots):
    root = bpy.data.objects.new(f"Sheep_{i:02d}", None)
    root.empty_display_size = 0.4
    flock.objects.link(root)
    root.location = (s.x, s.y, 0.0)
    root.rotation_euler.z = rnd.uniform(0, 2 * math.pi)
    sz = rnd.uniform(0.88, 1.08); root.scale = (sz, sz, sz)
    dark = i in dark_ids
    bo = bpy.data.objects.new(f"Sheep_{i:02d}_body", body_dark if dark else body_me)
    flock.objects.link(bo); bo.parent = root
    pv = bpy.data.objects.new(f"Sheep_{i:02d}_neck", None)
    flock.objects.link(pv); pv.parent = root; pv.location = (0, 0.5, 0.74)
    pv.rotation_mode = "XYZ"
    ho = bpy.data.objects.new(f"Sheep_{i:02d}_head", head_dark if dark else head_me)
    flock.objects.link(ho); ho.parent = pv
    sheep.append((root, pv))

# ---------- 5. jetpack ----------
top = max((o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices)
S = top / 1.80
torso = bpy.data.objects["Torso"]
tmw = torso.matrix_parent_inverse @ torso.matrix_basis
tverts = [tmw @ v.co for v in torso.data.vertices]
tree = BVHTree.FromPolygons(tverts, [list(p.vertices) for p in torso.data.polygons])
back = max(v.y for v in tverts if 1.12 * S < v.z < 1.36 * S)
J0 = Vector((0, back + 0.075, 1.22 * S))

metal, n, l, b, _ = new_mat("JetMetal")
oc = coord(n, "Object")
mp = n.new("ShaderNodeMapping"); l.new(oc, mp.inputs["Vector"]); mp.inputs["Scale"].default_value = (300, 300, 4)
brush = noise_tex(n, l, mp.outputs["Vector"], 2, 4)
l.new(tint(n, l, (0.78, 0.79, 0.8, 1), maprange(n, l, brush, 0.3, 0.7, 0.9, 1.05)), b.inputs["Base Color"])
inp(b, "Metallic", 1.0); inp(b, "Roughness", 0.24); inp(b, "Anisotropic", 0.6)
bump_chain(n, l, b, [(brush, 0.05, 0.001)])
red, n, l, b, _ = new_mat("JetRed")
inp(b, "Base Color", (0.55, 0.03, 0.02, 1)); inp(b, "Roughness", 0.3); inp(b, "Coat Weight", 0.7)
darkm, n, l, b, _ = new_mat("JetDark")
oc = coord(n, "Object")
wv = noise_tex(n, l, oc, 400, 2)
inp(b, "Base Color", (0.025, 0.025, 0.027, 1)); inp(b, "Roughness", 0.6); inp(b, "Sheen Weight", 0.4)
bump_chain(n, l, b, [(wv, 0.2, 0.0008)])

bm = bmesh.new()
for sx in (-0.085, 0.085):
    cyl(bm, (sx, 0, -0.2), 0.07, 0.07, 0.4, 0, 32)
    blob(bm, (sx, 0, 0.2), (0.07, 0.07, 0.07), 0, 3, rough=False)
    cyl(bm, (sx, 0, -0.29), 0.06, 0.04, 0.09, 2, 24)        # nozzle bell
    cyl(bm, (sx, 0, 0.26), 0.014, 0.014, 0.05, 2, 12)       # valve
    for z in (-0.13, 0.1):
        cyl(bm, (sx, 0, z), 0.0715, 0.0715, 0.03, 1, 32)    # red stripes
cyl(bm, (0, -0.035, -0.18), 0.05, 0.05, 0.34, 2, 4)          # frame between the tanks
# shoulder and chest straps that follow his shirt
def strap_points(x, angles, center, radius):
    pts = []
    for a in angles:
        d = Vector((0, math.cos(a), math.sin(a)))
        start = Vector((x, center.y, center.z)) + d * radius
        hit = tree.ray_cast(start, -d)
        if hit[0] is not None:
            pts.append((hit[0] + d * 0.007, d))
    return pts


def ribbon(pts, width, axis, mi):
    rows = []
    for p, nrm in pts:
        q = p - J0
        side = axis
        a = bm.verts.new(q - side * width / 2); c = bm.verts.new(q + side * width / 2)
        a2 = bm.verts.new(q - side * width / 2 + nrm * 0.006); c2 = bm.verts.new(q + side * width / 2 + nrm * 0.006)
        rows.append((a, c, c2, a2))
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(4):
            bm.faces.new((r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k])).material_index = mi


ctr = Vector((0, 0.0, 1.28 * S))
for sx in (-0.11, 0.11):
    angs = [math.radians(a) for a in range(-30, 216, 6)]        # back (around the top) to front
    pts = strap_points(sx, angs, ctr, 0.5)
    ribbon(pts, 0.042, Vector((1, 0, 0)), 2)
front = []
for x in [i * 0.01 for i in range(-11, 12)]:
    start = Vector((x, -0.5, 1.29 * S))
    hit = tree.ray_cast(start, Vector((0, 1, 0)))
    if hit[0] is not None:
        front.append((hit[0] + Vector((0, -0.008, 0)), Vector((0, -1, 0))))
ribbon(front, 0.03, Vector((0, 0, 1)), 2)
blob(bm, (0, front[len(front) // 2][0].y - J0.y - 0.012, 1.29 * S - J0.z), (0.022, 0.008, 0.016), 0, 2, rough=False)
jet = mesh_obj("Jetpack", bm, [metal, red, darkm])
for p in jet.data.polygons:
    p.use_smooth = True
col.objects.link(jet); sc.collection.objects.unlink(jet)
RIG.data.pose_position = "REST"
sc.frame_set(1); bpy.context.view_layer.update()
want = RIG.matrix_world @ Matrix.Translation(J0)
jet.parent = RIG; jet.parent_type = "BONE"; jet.parent_bone = "chest"
bpy.context.view_layer.update()
jet.matrix_world = want
RIG.data.pose_position = "POSE"

# flames, light and smoke
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
flames, nozzles = [], []
for sx in (-0.085, 0.085):
    noz = bpy.data.objects.new("Nozzle", None); sc.collection.objects.link(noz)
    noz.parent = jet; noz.location = (sx, 0, -0.29)
    nozzles.append(noz)
    for mat_, r, inner in ((FL_OUT, 0.055, False), (FL_IN, 0.028, True)):
        bm = bmesh.new()
        ret = bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.0, radius2=r, depth=1.0)
        bmesh.ops.translate(bm, verts=ret["verts"], vec=(0, 0, -0.5))
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.5],
                                  cuts=6)
        fo = mesh_obj("FlameCore" if inner else "Flame", bm, [mat_])
        fo.parent = noz
        fo.visible_shadow = False
        flames.append((fo, inner))
glow = bpy.data.objects.new("ThrustLight", bpy.data.lights.new("ThrustLight", "POINT"))
sc.collection.objects.link(glow); glow.parent = jet; glow.location = (0, 0, -0.6)
glow.data.color = (1.0, 0.55, 0.2); glow.data.shadow_soft_size = 0.15

for f in range(1, END + 1):
    on = f >= IGNITE
    if f in (1, IGNITE - 1, IGNITE):
        for fo, inner in flames:
            fo.hide_render = not on; fo.hide_viewport = not on
            fo.keyframe_insert("hide_render", frame=f); fo.keyframe_insert("hide_viewport", frame=f)
    if not on:
        if f == 1 or f == IGNITE - 1:
            glow.data.energy = 0; glow.data.keyframe_insert("energy", frame=f)
        continue
    sputter = f < LIFT
    power = (0.35 + 0.4 * rnd.random() * (1 if (f // 3) % 2 else 0.3)) if sputter else (0.95 + 0.25 * rnd.random())
    if LIFT - 6 <= f < LIFT:
        power = 0.8 + 0.2 * rnd.random()
    for fo, inner in flames:
        L = power * (0.55 if inner else 1.05)
        w = 0.9 + 0.2 * rnd.random()
        fo.scale = (w, w, L)
        fo.keyframe_insert("scale", frame=f)
    glow.data.energy = 900 * power
    glow.data.keyframe_insert("energy", frame=f)

# ---------- 6. the stop, crouch and flight ----------
pb = RIG.pose.bones
for bn in pb:
    bn.rotation_mode = "XYZ"


def pose(frame, d):
    for bn in pb:
        bn.rotation_euler = d.get(bn.name, (0, 0, 0))
        bn.keyframe_insert("rotation_euler", frame=frame)


def mirror(d):
    out = dict(d)
    for k, v in list(d.items()):
        if k.endswith(".L"):
            out[k[:-2] + ".R"] = (v[0], -v[1], -v[2])
    return out


sc.frame_set(WALK)
y_end = RIG.location.y
v_walk = (path[-1].y - path[-6].y) / 5 * FPS / FPS          # meters per frame
stand = mirror({"forearm.L": (-0.1, 0, 0), "upperarm.L": (0.02, 0, -0.07)})
crouch = mirror({"thigh.L": (-0.55, 0, 0), "shin.L": (1.05, 0, 0), "foot.L": (-0.5, 0, 0),
                 "upperarm.L": (0.65, 0, -0.1), "forearm.L": (-0.35, 0, 0), "chest": (0.18, 0, 0), "head": (-0.15, 0, 0)})
push = mirror({"thigh.L": (0.05, 0, 0), "shin.L": (0.08, 0, 0), "foot.L": (0.45, 0, 0),
               "upperarm.L": (0.45, 0, -0.15), "forearm.L": (-0.2, 0, 0)})
pose(WALK + 10, stand)
pose(LIFT - 7, stand)
pose(LIFT - 1, crouch)
pose(LIFT + 4, push)

# speeds after lift-off (meters per second)
def vz(t): return 4.4 * smooth(t / 1.1) if t < 3 else lerp(4.4, 0.7, smooth((t - 3) / 2.2))
def vy(t): return 3.6 * smooth((t - 0.9) / 2.3)


pos = Vector((RIG.location.x, y_end, 0.03))
zcur = 0.03 - 0.11
track = {}
for f in range(WALK + 1, END + 1):
    k = f - WALK
    tilt = 0.0
    if k <= 10:                                               # last slowing step
        pos.y += v_walk * (1 - k / 10)
        pos.z = 0.03
    elif f < LIFT:                                            # crouch
        pos.z = 0.03 - 0.11 * smooth((f - (LIFT - 7)) / 6)
    else:                                                     # blast off
        t = (f - LIFT) / FPS
        pos.y += vy(t) / FPS
        zcur += vz(t) / FPS
        pos.z = zcur
        pos.x = 0.35 * math.sin(t * 1.3) * smooth(t / 2)
        tilt = min(math.radians(48), 0.7 * math.atan2(vy(t), max(vz(t), 0.05)))
    RIG.location = pos
    RIG.rotation_euler = (tilt, 0.0, math.pi)
    RIG.keyframe_insert("location", frame=f)
    RIG.keyframe_insert("rotation_euler", frame=f)
    track[f] = (pos.copy(), tilt)
    if f >= LIFT + 12 and (f - LIFT) % 6 == 0:                # flying pose with a little dangle
        s = math.sin(f * 0.21)
        pose(f, {"thigh.L": (0.1 + 0.07 * s, 0, 0), "thigh.R": (0.1 - 0.07 * s, 0, 0),
                 "shin.L": (0.38 - 0.1 * s, 0, 0), "shin.R": (0.38 + 0.1 * s, 0, 0),
                 "foot.L": (0.5, 0, 0), "foot.R": (0.5, 0, 0),
                 "upperarm.L": (0.42, 0, -0.32), "upperarm.R": (0.42, 0, 0.32),
                 "forearm.L": (-0.25, 0, 0), "forearm.R": (-0.25, 0, 0),
                 "chest": (0.05, 0, 0.03 * s), "head": (-0.7 * tilt, 0, 0)})
for f in range(1, WALK + 1):
    track[f] = (path[f - 1], 0.0)

# ---------- 7. smoke: dust ring at lift-off and a trail ----------
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


lift_spot = track[LIFT][0].copy()
for i in range(30):
    a = i / 30 * 2 * math.pi + rnd.uniform(-0.1, 0.1)
    d = Vector((math.cos(a), math.sin(a), 0))
    puff(LIFT - 4 + rnd.randint(0, 8), 60, lift_spot + d * 0.4 + Vector((0, 0, 0.15)),
         d * rnd.uniform(3.5, 5.5), 0.2, rnd.uniform(0.7, 1.15), 0.42, (0.42, 0.38, 0.31), 0.25, 0.6)
for f in range(IGNITE, END - 4, 2):
    if f < LIFT and rnd.random() < 0.6:
        continue
    sc.frame_set(f)
    noz = nozzles[(f // 2) % 2]
    p0 = noz.matrix_world.translation.copy()
    down = (noz.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    spread = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3))) * 0.5
    puff(f, 36, p0 + down * 0.5, (down * 3.0 + spread), 0.07, rnd.uniform(0.4, 0.65), 0.38, (0.6, 0.58, 0.55), 0.3, 0.5)

# ---------- 8. sheep: graze, then watch him fly ----------
def key_head(pv, f, pitch, yaw):
    pv.rotation_euler = (math.radians(pitch), 0, math.radians(yaw))
    pv.keyframe_insert("rotation_euler", frame=int(f))


for root, pv in sheep:
    pivot_w = root.matrix_world @ Vector((0, 0.5, 0.74))
    dist = (pivot_w.xy - lift_spot.xy).length
    react = IGNITE + 6 + min(30, int(dist / 12 * FPS))
    f = 1
    grazing = rnd.random() < 0.75
    yaw = rnd.uniform(-20, 20)
    while f < react:
        if grazing:
            dur = rnd.randint(50, 150)
            for k in range(0, dur, 9):
                if f + k >= react: break
                key_head(pv, f + k, -78 + rnd.uniform(-6, 6), yaw + rnd.uniform(-4, 4))
        else:
            dur = rnd.randint(30, 70)
            yaw = rnd.uniform(-35, 35)
            key_head(pv, f + 6, rnd.uniform(-10, 4), yaw)
            if f + dur - 6 < react:
                key_head(pv, f + dur - 6, rnd.uniform(-10, 4), yaw)
        f += dur
        grazing = not grazing if rnd.random() < 0.8 else grazing
    for f in range(react, END + 1, 6):
        p = track[min(f, END)][0] + Vector((0, 0, 1.0))
        dvec = p - pivot_w
        heading = root.rotation_euler.z
        phi = math.atan2(-dvec.x, dvec.y)
        rel = (phi - heading + math.pi) % (2 * math.pi) - math.pi
        rel = max(-1.4, min(1.4, rel))
        elev = math.atan2(dvec.z, dvec.xy.length) - math.radians(10)
        key_head(pv, f if f > react else react + 5, max(-12, min(48, math.degrees(elev))), math.degrees(rel))

# ---------- 9. camera for the ending ----------
w = g["w"]
cam.rotation_mode = "XYZ"
prev = cam.rotation_euler.copy()
sc.frame_set(WALK)
a = math.atan2(cam.location.y - path[-1].y, cam.location.x - path[-1].x)
radius = (cam.location.xy - path[-1].xy).length
height = cam.location.z
ground_cam = None
for f in range(WALK + 1, END + 1):
    k = f - WALK
    him, tilt = track[f]
    a += w * (1 - smooth(k / 24))
    if f < LIFT:
        s = smooth(k / 20)
        r_ = lerp(radius, 4.3, s); h_ = lerp(height, 0.5, s)
        pos = Vector((him.x + r_ * math.cos(a), him.y + r_ * math.sin(a), h_))
        look = him + Vector((0, 0, lerp(0.9, 1.1, s)))
        ground_cam = pos.copy()
    else:
        s = smooth((f - (LIFT + 14)) / 85)
        chase = him + Vector((2.3, 4.8, 1.7))
        pos = ground_cam.lerp(chase, s)
        look = (him + Vector((0, 0, 0.9))).lerp(him + Vector((0, 0, -1.4)), s)
    cam.location = pos
    q = (look - pos).to_track_quat("-Z", "Y")
    e = q.to_euler("XYZ", prev); prev = e
    cam.rotation_euler = e
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    target.location = him + Vector((0, 0, 1.0))
    target.keyframe_insert("location", frame=f)

# ---------- 10. render settings ----------
sc.frame_start, sc.frame_end = 1, END
sc.render.engine = "CYCLES"
sc.cycles.samples = int(args.get("samples", "64"))
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 4
sc.cycles.transparent_max_bounces = 24
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.view_settings.view_transform = args.get("view", "Standard")
try:
    sc.view_settings.look = args.get("look", "AgX - Medium High Contrast") if sc.view_settings.view_transform == "AgX" else "None"
except TypeError:
    pass
sc.view_settings.exposure = float(args.get("exposure", "-0.5"))
bg = sc.world.node_tree.nodes["Background"]
bg.inputs["Strength"].default_value = float(args.get("sky", "0.12"))
bpy.data.objects["Sun"].data.energy = float(args.get("sun", "2.6"))
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(Z, "jetpack_frames", "f_")
sc.render.use_overwrite = False
sc.render.use_placeholder = True
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(Z, "gabriel_jetpack_video.blend"))
print(f"[jetpack] scene ready: {END} frames, {len(sheep)} sheep")
