"""Build a smooth, cute 3D Fuzzboi (code #456800: Body B, red, crown, taco, blush).
Run: python3 build_fuzzboi.py [render]
"""
import sys, math, random
import bpy, bmesh
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
random.seed(7)

# ---------- helpers ----------
def hexcol(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)

def mat(name, hexc, rough=0.45, sheen=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hexcol(hexc)
    b.inputs["Roughness"].default_value = rough
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
        b.inputs["Sheen Roughness"].default_value = 0.4
    if emit:
        b.inputs["Emission Color"].default_value = hexcol(hexc)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = hexcol(hexc)
    return m

def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True

def add_mod_subsurf(obj, lvl=2):
    m = obj.modifiers.new("Subsurf", "SUBSURF")
    m.levels = lvl
    m.render_levels = lvl
    return m

def apply_all(obj):
    bpy.context.view_layer.objects.active = obj
    for m in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)

def uvsphere(name, loc, scale, material, segs=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=rings, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    smooth(o)
    return o

def orient_to(obj, normal, up=Vector((0, 0, 1))):
    q = normal.to_track_quat('Z', 'Y')
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = q

# ---------- reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

M = {
    "body":    mat("Fuzz_Red",      "#FF3A1E", rough=0.6, sheen=0.8),
    "rim":     mat("Fuzz_PinkRim",  "#F20AC8", rough=0.5),
    "eye":     mat("Eye_Black",     "#050505", rough=0.08),
    "shine":   mat("Eye_Shine",     "#FFFFFF", rough=0.2, emit=0.6),
    "blush":   mat("Blush_Pink",    "#F8C3DA", rough=0.5),
    "crown":   mat("Crown_Yellow",  "#FFEF7A", rough=0.35),
    "gem":     mat("Crown_Gem",     "#E2C512", rough=0.15),
    "shell":   mat("Taco_Shell",    "#E8BC52", rough=0.55),
    "meat":    mat("Taco_Meat",     "#6B3E1C", rough=0.7),
    "lettuce": mat("Taco_Lettuce",  "#3FBF2E", rough=0.5),
    "cheese":  mat("Taco_Cheese",   "#F6DD4A", rough=0.4),
    "tomato":  mat("Taco_Tomato",   "#E3201F", rough=0.3),
}

root = bpy.data.objects.new("Fuzzboi_456800", None)
scene.collection.objects.link(root)

# ---------- body: soft spiky blob ----------
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0)
body = bpy.context.active_object
body.name = "Body"

spikes = []
for deg, h, ytilt in [(8, .55, -.1), (45, .42, .15), (128, .5, 0), (163, .58, -.15),
                      (198, .6, .1), (232, .45, -.1), (268, .55, .12), (303, .5, -.1), (338, .48, .1)]:
    a = math.radians(deg)
    spikes.append((Vector((math.cos(a), ytilt, math.sin(a))).normalized(), h * 1.35, 0.25))
for d in [(.5, 1, .4), (-.6, 1, -.3), (.1, 1, -.7), (-.3, 1, .6)]:   # a few on the back
    spikes.append((Vector(d).normalized(), .38, .32))

bm = bmesh.new()
bm.from_mesh(body.data)
for v in bm.verts:
    d = v.co.normalized()
    r = 1.0
    for sd, h, w in spikes:
        ang = d.angle(sd)
        r += h * math.exp(-(ang / w) ** 2)
    v.co = Vector((d.x * r, d.y * r * 0.72, d.z * r * 0.92))
bm.to_mesh(body.data)
bm.free()
smooth(body)
body.data.materials.append(M["body"])
# gentle extra smoothing pass so spike tips are rounded marshmallow points
sm = body.modifiers.new("Smooth", "SMOOTH")
sm.factor = 0.5
sm.iterations = 3
apply_all(body)
body.parent = root

# rim: inverted hull outline (shows as a pink border; backface-culled in Unity)
rim = body.copy()
rim.data = body.data.copy()
rim.name = "Body_Rim"
scene.collection.objects.link(rim)
bm = bmesh.new()
bm.from_mesh(rim.data)
bm.normal_update()
for v in bm.verts:
    v.co += v.normal * 0.075
bmesh.ops.reverse_faces(bm, faces=bm.faces)
bm.to_mesh(rim.data)
bm.free()
rim.data.materials.clear()
rim.data.materials.append(M["rim"])
rim.parent = root

# Cycles preview: hide the near side of the hull (Unity does this via backface culling)
nt = M["rim"].node_tree
bsdf = nt.nodes["Principled BSDF"]
out = nt.nodes["Material Output"]
geo = nt.nodes.new("ShaderNodeNewGeometry")
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
em = nt.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = hexcol("#F20AC8")
em.inputs[1].default_value = 1.0
nt.links.new(em.outputs[0], mix.inputs[1])
nt.links.new(tr.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])
M["rim"].use_backface_culling = True
rim.visible_shadow = False
rim.visible_diffuse = False
rim.visible_glossy = False

dg = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(body, dg)

def hit_front(x, z):
    loc, nrm, _, _ = bvh.ray_cast(Vector((x, -5, z)), Vector((0, 1, 0)))
    return loc, nrm.normalized()

def hit_down(x, y):
    loc, nrm, _, _ = bvh.ray_cast(Vector((x, y, 5)), Vector((0, 0, -1)))
    return loc, nrm.normalized()

# ---------- eyes ----------
def make_eye(name, x, z, mirror):
    loc, n = hit_front(x, z)
    e = uvsphere(name, loc - n * 0.02, (0.17, 0.21, 0.08), M["eye"])
    orient_to(e, n)
    e.parent = root
    # tangent frame
    right = Vector((1, 0, 0)) - n * n.x
    right.normalize()
    up = n.cross(right)
    big = uvsphere(name + "_ShineBig", loc + n * 0.05 + right * (0.05 * mirror) - up * 0.04,
                   (0.06, 0.07, 0.03), M["shine"], 32, 16)
    orient_to(big, n)
    small = uvsphere(name + "_ShineSmall", loc + n * 0.06 - right * (0.05 * mirror) + up * 0.09,
                     (0.035, 0.04, 0.02), M["shine"], 24, 12)
    orient_to(small, n)
    big.parent = small.parent = root
    return loc, n, right, up

make_eye("Eye_L", -0.38, 0.0, 1)
make_eye("Eye_R", 0.36, -0.04, -1)

# ---------- blush stripes ----------
def blush(cx, cz):
    for i in range(4):
        x = cx + (i - 1.5) * 0.075
        loc, n = hit_front(x, cz)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=loc + n * 0.005)
        s = bpy.context.active_object
        s.name = "Blush"
        s.scale = (0.022, 0.065, 0.02)
        s.data.materials.append(M["blush"])
        smooth(s)
        orient_to(s, n)
        # slant the stripe like the drawing
        s.rotation_quaternion = s.rotation_quaternion @ Quaternion((0, 0, 1), math.radians(-30))
        s.parent = root

blush(-0.36, -0.27)
blush(0.38, -0.31)

# ---------- crown (it has a face too) ----------
def build_crown():
    N, pts = 160, 5
    verts, faces = [], []
    R = 0.42
    for i in range(N):
        t = 2 * math.pi * i / N
        tri = 1 - abs(((t * pts / (2 * math.pi)) % 1) * 2 - 1)   # triangle wave 0..1
        top = 0.32 + 0.38 * tri
        verts += [(R * math.cos(t), R * math.sin(t), 0.0), (R * math.cos(t), R * math.sin(t), top)]
    for i in range(N):
        j = (i + 1) % N
        faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    me = bpy.data.meshes.new("Crown")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("Crown", me)
    scene.collection.objects.link(o)
    sol = o.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.06
    sol.offset = 0
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.02
    bev.segments = 3
    add_mod_subsurf(o, 2)
    bpy.context.view_layer.objects.active = o
    apply_all(o)
    smooth(o)
    o.data.materials.append(M["crown"])
    # gems between the points
    for k in range(pts):
        t = 2 * math.pi * (k + 0.5) / pts
        g = uvsphere("Crown_Gem", (R * 1.04 * math.cos(t), R * 1.04 * math.sin(t), 0.2),
                     (0.05, 0.05, 0.065), M["gem"], 32, 16)
        g.parent = o
    # crown face (front = -Y)
    for gx in (-0.13, 0.13):
        e = uvsphere("Crown_Eye", (gx, -R - 0.02, 0.36), (0.055, 0.03, 0.075), M["eye"], 32, 16)
        e.parent = o
        h = uvsphere("Crown_EyeShine", (gx + 0.012, -R - 0.05, 0.39), (0.018, 0.012, 0.024), M["shine"], 16, 8)
        h.parent = o
    return o

crown = build_crown()
cloc, cn = hit_down(0.2, -0.05)
crown.location = cloc + Vector((0, 0, -0.18))
crown.rotation_euler = (math.radians(-8), math.radians(18), math.radians(-12))
crown.parent = root

# ---------- taco ----------
def build_taco():
    R, n = 0.42, 48
    me = bpy.data.meshes.new("TacoShell")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=1.0)
    fold = math.radians(78)
    Rf = R / fold
    for v in bm.verts:
        u, w = v.co.x, v.co.y
        x = u * math.sqrt(max(0, 1 - w * w / 2)) * R      # square -> disk
        y = w * math.sqrt(max(0, 1 - u * u / 2)) * R
        phi = y / Rf
        v.co = Vector((x, Rf * math.sin(phi), Rf * (1 - math.cos(phi))))
    bm.to_mesh(me)
    bm.free()
    shell = bpy.data.objects.new("Taco_Shell", me)
    scene.collection.objects.link(shell)
    sol = shell.modifiers.new("Solid", "SOLIDIFY")
    sol.thickness = 0.035
    add_mod_subsurf(shell, 1)
    apply_all(shell)
    smooth(shell)
    shell.data.materials.append(M["shell"])

    tex = bpy.data.textures.new("bumps", "CLOUDS")
    tex.noise_scale = 0.08

    def bumpy(name, loc, scale, material, strength):
        o = uvsphere(name, loc, scale, material, 64, 32)
        d = o.modifiers.new("Bumps", "DISPLACE")
        d.texture = tex
        d.strength = strength
        apply_all(o)
        smooth(o)
        o.parent = shell
        return o

    top = Rf * (1 - math.cos(fold)) * 0.85
    bumpy("Taco_Meat", (0, 0, top - 0.08), (0.36, 0.13, 0.1), M["meat"], 0.05)
    bumpy("Taco_Lettuce", (0, 0, top + 0.0), (0.34, 0.12, 0.07), M["lettuce"], 0.07)
    for i in range(9):
        x = -0.28 + i * 0.07 + random.uniform(-.02, .02)
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.012, depth=0.11,
                                            location=(x, random.uniform(-.05, .05), top + 0.07))
        c = bpy.context.active_object
        c.name = "Taco_Cheese"
        c.rotation_euler = (random.uniform(-1, 1), random.uniform(-.6, .6), random.uniform(0, 3))
        c.data.materials.append(M["cheese"])
        add_mod_subsurf(c, 2)
        apply_all(c)
        smooth(c)
        c.parent = shell
    for i in range(6):
        x = -0.24 + i * 0.095
        t = uvsphere("Taco_Tomato", (x, random.uniform(-.06, .06), top + 0.05),
                     (0.03, 0.03, 0.022), M["tomato"], 24, 12)
        t.parent = shell
    return shell

taco = build_taco()
taco.location = (1.15, -0.55, -0.35)
taco.scale = (1.6, 1.6, 1.6)
taco.rotation_euler = (math.radians(-32), math.radians(28), math.radians(-15))  # tipped forward, filling toward viewer
taco.parent = root


# ---------- no clipping: push accessories out of the body until they don't touch ----------
def group_bvh(obj):
    bpy.context.view_layer.update()
    verts, polys = [], []
    for o in [obj] + list(obj.children_recursive):
        if o.type != 'MESH':
            continue
        mw = o.matrix_world
        base = len(verts)
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)

def body_bvh():
    bpy.context.view_layer.update()
    mw = body.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in body.data.vertices], [list(p.vertices) for p in body.data.polygons])

def declip(obj, direction, step=0.01, gap=0.03, limit=200):
    direction = direction.normalized()
    b = body_bvh()
    moved = 0
    while b.overlap(group_bvh(obj)) and moved < limit:
        obj.location += direction * step
        moved += 1
    obj.location += direction * gap     # small breathing room so nothing z-fights
    bpy.context.view_layer.update()
    print(f"DECLIP {obj.name}: moved {moved*step+gap:.3f} units, clear={not b.overlap(group_bvh(obj))}")

declip(crown, Vector((0, 0, 1)))
declip(taco, Vector(taco.location).normalized() + Vector((0, -0.6, 0)))

# overall size: ~0.6 m tall prop
root.scale = (0.28, 0.28, 0.28)

# ---------- export ----------
import os
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/Fuzzboi_456800.blend")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.fbx(filepath=f"{OUT}/Fuzzboi_456800.fbx", use_selection=True,
                         apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
                         mesh_smooth_type='FACE', path_mode='AUTO')
tris = sum(len(o.data.loop_triangles) if (o.type == 'MESH' and not o.data.calc_loop_triangles()) else 0
           for o in scene.objects if o.type == 'MESH')
print("TRIS", tris)

# ---------- render previews ----------
if "render" in sys.argv:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 900
    w = bpy.data.worlds.new("W")
    scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = hexcol("#456800")
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    scene.view_settings.view_transform = 'Standard'
    scene.render.film_transparent = False

    def light(name, loc, energy, size=3):
        l = bpy.data.lights.new(name, 'AREA')
        l.energy = energy
        l.size = size
        o = bpy.data.objects.new(name, l)
        o.location = loc
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(o)
    light("Key", (-2, -3, 3), 400)
    light("Fill", (3, -2, 1), 150)
    light("Rim", (0, 3, 2), 250)

    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 60
    for tag, pos in [("front", (0.05, -3.2, 0.25)), ("three_quarter", (1.9, -2.4, 0.9)), ("side", (3.2, 0.3, 0.4))]:
        cam.location = pos
        cam.rotation_euler = (Vector((0.04, 0, 0.02)) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = f"{OUT}/preview_{tag}.png"
        bpy.ops.render.render(write_still=True)
print("DONE")
