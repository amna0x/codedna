// Renders catalogue/index.json. Display only: no installing from the website.
(async () => {
  const root = document.getElementById('plugins');
  const text = (tag, value, cls) => { const el = document.createElement(tag); el.textContent = value; if (cls) el.className = cls; return el; };
  try {
    const response = await fetch('catalogue/index.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const catalogue = await response.json();
    root.replaceChildren(...catalogue.plugins.map(plugin => {
      const card = document.createElement('div');
      card.className = 'card';
      const latest = plugin.versions[plugin.versions.length - 1];
      const title = text('h3', plugin.name);
      title.append(text('span', latest.builtin ? 'built in' : `v${latest.version}`, 'chip'));
      const source = document.createElement('a');
      source.href = plugin.source;
      source.textContent = 'Source';
      const meta = text('p', `Version ${latest.version} · plugin API ${latest.api_version} · licence: ${plugin.licence} · `);
      meta.append(source);
      if (!latest.builtin) meta.append(text('span', ` · SHA-256 ${latest.sha256.slice(0, 12)}…`));
      card.append(title, text('p', plugin.description), meta);
      return card;
    }));
  } catch (error) {
    root.replaceChildren(text('p', `Could not load the catalogue (${error.message}).`));
  }
})();
