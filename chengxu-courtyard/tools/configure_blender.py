from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'tools/blender_import.py';s=p.read_text(encoding='utf8').replace('Landmark office model only','Residential courtyard model only')
s=s.replace("    origin = np.array(parent.location)","    bpy.context.view_layer.update()\n    origin = np.array(parent.matrix_world.translation)")
start=s.index('views = {');end=s.index('for name, (position, target, fov) in views.items():',start)
s=s[:start]+"view_data = json.loads((ROOT/'outputs/viewer-views.json').read_text(encoding='utf8'))\nviews = {key.title(): (v['p'],v['q'],43) for key,v in view_data.items()}\n"+s[end:]
s=s.replace("{'Overview':244,'Front':222,'Top':146}[name]","view_data[name.lower()]['span']")
s=s.replace("cv([0,72,0])","cv([0,25,0])").replace("scene['height_m'] = 184","scene['height_m'] = 78")
p.write_text(s,encoding='utf8')
p=ROOT/'tools/render_blender.py';s=p.read_text(encoding='utf8').replace('space.region_3d.view_location=(0,0,85)','space.region_3d.view_location=(0,0,28)').replace('space.region_3d.view_distance=300','space.region_3d.view_distance=200').replace("['Overview','Front','Top','Low','Entrance','Terrace','Roof']","['Overview','Front','Top','Low','Entrance','Garden','Roof']").replace("['lamp','office-lit','sign-','obstruction']","['lamp','window-lit','sign-']")
s=s.replace('            # White studio master. Reflections keep the physical sky while camera background is white.', '''            # Blender 5.2 compositor: retain AgX shading over a truly white background.
            scene.render.film_transparent=True;bpy.data.objects['Backdrop'].is_shadow_catcher=True
            bpy.data.objects['Afternoon atmosphere'].hide_render=True
            tree=bpy.data.node_groups.new('White studio composite','CompositorNodeTree')
            tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
            output=tree.nodes.new('NodeGroupOutput');rl=tree.nodes.new('CompositorNodeRLayers');rl.scene=scene
            display=tree.nodes.new('CompositorNodeConvertToDisplay');display.view_settings.view_transform='AgX';display.view_settings.look='AgX - Medium High Contrast'
            over=tree.nodes.new('CompositorNodeAlphaOver');over.inputs['Factor'].default_value=1;over.inputs['Background'].default_value=(1,1,1,1)
            tree.links.new(rl.outputs['Image'],display.inputs['Image']);tree.links.new(display.outputs['Image'],over.inputs['Foreground']);tree.links.new(over.outputs[0],output.inputs['Image']);scene.compositing_node_group=tree
            scene.view_settings.view_transform='Raw';scene.view_settings.look='None';scene.view_settings.exposure=0
            scene.render.filepath=str(ROOT/'outputs/blender-white.png');bpy.ops.render.render(write_still=True)
            rendered.append({'view':'White studio','resolution':[1800,1200]})''')
s=s.replace("print('OFFICE_RENDER_COMPLETE'","print('COURTYARD_RENDER_COMPLETE'")
p.write_text(s,encoding='utf8')
