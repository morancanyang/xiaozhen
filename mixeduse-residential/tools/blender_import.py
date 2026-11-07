"""Import the exact reviewed Three.js snapshot into an isolated Blender file.

This script runs inside the NEW Blender process opened by our MCP tool. It does
not attach to, close, or clear any pre-existing user window.
"""
import base64
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
DATA = json.loads((OUT / 'scene.json').read_text(encoding='utf8'))
SCENE = bpy.data.scenes.new('ZONGYU_MIXEDUSE')
bpy.context.window.scene = SCENE
SCENE.unit_settings.system = 'METRIC'
SCENE.unit_settings.scale_length = 1
MODEL = bpy.data.collections.new('棕屿里 · 可移植模型')
SCENE.collection.children.link(MODEL)
STUDIO = bpy.data.collections.new('摄影环境 · 不属于城市模型')
SCENE.collection.children.link(STUDIO)
campus = bpy.data.objects.new('zongyu-mixeduse', None)
MODEL.objects.link(campus)
campus['footprint_m'] = [112.0, 112.0]
campus['front'] = '+Z Three.js / -Y Blender'
campus['snapshot_space'] = DATA.get('snapshotSpace', 'world')

owners = {}
def owner_empty(name):
    if name not in owners:
        empty = bpy.data.objects.new(str(name), None)
        empty.parent = campus
        MODEL.objects.link(empty)
        owners[name] = empty
    return owners[name]

for name in ('structure','facade','balconies','lobby','roof'):
    owner_empty(name)

MATERIALS = {}
EMISSIVE_MATERIALS = []
for uid, info in DATA['materials'].items():
    mat = bpy.data.materials.new(info.get('name', uid))
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bs = nodes.get('Principled BSDF')
    color = list(info.get('color', [1, 1, 1]))[:3]
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = info.get('roughness', .75)
    bs.inputs['Metallic'].default_value = info.get('metalness', 0)
    bs.inputs['Emission Color'].default_value = (*info.get('emissive', [0, 0, 0]), 1)
    bs.inputs['Emission Strength'].default_value = info.get('emissiveIntensity', 0)
    name = mat.name.lower()
    # Vertex tint carries both original vertex colours and instance colours.
    vc = nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'InstanceTint'
    tint = nodes.new('ShaderNodeMixRGB')
    tint.blend_type = 'MULTIPLY'
    tint.inputs[0].default_value = 1
    tint.inputs[1].default_value = (*color, 1)
    links.new(vc.outputs['Color'], tint.inputs[2])
    surface_color = tint.outputs['Color']
    if info.get('texture'):
        texture_path = OUT / ('blender-texture-' + uid + '.png')
        texture_path.write_bytes(base64.b64decode(info['texture'].split(',', 1)[1]))
        image = bpy.data.images.load(str(texture_path), check_existing=True)
        image.pack()
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = image
        tex.extension = 'REPEAT'
        coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeVectorMath')
        mapping.operation = 'MULTIPLY'
        repeat = info.get('repeat', [1, 1])
        mapping.inputs[1].default_value = (repeat[0], repeat[1], 1)
        links.new(coord.outputs['UV'], mapping.inputs[0])
        links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        mix = nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 1
        links.new(surface_color, mix.inputs[1])
        links.new(tex.outputs['Color'], mix.inputs[2])
        surface_color = mix.outputs['Color']
        if info.get('transparent') and 'glass' not in name:
            links.new(tex.outputs['Alpha'], bs.inputs['Alpha'])
    links.new(surface_color, bs.inputs['Base Color'])
    if any(k in name for k in ('glass', 'glazing')):
        # Actual closed glazing; room cards behind it supply depth and curtains.
        bs.inputs['Transmission Weight'].default_value = 1.0 if 'storefront' in name else .86
        bs.inputs['IOR'].default_value = 1.45
        bs.inputs['Coat Weight'].default_value = .65
        bs.inputs['Coat Roughness'].default_value = .09
        bs.inputs['Roughness'].default_value = max(.09, min(info.get('roughness', .14), .23))
        bs.inputs['Metallic'].default_value = 0
        if 'storefront' in name:
            bs.inputs['Base Color'].default_value=(.94,.98,.97,1)
            links.remove(bs.inputs['Base Color'].links[0])
            bs.inputs['Roughness'].default_value=.035
    if any(k in name for k in ('concrete', 'render', 'stone', 'paving', 'cream', 'plaster')):
        coord = nodes.new('ShaderNodeTexCoord')
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 35
        noise.inputs['Detail'].default_value = 2
        links.new(coord.outputs['Object'], noise.inputs['Vector'])
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .12
        bump.inputs['Distance'].default_value = .003
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bs.inputs['Normal'])
    if any(k in name for k in ('leaf', 'foliage')):
        bs.inputs['Subsurface Weight'].default_value = .07
        bs.inputs['Subsurface Radius'].default_value = (.35, .6, .25)
    if max(info.get('emissive', [0, 0, 0])) > .01 or any(k in name for k in ('lamp', 'interior', 'lit')):
        EMISSIVE_MATERIALS.append(mat)
    MATERIALS[uid] = mat

GEOMETRIES = {}
for uid, geo in DATA['geometries'].items():
    p = np.asarray(geo['positions'], dtype=np.float32).reshape(-1, 3)
    idx = np.asarray(geo['indices'] if geo.get('indices') is not None else range(len(p)), dtype=np.int32).reshape(-1, 3)
    uv = np.asarray(geo['uv'], dtype=np.float32).reshape(-1, 2) if geo.get('uv') else None
    cols = np.asarray(geo['colors'], dtype=np.float32).reshape(-1, 3) if geo.get('colors') else None
    GEOMETRIES[uid] = p, idx, uv, cols

batches = {}
for ob in DATA['objects']:
    batches.setdefault((ob.get('owner', 'site'), ob['m']), []).append(ob)

vertex_count = face_count = 0
for (owner, material_id), items in batches.items():
    positions, triangles, corner_uv, corner_colors = [], [], [], []
    offset = 0
    for ob in items:
        p, idx, uv, cols = GEOMETRIES[ob['g']]
        transform = np.asarray(ob['matrix'], dtype=np.float32).reshape(4, 4, order='F')
        v = p @ transform[:3, :3].T + transform[:3, 3]
        v = np.stack((v[:, 0], -v[:, 2], v[:, 1]), axis=1)
        faces = idx[:, ::-1] if np.linalg.det(transform[:3, :3]) < 0 else idx
        positions.append(v)
        triangles.append(faces + offset)
        offset += len(v)
        corner_uv.append(uv[faces].reshape(-1, 2) if uv is not None else np.zeros((faces.size, 2), dtype=np.float32))
        rgb = cols[faces].reshape(-1, 3) if cols is not None else np.ones((faces.size, 3), dtype=np.float32)
        rgb = rgb * np.asarray(ob.get('tint') or [1, 1, 1], dtype=np.float32)
        corner_colors.append(rgb)
    p = np.concatenate(positions)
    faces = np.concatenate(triangles)
    mesh = bpy.data.meshes.new(str(owner) + ' / ' + MATERIALS[material_id].name)
    mesh.vertices.add(len(p))
    mesh.vertices.foreach_set('co', p.ravel())
    mesh.loops.add(faces.size)
    mesh.loops.foreach_set('vertex_index', faces.ravel())
    mesh.polygons.add(len(faces))
    mesh.polygons.foreach_set('loop_start', np.arange(len(faces), dtype=np.int32) * 3)
    mesh.polygons.foreach_set('loop_total', np.full(len(faces), 3, dtype=np.int32))
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='UVMap')
    uv_layer.data.foreach_set('uv', np.concatenate(corner_uv).ravel())
    colors = np.concatenate(corner_colors)
    rgba = np.column_stack((colors, np.ones(len(colors), dtype=np.float32)))
    attr = mesh.color_attributes.new(name='InstanceTint', type='FLOAT_COLOR', domain='CORNER')
    attr.data.foreach_set('color', rgba.ravel())
    mesh.materials.append(MATERIALS[material_id])
    ob = bpy.data.objects.new(mesh.name, mesh)
    ob.parent = owner_empty(owner)
    MODEL.objects.link(ob)
    vertex_count += len(p)
    face_count += len(faces)
    print('Imported', mesh.name, len(p), 'vertices', flush=True)

# Separate photographic environment: never export this collection to the town.
def to_studio(ob):
    for collection in list(ob.users_collection):
        collection.objects.unlink(ob)
    STUDIO.objects.link(ob)
    return ob

def cv(p):
    return Vector((p[0], -p[2], p[1]))

world = bpy.data.worlds.new('Soft neutral daylight')
world.use_nodes = True
SCENE.world = world
world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.65, .76, .88, 1)
world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .36

bpy.ops.object.light_add(type='SUN', location=(-100, -120, 180))
sun = to_studio(bpy.context.object)
sun.name = 'Soft morning sun'
sun.data.energy = 2.5
sun.data.angle = math.radians(4)
sun.data.color = (1, .94, .85)
sun.rotation_euler = (-sun.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.light_add(type='AREA', location=(70, 0, 110))
fill = to_studio(bpy.context.object)
fill.name = 'Large soft sky fill'
fill.data.energy = 14000
fill.data.shape = 'DISK'
fill.data.size = 85
fill.data.color = (.85, .92, 1)
fill.rotation_euler = (Vector((0, 0, 20)) - fill.location).to_track_quat('-Z', 'Y').to_euler()

for sx in (-35,-26,-17,17,26,35):
    light=bpy.data.lights.new('Shop practical fill','AREA');light.energy=220;light.color=(1,.85,.66);light.shape='RECTANGLE';light.size=5;light.size_y=2
    ob=bpy.data.objects.new(light.name,light);ob.location=(sx,-35.4,4.0);STUDIO.objects.link(ob)

floor_mat = bpy.data.materials.new('Photography ground')
floor_mat.use_nodes = True
floor_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.68, .7, .66, 1)
floor_mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = 1
bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, -.52))
floor = to_studio(bpy.context.object)
floor.name = 'Backdrop - presentation only'
floor.data.materials.append(floor_mat)
floor.is_shadow_catcher=True
SCENE.render.film_transparent=True
# Blender 5.2 compositor node group: alpha-over onto a true white background.
comp=bpy.data.node_groups.new('White photographic background','CompositorNodeTree')
comp.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=comp.nodes.new('CompositorNodeRLayers');rl.scene=SCENE
over=comp.nodes.new('CompositorNodeAlphaOver');over.inputs['Factor'].default_value=1;over.inputs['Background'].default_value=(256,256,256,1)
comp.links.new(rl.outputs['Image'],over.inputs['Foreground'])
out=comp.nodes.new('NodeGroupOutput');comp.links.new(over.outputs['Image'],out.inputs['Image'])
SCENE.compositing_node_group=comp

SHOTS = [
 {'name':'overview','position':(145,115,165),'target':(0,33,15),'lens':48,'size':(7680,4320),'ortho':True,'scale':205},
 {'name':'facade','position':(0,38,180),'target':(0,38,24),'lens':48,'size':(3840,2880),'ortho':True,'scale':120},
 {'name':'shops','position':(-35,6.5,60),'target':(-25,2.5,37),'lens':40,'size':(3840,2880)},
 {'name':'entry','position':(12,6,61),'target':(0,2.5,40),'lens':44,'size':(3840,2880)},
 {'name':'twilight','position':(145,115,165),'target':(0,33,15),'lens':48,'size':(3840,2880),'ortho':True,'scale':175},
]
CAMERAS = {}
for shot in SHOTS:
    camera_data = bpy.data.cameras.new('Camera_' + shot['name'])
    camera_data.lens = shot['lens']
    if shot.get('ortho'):
        camera_data.type='ORTHO'
        camera_data.ortho_scale=shot['scale']
    camera_data.sensor_width = 36
    camera_data.sensor_fit = 'HORIZONTAL'
    camera_data.clip_start = .1
    camera_data.clip_end = 5000
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    STUDIO.objects.link(camera)
    camera.location = cv(shot['position'])
    camera.rotation_euler = (cv(shot['target']) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    CAMERAS[shot['name']] = camera
SCENE.camera = CAMERAS['overview']
SCENE.render.engine = 'CYCLES'
SCENE.cycles.samples = 64
SCENE.cycles.use_denoising = True
SCENE.cycles.use_adaptive_sampling = True
SCENE.cycles.adaptive_threshold = .018
SCENE.cycles.adaptive_min_samples = 16
SCENE.cycles.max_bounces = 8
SCENE.cycles.transmission_bounces = 6
DEVICE_NAMES = []
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = device.type == 'OPTIX'
        if device.use:
            DEVICE_NAMES.append(device.name)
    SCENE.cycles.device = 'GPU' if DEVICE_NAMES else 'CPU'
except Exception as error:
    SCENE.cycles.device = 'CPU'
    print('GPU unavailable:', str(error), flush=True)
SCENE.render.resolution_percentage = 100
SCENE.render.image_settings.file_format = 'PNG'
SCENE.render.image_settings.color_mode = 'RGBA'
SCENE.view_settings.view_transform = 'AgX'
SCENE.view_settings.exposure = .1
try:
    SCENE.view_settings.look = 'AgX - Medium High Contrast'
except TypeError:
    pass
SCENE.render.resolution_x, SCENE.render.resolution_y = SHOTS[0]['size']
# Frame all eight corners of the REAL imported model bounds, not an assumed
# radius. A tall slab and the nearest parcel corner must fit simultaneously.
bpy.context.view_layer.update()
model_points = [ob.matrix_world @ Vector(corner) for ob in MODEL.objects if ob.type=='MESH' for corner in ob.bound_box]
minimum = Vector(tuple(min(point[i] for point in model_points) for i in range(3)))
maximum = Vector(tuple(max(point[i] for point in model_points) for i in range(3)))
bound_corners = [Vector((x,y,z)) for x in (minimum.x,maximum.x) for y in (minimum.y,maximum.y) for z in (minimum.z,maximum.z)]
framing = {}
for name in ('overview','twilight'):
    camera = CAMERAS[name]
    shot=next(s for s in SHOTS if s['name']==name)
    SCENE.render.resolution_x,SCENE.render.resolution_y=shot['size']
    target = cv(shot['target'])
    offset = camera.location - target
    for attempt in range(48):
        camera.location = target + offset
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update()
        projected = [world_to_camera_view(SCENE,camera,corner) for corner in bound_corners]
        if all(.055<=p.x<=.945 and .055<=p.y<=.945 and p.z>camera.data.clip_start for p in projected):
            break
        camera.data.ortho_scale *= 1.045 if camera.data.type=='ORTHO' else 1
        offset *= 1.045
    else:
        raise RuntimeError('Could not frame the complete model for '+name)
    framing[name] = {'camera_blender':list(camera.location),'target_blender':list(target),'bounds_min':list(minimum),'bounds_max':list(maximum),'projected_min':[min(p.x for p in projected),min(p.y for p in projected)],'projected_max':[max(p.x for p in projected),max(p.y for p in projected)],'iterations':attempt}
(OUT/'blender-framing.json').write_text(json.dumps(framing,ensure_ascii=False,indent=2),encoding='utf8')
SCENE['camera_fit'] = json.dumps(framing)
SCENE.render.resolution_x,SCENE.render.resolution_y=SHOTS[0]['size']
SCENE['source'] = 'Exact reviewed Three.js scene.json; baked world transforms, UV, vertex and instance colours'
SCENE['units'] = 'metres'
SCENE['parcel_m'] = 112
SCENE['dynamic_note'] = 'HTML has procedural wind, curtains and staggered day/night lights; blend stores exported geometry and photographic lighting.'
SCENE['snapshot_objects'] = len(DATA['objects'])
SCENE['imported_vertices'] = vertex_count
SCENE['imported_triangles'] = face_count
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'棕屿里.blend'), compress=True)
print('SCENE_PREPARED', vertex_count, 'vertices;', face_count, 'triangles;', SCENE.cycles.device, DEVICE_NAMES, flush=True)
