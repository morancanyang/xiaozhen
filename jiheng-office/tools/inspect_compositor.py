import bpy
s=bpy.context.scene;t=bpy.data.node_groups.new('Debug','CompositorNodeTree');n=t.nodes.new('CompositorNodeConvertToDisplay');print('PROPS',[(p.identifier,p.is_readonly) for p in n.view_settings.bl_rna.properties],flush=True);print('SOCKETS',[(i.name,i.bl_idname) for i in n.inputs],flush=True)
