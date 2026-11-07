import {createMallComplex} from './mall-module.mjs';

/** Explicitly call this adapter from the host. It never alters other parcels. */
export function mountMall({THREE,scene,parcelCenter={x:0,y:0,z:0},footprint=112,rotation=0}){
  const mall=createMallComplex({THREE,footprint,quality:'high',includeLandscape:true});
  mall.model.position.set(parcelCenter.x,parcelCenter.y??0,parcelCenter.z);
  mall.model.rotation.y=rotation;
  scene.add(mall.model);
  return mall;
}

// Host's existing loop: mall.update(deltaSeconds,{nightFactor:0,people:true,wind:true});
// Removal: mall.dispose(); Do not dispose the host renderer/environment.
