import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/office-integration'
html=(ROOT/'dist/index.html').read_text(encoding='utf8');imports=re.search(r'<script type="importmap">.*?</script>',html,re.S).group(0)
fixture=ROOT/'dist/__office-adapter.html';fixture.write_text('<!doctype html><meta charset="utf-8">'+imports,encoding='utf8')
try:
 with sync_playwright() as p:
  b=p.chromium.launch(channel='msedge',headless=True);page=b.new_page();page.goto('http://127.0.0.1:5173/__office-adapter.html')
  result=page.evaluate('''async()=>{
   const T=await import('three'),{buildCity}=await import('./city.js'),{installOffice}=await import('./office-site.js');const city=buildCity(new T.Scene()),before=city.plan.buildings.length,other=city.groups.size,previous={...city.plan.blocks.find(b=>b.id==='BLK-9')},a=installOffice(city),m=a.model;
   const checks={placement:m.root.position.equals(new T.Vector3(112,.34,-210)),registration:city.groups.get('JIHENG-ONE')===m.root&&city.plan.buildings.length===before+1,native_factory_no_camera:true,medium_light_budget:a.lights.filter(l=>l.visible).length===6};
   m.root.traverse(o=>{if(o.isCamera)checks.native_factory_no_camera=false});m.setQuality('high');checks.cinema_full_lights=a.lights.filter(l=>l.visible).length===16;m.setQuality('low');checks.fast_light_budget=a.lights.every(l=>!l.visible);m.setQuality('medium');m.setTimeOfDay(1);checks.night_power=a.lights.every(l=>l.intensity>0);m.setTimeOfDay(0);checks.day_power=a.lights.every(l=>l.intensity===0);
   m.root.visible=false;const snapshot=m.exportScene();checks.snapshot_geometry=snapshot.objects.length>10000&&snapshot.snapshotSpace==='world';checks.snapshot_restores_state=!m.root.visible&&m.quality==='medium'&&a.lights.filter(l=>l.visible).length===6;
   checks.parts_preserved=['lower','middle','upper','podium','roof','terraces','site','landscape','life'].every(id=>snapshot.objects.some(o=>o.owner===id));
   checks.grade_normals=a.connections.children.every(o=>o.geometry.attributes.normal.getY(0)>0);checks.world_geometry=snapshot.objects.some(o=>Math.abs(o.matrix[12]-112)<1e-6&&o.matrix[14]<-250);
   let duplicate=false;try{installOffice(city)}catch(e){duplicate=true}checks.duplicate_guard=duplicate;
   m.dispose();m.dispose();checks.clean_disposal=city.groups.size===other&&city.plan.buildings.length===before&&JSON.stringify(a.block)===JSON.stringify(previous)&&m.root.children.length===0;return checks;
  }''');(OUT/'adapter-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True);b.close()
  if not all(result.values()):raise AssertionError('Office adapter validation failed')
finally:fixture.unlink(missing_ok=True)
