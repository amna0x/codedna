const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');
const { test } = require('node:test');
const ts = require('typescript');
const tick = () => new Promise(resolve => setImmediate(resolve));

function service() {
    const timers = new Set(), launches = [];
    const child = new EventEmitter();
    child.stdout = new EventEmitter(); child.stderr = new EventEmitter();
    child.exitCode = null; child.killed = false;
    child.kill = () => { child.killed = true; };
    const net = { createServer: () => ({ unref() {}, on() {},
        listen(_port,_host,callback) { callback(); }, address:()=>({port:12345}), close:callback=>callback() }) };
    const source = fs.readFileSync(path.join(__dirname,'../src/node/codedna-service-impl.ts'),'utf8');
    const code = ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,
        target:ts.ScriptTarget.ES2022,experimentalDecorators:true}}).outputText;
    const module = {exports:{}};
    vm.runInNewContext(code,{module,exports:module.exports,
        process:{env:{CODEDNA_EXECUTABLE:'fake-core'}},
        require(id) {
            if(id==='child_process') return {spawn:(executable,args,options)=>{ launches.push({executable,args,options}); return child; }};
            if(id==='net') return net;
            if(id==='crypto') return require('node:crypto');
            if(id==='path') return require('node:path');
            if(id.endsWith('/inversify')) return {injectable:()=>target=>target};
            return {};
        },
        fetch:async()=>({ok:true,json:async()=>({version:'test-version'})}),
        setTimeout(callback,ms) { const timer={callback,ms};timers.add(timer);return timer; },
        clearTimeout:timer=>timers.delete(timer)
    });
    return {client:new module.exports.CodeDnaServiceImpl(),child,launches,
        advance(ms) { for(const timer of [...timers]) if(timer.ms<=ms) {timers.delete(timer);timer.callback();} }};
}

test('A slow cold core can announce after 20 seconds instead of being killed at 15',async()=>{
    const {client,child,advance}=service();
    const starting=client.start();
    await tick();
    advance(20000);
    child.stdout.emit('data',Buffer.from('{"url":"http://127.0.0.1:12345"}\n'));
    await starting;
    assert.equal(child.killed,false);
    assert.equal(client.baseUrl,'http://127.0.0.1:12345');
    assert.equal(client.version,'test-version');
});

test('An unresponsive core still times out and is cleaned up',async()=>{
    const {client,child,advance}=service();
    const starting=client.start();
    const rejected=assert.rejects(starting,/did not start within 60 s/);
    await tick();
    advance(60001);
    await rejected;
    assert.equal(child.killed,true);
    assert.equal(client.baseUrl,undefined);
});

test('desktop plugin activation is retained across a consented API restart', async () => {
    const { client, child, launches } = service();
    const snapshot = { schema_version: 1, home: 'fixture', directories: ['python-1.0.0-' + 'a'.repeat(32)], error: null };
    const first = client.start(); await tick();
    child.stdout.emit('data', Buffer.from(JSON.stringify({ url: 'http://127.0.0.1:12345', plugin_snapshot: snapshot }) + '\n'));
    await first;
    assert.equal(launches[0].options.env.CODEDNA_DESKTOP_PLUGIN_SNAPSHOT, undefined);
    client.onStop(); client.buildsEnabled = true;
    const restarted = client.start(); await tick();
    assert.equal(launches[1].options.env.CODEDNA_DESKTOP_PLUGIN_SNAPSHOT, JSON.stringify(snapshot));
    assert.ok(launches[1].args.includes('--allow-build'));
    child.stdout.emit('data', Buffer.from(JSON.stringify({ url: 'http://127.0.0.1:12345', plugin_snapshot: snapshot }) + '\n'));
    await restarted;
});
