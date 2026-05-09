// Demiurge — frontend logic

const TYPE_LABELS = {
  feature: '功能点',
  ui: '界面/交互',
  data: '数据结构',
  flow: '用户路径',
  constraint: '约束条件',
};

// ── Requirements board ──
let cards = [];
let currentSpec = '';
let addFormOpen = false;

// ── Wireframe ──
let wfElements = [];
let wfNextId = 1;
let wfSelectedId = null;
let _wfDrag = null;
let _wfAction = null;

// ── Multi-project ──
let currentSlug = 'default';
let _projPanelOpen = false;

// ─────────────────────────────
// Tab switching
// ─────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', (name === 'req' && i === 0) || (name === 'wf' && i === 1));
  });
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');

  const btn = document.getElementById('main-action-btn');
  if (name === 'wf') {
    btn.textContent = '导出线框图';
    btn.onclick = exportWireframe;
  } else {
    btn.textContent = '✦ Generate Spec';
    btn.onclick = generateSpec;
  }
}

// ─────────────────────────────
// Project panel
// ─────────────────────────────
function toggleProjectPanel() {
  _projPanelOpen ? closeProjectPanel() : openProjectPanel();
}

function openProjectPanel() {
  _projPanelOpen = true;
  document.getElementById('proj-panel').classList.add('open');
  document.getElementById('proj-overlay').classList.add('open');
  loadProjects();
}

function closeProjectPanel() {
  _projPanelOpen = false;
  document.getElementById('proj-panel').classList.remove('open');
  document.getElementById('proj-overlay').classList.remove('open');
}

async function loadProjects() {
  const resp = await fetch('/api/projects');
  const list = await resp.json();
  renderProjectList(list);
}

function renderProjectList(list) {
  const el = document.getElementById('proj-list');
  if (list.length === 0) {
    el.innerHTML = '<div style="padding:12px;color:var(--text2);font-size:12px;">暂无项目</div>';
    return;
  }
  el.innerHTML = list.map(p => `
    <div class="proj-item${p.slug === currentSlug ? ' current' : ''}" onclick="switchProject('${p.slug}')">
      <div class="proj-dot"></div>
      <div class="proj-item-name">${esc(p.name)}</div>
      <button class="proj-del" title="删除" onclick="deleteProject('${p.slug}',event)">✕</button>
    </div>
  `).join('');
}

async function switchProject(slug) {
  if (slug === currentSlug) { closeProjectPanel(); return; }
  await _doSave(); // save current first
  currentSlug = slug;
  closeProjectPanel();
  await _loadProject(slug);
  await loadProjects(); // refresh list highlight (panel closed, but keep data fresh)
}

async function newProject() {
  const name = prompt('项目名称：', '新项目');
  if (!name || !name.trim()) return;
  await _doSave(); // save current first
  const resp = await fetch('/api/projects/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name.trim() }),
  });
  const data = await resp.json();
  currentSlug = data.slug;
  cards = [];
  wfElements = [];
  wfNextId = 1;
  document.getElementById('project-name').value = data.name;
  renderCards();
  wfRender();
  closeProjectPanel();
}

async function deleteProject(slug, evt) {
  evt.stopPropagation();
  const list = await (await fetch('/api/projects')).json();
  if (list.length <= 1) { alert('至少保留一个项目'); return; }
  if (!confirm(`删除项目「${list.find(p => p.slug === slug)?.name || slug}」？`)) return;
  await fetch('/api/projects/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug }),
  });
  if (slug === currentSlug) {
    const remaining = list.filter(p => p.slug !== slug);
    await switchProject(remaining[0].slug);
  } else {
    loadProjects();
  }
}

// ─────────────────────────────
// Requirements board
// ─────────────────────────────
function renderCards() {
  const list = document.getElementById('card-list');
  list.innerHTML = '';
  if (cards.length === 0) {
    list.innerHTML = '<div style="color:var(--text2);font-size:12px;text-align:center;padding:20px;">还没有卡片，点击右上角添加</div>';
    updateStats();
    return;
  }
  cards.forEach((card, i) => {
    const div = document.createElement('div');
    div.className = 'card';
    div.dataset.type = card.type;
    div.innerHTML = `
      <div class="card-type-tag tag-${card.type}">${TYPE_LABELS[card.type] || card.type}</div>
      <div class="card-title">${esc(card.title)}</div>
      ${card.desc ? `<div class="card-desc">${esc(card.desc)}</div>` : ''}
      <div class="card-actions">
        <button class="card-btn del" onclick="deleteCard(${i})">删除</button>
      </div>
    `;
    list.appendChild(div);
  });
  updateStats();
}

function updateStats() {
  const counts = {};
  cards.forEach(c => { counts[c.type] = (counts[c.type] || 0) + 1; });
  const el = document.getElementById('stats');
  if (cards.length === 0) {
    el.innerHTML = '<div style="color:var(--text2);font-size:11px;">暂无卡片</div>';
    return;
  }
  el.innerHTML = Object.entries(TYPE_LABELS).filter(([k]) => counts[k]).map(([k, label]) =>
    `<div class="stat-row"><span>${label}</span><span>${counts[k]}</span></div>`
  ).join('') + `<div class="stat-row" style="margin-top:4px;"><span>合计</span><span>${cards.length}</span></div>`;
}

function toggleAddForm() {
  addFormOpen = !addFormOpen;
  document.getElementById('add-form').classList.toggle('open', addFormOpen);
  if (addFormOpen) document.getElementById('f-title').focus();
}

function submitCard() {
  const title = document.getElementById('f-title').value.trim();
  if (!title) { document.getElementById('f-title').focus(); return; }
  const desc = document.getElementById('f-desc').value.trim();
  const type = document.getElementById('f-type').value;
  cards.push({ title, desc, type });
  document.getElementById('f-title').value = '';
  document.getElementById('f-desc').value = '';
  document.getElementById('f-title').focus();
  renderCards();
  scheduleAutoSave();
}

function deleteCard(i) {
  cards.splice(i, 1);
  renderCards();
  scheduleAutoSave();
}

// ─────────────────────────────
// Spec generation
// ─────────────────────────────
async function generateSpec() {
  if (cards.length === 0) { alert('请先添加需求卡片'); return; }
  const specBody = document.getElementById('spec-body');
  specBody.innerHTML = '<div class="spec-generating">✦ AI 正在结构化需求...</div>';
  const projectName = document.getElementById('project-name').value.trim() || 'Untitled';
  try {
    const resp = await fetch('/api/generate_spec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cards, projectName }),
    });
    const data = await resp.json();
    currentSpec = data.spec || '';
    renderSpec(currentSpec);
  } catch (e) {
    specBody.innerHTML = `<div class="spec-placeholder" style="color:var(--danger);">生成失败：${e.message}</div>`;
  }
}

function renderSpec(md) {
  document.getElementById('spec-body').innerHTML = `<pre>${esc(md)}</pre>`;
}

function copySpec() {
  if (!currentSpec) { alert('请先生成 Spec'); return; }
  navigator.clipboard.writeText(currentSpec).then(() => {
    const btn = event.currentTarget;
    const orig = btn.querySelector('strong').textContent;
    btn.querySelector('strong').textContent = '✓ 已复制！';
    setTimeout(() => { btn.querySelector('strong').textContent = orig; }, 1500);
  });
}

function downloadSpec() {
  if (!currentSpec) { alert('请先生成 Spec'); return; }
  const name = (document.getElementById('project-name').value.trim() || 'demiurge-spec').replace(/\s+/g, '-').toLowerCase();
  const blob = new Blob([currentSpec], { type: 'text/markdown' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${name}.md`;
  a.click();
}

// ─────────────────────────────
// Wireframe — render
// ─────────────────────────────
function wfRender() {
  const canvas = document.getElementById('wf-canvas');
  canvas.innerHTML = '';

  wfElements.forEach(el => {
    const div = document.createElement('div');
    div.className = 'wf-el' + (el.id === wfSelectedId ? ' selected' : '');
    div.id = 'wf-el-' + el.id;
    div.dataset.type = el.type;
    div.style.cssText = `left:${el.x}px;top:${el.y}px;width:${el.w}px;height:${el.h}px;`;
    div.innerHTML = `<div class="wf-el-label">${esc(el.label)}</div>`;

    if (el.id === wfSelectedId) {
      ['se', 'e', 's'].forEach(dir => {
        const h = document.createElement('div');
        h.className = `wf-handle ${dir}`;
        h.dataset.dir = dir;
        h.dataset.id = el.id;
        div.appendChild(h);
      });
    }

    div.addEventListener('mousedown', e => {
      if (e.target.classList.contains('wf-handle')) return;
      e.stopPropagation();
      wfSelectedId = el.id;
      wfRender();
      _wfAction = { kind: 'move', id: el.id, sx: e.clientX, sy: e.clientY, ox: el.x, oy: el.y };
    });

    div.addEventListener('dblclick', e => {
      e.stopPropagation();
      const newLabel = prompt('编辑标签:', el.label);
      if (newLabel !== null) { el.label = newLabel; wfRender(); scheduleAutoSave(); }
    });

    canvas.appendChild(div);
  });

  canvas.querySelectorAll('.wf-handle').forEach(handle => {
    handle.addEventListener('mousedown', e => {
      e.stopPropagation();
      const id  = parseInt(handle.dataset.id);
      const dir = handle.dataset.dir;
      const el  = wfElements.find(x => x.id === id);
      if (!el) return;
      _wfAction = { kind: 'resize', id, dir, sx: e.clientX, sy: e.clientY, ow: el.w, oh: el.h };
    });
  });
}

// ─────────────────────────────
// Wireframe — palette & canvas
// ─────────────────────────────
function wfInitPalette() {
  document.querySelectorAll('.wf-item').forEach(item => {
    item.addEventListener('dragstart', e => {
      _wfDrag = {
        type:  item.dataset.type,
        w:     parseInt(item.dataset.w),
        h:     parseInt(item.dataset.h),
        label: item.dataset.label || item.dataset.type,
      };
      e.dataTransfer.effectAllowed = 'copy';
    });
    item.addEventListener('dragend', () => { _wfDrag = null; });
  });

  const canvas = document.getElementById('wf-canvas');
  canvas.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; });

  canvas.addEventListener('drop', e => {
    e.preventDefault();
    if (!_wfDrag) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.max(0, Math.round((e.clientX - rect.left) / 20) * 20);
    const y = Math.max(0, Math.round((e.clientY - rect.top)  / 20) * 20);
    const newEl = { id: wfNextId++, ..._wfDrag, x, y };
    wfElements.push(newEl);
    wfSelectedId = newEl.id;
    wfRender();
    scheduleAutoSave();
    _wfDrag = null;
  });

  canvas.addEventListener('mousedown', e => {
    if (e.target === canvas) { wfSelectedId = null; wfRender(); }
  });
}

// ─────────────────────────────
// Wireframe — global mouse events
// ─────────────────────────────
document.addEventListener('mousemove', e => {
  if (!_wfAction) return;
  const el   = wfElements.find(x => x.id === _wfAction.id);
  if (!el) return;
  const dx   = e.clientX - _wfAction.sx;
  const dy   = e.clientY - _wfAction.sy;
  const node = document.getElementById('wf-el-' + el.id);

  if (_wfAction.kind === 'move') {
    el.x = Math.max(0, Math.round((_wfAction.ox + dx) / 20) * 20);
    el.y = Math.max(0, Math.round((_wfAction.oy + dy) / 20) * 20);
    if (node) { node.style.left = el.x + 'px'; node.style.top = el.y + 'px'; }
  } else {
    const { dir, ow, oh } = _wfAction;
    if (dir === 'se' || dir === 'e') el.w = Math.max(40, Math.round((ow + dx) / 20) * 20);
    if (dir === 'se' || dir === 's') el.h = Math.max(24, Math.round((oh + dy) / 20) * 20);
    if (node) { node.style.width = el.w + 'px'; node.style.height = el.h + 'px'; }
  }
});

document.addEventListener('mouseup', () => {
  if (_wfAction) { _wfAction = null; scheduleAutoSave(); }
});

document.addEventListener('keydown', e => {
  if ((e.key === 'Delete' || e.key === 'Backspace') && wfSelectedId !== null) {
    const active = document.activeElement;
    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) return;
    wfDeleteSelected();
  }
});

// ─────────────────────────────
// Wireframe — toolbar
// ─────────────────────────────
function wfClearSelected() { wfSelectedId = null; wfRender(); }

function wfDeleteSelected() {
  if (wfSelectedId === null) return;
  wfElements = wfElements.filter(x => x.id !== wfSelectedId);
  wfSelectedId = null;
  wfRender();
  scheduleAutoSave();
}

function wfClear() {
  if (wfElements.length > 0 && !confirm('清空画板？')) return;
  wfElements = []; wfSelectedId = null;
  wfRender(); scheduleAutoSave();
}

function exportWireframe() {
  const name  = (document.getElementById('project-name').value.trim() || 'wireframe').replace(/\s+/g, '-').toLowerCase();
  const maxX  = wfElements.reduce((m, e) => Math.max(m, e.x + e.w), 400) + 40;
  const maxY  = wfElements.reduce((m, e) => Math.max(m, e.y + e.h), 300) + 40;
  const elHtml = wfElements.map(el =>
    `  <div style="position:absolute;left:${el.x}px;top:${el.y}px;width:${el.w}px;height:${el.h}px;` +
    `border:1.5px solid #999;border-radius:4px;background:#f5f5f5;display:flex;align-items:center;` +
    `justify-content:center;font:12px sans-serif;color:#555;text-align:center;padding:4px;" data-type="${el.type}">${esc(el.label)}</div>`
  ).join('\n');
  const html = `<!DOCTYPE html>\n<html><head><meta charset="UTF-8"><title>${esc(name)} Wireframe</title></head>\n` +
    `<body style="margin:20px;background:#fff;">\n<h2 style="font-family:sans-serif;color:#333;margin-bottom:16px;">${esc(name)} — Wireframe</h2>\n` +
    `<div style="position:relative;width:${maxX}px;height:${maxY}px;border:1px solid #ddd;">\n${elHtml}\n</div>\n</body></html>`;
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([html], { type: 'text/html' })),
    download: `${name}-wireframe.html`,
  });
  a.click();
}

function copyWireframeAsText() {
  if (wfElements.length === 0) { alert('画板是空的'); return; }
  const name   = document.getElementById('project-name').value.trim() || 'Untitled';
  const sorted = [...wfElements].sort((a, b) => a.y - b.y || a.x - b.x);
  const lines  = [
    `# ${name} — 线框图布局描述`, '',
    '以下是界面组件的位置和尺寸（坐标原点左上角）：', '',
    ...sorted.map(el => `- [${el.type}] "${el.label}" → 位置 (${el.x}, ${el.y})，尺寸 ${el.w}×${el.h}px`),
    '', '_由 Demiurge 线框图生成_',
  ];
  navigator.clipboard.writeText(lines.join('\n')).then(() => alert('已复制到剪贴板！'));
}

// ─────────────────────────────
// Save / Load
// ─────────────────────────────
let _autoSaveTimer = null;
function scheduleAutoSave() {
  clearTimeout(_autoSaveTimer);
  _autoSaveTimer = setTimeout(_doSave, 1500);
}

async function _doSave() {
  const projectName = document.getElementById('project-name').value.trim();
  await fetch('/api/projects/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug: currentSlug, projectName, cards, wfElements, wfNextId }),
  });
}

async function saveAll() {
  await _doSave();
  const btn = event?.currentTarget;
  if (btn) {
    const orig = btn.textContent;
    btn.textContent = '✓ Saved';
    setTimeout(() => { btn.textContent = orig; }, 1200);
  }
}

function saveBoard() { saveAll(); }

async function _loadProject(slug) {
  const resp = await fetch(`/api/projects/load?slug=${encodeURIComponent(slug)}`);
  const data = await resp.json();
  cards      = data.cards      || [];
  wfElements = data.wfElements || [];
  wfNextId   = data.wfNextId   || (wfElements.reduce((m, e) => Math.max(m, e.id), 0) + 1);
  document.getElementById('project-name').value = data.projectName || slug;
  currentSpec = '';
  document.getElementById('spec-body').innerHTML =
    '<div class="spec-placeholder">在左侧添加需求卡片<br>然后点击右上角 <strong>✦ Generate Spec</strong></div>';
  renderCards();
  wfRender();
}

async function loadBoard() {
  // Pick the most-recent project on first load
  try {
    const list = await (await fetch('/api/projects')).json();
    if (list.length > 0) {
      currentSlug = list[0].slug;
      await _loadProject(currentSlug);
    }
  } catch (e) {
    console.error('Load failed', e);
  }
}

document.getElementById('project-name').addEventListener('input', scheduleAutoSave);

// ─────────────────────────────
// Utility
// ─────────────────────────────
function esc(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ─────────────────────────────
// Init
// ─────────────────────────────
wfInitPalette();
loadBoard();
