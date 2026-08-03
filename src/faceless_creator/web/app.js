
const state = {
  projects: [],
  project: null,
  selectedSceneId: null,
  polling: null,
};

const elements = Object.fromEntries(
  [...document.querySelectorAll('[id]')].map((element) => [element.id.replace(/-([a-z])/g, (_, char) => char.toUpperCase()), element]),
);

const statusLabels = {
  draft: 'Borrador',
  review: 'Esperando revisión',
  completed: 'Completado',
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error?.message || 'La operación no pudo completarse.');
  return value;
}

function showNotice(message = '') {
  elements.notice.textContent = message;
  elements.notice.hidden = !message;
}

async function initialize() {
  bindEvents();
  try {
    const health = await api('/api/health');
    elements.systemStatus.classList.add('online');
    elements.systemStatus.lastElementChild.textContent = health.ffmpeg ? 'Sistema listo' : 'FFmpeg no disponible';
    await loadProjects();
  } catch (error) {
    elements.systemStatus.lastElementChild.textContent = 'Sin conexión local';
    showNotice(error.message);
  }
}

function bindEvents() {
  elements.newProjectButton.addEventListener('click', openProjectDialog);
  elements.emptyCreateButton.addEventListener('click', openProjectDialog);
  elements.projectForm.addEventListener('submit', createProject);
  elements.refreshButton.addEventListener('click', () => refreshCurrent());
  elements.prepareButton.addEventListener('click', () => startJob(`/api/projects/${state.project.id}/prepare-demo`, 'Preparando insumos'));
  elements.previewButton.addEventListener('click', () => startJob(`/api/projects/${state.project.id}/preview`, 'Generando preview'));
  elements.exportButton.addEventListener('click', () => startJob(`/api/projects/${state.project.id}/export`, 'Exportando video'));
  elements.alternativesButton.addEventListener('click', loadAlternatives);
  elements.openPreviewButton.addEventListener('click', openPreviewExternally);
  elements.audioInput.addEventListener('change', importSelectedAudio);
}

function openProjectDialog() {
  elements.projectName.value = '';
  elements.projectDialog.showModal();
  requestAnimationFrame(() => elements.projectName.focus());
}

async function createProject(event) {
  event.preventDefault();
  const name = elements.projectName.value.trim();
  if (!name) return;
  elements.createProjectSubmit.disabled = true;
  try {
    const project = await api('/api/projects', { method: 'POST', body: JSON.stringify({ name }) });
    elements.projectDialog.close();
    await loadProjects(project.id);
  } catch (error) {
    showNotice(error.message);
  } finally {
    elements.createProjectSubmit.disabled = false;
  }
}

async function loadProjects(selectId = null) {
  const value = await api('/api/projects');
  state.projects = value.projects;
  renderProjectList();
  const target = selectId || state.project?.id || state.projects[0]?.id;
  if (target) await selectProject(target);
  else renderEmpty();
}

function renderProjectList() {
  elements.projectList.replaceChildren();
  for (const project of state.projects) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `project-link${project.id === state.project?.id ? ' active' : ''}`;
    button.innerHTML = `<strong></strong><span></span>`;
    button.querySelector('strong').textContent = project.name;
    button.querySelector('span').textContent = `${statusLabels[project.status] || project.status} · Plan v${project.plan_version}`;
    button.addEventListener('click', () => selectProject(project.id));
    elements.projectList.append(button);
  }
}

function renderEmpty() {
  state.project = null;
  elements.emptyState.hidden = false;
  elements.projectView.hidden = true;
}

async function selectProject(projectId) {
  stopPolling();
  showNotice();
  state.project = await api(`/api/projects/${projectId}`);
  state.selectedSceneId = state.project.render_plan?.scenes[0]?.id || null;
  renderProjectList();
  renderProject();
  const active = state.project.jobs.find((job) => ['queued', 'running'].includes(job.status));
  if (active) pollJob(active.id, active.kind);
}

async function refreshCurrent() {
  if (!state.project) return loadProjects();
  state.project = await api(`/api/projects/${state.project.id}`);
  renderProjectList();
  renderProject();
}

function renderProject() {
  const project = state.project;
  elements.emptyState.hidden = true;
  elements.projectView.hidden = false;
  elements.projectTitle.textContent = project.name;
  elements.projectStatus.textContent = statusLabels[project.status] || project.status;
  elements.projectStage.textContent = project.render_plan ? 'Producción activa' : 'Proyecto nuevo';
  elements.setupPanel.hidden = Boolean(project.render_plan);
  elements.productionPanel.hidden = !project.render_plan;
  renderAudio(project.audio);
  setStages(project);
  if (!project.render_plan) return;

  const plan = project.render_plan;
  elements.planVersion.textContent = `PLAN V${plan.version}`;
  elements.timelineDuration.textContent = formatDuration(plan.duration);
  if (!plan.scenes.some((scene) => scene.id === state.selectedSceneId)) state.selectedSceneId = plan.scenes[0].id;
  renderScenes();
  renderPreview();
  renderArtifacts();
}

function renderAudio(audio) {
  elements.prepareButton.disabled = !audio;
  if (!audio) {
    elements.audioName.textContent = 'Ningún audio agregado';
    elements.audioDetail.textContent = 'Selecciona la narración existente.';
    return;
  }
  elements.audioName.textContent = audio.original_name;
  elements.audioDetail.textContent = `${formatDuration(audio.duration)} · ${audio.format.toUpperCase()} · ${formatBytes(audio.size)}`;
}

async function importSelectedAudio() {
  const [file] = elements.audioInput.files;
  if (!file || !state.project) return;
  elements.audioInput.disabled = true;
  elements.prepareButton.disabled = true;
  showNotice();
  elements.audioName.textContent = 'Validando audio…';
  elements.audioDetail.textContent = file.name;
  try {
    state.project = await api(`/api/projects/${state.project.id}/audio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/octet-stream',
        'X-Filename': encodeURIComponent(file.name),
      },
      body: file,
    });
    renderProjectList();
    renderProject();
  } catch (error) {
    showNotice(error.message);
    renderAudio(state.project.audio);
  } finally {
    elements.audioInput.value = '';
    elements.audioInput.disabled = false;
  }
}

function setStages(project) {
  const preview = currentArtifact('preview');
  const exported = currentArtifact('export');
  const done = new Set();
  if (project.render_plan) done.add('inputs').add('plan');
  if (preview) done.add('preview');
  if (exported) done.add('export');
  document.querySelectorAll('.stage-nav li').forEach((item) => item.classList.toggle('done', done.has(item.dataset.stage)));
}

function renderScenes() {
  const plan = state.project.render_plan;
  const scriptById = Object.fromEntries(state.project.script.blocks.map((block) => [block.id, block]));
  elements.sceneList.replaceChildren();
  for (const scene of plan.scenes) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'scene-item';
    button.setAttribute('role', 'option');
    button.setAttribute('aria-selected', String(scene.id === state.selectedSceneId));
    button.innerHTML = '<span></span><strong></strong>';
    button.querySelector('span').textContent = `${scene.start.toFixed(1)}–${scene.end.toFixed(1)} s`;
    button.querySelector('strong').textContent = scriptById[scene.block_id]?.text || scene.id;
    button.addEventListener('click', () => {
      state.selectedSceneId = scene.id;
      renderScenes();
      renderPreview();
    });
    elements.sceneList.append(button);
  }
  renderInspector();
}

function renderInspector() {
  const scene = selectedScene();
  if (!scene) return;
  const block = state.project.script.blocks.find((item) => item.id === scene.block_id);
  elements.sceneTitle.textContent = `Escena ${scene.order + 1}`;
  elements.sceneStart.textContent = `${scene.start.toFixed(1)} s`;
  elements.sceneDuration.textContent = `${scene.duration.toFixed(1)} s`;
  elements.sceneText.textContent = block?.text || '';
  elements.sceneInstruction.textContent = scene.visual_instruction;
  elements.alternatives.hidden = true;
  elements.alternatives.replaceChildren();
}

function renderPreview() {
  const preview = currentArtifact('preview');
  const scene = selectedScene();
  elements.videoPreview.hidden = true;
  elements.sceneImage.hidden = true;
  elements.previewPlaceholder.hidden = false;
  elements.openPreviewButton.hidden = !preview;
  if (preview) {
    const source = `/api/artifacts/${preview.id}`;
    if (elements.videoPreview.dataset.artifact !== preview.id) {
      elements.videoPreview.src = source;
      elements.videoPreview.dataset.artifact = preview.id;
    }
    elements.videoPreview.hidden = false;
    elements.previewPlaceholder.hidden = true;
    elements.previewTitle.textContent = 'Preview vigente';
  } else if (scene) {
    const imageArtifactUrl = sceneImageUrl(scene.image_path);
    elements.sceneImage.src = imageArtifactUrl;
    elements.sceneImage.alt = scene.visual_instruction;
    elements.sceneImage.hidden = false;
    elements.previewPlaceholder.hidden = true;
    elements.previewTitle.textContent = `Escena ${scene.order + 1} · imagen seleccionada`;
  }
}

function sceneImageUrl(relativePath) {
  const projectId = state.project.id;
  return `/api/projects/${projectId}/assets/${relativePath.split('/').map(encodeURIComponent).join('/')}`;
}

function currentArtifact(kind) {
  const versionToken = `-v${state.project.plan_version}.`;
  return state.project.artifacts.find((artifact) => artifact.kind === kind && artifact.relative_path.includes(versionToken));
}

function renderArtifacts() {
  const exportArtifact = currentArtifact('export');
  elements.outputCard.hidden = !exportArtifact;
  elements.artifactList.replaceChildren();
  if (!exportArtifact) return;
  for (const artifact of state.project.artifacts.filter((item) => item.relative_path.includes(`-v${state.project.plan_version}.`))) {
    const link = document.createElement('a');
    link.className = 'artifact-link';
    link.href = `/api/artifacts/${artifact.id}`;
    link.addEventListener('click', (event) => {
      event.preventDefault();
      openArtifactExternally(artifact.id);
    });
    link.innerHTML = '<span></span><span></span>';
    link.firstElementChild.textContent = artifact.kind;
    link.lastElementChild.textContent = formatBytes(artifact.size);
    elements.artifactList.append(link);
  }
}

async function startJob(path, label) {
  setBusy(true);
  showNotice();
  try {
    const job = await api(path, { method: 'POST', body: '{}' });
    pollJob(job.id, label);
  } catch (error) {
    setBusy(false);
    showNotice(error.message);
  }
}

function pollJob(jobId, label) {
  stopPolling();
  elements.jobCard.hidden = false;
  elements.jobLabel.textContent = humanJobLabel(label);
  const tick = async () => {
    try {
      const job = await api(`/api/jobs/${jobId}`);
      elements.jobProgress.style.width = `${job.progress}%`;
      elements.jobProgressLabel.textContent = `${job.progress}%`;
      if (['queued', 'running'].includes(job.status)) {
        state.polling = window.setTimeout(tick, 500);
        return;
      }
      stopPolling();
      setBusy(false);
      if (job.status === 'succeeded') {
        await refreshCurrent();
      } else {
        showNotice(job.error_message || 'El trabajo se interrumpió. Puedes volver a intentarlo.');
        await refreshCurrent();
      }
    } catch (error) {
      stopPolling();
      setBusy(false);
      showNotice(error.message);
    }
  };
  tick();
}

function stopPolling() {
  if (state.polling) window.clearTimeout(state.polling);
  state.polling = null;
}

function setBusy(value) {
  for (const button of [elements.prepareButton, elements.previewButton, elements.exportButton]) button.disabled = value;
  if (!value) elements.jobCard.hidden = true;
}

async function loadAlternatives() {
  const scene = selectedScene();
  if (!scene) return;
  elements.alternativesButton.disabled = true;
  try {
    const value = await api(`/api/projects/${state.project.id}/scenes/${encodeURIComponent(scene.id)}/alternatives`);
    elements.alternatives.replaceChildren();
    if (!value.alternatives.length) {
      elements.alternatives.textContent = 'No se encontraron alternativas.';
    }
    for (const alternative of value.alternatives) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'alternative-button';
      button.textContent = alternative.label;
      button.addEventListener('click', () => replaceVisual(scene.id, alternative.relative_path));
      elements.alternatives.append(button);
    }
    elements.alternatives.hidden = false;
  } catch (error) {
    showNotice(error.message);
  } finally {
    elements.alternativesButton.disabled = false;
  }
}

async function replaceVisual(sceneId, relativePath) {
  setBusy(true);
  try {
    state.project = await api(`/api/projects/${state.project.id}/scenes/${encodeURIComponent(sceneId)}/replace`, {
      method: 'POST',
      body: JSON.stringify({ relative_path: relativePath }),
    });
    state.selectedSceneId = sceneId;
    renderProjectList();
    renderProject();
  } catch (error) {
    showNotice(error.message);
  } finally {
    setBusy(false);
  }
}

async function openPreviewExternally() {
  const preview = currentArtifact('preview');
  if (!preview) return;
  await openArtifactExternally(preview.id);
}

async function openArtifactExternally(artifactId) {
  try {
    await api(`/api/artifacts/${artifactId}/open`, { method: 'POST', body: '{}' });
  } catch (error) {
    showNotice(error.message);
  }
}

function selectedScene() {
  return state.project?.render_plan?.scenes.find((scene) => scene.id === state.selectedSceneId) || null;
}

function humanJobLabel(value) {
  const labels = { prepare: 'Preparando insumos', preview: 'Generando preview', export: 'Exportando video' };
  return labels[value] || value;
}

function formatDuration(seconds) {
  const value = Math.round(seconds);
  return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`;
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

initialize();
