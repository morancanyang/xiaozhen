import * as THREE from 'three';
import {createRiver} from './river-model.js';
import {createRiverPass} from './river-pass.js';

export const RIVER_SITE=Object.freeze({id:'RIVER-QINGLAN',minX:-32,maxX:32,minZ:-300,maxZ:300,width:64,length:600});
export function installRiver(city){
 const c=city.plan.corridor,s=RIVER_SITE;if(c.minX!==s.minX||c.maxX!==s.maxX||c.minZ!==s.minZ||c.maxZ!==s.maxZ)throw new Error('城市河道范围不一致');
 const river=createRiver({THREE,quality:'medium'});river.root.name=s.id;river.root.userData={moduleId:'qinglan-river',cityModule:true,landscape:true};city.root.add(river.root);
 Object.assign(c,{type:'natural-river',name:'青岚河',moduleId:'qinglan-river',waterLevel:river.manifest.waterLevel,bankLevel:river.manifest.bankLevel});
 const pass=createRiverPass({THREE,river}),exportScene=river.exportScene,dispose=river.dispose;
 river.exportScene=()=>{const q=river.quality,visible=river.root.visible;river.root.visible=true;river.setQuality('high');try{return exportScene();}finally{river.setQuality(q);river.root.visible=visible;}};
 river.dispose=()=>{pass.dispose();dispose();};city.root.updateMatrixWorld(true);return{river,pass,site:s};
}
