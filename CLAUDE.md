# Demiurge — 项目协议

> 造物主。把脑子里的想法变成 AI 可以执行的结构化 spec。

## 项目定位

**Stage 1 工具**：在写代码之前，帮用户把模糊的需求可视化、结构化，输出 AI 可直接理解的 Markdown spec。

与 Architect 的关系：
- Demiurge → 需求 → Spec（Stage 1，这个项目）
- Architect → 代码分析 → 诊断（Stage 2，已有工具）

## 核心流程

```
用户拖拽/填写需求卡片
        ↓
Demiurge 调用 AI 结构化
        ↓
生成标准 Spec Markdown
        ↓
直接复制给 Claude / 任何 AI 执行
```

## 运行

```bash
python3 main.py
```

## 架构

```
Demiurge/
├── main.py                # 本地 HTTP server 入口
├── board_state.json       # 自动保存状态（cards + wfElements）
├── ui/
│   ├── index.html         # 主界面（Tab: 需求画板 | 线框图）
│   └── app.js             # 前端逻辑（两个 Tab 共用）
├── ai/
│   └── spec_generator.py  # 调用 AI 把卡片转成 Spec MD
└── CLAUDE.md              # 本文件
```

## 界面布局

**Tab 1 — 需求画板**
```
┌─────────────────────┬──────────────────────┬────────────┐
│  需求画板            │  AI Spec 预览         │  导出       │
│  + 新建卡片          │  ## 目标              │  复制 MD    │
│  [卡片: 标题/描述]   │  ## 用户路径          │            │
│  [卡片: 标题/描述]   │  ## 数据结构          │            │
└─────────────────────┴──────────────────────┴────────────┘
```

**Tab 2 — 线框图**
```
┌──────────┬───────────────────────────────────────────────┐
│  组件面板 │  画板（网格，可拖放）                           │
│  Header   │  ┌──────────────── Header ────────────────┐  │
│  Nav Bar  │  ├── Sidebar ──┬──────── Container ───────┤  │
│  Sidebar  │  │             │  [Button]  [Input]        │  │
│  Button   │  └─────────────┴──────────────────────────┘  │
│  ...      │                                               │
└──────────┴───────────────────────────────────────────────┘
```

## 线框图功能

- 从左侧面板拖拽组件到画板（自动吸附 20px 网格）
- 选中后可鼠标拖动移动、拖拽 handle 缩放
- 双击编辑标签，Delete 键删除
- 「导出 HTML」→ 下载干净的静态线框图文件
- 「复制描述给 AI」→ 把布局转成文字描述复制到剪贴板

## 保存机制

- **自动保存**：任何改动 1.5 秒后自动写入 `board_state.json`
- **手动保存**：顶部 Save 按钮
- `board_state.json` 包含：`cards`、`wfElements`、`wfNextId`、`projectName`

## 卡片类型

- `feature` — 功能点
- `ui` — 界面/交互
- `data` — 数据结构
- `constraint` — 约束/限制
- `flow` — 用户路径

## API 接口契约

- `GET /` — 主界面
- `POST /api/generate_spec` — 传入卡片列表，返回结构化 Spec MD
- `POST /api/save` — 保存当前画板状态
- `GET /api/load` — 加载上次状态

## Claude 直接改代码规则

每次确认功能变更后，必须在同一对话内：
1. 直接 Edit 对应文件落地代码
2. 更新本 CLAUDE.md 反映新状态
