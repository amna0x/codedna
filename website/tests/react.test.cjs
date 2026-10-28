const {test}=require('node:test');
const assert=require('node:assert/strict');
for(const page of ['index.html','docs.html','plugins.html','downloads.html']){
test('React pre-render preserves usable content for '+page,async()=>{
 const {render,metadata}=await import('../.render.mjs');
 const html=render(page);
 assert.equal((html.match(/<h1[ >]/g)||[]).length,1);
 assert.match(html,/id="main"/);
 assert.match(html,/aria-controls="primary-nav"/);
 assert.ok(metadata[page].title.includes('CodeDNA'));
 assert.equal(html.includes('dangerouslySetInnerHTML'),false);
});}
