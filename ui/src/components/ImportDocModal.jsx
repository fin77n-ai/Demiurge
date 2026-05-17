import { useState } from 'react'

export default function ImportDocModal({ onAppend, onClose }) {
  const [text, setText]       = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const doImport = async () => {
    if (!text.trim()) { setError('请粘贴文档内容'); return }
    setLoading(true)
    setError('')
    try {
      const resp = await fetch('/api/import_cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() }),
      })
      const data = await resp.json()
      if (data.error) { setError(data.error); return }
      onAppend(data.cards || [])
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={S.overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={S.modal}>
        <div style={S.header}>
          <span style={S.title}>从文档导入卡片</span>
          <button style={S.closeBtn} onClick={onClose}>✕</button>
        </div>
        <div style={S.hint}>粘贴 PRD、README、需求文档或任意文本，AI 自动拆解成需求卡片</div>
        <textarea
          style={S.textarea}
          placeholder="粘贴文档内容..."
          value={text}
          onChange={e => { setText(e.target.value); setError('') }}
          disabled={loading}
        />
        {error && <div style={S.error}>{error}</div>}
        <div style={S.footer}>
          <button style={{ ...S.btn }} onClick={onClose} disabled={loading}>取消</button>
          <button style={{ ...S.btn, ...S.btnPrimary, opacity: loading ? 0.6 : 1 }}
            onClick={doImport} disabled={loading}>
            {loading ? 'AI 解析中...' : '解析并导入'}
          </button>
        </div>
      </div>
    </div>
  )
}

const S = {
  overlay:  { position: 'fixed', inset: 0, background: '#00000088', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  modal:    { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, width: 500, padding: 24, boxShadow: '0 20px 60px #00000090', display: 'flex', flexDirection: 'column', gap: 14 },
  header:   { display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  title:    { fontSize: 14, fontWeight: 700, color: 'var(--text)' },
  closeBtn: { background: 'none', border: 'none', color: 'var(--text2)', cursor: 'pointer', fontSize: 14, padding: '2px 6px' },
  hint:     { fontSize: 11, color: 'var(--text2)', lineHeight: 1.6 },
  textarea: { background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 6, padding: '10px 12px', fontSize: 12, resize: 'vertical', minHeight: 180, outline: 'none', fontFamily: 'inherit', lineHeight: 1.6 },
  error:    { background: '#f76a6a18', border: '1px solid #f76a6a44', borderRadius: 6, padding: '8px 12px', fontSize: 12, color: '#f76a6a' },
  footer:   { display: 'flex', justifyContent: 'flex-end', gap: 8 },
  btn:      { background: 'var(--surface2)', border: '1px solid var(--border)', color: 'var(--text)', padding: '7px 18px', borderRadius: 6, cursor: 'pointer', fontSize: 12, transition: 'all .15s' },
  btnPrimary: { background: 'var(--primary)', borderColor: 'var(--primary)', color: '#fff' },
}
