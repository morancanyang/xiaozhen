/** Import in the host's existing module graph. No renderer or animation loop is created. */
import {createResidentialBlock} from './residential-block.mjs';

export function attachResidentialBlock({THREE,cityRoot,block,groundY=0.34,quality='medium'}) {
  if(!block || !(block.size>0)) throw new Error('A square city block with x/z/size is required');
  const asset=createResidentialBlock({THREE,footprint:block.size,quality,seed:1104});
  asset.root.position.set(block.x,groundY,block.z);
  asset.root.userData.blockId=block.id;
  cityRoot.add(asset.root);
  return {
    asset,
    update(delta,state={}) {
      // delta is already multiplied by the host speed. Apply it exactly once.
      asset.update(delta,{paused:!!state.paused,wind:state.wind!==false,windStrength:state.windStrength??.45,nightFactor:state.nightFactor??0});
    },
    dispose(){asset.dispose();}
  };
}
