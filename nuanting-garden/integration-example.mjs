import {createGardenHousing} from './model.mjs';

/** Mount one square parcel; the city owns its existing renderer, camera and frame loop. */
export function mountGardenHousing({THREE,scene,x=0,z=0,groundY=0,blockSize=112,rotationY=0,quality='medium'}={}){
  if(!scene?.add)throw new Error('A host THREE.Scene is required');
  const model=createGardenHousing({THREE,blockSize,quality});
  model.root.position.set(x,groundY,z);
  model.root.rotation.y=rotationY;
  scene.add(model.root);
  return model;
}

/** Optional actual point lights. Reuses host THREE and converts native manifest positions. */
export function attachGardenLights({THREE,scene,model}){
  let disposed=false,night=0;
  const lights=(model.manifest.lightFixtures||[]).map(f=>{
    const light=new THREE.PointLight(f.color??0xffd19b,0,f.distance??16,2);
    light.castShadow=false;scene.add(light);return light;
  });
  function sync(){
    if(disposed)return;
    model.root.updateWorldMatrix(true,false);
    const scale=model.root.getWorldScale(new THREE.Vector3()).x;
    lights.forEach((light,i)=>{
      const fixture=model.manifest.lightFixtures[i];
      light.position.copy(model.root.localToWorld(new THREE.Vector3(...fixture.position)));
      light.distance=(fixture.distance??16)*scale;
      light.intensity=(fixture.power??28)*scale*scale*night;
    });
  }
  sync();
  return {
    lights,sync,
    setNight(value){night=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value?1:0;model.setTimeOfDay(night);sync();},
    dispose(){if(disposed)return;disposed=true;lights.forEach(light=>{light.removeFromParent();light.dispose();});}
  };
}
