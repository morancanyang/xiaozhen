"""Run in visible Blender. Timers keep the UI alive while render jobs run."""
import bpy,json,sys,math,traceback
from pathlib import Path
from mathutils import Vector
root=Path(sys.argv[sys.argv.index('--')+1]);scene=bpy.context.scene;camera=scene.camera
shots=[('blender-overview',(135,-170,125),(0,0,3),48,3840,2880),('blender-path',(-34,-20,3.1),(-37,0,3),30,1920,1280),('blender-lake',(32,-18,5),(12,5,0),35,1920,1280),('blender-bench',(16,-23,3.1),(10,-16,1.2),35,1920,1280),('blender-detail',(-24,-19,3),(-18,-14,1),38,1920,1280),('blender-night',(135,-170,125),(0,0,3),48,1920,1440)]
state={'index':0,'running':False,'finished':[]}
bpy.context.preferences.view.render_display_type='WINDOW'
def progress(status):
 (root/'outputs/visible-progress.json').write_text(json.dumps({'status':status,'index':state['index'],'total':len(shots),'finished':state['finished']},ensure_ascii=False),encoding='utf8')
def tick():
 try:
  if state['running']:
   if bpy.app.is_job_running('RENDER'):return 1.0
   path=root/'outputs'/(shots[state['index']][0]+'.png')
   if not path.is_file():raise RuntimeError('Render did not produce '+str(path))
   state['finished'].append(str(path));state['index']+=1;state['running']=False;progress('rendering')
  if state['index']>=len(shots):
   result={'status':'complete','engine':scene.render.engine,'samples':scene.cycles.samples,'device':scene.cycles.device,'blend':str(root/'森隐公园.blend'),'renders':state['finished'],'visible_gui':True}
   (root/'outputs/blender-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');progress('complete');return None
  name,pos,target,lens,w,h=shots[state['index']]
  if name=='blender-night':
   scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.025
   for o in scene.objects:
    if o.type=='LIGHT':o.data.energy=.04 if o.data.type=='SUN' else 3500
   for mat in bpy.data.materials:
    if 'Warm lantern diffuser' in mat.name:mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=3
   for i in range(10):
    a=i/10*math.pi*2;x=-2+math.cos(a)*39;x+=1.9 if x>0 else -1.9;z=math.sin(a)*38
    bpy.ops.object.light_add(type='POINT',location=(x,-z,2.9));lamp=bpy.context.object;lamp.data.energy=650;lamp.data.color=(1,.73,.42);lamp.data.shadow_soft_size=.35
   scene.view_settings.exposure=.5
  camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
  scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.filepath=str(root/'outputs'/(name+'.png'));progress('rendering');state['running']=True
  bpy.ops.render.render('INVOKE_DEFAULT',write_still=True);return 2.0
 except Exception:
  (root/'outputs/blender-result.json').write_text(json.dumps({'status':'failed','error':traceback.format_exc()}),encoding='utf8');return None
# Camera view is immediately useful when the model opens.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
progress('opening');bpy.app.timers.register(tick,first_interval=4.0)
