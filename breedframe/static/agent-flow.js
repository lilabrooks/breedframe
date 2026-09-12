'use strict';

// UI state comes only from persisted case status and recorded events.
function agentFlow(caseData) {
  if (!caseData) return { phase: null, tone: 'idle' };
  const status = caseData.status;
  const event = caseData.events.at(-1);
  if (caseData.cancel_pending) return { phase: null, tone: 'paused', title: 'Cancellation requested.', detail: 'Waiting for the current bounded call to return. Recorded evidence stays in the case.' };
  if (status === 'ready') return { phase: null, tone: 'running', title: 'Investigation queued.', detail: 'Waiting for the local controller to start.' };
  if (status === 'running') {
    if (event?.kind === 'tool' && event.status === 'running') return { phase: 'execute', tone: 'running', title: 'Running the selected action.', detail: 'The tool call is in progress. Its result will appear in the timeline.' };
    return { phase: 'choose', tone: 'running', title: 'Choosing the next action.', detail: 'The controller is using case state and available tool results to choose what happens next.' };
  }
  if (status === 'awaiting_photo') return { phase: null, tone: 'paused', title: 'The agent is waiting for you.', detail: 'It requested another view. Add a follow-up photo to continue with the recorded evidence.' };
  if (status === 'incomplete') return { phase: null, tone: 'paused', title: 'Investigation stopped early.', detail: caseData.stop_reason || 'Completed observations are preserved. Review them or retry the remaining actions.' };
  if (status === 'complete') return { phase: null, tone: caseData.report?.outcome === 'inconclusive' ? 'inconclusive' : 'complete', title: caseData.report?.outcome === 'inconclusive' ? 'Investigation finished. Evidence inconclusive.' : 'Investigation finished. Assessment recorded.', detail: caseData.report?.completed_by === 'user' ? 'You saved a partial assessment. Review its evidence and limits below.' : 'Review the decisions in the timeline and the resulting assessment below.' };
  return { phase: null, tone: 'idle' };
}

function actionOrigin(event) {
  if (event.kind === 'user_region' || event.kind === 'user_action') return 'You';
  if (event.kind === 'controller_error') return 'Controller error';
  if (event.controller?.model) return `Controller · ${event.controller.model}`;
  return 'Application';
}

if (typeof module !== 'undefined') module.exports = { agentFlow, actionOrigin };
