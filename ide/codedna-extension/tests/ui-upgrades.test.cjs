const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');
const cp = require('node:child_process');
const { test, after } = require('node:test');
const ts = require('typescript');
function load(file, overrides = {}) {
  const source = fs.readFileSync(path.join(__dirname, '../src/', file), 'utf8');
  const code = ts.transpileModule(source, {compilerOptions: {module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.React,experimentalDecorators:true}}).outputText;
  const module = {exports:{}};
  vm.runInNewContext(code, {module,exports:module.exports,process,require(id) {
    if (id in overrides) return overrides[id];
    if (id.endsWith('/inversify')) return {injectable:()=>x=>x,inject:()=>()=>{},postConstruct:()=>()=>{}};
    if (id === 'child_process') return cp;
    if (['crypto','path','net'].includes(id)) return require(id);
    return {};
  }});
  return module.exports;
}
const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'codedna-ui-diff-'));
after(()=>fs.rmSync(folder,{recursive:true,force:true}));
const git = (...args)=>cp.execFileSync('git',['-C',folder,...args],{encoding:'utf8'}).trim();
git('init','--quiet');
fs.writeFileSync(path.join(folder,'Price.java'),'class Price { int total = 90; }\n');
git('add','.');git('-c','user.name=Test','-c','user.email=test@example.invalid','-c','commit.gpgsign=false','commit','--quiet','-m','before');
const revision=git('rev-parse','HEAD');
const Service=load('node/codedna-service-impl.ts').CodeDnaServiceImpl;
test('snapshot comparison reads committed content despite later working edits',async()=>{
  fs.writeFileSync(path.join(folder,'Price.java'),'working edit must remain untouched');
  const content=await new Service().snapshotFile(folder,revision,'Price.java');
  assert.match(content,/total = 90/);
  assert.equal(fs.readFileSync(path.join(folder,'Price.java'),'utf8'),'working edit must remain untouched');
});
test('snapshot reader rejects revisions and paths outside its immutable contract',async()=>{
  for(const [rev,file] of [['HEAD','Price.java'],[revision,'../secret'],[revision,'C:/secret'],[revision,'/secret'],[revision,'x\\secret']]) {
    await assert.rejects(new Service().snapshotFile(folder,rev,file),/Invalid snapshot/);
  }
});
test('snapshot missing files remain errors instead of invented empty content',async()=>{
  await assert.rejects(new Service().snapshotFile(folder,revision,'missing.java'),/Could not read/);
});
test('all four themes register with distinct selectable identities',()=>{
  const Theme=load('browser/theme/codedna-theme.ts').CodeDnaThemeContribution;
  const instance=new Theme(),registered=[];instance.theming={registerParsedTheme:t=>registered.push(t)};
  instance.register();assert.deepEqual(registered.map(t=>t.id).sort(),['codedna-contrast','codedna-dark','codedna-light','codedna-ocean']);
  assert.equal(registered.find(t=>t.id==='codedna-light').uiTheme,'vs');
  assert.equal(registered.find(t=>t.id==='codedna-contrast').uiTheme,'hc-black');
});
test('workflow navigation uses stable open commands and does not toggle panels shut',()=>{
  const callbacks=[], React={useState:initial=>[initial,()=>{}],createElement:(tag,props,...children)=>{if(tag==='button') callbacks.push(props);return {tag,props,children};}};
  const UI=load('browser/ui.tsx',{'@theia/core/shared/react':React});const visited=[];
  UI.WorkflowNav({workspace:{theme:'codedna-dark',navigate:id=>{visited.push(id);return Promise.resolve();}},current:'changes'});
  assert.equal(callbacks.find(b=>b['aria-current']==='page').disabled,true);
  callbacks.find(b=>b.key==='tests').onClick();assert.deepEqual(visited,['tests']);
});
for (const status of ['modified','added','deleted','renamed']) {
  test(`comparison handles ${status} files without reading a nonexistent side`, async()=>{
    const Widget=load('browser/change-view-widget.tsx',{'@theia/core/lib/browser/widgets/react-widget':{ReactWidget:class {update(){}}}}).ChangeViewWidget;
    const view=new Widget(),reads=[],opened=[];
    view.changes={repository:folder,base_commit:'a'.repeat(40),head_commit:'b'.repeat(40)};
    view.codedna={snapshotFile:async(repo,rev,file)=>{reads.push({rev,file});return rev[0];}};
    view.workspace={openComparison:async(...args)=>opened.push(args)};
    await view.showDifference({path:'new.java',old_path:status==='renamed'?'old.java':null,status,is_binary:false},22);
    assert.equal(reads.length,['added','deleted'].includes(status)?1:2);
    assert.equal(opened[0][1],status==='added'?'':'a');assert.equal(opened[0][2],status==='deleted'?'':'b');
    if(status==='renamed') assert.equal(reads[0].file,'old.java');
  });
}
test('a comparison finishing after the user changes selection does not open stale code',async()=>{
  const Widget=load('browser/change-view-widget.tsx',{'@theia/core/lib/browser/widgets/react-widget':{ReactWidget:class {update(){}}}}).ChangeViewWidget;
  const view=new Widget();let release,opened=false;const pending=new Promise(resolve=>release=resolve);
  view.changes={repository:folder,base_commit:'a'.repeat(40),head_commit:'b'.repeat(40)};
  view.codedna={snapshotFile:async()=>pending};view.workspace={openComparison:async()=>{opened=true;}};
  const run=view.showDifference({path:'file.java',status:'modified'});view.changes=undefined;release('source');await run;
  assert.equal(opened,false);
});
