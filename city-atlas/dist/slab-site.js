import * as THREE from 'three';
import {createResidentialBlock} from './slab-model.js';
export const SLAB_SITE=Object.freeze({blockId:'BLK-12',x:112,z:210,size:112,groundY:.34});
export function installSlab(city){
 const site=SLAB_SITE,block=city.plan.blocks.find(b=>b.id===site.blockId);
 if(!block||block.x!==site.x||block.z!==site.z)throw new Error('BLK-12 与浅序住区地块位置不一致');
 const model=createResidentialBlock({THREE,footprint:site.size,quality:'medium',seed:1104});
 const record={id:'QIANXU-RESIDENTIAL',name:'浅序住区',type:'现代板式住宅 · 三栋九单元',x:site.x,z:site.z,width:112,depth:112,height:66.2,floors:20,blockId:site.blockId,moduleId:'qianxu-slab-residential',groundY:site.groundY};
 // Descendant IDs describe source units; picking resolves to the city asset root.
 model.root.traverse(o=>{if(o!==model.root)delete o.userData.id;});
 model.root.name=record.id;model.root.position.set(site.x,site.groundY,site.z);Object.assign(model.root.userData,record,{cityModule:true});
 city.root.add(model.root);city.groups.set(record.id,model.root);city.plan.buildings.push(record);
 Object.assign(block,{name:record.name,type:'residential-complex',moduleId:record.moduleId});
 const dispose=model.dispose;model.dispose=()=>{city.groups.delete(record.id);dispose();};
 city.root.updateMatrixWorld(true);return{model,record,site,block};
}
