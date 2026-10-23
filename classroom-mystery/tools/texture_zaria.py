"""
Classroom Mystery - better textures for Zaria (Character 1, black hoodie)
========================================================================
Run this in Blender on the file that has the "Character_StudentA"
collection (character_1_black_hoodie.blend). It:

  - gives each piece of clothing a real cloth texture with surface bumps
    (normal maps): fleece hoodie, rib-knit cuffs and hem, woodland camo
    tank top, heather sweatpants, strand hair, soft skin, pebbled white
    leather sneakers with grooved soles, metal zipper teeth
  - replaces the round "camo spots" with a proper camo print
  - lays the textures out at their real size (texture coordinates in
    meters), so the fabric looks the same size everywhere
  - packs the images into the .blend, so the file works on its own

TEXTURE_DIR: the folder with the zaria_*.jpg files
(classroom-mystery/assets/textures/characters in the game folder).
Leave it empty to use a "textures/zaria" folder next to the .blend.
"""

import os
import bpy
import bmesh
from mathutils import Vector

TEXTURE_DIR = ""
COLLECTION = "Character_StudentA"
PREFIX = "STA_"

# material -> (texture, meters covered by one copy, roughness, bump strength)
LOOK = {
    "Hoodie": ("zaria_fleece", 0.18, 0.95, 0.6),
    "Rib": ("zaria_rib", 0.10, 0.9, 0.8),
    "Camo1": ("zaria_camo", 0.35, 0.9, 0.4),
    "Pants": ("zaria_jogger", 0.20, 0.95, 0.5),
    "Hair": ("zaria_hair", 0.15, 0.75, 0.35),
    "Skin": ("zaria_skin", 0.20, 0.55, 0.0),
    "Shoe": ("zaria_leather", 0.08, 0.45, 0.5),
    "Sole": ("zaria_sole", 0.06, 0.8, 0.8),
    "Zip": ("zaria_zip", 0.02, 0.35, 0.6),
}


def tex_dir():
    if TEXTURE_DIR:
        return TEXTURE_DIR
    return os.path.join(os.path.dirname(bpy.data.filepath) or os.getcwd(), "textures", "zaria")


def image(name, non_color=False):
    path = os.path.join(tex_dir(), name + ".jpg")
    if not os.path.exists(path):
        return None
    img = bpy.data.images.load(path, check_existing=True)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def setup_material(mat, tex, rough, bump):
    col = image(tex)
    if col is None:
        print("[zaria] missing texture:", tex)
        return False
    nrm = image(tex + "_n", non_color=True) if bump > 0 else None
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (500, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Roughness"].default_value = rough
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.location = (-300, 150)
    t.image = col
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if nrm is not None:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.location = (-300, -200)
        tn.image = nrm
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.location = (0, -200)
        nm.inputs["Strength"].default_value = bump
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return True


def material(name):
    return bpy.data.materials.get(PREFIX + name)


col = bpy.data.collections.get(COLLECTION)
if col is None:
    raise SystemExit(f"[zaria] No '{COLLECTION}' collection in this file. Open character_1_black_hoodie.blend first.")

meshes = [o for o in col.all_objects if o.type == "MESH"]
top_z = max((o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices)
S = top_z / 1.782                       # this character's size compared with the 1.78 m base

# New rib-knit material for the cuffs and the hoodie hem
rib = material("Rib")
if rib is None:
    rib = bpy.data.materials.new(PREFIX + "Rib")
    rib.diffuse_color = (0.012, 0.013, 0.015, 1)

hoodie, camo2, camo3 = material("Hoodie"), material("Camo2"), material("Camo3")

for ob in meshes:
    me = ob.data
    names = [m.name if m else "" for m in me.materials]
    if rib.name not in names and hoodie and hoodie.name in names:
        me.materials.append(rib)
        names.append(rib.name)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    # 1. remove the old round camo spots (a print texture replaces them)
    spots = [f for f in bm.faces if names[f.material_index] in (camo2 and camo2.name, camo3 and camo3.name)]
    if spots:
        bmesh.ops.delete(bm, geom=spots, context="FACES")
    # 2. rib knit at the hoodie hem and the sleeve cuffs
    if hoodie and hoodie.name in names:
        hi = names.index(hoodie.name)
        ri = names.index(rib.name)
        limit = (0.92 if ob.name.startswith("Arm_") else 0.888) * S
        for f in bm.faces:
            if f.material_index == hi and (ob.matrix_world @ f.calc_center_median()).z < limit:
                f.material_index = ri
    # 3. texture coordinates in meters: project each face from its main direction
    uv = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
    tile_of = []
    for nm in names:
        key = nm[len(PREFIX):] if nm.startswith(PREFIX) else nm
        tile_of.append(LOOK.get(key, (None, 0.2))[1])
    mw = ob.matrix_world
    for f in bm.faces:
        n = (mw.to_3x3() @ f.normal).normalized()
        ax = max(range(3), key=lambda i: abs(n[i]))
        t = tile_of[f.material_index] if f.material_index < len(tile_of) else 0.2
        for loop in f.loops:
            p = mw @ loop.vert.co
            if ax == 0:
                u, v = (p.y if n.x > 0 else -p.y), p.z
            elif ax == 1:
                u, v = (-p.x if n.y > 0 else p.x), p.z
            else:
                u, v = p.x, (p.y if n.z > 0 else -p.y)
            loop[uv].uv = (u / t, v / t)
    bm.to_mesh(me)
    bm.free()
    me.update()

done = []
for key, (tex, tile, rough, bump) in LOOK.items():
    m = material(key) if key != "Rib" else rib
    if m and setup_material(m, tex, rough, bump):
        done.append(key)

for img in bpy.data.images:
    if img.name.startswith("zaria_") and not img.packed_file:
        img.pack()

tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
print(f"[zaria] textured: {', '.join(done)}; about {tris:,} triangles")
