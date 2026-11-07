import {createAmusementPark} from './amusement-park-module.mjs';
export function mountAmusementPark({THREE,scene,block,quality='medium'}){
 if(!THREE||!scene||!block)throw new Error('THREE, scene and block are required');
 const park=createAmusementPark({THREE,footprint:block.size??112,quality});
 park.model.position.set(block.x??0,block.groundY??.36,block.z??0);
 park.model.userData.blockId=block.id??null;scene.add(park.model);
 return {park,update:(dt,state={})=>park.update(dt,{paused:state.paused,speed:state.speed??1,wind:state.wind,windStrength:state.windStrength??.6,nightFactor:state.nightFactor??0,rides:state.rides,lights:state.lights}),dispose:()=>park.dispose()};
}
