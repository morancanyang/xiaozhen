import {createSportsField} from './model.mjs';

/** Mount within a city parcel; the host owns the renderer, camera and frame loop. */
export function mountSportsField({THREE,scene,x=0,z=0,groundY=0,blockSize=112,rotationY=0,quality='medium'}={}){
  if(!scene?.add)throw new Error('A host THREE.Scene is required');
  const model=createSportsField({THREE,blockSize,quality});
  model.root.position.set(x,groundY,z);
  model.root.rotation.y=rotationY;
  scene.add(model.root);
  return model;
}

/** Optional lighting adapter: light positions follow parcel scaling and rotation. */
export function attachSportsFloodlights({THREE,scene,model}){
  model.root.updateWorldMatrix(true,false);
  const scale=model.root.getWorldScale(new THREE.Vector3()).x;
  const lights=model.manifest.lightFixtures.map(f=>{
    const light=new THREE.SpotLight(0xffedcf,0,130*scale,.65,.65,2);
    light.position.copy(model.root.localToWorld(new THREE.Vector3(...f.position)));
    light.target.position.copy(model.root.localToWorld(new THREE.Vector3(...f.target)));
    scene.add(light,light.target);
    return light;
  });
  return {
    setNight(night){
      model.setTimeOfDay(night?'night':'day');
      lights.forEach(light=>light.intensity=night?3600*scale*scale:0);
    },
    dispose(){lights.forEach(light=>{light.removeFromParent();light.target.removeFromParent();light.dispose();});},
    lights
  };
}
