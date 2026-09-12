'use strict';
const $ = id => document.getElementById(id);
let current = null, selectedFile = null, polling = null, lastVersion = '', pending = false;
const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; };
for (const link of document.querySelectorAll('.agent-jump')) link.addEventListener('click', event => {
  event.preventDefault();
  $('agent-workspace').scrollIntoView({ block: 'start' });
  $('agent-workspace').focus({ preventScroll: true });
});
const labels = { inspect_image: 'Inspect image quality', classify_breed: 'Run the breed classifier', classify_region: 'Classify your selected region', request_another_photo: 'Request another photo', finish_assessment: 'Finish the assessment' };
function error(message) { $('error').textContent = message; $('error').hidden = !message; }
async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(typeof body.detail === 'string' ? body.detail : 'The request could not be processed.'); }
  return response.json();
}
function active() { return pending || (current && (['ready','running'].includes(current.status) || current.baseline?.status === 'running')); }
function resumable() { return current && ['awaiting_photo','incomplete','complete'].includes(current.status) && current.photos.length < 3; }
function renderAgentState(caseData) {
  const state = agentFlow(caseData);
  $('agent-workspace').dataset.tone = state.tone;
  for (const phase of ['choose', 'execute', 'review']) {
    const step = $('flow-' + phase);
    step.classList.toggle('is-active', state.phase === phase);
    if (state.phase === phase) step.setAttribute('aria-current', 'step');
    else step.removeAttribute('aria-current');
  }
  if (state.title) $('status-title').textContent = state.title;
  if (state.detail) $('status-detail').textContent = state.detail;
  $('status-dot').classList.toggle('working', state.tone === 'running');
}
function controls() {
  $('case-management').hidden = !current;
  renderAgentState(current);
  for (const id of ['demo-clear','demo-small','demo-resume','baseline-button','new-case','region-save','retry-case','finish-partial','delete-case']) $(id).disabled = !!active();
  $('photo-input').disabled = !!active();
  $('upload-button').disabled = !selectedFile || !!active();
  $('upload-button').replaceChildren(document.createTextNode(selectedFile ? (resumable() ? 'Add photo & resume case' : 'Start local investigation') : 'Choose a photo first'), el('span', '', '↗'));
  if (current) {
    const p = current.photos.at(-1);
    $('region-editor').hidden = !!active() || !!p.regions?.length || (current.attempts[p.id] || 0) > 4;
    $('cancel-case').hidden = !['ready','running'].includes(current.status);
    $('cancel-case').disabled = !!current.cancel_pending;
    $('cancel-note').hidden = !current.cancel_pending;
    $('retry-case').hidden = current.status !== 'incomplete' || current.attempts[p.id] >= 6;
    $('finish-partial').hidden = !['awaiting_photo','incomplete'].includes(current.status);
    $('delete-case').hidden = false;
    $('report-export').hidden = false; $('report-export').href = `/api/cases/${current.id}/report`;
  }
  $('upload-label').textContent = selectedFile ? selectedFile.name : resumable() ? 'Add another view of the same dog.' : 'Choose a photo to investigate';
}
async function startRequest(url, options = {}) {
  pending = true; controls(); error('');
  try {
    current = await api(url, { method: 'POST', ...options });
    history.replaceState(null, '', '#'+current.id);
    lastVersion = ''; render(current); poll();
  } catch (e) { error(e.message); }
  finally { pending = false; controls(); }
}
function chooseFile(file) {
  if (!file) return;
  if (file.size > 12*1024*1024) return error('Choose a photo smaller than 12 MiB.');
  selectedFile = file; error(''); controls();
}
$('photo-input').addEventListener('change', e => chooseFile(e.target.files[0]));
$('upload-form').addEventListener('submit', async e => {
  e.preventDefault(); if (!selectedFile) return;
  const data = new FormData(); data.append('photo', selectedFile);
  const url = resumable() ? `/api/cases/${current.id}/photos` : '/api/cases';
  await startRequest(url, { body:data }); selectedFile = null; $('photo-input').value = ''; controls();
});
for (const name of ['dragenter','dragover']) $('drop-zone').addEventListener(name, e => { e.preventDefault(); $('drop-zone').classList.add('drag'); });
for (const name of ['dragleave','drop']) $('drop-zone').addEventListener(name, e => { e.preventDefault(); $('drop-zone').classList.remove('drag'); });
$('drop-zone').addEventListener('drop', e => { if (!active()) chooseFile(e.dataTransfer.files[0]); });
$('demo-clear').onclick = () => startRequest('/api/demo/clear');
$('demo-small').onclick = () => startRequest('/api/demo/small');
$('demo-resume').onclick = () => startRequest(`/api/cases/${current.id}/demo-resume`);
$('focus-upload').onclick = () => $('photo-input').click();
$('baseline-button').onclick = () => startRequest(`/api/cases/${current.id}/baseline`);
$('new-case').onclick = () => { location.href = '/'; };
function showPhoto(caseData, photo) {
  const image = el('img'); image.src = `/api/cases/${caseData.id}/photos/${photo.id}`; image.alt = `Case evidence ${photo.id}, ${photo.width} by ${photo.height} pixels`;
  $('photo-stage').replaceChildren(image, el('span','image-caption',`${photo.id.toUpperCase()} · ${photo.width} × ${photo.height} · LOCAL`));
}
function summarize(event) {
  const o = event.output || {};
  if (event.status === 'running') return 'Executing locally…';
  if (event.status === 'error') return o.error || 'The action failed validation or execution.';
  if (event.tool === 'inspect_image') return `${o.width} × ${o.height} pixels. ${o.quality_flags.length ? 'Quality concerns: '+o.quality_flags.join(', ').replaceAll('_',' ')+'.' : 'No pixel-quality flags.'} This does not confirm a dog is present.`;
  if (event.tool === 'classify_breed') return `Leading candidate: ${o.candidates[0].label.replaceAll('_',' ')} · raw score ${o.candidates[0].score.toFixed(3)}. ${o.device.toUpperCase()} inference.`;
  if (event.tool === 'request_another_photo') return `${o.why} Case paused.`;
  if (event.kind === 'user_region') return 'You selected a region on this photo. Its bounds and source are recorded.';
  if (event.kind === 'user_action') return o.action === 'finish_partial' ? 'You saved a partial assessment with the available evidence.' : 'You retried the case with its remaining action budget.';
  if (event.tool === 'classify_region') return `Actual inference on ${o.region_id}; this region shares its parent photo’s evidence.`;
  if (event.tool === 'finish_assessment' && o.version === 2) return o.comparison.summary;
  if (event.tool === 'finish_assessment') return o.outcome === 'inconclusive' ? 'The agent concluded that the evidence is insufficient.' : `The agent selected classifier event ${o.selected_result_id}. Scores copied from that result.`;
  return 'Recorded application event.';
}
function render(caseData) {
  const version = JSON.stringify(caseData);
  if (version === lastVersion) return;
  lastVersion = version;
  if (regionCaseId !== caseData.id || regionPhotoId !== caseData.photos.at(-1).id) $('region-editor').open = false;
  const openDetails = new Set([...document.querySelectorAll('[data-event][open]')].map(x => x.dataset.event));
  const scroll = $('trace').scrollTop;
  const followLatest = $('trace').scrollHeight - scroll - $('trace').clientHeight < 48;
  $('photo-count').textContent = `${caseData.photos.length} / 3 PHOTOS`;
  showPhoto(caseData, caseData.photos.at(-1));
  $('thumbnails').replaceChildren();
  if (caseData.photos.length > 1) for (const p of caseData.photos) {
    const b = el('button','thumb'); const im = el('img'); im.src = `/api/cases/${caseData.id}/photos/${p.id}`; im.alt = p.id;
    b.append(im, el('span','',`${p.width}×${p.height}`)); b.onclick = () => showPhoto(caseData,p); $('thumbnails').append(b);
  }
  const statuses = { ready: 'QUEUED', running: 'INVESTIGATING', awaiting_photo: 'WAITING FOR YOU', incomplete: 'INCOMPLETE', complete: 'ASSESSMENT RECORDED' };
  $('status').textContent = statuses[caseData.status] || 'READY';
  renderAgentState(caseData);
  $('activity-count').textContent = `${caseData.events.length} recorded ${caseData.events.length === 1 ? 'event' : 'events'}`;
  const controllerName = caseData.controller || caseData.events.findLast(event => event.controller?.model)?.controller.model || 'Local controller';
  $('controller-name').textContent = controllerName;
  $('trace').replaceChildren();
  for (const event of caseData.events) {
    const block = el('div','event'+(event.status === 'error' ? ' error-event' : event.status === 'running' ? ' running-event' : ''));
    const head = el('div','event-header');
    head.append(el('h3','',`${String(event.id).padStart(2,'0')}  ${labels[event.tool] || (event.kind === 'user_region' ? 'Region selected by you' : event.kind === 'user_action' ? 'Your case action' : 'Controller response rejected')}`), el('span','event-time',event.status === 'running' ? 'RUNNING' : `${event.status === 'error' ? 'FAILED · ' : ''}${((event.controller_seconds || 0)+(event.seconds || 0)).toFixed(1)}s`));
    const origin = el('div', 'event-origin');
    origin.append(el('span', 'actor', actionOrigin(event)));
    if (event.photo_id) origin.append(el('span', '', event.photo_id.replaceAll('-', ' ')));
    origin.append(el('span', '', event.status === 'running' ? 'In progress' : event.status === 'error' ? 'Failed' : 'Recorded'));
    block.append(el('span','event-dot'), head, origin, el('p','event-summary',summarize(event)));
    const detail = el('details'); detail.dataset.event = String(event.id); detail.open = openDetails.has(String(event.id));
    detail.append(el('summary','','Inspect input & result'), el('pre','',JSON.stringify({input:event.input,output:event.output,controller:event.controller},null,2)));
    block.append(detail); $('trace').append(block);
  }
  if (!caseData.events.length) $('trace').append(el('p','subtle','Waiting for the local controller’s first decision…'));
  $('trace').scrollTop = followLatest ? $('trace').scrollHeight : scroll;
  const photo = caseData.photos.at(-1);
  $('budget').textContent = `${caseData.attempts[photo.id] || 0} / 6 attempts · ${photo.id}`;
  $('duration').textContent = caseData.runs.length ? `${caseData.runs.reduce((s,r)=>s+r.seconds,0).toFixed(1)}s recorded · ${controllerName}` : `${controllerName} + ViT`;
  $('request-panel').hidden = caseData.status !== 'awaiting_photo';
  if (caseData.request) { $('request-text').textContent = caseData.request.message; $('request-why').textContent = caseData.request.why; }
  $('demo-resume').hidden = !caseData.demo || !resumable() || caseData.photos[0].width !== 48 || caseData.photos.length > 1;
  const ranks = caseData.events.filter(e => e.tool === 'classify_breed' && e.status === 'ok');
  const last = ranks.at(-1);
  const report = caseData.report;
  const comparison = report?.comparison || caseData.comparison;
  const candidates = report ? report.candidates : []; 
  $('result-tag').textContent = report && !report.version ? 'HISTORICAL REPORT' : report ? (report.completed_by === 'user' ? 'PARTIAL ASSESSMENT' : report.outcome === 'inconclusive' ? 'INCONCLUSIVE' : 'AGENT REPORT') : last ? 'PROVISIONAL EVIDENCE' : 'AWAITING EVIDENCE';
  $('report-intro').textContent = report?.version === 2 ? (report.outcome === 'inconclusive' ? 'No breed report. The observations below show what is known and what remains unresolved.' : 'Candidates ordered by agreement across photographs. Raw scores stay attached to each observation.') : report?.outcome === 'inconclusive' ? 'The agent declined to select a breed match. Earlier classifier results remain in the trace.' : candidates.length ? `Raw classifier scores on ${report ? 'selected' : 'latest'} photo. Alternative matches, not a breed mixture.` : last ? 'Provisional observations only; the investigation has not produced a final assessment.' : 'A ranked comparison will appear after a real classifier call.';
  $('candidates').replaceChildren();
  candidates.forEach((candidate,i) => {
    const row = el('div','candidate'), body = el('div');
    body.append(el('div','candidate-name',candidate.label.replaceAll('_',' ')+(candidate.unresolved_label ? ' · published label incomplete' : '')));
    const bar = el('div','bar'), fill = el('div','bar-fill'); fill.style.width = `${candidate.observations ? candidate.supporting_photo_ids.length / Math.max(1,comparison.ranked_photo_count)*100 : candidate.score*100}%`; bar.append(fill); body.append(bar);
    row.append(el('span','rank',String(i+1).padStart(2,'0')),body,el('span','score',candidate.observations ? `${candidate.supporting_photo_ids.length}/${comparison.ranked_photo_count} views` : candidate.score.toFixed(3))); $('candidates').append(row);
  });
  renderComparison(caseData, comparison);
  $('change').hidden = !report?.change; $('change').textContent = report?.change || '';
  $('uncertainty').hidden = !last && !report;
  $('uncertainty').replaceChildren();
  if (last && (last.output.margin < .15 || last.output.candidates[0].score < .5)) $('uncertainty').append(el('p','','Weak or closely ranked output. The leading score does not establish a confident match.'));
  if (report && !report.version) $('uncertainty').append(el('p','','Historical report: it was produced before the current comparison policy.'));
  if (comparison?.blockers) for (const message of comparison.blockers) $('uncertainty').append(el('p','',message));
  if (report?.quality_flags?.length) $('uncertainty').append(el('p','',`Unresolved quality concerns: ${report.quality_flags.join(', ').replaceAll('_',' ')}.`));
  if (last || report) $('uncertainty').append(el('p','','Breed identity remains unverified. This classifier can assign a dog breed to a non-dog image. The text controller cannot independently check visible features.'));
  $('ranking-history').hidden = !ranks.length;
  $('ranking-rows').replaceChildren(...ranks.map(e => el('p','',`Event ${e.id} · ${e.photo_id}: ${e.output.candidates.map(c => c.label.replaceAll('_',' ')+' '+c.score.toFixed(3)).join(' → ')}`)));
  $('baseline-area').hidden = ['ready','running'].includes(caseData.status);
  const baseline = caseData.baseline;
  $('baseline-result').replaceChildren();
  if (baseline) {
    const text = baseline.status === 'running' ? 'Running one direct classifier pass…' : baseline.status === 'failed' ? baseline.error : `${baseline.candidates[0].label.replaceAll('_',' ')} · ${baseline.candidates[0].score.toFixed(3)} raw score · ${baseline.seconds.toFixed(2)}s. One classifier call; no agent actions. Same current photo and processor.`;
    $('baseline-result').append(el('p','',text));
  }
  $('export').hidden = false; $('export').href = `/api/cases/${caseData.id}`; $('export').target = '_blank';
  controls();
}
function poll() {
  clearTimeout(polling);
  polling = setTimeout(async () => {
    if (!current) return;
    try { current = await api(`/api/cases/${current.id}`); render(current); if (active()) poll(); else loadCases(); }
    catch (e) { error('Progress connection interrupted. '+e.message); poll(); }
  },1000);
}
async function loadCases() {
  try {
    const cases = await api('/api/cases'); $('case-list').replaceChildren();
    for (const c of cases) {
      const b = el('button','',`${c.id.slice(0,8)} · ${c.status.replaceAll('_',' ')} · ${c.photos.length} photo(s)`);
      b.onclick = async () => { if (active()) return; current = await api(`/api/cases/${c.id}`); history.replaceState(null,'','#'+c.id); lastVersion=''; render(current); if(active()) poll(); };
      $('case-list').append(b);
    }
  } catch(e) { error(e.message); }
}
function renderComparison(caseData, comparison) {
  const host = $('comparison-views'); host.replaceChildren();
  if (!comparison) return;
  for (const view of comparison.views) {
    const card = el('section','evidence-view');
    const image = el('img'); image.src = `/api/cases/${caseData.id}/photos/${view.photo_id}`; image.alt = view.photo_id;
    card.append(image, el('h3','',view.photo_id.replace('-',' ').toUpperCase()));
    card.append(el('p','small',view.quality_flags.length ? 'Quality concerns: '+view.quality_flags.join(', ').replaceAll('_',' ') : view.inspection_event_id ? `Inspection event ${view.inspection_event_id}: no quality flag.` : 'Not yet inspected.'));
    for (const ranking of view.rankings) {
      if (ranking.region_id) {
        const crop = el('img'); crop.src = `/api/cases/${caseData.id}/photos/${view.photo_id}/regions/${ranking.region_id}`; crop.alt = 'Your selected region'; card.append(crop);
      }
      card.append(el('p','small',`Event ${ranking.event_id} · ${ranking.region_id ? 'your region' : 'whole photo'}${ranking.weak_scores ? ' · weak scores' : ''}`));
      for (const c of ranking.candidates) card.append(el('p','view-rank',`${c.label.replaceAll('_',' ')} · ${c.score.toFixed(3)}`));
    }
    if (!view.rankings.length) card.append(el('p','small','No classification recorded.'));
    host.append(card);
  }
}
$('finish-partial').onclick = () => startRequest(`/api/cases/${current.id}/finish-partial`);
$('retry-case').onclick = () => startRequest(`/api/cases/${current.id}/retry`);
$('cancel-case').onclick = async () => {
  try { await api(`/api/cases/${current.id}/cancel`, {method:'POST'}); current.cancel_pending = true; controls(); poll(); }
  catch(e) { error(e.message); }
};
$('delete-case').onclick = async () => {
  if (!confirm('Delete this case and all of its local photos and reports?')) return;
  try { await api(`/api/cases/${current.id}`, {method:'DELETE',headers:{'Content-Type':'application/json'},body:'{}'}); location.href='/'; }
  catch(e) { error(e.message); }
};
let regionImage = null, regionPhotoId = null, regionCaseId = null, box = null, dragStart = null;
const canvas = $('region-canvas');
function drawRegion() {
  if (!regionImage) return;
  const ctx = canvas.getContext('2d'); ctx.drawImage(regionImage,0,0,canvas.width,canvas.height);
  if (box) { ctx.strokeStyle='#e2fb8b'; ctx.lineWidth=3; ctx.strokeRect(box.left*canvas.width,box.top*canvas.height,(box.right-box.left)*canvas.width,(box.bottom-box.top)*canvas.height); }
}
$('region-editor').addEventListener('toggle', () => {
  if (!$('region-editor').open || !current) return;
  const p = current.photos.at(-1); regionPhotoId=p.id; regionCaseId=current.id; box=null; dragStart=null;
  for(const k of ['left','top','right','bottom']) $('region-'+k).value = ['left','top'].includes(k) ? '0' : '100';
  regionImage = new Image(); regionImage.onload = () => {
    canvas.width = Math.min(800,regionImage.naturalWidth); canvas.height = Math.round(canvas.width*regionImage.naturalHeight/regionImage.naturalWidth); drawRegion();
  };
  regionImage.src=`/api/cases/${current.id}/photos/${p.id}`;
});
function point(e) { const r=canvas.getBoundingClientRect(); return {x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))}; }
canvas.addEventListener('pointerdown',e=>{dragStart=point(e);canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{
  if(!dragStart)return; const p=point(e);
  box={left:Math.min(p.x,dragStart.x),top:Math.min(p.y,dragStart.y),right:Math.max(p.x,dragStart.x),bottom:Math.max(p.y,dragStart.y)};
  for(const k of ['left','top','right','bottom']) $('region-'+k).value=(box[k]*100).toFixed(1); drawRegion();
});
canvas.addEventListener('pointerup',()=>{dragStart=null;});
canvas.addEventListener('pointercancel',()=>{dragStart=null;});
for(const k of ['left','top','right','bottom']) $('region-'+k).oninput=()=>{
  box=Object.fromEntries(['left','top','right','bottom'].map(key=>[key,Number($('region-'+key).value)/100])); drawRegion();
};
$('region-save').onclick=async()=>{
  if (!regionPhotoId || regionPhotoId !== current.photos.at(-1).id || regionCaseId !== current.id) return error('Reopen region selection for the current photo.');
  const bounds=Object.fromEntries(['left','top','right','bottom'].map(key=>[key,Number($('region-'+key).value)/100]));
  await startRequest(`/api/cases/${current.id}/regions`,{headers:{'Content-Type':'application/json'},body:JSON.stringify({photo_id:regionPhotoId,...bounds})});
  $('region-editor').open=false;
};
async function initialize() {
  try {
    const health = await api('/api/health'); $('runtime').textContent = health.ready ? '● LOCAL MODELS READY' : '○ SETUP REQUIRED';
    $('controller-name').textContent = health.controller || 'Local controller';
    if (!health.ready) error(`${health.detail} ${health.classifier_ready ? '' : 'Classifier files are missing. Run setup.'}`);
    const id = location.hash.slice(1);
    if (/^[a-f0-9]{32}$/.test(id)) { current = await api(`/api/cases/${id}`); render(current); if(active()) poll(); }
    await loadCases();
  } catch(e) { error(e.message); }
}
initialize();
