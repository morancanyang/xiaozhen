"""Refine the same editable model into a pure-white Cycles studio master."""
import bpy,json,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];start=time.time()
try:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'霁衡中心.blend'))
    scene=bpy.data.scenes['JIHENG_ONE']
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU' if any(d.use and d.type=='OPTIX' for d in prefs.devices) else 'CPU'
    scene.render.film_transparent=True;bpy.data.objects['Backdrop'].is_shadow_catcher=True
    bpy.data.objects['Afternoon atmosphere'].hide_render=True
    tree=bpy.data.node_groups.new('White studio composite','CompositorNodeTree')
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    output=tree.nodes.new('NodeGroupOutput');render=tree.nodes.new('CompositorNodeRLayers');render.scene=scene
    # Blender 5.2 has named Background/Foreground sockets and an explicit display conversion node.
    display=tree.nodes.new('CompositorNodeConvertToDisplay');display.view_settings.view_transform='AgX';display.view_settings.look='AgX - Medium High Contrast'
    over=tree.nodes.new('CompositorNodeAlphaOver');over.inputs['Factor'].default_value=1;over.inputs['Background'].default_value=(1,1,1,1)
    tree.links.new(render.outputs['Image'],display.inputs['Image']);tree.links.new(display.outputs['Image'],over.inputs['Foreground']);tree.links.new(over.outputs[0],output.inputs['Image']);scene.compositing_node_group=tree
    scene.view_settings.view_transform='Raw';scene.view_settings.look='None';scene.view_settings.exposure=0
    scene.camera=scene.objects[scene['office_camera_Overview']]
    scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.cycles.samples=64
    scene.render.filepath=str(ROOT/'outputs/blender-white.png');bpy.ops.render.render(write_still=True)
    scene.render.resolution_x=7680;scene.render.resolution_y=4320;scene.cycles.samples=96
    scene.render.filepath=str(ROOT/'outputs/霁衡中心-8K.png');bpy.ops.render.render(write_still=True)
    scene['studio_background']='white composited over physically rendered shadow catcher'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'霁衡中心.blend'),compress=True)
    result={'status':'complete','engine':'CYCLES','device':scene.cycles.device,'resolution':[7680,4320],'samples':96,'elapsed_seconds':round(time.time()-start,1),'background':'white shadow catcher','blender_version':bpy.app.version_string}
    (ROOT/'outputs/blender-white-result.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True)
except Exception:
    (ROOT/'outputs/blender-white-result.json').write_text(json.dumps({'status':'failed','error':traceback.format_exc()}),encoding='utf8');raise
