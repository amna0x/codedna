const assert = require('node:assert/strict');
const { test } = require('node:test');
const ui = require('../plugins.js');
const bundled = require('../catalogue/index.json');
const release = 'https://github.com/mohibk0004-del/codedna/releases/download/v1/codedna_python-1.2.3-py3-none-any.whl';
function optional() { return { schema_version:1, plugins:[{ id:'python', package:'codedna-python', name:'Python',
    description:'Example', licence:'Example', source:'https://example.invalid/source', versions:[{
        version:'1.2.3', api_version:'1.1', url:release, sha256:'a'.repeat(64) }] }] }; }
class Element {
    constructor(tag) { this.tag=tag; this.children=[]; this.attributes={}; this.events={}; this.textContent=''; }
    append(...children) { this.children.push(...children); }
    replaceChildren(...children) { this.children=children; }
    setAttribute(name,value) { this.attributes[name]=value; }
    addEventListener(name,callback) { this.events[name]=callback; }
}
const document = { createElement: tag => new Element(tag) };
function all(element) { return [element,...element.children.flatMap(all)]; }

test('Current Java/Python catalogue offers bundled acquisition without fake download links', () => {
    const cards=ui.render(document,bundled);
    assert.equal(cards.length,2);
    for(const card of cards) {
        const link=all(card).find(e=>e.tag==='a'&&e.className==='button');
        assert.equal(link.href,'downloads.html#desktop');
        assert.match(link.textContent,/Get CodeDNA/);
        assert.ok(all(card).some(e=>/Already installed/.test(e.textContent)));
    }
});

test('Optional version exposes only the official wheel, complete hash and pinned command', () => {
    const [card]=ui.render(document,optional());
    assert.equal(all(card).find(e=>e.textContent==='Download v1.2.3').href,release);
    assert.ok(all(card).some(e=>e.tag==='code'&&e.textContent==='a'.repeat(64)));
    assert.ok(all(card).some(e=>e.tag==='pre'&&e.textContent==='codedna plugins install python 1.2.3 --yes'));
});

test('Numeric version sorting does not select 1.9 over 1.10', () => {
    const data=optional(); data.plugins[0].versions.push({...data.plugins[0].versions[0],version:'1.10.0'});
    data.plugins[0].versions[0].version='1.9.0';
    assert.ok(all(ui.render(document,data)[0]).some(e=>e.textContent==='Download v1.10.0'));
});

for(const bad of ['https://evil.invalid/p.whl',release+'?redirect=evil',release+'#fragment',
    release.replace('/v1/','/../'),release.replace('/v1/','/%2e%2e/'),release.replace('.whl','.exe')]) {
    test('Refuses non-official or malformed wheel URL: '+bad,()=>{
        const data=optional();data.plugins[0].versions[0].url=bad;
        assert.throws(()=>ui.render(document,data),/Unverified download/);
    });
}

test('Refuses missing IDs, duplicate versions, unpinned versions and invalid checksums',()=>{
    for(const mutate of [d=>delete d.plugins[0].id,
        d=>d.plugins[0].versions.push({...d.plugins[0].versions[0]}),
        d=>d.plugins[0].versions[0].version='>=1',d=>d.plugins[0].versions[0].sha256=null]) {
        const data=optional();mutate(data);assert.throws(()=>ui.validate(data));
    }
});

test('Repository-controlled text remains text, not HTML markup',()=>{
    const data=optional();data.plugins[0].name='<img src=x onerror=alert(1)>';
    const nodes=all(ui.render(document,data)[0]);
    assert.ok(nodes.some(e=>e.textContent===data.plugins[0].name));
    assert.equal(nodes.some(e=>Object.hasOwn(e,'innerHTML')),false);
});

test('Offline catalogue renders a useful message with no broken actions',async()=>{
    const root=new Element('div');
    await ui.mount({...document,getElementById:()=>root},async()=>{throw new Error('offline');});
    assert.match(root.children[0].textContent,/Bundled Java and Python keep working/);
    assert.equal(all(root).some(e=>e.tag==='a'),false);
});

test('No browser clipboard shows manual-copy instructions instead of losing the command',async()=>{
    const [card]=ui.render(document,optional());
    await all(card).find(e=>e.textContent==='Copy install command').events.click();
    assert.ok(all(card).some(e=>/Clipboard unavailable/.test(e.textContent)));
});
