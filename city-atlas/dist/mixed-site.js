import * as THREE from 'three';
import {createMixedUseResidential} from './mixed-model.js';
export const MIXED_SITE=Object.freeze({blockId:'BLK-15',x:252,z:70,size:112,groundY:.34});
export function installMixed(city){
 const site=MIXED_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
 if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-15 与棕屿里地块位置不一致');
 const model=createMixedUseResidential({THREE,footprint:site.size,quality:'medium',seed:1105});
 const record={id:'ZONGYU-RESIDENCES',name:'棕屿里',type:'高层住宅 · 沿街商业',x:site.x,z:site.z,width:112,depth:112,height:75.91,floors:23,blockId:site.blockId,moduleId:'zongyu-mixeduse',groundY:site.groundY};
 // Descendant IDs describe source units; picking resolves to the city asset root.
 model.root.traverse(o=>{if(o!==model.root)delete o.userData.id;});
 model.root.name=record.id;model.root.position.set(site.x,site.groundY,site.z);Object.assign(model.root.userData,record,{cityModule:true});
 city.root.add(model.root);city.groups.set(record.id,model.root);city.plan.buildings.push(record);
 Object.assign(block,{name:record.name,type:'residential-complex',moduleId:record.moduleId});
 const dispose=model.dispose;model.dispose=()=>{city.groups.delete(record.id);dispose();};
 city.root.updateMatrixWorld(true);return{model,record,site,block};
}
