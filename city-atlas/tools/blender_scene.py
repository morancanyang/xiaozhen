"""Run inside Blender: blender -b --python tools/blender_scene.py -- scene.json outputs 32"""
import bpy,bmesh,json,sys,math,time
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
source=Path(args[0]).resolve();out=Path(args[1]).resolve();samples=int(args[2]) if len(args)>2 else 32
out.mkdir(parents=True,exist_ok=True)
data=json.loads(source.read_text(encoding='utf-8'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
mats={}
for name,params in data['materials'].items():
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*params['color'],1)
    
    if name=='asphalt':bs.inputs['Base Color'].default_value=(.00243,.02029,.05448,1)
    if name=='paving':bs.inputs['Base Color'].default_value=(.65,.64,.59,1)
    bs.inputs['Roughness'].default_value=params['roughness'];bs.inputs['Metallic'].default_value=params['metalness']
    bs.inputs['Emission Color'].default_value=(*params['emissive'],1);bs.inputs['Emission Strength'].default_value=params['emissiveIntensity']
    if name in ('glass','shopglass','rail'):bs.inputs['Roughness'].default_value=.23;bs.inputs['Metallic'].default_value=.35
    if name in ('asphalt','paving','ivory','sand','stone','warm'):
        nodes=m.node_tree.nodes;links=m.node_tree.links
        noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=75 if name=='asphalt' else 16;noise.inputs['Detail'].default_value=2
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22 if name=='asphalt' else .1;bump.inputs['Distance'].default_value=.025
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    mats[name]=m

def template(kind):
    bm=bmesh.new()
    if kind=='box':bmesh.ops.create_cube(bm,size=1)
    elif kind=='cylinder':bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=8,radius1=.5,radius2=.5,depth=1)
    elif kind=='sphere':bmesh.ops.create_icosphere(bm,subdivisions=2,radius=.5)
    else:raise ValueError(kind)
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    verts=[tuple(v.co) for v in bm.verts];faces=[tuple(v.index for v in f.verts) for f in bm.faces];bm.free();return verts,faces
templates={k:template(k) for k in ('box','sphere','cylinder')}
groups={}
for b in data['plan']['buildings']:
    obj=bpy.data.objects.new(b['id'],None);obj.location=(b['x'],-b['z'],0);obj.empty_display_size=3
    for k in ('id','name','floors','height','blockId'):obj[k]=b[k]
    scene.collection.objects.link(obj);groups[b['id']]=obj

for n,batch in enumerate(data['batches']):
    unit,unitfaces=templates[batch['type']];verts=[];faces=[];parent=groups.get(batch['owner']);origin=parent.location if parent else Vector((0,0,0))
    for item in batch['items']:
        px,py,pz=item['p'];sx,sy,sz=item['s'];c=math.cos(item['r']);s=math.sin(item['r']);offset=len(verts)
        for vx,vy,vz in unit:
            x=vx*sx;y=vy*sz;z=vz*sy
            verts.append((c*x-s*y+px-origin.x,s*x+c*y-pz-origin.y,z+py))
        faces.extend(tuple(offset+i for i in f) for f in unitfaces)
    mesh=bpy.data.meshes.new(f"{batch['owner']}_{batch['material']}");mesh.from_pydata(verts,[],faces);mesh.materials.append(mats[batch['material']]);mesh.update()
    obj=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(obj)
    if parent:obj.parent=parent
    if batch['material'] in ('leaf1','leaf2'):
        for p in mesh.polygons:p.use_smooth=True
    if batch['material'] in ('ivory','sand','stone','warm','equipment','ledge'):
        bevel=obj.modifiers.new('Subtle architectural edge highlights','BEVEL');bevel.width=.055;bevel.segments=2
    if n%75==0:print('IMPORT',n,'/',len(data['batches']),flush=True)

# A clear, editable record of the future waterway, hidden in final renders.
guide=bpy.data.objects.new('FUTURE_RIVER_64M_DO_NOT_BUILD',None);guide.empty_display_type='CUBE';guide.scale=(32,300,.1);guide['width_m']=64;guide['purpose']='Reserved continuous empty corridor; no river yet';scene.collection.objects.link(guide)

def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
bpy.ops.mesh.primitive_plane_add(size=20000,location=(0,0,-7.4));backdrop=bpy.context.object;backdrop.name='Studio ground';backdrop.data.materials.append(material('Studio sage',(0.72,.77,.69)))
world=bpy.data.worlds.new('Morning atmosphere');world.use_nodes=True;scene.world=world
nodes=world.node_tree.nodes;links=world.node_tree.links;sky=nodes.new('ShaderNodeTexSky');sky_types={p.identifier for p in sky.bl_rna.properties['sky_type'].enum_items};sky.sky_type='MULTIPLE_SCATTERING' if 'MULTIPLE_SCATTERING' in sky_types else 'NISHITA';sky.sun_elevation=math.radians(27);sky.sun_rotation=math.radians(135);sky.altitude=.1;sky.air_density=1.1;setattr(sky,'aerosol_density' if hasattr(sky,'aerosol_density') else 'dust_density',.6)
links.new(sky.outputs['Color'],nodes.get('Background').inputs['Color']);nodes.get('Background').inputs['Strength'].default_value=.12
bpy.ops.object.light_add(type='SUN',location=(-180,-210,180));sun=bpy.context.object;sun.name='Soft morning sun';sun.data.energy=2.3;sun.data.angle=math.radians(5);sun.data.color=(1,.9,.72);sun.rotation_euler=Vector((180,210,-180)).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='AREA',location=(80,-60,400));fill=bpy.context.object;fill.name='Sky soft fill';fill.data.energy=150000;fill.data.shape='DISK';fill.data.size=500

# Restrained volumetric morning haze in a physically sampled volume.
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,50));haze=bpy.context.object;haze.name='Morning volumetric haze';haze.scale=(850,750,115)
fog=bpy.data.materials.new('Subtle aerial perspective');fog.use_nodes=True;fog.node_tree.nodes.clear();output=fog.node_tree.nodes.new('ShaderNodeOutputMaterial');volume=fog.node_tree.nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Density'].default_value=.00012;volume.inputs['Color'].default_value=(.8,.87,.81,1);volume.inputs['Anisotropy'].default_value=.25;fog.node_tree.links.new(volume.outputs['Volume'],output.inputs['Volume']);haze.data.materials.append(fog)

bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='City overview';scene.camera=camera;camera.data.type='PERSP';camera.data.lens=44;camera.data.clip_end=20000
def frame_camera(pos,target,lens=44):
    camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
frame_camera((760,-940,760),(0,0,15))
scene.render.engine='CYCLES';scene.cycles.samples=samples;scene.cycles.use_denoising=True;scene.cycles.max_bounces=6;scene.cycles.transparent_max_bounces=4;scene.cycles.volume_bounces=1
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    for backend in ('OPTIX','CUDA','HIP','ONEAPI'):
        try:
            prefs.compute_device_type=backend;prefs.get_devices()
            gpu=[d for d in prefs.devices if d.type!='CPU']
            if gpu:
                for d in prefs.devices:d.use=d.type!='CPU'
                scene.cycles.device='GPU';print('CYCLES GPU',backend,[d.name for d in gpu],flush=True);break
        except Exception:pass
except Exception:pass
scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.65
try:scene.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
scene.render.fps=24;scene.frame_start=1;scene.frame_end=144
# Six-second camera orbit. Curves are retained in the .blend for further work.
for frame,pos in [(1,(760,-940,760)),(72,(1010,-660,660)),(144,(1100,-250,610))]:
    frame_camera(pos,(0,0,15));camera.keyframe_insert(data_path='location',frame=frame);camera.keyframe_insert(data_path='rotation_euler',frame=frame)
scene.frame_set(1)
scene['source']='Three.js qianren-city-v1';scene['central_corridor_width_m']=64;scene['building_count']=len(groups)
scene.render.filepath=str(out/'blender-overview.png');bpy.ops.wm.save_as_mainfile(filepath=str(out/'qianren-city.blend'))
print('RENDER overview',flush=True);bpy.ops.render.render(write_still=True)
frame_camera((240,-150,115),(112,70,25),48)
camera.animation_data_clear();scene.render.filepath=str(out/'blender-street.png');print('RENDER street',flush=True);bpy.ops.render.render(write_still=True)
summary={'status':'complete','buildings':len(groups),'meshes':len(data['batches']),'engine':scene.render.engine,'samples':samples,'blend':str(out/'qianren-city.blend'),'images':[str(out/'blender-overview.png'),str(out/'blender-street.png')],'animation':'144-frame editable camera orbit in blend; video not rendered'}
(out/'blender-result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print('CITY_RENDER_COMPLETE',json.dumps(summary),flush=True)
