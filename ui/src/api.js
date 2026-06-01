export async function getProjects() {
  const r = await fetch('/api/projects')
  return r.json()
}

export async function loadProject(slug) {
  const r = await fetch(`/api/projects/load?slug=${encodeURIComponent(slug)}`)
  return r.json()
}

function safeStringify(obj) {
  const cache = new Set();
  return JSON.stringify(obj, (key, value) => {
    if (value instanceof HTMLElement || (value && typeof value === 'object' && 'nodeType' in value)) {
      return undefined;
    }
    if (key.startsWith('__')) {
      return undefined;
    }
    if (typeof value === 'object' && value !== null) {
      if (cache.has(value)) {
        return undefined;
      }
      cache.add(value);
    }
    return value;
  });
}

export async function saveProject(payload) {
  await fetch('/api/projects/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: safeStringify(payload),
  })
}

export async function createProject(name) {
  const r = await fetch('/api/projects/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  return r.json()
}

export async function deleteProject(slug) {
  await fetch('/api/projects/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug }),
  })
}

export async function generateSpec(cards, projectName) {
  const r = await fetch('/api/generate_spec', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cards, projectName }),
  })
  const data = await r.json()
  return data.spec || ''
}
