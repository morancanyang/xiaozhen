import { createHospital } from './hospital-module.mjs';

/** Call from the town app. The hospital owns no camera, renderer, lights or RAF. */
export async function installHospital({THREE,scene,parcel,siteAdapter,quality='high'}) {
  const module=createHospital({THREE,embedded:true,quality});
  // Choose the destination parcel in the town app before calling this helper.
  // prepareParcel should remove its old buildings/landscape and cut its underlying
  // ground where manifest.excavations specifies the real underground garage.
  if(typeof siteAdapter?.prepareParcel!=='function') {
    module.dispose();
    throw new Error('Provide siteAdapter.prepareParcel({ parcel, manifest }) to replace the chosen block and open the garage cutout.');
  }
  const prepared=await siteAdapter.prepareParcel({parcel,manifest:module.manifest});
  const groundY=prepared?.groundY??parcel.groundY??0;
  module.root.position.set(parcel.x,groundY,parcel.z);
  module.root.rotation.y=parcel.rotationY??0;
  scene.add(module.root);
  return {
    module,
    update(dt,elapsed){module.update(dt,elapsed);},
    setQuality(level){module.setQuality(level);},
    setTimeOfDay(value){module.setTimeOfDay(value);},
    setPaused(paused){module.setDynamicsEnabled(!paused);},
    dispose(){module.dispose();prepared?.dispose?.();}
  };
}

// Existing town animation loop:
// const installed=await installHospital({THREE,scene,parcel:chosenBlock,siteAdapter});
// installed.update(dt,worldElapsed);
// The town's renderer.render(scene,camera) remains the only renderer call.
