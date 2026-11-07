import {createQuietCityPark} from './quiet-park-module.mjs';
export function mountQuietPark({THREE,scene,block,quality='medium'}){
 if(!THREE||!scene||!block)throw new Error('THREE, scene and block required');
 const park=createQuietCityPark({THREE,footprint:block.size??112,quality});
 park.model.position.set(block.x??0,block.groundY??0,block.z??0);park.model.userData.blockId=block.id??null;
 // Before mounting, the host must remove the parcel's original surface/soil across
 // this terrain volume; otherwise the existing ground can fill the actual lake basin.
 scene.add(park.model);
 return{park,update:(dt,state={})=>park.update(dt,{paused:state.paused,speed:state.speed??1,wind:state.wind,windStrength:state.windStrength??.35,water:state.water,lights:state.lights,nightFactor:state.nightFactor??0}),dispose:()=>park.dispose()};
}
