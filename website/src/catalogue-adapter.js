const module={exports:{}}; const document=undefined;
// The website displays the same official catalogue as the core. No local code runs here.
const CodeDnaCatalogue = (() => {
  const RELEASES = 'https://github.com/mohibk0004-del/codedna/releases/download/';
  const pinned = /^\d+\.\d+\.\d+$/;
  const id = /^[a-z][a-z0-9-]{1,40}$/;
  const asset = /^[A-Za-z0-9][A-Za-z0-9._+-]*\/[A-Za-z0-9][A-Za-z0-9._+-]*$/;
  function validate(data) {
    if (!data || data.schema_version !== 1 || !Array.isArray(data.plugins)) throw new Error('Invalid catalogue schema');
    const seen = new Set();
    for (const plugin of data.plugins) {
      if (typeof plugin.id !== 'string' || !id.test(plugin.id) || seen.has(plugin.id)) throw new Error('Invalid or duplicate plugin');
      seen.add(plugin.id);
      if (!['name', 'description', 'licence', 'source'].every(k => typeof plugin[k] === 'string' && plugin[k].trim())) throw new Error('Incomplete plugin information');
      if (!/^https:\/\//.test(plugin.source)) throw new Error('Invalid source link');
      if (!Array.isArray(plugin.versions) || !plugin.versions.length) throw new Error('No pinned versions');
      const versions = new Set();
      for (const version of plugin.versions) {
        if (!pinned.test(version.version) || versions.has(version.version) || !/^\d+\.\d+$/.test(version.api_version)) throw new Error('Invalid version');
        versions.add(version.version);
        if (version.builtin === true) {
          if (version.url != null || version.sha256 != null) throw new Error('Bundled version has no separate download');
        } else {
          if (!id.test(String(plugin.package || '').replaceAll('_', '-'))) throw new Error('Missing package name');
          if (typeof version.url !== 'string' || !version.url.startsWith(RELEASES) ||
              !asset.test(version.url.slice(RELEASES.length)) || version.url.includes('..') ||
              !version.url.endsWith('.whl') || !/^[0-9a-f]{64}$/.test(version.sha256)) throw new Error('Unverified download');
        }
      }
    }
    return data;
  }
  function compare(a, b) {
    const x = a.split('.').map(Number), y = b.split('.').map(Number);
    for (let i=0;i<3;i++) if (x[i] !== y[i]) return x[i] - y[i];
    return 0;
  }
  function actions(plugin, version) {
    if (version.builtin === true) return { bundled:true, href:'downloads.html#desktop', label:'Get CodeDNA with ' + plugin.name };
    return { bundled:false, href:version.url, label:'Download v' + version.version,
      command:'codedna plugins install ' + plugin.id + ' ' + version.version + ' --yes' };
  }
  function render(document, data) {
    validate(data);
    const text = (tag, value, cls) => { const el=document.createElement(tag); el.textContent=value; if(cls)el.className=cls; return el; };
    return data.plugins.map(plugin => {
      const version=[...plugin.versions].sort((a,b)=>compare(b.version,a.version))[0];
      const action=actions(plugin,version), card=document.createElement('article'); card.className='card';
      const heading=text('h2',plugin.name); heading.append(text('span',action.bundled?'Included with IDE':'Optional download','chip'));
      card.append(heading,text('p',plugin.description),text('p','Version '+version.version+' · plugin API '+version.api_version,'plugin-meta'));
      const link=text('a',action.label,'button'); link.href=action.href;
      card.append(link);
      if(action.bundled) card.append(text('p','Already installed in the desktop bundle. Open Extensions → Language plugins to inspect it.','plugin-meta'));
      else {
        link.setAttribute('rel','noopener noreferrer');
        card.append(text('p','In the app: Extensions → Language plugins. Review the version and confirm Install.','plugin-meta'));
        const details=document.createElement('details'); details.append(text('summary','Verify download and install from the terminal'));
        details.append(text('p','SHA-256'),text('code',version.sha256,'checksum'),text('pre',action.command));
        const copy=text('button','Copy install command','button secondary'); copy.type='button';
        const status=text('span','','copy-status'); status.setAttribute('role','status');
        copy.addEventListener('click',async()=>{
          try { await globalThis.navigator.clipboard.writeText(action.command); status.textContent='Command copied. Review it before running.'; }
          catch { status.textContent='Clipboard unavailable. Select and copy the command above.'; }
        });
        details.append(copy,status,text('p','The core downloads from the official catalogue and verifies the complete checksum before installing. A website download does not install a plugin.'));
        card.append(details);
      }
      card.append(text('p','Licence: '+plugin.licence,'plugin-meta'));
      const source=text('a','Source repository'); source.href=plugin.source; source.rel='noopener noreferrer'; card.append(source);
      return card;
    });
  }
  async function mount(document, fetcher=globalThis.fetch) {
    const root=document.getElementById('plugins');
    try {
      const response=await fetcher('catalogue/index.json');
      if(!response.ok) throw new Error('HTTP '+response.status);
      root.replaceChildren(...render(document,await response.json()));
    } catch(error) {
      const message=document.createElement('p');
      message.textContent='The catalogue could not be loaded. Bundled Java and Python keep working in CodeDNA. '+error.message;
      root.replaceChildren(message);
    }
  }
  return {validate,compare,actions,render,mount};
})();
if(typeof module !== 'undefined' && module.exports) module.exports=CodeDnaCatalogue;
if(typeof document !== 'undefined') CodeDnaCatalogue.mount(document);

export default module.exports;
