'use strict';

const toolActivity = {
  inspect_image: ['Checking photo quality', 'Measuring image size, brightness, and detail before comparing breeds.'],
  classify_breed: ['Vision model is comparing breeds', 'The vision model is reading this photo and ranking its matches across 120 breeds. Scout will use those results to choose the next step.'],
  classify_region: ['Vision model is analyzing your selection', 'The vision model is comparing the area you selected with its known breed classes.'],
  request_another_photo: ['Scout is requesting another photo', 'Recording which additional view could help this case, based on the evidence collected so far.'],
  finish_assessment: ['Preparing your assessment', 'BreedFrame is assembling the recorded rankings and notes into your result.'],
};

function runtimeReadiness(health, { checking = false, unreachable = false } = {}) {
  if (unreachable) return { ready: false, badge: 'CONNECTION UNAVAILABLE', title: 'Scout can’t reach the local app.', detail: 'Keep the startup terminal running, then choose Check again. Your saved cases remain on this Mac.' };
  if (checking || !health) return { ready: false, badge: 'CHECKING MODELS', title: 'Checking Scout’s local models…', detail: 'A quick availability check before you start an investigation.' };
  if (health.ready === true && health.controller_ready === true && health.classifier_ready === true) return { ready: true, badge: 'LOCAL MODELS READY' };
  const title = !health.controller_ready && !health.classifier_ready ? 'Let’s get Scout’s local models ready.' : !health.controller_ready ? 'Scout’s language model isn’t ready yet.' : 'The vision model isn’t ready yet.';
  return { ready: false, badge: 'SETUP REQUIRED', title, detail: 'Investigations are disabled until both local models are available. Follow the setup steps below, then choose Check again. You can still open saved cases.' };
}

// Progress follows recorded work. Request and connection states describe the browser's own activity.
function agentFlow(caseData, { requestPending = false, connectionLost = false, runtime = null } = {}) {
  if (connectionLost) return { phase: null, tone: 'paused', busy: true, badge: 'RECONNECTING', title: 'Checking the progress connection', detail: 'Live updates were interrupted. Reconnecting to check whether the investigation is still running.', disconnected: true };
  if (requestPending) return { phase: null, tone: 'running', busy: true, badge: 'STARTING', title: 'Sending your request', detail: 'Preparing your photo or selected action in the local workspace.' };
  if (runtime && !runtime.ready && !(['ready', 'running'].includes(caseData?.status) || caseData?.baseline?.status === 'running')) return { phase: null, tone: 'paused', ...runtime };
  if (!caseData) return { phase: null, tone: 'idle', title: 'Scout is ready to investigate.', detail: 'Add a photo and follow Scout as it chooses tools, collects their results, and decides what to do next.' };
  const status = caseData.status;
  const photoId = caseData.photos?.at(-1)?.id;
  const event = caseData.events.findLast(e => !photoId || e.photo_id === photoId);
  if (caseData.cancel_pending && ['ready', 'running'].includes(status)) return { phase: null, tone: 'paused', busy: true, badge: 'STOPPING', title: 'Cancellation requested.', detail: 'Waiting for the current bounded call to return. Recorded evidence stays in the case.' };
  if (caseData.baseline?.status === 'running') return { phase: null, tone: 'running', busy: true, badge: 'COMPARING', title: 'Running your direct comparison', detail: 'The vision model is classifying this photo once, independently of the agent’s decisions.' };
  if (status === 'ready') return { phase: null, tone: 'running', busy: true, badge: 'QUEUED', title: 'Scout’s investigation is queued', detail: 'Scout will choose the first action when the local controller starts.' };
  if (status === 'running') {
    if (event?.kind === 'tool' && event.status === 'running') {
      const [title, detail] = toolActivity[event.tool] || ['Running the selected action', 'The tool is working locally. Its result will appear in the timeline.'];
      return { phase: 'execute', completedPhase: 'choose', tone: 'running', busy: true, badge: 'TOOL RUNNING', title, detail };
    }
    const returned = event?.kind === 'tool' && event.status === 'ok';
    return { phase: 'choose', completedPhase: returned ? 'review' : null, tone: 'running', busy: true, badge: returned ? 'RESULT RECEIVED' : 'SCOUT WORKING', title: returned ? 'Scout is reviewing the results' : 'Scout is choosing the next step', detail: returned ? 'The tool result is recorded. Scout is deciding whether to gather more evidence, request a photo, or finish.' : 'Scout’s language model is reviewing recorded evidence and selecting an action for the local tools.' };
  }
  if (status === 'awaiting_photo') return { phase: null, tone: 'paused', title: 'Scout is waiting for another photo.', detail: 'Scout requested another view. Add a follow-up photo to continue with the recorded evidence.' };
  if (status === 'incomplete') return { phase: null, tone: 'paused', title: 'Scout’s investigation stopped early.', detail: caseData.stop_reason || 'Completed observations are preserved. Review them or retry the remaining actions.' };
  if (status === 'complete') return { phase: null, tone: caseData.report?.outcome === 'inconclusive' ? 'inconclusive' : 'complete', title: 'Investigation finished. Your results are ready.', detail: caseData.report?.completed_by === 'user' ? 'You saved a partial assessment. Review the available matches and notes below.' : 'Review the visual matches and model scores in your assessment below.' };
  return { phase: null, tone: 'idle' };
}

function actionOrigin(event) {
  if (event.kind === 'user_region' || event.kind === 'user_action') return 'You';
  if (event.kind === 'controller_error') return 'Controller error';
  if (event.controller?.model) return 'Scout · chose this action';
  return 'Application';
}

if (typeof module !== 'undefined') module.exports = { agentFlow, actionOrigin, runtimeReadiness };
