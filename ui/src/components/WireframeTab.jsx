import { useState, forwardRef, useImperativeHandle } from 'react'
import { Excalidraw } from '@excalidraw/excalidraw'
import '@excalidraw/excalidraw/index.css'
import SourceAnalyzerModal from './SourceAnalyzerModal'

const WireframeTab = forwardRef(function WireframeTab({ initialData, onChange }, ref) {
  const [excalidrawAPI, setExcalidrawAPI] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)

  useImperativeHandle(ref, () => ({
    appendElements(newElements) {
      if (!excalidrawAPI) return
      const existing = excalidrawAPI.getSceneElements()

      // Compute max X of existing elements to place new ones beside them
      const maxX = existing.reduce((m, el) => Math.max(m, (el.x || 0) + (el.width || 0)), 0)
      const offsetX = maxX > 0 ? maxX + 100 : 0

      const shifted = newElements.map(el => ({ ...el, x: (el.x || 0) + offsetX }))
      excalidrawAPI.updateScene({ elements: [...existing, ...shifted] })
      // Scroll to show new elements
      setTimeout(() => excalidrawAPI.scrollToContent(), 100)
    }
  }), [excalidrawAPI])

  const initialExcalidrawData = initialData
    ? {
        elements: initialData.elements || [],
        appState: { ...(initialData.appState || {}), theme: 'dark' },
        files: initialData.files || {},
      }
    : { appState: { theme: 'dark' } }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      {/* Generate from code button */}
      <button
        onClick={() => setModalOpen(true)}
        style={{
          position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
          zIndex: 10, background: 'var(--primary)', border: 'none', color: '#fff',
          padding: '7px 18px', borderRadius: 20, fontSize: 12, cursor: 'pointer',
          boxShadow: '0 2px 12px #7c6af760', fontWeight: 600, letterSpacing: 0.3,
        }}
      >
        ✦ 从代码生成线框图
      </button>

      <Excalidraw
        excalidrawAPI={api => setExcalidrawAPI(api)}
        initialData={initialExcalidrawData}
        onChange={onChange}
        theme="dark"
      />

      {modalOpen && (
        <SourceAnalyzerModal
          onAppend={elements => ref.current?.appendElements(elements)}
          onClose={() => setModalOpen(false)}
        />
      )}
    </div>
  )
})

export default WireframeTab
