const fs=require('fs'),path=require('path');
let esbuild;try{esbuild=require('esbuild');}catch{esbuild=require('esbuild');}
const root=__dirname;
const result=esbuild.buildSync({entryPoints:[path.join(root,'src/app.js')],bundle:true,write:false,format:'iife',target:'es2022',minify:true,nodePaths:[path.resolve(root,'../city-atlas/node_modules')],legalComments:'inline'});
const html=fs.readFileSync(path.join(root,'src/shell.html'),'utf8').replace('__STYLE__',()=>fs.readFileSync(path.join(root,'src/style.css'),'utf8')).replace('__APP__',()=>result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script'));
fs.writeFileSync(path.join(root,'云际中心.html'),html);
fs.copyFileSync(path.join(root,'src/tower-model.js'),path.join(root,'skyline-module.mjs'));
console.log('Offline single HTML:',Buffer.byteLength(html),'bytes');
