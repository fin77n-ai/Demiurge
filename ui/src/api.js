export async function getProjects() {
  const r = await fetch('/api/projects')
  return r.json()
}

export async function loadProject(slug) {
  const r = await fetch(`/api/projects/load?slug=${encodeURIComponent(slug)}`)
  return r.json()
}

export async function saveProject(payload) {
  await fetch('/api/projects/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
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
