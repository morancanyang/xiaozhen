const fs=require('fs'),path=require('path'),esbuild=require('esbuild');
const root=__dirname;
const bundle=esbuild.buildSync({entryPoints:[path.join(root,'src/app.js')],bundle:true,write:false,format:'iife',target:'es2022',minify:true,legalComments:'inline'}).outputFiles[0].text;
const html=fs.readFileSync(path.join(root,'src/shell.html'),'utf8').replace('__STYLE__',()=>fs.readFileSync(path.join(root,'src/style.css'),'utf8')).replace('__APP__',()=>bundle.replace(/<\/script/gi,'<\\/script'));
fs.writeFileSync(path.join(root,'浅序住区.html'),html);fs.writeFileSync(path.join(root,'dist/index.html'),html);
fs.copyFileSync(path.join(root,'src/model.js'),path.join(root,'residential-block.mjs'));
console.log('Self-contained HTML: '+Buffer.byteLength(html)+' bytes');
