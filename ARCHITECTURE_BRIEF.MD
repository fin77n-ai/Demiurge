# Demiurge — 架构 SOT

> 这份文档是**信息源真理（SOT）**，描述项目当前已实现状态、不变量、文件职责。
> **本文档不贴代码**——代码就在 `main.py` / `ui/app.js` / `ai/spec_generator.py` 里。
> 想改代码？看 `BRIEF_TEMPLATE.md`，每次任务一个独立 brief。
> 历史变更看 `CHANGELOG.md`。

---

## 0. 快速定位（给 AI 架构助手看）

```
Demiurge/
├── main.py                  # Python stdlib HTTP server + all API routes
├── ai/
│   ├── __init__.py          # 🔒 package marker
│   └── spec_generator.py    # AI spec generation (Claude/DeepSeek/local fallback)
├── ui/
│   ├── index.html           # single-page app shell: topbar + 3 tabs + CSS
│   └── app.js               # all frontend logic (~550 lines, vanilla JS)
├── saves/
│   └── <slug>.json          # per-project state (cards + wfElements + sketchElements)
├── ARCHITECTURE_BRIEF.MD    # 🔒 this file — SOT, only D updates
├── CLAUDE.md                # agent entry point & red lines
├── BRIEF_TEMPLATE.md        # template for per-task change briefs
└── CHANGELOG.md             # 🔒 iteration history
```

**One-liner per key file:**
- `main.py` — `DemiurgeHandler` handles all GET/POST routes; `find_free_port` + `webbrowser.open` on startup
- `spec_generator.py` — `generate_spec(cards, project_name, wf_elements, sketch_data)` → Markdown string; calls `_claude_spec` → `_deepseek_spec` → `_local_spec`; `_format_wireframe` and `_format_sketch` produce readable sections
- `index.html` — dark-theme CSS + 3 tabs (需求画板 / 线框图 / 草图); sketch tab embeds `excalidraw.com/?embed=1`
- `app.js` — global state + `switchTab` + `_doSave` / `_loadProject` + wireframe drag-and-drop + sketch postMessage bridge

---

## 1. 项目目标（核心哲学，不可漂移）

**Demiurge 是「想清楚链路」的工具，不是「自动生成代码」的工具。**

用户先用任何形式（卡片 / 线框图 / 未来更多形式）把脑子里模糊的需求结构化、可视化，
然后用任何媒介（Spec MD / 线框图 HTML / 文字描述）和 LLM 沟通达成自己的目的。

- **Stage 1 工具**：在写代码之前。Architect 是 Stage 2（代码诊断），Demiurge 是 Stage 1（需求结构化）
- **多形式输入**：当前是「需求卡片」+「线框图」，未来可加流程图 / 状态机 / 用户旅程等
- **多形式输出**：当前是 Spec MD + 线框图 HTML + 线框图文字描述，输出形式保持灵活
- **核心是用户自己想清楚**：工具不替用户做决策；它只把脑子里的链路落地成 LLM 能读的东西

任何改动都要问：**这是在帮用户更好地"想清楚"吗？还是在自动化掉用户的思考？**

## 2. 运行

```
python3 main.py
```

启动后自动开浏览器到 `http://localhost:<7070+>`。

## 3. 技术栈

- 后端：Python 3 标准库（`http.server`，**无 Flask**）
- 前端：原生 JS（无框架）+ 内嵌 CSS（dark theme）
- 数据持久化：每个项目一份 `saves/<slug>.json`
- AI：可选 Anthropic Claude Haiku / DeepSeek，无 key 时本地回退

## 4. 已实现功能清单（按模块）

### A. 后端 — `main.py`
- Project CRUD：list / load / save / create / delete / rename（基于 `saves/<slug>.json`）
- Slug 处理：`slugify` / `unique_slug`（避免重名）/ `safe_slug`（防注入，≤64 字符）
- 静态服务：`/` / `/index.html` / `/ui/*`
- AI 端点：`POST /api/generate_spec`
- Legacy 端点：`/api/save` + `/api/load`（迁移用，仍保留）
- 启动：自由端口（7070+）+ 自动开浏览器
- `ensure_saves_dir()`：自动创建 `saves/` + 迁移老 `board_state.json` → `saves/default.json`

### B. 后端 — `ai/spec_generator.py`
三段降级：`ANTHROPIC_API_KEY` → `DEEPSEEK_API_KEY` → 本地纯模板
- `_claude_spec`：模型 `claude-haiku-4-5-20251001`，30s 超时
- `_deepseek_spec`：模型 `deepseek-chat`，30s 超时
- `_local_spec`：按类型分组输出（flow → feature → ui → data → constraint）
- AI 调用失败时自动回退到 `_local_spec` 并附错误信息
- `_format_wireframe(wf_elements)`：线框图组件 → `## 界面布局` Markdown 节
- `_format_sketch(sketch_elements)`：Excalidraw JSON → `## 草图分析` Markdown 节（shapes / arrows / texts）

### C. 前端状态层（globals）
`cards` / `currentSpec` / `wfElements` / `wfNextId` / `wfSelectedId` / `sketchElements` / `currentSlug` / `_autoSaveTimer` / `_wfDrag` / `_wfAction`。

### D. Tab 切换
`switchTab(name)` —— 切换需求 / 线框图 / 草图（i=0/1/2），主操作按钮（`#main-action-btn`）随之切换（线框图=导出，其余=✦ Generate Spec）。

### E. 项目面板
`toggleProjectPanel` / `openProjectPanel` / `closeProjectPanel` / `loadProjects` / `renderProjectList` / `switchProject` / `newProject` / `deleteProject`。
切换 / 新建前先 `_doSave()` 保存当前。**至少保留一个项目，不可删光**。

### F. 需求画板
- `renderCards` / `updateStats`
- `toggleAddForm` / `submitCard`（标题必填）/ `deleteCard`

### G. Spec 生成
- `generateSpec`：POST `/api/generate_spec`，body 含 `cards` / `wfElements` / `sketchElements`
- `renderSpec` / `copySpec`（→ 剪贴板）/ `downloadSpec`（→ 下载 .md）

### H. 线框图 — 渲染
- `wfRender`：每个元素一个 absolute div，选中时显示三个 handle（se / e / s）
- 网格背景（20px）通过 CSS linear-gradient 实现

### I. 线框图 — 拖拽创建
- `wfInitPalette`：HTML5 drag&drop 从左侧 palette 到画板
- 落点自动吸附 20px 网格 `Math.round(.../20)*20`

### J. 线框图 — 移动 / 缩放
- 全局 `mousemove` 监听 `_wfAction`（kind: 'move' | 'resize'）
- move：min (0,0)；resize：min w=40, h=24
- `mouseup` 结束动作并触发 `scheduleAutoSave()`

### K. 线框图 — 操作
- `wfClearSelected` / `wfDeleteSelected` / `wfClear`
- 全局 `keydown`：Delete / Backspace 删除选中（焦点在 input / textarea 时**不触发**）
- 双击元素 → `prompt` 编辑标签

### L. 线框图 — 导出
- `exportWireframe`：拼一份纯静态 HTML（absolute 定位 + 内联样式），下载
- `copyWireframeAsText`：按 (y, x) 排序后输出文字布局描述到剪贴板（喂给 LLM）

### M. 保存
- `scheduleAutoSave`：1.5s debounce
- `_doSave`：POST `/api/projects/save`，body 含 `slug` / `projectName` / `cards` / `wfElements` / `wfNextId` / `sketchElements`
- `loadBoard`：启动时取项目列表第一项
- `_loadProject(slug)`：拉取并 reset 前端状态（含 `sketchElements`，若有内容则 postMessage 恢复 iframe）

### N. 草图（Excalidraw）
- `sketchElements`：Excalidraw JSON elements 数组，随项目保存/加载
- `sketchMessageHandler`：监听 `window.message`，捕捉来自 `excalidraw.com` iframe 的 `payload.elements`
- `importSketchFile(input)`：读取 `.excalidraw` 文件，解析 `data.elements`，postMessage 推送到 iframe
- `clearSketch()`：清空 `sketchElements`
- `_updateSketchBadge()`：根据 `sketchElements.length` 切换 tab badge `.visible`

## 5. 关键不变量

改动绝对不能违反：

1. **每个项目一份 `saves/<slug>.json`**，不是单文件 `board_state.json`。slug 由 `safe_slug` 校验
2. **至少保留一个项目**：`deleteProject` 在 `list.length <= 1` 时阻止删除
3. **画板 = 卡片 + 线框图 + 草图**三类内容统一保存在同一个项目的 JSON 里（key 固定：`cards` / `wfElements` / `wfNextId` / `sketchElements` / `projectName`）
4. **网格 = 20px**：drop 落点 + move + resize 步进都对齐 20
5. **resize 最小尺寸**：w ≥ 40, h ≥ 24
6. **auto-save = 1.5s debounce**：任何画板改动后调 `scheduleAutoSave()`
7. **AI 三段降级**：Anthropic → DeepSeek → 本地纯模板。**不许去掉本地回退**（无 key 时也得能用）
8. **卡片 5 类**：`feature` / `ui` / `data` / `constraint` / `flow`（含义见 `ai/spec_generator.py:CARD_TYPE_LABELS`）
9. **Legacy `/api/save` + `/api/load`** 保留（迁移期），不要随便删
10. **多形式输出并存**：Spec MD / 线框图 HTML / 线框图文字描述三种产出并列存在，不可砍其中一种
11. 切换 / 新建项目前必须 `await _doSave()` 先保存当前（避免丢数据）

## 6. API 契约（后端，绝不可改签名）

```
GET  /                            主页（ui/index.html）
GET  /ui/<file>                   静态资源
GET  /api/projects                项目列表
GET  /api/projects/load?slug=     加载指定项目
POST /api/projects/save           保存
POST /api/projects/create         新建
POST /api/projects/delete         删除
POST /api/projects/rename         重命名
POST /api/generate_spec           AI 生成 spec
GET  /api/load                    legacy：加载默认项目
POST /api/save                    legacy：保存默认项目
```

## 7. 文件职责

| 文件 | 角色 | 可改？ |
|------|------|--------|
| `main.py` | HTTP server + API | ⚠️ 仅 BRIEF 明确允许时 |
| `ai/spec_generator.py` | AI 调用 + 本地 fallback | ⚠️ 仅 BRIEF 明确允许时 |
| `ai/__init__.py` | 包标记 | ❌ 锁 |
| `ui/index.html` | UI 模板（topbar + tabs + 两个 page） | ✅ 默认执行区之一 |
| `ui/app.js` | 全部前端逻辑（约 550 行） | ✅ 默认执行区之一 |
| `saves/*.json` | 用户数据 | ❌ 不许程序之外的方式写 |
| `board_state.json`（如存在）| 老数据，自动迁移 | ❌ 留着兼容 |
| `ARCHITECTURE_BRIEF.MD` | 本文档 | ❌ 只有 D 在确认变更后更新 |
| `CHANGELOG.md` | 历史 | ❌ 只有 D 写 |
| `BRIEF_TEMPLATE.md` | 任务模板 | ✅ 复制改名为 `BRIEF_<task>.md` 用 |

## 8. UI 模块（ui/index.html）

- **topbar**：⚗ Demiurge logo / Projects 切换按钮 / project-name input / Save / 主操作按钮（随 tab 变化：`✦ Generate Spec` 或 `导出线框图`）
- **tabs**：需求画板 / 线框图 / 草图（3 tabs，i=0/1/2）
- **需求画板页**：左侧卡片栏（340px）+ 中间 Spec 预览 + 右侧导出（220px，含统计）
- **线框图页**：toolbar + 左侧 palette（130px，11 种组件：header / nav / sidebar / container / button / input / card / list / image / text / modal）+ 右侧画板（20px 网格）
- **草图页**：toolbar（Import .excalidraw + 清空）+ `excalidraw.com/?embed=1` iframe（flex:1）；tab 含 badge `●` 当有内容时亮起
- **项目面板**：左上抽屉式弹出，列出项目 + 新建按钮 + 项目级删除

## 9. 🚫 锁列表（执行模型一律不得改）

- `ai/__init__.py` / 任何 `__pycache__/`
- 本文档（`ARCHITECTURE_BRIEF.MD`）—— 只有 D 在确认变更后更新
- `CHANGELOG.md` —— 只有 D 写
- `saves/*.json` —— 用户数据
- 当前所有已实现的函数：除非 BRIEF 明确点名要改，否则一律不动

## 10. 待清理项 / 已知 TODO

（暂无。本轮重组只建框架，未发现明确的死代码。）

## 11. 工作流

**当前模式 = D 直接 Edit**（Demiurge 还没接 Gemini 执行模型）：

```
P 提需求
   ↓
D 写 BRIEF_<task>.md（即便自己执行也走一遍，留痕）
   ↓
D 直接 Edit 代码
   ↓
D 在 CHANGELOG.md 加一行
   ↓
删掉用过的 BRIEF_<task>.md
```

**未来切到 D ↔ Gemini 模式**时：

```
P 提需求 → D 写 BRIEF → 贴给 Gemini → Gemini 改代码 → D 人工 diff + 启动 smoke → CHANGELOG 加一行 → 删 BRIEF
```

**执行模型红线**（不论 D 自己还是 Gemini）：
- 只动 BRIEF 第 2 节点名的文件 + 函数
- 不许执行 git 命令
- 不许修改本文档（`ARCHITECTURE_BRIEF.MD`）和 `CHANGELOG.md`
- 不许新增 `fix_*.py` / `apply_*.py` / `analyze_*.py` 这类补丁脚本
- 不许重写整个文件
