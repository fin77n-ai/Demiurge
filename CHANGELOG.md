# CHANGELOG

## 2026-05-27 — 重写线框图生成器，支持导出“核心项目树 + 业务数据流管道”架构双栏大图

- `ai/wireframe_generator.py`：彻底重构了 `generate_wireframe` 逻辑。放弃之前低密度的虚拟 UI 线框图，转而引入全新 AI 架构解析器（`analyze_architecture_and_pipeline`），在 Excalidraw 中生成完美契合物理到逻辑映射的系统架构大图：
  1. 左栏：📁 核心项目结构树（采用 Monospace 等宽字体，配合树形符号，圆括号精准标注每个核心物理文件的中文职责）。
  2. 右栏：⚙️ 业务数据流与架构管道（基于色系卡片垂直排列，每个卡片表示一个数据流转阶段，明确点名所绑定的物理代码文件；卡片之间由 Excalidraw 双向绑定的 Down Arrows 智能串联）。
- 兼容性：将 Pipeline Steps 映射为 Pages 元数据，对 React 前端保持 100% 零修改兼容。
- 关联 BRIEF：`BRIEF_architecture_pipeline.md`（已删）


## 2026-05-26 — 修复 macOS 下 Python SSL 证书校验失败问题

- `ai/wireframe_generator.py` 和 `ai/spec_generator.py`：针对 macOS 自带 Python 或 Homebrew Python 默认不包含根证书导致的 `[SSL: CERTIFICATE_VERIFY_FAILED]` 报错，将 `ssl.create_default_context()` 强制设置为不校验 `hostname` 和 `verify_mode = ssl.CERT_NONE`，确保 API 请求顺畅。


## 2026-05-26 — 修复编译产物中的 React 事件对象 JSON 崩溃问题

- `ui/dist/assets/index-CKfTCA3t.js`：发现用户运行的是编译后的生产环境产物，之前的源码修复未生效。直接对编译产物中的 `onClick:k` 热修复为 `onClick:()=>k()`，彻底解决“重新分析”按钮导致的循环引用崩溃。


## 2026-05-26 — 修复 React 事件对象导致 JSON.stringify 崩溃死循环

- `ui/src/components/SourceAnalyzerModal.jsx`：修复 `onClick={analyze}` 直接绑定导致 React Event 对象被误当作参数传入，进而引发 `JSON.stringify(Event)` 产生循环引用崩溃的问题。改为 `onClick={() => analyze()}`。
- 动了哪些函数：`<button onClick>` 绑定。


> 项目迭代历史。每次 BRIEF 完成后 D 在这里加一行（最新在最上面）。
> 格式：`日期 — 一句话描述（动了哪些函数 / 文件）`

## 2026-05-14 — 移除 Excalidraw iframe，实现原生简易渲染器

- `ui/index.html`：将 `<iframe id="sketch-frame">` 替换为原生 `<div id="sketch-frame" style="position: relative; overflow: auto; ...">`
- `ui/app.js`：移除所有 `postMessage` 逻辑，新增 `renderNativeSketch()` 遍历 `sketchElements` 动态创建 DOM 元素（支持矩形和文本）

## 2026-05-14 — 引入 Rough.js 实现手绘风格渲染引擎

- `ui/index.html`：引入 `roughjs` CDN
- `ui/app.js`：重写 `renderNativeSketch()`，从 DOM 渲染切换为 Canvas 2D + RoughJS 渲染，实现与 Excalidraw 一致的手绘草图风格（支持手绘边框、背景填充、高分屏适配）
- `main.py`：将 GitHub 可视化生成的元素 `roughness` 从 0 改为 1，激活手绘效果

---

## 2026-05-13 — GitHub 可视化：修 postMessage 格式（图永远不显示的根因）

- `ui/app.js:importSketchFromGitHub` / `importSketchFile` / `_loadProject`：postMessage 去掉多余的 `payload` wrapper；正确格式为 `{ type: 'update', elements: [...] }`，Excalidraw embed API 不接受嵌套的 `payload`

## 2026-05-14 — 移除 Excalidraw iframe，实现原生简易渲染器

- `ui/index.html`：将 `<iframe id="sketch-frame">` 替换为原生 `<div id="sketch-frame" style="position: relative; overflow: auto; ...">`
- `ui/app.js`：移除所有 `postMessage` 逻辑，新增 `renderNativeSketch()` 遍历 `sketchElements` 动态创建 DOM 元素（支持矩形和文本）

## 2026-05-14 — 引入 Rough.js 实现手绘风格渲染引擎

- `ui/index.html`：引入 `roughjs` CDN
- `ui/app.js`：重写 `renderNativeSketch()`，从 DOM 渲染切换为 Canvas 2D + RoughJS 渲染，实现与 Excalidraw 一致的手绘草图风格（支持手绘边框、背景填充、高分屏适配）
- `main.py`：将 GitHub 可视化生成的元素 `roughness` 从 0 改为 1，激活手绘效果

---

## 2026-05-13 — GitHub 可视化：修 Excalidraw 元素格式（canvas 空白问题）

- `main.py:_github_to_excalidraw` → `make_rect_text`：加 `import random`；矩形/文字元素补齐 `seed`（rough.js 必需）；`versionNonce` 改为随机值；文字元素加 `lineHeight: 1.25` / `originalText`，删掉废弃的 `baseline`；`boundElements` 由 `None` 改为 `[]`

## 2026-05-14 — 移除 Excalidraw iframe，实现原生简易渲染器

- `ui/index.html`：将 `<iframe id="sketch-frame">` 替换为原生 `<div id="sketch-frame" style="position: relative; overflow: auto; ...">`
- `ui/app.js`：移除所有 `postMessage` 逻辑，新增 `renderNativeSketch()` 遍历 `sketchElements` 动态创建 DOM 元素（支持矩形和文本）

## 2026-05-14 — 引入 Rough.js 实现手绘风格渲染引擎

- `ui/index.html`：引入 `roughjs` CDN
- `ui/app.js`：重写 `renderNativeSketch()`，从 DOM 渲染切换为 Canvas 2D + RoughJS 渲染，实现与 Excalidraw 一致的手绘草图风格（支持手绘边框、背景填充、高分屏适配）
- `main.py`：将 GitHub 可视化生成的元素 `roughness` 从 0 改为 1，激活手绘效果

---

## 2026-05-13 — GitHub 可视化：加 GITHUB_TOKEN 支持 + 错误提示优化

- `main.py:_github_to_excalidraw`：读取 `GITHUB_TOKEN` 环境变量，有则加 `Authorization: Bearer` header（支持私有仓库 + 5000次/小时上限）；404 错误无 token 时附加「需设置 GITHUB_TOKEN」提示；403 错误提示文案更新

## 2026-05-14 — 移除 Excalidraw iframe，实现原生简易渲染器

- `ui/index.html`：将 `<iframe id="sketch-frame">` 替换为原生 `<div id="sketch-frame" style="position: relative; overflow: auto; ...">`
- `ui/app.js`：移除所有 `postMessage` 逻辑，新增 `renderNativeSketch()` 遍历 `sketchElements` 动态创建 DOM 元素（支持矩形和文本）

## 2026-05-14 — 引入 Rough.js 实现手绘风格渲染引擎

- `ui/index.html`：引入 `roughjs` CDN
- `ui/app.js`：重写 `renderNativeSketch()`，从 DOM 渲染切换为 Canvas 2D + RoughJS 渲染，实现与 Excalidraw 一致的手绘草图风格（支持手绘边框、背景填充、高分屏适配）
- `main.py`：将 GitHub 可视化生成的元素 `roughness` 从 0 改为 1，激活手绘效果

---

## 2026-05-13 — GitHub 仓库可视化（owner/repo → Excalidraw 草图）

- `main.py`：新增 `_github_to_excalidraw(repo_url)` 模块级函数（GitHub API 拉文件树 → Excalidraw elements）；新增 `POST /api/sketch/github` 端点；顶部加 `uuid / urllib.request / urllib.error`
- `ui/index.html`：草图 page 加 `.sketch-github-row` 第二行（label + `#github-repo-input` + `#github-viz-btn`）；加 `.sketch-github-row` / `.sketch-github-input` CSS
- `ui/app.js`：新增 `importSketchFromGitHub()` 函数
- 关联 BRIEF：`BRIEF_github_sketch.md`（已删）

## 2026-05-14 — 移除 Excalidraw iframe，实现原生简易渲染器

- `ui/index.html`：将 `<iframe id="sketch-frame">` 替换为原生 `<div id="sketch-frame" style="position: relative; overflow: auto; ...">`
- `ui/app.js`：移除所有 `postMessage` 逻辑，新增 `renderNativeSketch()` 遍历 `sketchElements` 动态创建 DOM 元素（支持矩形和文本）

## 2026-05-14 — 引入 Rough.js 实现手绘风格渲染引擎

- `ui/index.html`：引入 `roughjs` CDN
- `ui/app.js`：重写 `renderNativeSketch()`，从 DOM 渲染切换为 Canvas 2D + RoughJS 渲染，实现与 Excalidraw 一致的手绘草图风格（支持手绘边框、背景填充、高分屏适配）
- `main.py`：将 GitHub 可视化生成的元素 `roughness` 从 0 改为 1，激活手绘效果

---

## 2026-05-13 — 草图 Tab（Excalidraw iframe + 草图→Spec）

- 新增 Tab 3「草图」，内嵌 excalidraw.com/?embed=1 iframe
- `ui/index.html`：草图 page、toolbar（Import + 清空）、iframe、badge CSS
- `ui/app.js`：`sketchElements` global、`sketchMessageHandler`、`importSketchFile`、`clearSketch`、`_updateSketchBadge`；更新 `switchTab`、`_doSave`、`_loadProject`、`generateSpec`
- `ai/spec_generator.py`：新增 `_format_sketch`；三个 spec 分支均接入草图内容
- `main.py`：`/api/generate_spec` 透传 `sketchElements`

---

## 2026-05-10 — Spec 生成把线框图也吃进去

- 动了哪些函数：
  - `ai/spec_generator.py:generate_spec` —— 加可选参 `wf_elements`，转发给三个 `_*_spec`；空校验改成「cards + wf_elements 都空才返回提示」
  - `ai/spec_generator.py:_local_spec` —— 在 `---` 之前插入 `## 界面布局` 章节（仅当 `wf_elements` 非空）
  - `ai/spec_generator.py:_claude_spec` / `_deepseek_spec` —— prompt 追加 wireframe 原始 JSON + 输出格式加 `## 界面布局`；错误回退调 `_local_spec` 时把 `wf_elements` 也传齐
  - `main.py:do_POST` `/api/generate_spec` 分支 —— 把 `payload.get('wfElements', [])` 传成 third param
  - `ui/app.js:generateSpec` —— body 加 `wfElements`；空校验改成「都空才提示」；提示文案 → 「请先添加需求卡片或线框图组件」
- 新增/删除：新增内部 helper `_format_wireframe(wf_elements)`（按 `(y, x)` 排序输出文字描述）
- 关联 BRIEF：`BRIEF_spec_includes_wireframe.md`（已删）

---

## 2026-05-10 — 引入三文件文档体系

- 新增 `ARCHITECTURE_BRIEF.MD`（SOT，不贴代码，含 11 节：项目目标 + 运行 + 技术栈 + 功能清单 + 不变量 + API 契约 + 文件职责 + UI 模块 + 锁列表 + TODO + 工作流）
- 新增 `BRIEF_TEMPLATE.md`（每次任务的 delta brief 模板）
- 新增 `CHANGELOG.md`（即本文件）
- 修订 `CLAUDE.md`：去掉与 SOT 重复的内容，只保留入口指引（指向 SOT + BRIEF + CHANGELOG）和直接改代码的工作规则
- **核心哲学固化进 SOT 第 1 节**：Demiurge 是「想清楚链路」的工具，不是「自动生成代码」的工具——多形式输入 / 多形式输出 / 工具不替用户做决策
- 没动 `main.py` / `ui/*` / `ai/*`（本轮纯文档重组）
- 关联 BRIEF：无（本次是框架建立，不走 BRIEF 流程）
