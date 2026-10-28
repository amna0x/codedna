const assert = require('node:assert/strict');
const {test} = require('node:test');
const {init} = require('../site.js');

function element(dataset = {}, textContent = '') {
  const values = new Set();
  return {dataset, textContent, hidden:false, attributes:{}, events:{}, focused:false,
    classList:{add(v){values.add(v);},remove(v){values.delete(v);},contains(v){return values.has(v);},
      toggle(v,on){if(on)values.add(v);else values.delete(v);}},
    setAttribute(k,v){this.attributes[k]=v;},getAttribute(k){return this.attributes[k];},
    addEventListener(k,fn){this.events[k]=fn;},focus(){this.focused=true;}};
}
function fixture({reduced=false, observer=true} = {}) {
  const toggle=element(),nav=element(),status=element(),body=element(),rail={scrollLeft:250};
  toggle.setAttribute('aria-expanded','false');
  const buttons=['all','java','python','agents'].map(key=>element({filter:key},key));
  const cards=['java','python','agents','java python'].map(key=>element({category:key}));
  const reveals=[element(),element()];
  let watched=[],disconnected=false;
  const queries={'.menu-toggle':toggle,'#primary-nav':nav,'#filter-status':status,'.workflow-rail':rail};
  const doc={body,events:{},querySelector:s=>queries[s]||null,
    querySelectorAll:s=>s==='[data-filter]'?buttons:s==='[data-category]'?cards:s==='[data-reveal]'?reveals:[],
    addEventListener(k,fn){this.events[k]=fn;}};
  const media=[];
  const win={matchMedia(query){const item={matches:query.includes('reduce')&&reduced,addEventListener(k,fn){this.change=fn;}};media.push(item);return item;}};
  if(observer) win.IntersectionObserver=class {
    constructor(fn){this.callback=fn;}
    observe(el){watched.push(el);}
    unobserve(){}
    disconnect(){disconnected=true;}
  };
  init(doc,win);
  return {toggle,nav,status,buttons,cards,reveals,doc,media,rail,get watched(){return watched;},get disconnected(){return disconnected;}};
}

test('Workflow filters hide irrelevant links and include shared-language guides',()=>{
  const f=fixture();
  f.buttons[1].events.click();
  assert.deepEqual(f.cards.map(c=>c.hidden),[false,true,true,false]);
  assert.equal(f.buttons[1].attributes['aria-pressed'],'true');
  assert.equal(f.buttons[0].attributes['aria-pressed'],'false');
  assert.equal(f.status.textContent,'Showing 2 java workflows.');
  assert.equal(f.rail.scrollLeft,0);
  f.buttons[2].events.click();
  assert.deepEqual(f.cards.map(c=>c.hidden),[true,false,true,false]);
  f.buttons[3].events.click();
  assert.deepEqual(f.cards.map(c=>c.hidden),[true,true,false,true]);
  assert.equal(f.status.textContent,'Showing 1 agents workflow.');
  f.buttons[0].events.click();
  assert.ok(f.cards.every(c=>!c.hidden));
});
test('Mobile menu closes on Escape and returns focus to its trigger',()=>{
  const f=fixture();f.toggle.events.click();
  assert.equal(f.toggle.attributes['aria-expanded'],'true');
  assert.ok(f.nav.classList.contains('is-open'));
  f.doc.events.keydown({key:'Escape'});
  assert.equal(f.toggle.attributes['aria-expanded'],'false');
  assert.equal(f.nav.classList.contains('is-open'),false);
  assert.equal(f.toggle.focused,true);
});
test('Selecting a menu link and moving to desktop reset expanded state',()=>{
  const f=fixture();f.toggle.events.click();
  f.nav.events.click({target:{closest:()=>({})}});
  assert.equal(f.toggle.attributes['aria-expanded'],'false');
  f.toggle.events.click();f.media[0].change({matches:true});
  assert.equal(f.toggle.attributes['aria-expanded'],'false');
});
test('Reduced motion and missing observers leave illustrations visible',()=>{
  for(const options of [{reduced:true},{observer:false}]) {
    const f=fixture(options);
    assert.equal(f.watched.length,0);
    assert.ok(f.reveals.every(el=>!el.classList.contains('will-reveal')));
  }
});
test('Enabling reduced motion during a visit disconnects animation and reveals content',()=>{
  const f=fixture();
  assert.equal(f.watched.length,2);
  f.media[1].change({matches:true});
  assert.equal(f.disconnected,true);
  assert.ok(f.reveals.every(el=>el.classList.contains('is-visible')));
});
