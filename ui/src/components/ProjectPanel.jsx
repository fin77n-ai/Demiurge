export default function ProjectPanel({ projects, currentSlug, onSwitch, onNew, onDelete, onClose }) {
  return (
    <>
      <div className="proj-overlay" onClick={onClose} />
      <div className="proj-panel">
        <div className="proj-panel-head">
          <span>项目列表</span>
          <button className="proj-new-btn" onClick={onNew}>＋ 新建</button>
        </div>
        <div className="proj-list">
          {projects.length === 0 ? (
            <div style={{ padding: 12, color: 'var(--text2)', fontSize: 12 }}>暂无项目</div>
          ) : projects.map(p => (
            <div
              key={p.slug}
              className={`proj-item${p.slug === currentSlug ? ' current' : ''}`}
              onClick={() => onSwitch(p.slug)}
            >
              <div className="proj-dot" />
              <div className="proj-item-name">{p.name}</div>
              <button
                className="proj-del"
                title="删除"
                onClick={e => { e.stopPropagation(); onDelete(p.slug) }}
              >✕</button>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
