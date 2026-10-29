"""Bounded experimental Java numeric paired execution, not a regression oracle."""
from __future__ import annotations

from hashlib import sha256
from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
from threading import Event, Thread
from time import monotonic, sleep
from uuid import uuid4

from codedna.git_analysis.blobs import list_files, read_blobs
from codedna.git_analysis.git import run_git
from codedna_java.parser import parse_java
from codedna_java.witness_inputs import parameter_types, encode, generate, complexity, reductions
from codedna_java.witness_values import instance_array_probe, normal_value

MIN_INT, MAX_INT = -(2**31), 2**31-1
MAX_SOURCE = 256 * 1024
NAME = r'[A-Za-z_$][A-Za-z0-9_$]*'
ARG = r'(?:int\[\]|int\.\.\.|int|long|boolean|String)'
SYMBOL = re.compile(rf'^({NAME}(?:\.{NAME})*)#({NAME})\(({ARG})(?:,({ARG}))?\)$')
INTEGER = re.compile(r'^(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|[0-9][0-9_]*)[lL]?$')
HARNESS = '''import java.lang.reflect.*;
public final class CodeDNABehaviorProbe {
  public static void main(String[] args) throws Exception {
    try {
      String[] kinds = args.length > 4 ? args[4].split(",") : new String[]{"int"};
      String[] inputs = args[2].split(":", -1);
      if (kinds.length < 1 || kinds.length > 2 || inputs.length != kinds.length)
        throw new IllegalArgumentException("unsupported input arity");
      Class<?>[] types = new Class<?>[kinds.length];
      Object[] values = new Object[kinds.length];
      for (int i=0; i<kinds.length; i++) {
        switch (kinds[i]) {
          case "int": types[i]=int.class; values[i]=Integer.parseInt(inputs[i]); break;
          case "long": types[i]=long.class; values[i]=Long.parseLong(inputs[i]); break;
          case "int[]": case "int...": types[i]=int[].class;
            values[i]=inputs[i].isEmpty() ? new int[0] : java.util.Arrays.stream(inputs[i].split(",")).mapToInt(Integer::parseInt).toArray(); break;
          case "boolean": types[i]=boolean.class;
            if (!inputs[i].equals("true") && !inputs[i].equals("false")) throw new IllegalArgumentException("boolean");
            values[i]=Boolean.parseBoolean(inputs[i]); break;
          case "String": types[i]=String.class;
            values[i]=new String(java.util.Base64.getDecoder().decode(inputs[i]), java.nio.charset.StandardCharsets.UTF_8); break;
          default: throw new IllegalArgumentException("unsupported argument type");
        }
      }
      Method method = Class.forName(args[0]).getDeclaredMethod(args[1], types);
      if (!Modifier.isPublic(method.getModifiers()) || !Modifier.isStatic(method.getModifiers())
          || (method.getReturnType() != int.class && method.getReturnType() != long.class)) throw new IllegalArgumentException("unsupported method");
      long result = ((Number)method.invoke(null, values)).longValue();
      System.out.println(args[3] + "value:" + result);
    } catch (InvocationTargetException ex) {
      System.out.println(args[3] + "throw:" + ex.getCause().getClass().getName());
    }
  }
}
'''


HARNESS = instance_array_probe(HARNESS)


class ToolFailure(RuntimeError):
    pass


def _run(command, cwd, deadline, *, step_timeout=5):
    """Bound both project streams; outer CodeDNA owner contains descendants."""
    remaining = min(step_timeout, deadline-monotonic())
    if remaining <= 0:
        raise ToolFailure('time budget exhausted before the next tool invocation')
    env = os.environ.copy()
    for name in ('CLASSPATH', 'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS'):
        env.pop(name, None)
    buffers, overflow = [bytearray(), bytearray()], Event()
    process = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

    def read(stream, buffer):
        try:
            while chunk := stream.read1(4096):
                if len(buffer)+len(chunk) > 64 * 1024:
                    overflow.set()
                    return
                buffer.extend(chunk)
        except (OSError, ValueError):
            overflow.set()

    readers = [Thread(target=read, args=(stream, buffer), daemon=True)
               for stream, buffer in zip((process.stdout, process.stderr), buffers)]
    for thread in readers:
        thread.start()
    end = monotonic()+remaining
    try:
        while process.poll() is None:
            if overflow.is_set():
                raise ToolFailure('project/tool output exceeded 64 KiB per stream')
            if monotonic() >= end:
                raise ToolFailure('project/tool invocation exceeded its time budget')
            sleep(.01)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for thread in readers:
            thread.join(timeout=.5)
        # A descendant retaining a pipe prevents acceptance; the outer owner
        # closes its whole process tree before accepting any worker result.
        if not any(thread.is_alive() for thread in readers):
            process.stdout.close(); process.stderr.close()
    if overflow.is_set() or any(thread.is_alive() for thread in readers):
        raise ToolFailure('project/tool output did not finish within its bounds')
    return process.returncode, [bytes(b).decode('utf-8', errors='replace') for b in buffers]


def _tools(repo):
    suffix = '.exe' if os.name == 'nt' else ''
    home = os.environ.get('JAVA_HOME')
    javac = Path(home)/'bin'/('javac'+suffix) if home else Path(shutil.which('javac') or '')
    if not javac.is_file():
        raise ValueError('A JDK with javac is required; set JAVA_HOME to its installation')
    javac = javac.resolve()
    java = javac.with_name('java'+suffix)
    if not java.is_file() or javac.is_relative_to(repo) or java.is_relative_to(repo):
        raise ValueError('Use a matching external JDK, not an analysed-repository wrapper')
    return str(javac), str(java)


def _source(repo, commit, file):
    files = dict(list_files(repo, commit, '.java'))
    if file not in files:
        raise ValueError('Selected Java source is missing or not a regular file on one version')
    blob = files[file]
    if int(run_git(repo, 'cat-file', '-s', blob).strip()) > MAX_SOURCE:
        raise ValueError('Selected source exceeds the 256 KiB pilot limit')
    source = read_blobs(repo, [blob])[blob]
    try:
        source.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('Pilot requires UTF-8 Java source on both versions') from exc
    return source


def _method(source, symbol):
    match = SYMBOL.fullmatch(symbol)
    if match is None:
        raise ValueError('Pilot symbol must select one or two supported numeric/boolean/String arguments')
    class_name, method_name = match.groups()[:2]
    parameter_types(symbol)
    if class_name.rsplit('.', 1)[-1] in {'CodeDNABehaviorProbe', 'ReproduceDifference', 'CodeDNAWitnessTest'}:
        raise ValueError('Selected type conflicts with a reserved reproducer class name')
    parsed = parse_java(source)
    classes = [d for d in parsed.declarations if d.id == class_name and d.kind == 'class' and d.parent is None]
    methods = [d for d in parsed.declarations if d.id == symbol and d.kind == 'method']
    if parsed.has_syntax_errors or len(classes) != 1 or len(methods) != 1:
        raise ValueError('Pilot requires the same syntactically valid top-level class and method on both versions')
    method = methods[0]
    prefix = method.tokens[:method.tokens.index(method_name)]
    numeric_return = bool(prefix) and (prefix[-1] in ('int', 'long')
                                       or tuple(prefix[-3:]) == ('int', '[', ']'))
    if ('public' not in classes[0].tokens or 'public' not in prefix
            or not numeric_return or '{' not in method.tokens
            or {'native', 'abstract', 'synchronized'}.intersection(prefix)):
        raise ValueError('Pilot requires a public top-level class and a public int/long/int[]-return method with a body')
    if 'static' not in prefix:
        constructors = [d for d in parsed.declarations if d.kind == 'constructor' and d.parent == class_name]
        if ('abstract' in classes[0].tokens or constructors and not any(
                d.id == class_name+'#<init>()' and d.tokens[0] == 'public' for d in constructors)):
            raise ValueError('Instance witness requires a concrete class with a public no-argument constructor')
    return class_name, method_name, method


def _literals(tokens, bits=32):
    result = []
    for index, token in enumerate(tokens):
        if not INTEGER.fullmatch(token):
            continue
        is_long = token[-1:] in ('l', 'L')
        raw = token.rstrip('lL').replace('_', '')
        try:
            value = int(raw, 16 if raw.lower().startswith('0x') else
                        2 if raw.lower().startswith('0b') else 8 if len(raw)>1 and raw.startswith('0') else 10)
        except ValueError:
            continue
        nondecimal = raw.lower().startswith(('0x', '0b')) or len(raw)>1 and raw.startswith('0')
        if not is_long and nondecimal and MAX_INT < value <= 2**32-1:
            value -= 2**32
        elif is_long and nondecimal and 2**63-1 < value <= 2**64-1:
            value -= 2**64
        if index and tokens[index-1] == '-':
            value = -value
        if -(2**(bits-1)) <= value < 2**(bits-1):
            result.append(value)
    return result


def candidates(base_tokens, head_tokens, *, mode, seed, maximum, bits=32):
    """Syntax-derived boundaries are suggestions, never semantic guarantees."""
    rng = random.Random(seed)
    lower, upper = -(2**(bits-1)), 2**(bits-1)-1
    initial = [0, 1, -1, 2, -2, lower, upper]
    if mode == 'guided':
        guided = []
        # Prioritize edited literals before unchanged constants in a large method.
        # Bound matching work; this remains syntax guidance, not branch coverage.
        changed = []
        if len(base_tokens) + len(head_tokens) <= 8192:
            matcher = SequenceMatcher(None, base_tokens, head_tokens, autojunk=False)
            for tag, a, b, c, d in matcher.get_opcodes():
                if tag != 'equal':
                    # Keep the preceding sign token when a signed literal changed.
                    changed.extend(_literals(head_tokens[max(0,c-1):d], bits))
                    changed.extend(_literals(base_tokens[max(0,a-1):b], bits))
        for value in changed+_literals(head_tokens, bits)+_literals(base_tokens, bits):
            guided.extend([value, value-1, value+1])
        initial = guided+initial
    seen, result = set(), []
    for value in initial:
        if lower <= value <= upper and value not in seen:
            seen.add(value); result.append(value)
            if len(result) == maximum:
                return result
    while len(result) < maximum:
        value = rng.randint(lower, upper)
        if value not in seen:
            seen.add(value); result.append(value)
    return result


def _smaller(value):
    values = {0}
    sign, n = (-1 if value < 0 else 1), abs(value)
    while n > 1:
        n //= 2
        values.add(sign*n)
    return sorted((n for n in values if abs(n) < abs(value)), key=lambda n: (abs(n), n))


def find_witness(request):
    """Called only in the consented contained worker, never by read-only jobs."""
    report = {'status': 'inconclusive', 'observations': [], 'jvm_runs': 0,
              'compilations': 0, 'search_inputs': 0, 'reduction_inputs': 0,
              'source_encoding': 'UTF-8', 'runtime_file_encoding': 'UTF-8',
              'budget': dict(request['options']),
              'guidance': 'Edited integer literals first, then literal neighbors and fixed/seeded inputs from selected method syntax; no semantic or coverage guarantee.'}
    repo = Path(request['repository'])
    try:
        if request.get('allow_build') is not True:
            raise ValueError('explicit project-code consent is required')
        javac, java = _tools(repo)
        sources = [_source(repo, request[key], request['file']) for key in ('base_commit', 'head_commit')]
        support = {label: [(file, _source(repo, request[key], file)) for file in request.get('support_files', [])]
                   for label, key in [('base', 'base_commit'), ('head', 'head_commit')]}
        methods = [_method(source, request['symbol']) for source in sources]
        class_name, method_name, _ = methods[0]
        types = parameter_types(request['symbol'])
        report['input_types'] = types
        report['receiver_semantics'] = 'One invocation per fresh JVM; instance methods use a fresh public no-argument receiver. Constructor code executes.'
        if request.get('supplied_expectation') is not None:
            encode(types, request['supplied_expectation']['input'])
        basename = Path(request['file']).name
        if basename != class_name.rsplit('.', 1)[-1]+'.java':
            raise ValueError('Selected public class must match its Java source filename')
        report['source_sha256'] = {'base': sha256(sources[0]).hexdigest(), 'head': sha256(sources[1]).hexdigest()}
        report['selected_method_tokens_changed'] = methods[0][2].tokens != methods[1][2].tokens
    except (ValueError, OSError) as exc:
        return {**report, 'status': 'unsupported', 'reason': str(exc)}

    deadline = request['deadline']
    options = request['options']
    with TemporaryDirectory(prefix='codedna-witness-') as directory:
        work = Path(directory)
        empty = work/'empty'; empty.mkdir()
        paths = []
        try:
            for label, source in zip(('base', 'head'), sources):
                folder = work/label; folder.mkdir(); classes = folder/'classes'; classes.mkdir()
                (folder/basename).write_bytes(source)
                helper_paths = []
                for file, raw in support[label]:
                    target = folder/'support'/file
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                    helper_paths.append(str(target))
                (folder/'CodeDNABehaviorProbe.java').write_text(HARNESS, encoding='utf-8')
                code, output = _run([javac, '-J-Xmx128m', '-J-Dfile.encoding=UTF-8', '-encoding', 'UTF-8', '-proc:none', '-classpath', str(empty),
                    '-sourcepath', str(empty), '-d', str(classes), str(folder/basename),
                    str(folder/'CodeDNABehaviorProbe.java'), *helper_paths], folder, deadline, step_timeout=10)
                report['compilations'] += 1
                if code:
                    return {**report, 'status': 'unsupported',
                            'reason': 'Self-contained pilot compilation failed; external dependencies/build scripts are unsupported.',
                            'compiler_details': output[1][-2000:]}
                paths.append((folder, classes))
            code, version = _run([java, '-version'], work, deadline)
            if code:
                raise ToolFailure('JDK version probe failed')
            report['java_version'] = (version[1] or version[0])[:1000]
            code, version = _run([javac, '-version'], work, deadline)
            if code:
                raise ToolFailure('Compiler version probe failed')
            report['javac_version'] = (version[1] or version[0])[:1000]

            def observe(value, phase):
                pair = []
                for folder, classes in paths:
                    token = 'CODEDNA_'+uuid4().hex+':'
                    code, output = _run([java, '-Xmx64m', '-Xss256k', '-Dfile.encoding=UTF-8', '-cp', str(classes),
                        'CodeDNABehaviorProbe', class_name, method_name, encode(types, value), token,
                        ','.join(types)], folder, deadline)
                    report['jvm_runs'] += 1
                    lines = [line[len(token):] for line in output[0].splitlines() if line.startswith(token)]
                    if code or len(lines) != 1:
                        raise ToolFailure('Project execution returned no unique complete observation')
                    if lines[0].startswith('value:'):
                        observed = {'kind': 'value', 'value': normal_value(lines[0][6:])}
                    elif lines[0].startswith('throw:'):
                        observed = {'kind': 'exception', 'type': lines[0][6:]}
                    else:
                        raise ToolFailure('Unrecognized project observation')
                    pair.append(observed)
                item = {'phase': phase, 'input': value, 'base': pair[0], 'head': pair[1]}
                report['observations'].append(item)
                return item

            def confirm(item):
                for _ in range(2):
                    actual = observe(item['input'], 'confirmation')
                    if actual['base'] != item['base'] or actual['head'] != item['head']:
                        raise ToolFailure('Repeated fresh JVM runs disagreed; witness is unstable')

            values = generate(types, methods[0][2].tokens, methods[1][2].tokens,
                mode=options['generation'], seed=options['seed'], maximum=options['max_inputs'],
                int_candidates=candidates)
            report['candidate_inputs'] = values
            expectation = request.get('supplied_expectation')
            if expectation is not None:
                value = expectation['input']
                values = ([value] + [v for v in values if v != value])[:options['max_inputs']]
                report['candidate_inputs'] = values
                report['supplied_input_counts_toward_search_budget'] = True
            witness = None
            report['non_normal_search_inputs'] = 0
            for value in values:
                report['search_inputs'] += 1
                item = observe(value, 'search')
                if any(item[label]['kind'] != 'value' for label in ('base', 'head')):
                    report['non_normal_search_inputs'] += 1
                    continue
                if item['base'] != item['head']:
                    witness = item
                    break
            if witness is None:
                if report['non_normal_search_inputs']:
                    return {**report, 'status': 'inconclusive',
                        'reason': 'Exception observed for some inputs; no confirmed normal-return difference within the remaining finite budget. All observations retained.'}
                return {**report, 'status': 'no_difference_observed',
                        'reason': 'No normal-return difference observed within the finite input/time budget; equivalence is not established.'}
            confirm(witness)
            original = witness
            for value in reductions(original['input'], _smaller, types)[:options['reduce_budget']]:
                if complexity(value) >= complexity(witness['input']):
                    continue
                report['reduction_inputs'] += 1
                item = observe(value, 'reduction')
                if any(item[label]['kind'] != 'value' for label in ('base', 'head')):
                    continue
                if item['base'] != item['head']:
                    witness = item
            confirm(witness)
            report.update(status='difference', witness=witness, original_witness=original,
                          reduction='Smallest absolute value for int, or summed magnitude/string-length complexity, among candidates actually tried; no global minimality claim.',
                          confirmation='Each accepted witness pair matched two further fresh-JVM pairs; general determinism is not proved.')
            from codedna_java.witness_export import export_reproducer
            report['reproducer'] = export_reproducer(Path(request['output_dir']), basename, sources,
                request['symbol'], witness, report['source_sha256'], HARNESS,
                expectation=expectation, support=support,
                instance='static' not in methods[1][2].tokens[:methods[1][2].tokens.index(method_name)])
            return report
        except (ToolFailure, OSError, ValueError) as exc:
            return {**report, 'status': 'inconclusive', 'reason': str(exc)[:1000]}
