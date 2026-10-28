import {build} from 'esbuild';
import {writeFile,mkdir,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
await mkdir('assets',{recursive:true});
await build({entryPoints:['src/client.jsx'],bundle:true,minify:true,format:'esm',outfile:'assets/app.js',define:{'process.env.NODE_ENV':'"production"'}});
await build({entryPoints:['src/render.jsx'],bundle:true,platform:'node',format:'esm',external:['react','react-dom/server'],outfile:'.render.mjs'});
const {render,metadata}=await import('./.render.mjs?'+Date.now());
const assetVersion=createHash('sha256').update(await readFile('assets/app.js')).digest('hex').slice(0,12);
const escape=s=>s.replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;');
for(const [file,meta] of Object.entries(metadata)){
await writeFile(file,`<!doctype html><html lang="en" id="top"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="${escape(meta.description)}"><title>${escape(meta.title)}</title><link rel="icon" href="assets/favicon.svg"><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="assets/app.css?v=${assetVersion}"></head><body class="${meta.className}" data-page="${file}"><div id="root">${render(file)}</div><noscript><p class="note">Interactive filters need JavaScript. Java and Python are bundled. <a href="catalogue/index.json">Read the catalogue</a>.</p></noscript><script type="module" src="assets/app.js?v=${assetVersion}"></script></body></html>`);
}
