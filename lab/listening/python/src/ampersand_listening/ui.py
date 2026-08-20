# ruff: noqa: E501, RUF001

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ampersand Blinded Listening Lab</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    body { margin: 0; background: #090d14; color: #eef3fb; }
    main { width: min(1080px, calc(100% - 32px)); margin: 32px auto 80px; }
    header, .panel { background: #111925; border: 1px solid #27374c; border-radius: 18px; padding: 22px; }
    header { background: linear-gradient(135deg, #142136, #101823 65%); }
    h1, h2, h3 { margin-top: 0; }
    .muted { color: #9fb0c7; }
    .notice { margin: 18px 0; padding: 14px 16px; border-left: 4px solid #54d6be; background: #10231f; }
    .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(270px, 1fr)); }
    .option { border: 1px solid #30445f; border-radius: 14px; padding: 16px; background: #0d1520; }
    audio { width: 100%; margin: 8px 0 14px; }
    label { display: block; margin: 10px 0 5px; font-weight: 650; }
    input, select, textarea, button { font: inherit; }
    input[type=text], select, textarea { width: 100%; box-sizing: border-box; background: #09111b; color: #eef3fb; border: 1px solid #3a4d67; border-radius: 9px; padding: 9px; }
    textarea { min-height: 80px; }
    .checks { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 7px 12px; }
    .checks label, .choice { font-weight: 450; margin: 0; }
    button { border: 0; border-radius: 10px; padding: 11px 16px; cursor: pointer; background: #54d6be; color: #07110f; font-weight: 750; }
    button.secondary { background: #293b54; color: #eef3fb; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    .hidden { display: none; }
    .status { margin: 14px 0; min-height: 24px; color: #ffd282; }
    pre { overflow: auto; max-height: 520px; padding: 14px; background: #07101a; border-radius: 10px; white-space: pre-wrap; }
  </style>
</head>
<body>
<main>
  <header>
    <p class="muted">Local-only · identities hidden until close</p>
    <h1>Ampersand Blinded Listening Lab</h1>
    <p>Compare loudness-matched options on the same playback setup. Human judgment is the quality gate; measurements are diagnostic only.</p>
  </header>

  <div class="notice" id="instructions">Loading session…</div>

  <section class="panel">
    <label for="listener">Listener pseudonym</label>
    <input id="listener" type="text" value="listener:local-1" pattern="[a-z0-9][a-z0-9._:-]+" autocomplete="off">
    <p class="muted">Use an opaque ID—never a name, email, or customer identifier.</p>
  </section>

  <section class="panel" id="trial" style="margin-top:16px"></section>
  <div class="status" id="status" role="status" aria-live="polite"></div>
  <div class="actions">
    <button id="submit">Submit trial</button>
    <button id="next" class="secondary" disabled>Next trial</button>
    <button id="close" class="secondary">Close and reveal</button>
  </div>
  <section id="report" class="panel hidden" style="margin-top:16px">
    <h2>Closed report</h2>
    <p class="muted">Identity and processor metadata are visible only after close.</p>
    <pre id="report-json"></pre>
  </section>
</main>
<script>
let session;
let index = 0;
let submitted = new Set();
const $ = (id) => document.getElementById(id);
const scoreOptions = '<option value="">Choose…</option>' + [1,2,3,4,5].map(n => `<option value="${n}">${n}</option>`).join('');

async function request(path, options={}) {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function checkboxGroup(name, values) {
  const wrapper = document.createElement('div');
  wrapper.className = 'checks';
  for (const value of values) {
    const label = document.createElement('label');
    const input = document.createElement('input');
    input.type = 'checkbox'; input.name = name; input.value = value;
    label.append(input, ` ${value.replaceAll('_',' ')}`);
    wrapper.append(label);
  }
  return wrapper;
}

function renderTrial() {
  const trial = session.trials[index];
  const root = $('trial'); root.replaceChildren();
  const heading = document.createElement('h2');
  heading.textContent = `Trial ${index + 1} of ${session.trials.length}`;
  const prompt = document.createElement('p'); prompt.textContent = trial.evaluation_prompt;
  root.append(heading, prompt);
  const grid = document.createElement('div'); grid.className = 'grid';
  trial.options.forEach((option, optionIndex) => {
    const card = document.createElement('article'); card.className = 'option';
    const title = document.createElement('h3'); title.textContent = `Option ${optionIndex + 1}`;
    const audio = document.createElement('audio'); audio.controls = true; audio.preload = 'metadata'; audio.src = option.audio_relative_path;
    card.append(title, audio);
    for (const [field,label] of [['speech_quality','Speech quality'],['background_quality','Background quality'],['overall_quality','Overall quality']]) {
      const lab = document.createElement('label'); lab.htmlFor = `${field}-${option.option_id}`; lab.textContent = `${label} (1–5)`;
      const select = document.createElement('select'); select.id = `${field}-${option.option_id}`; select.dataset.field = field; select.dataset.option = option.option_id; select.innerHTML = scoreOptions;
      card.append(lab, select);
    }
    const artifactTitle = document.createElement('label'); artifactTitle.textContent = 'Artifacts heard in this option';
    card.append(artifactTitle, checkboxGroup(`artifact-${option.option_id}`, session.artifact_flags));
    grid.append(card);
  });
  root.append(grid);
  const preference = document.createElement('div'); preference.style.marginTop = '18px';
  const prefTitle = document.createElement('h3'); prefTitle.textContent = 'Preference'; preference.append(prefTitle);
  trial.options.forEach((option, optionIndex) => {
    const label = document.createElement('label'); label.className = 'choice';
    const radio = document.createElement('input'); radio.type='radio'; radio.name='preference'; radio.value=option.option_id;
    label.append(radio, ` Option ${optionIndex + 1}`); preference.append(label);
  });
  const noLabel = document.createElement('label'); noLabel.className='choice';
  const noRadio = document.createElement('input'); noRadio.type='radio'; noRadio.name='preference'; noRadio.value='no_preference';
  noLabel.append(noRadio, ' No meaningful preference'); preference.append(noLabel);
  root.append(preference);
  const trialFlagsTitle = document.createElement('h3'); trialFlagsTitle.textContent='Trial-level artifacts or transitions';
  root.append(trialFlagsTitle, checkboxGroup('trial-artifact', session.artifact_flags));
  if (trial.mode === 'clean_preservation') {
    const clean = document.createElement('div'); clean.id='clean-answers'; clean.innerHTML='<h3>Clean-input preservation</h3>';
    for (const [field,label] of [
      ['audible_degradation','Any audible degradation?'],['voice_identity_changed','Voice identity/timbre changed?'],
      ['speech_less_natural','Speech less natural?'],['ambience_or_music_changed','Ambience or music changed unnaturally?'],
      ['processing_preferred','Would you prefer processing?']]) {
      const lab=document.createElement('label'); lab.htmlFor=field; lab.textContent=label;
      const select=document.createElement('select'); select.id=field; select.innerHTML='<option value="false">No</option><option value="true">Yes</option>';
      clean.append(lab,select);
    }
    root.append(clean);
  }
  const confLabel=document.createElement('label'); confLabel.htmlFor='confidence'; confLabel.textContent='Confidence (1–5)';
  const conf=document.createElement('select'); conf.id='confidence'; conf.innerHTML=scoreOptions;
  const notesLabel=document.createElement('label'); notesLabel.htmlFor='notes'; notesLabel.textContent='Private notes (optional; no personal data)';
  const notes=document.createElement('textarea'); notes.id='notes';
  root.append(confLabel,conf,notesLabel,notes);
  $('submit').disabled = submitted.has(trial.trial_id);
  $('next').disabled = !submitted.has(trial.trial_id) || index >= session.trials.length - 1;
}

function checked(name) { return [...document.querySelectorAll(`input[name="${CSS.escape(name)}"]:checked`)].map(x=>x.value); }

function scoreValue(selector, label) {
  const value = document.querySelector(selector).value;
  if (!value) throw new Error(`Choose a ${label} score for every option.`);
  return Number(value);
}

async function submitTrial() {
  const trial=session.trials[index];
  const preference=document.querySelector('input[name="preference"]:checked');
  if (!preference) throw new Error('Choose a preferred option or no meaningful preference.');
  const ratings=trial.options.map(option => ({
    option_id: option.option_id,
    speech_quality: scoreValue(`[data-field="speech_quality"][data-option="${option.option_id}"]`, 'speech quality'),
    background_quality: scoreValue(`[data-field="background_quality"][data-option="${option.option_id}"]`, 'background quality'),
    overall_quality: scoreValue(`[data-field="overall_quality"][data-option="${option.option_id}"]`, 'overall quality'),
    artifact_flags: checked(`artifact-${option.option_id}`)
  }));
  const payload={
    listener_id:$('listener').value.trim(), trial_id:trial.trial_id,
    preferred_option_id:preference.value==='no_preference'?null:preference.value,
    no_meaningful_preference:preference.value==='no_preference', option_ratings:ratings,
    confidence:scoreValue('#confidence', 'confidence'), trial_artifact_flags:checked('trial-artifact'),
    notes:$('notes').value.trim()||null
  };
  if (trial.mode==='clean_preservation') for (const field of ['audible_degradation','voice_identity_changed','speech_less_natural','ambience_or_music_changed','processing_preferred']) payload[field]=$(`${field}`).value==='true';
  await request('/api/scores',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  submitted.add(trial.trial_id); $('status').textContent='Score stored privately.'; renderTrial();
}

async function closeAndReveal() {
  if (!window.confirm('Close scoring permanently and reveal candidate identities?')) return;
  await request('/api/close',{method:'POST'});
  const report=await request('/api/reveal');
  $('report-json').textContent=JSON.stringify(report,null,2); $('report').classList.remove('hidden');
  $('submit').disabled=true; $('next').disabled=true; $('close').disabled=true; $('status').textContent='Session closed. Identities revealed below.';
}

$('submit').addEventListener('click',()=>submitTrial().catch(e=>$('status').textContent=e.message));
$('next').addEventListener('click',()=>{ if(index<session.trials.length-1){index++;renderTrial();$('status').textContent='';} });
$('close').addEventListener('click',()=>closeAndReveal().catch(e=>$('status').textContent=e.message));

(async()=>{
  try {
    session=await request('/session.json');
    $('instructions').textContent=session.instructions.join(' ');
    const status=await request('/api/status'); submitted=new Set(status.submitted_trial_ids||[]);
    renderTrial();
    if(status.state==='closed'){ const report=await request('/api/reveal'); $('report-json').textContent=JSON.stringify(report,null,2); $('report').classList.remove('hidden'); $('close').disabled=true; }
  } catch(e) { $('status').textContent=e.message; }
})();
</script>
</body>
</html>
"""
