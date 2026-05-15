import { useState } from 'react'

export default function Topbar({ projectName, onProjectNameChange, onProjectsToggle, onSave, tab, onGenerateSpec }) {
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    await onSave()
    setSaved(true)
    setTimeout(() => setSaved(false), 1200)
  }

  return (
    <div className="topbar">
      <h1>⚗ Demiurge</h1>
      <button className="btn" onClick={onProjectsToggle} style={{ fontSize: 11, flexShrink: 0 }}>
        Projects ▾
      </button>
      <input
        className="project-name"
        placeholder="项目名称..."
        value={projectName}
        onChange={e => onProjectNameChange(e.target.value)}
      />
      <div className="topbar-right">
        <button className="btn" onClick={handleSave}>
          {saved ? '✓ Saved' : 'Save'}
        </button>
        {tab === 'req' && (
          <button className="btn btn-primary" onClick={onGenerateSpec}>
            ✦ Generate Spec
          </button>
        )}
      </div>
    </div>
  )
}
