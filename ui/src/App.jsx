import { useState, useEffect, useCallback, useRef, createRef } from 'react'
import Topbar from './components/Topbar'
import ProjectPanel from './components/ProjectPanel'
import RequirementsTab from './components/RequirementsTab'
import WireframeTab from './components/WireframeTab'
import * as api from './api'

export default function App() {
  const [tab, setTab] = useState('req')
  const [cards, setCards] = useState([])
  const [currentSpec, setCurrentSpec] = useState('')
  const [specLoading, setSpecLoading] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [currentSlug, setCurrentSlug] = useState('default')
  const [projects, setProjects] = useState([])
  const [projPanelOpen, setProjPanelOpen] = useState(false)
  const [initialExcalidrawData, setInitialExcalidrawData] = useState(null)

  // Refs
  const wireframeRef = useRef(null)
  const excalidrawDataRef = useRef(null)
  const autoSaveTimer = useRef(null)
  const saveDataRef = useRef({ slug: 'default', projectName: '', cards: [] })

  useEffect(() => {
    saveDataRef.current = { slug: currentSlug, projectName, cards }
  }, [currentSlug, projectName, cards])

  const doSave = useCallback(async () => {
    const { slug, projectName, cards } = saveDataRef.current
    await api.saveProject({ slug, projectName, cards, excalidrawData: excalidrawDataRef.current })
  }, [])

  const scheduleAutoSave = useCallback(() => {
    clearTimeout(autoSaveTimer.current)
    autoSaveTimer.current = setTimeout(doSave, 1500)
  }, [doSave])

  const refreshProjects = useCallback(async () => {
    const list = await api.getProjects()
    setProjects(list)
    return list
  }, [])

  const loadProject = useCallback(async (slug) => {
    const data = await api.loadProject(slug)
    setCards(data.cards || [])
    setProjectName(data.projectName || slug)
    setInitialExcalidrawData(data.excalidrawData || null)
    excalidrawDataRef.current = data.excalidrawData || null
    setCurrentSpec('')
    setSpecLoading(false)
  }, [])

  // Initial load
  useEffect(() => {
    refreshProjects().then(list => {
      if (list.length > 0) {
        setCurrentSlug(list[0].slug)
        loadProject(list[0].slug)
      }
    })
  }, [])

  const switchProject = useCallback(async (slug) => {
    if (slug === currentSlug) { setProjPanelOpen(false); return }
    await doSave()
    setCurrentSlug(slug)
    await loadProject(slug)
    setProjPanelOpen(false)
    await refreshProjects()
  }, [currentSlug, doSave, loadProject, refreshProjects])

  const newProject = useCallback(async () => {
    const name = prompt('项目名称：', '新项目')
    if (!name?.trim()) return
    await doSave()
    const data = await api.createProject(name.trim())
    setCurrentSlug(data.slug)
    setProjectName(data.name)
    setCards([])
    setInitialExcalidrawData(null)
    excalidrawDataRef.current = null
    setCurrentSpec('')
    setProjPanelOpen(false)
    await refreshProjects()
  }, [doSave, refreshProjects])

  const deleteProject = useCallback(async (slug) => {
    const proj = projects.find(p => p.slug === slug)
    if (projects.length <= 1) { alert('至少保留一个项目'); return }
    if (!confirm(`删除项目「${proj?.name || slug}」？`)) return
    await api.deleteProject(slug)
    let nextSlug = currentSlug
    if (slug === currentSlug) {
      const remaining = projects.filter(p => p.slug !== slug)
      nextSlug = remaining[0].slug
      setCurrentSlug(nextSlug)
      await loadProject(nextSlug)
    }
    await refreshProjects()
  }, [projects, currentSlug, loadProject, refreshProjects])

  const generateSpec = useCallback(async () => {
    if (cards.length === 0) { alert('请先添加需求卡片'); return }
    setSpecLoading(true)
    setCurrentSpec('')
    try {
      const spec = await api.generateSpec(cards, projectName || 'Untitled')
      setCurrentSpec(spec)
    } catch (e) {
      setCurrentSpec(`生成失败：${e.message}`)
    } finally {
      setSpecLoading(false)
    }
  }, [cards, projectName])

  const handleExcalidrawChange = useCallback((elements, appState, files) => {
    excalidrawDataRef.current = { elements, appState, files }
    scheduleAutoSave()
  }, [scheduleAutoSave])

  const handleProjectNameChange = useCallback((name) => {
    setProjectName(name)
    scheduleAutoSave()
  }, [scheduleAutoSave])

  const handleCardsChange = useCallback((newCards) => {
    setCards(newCards)
    scheduleAutoSave()
  }, [scheduleAutoSave])

  return (
    <div className="app">
      <Topbar
        projectName={projectName}
        onProjectNameChange={handleProjectNameChange}
        onProjectsToggle={() => setProjPanelOpen(v => !v)}
        onSave={doSave}
        tab={tab}
        onGenerateSpec={generateSpec}
      />

      {projPanelOpen && (
        <ProjectPanel
          projects={projects}
          currentSlug={currentSlug}
          onSwitch={switchProject}
          onNew={newProject}
          onDelete={deleteProject}
          onClose={() => setProjPanelOpen(false)}
        />
      )}

      <div className="tabs">
        <div className={`tab${tab === 'req' ? ' active' : ''}`} onClick={() => setTab('req')}>需求画板</div>
        <div className={`tab${tab === 'wf' ? ' active' : ''}`} onClick={() => setTab('wf')}>线框图</div>
      </div>

      <div className="pages-container">
        <div className={`page${tab === 'req' ? ' active' : ''}`}>
          <RequirementsTab
            cards={cards}
            onCardsChange={handleCardsChange}
            currentSpec={currentSpec}
            specLoading={specLoading}
            projectName={projectName}
          />
        </div>
        <div className={`page${tab === 'wf' ? ' active' : ''}`}>
          <WireframeTab
            key={currentSlug}
            ref={wireframeRef}
            initialData={initialExcalidrawData}
            onChange={handleExcalidrawChange}
          />
        </div>
      </div>
    </div>
  )
}
