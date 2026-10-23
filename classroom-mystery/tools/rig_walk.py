"""
Classroom Mystery - add a skeleton and a walk to a character
============================================================
Run in Blender after a character script (for example gabriel_character.py)
has built its "Character_..." collection. It:

  1. adds a simple skeleton ("Rig"): hips, spine, chest, neck, head,
     upper legs, lower legs, feet, upper arms, forearms, hands
  2. attaches each body piece to its bones, blending around the knees,
     elbows, waist and neck so they bend smoothly
  3. makes a walking action ("Walk") and a standing action ("Idle"):
     legs and knees, opposite arm swing, hip bob and sway, a little
     shoulder twist. The walk moves the character forward at a speed that
     matches the steps, so the feet do not slide much.

Settings: WALK_FRAMES (how long to walk), STEP_TIME (seconds per two steps),
FACE_Y (+1 walks toward +Y, -1 toward -Y), START (where the walk starts).
"""

import math
import bpy
from mathutils import Vector

FPS = 24
WALK_FRAMES = 374
STEP_TIME = 1.1            # seconds for one full cycle (left step + right step)
SWING = math.radians(22)   # how far the legs swing forward and back
FACE_Y = 1
START = (0.0, -1.0)
Z_OFFSET = 0.0         # raise the walk, e.g. onto a sidewalk
COLLECTION_PREFIX = "Character_"

col = next(c for c in bpy.data.collections if c.name.startswith(COLLECTION_PREFIX))
meshes = [o for o in col.all_objects if o.type == "MESH"]
top = max((o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices)
S = top / 1.80             # body numbers below are for the 1.78 m base (cap top ~1.80)

# ---------- 1. skeleton ----------
arm_data = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm_data)
col.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.context.view_layer.objects:
    o.select_set(False)
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, connect=False):
    b = eb.new(name)
    b.head = Vector(head) * S
    b.tail = Vector(tail) * S
    b.roll = 0
    if parent:
        b.parent = eb[parent]
        b.use_connect = connect
    return b


bone("root", (0, 0, 0), (0, 0.25, 0))
bone("hips", (0, 0, 0.92), (0, 0, 1.03), "root")
bone("spine", (0, 0, 1.03), (0, 0, 1.25), "hips", True)
bone("chest", (0, 0, 1.25), (0, 0, 1.45), "spine", True)
bone("neck", (0, 0.012, 1.47), (0, 0.012, 1.58), "chest")
bone("head", (0, 0.012, 1.58), (0, 0.012, 1.8), "neck", True)
for side, sfx in ((1, "L"), (-1, "R")):
    bone(f"thigh.{sfx}", (side * 0.09, 0, 0.9), (side * 0.103, 0, 0.5), "hips")
    bone(f"shin.{sfx}", (side * 0.103, 0, 0.5), (side * 0.104, 0.012, 0.11), f"thigh.{sfx}", True)
    bone(f"foot.{sfx}", (side * 0.104, 0.012, 0.11), (side * 0.105, -0.13, 0.03), f"shin.{sfx}", True)
    bone(f"upperarm.{sfx}", (side * 0.19, 0.008, 1.42), (side * 0.215, 0.005, 1.17), "chest")
    bone(f"forearm.{sfx}", (side * 0.215, 0.005, 1.17), (side * 0.233, -0.01, 0.895), f"upperarm.{sfx}", True)
    bone(f"hand.{sfx}", (side * 0.233, -0.01, 0.895), (side * 0.233, -0.01, 0.74), f"forearm.{sfx}", True)
for b in eb:
    b.roll = 0
bpy.ops.object.mode_set(mode="OBJECT")


# ---------- 2. attach the body pieces ----------
def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def weights_for(name, p):
    """Bone weights for a vertex at rest position p (meters, 1.78 m scale)."""
    x, y, z = p.x / S, p.y / S, p.z / S
    sfx = "L" if x > 0 else "R"
    if name.startswith("Shoe"):
        return {f"foot.{sfx}": 1}
    if name.startswith("Leg"):
        k = smooth(0.44, 0.58, z)                 # knee blend
        w = {f"thigh.{sfx}": k, f"shin.{sfx}": 1 - k}
        if z < 0.16:
            w = {f"shin.{sfx}": 1 - 0.5 * smooth(0.16, 0.1, z), f"foot.{sfx}": 0.5 * smooth(0.16, 0.1, z)}
        if z > 0.82:                              # top of the leg follows the hips a little
            h = smooth(0.82, 0.92, z) * 0.6
            w = {f"thigh.{sfx}": 1 - h, "hips": h}
        return w
    if name.startswith("Arm") or name.startswith("Sleeve"):
        if z < 0.9:                               # hand and fingers
            return {f"hand.{sfx}": 1}
        e = smooth(1.1, 1.24, z)                  # elbow blend
        w = {f"upperarm.{sfx}": e, f"forearm.{sfx}": 1 - e}
        if z > 1.36:
            c = smooth(1.36, 1.45, z) * 0.5       # shoulder top shares with the chest
            w = {f"upperarm.{sfx}": 1 - c, "chest": c}
        if z < 0.93:
            w = {f"forearm.{sfx}": 0.6, f"hand.{sfx}": 0.4}
        return w
    if name.startswith("Torso") or name.startswith("Shirt") or name.startswith("Top"):
        if z < 1.0:
            return {"hips": 1 - smooth(0.95, 1.05, z), "spine": smooth(0.95, 1.05, z)}
        if z < 1.3:
            c = smooth(1.2, 1.32, z)
            return {"spine": 1 - c, "chest": c}
        if z > 1.46:
            n = smooth(1.46, 1.52, z)
            return {"chest": 1 - n, "neck": n}
        return {"chest": 1}
    # head pieces: head, face, stubble/beard, hair, cap
    if z < 1.57:
        n = smooth(1.5, 1.57, z)
        return {"chest": 1 - n, "neck": n} if z < 1.5 else {"neck": 1 - n * 0.3, "head": n * 0.3}
    return {"head": 1}


for ob in meshes:
    for vg in list(ob.vertex_groups):
        ob.vertex_groups.remove(vg)
    groups = {}
    for v in ob.data.vertices:
        p = ob.matrix_world @ v.co
        for bname, w in weights_for(ob.name, p).items():
            if w <= 0.001:
                continue
            g = groups.get(bname) or ob.vertex_groups.new(name=bname)
            groups[bname] = g
            g.add([v.index], w, "REPLACE")
    for m in [m for m in ob.modifiers if m.type == "ARMATURE"]:
        ob.modifiers.remove(m)
    mod = ob.modifiers.new("Rig", "ARMATURE")
    mod.object = rig
    ob.parent = rig

# ---------- 3. walk + idle actions ----------
L = 0.79 * S                                    # hip to ankle
T = STEP_TIME * FPS
SPEED = 4 * L * math.sin(SWING) / STEP_TIME     # meters per second that matches the steps
rig.rotation_mode = "XYZ"
rig.rotation_euler = (0, 0, 0 if FACE_Y < 0 else math.pi)
pb = rig.pose.bones
for b in pb:
    b.rotation_mode = "XYZ"


def key_pose(frame, phase, walking=True):
    p = 2 * math.pi * phase
    if walking:
        for sfx, off in (("L", 0.0), ("R", math.pi)):
            a = SWING * math.sin(p + off)                     # + = leg forward
            knee = math.radians(42) * max(0.0, math.cos(p + off - 0.35)) ** 1.5 + math.radians(6)
            pb[f"thigh.{sfx}"].rotation_euler = (-a, 0, 0)
            pb[f"shin.{sfx}"].rotation_euler = (knee, 0, 0)
            toe = math.radians(12) * max(0.0, -math.cos(p + off)) * max(0.0, -math.sin(p + off))
            pb[f"foot.{sfx}"].rotation_euler = (a - knee + toe, 0, 0)
            pb[f"upperarm.{sfx}"].rotation_euler = (0.65 * a, 0, math.radians(-4 if sfx == "L" else 4))
            pb[f"forearm.{sfx}"].rotation_euler = (-math.radians(14) - 0.3 * max(0.0, a), 0, 0)
        pb["hips"].rotation_euler = (0, math.radians(3) * math.sin(2 * p), math.radians(5) * math.sin(p))
        pb["chest"].rotation_euler = (math.radians(-3), 0, math.radians(-6) * math.sin(p))
        pb["head"].rotation_euler = (math.radians(2), 0, math.radians(3) * math.sin(p))
        drop = L * (1 - math.cos(SWING * math.sin(p)))
        rig.location = (START[0], START[1] + FACE_Y * SPEED * frame / FPS, Z_OFFSET - drop)
    else:                                                     # idle: breathing and a small sway
        for sfx in ("L", "R"):
            pb[f"thigh.{sfx}"].rotation_euler = (0, 0, 0)
            pb[f"shin.{sfx}"].rotation_euler = (0, 0, 0)
            pb[f"foot.{sfx}"].rotation_euler = (0, 0, 0)
            pb[f"upperarm.{sfx}"].rotation_euler = (math.radians(2) * math.sin(p), 0, 0)
            pb[f"forearm.{sfx}"].rotation_euler = (-math.radians(6), 0, 0)
        pb["hips"].rotation_euler = (0, math.radians(1.2) * math.sin(p), 0)
        pb["chest"].rotation_euler = (math.radians(-1.5) * (1 + math.sin(2 * p)) / 2, 0, 0)
        pb["head"].rotation_euler = (0, 0, math.radians(4) * math.sin(p * 0.5))
    for b in pb:
        b.keyframe_insert("rotation_euler", frame=frame)
    if walking:
        rig.keyframe_insert("location", frame=frame)


rig.animation_data_create()
idle = bpy.data.actions.new("Idle")
rig.animation_data.action = idle
for f in range(1, 4 * FPS + 2):                               # 4-second loop
    key_pose(f, (f - 1) / (4 * FPS), walking=False)
idle.use_fake_user = True

walk = bpy.data.actions.new("Walk")
rig.animation_data.action = walk
for f in range(1, WALK_FRAMES + 1):
    key_pose(f, (f - 1) / T, walking=True)
walk.use_fake_user = True
for fc in getattr(walk, "fcurves", []):
    for k in fc.keyframe_points:
        k.interpolation = "LINEAR"

print(f"[rig] skeleton with {len(pb)} bones; walk speed {SPEED:.2f} m/s; "
      f"walks {SPEED * WALK_FRAMES / FPS:.1f} m in {WALK_FRAMES / FPS:.1f} s")
