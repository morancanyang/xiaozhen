import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const three=path.join(root,'node_modules/three');
const destination=path.join(root,'dist/vendor');
fs.mkdirSync(destination,{recursive:true});
for(const name of ['three.module.js','three.core.js'])fs.copyFileSync(path.join(three,'build',name),path.join(destination,name));
fs.copyFileSync(path.join(three,'LICENSE'),path.join(destination,'THREE-LICENSE.txt'));
const visited=new Set();
function scan(file,isAddon=false){
  if(visited.has(file))return;visited.add(file);
  const contents=fs.readFileSync(file,'utf8');
  if(isAddon){const relative=path.relative(path.join(three,'examples/jsm'),file);const target=path.join(destination,'addons',relative);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(file,target);}
  for(const match of contents.matchAll(/(?:from\s*|import\s*)['"]([^'"]+)['"]/g)){
    const spec=match[1];
    if(spec.startsWith('three/addons/'))scan(path.join(three,'examples/jsm',spec.slice(13)),true);
    else if(isAddon&&spec.startsWith('.'))scan(path.resolve(path.dirname(file),spec),true);
  }
}
scan(path.join(root,'dist/main.js'));scan(path.join(root,'dist/city.js'));
console.log(`Vendored Three.js and ${visited.size-2} addon modules; runtime has no CDN dependency.`);
