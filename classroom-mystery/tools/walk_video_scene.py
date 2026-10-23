"""
Classroom Mystery - "bullet time" walking video
===============================================
Builds a character (gabriel_character.py), gives them a skeleton and a
walk (rig_walk.py), puts them on a sidewalk in a sunny schoolyard, and
animates the camera: it swoops down from high above, then circles the
walking character three times at normal speed.

Run with Blender in the background, for example:
  blender -b --factory-startup --python walk_video_scene.py -- \
      dir=/path/to/folder engine=EEVEE res=1080 samples=32
"dir" must contain gabriel_character.py and rig_walk.py. The scene is
saved there as gabriel_walk_video.blend; render it with render_frames.
"""
import bpy, math, os, sys, random
from mathutils import Vector, Euler

args = dict(a.split("=", 1) for a in sys.argv[sys.argv.index("--") + 1:]) if "--" in sys.argv else {}
Z = args.get("dir", os.getcwd())
ENGINE = args.get("engine", "CYCLES")
RES = int(args.get("res", "720"))
FPS = 24
SWOOP = 3.0          # seconds
ORBITS = 3
ORBIT_T = 4.2        # seconds per full turn (normal speed)
FRAMES = int(round((SWOOP + ORBITS * ORBIT_T) * FPS))
random.seed(4)

bpy.ops.wm.read_homefile(use_empty=True)
sc = bpy.context.scene
exec(compile(open(os.path.join(Z, "gabriel_character.py")).read(), "gabriel_character.py", "exec"), {"__name__": "__main__"})
rig_src = open(os.path.join(Z, "rig_walk.py")).read()
rig_src = rig_src.replace("WALK_FRAMES = 374", f"WALK_FRAMES = {FRAMES}").replace("Z_OFFSET = 0.0", "Z_OFFSET = 0.03")
exec(compile(rig_src, "rig_walk.py", "exec"), {"__name__": "__main__"})
RIG = bpy.data.objects["Rig"]


def mat_nodes(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def add_mesh(op, **kw):
    op(**kw)
    return bpy.context.active_object


# ---------- ground: grass with a concrete pad and a sidewalk ----------
m, n, l, b = mat_nodes("Grass")
noise = n.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 40; noise.inputs["Detail"].default_value = 8
big = n.new("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 1.5
ramp = n.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.05, 0.12, 0.025, 1); ramp.color_ramp.elements[1].color = (0.16, 0.3, 0.06, 1)
mix = n.new("ShaderNodeMath"); mix.operation = "MULTIPLY"
l.new(noise.outputs["Fac"], mix.inputs[0]); l.new(big.outputs["Fac"], mix.inputs[1])
l.new(mix.outputs[0], ramp.inputs["Fac"]); l.new(ramp.outputs["Color"], b.inputs["Base Color"])
bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6
l.new(noise.outputs["Fac"], bump.inputs["Height"]); l.new(bump.outputs["Normal"], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.95
ground = add_mesh(bpy.ops.mesh.primitive_plane_add, size=400, location=(0, 0, -0.002))
ground.data.materials.append(m)

m, n, l, b = mat_nodes("Concrete")
cn = n.new("ShaderNodeTexNoise"); cn.inputs["Scale"].default_value = 60; cn.inputs["Detail"].default_value = 10
cr = n.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].color = (0.2, 0.195, 0.185, 1); cr.color_ramp.elements[1].color = (0.32, 0.31, 0.29, 1)
l.new(cn.outputs["Fac"], cr.inputs["Fac"]); l.new(cr.outputs["Color"], b.inputs["Base Color"])
cb = n.new("ShaderNodeBump"); cb.inputs["Strength"].default_value = 0.25
l.new(cn.outputs["Fac"], cb.inputs["Height"]); l.new(cb.outputs["Normal"], b.inputs["Normal"])
b.inputs["Roughness"].default_value = 0.85
concrete = m
pad = add_mesh(bpy.ops.mesh.primitive_cylinder_add, radius=3.2, depth=0.06, vertices=64, location=(0, 0, 0.0))
pad.data.materials.append(concrete)
walk = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 20.1, 0.0))
walk.scale = (2.0, 34, 0.058); walk.data.materials.append(concrete)
for k in range(1, 18):                         # sidewalk joints
    j = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 3.1 + k * 2.0, 0.03))
    j.scale = (2.0, 0.02, 0.002); j.data.materials.append(bpy.data.materials['Trim'] if 'Trim' in bpy.data.materials else concrete)


# ---------- school building in the background ----------
m, n, l, b = mat_nodes("Brick")
br = n.new("ShaderNodeTexBrick")
br.inputs["Color1"].default_value = (0.36, 0.12, 0.07, 1); br.inputs["Color2"].default_value = (0.45, 0.17, 0.1, 1)
br.inputs["Mortar"].default_value = (0.45, 0.42, 0.38, 1)
geo = n.new("ShaderNodeNewGeometry")
l.new(geo.outputs["Position"], br.inputs["Vector"]); br.inputs["Scale"].default_value = 2.2; l.new(br.outputs["Color"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.9
brick = m
school = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 42, 5))
school.scale = (46, 10, 10); school.data.materials.append(brick)
m, n, l, b = mat_nodes("Window")
b.inputs["Base Color"].default_value = (0.08, 0.12, 0.18, 1); b.inputs["Roughness"].default_value = 0.08
b.inputs["Metallic"].default_value = 0.6
win = m
for row in (2.6, 6.4):
    for k in range(-10, 11):
        if abs(k) <= 1 and row < 4:
            continue
        w = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(k * 2.1, 36.95, row))
        w.scale = (1.4, 0.1, 1.8); w.data.materials.append(win)
door = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 36.95, 1.4))
door.scale = (3.6, 0.12, 2.8); door.data.materials.append(win)
m, n, l, b = mat_nodes("Trim")
b.inputs["Base Color"].default_value = (0.8, 0.8, 0.78, 1)
for z in (0.25, 9.9):
    t = add_mesh(bpy.ops.mesh.primitive_cube_add, size=1, location=(0, 36.9, z))
    t.scale = (46, 0.2, 0.5); t.data.materials.append(m)
pole = add_mesh(bpy.ops.mesh.primitive_cylinder_add, radius=0.06, depth=12, location=(6, 30, 6))
pole.data.materials.append(m)
m2, n, l, b = mat_nodes("Flag")
b.inputs["Base Color"].default_value = (0.1, 0.2, 0.55, 1)
flag = add_mesh(bpy.ops.mesh.primitive_plane_add, size=1, location=(6.9, 30, 11.2), rotation=(math.radians(90), 0, 0))
flag.scale = (1.6, 1.0, 1); flag.data.materials.append(m2)

# ---------- trees ----------
m, n, l, b = mat_nodes("Bark")
b.inputs["Base Color"].default_value = (0.16, 0.1, 0.06, 1); b.inputs["Roughness"].default_value = 0.95
bark = m
m, n, l, b = mat_nodes("Leaves")
ln = n.new("ShaderNodeTexNoise"); ln.inputs["Scale"].default_value = 6
lr = n.new("ShaderNodeValToRGB")
lr.color_ramp.elements[0].color = (0.04, 0.12, 0.03, 1); lr.color_ramp.elements[1].color = (0.18, 0.36, 0.08, 1)
l.new(ln.outputs["Fac"], lr.inputs["Fac"]); l.new(lr.outputs["Color"], b.inputs["Base Color"])
b.inputs["Roughness"].default_value = 0.8
leaves = m
for k in range(16):
    a = k / 16 * 2 * math.pi + random.uniform(-0.15, 0.15)
    r = random.uniform(14, 24)
    x, y = r * math.cos(a), r * math.sin(a)
    if y > 25 or (abs(x) < 7.5 and -6 < y < 30):   # keep the building and the walking path clear
        continue
    h = random.uniform(3.5, 6)
    trunk = add_mesh(bpy.ops.mesh.primitive_cylinder_add, radius=0.18, depth=h, location=(x, y, h / 2))
    trunk.data.materials.append(bark)
    for c in range(3):
        crown = add_mesh(bpy.ops.mesh.primitive_ico_sphere_add, subdivisions=3, radius=random.uniform(1.4, 2.2),
                         location=(x + random.uniform(-0.8, 0.8), y + random.uniform(-0.8, 0.8), h + random.uniform(-0.3, 1.2)))
        crown.data.materials.append(leaves)
        for poly in crown.data.polygons: poly.use_smooth = True
        d = crown.modifiers.new("lumpy", "DISPLACE")
        tex = bpy.data.textures.new("lumps", "CLOUDS"); tex.noise_scale = 0.6; d.texture = tex; d.strength = 0.6

# ---------- sky and sun ----------
world = bpy.data.worlds.new("Sky"); sc.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn["Background"]
sky = wn.new("ShaderNodeTexSky")
try:
    sky.sky_type = "NISHITA"
except TypeError:
    pass
for attr, val in (("sun_elevation", math.radians(38)), ("sun_rotation", math.radians(215)), ("altitude", 100), ("air_density", 1.0), ("dust_density", 1.5)):
    if hasattr(sky, attr):
        setattr(sky, attr, val)
wl.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = float(args.get("sky", "0.25"))
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = float(args.get('sun', '3.0')); sun.data.angle = math.radians(1.5); sun.data.color = (1.0, 0.96, 0.9)
sun.rotation_euler = Euler((math.radians(52), 0, math.radians(215 - 90)))
sc.collection.objects.link(sun)

# ---------- camera: swoop down, then 3 orbits at normal speed ----------
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 35
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0
target = bpy.data.objects.new("Look", None); target.location = (0, 0, 1.0); sc.collection.objects.link(target)
cam.data.dof.focus_object = target
w = 2 * math.pi / (ORBIT_T * FPS)          # same turning speed the whole time


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


start_angle = math.radians(-120)
path = []
for f in range(1, FRAMES + 1):
    sc.frame_set(f)
    path.append(RIG.matrix_world.translation.copy())
for f in range(1, FRAMES + 1):
    t = f - 1
    s = smooth(t / (SWOOP * FPS))
    radius = 14 * (1 - s) + 3.4 * s
    height = 20 * (1 - s) + (1.2 + 0.3 * math.sin(t / (ORBIT_T * FPS) * 2 * math.pi * 1.5)) * s
    look_z = 0.5 * (1 - s) + (0.86 + 0.04 * math.sin(t / 40)) * s
    a = start_angle + w * t + (1 - s) * math.radians(40)
    cx, cy = path[t].x, path[t].y
    cam.location = (cx + radius * math.cos(a), cy + radius * math.sin(a), height)
    d = Vector((cx, cy, look_z)) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    target.location = (cx, cy, look_z); target.keyframe_insert("location", frame=f)

sc.frame_start, sc.frame_end = 1, FRAMES
sc.render.fps = FPS
sc.render.resolution_x, sc.render.resolution_y = RES * 16 // 9, RES
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = args.get("view", "Standard")
sc.view_settings.look = "None"
sc.view_settings.exposure = float(args.get("exposure", "0"))
sc.render.use_motion_blur = args.get('blur', '1') == '1'
sc.render.motion_blur_shutter = 0.35
sc.render.engine = "CYCLES" if ENGINE == "CYCLES" else "BLENDER_EEVEE"
if ENGINE == "CYCLES":
    sc.cycles.samples = int(args.get("samples", "24"))
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.use_adaptive_sampling = True
else:
    sc.eevee.taa_render_samples = int(args.get("samples", "32"))
    for attr, val in (("use_shadows", True), ("use_raytracing", args.get("ray", "0") == "1")):
        if hasattr(sc.eevee, attr):
            setattr(sc.eevee, attr, val)
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(Z, "walk_frames", "f_")
sc.render.use_overwrite = False
sc.render.use_placeholder = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(Z, "gabriel_walk_video.blend"))
print(f"[video] scene ready: {FRAMES} frames, engine {sc.render.engine}")
