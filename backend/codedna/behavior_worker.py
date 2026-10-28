"""Private consented execution worker. Wait for containment before plugin loading."""
import json
import sys

MAX_MESSAGE = 1024 * 1024


def main():
    line = sys.stdin.buffer.readline(64 * 1024 + 1)
    output = sys.stdout
    try:
        if len(line) > 64 * 1024:
            raise ValueError('behavioral request exceeds its message limit')
        request = json.loads(line)
        if request.get('allow_build') is not True:
            raise ValueError('behavioral worker requires explicit project-code consent')
        from contextlib import redirect_stdout
        with redirect_stdout(sys.stderr):
            if getattr(sys, 'frozen', False):
                from codedna.plugins import desktop_store
                desktop_store.pin_worker_snapshot(request['plugins'])
            from codedna.plugins import load_plugins
            from codedna.plugins.languages import require
            plugin = require(request['language'], load_plugins())
            operation = getattr(plugin, 'find_witness', None)
            if not callable(operation):
                raise ValueError('language has no experimental behavioral witness capability')
            result = operation(request)
        encoded = json.dumps(result, ensure_ascii=True, allow_nan=False)
        if len(encoded) > MAX_MESSAGE:
            raise ValueError('behavioral result exceeds its message limit')
        output.write(encoded+'\n'); output.flush()
        return 0
    except Exception as exc:
        output.write(json.dumps({'status': 'inconclusive', 'reason': str(exc)[:1000]})+'\n')
        output.flush()
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
