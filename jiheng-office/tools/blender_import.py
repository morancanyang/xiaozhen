"""Import the exact Three.js world-space snapshot into a fresh Blender scene."""
import bpy, json, math, base64, numpy as np
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'outputs/office-scene.json').read_text(encoding='utf8'))
assert DATA['format'] == 'jiheng-landmark-office-v1'
assert DATA.get('snapshotSpace') == 'world'

def cv(p):
    return Vector((p[0], -p[2], p[1]))

scene = bpy.data.scenes.new('JIHENG_ONE')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
collection = bpy.data.collections.new('Landmark office model only')
scene.collection.children.link(collection)
studio = bpy.data.collections.new('Presentation - not part of city module')
scene.collection.children.link(studio)
campus = bpy.data.objects.new('jiheng-landmark-office', None)
collection.objects.link(campus)
campus['width_m'] = campus['depth_m'] = 112
campus['front'] = '+Z in Three.js / -Y in Blender'
owners = {}
building_specs = {b['id']: b for b in DATA['manifest']['buildings']}
owner_names = sorted({o['owner'] for o in DATA['objects']} | set(building_specs))
for owner in owner_names:
    parent = bpy.data.objects.new(owner, None)
    parent.parent = campus
    parent['id'] = owner
    if owner in building_specs:
        b = building_specs[owner]
        parent['name_cn'] = b['name']
        parent['floors'] = b['floors']
        parent.location = cv([b['x'], 0, b['z']])
    collection.objects.link(parent)
    owners[owner] = parent

for part in DATA['manifest']['parts']:
    if part.get('buildingId'):
        owners[part['id']].parent = owners[part['buildingId']]

materials = {}
for uid, item in DATA['materials'].items():
    mat = bpy.data.materials.new('NUANTING_' + item['name'])
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*item['color'], 1)
    bs.inputs['Roughness'].default_value = item.get('roughness', .8)
    bs.inputs['Metallic'].default_value = item.get('metalness', 0)
    bs.inputs['Emission Color'].default_value = (*item.get('emissive', [0, 0, 0]), 1)
    bs.inputs['Emission Strength'].default_value = item.get('emissiveIntensity', 0)
    name = item['name'].lower()
    if 'glass' in name and 'window-lit' not in name:
        bs.inputs['Coat Weight'].default_value = .65
        bs.inputs['Coat Roughness'].default_value = .12
        bs.inputs['Transmission Weight'].default_value = item.get('transmission', 0)
        bs.inputs['Coat Weight'].default_value = .85
        bs.inputs['IOR'].default_value = 1.45
        bs.inputs['Roughness'].default_value = max(.08, item.get('roughness', .15))
    if item.get('texture'):
        file = ROOT / 'outputs' / ('texture_' + uid + '.png')
        file.write_bytes(base64.b64decode(item['texture'].split(',')[1]))
        im = bpy.data.images.load(str(file)); im.pack()
        texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image = im; texture.extension = 'REPEAT'
        uv = mat.node_tree.nodes.new('ShaderNodeTexCoord')
        repeat = mat.node_tree.nodes.new('ShaderNodeVectorMath')
        repeat.operation = 'MULTIPLY'
        repeat.inputs[1].default_value = (*item.get('repeat', [1, 1]), 1)
        mat.node_tree.links.new(uv.outputs['UV'], repeat.inputs[0])
        mat.node_tree.links.new(repeat.outputs['Vector'], texture.inputs['Vector'])
        mat.node_tree.links.new(texture.outputs['Color'], bs.inputs['Base Color'])
    if any(token in name for token in ['wall', 'paint', 'stucco', 'stone', 'paving', 'asphalt', 'roof', 'tile']):
        noise = mat.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 55 if any(t in name for t in ['wall', 'paint', 'stucco']) else 32
        bump = mat.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .16
        bump.inputs['Distance'].default_value = .008 if 'wall' in name else .013
        mat.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'], bs.inputs['Normal'])
    materials[uid] = mat

geometries = {}
for uid, item in DATA['geometries'].items():
    vertices = np.array(item['positions'], dtype=np.float32).reshape((-1, 3))
    indices = np.array(item['indices'] if item.get('indices') is not None else np.arange(len(vertices)), dtype=np.int32).reshape((-1, 3))
    uv = np.array(item['uv'], dtype=np.float32).reshape((-1, 2)) if item.get('uv') else None
    geometries[uid] = vertices, indices, uv
batches = {}
for obj in DATA['objects']:
    batches.setdefault((obj['owner'], obj['m']), []).append(obj)
for (owner, mid), objects in batches.items():
    all_vertices, all_faces, all_uvs = [], [], []
    offset = 0; parent = owners.get(owner, campus)
    origin = np.array(parent.location)
    for item in objects:
        pos, indices, uv = geometries[item['g']]
        matrix = np.array(item['matrix'], dtype=np.float32).reshape((4, 4), order='F')
        world = pos @ matrix[:3, :3].T + matrix[:3, 3]
        converted = np.stack((world[:, 0], -world[:, 2], world[:, 1]), axis=1) - origin
        all_vertices.append(converted); all_faces.append(indices + offset); offset += len(pos)
        all_uvs.append(uv[indices].reshape((-1, 2)) if uv is not None else np.zeros((indices.size, 2), dtype=np.float32))
    vertices = np.concatenate(all_vertices); faces = np.concatenate(all_faces)
    mesh = bpy.data.meshes.new(owner + '_' + materials[mid].name)
    mesh.vertices.add(len(vertices)); mesh.vertices.foreach_set('co', vertices.ravel())
    mesh.loops.add(len(faces) * 3); mesh.loops.foreach_set('vertex_index', faces.ravel())
    mesh.polygons.add(len(faces)); mesh.polygons.foreach_set('loop_start', np.arange(len(faces), dtype=np.int32) * 3)
    mesh.polygons.foreach_set('loop_total', np.full(len(faces), 3, dtype=np.int32))
    mesh.update()
    layer = mesh.uv_layers.new(name='UVMap'); layer.data.foreach_set('uv', np.concatenate(all_uvs).ravel())
    mesh.materials.append(materials[mid])
    obj = bpy.data.objects.new(mesh.name, mesh); obj.parent = parent; collection.objects.link(obj)
    name = DATA['materials'][mid]['name'].lower()
    if any(t in name for t in ['leaf', 'foliage', 'skin']):
        for poly in mesh.polygons: poly.use_smooth = True

world = bpy.data.worlds.new('Warm afternoon sky'); world.use_nodes = True; scene.world = world
nodes = world.node_tree.nodes; links = world.node_tree.links
background = nodes.get('Background'); background.inputs['Strength'].default_value = .3
sky = nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
sky.sun_elevation = math.radians(36); sky.sun_rotation = math.radians(135); sky.sun_disc = False; sky.altitude = .1
links.new(sky.outputs['Color'], background.inputs['Color'])
sun_data = bpy.data.lights.new('Afternoon sun', 'SUN'); sun_data.energy = 2.5
sun_data.angle = math.radians(2.7); sun_data.color = (1, .94, .86)
sun = bpy.data.objects.new('Afternoon sun', sun_data); studio.objects.link(sun)
sun.location = cv([-180,310,220]); sun.rotation_euler = (cv([0,72,0])-sun.location).to_track_quat('-Z', 'Y').to_euler()

backdrop = bpy.data.materials.new('Warm limestone studio floor'); backdrop.diffuse_color = (.91, .94, .96, 1)
mesh = bpy.data.meshes.new('Backdrop')
mesh.from_pydata([(-10000, -10000, -.62), (10000, -10000, -.62), (10000, 10000, -.62), (-10000, 10000, -.62)], [], [(0, 1, 2, 3)])
obj = bpy.data.objects.new('Backdrop', mesh); mesh.materials.append(backdrop); studio.objects.link(obj)
fog = bpy.data.materials.new('Afternoon subtle participating medium'); fog.use_nodes = True
fog.node_tree.nodes.clear(); out = fog.node_tree.nodes.new('ShaderNodeOutputMaterial')
volume = fog.node_tree.nodes.new('ShaderNodeVolumePrincipled'); volume.inputs['Density'].default_value = .000075
volume.inputs['Color'].default_value = (.94, .89, .78, 1); volume.inputs['Anisotropy'].default_value = .3
fog.node_tree.links.new(volume.outputs['Volume'], out.inputs['Volume'])
mesh = bpy.data.meshes.new('Atmosphere volume')
verts = [(x, y, z) for x in [-220, 220] for y in [-220, 220] for z in [-1, 210]]
mesh.from_pydata(verts, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
obj = bpy.data.objects.new('Afternoon atmosphere', mesh); mesh.materials.append(fog); studio.objects.link(obj)

# Camera coordinates match the standalone Three.js viewer (Y up, 43 degree vertical FOV).
views = {
    'Overview': ([235,242,280],[0,85,0],43),
    'Front': ([0,90,350],[0,90,0],43),
    'Top': ([0,350,.01],[0,0,0],43),
    'Low': ([75,10,100],[0,105,0],43),
    'Entrance': ([16,8,66],[0,6,30],43),
    'Terrace': ([35,79,43],[7,69.5,19],43),
    'Roof': ([48,207,55],[0,175,0],43),
}
for name, (position, target, fov) in views.items():
    camera_data = bpy.data.cameras.new(name); cam = bpy.data.objects.new(scene.name + '_' + name, camera_data)
    studio.objects.link(cam); cam.location = cv(position); cam.rotation_euler = (cv(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    camera_data.sensor_fit = 'VERTICAL'; camera_data.sensor_height = 24
    camera_data.lens = 24 / (2 * math.tan(math.radians(fov) / 2)); camera_data.clip_end = 8000
    camera_data.clip_start = .05
    if name in ['Overview','Front','Top']:
        camera_data.type = 'ORTHO'
        camera_data.ortho_scale = {'Overview':244,'Front':222,'Top':146}[name]
    scene['office_camera_' + name] = cam.name
scene.camera = scene.objects[scene['office_camera_Overview']]
scene.render.engine = 'CYCLES'; scene.cycles.samples = 64; scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6; scene.cycles.volume_bounces = 1
scene.render.resolution_x = 1800; scene.render.resolution_y = 1200; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = -.1
try: scene.view_settings.look = 'AgX - Medium High Contrast'
except TypeError: pass
scene['source'] = 'office-scene.json / exact Three.js world-space geometry'
scene['width_m'] = scene['depth_m'] = 112
scene['front_three_js'] = '+Z'
scene['building_ids'] = json.dumps(sorted(building_specs))
scene['height_m'] = 184
scene.cycles.adaptive_threshold = .035
scene.cycles.use_adaptive_sampling = True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / '霁衡中心.blend'), compress=True)
print(json.dumps({'status': 'imported', 'scene': scene.name, 'objects': len(scene.objects), 'model_batches': len(batches), 'buildings': sorted(building_specs), 'owners': owner_names}, ensure_ascii=True), flush=True)
