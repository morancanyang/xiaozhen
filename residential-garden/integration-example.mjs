import {createResidential} from './model.mjs';
export function mountResidential({THREE,scene,x=0,z=0,groundY=0,blockSize=112,rotationY=0,quality='medium'}={}){
 const model=createResidential({THREE,blockSize,quality});model.root.position.set(x,groundY,z);model.root.rotation.y=rotationY;scene.add(model.root);return model;
}
