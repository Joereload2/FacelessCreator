


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
    await loadPackageList();
  } catch (error) {
    elements.systemStatus.lastElementChild.textContent = 'Sin conexión local';
    showNotice(error.message);
  }
}

async function loadPackageList() {
  if (!elements.packageSelect) return;
  try {
    const value = await api('/api/packages');
    const current = elements.packageSelect.value;
    elements.packageSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = '— Packages FacelessStudio —';
    elements.packageSelect.append(placeholder);
    for (const item of value.packages || []) {
      const option = document.createElement('option');
      option.value = item.path;
      option.textContent = `${item.title || item.package_id} (${item.beats || 0} beats)`;
      elements.packageSelect.append(option);
    }
    if (current) elements.packageSelect.value = current;
  } catch (error) {
    showNotice(error.message);
  }
}

async function importSelectedPackage() {
  if (!state.project) {
    showNotice('Crea o selecciona un proyecto antes de importar.');
    return;
  }
  const packagePath = elements.packageSelect?.value;
  if (!packagePath) {
    showNotice('Elige un package de la lista (exporta antes desde YouToMagic).');
    return;
  }
  elements.importPackageButton.disabled = true;
  try {
    await startJob(
      `/api/projects/${state.project.id}/import-package`,
      'Importando package (TTS stub + plan)',
      { package_path: packagePath },
    );
  } finally {
    elements.importPackageButton.disabled = false;
  }
}

function bindEvents() {
  elements.newProjectButton.addEventListener('click', openProjectDialog);
  elements.emptyCreateButton.addEventListener('click', openProjectDialog);
  elements.projectForm.addEventListener('submit', createProject);
  elements.refreshButton.addEventListener('click', () => refreshCurrent());
  elements.primaryActionButton.addEventListener('click', runPrimaryAction);
  elements.alternativesButton.addEventListener('click', loadAlternatives);
  elements.openPreviewButton.addEventListener('click', openPreviewExternally);
  elements.audioInput.addEventListener('change', importSelectedAudio);
  if (elements.refreshPackagesButton) {
    elements.refreshPackagesButton.addEventListener('click', loadPackageList);
  }
  if (elements.importPackageButton) {
    elements.importPackageButton.addEventListener('click', importSelectedPackage);
  }
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
  elements.projectContext.hidden = true;
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
  elements.projectContext.hidden = false;
  elements.projectTitle.textContent = project.name;
  elements.projectStatus.textContent = statusLabels[project.status] || project.status;
  elements.projectStage.textContent = currentStageLabel(project);
  elements.setupPanel.hidden = Boolean(project.render_plan);
  elements.productionPanel.hidden = !project.render_plan;
  elements.operationBar.hidden = !project.render_plan;
  renderInputs(project);
  renderPrimaryAction(project);
  if (!project.render_plan) return;

  const plan = project.render_plan;
  elements.planVersion.textContent = `PLAN V${plan.version}`;
  elements.timelineDuration.textContent = formatDuration(plan.duration);
  if (!plan.scenes.some((scene) => scene.id === state.selectedSceneId)) state.selectedSceneId = plan.scenes[0].id;
  renderScenes();
  renderPreview();
  renderArtifacts();
  renderOperationSummary(project);
}

function renderAudio(audio, plan) {
  elements.audioInputState.classList.toggle('ready', Boolean(audio || plan));
  if (audio) {
    elements.audioName.textContent = audio.original_name;
    elements.audioDetail.textContent = `${formatDuration(audio.duration)} · ${audio.format.toUpperCase()}`;
  } else if (plan) {
    elements.audioName.textContent = 'Audio de fixture';
    elements.audioDetail.textContent = formatDuration(plan.duration);
  } else {
    elements.audioName.textContent = 'Sin audio';
    elements.audioDetail.textContent = 'Agregar narración';
  }
}

async function importSelectedAudio() {
  const [file] = elements.audioInput.files;
  if (!file || !state.project) return;
  elements.audioInput.disabled = true;
  elements.primaryActionButton.disabled = true;
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
    elements.primaryActionButton.disabled = false;
  }
}

function renderInputs(project) {
  const plan = project.render_plan;
  const scriptReady = Boolean(project.script);
  elements.scriptInputState.classList.toggle('ready', scriptReady);
  elements.scriptInputDetail.textContent = scriptReady ? `${project.script.blocks.length} bloques` : 'Fixture pendiente';
  renderAudio(project.audio, plan);
  elements.visualInputState.classList.toggle('ready', Boolean(plan));
  elements.visualInputDetail.textContent = plan ? `${plan.scenes.length} resueltas` : 'Pendientes';
}

function currentStageLabel(project) {
  if (!project.render_plan) return project.audio ? 'Listo para planificar' : 'Faltan insumos';
  if (currentArtifact('export')) return 'Resultado listo';
  if (currentArtifact('preview')) return 'Revisión visual';
  return `Plan v${project.plan_version}`;
}

function renderPrimaryAction(project) {
  const preview = project.render_plan ? currentArtifact('preview') : null;
  const exported = project.render_plan ? currentArtifact('export') : null;
  let action = 'package';
  let label = 'Importar package / demo';
  if (project.render_plan && exported) {
    action = 'result';
    label = 'Abrir resultado';
  } else if (project.render_plan && preview) {
    action = 'export';
    label = 'Exportar video + SRT';
  } else if (project.render_plan) {
    action = 'preview';
    label = 'Generar preview';
  } else if (project.audio) {
    action = 'prepare';
    label = 'Crear plan (fixture demo)';
  }
  elements.primaryActionButton.dataset.action = action;
  elements.primaryActionButton.textContent = label;
}

function runPrimaryAction() {
  const action = elements.primaryActionButton.dataset.action;
  if (action === 'audio') return elements.audioInput.click();
  if (action === 'package') {
    if (elements.packageSelect?.value) return importSelectedPackage();
    return startJob(`/api/projects/${state.project.id}/prepare-demo`, 'Preparando insumos demo');
  }
  if (action === 'prepare') return startJob(`/api/projects/${state.project.id}/prepare-demo`, 'Preparando insumos');
  if (action === 'preview') return startJob(`/api/projects/${state.project.id}/preview`, 'Generando preview');
  if (action === 'export') return startJob(`/api/projects/${state.project.id}/export`, 'Exportando video');
  if (action === 'result') {
    const exported = currentArtifact('export');
    if (exported) openArtifactExternally(exported.id);
  }
}

function renderOperationSummary(project) {
  const plan = project.render_plan;
  const exported = currentArtifact('export');
  elements.operationDuration.textContent = formatDuration(plan.duration);
  elements.operationScenes.textContent = String(plan.scenes.length);
  elements.operationPending.textContent = exported ? '0' : String(plan.scenes.length);
  elements.reviewBadge.textContent = exported ? 'Revisado' : 'Revisar';
  elements.reviewBadge.classList.toggle('ready', Boolean(exported));
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
    button.innerHTML = '<img alt=""><div><span></span><strong></strong></div>';
    button.querySelector('img').src = sceneImageUrl(scene.image_path);
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

async function startJob(path, label, body = {}) {
  setBusy(true);
  showNotice();
  try {
    const job = await api(path, { method: 'POST', body: JSON.stringify(body || {}) });
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
  elements.primaryActionButton.disabled = value;
  elements.audioInput.disabled = value;
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
