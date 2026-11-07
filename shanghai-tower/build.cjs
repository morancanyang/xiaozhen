const fs=require('node:fs'),path=require('node:path');
let esbuild;try{esbuild=require('esbuild');}catch{esbuild=require('esbuild');}
const root=__dirname;
const build=esbuild.buildSync({entryPoints:[path.join(root,'src/app.js')],bundle:true,write:false,format:'iife',target:'es2022',minify:true,nodePaths:[path.resolve(root,'../city-atlas/node_modules')],legalComments:'inline'});
const html=fs.readFileSync(path.join(root,'src/shell.html'),'utf8').replace('__STYLE__',()=>fs.readFileSync(path.join(root,'src/style.css'),'utf8')).replace('__APP__',()=>build.outputFiles[0].text.replace(/<\/script/gi,'<\\/script'));
fs.writeFileSync(path.join(root,'上海中心.html'),html);
fs.copyFileSync(path.join(root,'src/model.js'),path.join(root,'shanghai-tower-module.mjs'));
fs.copyFileSync(path.join(root,'../city-atlas/node_modules/three/LICENSE'),path.join(root,'THREE-LICENSE.txt'));
const demo=esbuild.buildSync({entryPoints:[path.join(root,'src/demo.js')],bundle:true,write:false,format:'iife',target:'es2022',minify:true,nodePaths:[path.resolve(root,'../city-atlas/node_modules')],legalComments:'inline'});
fs.writeFileSync(path.join(root,'接入演示.html'),'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22/%3E"><title>上海中心 · 宿主接入演示</title><style>body{margin:0;overflow:hidden;background:#d9e3e6}canvas{display:block}#status{position:absolute;bottom:20px;left:20px;background:#19364be8;color:#e1edf1;padding:15px 20px;font:12px sans-serif;border-radius:4px}</style><div id="status">正在通过同源模型接口接入…</div><script>'+demo.outputFiles[0].text.replace(/<\/script/gi,'<\\/script')+'</script></html>');
console.log('Standalone HTML:',Buffer.byteLength(html),'bytes');
