import os
import re
import json
import random
import string
import time
import urllib.request
import urllib.error
import ssl

# ── Constants ─────────────────────────────────────────────────

FRONTEND_EXTS  = {'.jsx', '.tsx', '.vue', '.html', '.js', '.ts', '.py'}
SKIP_DIRS      = {'node_modules', 'dist', 'build', '.git', '__pycache__',
                  '.next', 'out', '.nuxt', '.vite', '.cache', 'coverage'}
PAGE_DIRS      = {'pages', 'views', 'screens', 'routes', 'app'}
CONFIG_NAMES   = {'package.json', 'requirements.txt', 'pipfile', 'gemfile',
                  'go.mod', 'cargo.toml', 'readme.md', 'readme.rst',
                  'docker-compose.yml', 'pyproject.toml', '.env.example', 'makefile'}

MAX_SELECT_FILES = 25
MAX_FILE_BYTES   = 15_000 # Increased to capture larger files fully
CONFIG_MAX_BYTES = 4_000

# High-contrast Light Mode Palette (perfect for PPT/Markdown exports)
PIPELINE_COLORS = {
    'green':  ('#f0fdf4', '#16a34a', '#14532d', '#166534'),  # bg, stroke, title_text, desc_text
    'purple': ('#f5f3ff', '#7c3aed', '#581c87', '#6b21a8'),
    'blue':   ('#eff6ff', '#2563eb', '#1e3a8a', '#1e40af'),
    'yellow': ('#fefce8', '#ca8a04', '#713f12', '#854d0e'),
    'orange': ('#fff7ed', '#ea580c', '#7c2d12', '#9a3412'),
    'red':    ('#fef2f2', '#dc2626', '#7f1d1d', '#991b1b'),
    'gray':   ('#f8fafc', '#475569', '#0f172a', '#334155'),
}


# ── Excalidraw element builders ────────────────────────────────

def _id():   return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
def _seed(): return random.randint(100_000, 999_999)
def _ts():   return int(time.time() * 1000)

_BASE = {
    'angle': 0, 'fillStyle': 'solid', 'strokeWidth': 1, 'strokeStyle': 'solid',
    'roughness': 1, 'opacity': 100, 'groupIds': [], 'frameId': None,
    'roundness': None, 'isDeleted': False, 'boundElements': None,
    'link': None, 'locked': False, 'version': 1,
}

def _rect(x, y, w, h, frame_id=None, bg='transparent', stroke='#9ca3af'):
    eid, ts = _id(), _ts()
    return {**_BASE, 'id': eid, 'type': 'rectangle', 'x': x, 'y': y,
            'width': w, 'height': h, 'seed': _seed(), 'versionNonce': _seed(),
            'updated': ts, 'frameId': frame_id, 'backgroundColor': bg,
            'strokeColor': stroke, 'boundElements': []}

def _frame(x, y, w, h, name):
    eid, ts = _id(), _ts()
    return {**_BASE, 'id': eid, 'type': 'frame', 'x': x, 'y': y,
            'width': w, 'height': h, 'seed': _seed(), 'versionNonce': _seed(),
            'updated': ts, 'name': name,
            'strokeColor': '#cbd5e1', 'backgroundColor': 'transparent'}

def _free_text(text, x, y, w, h, frame_id, size=12, color='#1e293b',
               align='left', valign='top', font_family=1):
    """Free-floating text — NOT bound to any container, so position is ours to control."""
    eid, ts = _id(), _ts()
    return {**_BASE, 'id': eid, 'type': 'text',
            'x': x, 'y': y, 'width': w, 'height': h,
            'seed': _seed(), 'versionNonce': _seed(), 'updated': ts,
            'frameId': frame_id, 'containerId': None,
            'text': text, 'originalText': text,
            'fontSize': size, 'fontFamily': font_family,
            'textAlign': align, 'verticalAlign': valign,
            'lineHeight': 1.4, 'autoResize': False,
            'strokeColor': color, 'backgroundColor': 'transparent',
            'boundElements': None}


# ── AI caller ─────────────────────────────────────────────────

# Accumulate token usage across all calls in one generation run
_token_log = {'input': 0, 'output': 0, 'calls': 0}

def _reset_tokens():
    _token_log['input'] = _token_log['output'] = _token_log['calls'] = 0

def _call_ai(system_prompt, user_content, max_tokens=1500):
    key_claude   = os.environ.get('ANTHROPIC_API_KEY')
    key_deepseek = os.environ.get('DEEPSEEK_API_KEY')
    if not (key_claude or key_deepseek):
        raise RuntimeError('未设置 ANTHROPIC_API_KEY 或 DEEPSEEK_API_KEY')

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    if key_claude:
        payload = json.dumps({
            'model': 'claude-haiku-4-5-20251001',
            'max_tokens': max_tokens,
            'system': system_prompt,
            'messages': [{'role': 'user', 'content': user_content}],
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages', data=payload,
            headers={'x-api-key': key_claude, 'anthropic-version': '2023-06-01',
                     'content-type': 'application/json'})
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            resp = json.loads(r.read())
        usage = resp.get('usage', {})
        _token_log['input']  += usage.get('input_tokens', 0)
        _token_log['output'] += usage.get('output_tokens', 0)
        _token_log['calls']  += 1
        return resp['content'][0]['text']
    else:
        payload = json.dumps({
            'model': 'deepseek-chat', 'max_tokens': max_tokens,
            'messages': [{'role': 'system', 'content': system_prompt},
                         {'role': 'user',   'content': user_content}],
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.deepseek.com/v1/chat/completions', data=payload,
            headers={'Authorization': f'Bearer {key_deepseek}',
                     'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
            resp = json.loads(r.read())
        usage = resp.get('usage', {})
        _token_log['input']  += usage.get('prompt_tokens', 0)
        _token_log['output'] += usage.get('completion_tokens', 0)
        _token_log['calls']  += 1
        return resp['choices'][0]['message']['content']


def _parse_json(raw):
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw.strip())
    
    # Replace \u when not followed by 4 hex digits (e.g. \user) with u
    raw = re.sub(r'\\u(?![0-9a-fA-F]{4})', 'u', raw)
    
    # Replace any invalid backslash escape (not followed by b, f, n, r, t, ", \, /) with just the character
    raw = re.sub(r'\\([^bfnrt"\\/])', r'\1', raw)
    
    return json.loads(raw.strip())


# ── Path helpers ───────────────────────────────────────────────

def _norm(p):
    return p.replace('\\', '/').lstrip('.').lstrip('/')


# ── Phase 1: File tree ────────────────────────────────────────

def get_github_tree(repo_url):
    match = re.search(r'github\.com/([^/]+)/([^/?#]+)', repo_url)
    if not match:
        raise ValueError('无效的 GitHub 地址')
    owner = match.group(1)
    repo  = match.group(2).rstrip('/')
    ctx   = ssl.create_default_context()

    url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1'
    req = urllib.request.Request(url, headers={'User-Agent': 'Demiurge/1.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        data = json.loads(r.read())

    paths = [item['path'] for item in data.get('tree', []) if item['type'] == 'blob']
    return owner, repo, paths


def get_local_tree(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f'路径不存在：{folder_path}')
    paths = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            rel = os.path.relpath(os.path.join(root, fname), folder_path)
            paths.append(rel.replace('\\', '/'))
    return paths


# ── Phase 2: Fetch file content ───────────────────────────────

def _fetch_github(owner, repo, paths, max_bytes=MAX_FILE_BYTES):
    ctx     = ssl.create_default_context()
    headers = {'User-Agent': 'Demiurge/1.0'}
    result  = {}
    for path in paths:
        url = f'https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}'
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                result[path] = r.read(max_bytes).decode('utf-8', errors='replace')
        except Exception:
            continue
    return result


def _fetch_local(folder_path, paths, max_bytes=MAX_FILE_BYTES):
    result = {}
    for rel in paths:
        try:
            with open(os.path.join(folder_path, rel), 'r', encoding='utf-8', errors='replace') as f:
                result[rel] = f.read(max_bytes)
        except Exception:
            continue
    return result


# ── Phase 3: Doctor — understand project ──────────────────────

DOCTOR_SYSTEM = """你是代码架构专家。分析项目文件树和配置文件，识别技术栈。

只返回合法 JSON，不要 markdown 代码块，不要解释：
{
  "project_type": "简短描述（如：React SPA、Flask + React 全栈、Next.js 全栈、Vue + Express 等）",
  "frontend_framework": "react|vue|angular|svelte|html|none",
  "backend_framework": "express|fastapi|flask|django|spring|rails|go|none",
  "frontend_files": ["最重要的前端文件路径，优先页面/路由/布局组件，最多15条"],
  "backend_files": ["最重要的后端路由/API/Model文件路径，最多10条"],
  "notes": "一句话说明项目用途"
}

重要：只填写实际存在于文件树中的路径，不要捏造路径。"""


def doctor_analysis(all_paths, config_content):
    tree_text   = '\n'.join(all_paths[:400])
    config_text = '\n\n'.join(f'=== {k} ===\n{v}' for k, v in config_content.items())
    raw = _call_ai(DOCTOR_SYSTEM,
                   f'文件树：\n{tree_text}\n\n配置文件：\n{config_text}',
                   max_tokens=800)
    return _parse_json(raw)


# ── Phase 4: Smart Architecture & Pipeline Analysis ───────────

ARCH_PIPELINE_SYSTEM = """你是世界级的软件架构师与数据流分析专家。
请深度分析用户提供的项目文件和配置文件，理解它的项目物理结构以及它底层的核心业务数据流（如：从数据摄入、清洗、Embedding 向量化、物理存储、再到检索和重排的 RAG 管道，或者其电控/API 业务管道）。

你需要返回一个合法的 JSON，不要包含 any markdown 代码块，不要有任何额外解释：
{
  "title": "🛡 Demiurge: <项目名> 架构与数据流向图",
  "subtitle": "模块结构树 + <管道类型，例如：双阶段 RAG / 业务API数据> 管道",
  "project_tree_text": "用 📁 📄 和树状线条(├──, └──, │)格式化好的核心项目结构树，重点突出，只展示最关键的文件夹和文件（不超过25个文件/夹），并在每个核心文件右侧用圆括号附上简短的中文职责描述。例如：\\nquip-rag/\\n├── backend/ (FastAPI 后端)\\n│   ├── main.py (入口与 API 路由)\\n│   └── services/ (核心引擎服务)\\n│       ├── quip_parser.py (HTML 精准重构)\\n│       └── staging_store.py (SQLite 暂存)",
  "pipeline_steps": [
    {
      "title": "阶段标题，如：Quip JSON 上传与 HTML 结构提取",
      "description": "详细的中文数据流向说明，说明在这个阶段数据发生了什么转变、流向了何处、调用了左侧结构树中的哪些具体文件或模块。字数约 60-120 字。",
      "icon": "📤", // 一个贴切的 Emoji 字符
      "color": "green" // 必须是以下之一: green, purple, blue, yellow, orange, red, gray
    }
  ]
}

关键指导规则（极其核心，请严格执行）：
1. 核心项目结构树：
   - 必须真实反映用户项目中的目录和文件结构，绝对禁止凭空捏造不存在的文件夹。
   - 层级清晰，使用标准的树状连接符。
   - 文件名和文件夹名必须 100% 准确，职责描述要简练、专业（例如：控制器、数据访问层、契约定义、向量化服务等）。
2. 业务数据流管道与高精密度技术提取（绝对不可丢失细节）：
   - 必须设计 3 到 5 个连续的数据流转阶段，表现一个完整的端到端物理到逻辑数据流闭环。
   - 深度挖掘代码中使用的具体底层数据库、检索算法、权重模型（例如：DuckDB, LanceDB, SQLite, ChromaDB, BGE-M3, MMR 多样化去重, BGE-Reranker 本地重排, Pydantic, FastAPI, rules 过滤等）。
   - 绝对不放过任何一处关键技术细节！即便在代码里只出现了一次（例如 rules_store.py / duck_lance_store.py / retrieval_scoring.py 中的 DuckDB / MMR 检索逻辑），也必须在 Pipeline 对应步骤的 description 中极其详尽地体现出来！
   - 每个阶段在 description 中必须明确点名它调用了左侧结构树中的哪些具体物理代码文件和逻辑架构。
   - 绝对禁止使用“内容区”“主区域”“占位符”等毫无业务意义的泛泛词汇，必须百分之百针对该项目的技术栈与业务场景定制，彰显真实的架构灵魂！
"""


def analyze_architecture_and_pipeline(files_dict, project_type, notes, all_paths):
    # Expanded file selection up to 24 files, and read up to 6000 chars per file to prevent truncating databases and specialized scripts (like DuckDB and MMR scorer)
    files_text = '\n\n'.join(
        f'=== {path} ===\n{content[:6000]}' for path, content in list(files_dict.items())[:24]
    )
    tree_summary = '\n'.join(all_paths[:200])
    user_content = (f"项目类型：{project_type}\n项目说明：{notes}\n"
                    f"完整文件树（前200个）：\n{tree_summary}\n\n"
                    f"核心代码文件内容：\n{files_text}")
    raw = _call_ai(ARCH_PIPELINE_SYSTEM, user_content, max_tokens=3500)
    return _parse_json(raw)


def _heuristic_select(all_paths):
    candidates = [p for p in all_paths if os.path.splitext(p)[1] in FRONTEND_EXTS]
    candidates.sort(key=lambda p: (
        0 if any(d in p.split('/') for d in PAGE_DIRS) else
        1 if any(k in p.lower() for k in ('index', 'app', 'router', 'main', 'layout')) else 2
    ))
    return candidates[:MAX_SELECT_FILES]


# ── Main Entry ────────────────────────────────────────────────

def generate_wireframe(source_type, source_path):
    _reset_tokens()

    # ── Phase 1: File tree ──────────────────────────────────
    if source_type == 'github':
        owner, repo, raw_paths = get_github_tree(source_path)
    else:
        raw_paths = get_local_tree(source_path)

    # Strip skip dirs
    all_paths = [
        p for p in raw_paths
        if not any(part in SKIP_DIRS for part in p.split('/'))
    ]
    all_paths_norm = {_norm(p): p for p in all_paths}  # normalized → original

    # ── Phase 2: Config files ───────────────────────────────
    config_paths = [
        p for p in all_paths
        if os.path.basename(p).lower() in CONFIG_NAMES
    ][:8]

    if source_type == 'github':
        config_content = _fetch_github(owner, repo, config_paths, max_bytes=CONFIG_MAX_BYTES)
    else:
        config_content = _fetch_local(source_path, config_paths, max_bytes=CONFIG_MAX_BYTES)

    # ── Phase 3: Doctor ─────────────────────────────────────
    project_map  = doctor_analysis(all_paths, config_content)
    project_type = project_map.get('project_type', 'Unknown')
    notes        = project_map.get('notes', '')

    # ── Phase 4: Smart file selection ───────────────────────
    suggested = (project_map.get('frontend_files', []) +
                 project_map.get('backend_files', []))

    # Validate: doctor sometimes hallucinations paths — only keep real ones
    valid = []
    for p in suggested:
        n = _norm(p)
        if n in all_paths_norm:
            valid.append(all_paths_norm[n])

    # Fallback if doctor picked nothing valid
    if not valid:
        valid = _heuristic_select(all_paths)

    valid = valid[:MAX_SELECT_FILES]

    if source_type == 'github':
        files_content = _fetch_github(owner, repo, valid)
    else:
        files_content = _fetch_local(source_path, valid)

    if not files_content:
        raise RuntimeError('未能读取任何文件内容')

    # ── Phase 5: Analyze Architecture & Pipeline ───────────
    arch_data = analyze_architecture_and_pipeline(files_content, project_type, notes, all_paths)
    
    title             = arch_data.get('title', '🛡 Demiurge: 项目架构与数据流向图')
    subtitle          = arch_data.get('subtitle', '模块结构树 + 核心业务数据管道')
    project_tree_text = arch_data.get('project_tree_text', '')
    pipeline_steps    = arch_data.get('pipeline_steps', [])

    all_elements = []

    # Calculate layout geometry
    tree_lines      = project_tree_text.strip().splitlines()
    tree_line_count = len(tree_lines)
    tree_content_h  = tree_line_count * 24 + 100
    tree_frame_h    = max(640, tree_content_h)

    step_count     = len(pipeline_steps)
    pipe_content_h = step_count * 190 + 100
    frame_h        = max(640, tree_content_h, pipe_content_h)

    # Create one single top-level outer frame to ensure Excalidraw Frame-export grabs everything cleanly!
    outer_frm = _frame(10, 10, 1160, frame_h + 160, "🛡️ Demiurge 架构与数据流向图")
    all_elements.append(outer_frm)

    # ── SOLID Light-Gray Card Canvas Background ──────────────
    # Ensures high-contrast readability whether exported as transparent PNG, white background, or light mode.
    # Appended inside the outer frame so that frame-level exports inherit the background.
    bg_rect = _rect(10, 10, 1160, frame_h + 160, outer_frm['id'], '#f8fafc', '#cbd5e1')
    bg_rect['roughness'] = 0
    bg_rect['fillStyle'] = 'solid'
    all_elements.append(bg_rect)

    # Draw Title and Subtitle inside the outer frame (highly readable slate-900 and slate-600)
    all_elements.append(_free_text(title, 40, 40, 1000, 40, outer_frm['id'], 20, '#0f172a', 'left', 'middle', font_family=1))
    all_elements.append(_free_text(subtitle, 40, 80, 1000, 24, outer_frm['id'], 13, '#475569', 'left', 'middle', font_family=1))

    # Column 1 Panel: 核心项目结构树 (Left Column Box - Solid White)
    tree_bg = _rect(40, 130, 480, frame_h, outer_frm['id'], '#ffffff', '#cbd5e1')
    tree_bg['roundness'] = {'type': 3}
    tree_bg['fillStyle'] = 'solid'
    all_elements.append(tree_bg)
    # Column 1 Header Text
    all_elements.append(_free_text("📁 核心项目结构树", 60, 150, 440, 24, outer_frm['id'], 13, '#0f172a', 'left', 'middle', font_family=1))
    # Tree Text (using dark slate-700 on white panel, monospace font family 3)
    all_elements.append(_free_text(project_tree_text, 60, 190, 440, frame_h - 100, outer_frm['id'], 12, '#334155', 'left', 'top', font_family=3))

    # Column 2 Panel: 业务数据流与架构管道 (Right Column Box - Solid White)
    pipe_bg = _rect(560, 130, 580, frame_h, outer_frm['id'], '#ffffff', '#cbd5e1')
    pipe_bg['roundness'] = {'type': 3}
    pipe_bg['fillStyle'] = 'solid'
    all_elements.append(pipe_bg)
    # Column 2 Header Text
    all_elements.append(_free_text("⚙️ 业务数据流与架构管道", 580, 150, 540, 24, outer_frm['id'], 13, '#0f172a', 'left', 'middle', font_family=1))

    # Sequential Card rect IDs for arrow bindings
    card_ids = [_id() for _ in range(step_count)]

    for j, step in enumerate(pipeline_steps):
        cy = 190 + j * 190
        color_name = step.get('color', 'gray').lower()
        bg, stroke, title_color, desc_color = PIPELINE_COLORS.get(color_name, PIPELINE_COLORS['gray'])
        
        # Rounded Rect Card (Solid Light Color)
        card_rect = _rect(590, cy, 520, 130, outer_frm['id'], bg, stroke)
        card_rect['id'] = card_ids[j] # Override with pre-generated ID
        card_rect['roundness'] = {'type': 3}
        card_rect['fillStyle'] = 'solid'
        card_rect['boundElements'] = []
        all_elements.append(card_rect)

        # Title text (High contrast text)
        title_text = f"{step.get('icon', '🔹')}  {step.get('title', '步骤')}"
        title_el = _free_text(title_text, 610, cy + 15, 480, 24, outer_frm['id'], 13, title_color, 'left', 'middle', font_family=1)
        all_elements.append(title_el)

        # Description text (High contrast dark grey text)
        desc_el = _free_text(step.get('description', ''), 610, cy + 45, 480, 75, outer_frm['id'], 11, desc_color, 'left', 'top', font_family=1)
        all_elements.append(desc_el)

        # Draw down arrow if not last step
        if j < step_count - 1:
            arrow_id = _id()
            arrow = {
                **_BASE,
                'id': arrow_id,
                'type': 'arrow',
                'x': 850, 'y': cy + 130,
                'width': 1, 'height': 60,
                'points': [[0, 0], [0, 60]],
                'seed': _seed(), 'versionNonce': _seed(), 'updated': _ts(),
                'frameId': outer_frm['id'],
                'boundElements': [],
                'startBinding': {'elementId': card_ids[j], 'gap': 6, 'focus': 0.0},
                'endBinding': {'elementId': card_ids[j+1], 'gap': 6, 'focus': 0.0},
                'startArrowhead': None, 'endArrowhead': 'arrow',
                'strokeColor': '#94a3b8', 'strokeWidth': 1.5, # Elegant light slate arrow
                'roundness': {'type': 2}, 'lastCommittedPoint': None
            }
            all_elements.append(arrow)
            # Register start card binding
            card_rect['boundElements'].append({'id': arrow_id, 'type': 'arrow'})

    # Register arrow end bindings to respective cards
    for el in all_elements:
        if el['type'] == 'arrow':
            target_id = el['endBinding']['elementId']
            # Find target card and append arrow reference
            for el_card in all_elements:
                if el_card['id'] == target_id:
                    el_card['boundElements'].append({'id': el['id'], 'type': 'arrow'})
                    break

    # Build page_meta as pipeline steps to maintain complete React/UI compatibility
    page_meta = []
    for idx, step in enumerate(pipeline_steps):
        page_meta.append({
            'name': step.get('title', '步骤'),
            'route': f"阶段 {idx+1}"
        })

    return {
        'pages':       page_meta,
        'elements':    all_elements,
        'fileCount':   len(files_content),
        'projectType': project_type,
        'notes':       notes,
        'tokens': {
            'input':  _token_log['input'],
            'output': _token_log['output'],
            'total':  _token_log['input'] + _token_log['output'],
            'calls':  _token_log['calls'],
        },
    }
