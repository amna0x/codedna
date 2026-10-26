/**
 * Plain-language wording for newcomers. The analysis itself is unchanged —
 * these helpers only rephrase the core's messages and labels. Anything not
 * recognised is shown as-is, so no information is lost.
 */

export interface FriendlyError {
    title: string;
    help: string;
    details: string;
}

export function friendlyError(message: string): FriendlyError {
    if (/not a Git repository|does not exist|not a directory/i.test(message)) {
        return { title: 'This folder isn’t a Git project', help: 'Open a folder that uses Git (File → Open Folder…).', details: message };
    }
    if (/unknown commit/i.test(message)) {
        return {
            title: 'CodeDNA couldn’t find those commits',
            help: 'If the project has only one commit there is nothing to compare yet. Otherwise check the commit names.',
            details: message
        };
    }
    if (/could not start|CODEDNA_EXECUTABLE|exited with|did not start|health/i.test(message)) {
        return {
            title: 'CodeDNA’s engine isn’t running',
            help: 'Install CodeDNA (see ide/README.md) or set CODEDNA_EXECUTABLE, then try again.',
            details: message
        };
    }
    if (/language plugin .* is not installed/i.test(message)) {
        return {
            title: 'Java support isn’t installed',
            help: 'Run start.bat once (it installs the Java plugin), then try again. The Language plugins view shows what CodeDNA found.',
            details: message
        };
    }
    if (/Open a folder/i.test(message)) {
        return { title: 'No project open', help: 'Open your project folder first (File → Open Folder…).', details: '' };
    }
    return { title: 'Something went wrong', help: 'Try again. If it keeps happening, the details below explain what failed.', details: message };
}

export function friendlyWarning(warning: string): string | undefined {
    // Older reports said "non-Java file(s)"; current ones name no language.
    let match = warning.match(/^(\d+) changed (?:non-Java file\(s\) not analysed|file\(s\) not analysed by any installed language plugin)/);
    if (match) {
        const n = Number(match[1]);
        return `${n} changed file${n === 1 ? ' isn’t' : 's aren’t'} code CodeDNA reads, so it can’t tell what ${n === 1 ? 'it affects' : 'they affect'}.`;
    }
    match = warning.match(/^(\d+) changed \.\w+ file\(s\) not analysed: the (\w+) plugin/);
    if (match) {
        return `${languageName(match[2])} support isn’t installed, so CodeDNA can list these files but not analyse them. Run start.bat once to install it.`;
    }
    match = warning.match(/^(\d+) changed (\w+) file\(s\) count as unanalysed: no \w+ tests were found/);
    if (match) {
        const language = languageName(match[2]);
        return `CodeDNA found no ${language} tests and doesn’t follow links between languages, so ${language} changes make it suggest every test.`;
    }
    match = warning.match(/^(\d+) test class\(es\) (?:outside Surefire's default includes|the build does not run by default)/);
    if (match) {
        return 'Some tests wouldn’t run with the build’s default settings, so they aren’t listed.';
    }
    if (/(?:non-Java|unanalysed) change\(s\) ignored by request/.test(warning)) {
        return undefined; // the user asked for this; nothing to warn about
    }
    match = warning.match(/^(.+?): ((?:Java|Python) syntax error.*)$/);
    if (match) {
        return `${match[1]} has a syntax error, so its changes couldn’t be matched to ${match[2].startsWith('Python') ? 'functions' : 'methods'}.`;
    }
    return warning;
}

export function friendlyReason(reason: string): string {
    if (reason === 'test class changed') {
        return 'This test file was edited.';
    }
    if (reason === 'retest-all') {
        return 'You chose to run every test.';
    }
    let match = reason.match(/^non-Java file changed \((.+?)(?: and others)?\)/);
    if (match) {
        return `${match[1]} changed and isn’t Java code, so every test is suggested to be safe.`;
    }
    match = reason.match(/^unanalysed file changed \((.+?)(?: and others)?\)/);
    if (match) {
        return `${match[1]} changed and CodeDNA can’t follow what it affects, so every test is suggested to be safe.`;
    }
    match = reason.match(/^depends on changed type:(\S+) \(distance (\d+)\)/);
    if (match) {
        const steps = Number(match[2]);
        const via = steps > 1 ? ` (through ${steps - 1} other class${steps - 1 === 1 ? '' : 'es'})` : '';
        return `Uses ${simpleName(match[1])}, which changed${via}.`;
    }
    return reason;
}

export function changeLabel(change: string, commentOnly: boolean): { text: string; tone: string } {
    if (commentOnly) {
        return { text: 'Comments only', tone: 'muted' };
    }
    switch (change) {
        case 'added': return { text: 'New', tone: 'added' };
        case 'deleted': return { text: 'Removed', tone: 'deleted' };
        default: return { text: 'Changed', tone: 'modified' };
    }
}

export function fileStatusLabel(status: string): { text: string; tone: string } {
    switch (status) {
        case 'added': return { text: 'New file', tone: 'added' };
        case 'deleted': return { text: 'Removed', tone: 'deleted' };
        case 'renamed': return { text: 'Renamed', tone: 'modified' };
        default: return { text: 'Changed', tone: 'modified' };
    }
}

export function confidenceLabel(confidence: string): { text: string; tone: string; hint: string } {
    return confidence === 'heuristic'
        ? { text: 'Likely', tone: 'heuristic', hint: 'Probably connected — CodeDNA could not fully confirm this link.' }
        : { text: 'Direct', tone: 'confirmed', hint: 'Connected directly in the code.' };
}

export function kindLabel(kind: string): string {
    return ({ constructor: 'constructor', method: 'method', field: 'field', class: 'class',
        interface: 'interface', enum: 'enum', record: 'record', initializer: 'setup block',
        enum_constant: 'enum value', annotation_type: 'annotation', annotation_element: 'annotation value',
        module: 'module', function: 'function' } as Record<string, string>)[kind] ?? kind;
}

/** `example.PriceCalculator#applyDiscount(double)` → `PriceCalculator.applyDiscount()`. */
export function readableName(id: string): string {
    const [type, member] = id.replace(/^type:/, '').split('#');
    const simple = simpleName(type);
    if (!member) {
        return simple;
    }
    if (member.startsWith('<init>')) {
        return `${simple} (constructor)`;
    }
    return `${simple}.${member.replace(/\(.*\)$/, '()')}`;
}

/** Graph and test IDs without their `type:` and language (`py:`) prefixes. */
function bareId(typeId: string): string {
    return typeId.replace(/^type:/, '').replace(/^py:/, '');
}

export function simpleName(typeId: string): string {
    return bareId(typeId).split('.').slice(-1)[0];
}

export function packageName(typeId: string): string {
    const parts = bareId(typeId).split('.');
    return parts.slice(0, -1).join('.');
}

/** Insert soft break points after dots so long names wrap at sensible places. */
export function breakable(name: string): string {
    return name.replace(/\./g, '.​');
}

export function plural(n: number, one: string, many: string): string {
    return `${n} ${n === 1 ? one : many}`;
}

/** "java" → "Java", "python" → "Python". */
export function languageName(language: string): string {
    return language.charAt(0).toUpperCase() + language.slice(1);
}
