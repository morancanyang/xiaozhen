import {createUniversityCampus} from './university-module.mjs';

/** Call this with a host-owned THREE namespace, scene and selected block. */
export function mountUniversityCampus({THREE,scene,block,quality='high'}){
  if(!THREE||!scene||!block)throw new Error('需要 THREE、scene、block');
  const size=block.size??112;
  const campus=createUniversityCampus({THREE,footprint:size,quality,includeLandscape:true});
  campus.model.position.set(block.x??0,block.groundY??.3,block.z??0);
  campus.model.name=block.id?`${block.id}_UNIVERSITY`:'UNIVERSITY_CAMPUS';
  campus.model.userData.blockId=block.id??null;
  scene.add(campus.model);
  // The host retains its camera, renderer, environment and single animation loop.
  return {
    campus,
    update(deltaTime,state={}){
      campus.update(deltaTime*(state.speed??1),{
        paused:!!state.paused,
        wind:state.wind!==false,
        windStrength:state.windStrength??.6,
        flags:state.flags!==false,
        lights:state.lights!==false,
        nightFactor:state.nightFactor??0,
        cameraDistance:state.cameraDistance
      });
    },
    dispose:()=>campus.dispose()
  };
}
