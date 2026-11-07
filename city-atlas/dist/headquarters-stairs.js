/** Closed steps, real ramps and continuous switchback escape stairwells. */
export function createStairs(c){
 const {THREE,group,part,box,beam,coarse,manifest}=c;
 manifest.stairs={external:[],internal:[],riserMax:0,treadMin:.27};
 function entrance(id,x,z,front){const owner=id+'-entrance';
  box('paving',x+.9,.12,front+3.5,14,.24,7.6,owner);
  // Path .24 -> lobby .69 in three equal, solid 150mm rises.
  box('stair-stone',x,.465,front+2.6,12,.45,5.2,owner);
  for(let n=0;n<3;n++){const top=.39+n*.15,zz=front+6.2-n*.4;box('stair-stone',x,(.24+top)/2,zz,12,top-.24,.4,owner);box('trim',x,top-.018,zz+.195,12,.036,.035,owner,1);for(let k=0;k<3;k++)box('stair-inlay',x,top+.001,zz+.12-k*.032,11.7,.003,.009,owner,2)}
  for(const sx of [-1,1]){const xx=x+sx*5.6;beam('metal',[xx,.39+.95,front+6.35],[xx,.69+.95,front+5.2],.042,owner,1);beam('metal',[xx,1.64,front+5.2],[xx,1.64,front+.6],.042,owner,1);for(const zz of [front+.6,front+2.4,front+4.2,front+5.2])box('metal',xx,1.15,zz,.045,.98,.045,owner,1)}
  // Wedge ramp: 450mm rise over 5.4m run, clear width 1.8m.
  const rx=x+6.9,near=front+.2,far=front+5.6,points=[[rx-.9,.24,far],[rx+.9,.24,far],[rx-.9,.69,near],[rx+.9,.69,near],[rx-.9,.24,near],[rx+.9,.24,near]],idx=[0,1,2,1,3,2,0,2,4,1,5,3,2,3,4,3,5,4,0,4,1,1,4,5];
  c.custom('Access ramp 1:12',points,idx,'stair-stone',owner);
  for(const sx of [-1,1]){const xx=rx+sx*.84;beam('metal',[xx,1.19,far],[xx,1.64,near],.042,owner,1);for(let k=0;k<=4;k++){const zz=near+k*1.35,y=.69-k*.1125;box('metal',xx,y+.47,zz,.04,.94,.04,owner,1)}}
  box('stair-stone',rx,.465,front-.2,1.8,.45,.8,owner);box('stair-stone',x+5.6,.465,front+.2,2.6,.45,1.6,owner);
  if(!coarse)for(let a=0;a<30;a++)for(let b=0;b<3;b++)part('cyl','stair-inlay',[x-4.35+a*.3,.249,front+7.1+b*.12],[.035,.015,.035],0,owner,2);
  manifest.stairs.external.push({building:id,steps:3,riser:.15,tread:.4,bottom:.24,landing:.69,ramp:{rise:.45,run:5.4,width:1.8,slope:'1:12'}});
 }
 function internal(id,x,z,floors,roofY){const owner=id+'-stairs';group(owner,(id==='main'?'主楼':'辅楼')+' · 连续疏散楼梯',c.groups.get(id),[0,0,0],id);
  const cx=x-3,cz=z-3;
  for(let floor=0;floor<floors;floor++){
   const base=floor===0?.69:4.8+(floor-1)*4+.27,top=floor===floors-1?roofY+.09:4.8+floor*4+.27,rise=top-base,n=14,rs=rise/(2*n),run=n*.27;
   manifest.stairs.riserMax=Math.max(manifest.stairs.riserMax,rs);
   if(floor===0)box('stair-stone',cx,base-.09,cz-2.82,4.4,.18,1.14,owner);
   for(let flight=0;flight<2;flight++){
    const side=flight===0?-1:1,xx=cx+side*1.18,start=flight===0?cz-2.25:cz+1.53,dir=flight===0?1:-1,y0=base+flight*rise/2;
    if(coarse){c.slabSlope(owner,xx,y0,start,dir,run,rise/2,1.8);continue}
    for(let k=0;k<n;k++){const yy=y0+(k+1)*rs,zz=start+dir*(k+.5)*.27;box('stair-stone',xx,yy-rs/2,zz,1.8,rs,.27,owner);box('trim',xx,yy-.012,zz+dir*.131,1.8,.024,.027,owner,1);for(let j=0;j<2;j++)box('stair-inlay',xx,yy+.001,zz+dir*(.08-j*.035),1.65,.003,.008,owner,2)}
    c.slabSlope(owner,xx,y0-.15,start,dir,run,rise/2,1.9);
    for(const sx of [-1,1]){const rx=xx+sx*.83;beam('metal',[rx,y0+rs+.95,start+dir*.135],[rx,y0+rise/2+.95,start+dir*(run-.135)],.04,owner,1);for(let k=0;k<n;k+=3){const yy=y0+(k+1)*rs,zz=start+dir*(k+.5)*.27;box('metal',rx,yy+.46,zz,.035,.92,.035,owner,1)}}
   }
   box('stair-stone',cx,base+rise/2-.09,cz+2.1,4.4,.18,1.14,owner);
   box('stair-stone',cx,top-.09,cz-2.82,4.4,.18,1.14,owner);
   box('stair-inlay',cx,base+rise/2-.13,cz+2.63,4.3,.08,.04,owner,1);
   if(!coarse)for(const [zz,yy] of [[cz+2.63,base+rise/2],[cz-3.35,top]]){beam('metal',[cx-2.12,yy+.95,zz],[cx+2.12,yy+.95,zz],.04,owner,1);for(const dx of [-2.1,-.7,.7,2.1])box('metal',cx+dx,yy+.46,zz,.035,.92,.035,owner,1)}
  }
  manifest.stairs.internal.push({building:id,flights:floors*2,levels:floors,clearWidth:1.8,tread:.27,firstLanding:.69,roofLanding:roofY+.09});
 }
 return{entrance,internal};
}
