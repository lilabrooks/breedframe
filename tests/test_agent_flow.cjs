const test = require('node:test');
const assert = require('node:assert/strict');
const { agentFlow, actionOrigin, runtimeReadiness } = require('../breedframe/static/agent-flow.js');
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
  assert.match(state.title, /Your results are ready/);
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
  assert.equal(actionOrigin({ kind: 'tool', controller: { model: 'qwen3:4b' } }), 'Scout · chose this action');
  assert.equal(actionOrigin({ kind: 'tool' }), 'Application');
});

test('each running tool names the actual work without inventing a completion percentage', () => {
  const titles = {
    inspect_image: 'Checking photo quality',
    classify_breed: 'Vision model is comparing breeds',
    classify_region: 'Vision model is analyzing your selection',
    request_another_photo: 'Scout is requesting another photo',
    finish_assessment: 'Preparing your assessment',
  };
  for (const [tool, title] of Object.entries(titles)) {
    const state = agentFlow(caseState('running', { events: [{ kind: 'tool', status: 'running', tool }] }));
    assert.equal(state.title, title);
    assert.equal(state.phase, 'execute');
    assert.equal(state.completedPhase, 'choose');
    assert.equal(state.busy, true);
    assert.equal(state.percent, undefined);
  }
});

test('returned evidence is marked received while the controller chooses again', () => {
  const state = agentFlow(caseState('running', { events: [{ kind: 'tool', status: 'ok', tool: 'inspect_image' }] }));
  assert.equal(state.phase, 'choose');
  assert.equal(state.completedPhase, 'review');
  assert.equal(state.badge, 'RESULT RECEIVED');
});

test('failed results are never marked as received evidence', () => {
  const state = agentFlow(caseState('running', { events: [{ kind: 'tool', status: 'error', tool: 'inspect_image' }] }));
  assert.equal(state.completedPhase, null);
});

test('a follow-up does not show stale activity from the previous photo', () => {
  const state = agentFlow(caseState('running', {
    photos: [{ id: 'photo-1' }, { id: 'photo-2' }],
    events: [{ photo_id: 'photo-1', kind: 'tool', status: 'ok', tool: 'finish_assessment' }],
  }));
  assert.equal(state.completedPhase, null);
  assert.equal(state.badge, 'SCOUT WORKING');
});

test('request and connection indicators stop when the corresponding condition clears', () => {
  assert.equal(agentFlow(null, { requestPending: true }).badge, 'STARTING');
  assert.equal(agentFlow(null).busy, undefined);
  const state = agentFlow(caseState('running'), { connectionLost: true });
  assert.equal(state.badge, 'RECONNECTING');
  assert.equal(state.phase, null);
  assert.equal(state.disconnected, true);
  assert.equal(agentFlow(caseState('complete')).busy, undefined);
});

test('direct classification has a busy state separate from the agent loop', () => {
  const state = agentFlow(caseState('complete', { baseline: { status: 'running' } }));
  assert.equal(state.busy, true);
  assert.equal(state.phase, null);
  assert.equal(state.title, 'Running your direct comparison');
  assert.equal(agentFlow(caseState('complete', { baseline: { status: 'complete' } })).busy, undefined);
});

test('cancellation remains visibly pending only while work is active', () => {
  assert.equal(agentFlow(caseState('running', { cancel_pending: true })).badge, 'STOPPING');
  const state = agentFlow(caseState('complete', { cancel_pending: true }));
  assert.equal(state.busy, undefined);
  assert.match(state.title, /results are ready/);
});


test('readiness fails closed until both components are explicitly available', () => {
  for (const health of [null, {}, {ready: true}, {ready: false, controller_ready: true, classifier_ready: true}]) assert.equal(runtimeReadiness(health).ready, false);
  for (const controller_ready of [false, true]) for (const classifier_ready of [false, true]) {
    const health = {ready: controller_ready && classifier_ready, controller_ready, classifier_ready};
    assert.equal(runtimeReadiness(health).ready, controller_ready && classifier_ready);
  }
  assert.match(runtimeReadiness({controller_ready: false, classifier_ready: true}).title, /language model/);
  assert.match(runtimeReadiness({controller_ready: true, classifier_ready: false}).title, /vision model/);
});

test('connection failure and recovery have no fake investigation activity', () => {
  const runtime = runtimeReadiness(null, {unreachable: true});
  assert.equal(runtime.ready, false);
  assert.equal(runtime.badge, 'CONNECTION UNAVAILABLE');
  for (const caseData of [null, caseState('complete'), caseState('awaiting_photo')]) {
    const state = agentFlow(caseData, {runtime});
    assert.equal(state.phase, null);
    assert.equal(!!state.busy, false);
    assert.equal(state.badge, runtime.badge);
  }
  assert.equal(agentFlow(caseState('running'), {runtime}).busy, true);
  const recovered = runtimeReadiness({ready: true, controller_ready: true, classifier_ready: true});
  assert.equal(agentFlow(null, {runtime: recovered}).tone, 'idle');
  assert.match(agentFlow(caseState('complete'), {runtime: recovered}).title, /results are ready/);
});
