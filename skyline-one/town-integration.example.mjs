import {createSkylineTower} from './skyline-module.mjs';

/** Host owns THREE, lighting, environment, RAF and the selected parcel's old contents. */
export function installSkyline({THREE,cityRoot,centerX,centerZ,groundY=0,rotationY=0,blockSize=112}){
  const tower=createSkylineTower({THREE,blockSize,quality:'high',embedded:true,seed:1101});
  tower.root.position.set(centerX,groundY,centerZ);
  tower.root.rotation.y=rotationY;
  cityRoot.add(tower.root);
  tower.root.updateMatrixWorld(true);
  function worldPoint(nativePoint){return tower.root.localToWorld(new THREE.Vector3(...nativePoint));}
  // Excavation is a rectangle in module space. Transform all four corners when yaw is nonzero.
  const cut=tower.manifest.excavations[0];
  const excavationCorners=[
    [cut.min[0],0,cut.min[2]],[cut.max[0],0,cut.min[2]],
    [cut.max[0],0,cut.max[2]],[cut.min[0],0,cut.max[2]]
  ].map(worldPoint);
  return {
    tower,excavationCorners,
    entrances:Object.fromEntries(Object.entries(tower.manifest.entrances).map(([id,e])=>[id,{...e,worldPosition:worldPoint(e.position)}])),
    update(delta,host){
      tower.setDynamicsEnabled(!host.paused);
      tower.setActivity({traffic:host.traffic,wind:host.wind,flight:host.flight??true});
      tower.setTimeOfDay(host.nightFactor??host.timeOfDay??'morning');
      const q={cinema:'high',balanced:'medium',fast:'low'}[host.quality]||host.quality||'high';
      if(tower.quality!==q)tower.setQuality(q);
      tower.update(delta*(host.speed??1));
    },
    dispose:()=>tower.dispose()
  };
}
