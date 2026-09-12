const test = require('node:test');
const assert = require('node:assert/strict');
const { agentFlow, actionOrigin } = require('../breedframe/static/agent-flow.js');
const caseState = (status, extra = {}) => ({ status, events: [], ...extra });

test('idle and queued cases do not invent an active decision', () => {
  assert.equal(agentFlow(null).phase, null);
  assert.equal(agentFlow(caseState('ready')).phase, null);
});

test('running cases distinguish choosing from an executing tool', () => {
  assert.equal(agentFlow(caseState('running')).phase, 'choose');
  const event = { kind: 'tool', tool: 'classify_breed', status: 'running' };
  assert.equal(agentFlow(caseState('running', { events: [event] })).phase, 'execute');
  assert.equal(agentFlow(caseState('running', { events: [{ ...event, status: 'ok' }] })).phase, 'choose');
  assert.equal(agentFlow(caseState('running', { events: [{ ...event, status: 'error' }] })).phase, 'choose');
});

test('terminal and paused states override stale running events', () => {
  for (const status of ['complete', 'incomplete', 'awaiting_photo']) {
    const state = agentFlow(caseState(status, { events: [{ kind: 'tool', status: 'running' }] }));
    assert.equal(state.phase, null);
    assert.notEqual(state.tone, 'running');
  }
});

test('cancellation waits for the bounded call without claiming it has stopped', () => {
  const state = agentFlow(caseState('running', { cancel_pending: true }));
  assert.equal(state.phase, null);
  assert.match(state.detail, /Waiting for the current bounded call/);
});

test('inconclusive completion and user-saved reports retain their meaning', () => {
  const state = agentFlow(caseState('complete', { report: { outcome: 'inconclusive', completed_by: 'user' } }));
  assert.equal(state.tone, 'inconclusive');
  assert.match(state.title, /Evidence inconclusive/);
  assert.match(state.detail, /You saved a partial assessment/);
});

test('early stops retain their recorded reason', () => {
  assert.equal(agentFlow(caseState('incomplete', { stop_reason: 'Action budget exhausted.' })).detail, 'Action budget exhausted.');
});

test('a new follow-up uses current status rather than a previous report', () => {
  const state = agentFlow(caseState('running', { report: { outcome: 'inconclusive' }, events: [{ kind: 'tool', status: 'ok', tool: 'finish_assessment' }] }));
  assert.equal(state.phase, 'choose');
  assert.equal(state.tone, 'running');
});

test('action attribution uses recorded provenance and never invents a model choice', () => {
  assert.equal(actionOrigin({ kind: 'user_region' }), 'You');
  assert.equal(actionOrigin({ kind: 'user_action' }), 'You');
  assert.equal(actionOrigin({ kind: 'controller_error' }), 'Controller error');
  assert.equal(actionOrigin({ kind: 'tool', controller: { model: 'qwen3:4b' } }), 'Controller · qwen3:4b');
  assert.equal(actionOrigin({ kind: 'tool' }), 'Application');
});
