import {createLandmarkOffice} from './model.mjs';
/** Host supplies its own THREE, Scene, renderer, camera and requestAnimationFrame. */
export function mountLandmarkOffice({THREE,scene,x=0,z=0,groundY=0,blockSize=112,rotationY=0,quality='medium'}={}){
 if(!scene?.add)throw new Error('Pass the host scene');
 const model=createLandmarkOffice({THREE,blockSize,quality});model.root.position.set(x,groundY,z);model.root.rotation.y=rotationY;scene.add(model.root);return model;
}
export function attachLandmarkLights({THREE,scene,model}){
 let night=0,disposed=false;const lights=model.manifest.lightFixtures.map(f=>{const o=new THREE.PointLight(f.color??0xffd5a0,0,f.distance??15,2);o.castShadow=false;scene.add(o);return o});
 function sync(){if(disposed)return;model.root.updateWorldMatrix(true,false);const scale=model.root.getWorldScale(new THREE.Vector3()).x;lights.forEach((light,i)=>{const f=model.manifest.lightFixtures[i];light.position.copy(model.root.localToWorld(new THREE.Vector3(...f.position)));light.distance=(f.distance??15)*scale;light.intensity=f.power*scale*scale*night})}
 sync();return{lights,sync,setNight(value){night=typeof value==='number'?THREE.MathUtils.clamp(value,0,1):value?1:0;model.setTimeOfDay(night);sync()},dispose(){if(disposed)return;disposed=true;lights.forEach(o=>{o.removeFromParent();o.dispose()})}};
}
