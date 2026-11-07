import {createShanghaiTower} from './shanghai-tower-module.mjs';

/** Explicit call only. This file does not modify the current town automatically. */
export function createTownLandmark({THREE,cityRoot,centerX,centerZ,groundY=.34,rotationY=0}){
  const landmark=createShanghaiTower({THREE,footprint:112,displayHeight:96,seed:632,quality:'high',includeLandscape:true});
  landmark.model.position.set(centerX,groundY,centerZ);
  landmark.model.rotation.y=rotationY;
  cityRoot.add(landmark.model);
  return {
    landmark,
    update(dt,host){
      landmark.update(host.paused?0:dt*(host.speed??1),{time:host.time,paused:host.paused,nightFactor:host.nightFactor??.25,wind:host.wind,people:host.people,lights:host.lights,cameraDistance:host.cameraDistance});
    },
    setQuality:landmark.setQuality,
    dispose:landmark.dispose
  };
}
