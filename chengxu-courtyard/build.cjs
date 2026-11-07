const fs=require('fs'),path=require('path');
const local=path.join(__dirname,'node_modules');
const deps=fs.existsSync(path.join(local,'three/package.json'))?local:'D:/3D建模/现代居民楼/01a19528-018c-7023-86c7-cebff28a47b9/residential/node_modules';
let esbuild;try{esbuild=require('esbuild')}catch{esbuild=require(path.join(deps,'esbuild'))}
const result=esbuild.buildSync({entryPoints:[path.join(__dirname,'src/app.js')],bundle:true,write:false,format:'iife',target:'es2022',minify:true,nodePaths:[deps],legalComments:'inline'});
const html=fs.readFileSync(path.join(__dirname,'src/shell.html'),'utf8').replace('__STYLE__',()=>fs.readFileSync(path.join(__dirname,'src/style.css'),'utf8')).replace('__APP__',()=>result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script'));
fs.writeFileSync(path.join(__dirname,'澄序住区.html'),html);fs.copyFileSync(path.join(__dirname,'src/model.js'),path.join(__dirname,'model.mjs'));
fs.copyFileSync(path.join(deps,'three/LICENSE'),path.join(__dirname,'THREE-LICENSE.txt'));
console.log('Offline HTML:',Buffer.byteLength(html));
