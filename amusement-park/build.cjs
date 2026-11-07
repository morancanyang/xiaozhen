const fs=require('node:fs'),path=require('node:path');
let esbuild;try{esbuild=require('esbuild');}catch{esbuild=require('esbuild');}
const root=__dirname,nodePaths=[path.resolve(root,'../city-atlas/node_modules')];
const bundle=entry=>esbuild.buildSync({entryPoints:[path.join(root,entry)],bundle:true,write:false,format:'iife',target:'es2022',minify:true,nodePaths,legalComments:'inline'}).outputFiles[0].text.replace(/<\/script/gi,'<\\/script');
const html=fs.readFileSync(path.join(root,'src/shell.html'),'utf8').replace('__STYLE__',()=>fs.readFileSync(path.join(root,'src/style.css'),'utf8')).replace('__APP__',()=>bundle('src/app.js'));
fs.writeFileSync(path.join(root,'晴空游乐园.html'),html);fs.copyFileSync(path.join(root,'src/model.js'),path.join(root,'amusement-park-module.mjs'));fs.copyFileSync(path.join(root,'../city-atlas/node_modules/three/LICENSE'),path.join(root,'THREE-LICENSE.txt'));
console.log('Offline HTML:',Buffer.byteLength(html),'bytes');

fs.writeFileSync(path.join(root,"接入演示.html"),`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>晴空游乐园 · 宿主接入演示</title><style>body{margin:0;overflow:hidden;background:#e1e1d8}canvas{display:block}#status{position:absolute;bottom:24px;left:24px;right:24px;background:#f5f6efeb;padding:16px;color:#3f524e;font:12px sans-serif;pointer-events:none}</style><div id="status">正在通过宿主接口载入大学模型…</div><script>${bundle("src/demo.js")}</script></html>`);
