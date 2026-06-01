import { useState, useEffect, useRef } from 'react'

const PHASES = [
  '正在读取项目文件树...',
  'Doctor 体检中，识别架构...',
  '智能选取前端 + 后端关键文件...',
  'AI 正在生成线框图...',
]

export default function SourceAnalyzerModal({ onAppend, onClose }) {
  const [sourceType, setSourceType] = useState('github')
  const [path, setPath]             = useState('')
  const [loading, setLoading]       = useState(false)
  const [phaseIdx, setPhaseIdx]     = useState(0)
  const [error, setError]           = useState('')
  const [result, setResult]         = useState(null)
  const [cacheInfo, setCacheInfo]   = useState(null)  // {cached_at, projectType, pages}
  const [isDragOver, setIsDragOver] = useState(false)
  const phaseTimer  = useRef(null)
  const cacheTimer  = useRef(null)

  // Cycle through phase messages while loading
  useEffect(() => {
    if (loading) {
      setPhaseIdx(0)
      phaseTimer.current = setInterval(() => {
        setPhaseIdx(i => Math.min(i + 1, PHASES.length - 1))
      }, 5000)
    } else {
      clearInterval(phaseTimer.current)
    }
    return () => clearInterval(phaseTimer.current)
  }, [loading])

  // Check for local cache whenever path or sourceType changes (debounced)
  useEffect(() => {
    setCacheInfo(null)
    clearTimeout(cacheTimer.current)
    const p = path.trim()
    if (!p) return
    cacheTimer.current = setTimeout(async () => {
      try {
        const resp = await fetch(`/api/wf_cache?type=${sourceType}&path=${encodeURIComponent(p)}`)
        const data = await resp.json()
        if (data.exists) setCacheInfo(data)
      } catch (_) {}
    }, 600)
    return () => clearTimeout(cacheTimer.current)
  }, [path, sourceType])

  const analyze = async (typeArg, pathArg) => {
    const t = typeArg ?? sourceType
    const p = (pathArg ?? path).trim()
    if (!p) { setError('请输入路径'); return }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const resp = await fetch('/api/analyze_source', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: t, path: p }),
      })
      const data = await resp.json()
      if (data.error) { setError(data.error); return }
      setResult(data)
      setCacheInfo(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    let filePath = ''

    // 1. Try text/uri-list (Safari / Firefox)
    const uriList = e.dataTransfer.getData('text/uri-list')
    const plain   = e.dataTransfer.getData('text/plain')
    const raw = (uriList || plain || '').split('\n').find(l => l.trim().startsWith('file://'))
    if (raw) {
      filePath = decodeURIComponent(raw.trim().replace(/^file:\/\//, ''))
    }

    // 2. Try non-standard file.path (Electron / some Chromium builds)
    if (!filePath && e.dataTransfer.files.length > 0) {
      const f = e.dataTransfer.files[0]
      if (f.path) filePath = f.path
    }

    // 3. Fall back: ask backend to locate by name in common dirs
    if (!filePath && e.dataTransfer.files.length > 0) {
      const name = e.dataTransfer.files[0].name
      setSourceType('local')
      setPath(`正在搜索 "${name}"...`)
      setResult(null)
      setError('')
      setCacheInfo(null)
      try {
        const resp = await fetch(`/api/resolve_path?name=${encodeURIComponent(name)}`)
        const data = await resp.json()
        if (data.path) {
          filePath = data.path
        } else {
          setPath(name)
          setError(`找不到"${name}"，请手动补全完整路径`)
          return
        }
      } catch {
        setPath(name)
        setError('路径解析失败，请手动补全完整路径')
        return
      }
    }

    if (!filePath) { setError('无法读取文件路径，请手动粘贴路径'); return }

    setSourceType('local')
    setPath(filePath)
    setResult(null)
    setError('')
    setCacheInfo(null)
    analyze('local', filePath)
  }

  const loadCache = () => {
    if (!cacheInfo) return
    setResult(cacheInfo)
    setCacheInfo(null)
  }

  const append = () => {
    if (!result) return
    onAppend(result.elements)
    onClose()
  }

  return (
    <div style={S.overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ ...S.modal, ...(isDragOver ? S.modalDragOver : {}) }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >

        {/* Header */}
        <div style={S.header}>
          <span style={S.title}>✦ 从代码生成线框图</span>
          <button style={S.closeBtn} onClick={onClose}>✕</button>
        </div>

        {/* Source toggle */}
        <div style={S.toggleRow}>
          {['github', 'local'].map(t => (
            <button key={t}
              style={{ ...S.toggleBtn, ...(sourceType === t ? S.toggleActive : {}) }}
              onClick={() => { setSourceType(t); setPath(''); setResult(null); setError(''); setCacheInfo(null) }}
            >
              {t === 'github' ? '🐙 GitHub 仓库' : '📁 本地文件夹'}
            </button>
          ))}
        </div>

        {/* Path input */}
        <div style={S.inputRow}>
          <input style={S.input}
            placeholder={sourceType === 'github'
              ? 'https://github.com/owner/repo'
              : '/Users/你/Desktop/my-project'}
            value={path}
            onChange={e => { setPath(e.target.value); setResult(null); setError('') }}
            onKeyDown={e => e.key === 'Enter' && !loading && analyze()}
            disabled={loading}
          />
          {sourceType === 'local' && (
            <button style={{ ...S.btn, opacity: loading ? 0.6 : 1 }}
              disabled={loading}
              onClick={async () => {
                try {
                  const resp = await fetch('/api/pick_folder')
                  const data = await resp.json()
                  if (data.path) {
                    setPath(data.path)
                    setResult(null)
                    setError('')
                    setCacheInfo(null)
                    analyze('local', data.path)
                  }
                } catch (e) { setError(e.message) }
              }}>
              📁
            </button>
          )}
          <button style={{ ...S.btn, ...S.btnPrimary, opacity: loading ? 0.6 : 1 }}
            onClick={() => analyze()} disabled={loading}>
            {loading ? '分析中' : '重新分析'}
          </button>
        </div>

        {/* Cache banner */}
        {cacheInfo && !result && !loading && (
          <div style={S.cacheBanner}>
            <div style={S.cacheLeft}>
              <span style={S.cacheIcon}>💾</span>
              <div>
                <div style={S.cacheTitle}>发现本地缓存 · {cacheInfo.cached_at}</div>
                <div style={S.cacheMeta}>
                  {cacheInfo.projectType} · {cacheInfo.pages?.length ?? 0} 个页面 · {cacheInfo.fileCount} 个文件
                </div>
              </div>
            </div>
            <button style={{ ...S.btn, ...S.btnCache }} onClick={loadCache}>
              免费加载 →
            </button>
          </div>
        )}

        {/* Loading phases */}
        {loading && (
          <div style={S.phaseBox}>
            {PHASES.map((msg, i) => (
              <div key={i} style={{
                ...S.phaseRow,
                color: i < phaseIdx ? 'var(--green)' : i === phaseIdx ? 'var(--primary)' : 'var(--text2)',
                opacity: i > phaseIdx + 1 ? 0.3 : 1,
              }}>
                <span style={{ marginRight: 8, fontSize: 11 }}>
                  {i < phaseIdx ? '✓' : i === phaseIdx ? '▶' : '○'}
                </span>
                {msg}
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {error && <div style={S.error}>{error}</div>}

        {/* Result */}
        {result && (
          <div style={S.result}>
            <div style={S.projectTag}>
              <span style={S.tagLabel}>项目类型</span>
              <span style={S.tagValue}>{result.projectType}</span>
              {result.cached_at && <span style={S.cacheTag}>💾 缓存 {result.cached_at}</span>}
            </div>
            {result.notes && <div style={S.notes}>{result.notes}</div>}
            <div style={S.resultMeta}>
              检测到 <strong style={{ color: 'var(--text)' }}>{result.pages.length}</strong> 个页面 ·
              读取了 <strong style={{ color: 'var(--text)' }}>{result.fileCount}</strong> 个文件
            </div>
            {result.tokens && result.tokens.total > 0 && (
              <div style={S.tokenRow}>
                <span style={S.tokenItem}>🔢 共 {result.tokens.total.toLocaleString()} tokens</span>
                <span style={S.tokenSep}>·</span>
                <span style={S.tokenItem}>↑ {result.tokens.input.toLocaleString()} 输入</span>
                <span style={S.tokenSep}>·</span>
                <span style={S.tokenItem}>↓ {result.tokens.output.toLocaleString()} 输出</span>
                <span style={S.tokenSep}>·</span>
                <span style={S.tokenItem}>{result.tokens.calls} 次调用</span>
              </div>
            )}
            <div style={S.pageList}>
              {result.pages.map((p, i) => (
                <div key={i} style={S.pageItem}>
                  <span style={S.pageDot}>●</span>
                  <span style={S.pageName}>{p.name}</span>
                  {p.route && <span style={S.pageRoute}>{p.route}</span>}
                </div>
              ))}
            </div>
            <button style={{ ...S.btn, ...S.btnPrimary, width: '100%', marginTop: 14 }}
              onClick={append}>
              追加到画板 →
            </button>
          </div>
        )}

        {isDragOver && (
          <div style={S.dropOverlay}>
            📁 松手即可分析
          </div>
        )}

        {!result && !loading && !cacheInfo && (
          <div style={S.hint}>
            支持 React / Vue / Flask / FastAPI / Express 等项目<br />
            每次分析结果自动保存本地，下次免费加载<br />
            <span style={{ color: 'var(--primary)', opacity: 0.8 }}>点 📁 用 Finder 选择，或把文件夹拖进来（Safari 支持）</span>
          </div>
        )}
      </div>
    </div>
  )
}

const S = {
  overlay:     { position: 'fixed', inset: 0, background: '#00000088', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  modal:       { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, width: 500, padding: 24, boxShadow: '0 20px 60px #00000090', display: 'flex', flexDirection: 'column', gap: 14 },
  header:      { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  title:       { fontSize: 14, fontWeight: 700, color: 'var(--text)' },
  closeBtn:    { background: 'none', border: 'none', color: 'var(--text2)', cursor: 'pointer', fontSize: 14, padding: '2px 6px' },
  toggleRow:   { display: 'flex', gap: 8 },
  toggleBtn:   { flex: 1, background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text2)', borderRadius: 6, padding: '7px 0', cursor: 'pointer', fontSize: 12, transition: 'all .15s' },
  toggleActive:{ background: '#7c6af720', borderColor: 'var(--primary)', color: 'var(--primary)' },
  inputRow:    { display: 'flex', gap: 8 },
  input:       { flex: 1, background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', padding: '7px 10px', borderRadius: 6, fontSize: 12, outline: 'none' },
  btn:         { background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)', padding: '7px 16px', borderRadius: 6, cursor: 'pointer', fontSize: 12, whiteSpace: 'nowrap', transition: 'all .15s' },
  btnPrimary:  { background: 'var(--primary)', borderColor: 'var(--primary)', color: '#fff' },
  btnCache:    { background: '#14532d', borderColor: '#22c55e', color: '#86efac' },
  cacheBanner: { background: '#14532d22', border: '1px solid #22c55e44', borderRadius: 8, padding: '10px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  cacheLeft:   { display: 'flex', alignItems: 'center', gap: 10 },
  cacheIcon:   { fontSize: 18 },
  cacheTitle:  { fontSize: 12, color: '#86efac', fontWeight: 600 },
  cacheMeta:   { fontSize: 11, color: '#4ade80', marginTop: 2 },
  cacheTag:    { fontSize: 10, color: '#4ade80', background: '#14532d44', borderRadius: 4, padding: '2px 6px', marginLeft: 4 },
  phaseBox:    { background: 'var(--surface2)', borderRadius: 8, border: '1px solid var(--border)', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 8 },
  phaseRow:    { fontSize: 12, display: 'flex', alignItems: 'center', transition: 'color .3s' },
  error:       { background: '#f76a6a18', border: '1px solid #f76a6a44', borderRadius: 6, padding: '8px 12px', fontSize: 12, color: '#f76a6a' },
  result:      { background: 'var(--surface2)', borderRadius: 8, border: '1px solid var(--border)', padding: 14, display: 'flex', flexDirection: 'column', gap: 8 },
  projectTag:  { display: 'flex', alignItems: 'center', gap: 8 },
  tagLabel:    { fontSize: 10, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '.6px' },
  tagValue:    { fontSize: 12, color: 'var(--primary)', fontWeight: 600 },
  notes:       { fontSize: 11, color: 'var(--text2)', lineHeight: 1.5 },
  resultMeta:  { fontSize: 12, color: 'var(--text2)' },
  pageList:    { display: 'flex', flexDirection: 'column', gap: 5 },
  pageItem:    { display: 'flex', alignItems: 'center', gap: 8 },
  pageDot:     { color: 'var(--primary)', fontSize: 8 },
  pageName:    { fontSize: 13, color: 'var(--text)', fontWeight: 600 },
  pageRoute:   { fontSize: 11, color: 'var(--text2)', fontFamily: 'monospace' },
  hint:        { fontSize: 11, color: 'var(--text2)', textAlign: 'center', padding: '8px 0 4px', lineHeight: 1.8 },
  tokenRow:    { display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' },
  tokenItem:   { fontSize: 11, color: 'var(--accent)', fontFamily: 'monospace' },
  tokenSep:    { fontSize: 11, color: 'var(--border)' },
  modalDragOver: { borderColor: 'var(--primary)', boxShadow: '0 0 0 2px var(--primary)40' },
  dropOverlay: { background: 'var(--primary)18', border: '1.5px dashed var(--primary)', borderRadius: 8, padding: '16px 0', textAlign: 'center', fontSize: 14, color: 'var(--primary)', fontWeight: 700, letterSpacing: 0.5 },
}
