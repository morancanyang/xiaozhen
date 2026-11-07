import * as THREE from 'three';

/** A drag-to-look flying camera. The host owns its render loop and mode changes. */
export function createFreeView({element,speedInput,speedLabel,altitudeLabel,movePad,lookPad,riseButtons}){
  let enabled=false,camera=null,speed=24,yaw=0,pitch=0,pinchDistance=0,readoutClock=0;
  const keys=new Set(),canvasPointers=new Map(),risePointers=new Map(),padPointers=new Map();
  const move=new THREE.Vector2(),look=new THREE.Vector2(),velocity=new THREE.Vector3(),forward=new THREE.Vector3(),right=new THREE.Vector3(),desired=new THREE.Vector3(),euler=new THREE.Euler(0,0,0,'YXZ'),up=new THREE.Vector3(0,1,0);
  const tracked=new Set(['KeyW','KeyA','KeyS','KeyD','KeyQ','KeyE','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','PageUp','PageDown','ShiftLeft','ShiftRight']);
  const cleanups=[];
  function on(target,type,listener,options){target.addEventListener(type,listener,options);cleanups.push(()=>target.removeEventListener(type,listener,options));}
  const editing=event=>!!event.target?.closest?.('input,select,textarea,[contenteditable="true"]')||!!document.querySelector('dialog[open]');
  element.tabIndex=0;
  function setSpeed(value){speed=THREE.MathUtils.clamp(Number(value)||1,1,120);speedInput.value=String(Math.round(speed));speedLabel.textContent=Math.round(speed)+' m/s';}
  function orient(){pitch=THREE.MathUtils.clamp(pitch,-Math.PI*.492,Math.PI*.492);camera.quaternion.setFromEuler(euler.set(pitch,yaw,0,'YXZ'));}
  function clampPosition(){camera.position.x=THREE.MathUtils.clamp(camera.position.x,-1600,1600);camera.position.z=THREE.MathUtils.clamp(camera.position.z,-1600,1600);camera.position.y=THREE.MathUtils.clamp(camera.position.y,.8,1200);}
  function dolly(distance){if(!enabled||document.querySelector('dialog[open]'))return;camera.getWorldDirection(forward);camera.position.addScaledVector(forward,distance);clampPosition();}
  function resetInput(){keys.clear();velocity.set(0,0,0);move.set(0,0);look.set(0,0);pinchDistance=0;canvasPointers.clear();risePointers.clear();padPointers.clear();for(const pad of [movePad,lookPad]){pad.querySelector('i').style.transform='translate(0px,0px)';pad.classList.remove('engaged');}riseButtons.forEach(b=>b.classList.remove('pressed'));element.classList.remove('is-looking');}
  function enter(nextCamera){camera=nextCamera;euler.setFromQuaternion(camera.quaternion,'YXZ');yaw=euler.y;pitch=euler.x;resetInput();enabled=true;element.focus({preventScroll:true});}
  function exit(){enabled=false;resetInput();}
  on(window,'keydown',event=>{if(!enabled||editing(event)||event.ctrlKey||event.metaKey||event.altKey||!tracked.has(event.code))return;event.preventDefault();keys.add(event.code);});
  on(window,'keyup',event=>keys.delete(event.code));
  on(window,'blur',resetInput);on(document,'visibilitychange',()=>{if(document.hidden)resetInput();});
  on(document,'focusin',event=>{if(enabled&&(editing(event)||event.target.closest?.('dialog')))resetInput();});
  on(element,'contextmenu',event=>{if(enabled)event.preventDefault();});
  on(element,'wheel',event=>{if(!enabled)return;event.preventDefault();if(!document.querySelector('dialog[open]'))setSpeed(speed*Math.exp(-event.deltaY*.0015));},{passive:false});
  on(element,'pointerdown',event=>{if(!enabled||event.button>2)return;event.preventDefault();element.focus({preventScroll:true});canvasPointers.set(event.pointerId,{x:event.clientX,y:event.clientY});element.setPointerCapture(event.pointerId);element.classList.add('is-looking');if(canvasPointers.size===2){const [a,b]=[...canvasPointers.values()];pinchDistance=Math.hypot(a.x-b.x,a.y-b.y);}});
  on(element,'pointermove',event=>{if(!enabled||!canvasPointers.has(event.pointerId))return;const old=canvasPointers.get(event.pointerId),dx=event.clientX-old.x,dy=event.clientY-old.y;canvasPointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
    if(canvasPointers.size===2){const [a,b]=[...canvasPointers.values()],distance=Math.hypot(a.x-b.x,a.y-b.y);if(pinchDistance)dolly((distance-pinchDistance)*.06*Math.max(1,speed/8));pinchDistance=distance;return;}
    yaw-=dx*.003;pitch-=dy*.003;orient();
  });
  function releaseCanvas(event){canvasPointers.delete(event.pointerId);pinchDistance=0;if(!canvasPointers.size)element.classList.remove('is-looking');}
  for(const type of ['pointerup','pointercancel','lostpointercapture'])on(element,type,releaseCanvas);
  for(const [pad,vector] of [[movePad,move],[lookPad,look]]){
    const knob=pad.querySelector('i');
    const updatePad=event=>{const rect=pad.getBoundingClientRect(),r=rect.width*.31;vector.set((event.clientX-rect.left-rect.width/2)/r,(event.clientY-rect.top-rect.height/2)/r);if(vector.length()>1)vector.normalize();knob.style.transform=`translate(${vector.x*r}px,${vector.y*r}px)`;};
    on(pad,'pointerdown',event=>{if(!enabled||padPointers.has(pad))return;event.preventDefault();event.stopPropagation();padPointers.set(pad,event.pointerId);pad.setPointerCapture(event.pointerId);pad.classList.add('engaged');updatePad(event);});
    on(pad,'pointermove',event=>{if(padPointers.get(pad)!==event.pointerId)return;event.preventDefault();updatePad(event);});
    const release=event=>{if(padPointers.get(pad)!==event.pointerId)return;padPointers.delete(pad);vector.set(0,0);knob.style.transform='translate(0px,0px)';pad.classList.remove('engaged');};
    for(const type of ['pointerup','pointercancel','lostpointercapture'])on(pad,type,release);
  }
  for(const button of riseButtons){
    on(button,'pointerdown',event=>{if(!enabled)return;event.preventDefault();event.stopPropagation();risePointers.set(event.pointerId,button.dataset.freeRise==='up'?1:-1);button.setPointerCapture(event.pointerId);button.classList.add('pressed');});
    const release=event=>{risePointers.delete(event.pointerId);button.classList.remove('pressed');};
    for(const type of ['pointerup','pointercancel','lostpointercapture'])on(button,type,release);
  }
  on(speedInput,'input',event=>setSpeed(event.target.value));
  function update(delta){if(!enabled)return;const dt=Math.min(.05,Math.max(0,delta));
    if(document.querySelector('dialog[open]')){resetInput();return;}
    yaw-=look.x*dt*1.7;pitch-=look.y*dt*1.3;orient();camera.getWorldDirection(forward);right.crossVectors(forward,up).normalize();
    const x=(keys.has('KeyD')||keys.has('ArrowRight')?1:0)-(keys.has('KeyA')||keys.has('ArrowLeft')?1:0)+move.x;
    const z=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0)-move.y;
    let y=(keys.has('KeyE')||keys.has('PageUp')?1:0)-(keys.has('KeyQ')||keys.has('PageDown')?1:0);for(const value of risePointers.values())y+=value;
    desired.set(0,0,0).addScaledVector(right,x).addScaledVector(forward,z).addScaledVector(up,y);if(desired.lengthSq()>1)desired.normalize();desired.multiplyScalar(speed*(keys.has('ShiftLeft')||keys.has('ShiftRight')?3:1));
    velocity.lerp(desired,1-Math.exp(-dt*12));camera.position.addScaledVector(velocity,dt);clampPosition();camera.updateMatrixWorld();
    readoutClock+=dt;if(readoutClock>.12){readoutClock=0;altitudeLabel.textContent=Math.round(camera.position.y)+' m';}
  }
  setSpeed(speed);return {enter,exit,update,dolly,setSpeed,resetInput,get enabled(){return enabled;},get speed(){return speed;},get heading(){return yaw;},dispose(){exit();cleanups.forEach(fn=>fn());}};
}
