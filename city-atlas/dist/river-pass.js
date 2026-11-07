/** Planar reflection + refraction/depth buffers. Uses the host's renderer and scene. */
export function createRiverPass({THREE,river}={}){
 const makeRT=()=>new THREE.WebGLRenderTarget(768,512,{type:THREE.HalfFloatType});
 const reflection=makeRT(),refraction=makeRT();refraction.depthTexture=new THREE.DepthTexture(768,512,THREE.UnsignedIntType);
 const bias=new THREE.Matrix4().set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1),viewProjection=new THREE.Matrix4();
 const clip=new THREE.Plane(new THREE.Vector3(0,1,0),.75),lastPosition=new THREE.Vector3(1e9,1e9,1e9),lastQuaternion=new THREE.Quaternion();
 let mirror=null,frames=0,updates=0,disposed=false,width=0,height=0,quality='',lastCamera=null,lastUpdate=-1e9,skipped=0,phase=0,passesThisFrame=0;
 const frustum=new THREE.Frustum(),waterBox=new THREE.Box3();
 const uniforms=river.waterUniforms;
 function beforeRender(renderer,scene,camera,{sunDirection=null,sunColor=null,optimized=true,moving=false,now=performance.now()}={}){
  passesThisFrame=0;if(disposed||!river.root.visible)return;
  if(!optimized||scene.matrixWorldAutoUpdate)river.root.updateWorldMatrix(true,true);camera.updateMatrixWorld();uniforms.uEye.value.copy(camera.position);
  if(sunDirection)uniforms.uSun.value.copy(sunDirection).normalize();if(sunColor)uniforms.uSunColor.value.copy(sunColor);
  frames++;const q=river.quality,aspect=camera.isPerspectiveCamera?camera.aspect:Math.abs((camera.right-camera.left)/(camera.top-camera.bottom));
  const edge=optimized?(q==='high'?(moving?768:1280):q==='medium'?(moving?448:640):(moving?256:384)):(q==='high'?1280:q==='medium'?896:512);
  const w=Math.max(128,Math.round(edge*Math.min(1,aspect))),h=Math.max(128,Math.round(edge/Math.max(1,aspect)));
  if(optimized){
   viewProjection.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);frustum.setFromProjectionMatrix(viewProjection);
   if(!river.water.geometry.boundingBox)river.water.geometry.computeBoundingBox();waterBox.copy(river.water.geometry.boundingBox).applyMatrix4(river.water.matrixWorld).expandByScalar(1);
   if(!frustum.intersectsBox(waterBox)){skipped++;return;}
   const interval=q==='high'?(moving?100:80):q==='medium'?(moving?160:200):(moving?280:400);
   const changed=width!==w||height!==h||q!==quality||camera!==lastCamera;
   // Camera motion cannot bypass this budget: stale buffers retain their own matrices.
   if(!changed&&now-lastUpdate<(moving?interval/2:interval)){skipped++;return;}
  }else{
   const moved=camera.position.distanceToSquared(lastPosition)>.002||Math.abs(camera.quaternion.dot(lastQuaternion))<.999999,interval=q==='high'?3:q==='medium'?5:9;
   if(!moved&&frames%interval&&q===quality&&camera===lastCamera)return;
  }
  const reset=width!==w||height!==h||camera!==lastCamera||q!==quality||now-lastUpdate>1000;
  if(width!==w||height!==h){reflection.setSize(w,h);refraction.setSize(w,h);width=w;height=h;}
  lastUpdate=now;
  quality=q;lastCamera=camera;lastPosition.copy(camera.position);lastQuaternion.copy(camera.quaternion);
  if(!mirror||mirror.type!==camera.type)mirror=camera.clone();
  const level=river.root.localToWorld(new THREE.Vector3(0,river.manifest.waterLevel,0)).y;
  mirror.position.copy(camera.position);mirror.position.y=2*level-camera.position.y;
  const direction=camera.getWorldDirection(new THREE.Vector3());direction.y=-direction.y;mirror.up.copy(camera.up);mirror.up.y=-mirror.up.y;mirror.lookAt(mirror.position.clone().add(direction));mirror.near=camera.near;mirror.far=camera.far;mirror.projectionMatrix.copy(camera.projectionMatrix);mirror.projectionMatrixInverse.copy(camera.projectionMatrixInverse);mirror.updateMatrixWorld();

  clip.constant=-level;
  const current=renderer.getRenderTarget(),planes=renderer.clippingPlanes,shadowUpdate=renderer.shadowMap.autoUpdate,shadowDirty=renderer.shadowMap.needsUpdate,xr=renderer.xr.enabled,visible=river.water.visible;
  try{
   river.water.visible=false;renderer.xr.enabled=false;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=false;
   const split=optimized&&moving&&!reset&&uniforms.uHasBuffers.value>0;
   if(!split||phase===0){uniforms.uProjectionInverse.value.copy(camera.projectionMatrixInverse);uniforms.uCameraWorld.value.copy(camera.matrixWorld);viewProjection.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);uniforms.uRefractionMatrix.value.copy(viewProjection);renderer.clippingPlanes=[];renderer.setRenderTarget(refraction);renderer.clear();renderer.render(scene,camera);passesThisFrame++;}
   if(!split||phase===1){uniforms.uReflectionMatrix.value.copy(bias).multiply(mirror.projectionMatrix).multiply(mirror.matrixWorldInverse);renderer.clippingPlanes=[clip];renderer.setRenderTarget(reflection);renderer.clear();renderer.render(scene,mirror);passesThisFrame++;}
   if(split)phase=1-phase;
   uniforms.uReflection.value=reflection.texture;uniforms.uRefraction.value=refraction.texture;uniforms.uDepth.value=refraction.depthTexture;uniforms.uHasBuffers.value=1;updates++;
  }finally{renderer.setRenderTarget(current);renderer.clippingPlanes=planes;renderer.shadowMap.autoUpdate=shadowUpdate;renderer.shadowMap.needsUpdate=shadowDirty;renderer.xr.enabled=xr;river.water.visible=visible;}
 }
 function dispose(){if(disposed)return;disposed=true;reflection.dispose();refraction.dispose();uniforms.uHasBuffers.value=0;uniforms.uReflection.value=uniforms.uRefraction.value=uniforms.uDepth.value=null;}
 return{beforeRender,dispose,get metrics(){return{updates,width,height,quality,skipped,lastUpdate,passesThisFrame};},get disposed(){return disposed;}};
}
