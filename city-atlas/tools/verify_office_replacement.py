"""Focused check: export a temporary user replacement without reviving original meshes."""
import json
import struct
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/office-integration'
OUT.mkdir(parents=True,exist_ok=True)

with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-webgl','--enable-unsafe-swiftshader'])
    page=browser.new_page(viewport={'width':1280,'height':900},accept_downloads=True)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    # This focused upload/export test suspends pixel rendering; actual city renders
    # are checked separately by verify_office_integration.py. UI/model/export code is unchanged.
    source=(ROOT/'dist/main.js').read_text(encoding='utf8').replace("$('#viewport').appendChild(renderer.domElement);","$('#viewport').appendChild(renderer.domElement);renderer.render=()=>{};",1)
    page.route('**/main.js',lambda route:route.fulfill(status=200,content_type='application/javascript',body=source))
    page.goto('http://127.0.0.1:5173',wait_until='networkidle')
    page.wait_for_function('window.cityApp?.ready',polling=100,timeout=120000)
    binary=page.evaluate('''async()=>{
      const T=await import('three'),{GLTFExporter}=await import('three/addons/exporters/GLTFExporter.js');
      const material=new T.MeshStandardMaterial({color:0x3b7468,roughness:.7});material.name='ReplacementMarkerMaterial';
      const cube=new T.Mesh(new T.BoxGeometry(2,2,2),material);cube.name='ReplacementMarker';
      const data=await new GLTFExporter().parseAsync(cube,{binary:true});
      cube.geometry.dispose();material.dispose();return Array.from(new Uint8Array(data));
    }''')
    marker=OUT/'replacement-marker.glb'
    marker.write_bytes(bytes(binary))
    page.evaluate("cityApp.select('JIHENG-ONE');window.replacementOriginal=cityApp.office.root.children.map(o=>({object:o,name:o.name,visible:o.visible}));")
    page.locator('#model-file').set_input_files(marker)
    page.wait_for_function("!!cityApp.office.root.getObjectByName('ReplacementMarker')",polling=100,timeout=45000)
    before=page.evaluate("({hidden:replacementOriginal.every(s=>!s.object.visible),states:replacementOriginal.map(s=>s.object.visible),names:replacementOriginal.map(s=>s.name).filter(Boolean),quality:cityApp.office.quality})")
    page.locator('#quality').select_option('fast')
    low=page.evaluate("({quality:cityApp.office.quality,hidden:replacementOriginal.every(s=>!s.object.visible)})")
    page.locator('#quality').select_option('balanced')
    balanced=page.evaluate("({quality:cityApp.office.quality,hidden:replacementOriginal.every(s=>!s.object.visible)})")
    snapshot=page.evaluate("(()=>{const m=cityApp.exportCity('JIHENG-ONE').modules.find(m=>m.id==='jiheng-landmark-office');return {objects:m.snapshot.objects.length,materials:[...new Set(m.snapshot.objects.map(o=>m.snapshot.materials[o.m].name))],hidden:replacementOriginal.every(s=>!s.object.visible),quality:cityApp.office.quality}})()")
    with page.expect_download(timeout=120000) as result:
        page.locator('#export-building').click()
    exported=OUT/'JIHENG-ONE-replacement.glb'
    result.value.save_as(exported)
    raw=exported.read_bytes()
    assert raw[:4]==b'glTF'
    size=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+size])
    names=[node.get('name','') for node in doc['nodes']]
    materials=[material.get('name','') for material in doc.get('materials',[])]
    after=page.evaluate("({states:replacementOriginal.map(s=>s.object.visible),quality:cityApp.office.quality,marker:!!cityApp.office.root.getObjectByName('ReplacementMarker')})")
    page.locator('#restore-building').click()
    restored=page.evaluate("({markerAbsent:!cityApp.office.root.getObjectByName('ReplacementMarker'),originalVisible:replacementOriginal.every(s=>s.object.visible),originalCount:replacementOriginal.length,quality:cityApp.office.quality})")
    checks={
        'upload_hides_original_landmark':before['hidden'],
        'low_quality_keeps_original_hidden':low['quality']=='low' and low['hidden'],
        'balanced_quality_keeps_original_hidden':balanced['quality']=='medium' and balanced['hidden'],
        'json_force_high_exports_only_replacement':snapshot['objects']==1 and snapshot['materials']==['ReplacementMarkerMaterial'] and snapshot['hidden'] and snapshot['quality']=='medium',
        'selected_glb_keeps_replacement': 'ReplacementMarker' in names,
        'selected_glb_excludes_original_mesh_names':not any(name in names for name in before['names']),
        'selected_glb_contains_only_marker_material':materials==['ReplacementMarkerMaterial'],
        'export_preserves_hidden_original_states':before['states']==after['states'],
        'export_restores_current_quality':before['quality']==after['quality'],
        'export_preserves_runtime_replacement':after['marker'],
        'restore_removes_marker_and_restores_original':restored['markerAbsent'] and restored['originalVisible'] and restored['originalCount']>0,
        'no_script_or_webgl_errors':not errors,
    }
    report={'checks':checks,'errors':errors,'glb_nodes':names,'glb_materials':materials,'glb_bytes':len(raw),'original_mesh_count':len(before['names']),'quality_before':before['quality'],'quality_after':after['quality'],'json_snapshot':snapshot,'restored':restored}
    (OUT/'replacement-verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=True),encoding='utf8')
    print(json.dumps(report,ensure_ascii=True),flush=True)
    browser.close()
    if not all(checks.values()):raise AssertionError('Replacement export check failed')
