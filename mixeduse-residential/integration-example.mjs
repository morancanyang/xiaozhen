import {createMixedUseResidential} from './mixeduse-module.mjs';
/** Host supplies its own THREE, scene and animation delta. No renderer is created. */
export function attachMixedUse({THREE,cityRoot,block,groundY=.34,quality='medium'}){
 const model=createMixedUseResidential({THREE,footprint:block.size||112,quality,seed:1105});
 model.root.position.set(block.x,groundY,block.z);model.root.userData.blockId=block.id;cityRoot.add(model.root);
 return {model,update(delta,state={}){model.update(delta,{paused:!!state.paused,wind:state.wind!==false,windStrength:state.windStrength??.45,nightFactor:state.nightFactor??0,doors:state.doors!==false});},dispose(){model.dispose();}};
}
