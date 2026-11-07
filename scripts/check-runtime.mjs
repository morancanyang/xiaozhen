import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../city-atlas/dist'),seen=new Set();
function visit(file){
 if(seen.has(file))return;seen.add(file);
 if(!fs.existsSync(file))throw new Error('Missing runtime module: '+path.relative(root,file));
 const text=fs.readFileSync(file,'utf8');
 for(const match of text.matchAll(/(?:\bfrom\s*|\bimport\s*\()\s*['"]([^'"]+)['"]/g)){
  const name=match[1];let target;
  if(name==='three')target=path.join(root,'vendor/three.module.js');
  else if(name.startsWith('three/addons/'))target=path.join(root,'vendor/addons',name.slice(13));
  else if(name.startsWith('.'))target=path.resolve(path.dirname(file),name);
  else continue;
  if(/\.m?js$/.test(target))visit(target);
 }
}
visit(path.join(root,'main.js'));
if(!fs.existsSync(path.join(root,'vendor/THREE-LICENSE.txt')))throw new Error('Missing Three.js license');
console.log('Runtime module closure verified: '+seen.size+' local modules');
