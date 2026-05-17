import { useState } from 'react'
import TemplateModal from './TemplateModal'
import ImportDocModal from './ImportDocModal'

const TYPE_LABELS = {
  feature: '功能点',
  ui: '界面/交互',
  data: '数据结构',
  flow: '用户路径',
  constraint: '约束条件',
}

export default function RequirementsTab({ cards, onCardsChange, currentSpec, specLoading, specHistory, projectName }) {
  const [addOpen, setAddOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')
  const [type, setType] = useState('feature')
  const [copyDone, setCopyDone] = useState(false)
  const [claudeDone, setClaudeDone] = useState(false)
  const [templateOpen, setTemplateOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const [historyIdx, setHistoryIdx] = useState(0)

  const submitCard = () => {
    if (!title.trim()) return
    onCardsChange([...cards, { title: title.trim(), desc: desc.trim(), type }])
    setTitle('')
    setDesc('')
  }

  const deleteCard = (i) => onCardsChange(cards.filter((_, idx) => idx !== i))

  const copySpec = async () => {
    if (!displaySpec) return
    await navigator.clipboard.writeText(displaySpec)
    setCopyDone(true)
    setTimeout(() => setCopyDone(false), 1500)
  }

  const displaySpec = specHistory && specHistory.length > 0
    ? specHistory[historyIdx]?.spec
    : currentSpec

  const sendToClaudeCode = async () => {
    if (!displaySpec) return
    const prompt = `请根据以下 Spec 实现此项目。先运行 /init 初始化项目结构，然后逐模块实现。\n\n---\n\n${displaySpec}`
    await navigator.clipboard.writeText(prompt)
    setClaudeDone(true)
    setTimeout(() => setClaudeDone(false), 1500)
  }

  const downloadSpec = () => {
    if (!displaySpec) return
    const name = (projectName || 'demiurge-spec').replace(/\s+/g, '-').toLowerCase()
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([displaySpec], { type: 'text/markdown' })),
      download: `${name}.md`,
    })
    a.click()
  }

  const counts = {}
  cards.forEach(c => { counts[c.type] = (counts[c.type] || 0) + 1 })

  return (
    <>
    <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      {/* Left: card board */}
      <div className="panel-board">
        <div className="panel-header">
          <span>需求画板</span>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
            <button className="btn" style={{ fontSize: 11 }} onClick={() => setImportOpen(true)} title="从文档导入">导入文档</button>
            <button className="btn" style={{ fontSize: 11 }} onClick={() => setTemplateOpen(true)} title="从模板创建">模板</button>
            <button className="btn" style={{ fontSize: 11 }} onClick={() => setAddOpen(v => !v)}>＋ 添加</button>
          </div>
        </div>

        <div className="card-list">
          {cards.length === 0 ? (
            <div style={{ color: 'var(--text2)', fontSize: 12, textAlign: 'center', padding: 20 }}>
              还没有卡片，点击右上角添加
            </div>
          ) : cards.map((card, i) => (
            <div key={i} className="card" data-type={card.type}>
              <div className="card-type-tag">{TYPE_LABELS[card.type] || card.type}</div>
              <div className="card-title">{card.title}</div>
              {card.desc && <div className="card-desc">{card.desc}</div>}
              <div className="card-actions">
                <button className="card-btn del" onClick={() => deleteCard(i)}>删除</button>
              </div>
            </div>
          ))}
        </div>

        <div className="add-card-area">
          {addOpen && (
            <div className="add-card-form">
              <input
                className="inp"
                placeholder="标题 *"
                value={title}
                onChange={e => setTitle(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && submitCard()}
                autoFocus
              />
              <textarea
                className="inp"
                placeholder="描述（可选）"
                value={desc}
                onChange={e => setDesc(e.target.value)}
              />
              <div className="form-row">
                <select className="inp" value={type} onChange={e => setType(e.target.value)}>
                  <option value="feature">功能点</option>
                  <option value="flow">用户路径</option>
                  <option value="ui">界面/交互</option>
                  <option value="data">数据结构</option>
                  <option value="constraint">约束条件</option>
                </select>
                <button className="btn btn-primary" onClick={submitCard} style={{ whiteSpace: 'nowrap' }}>添加</button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Middle: spec viewer */}
      <div className="panel-spec">
        <div className="panel-header">
          <span>AI Spec 预览</span>
          {specHistory && specHistory.length > 1 && (
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
              {specHistory.map((h, i) => (
                <button key={i}
                  style={{ fontSize: 10, padding: '2px 8px', borderRadius: 4, cursor: 'pointer', border: '1px solid var(--border)', background: i === historyIdx ? 'var(--primary)' : 'var(--surface2)', color: i === historyIdx ? '#fff' : 'var(--text2)' }}
                  onClick={() => setHistoryIdx(i)}
                  title={h.ts}
                >
                  {i === 0 ? '最新' : `v${specHistory.length - i}`}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="spec-body">
          {specLoading ? (
            <div className="spec-generating">✦ AI 正在结构化需求...</div>
          ) : displaySpec ? (
            <pre>{displaySpec}</pre>
          ) : (
            <div className="spec-placeholder">
              在左侧添加需求卡片<br />然后点击右上角 <strong>✦ Generate Spec</strong>
            </div>
          )}
        </div>
      </div>

      {/* Right: export */}
      <div className="panel-export">
        <div className="panel-header"><span>导出</span></div>
        <div className="export-body">
          <div>
            <div className="export-section">操作</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <button className="export-btn export-btn-claude" onClick={sendToClaudeCode} disabled={!displaySpec}>
                <strong>{claudeDone ? '✓ 已复制！' : '⚡ 发给 Claude Code'}</strong>
                <small>复制完整 prompt，粘贴即执行</small>
              </button>
              <button className="export-btn" onClick={copySpec}>
                <strong>{copyDone ? '✓ 已复制！' : '复制 Spec MD'}</strong>
                <small>直接粘给 Claude / Gemini</small>
              </button>
              <button className="export-btn" onClick={downloadSpec}>
                <strong>下载 .md 文件</strong>
                <small>保存到本地</small>
              </button>
            </div>
          </div>
          <div>
            <div className="export-section">卡片统计</div>
            {cards.length === 0 ? (
              <div style={{ color: 'var(--text2)', fontSize: 11 }}>暂无卡片</div>
            ) : (
              <>
                {Object.entries(TYPE_LABELS).filter(([k]) => counts[k]).map(([k, label]) => (
                  <div key={k} className="stat-row">
                    <span>{label}</span><span>{counts[k]}</span>
                  </div>
                ))}
                <div className="stat-row" style={{ marginTop: 4 }}>
                  <span>合计</span><span>{cards.length}</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>

    {templateOpen && (
      <TemplateModal
        onApply={tplCards => { onCardsChange([...cards, ...tplCards]); setAddOpen(false) }}
        onClose={() => setTemplateOpen(false)}
      />
    )}
    {importOpen && (
      <ImportDocModal
        onAppend={newCards => onCardsChange([...cards, ...newCards])}
        onClose={() => setImportOpen(false)}
      />
    )}
    </>
  )
}
