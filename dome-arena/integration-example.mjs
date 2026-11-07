import {createArenaComplex} from './arena-module.mjs';

/** Attach one parcel to an existing town. The host supplies its THREE and frame loop. */
export function mountArena({THREE,scene,blockSize=112,center={x:0,z:0},groundY=0,rotationY=0,quality='high',fixtureLights=false}={}) {
  if (!scene?.add) throw new Error('A host scene or group is required');
  const arena=createArenaComplex({THREE,blockSize,quality,embedded:true});
  const parcel=new THREE.Group();parcel.name='Town arena parcel';
  parcel.position.set(center.x,groundY,center.z);parcel.rotation.y=rotationY;
  parcel.add(arena.root);scene.add(parcel);
  const lights=[],scale=blockSize/112;
  if (fixtureLights) for (const f of arena.manifest.lightFixtures) {
    const light=new THREE.SpotLight(0xcbe9ff,0,150*scale,.58,.65,2);
    light.position.fromArray(f.position).multiplyScalar(scale);
    light.target.position.fromArray(f.target).multiplyScalar(scale);
    light.userData.nightPower=2200*scale*scale;
    // Host owns shadow policy. Four extra shadow maps are disabled by default.
    light.castShadow=false;parcel.add(light,light.target);lights.push(light);
  }
  let disposed=false;
  return {
    parcel,arena,manifest:arena.manifest,
    update(deltaSeconds){if(!disposed)arena.update(deltaSeconds);},
    setNight(amount=0){
      const v=THREE.MathUtils.clamp(amount,0,1);arena.setTimeOfDay(v);
      lights.forEach(l=>l.intensity=l.userData.nightPower*v);
    },
    entryWorld(id='public'){
      const entry=arena.manifest.entrances[id];if(!entry)throw new Error('Unknown entrance: '+id);
      parcel.updateWorldMatrix(true,true);
      return arena.root.localToWorld(new THREE.Vector3(...entry.position));
    },
    dispose(){if(disposed)return;disposed=true;arena.dispose();lights.forEach(l=>{l.shadow.dispose();l.removeFromParent();l.target.removeFromParent();});parcel.removeFromParent();parcel.clear();}
  };
}

// In the existing town's module:
// const arenaBlock=mountArena({THREE,scene,center:{x:blockX,z:blockZ},groundY:streetLevel,
//   blockSize:112,rotationY:0,fixtureLights:true});
// Call arenaBlock.update(deltaSeconds) from the existing animation loop.
// Call arenaBlock.setNight(0..1) from the town's existing day/night system.
// Remove the previous parcel content only after this model has loaded successfully.
