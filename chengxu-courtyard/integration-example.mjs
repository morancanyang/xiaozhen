import {createResidentialCourtyard} from './model.mjs';

/** Host owns renderer, camera, scene lights, RAF and surrounding municipal roads. */
export function mountResidentialCourtyard({THREE,scene,x=0,z=0,groundY=0,blockSize=112,rotationY=0,quality='medium'}={}) {
 const model=createResidentialCourtyard({THREE,blockSize,quality});
 model.root.position.set(x,groundY,z);model.root.rotation.y=rotationY;
 scene.add(model.root);return model;
}

/** Optional bounded light adapter. Native fixture locations remain in the manifest. */
export function attachCourtyardLights({THREE,scene,model,budget=4}={}) {
 const fixtures=model.manifest.lightFixtures.slice(0,Math.max(0,Math.min(8,Math.floor(budget))));
 const lights=fixtures.map(f=>{const l=new THREE.PointLight(0xffd8aa,0,1,2);l.name='Courtyard fixture';scene.add(l);return l});
 let night=0,disposed=false;
 function sync(){if(disposed)return;model.root.updateWorldMatrix(true,false);const scale=model.root.getWorldScale(new THREE.Vector3()).x;lights.forEach((l,i)=>{const f=fixtures[i];l.position.copy(model.root.localToWorld(new THREE.Vector3(...f.position)));l.distance=(f.distance||15)*scale;l.intensity=f.power*scale*scale*night})}
 function setNight(value){night=THREE.MathUtils.clamp(value,0,1);sync()}
 function dispose(){if(disposed)return;disposed=true;lights.forEach(l=>{l.removeFromParent();l.dispose()})}
 sync();return{lights,sync,setNight,dispose};
}
