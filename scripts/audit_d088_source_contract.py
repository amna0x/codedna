"""Read pinned development sources and audit method contracts without compiling them."""
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from codedna_java.parser import parse_java
from codedna_java.witness import _method


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'build/d088-inputs'
    cases = json.loads((root/'experiments/moonshot-real-bug-selection-d088.json').read_text())['cases']
    reports = []
    for case in cases:
        if case['split'] != 'development':
            continue
        raw = (folder/'gitbug-java/data/bugs'/case['metadata_file']).read_bytes()
        if sha256(raw).hexdigest() != case['metadata_sha256']:
            raise ValueError('Metadata changed')
        metadata = json.loads(raw.decode().splitlines()[case['metadata_line']-1])
        files = sorted({line[6:] for line in metadata['bug_patch'].splitlines()
                        if line.startswith('+++ b/') and line.endswith('.java')})
        report = {'repository': case['repository'], 'scope': 'source contract only; no code execution',
                  'files': [], 'candidates': [], 'errors': [], 'refusals': []}
        if len(files) > 24:
            report['errors'].append('Source audit exceeds the 24-file bound; no partial eligibility claim')
            files = []
        for name in files:
            try:
                sources = []
                hashes = []
                for revision in [case['previous_commit_hash'], case['commit_hash']]:
                    url = 'https://raw.githubusercontent.com/'+case['repository']+'/'+revision+'/'+quote(name, safe='/')
                    cache = folder/'source-cache'/sha256(url.encode()).hexdigest()
                    cache.parent.mkdir(exist_ok=True)
                    if cache.exists():
                        source = cache.read_bytes()
                    else:
                        with urlopen(url, timeout=30) as response:
                            source = response.read(256*1024+1)
                        if len(source) <= 256*1024:
                            cache.write_bytes(source)
                    if len(source) > 256*1024:
                        raise ValueError('Source exceeds witness size limit')
                    sources.append(source)
                    hashes.append(sha256(source).hexdigest())
                report['files'].append({'file': name, 'source_sha256': hashes})
                declarations = [{d.id: d for d in parse_java(s).declarations if d.kind == 'method'}
                                for s in sources]
                for symbol in sorted(set(declarations[0]) & set(declarations[1])):
                    if declarations[0][symbol].tokens == declarations[1][symbol].tokens:
                        continue
                    try:
                        for source in sources:
                            _method(source, symbol)
                    except ValueError as error:
                        method = declarations[1][symbol]
                        prefix = method.tokens[:method.tokens.index(symbol.split('#')[1].split('(')[0])]
                        report['refusals'].append({'file': name, 'symbol': symbol,
                            'prefix': list(prefix), 'reason': str(error)})
                        continue
                    report['candidates'].append({'file': name, 'symbol': symbol,
                        'note': 'Signature eligible; standalone compilation/dependencies and bug relevance unverified'})
                for symbol in sorted(set(declarations[0]) ^ set(declarations[1])):
                    report['refusals'].append({'file': name, 'symbol': symbol,
                        'reason': 'Added, removed or changed signature; no identity mapping guessed'})
            except Exception as error:
                report['errors'].append({'file': name, 'error': str(error)[:300]})
        reports.append(report)
        (folder/'development-source-contract.json').write_text(json.dumps(reports, indent=2)+'\n')
        print(case['repository'], 'candidate methods:',len(report['candidates']),
              'source errors:',len(report['errors']), flush=True)
    print('Development source audit complete. Held-out sources untouched.')


if __name__ == '__main__':
    main()
