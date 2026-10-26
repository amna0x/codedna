const { test } = require('node:test');
const assert = require('node:assert/strict');
const path = require('path');
const { resolveCoreExecutable } = require('./desktop-runtime.cjs');

test('packaged core works even when no Python or CodeDNA is on PATH', () => {
    const resources = path.resolve('installation with spaces', 'resources');
    const expected = path.join(resources, 'core', 'codedna-core.exe');
    assert.equal(resolveCoreExecutable({ PATH: '' }, resources, p => p === expected), expected);
});

test('explicit external core always takes precedence over the bundle', () => {
    const custom = path.resolve('custom core', 'codedna.exe');
    assert.equal(resolveCoreExecutable({ CODEDNA_EXECUTABLE: custom }, '/resources', () => true), custom);
});

test('development retains the normal PATH executable when no bundle exists', () => {
    assert.equal(resolveCoreExecutable({}, '/resources', () => false), 'codedna');
    assert.equal(resolveCoreExecutable({}, undefined, () => true), 'codedna');
});
