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

FRONTEND_EXTS  = {'.jsx', '.tsx', '.vue', '.html', '.js', '.ts'}
SKIP_DIRS      = {'node_modules', 'dist', 'build', '.git', '__pycache__',
                  '.next', 'out', '.nuxt', '.vite', '.cache', 'coverage'}
PAGE_DIRS      = {'pages', 'views', 'screens', 'routes', 'app'}
CONFIG_NAMES   = {'package.json', 'requirements.txt', 'pipfile', 'gemfile',
                  'go.mod', 'cargo.toml', 'readme.md', 'readme.rst',
                  'docker-compose.yml', 'pyproject.toml', '.env.example', 'makefile'}

MAX_SELECT_FILES = 25
MAX_FILE_BYTES   = 10_000
CONFIG_MAX_BYTES = 2_000

DEFAULT_HEIGHTS = {
    'navbar': 60, 'header': 60, 'hero': 240, 'sidebar': 400,
    'grid': 280, 'section': 160, 'form': 300, 'table': 320, 'footer': 60,
}
TYPE_COLORS = {
    'navbar':  ('#1e3a5f', '#3b82f6'),
    'header':  ('#1e3a5f', '#3b82f6'),
    'hero':    ('#2d1b69', '#7c3aed'),
    'sidebar': ('#1f2937', '#4b5563'),
    'grid':    ('#1f2937', '#4b5563'),
    'section': ('transparent', '#4b5563'),
    'form':    ('#1a1f2e', '#4b5563'),
    'table':   ('#1a1f2e', '#4b5563'),
    'footer':  ('#374151', '#6b7280'),
}
FLOW_COLORS = {
    'start':    ('#14532d', '#22c55e'),
    'end':      ('#7f1d1d', '#ef4444'),
    'page':     ('#1e3a5f', '#3b82f6'),
    'action':   ('#1f2937', '#6b7280'),
    'decision': ('#451a03', '#f59e0b'),
    'api':      ('#2d1b69', '#7c3aed'),
}
NODE_W, NODE_H      = 180, 48
FLOW_GAP_X, FLOW_GAP_Y = 60, 90


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

def _text(label, x, y, w, h, frame_id=None, container_id=None, size=13):
    eid, ts = _id(), _ts()
    return {**_BASE, 'id': eid, 'type': 'text', 'x': x, 'y': y,
            'width': w, 'height': h, 'seed': _seed(), 'versionNonce': _seed(),
            'updated': ts, 'frameId': frame_id,
            'text': label, 'originalText': label, 'fontSize': size,
            'fontFamily': 1, 'textAlign': 'center', 'verticalAlign': 'middle',
            'lineHeight': 1.25, 'autoResize': True,
            'strokeColor': '#e5e7eb', 'backgroundColor': 'transparent',
            'containerId': container_id}

def _frame(x, y, w, h, name):
    eid, ts = _id(), _ts()
    return {**_BASE, 'id': eid, 'type': 'frame', 'x': x, 'y': y,
            'width': w, 'height': h, 'seed': _seed(), 'versionNonce': _seed(),
            'updated': ts, 'name': name,
            'strokeColor': '#6b7280', 'backgroundColor': 'transparent'}


def _free_text(text, x, y, w, h, frame_id, size=12, color='#e2e8f0',
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


def _rich_element(x, y, w, h, item_type, label, items, frame_id):
    """Render a block: background rect + free-floating label + sub-content.
    IMPORTANT: no containerId on text — Excalidraw would reposition bound text."""
    bg, stroke = TYPE_COLORS.get(item_type, ('#1f2937', '#4b5563'))
    r = _rect(x, y, w, h, frame_id, bg, stroke)
    elements = [r]
    px, py = 10, 7

    # ── Navbar / Header: horizontal bar ──────────────────────
    if item_type in ('navbar', 'header'):
        nav_txt = f"{label}   {'  ·  '.join(str(i) for i in items[:6])}" if items else label
        elements.append(_free_text(nav_txt, x + px, y, w - 2*px, h,
                                   frame_id, 12, '#e2e8f0', 'center', 'middle'))
        return elements

    # ── Footer ───────────────────────────────────────────────
    if item_type == 'footer':
        footer_txt = '  ·  '.join(str(i) for i in items[:4]) if items else label
        elements.append(_free_text(footer_txt, x + px, y, w - 2*px, h,
                                   frame_id, 10, '#9ca3af', 'center', 'middle'))
        return elements

    # ── Content blocks: label chip at top, items below ───────
    label_h = 18
    elements.append(_free_text(label, x + px, y + py, w - 2*px, label_h,
                                frame_id, 11, '#93c5fd', 'left', 'top', font_family=3))

    sub_y = y + py + label_h + 5
    sub_h = max(16, h - py - label_h - 5 - py)

    if item_type == 'sidebar':
        sub_txt = '\n'.join(f'▸ {i}' for i in items[:8])
    elif item_type == 'form':
        sub_txt = '\n'.join(f'[ {i} ]' for i in items[:7])
    elif item_type == 'table':
        cols = items[:5]
        sub_txt = '| ' + ' | '.join(cols) + ' |\n|' + ' --- |' * len(cols)
    elif item_type == 'hero':
        sub_txt = '\n\n'.join(str(i) for i in items[:3])
    else:
        sub_txt = '\n'.join(f'· {i}' for i in items[:7])

    if sub_txt and sub_h > 12:
        elements.append(_free_text(sub_txt, x + px, sub_y, w - 2*px, sub_h,
                                   frame_id, 10, '#d1d5db', 'left', 'top'))
    return elements


# ── Page layout → Excalidraw elements ─────────────────────────

PAGE_W, PAD, GAP = 900, 20, 8

def build_page_elements(page_data, page_index):
    layout   = page_data.get('layout', [])
    start_x  = page_index * (PAGE_W + 80)
    elements = []

    headers  = [i for i in layout if i['type'] in ('navbar', 'header')]
    footers  = [i for i in layout if i['type'] == 'footer']
    sidebars = [i for i in layout if i['type'] == 'sidebar']
    body     = [i for i in layout if i['type'] not in ('navbar', 'header', 'footer', 'sidebar')]

    has_sidebar = bool(sidebars)
    sidebar_w   = (sidebars[0].get('width', 200) + GAP) if has_sidebar else 0

    header_h = sum(i.get('height', DEFAULT_HEIGHTS.get(i['type'], 60)) + GAP  for i in headers)
    footer_h = sum(i.get('height', DEFAULT_HEIGHTS.get(i['type'], 60)) + GAP  for i in footers)
    body_h   = sum(i.get('height', DEFAULT_HEIGHTS.get(i['type'], 120)) + GAP for i in body)
    if has_sidebar:
        body_h = max(body_h, sidebars[0].get('height', DEFAULT_HEIGHTS['sidebar']) + GAP)
    total_h = PAD + header_h + body_h + footer_h + PAD

    frm = _frame(start_x, 0, PAGE_W, total_h,
                 f"{page_data['name']}  {page_data.get('route', '')}")
    fid = frm['id']
    elements.append(frm)

    y = PAD
    for item in headers:
        h     = item.get('height', DEFAULT_HEIGHTS.get(item['type'], 60))
        items = item.get('items', [])
        elements += _rich_element(start_x + PAD, y, PAGE_W - 2*PAD, h, item['type'], item['label'], items, fid)
        y += h + GAP

    body_start_y = y
    if has_sidebar:
        sb    = sidebars[0]
        sb_h  = body_h - GAP
        items = sb.get('items', [])
        elements += _rich_element(start_x + PAD, y, sb['width'], sb_h, 'sidebar', sb['label'], items, fid)

    content_x = start_x + PAD + sidebar_w
    content_w = PAGE_W - 2*PAD - sidebar_w
    y = body_start_y

    for item in body:
        h     = item.get('height', DEFAULT_HEIGHTS.get(item['type'], 120))
        label = item['label']
        items = item.get('items', [])

        if item['type'] == 'grid':
            cols   = max(1, item.get('cols', 3))
            rows   = max(1, item.get('rows', 1))
            card_w = (content_w - (cols-1)*GAP) // cols
            card_h = (h - (rows-1)*GAP) // rows
            bg_g, stroke_g = TYPE_COLORS.get('grid', ('#1f2937', '#6b7280'))
            for row in range(rows):
                for col in range(cols):
                    idx = row * cols + col
                    lbl = items[idx] if idx < len(items) else f"{label} {idx+1}"
                    cx  = content_x + col * (card_w + GAP)
                    cy  = y + row * (card_h + GAP)
                    cr  = _rect(cx, cy, card_w, card_h, fid, bg_g, stroke_g)
                    ct  = _free_text(lbl, cx + 8, cy + 8, card_w - 16, card_h - 16,
                                     fid, 11, '#e2e8f0', 'center', 'middle')
                    elements += [cr, ct]
        else:
            elements += _rich_element(content_x, y, content_w, h, item['type'], label, items, fid)
        y += h + GAP

    y = total_h - PAD - footer_h
    for item in footers:
        h     = item.get('height', DEFAULT_HEIGHTS.get(item['type'], 60))
        items = item.get('items', [])
        elements += _rich_element(start_x + PAD, y, PAGE_W - 2*PAD, h, 'footer', item['label'], items, fid)
        y += h + GAP

    return elements


# ── Flow diagram builder ───────────────────────────────────────

def build_flow_diagram(flow_data, offset_x=0):
    """Render a directed flow graph as Excalidraw arrow + rect elements."""
    nodes = flow_data.get('nodes', [])
    edges = flow_data.get('edges', [])
    title = flow_data.get('title', '运行逻辑流图')
    if not nodes:
        return []

    node_map = {n['id']: n for n in nodes}

    # BFS level assignment from start node
    start_ids = [n['id'] for n in nodes if n.get('type') == 'start'] or [nodes[0]['id']]
    adj = {n['id']: [] for n in nodes}
    for e in edges:
        if e.get('from') in adj:
            adj[e['from']].append(e.get('to', ''))

    levels, visited, queue = {}, set(), [(start_ids[0], 0)]
    while queue:
        nid, lv = queue.pop(0)
        if nid in visited: continue
        visited.add(nid); levels[nid] = lv
        for nxt in adj.get(nid, []):
            if nxt not in visited: queue.append((nxt, lv + 1))

    max_lv = max(levels.values()) if levels else 0
    for n in nodes:
        if n['id'] not in levels: levels[n['id']] = max_lv + 1
    max_lv = max(levels.values())

    level_groups = {}
    for nid, lv in levels.items(): level_groups.setdefault(lv, []).append(nid)
    max_per_row = max(len(v) for v in level_groups.values())

    total_w = max(max_per_row * (NODE_W + FLOW_GAP_X) - FLOW_GAP_X + 80, 400)
    total_h = (max_lv + 1) * (NODE_H + FLOW_GAP_Y) - FLOW_GAP_Y + 100

    frm = _frame(offset_x, 0, total_w, total_h + 20, title)
    fid = frm['id']
    elements = [frm]

    # Barycenter sort: sort each level's nodes by avg x of their parents
    # to minimize edge crossings before assigning screen positions
    rev_adj = {n['id']: [] for n in nodes}
    for e in edges:
        if e.get('to') in rev_adj and e.get('from') in levels:
            rev_adj[e['to']].append(e['from'])

    # Two-pass: assign a temporary column index, then sort by parent barycenters
    col_order = {}  # nid → float sort key
    for lv in sorted(level_groups.keys()):
        nids = level_groups[lv]
        scored = []
        for nid in nids:
            parents = rev_adj.get(nid, [])
            if parents:
                score = sum(col_order.get(p, 0) for p in parents) / len(parents)
            else:
                score = list(node_map.keys()).index(nid)
            scored.append((score, nid))
        scored.sort()
        level_groups[lv] = [nid for _, nid in scored]
        for i, nid in enumerate(level_groups[lv]):
            col_order[nid] = i

    # Compute node screen positions (center of each node)
    node_pos = {}
    for lv, nids in sorted(level_groups.items()):
        count = len(nids)
        row_w = count * NODE_W + (count - 1) * FLOW_GAP_X
        rx = offset_x + (total_w - row_w) / 2
        for i, nid in enumerate(nids):
            nx = rx + i * (NODE_W + FLOW_GAP_X)
            ny = 30 + lv * (NODE_H + FLOW_GAP_Y)
            node_pos[nid] = (nx, ny)

    # Draw nodes — label text bound to rect via containerId so they move together
    rect_map = {}  # nid → rect dict (mutable, shared reference in elements list)
    for n in nodes:
        nid = n['id']
        if nid not in node_pos: continue
        nx, ny = node_pos[nid]
        bg, stroke = FLOW_COLORS.get(n.get('type', 'action'), ('#1f2937', '#6b7280'))
        r = _rect(nx, ny, NODE_W, NODE_H, fid, bg, stroke)
        r['roundness'] = {'type': 3}
        r['boundElements'] = []   # arrows + label text will append here
        # Label text bound to rect: Excalidraw centers it and moves it with rect
        t_eid, ts_n = _id(), _ts()
        t = {**_BASE, 'id': t_eid, 'type': 'text',
             'x': nx, 'y': ny, 'width': NODE_W, 'height': NODE_H,
             'seed': _seed(), 'versionNonce': _seed(), 'updated': ts_n,
             'frameId': fid, 'containerId': r['id'],
             'text': n.get('label', nid), 'originalText': n.get('label', nid),
             'fontSize': 12, 'fontFamily': 1,
             'textAlign': 'center', 'verticalAlign': 'middle',
             'lineHeight': 1.25, 'autoResize': True,
             'strokeColor': '#e2e8f0', 'backgroundColor': 'transparent',
             'boundElements': None}
        r['boundElements'].append({'id': t_eid, 'type': 'text'})
        elements += [r, t]
        rect_map[nid] = r

    # Draw arrows with start/end bindings so dragging nodes pulls arrows along
    ts_now = _ts()
    for e in edges:
        f_id, t_id = e.get('from', ''), e.get('to', '')
        if f_id not in node_pos or t_id not in node_pos: continue
        fx, fy = node_pos[f_id]
        tx, ty = node_pos[t_id]
        ax, ay = fx + NODE_W / 2, fy + NODE_H   # bottom-center of source
        ex, ey = tx + NODE_W / 2, ty             # top-center of target
        dx, dy = ex - ax, ey - ay
        src_r = rect_map.get(f_id)
        dst_r = rect_map.get(t_id)
        arrow_eid = _id()
        arrow = {**_BASE,
                 'id': arrow_eid, 'type': 'arrow',
                 'x': ax, 'y': ay, 'width': abs(dx) or 1, 'height': abs(dy) or 1,
                 'points': [[0, 0], [dx, dy]],
                 'seed': _seed(), 'versionNonce': _seed(), 'updated': ts_now,
                 'frameId': fid, 'boundElements': [],
                 'startBinding': {'elementId': src_r['id'], 'gap': 6, 'focus': 0.0} if src_r else None,
                 'endBinding':   {'elementId': dst_r['id'], 'gap': 6, 'focus': 0.0} if dst_r else None,
                 'startArrowhead': None, 'endArrowhead': 'arrow',
                 'strokeColor': '#6b7280', 'strokeWidth': 1.5,
                 'roundness': {'type': 2}, 'lastCommittedPoint': None}
        elements.append(arrow)
        # Register arrow into both endpoint rects so Excalidraw tracks the binding
        if src_r: src_r['boundElements'].append({'id': arrow_eid, 'type': 'arrow'})
        if dst_r: dst_r['boundElements'].append({'id': arrow_eid, 'type': 'arrow'})
        # Edge labels skipped — Excalidraw doesn't reposition containerId text when
        # an arrow is passively recomputed from node movement, only on direct drag.
        # Users can double-click any arrow to add a label manually.

    return elements


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


# ── Phase 4: Wireframe generation ────────────────────────────

WIREFRAME_SYSTEM = """你是 UI/UX 线框图专家。根据代码文件精确提取 UI 结构，每个页面必须生成能真实反映该页面功能的不同布局。

只返回合法 JSON，不要 markdown 代码块，不要解释：
{
  "pages": [
    {
      "name": "页面真实名称（从代码路由/组件名取）",
      "route": "/真实路由",
      "layout": [
        {"type": "navbar",  "label": "项目品牌名", "height": 56,  "items": ["品牌/Logo", "真实菜单项1", "真实菜单项2", "登录/操作按钮"]},
        {"type": "sidebar", "label": "侧边导航",   "width": 200, "height": 500, "items": ["菜单项1", "菜单项2", "菜单项3", "设置"]},
        {"type": "table",   "label": "真实数据表名", "height": 340, "items": ["从Model/API取的真实列1", "列2", "列3", "操作"]},
        {"type": "footer",  "label": "页脚",       "height": 48,  "items": ["版权", "文档链接", "GitHub"]}
      ]
    }
  ]
}

关键规则（违反则线框图无意义）：
1. label 和 items 100% 来自代码 —— 路由名、组件名、Model字段、API字段、菜单文字
2. 绝对禁止写"内容区""主区域""Main Content""示例""占位""内容1"等通用词
3. 每个页面的 layout 必须反映该页面的真实功能，不同页面 layout 结构要有差异
4. 根据页面功能选择正确的 type：
   - 有数据列表 → table（items=真实列名）
   - 有卡片/网格展示 → grid（items=每张卡片的真实名称，数量=cols×rows）
   - 有输入/提交 → form（items=真实字段名，最后一项是提交按钮）
   - 有侧边菜单 → sidebar（items=真实菜单项）
   - 有Hero横幅 → hero（items=主标题、副标题、CTA文字）
   - 普通内容区 → section（items=该区块的3-5个真实内容要点）
5. 从后端路由文件推断有哪些页面；从Model/Schema推断字段和列名
6. 最多6个页面；每页layout必须包含3-7个块（不能只有navbar+section+footer）
7. 有后端API的页面优先选用 table/form；纯展示页面选用 hero/grid/section"""


def analyze_with_context(files_dict, project_type, notes):
    files_text = '\n\n'.join(
        f'=== {path} ===\n{content}' for path, content in files_dict.items()
    )
    user_content = f'项目类型：{project_type}\n项目说明：{notes}\n\n代码文件：\n{files_text}'
    raw = _call_ai(WIREFRAME_SYSTEM, user_content, max_tokens=3500)
    return _parse_json(raw)


FLOW_SYSTEM = """你是 UX 流程分析专家。根据代码分析真实的用户操作流程，生成运行逻辑图。

只返回合法 JSON，不要 markdown 代码块，不要解释：
{
  "title": "项目名 运行逻辑",
  "nodes": [
    {"id": "n1", "label": "打开应用", "type": "start"},
    {"id": "n2", "label": "加载项目列表", "type": "action"},
    {"id": "n3", "label": "选择功能Tab", "type": "decision"},
    {"id": "n4", "label": "需求画板", "type": "page"},
    {"id": "n5", "label": "POST /api/generate_spec", "type": "api"},
    {"id": "n6", "label": "保存成功", "type": "end"}
  ],
  "edges": [
    {"from": "n1", "to": "n2", "label": ""},
    {"from": "n2", "to": "n3", "label": "加载完成"},
    {"from": "n3", "to": "n4", "label": "点击Tab"},
    {"from": "n4", "to": "n5", "label": "点击生成"},
    {"from": "n5", "to": "n6", "label": "返回结果"}
  ]
}

节点类型（严格按功能选）：
- start: 用户进入入口（每图只有1个）
- end: 流程终点（可多个，如：保存成功、退出）
- page: 用户可见的页面/视图/弹窗
- action: 用户操作或系统动作（点击按钮、自动保存、数据处理）
- decision: 条件判断/分支（必须有2条以上出边，label写判断条件）
- api: 后端API调用（label写 HTTP方法+路径，如 POST /api/save）

规则：
- label 必须来自真实代码（路由名、函数名、API路径、组件名、按钮文字）
- 最多18个节点，最多22条边
- decision 节点必须有 ≥2 条出边；边的 label 留空（""），分支条件写在目标节点的 label 里
- 覆盖核心用户流程：从打开应用 → 主要操作 → 结果
- 不要画所有细节，聚焦最重要的交互路径"""


def analyze_flow(files_dict, project_type, notes, pages):
    files_text = '\n\n'.join(
        f'=== {path} ===\n{content[:2500]}' for path, content in list(files_dict.items())[:12]
    )
    pages_text = ', '.join(p['name'] for p in pages)
    user_content = (f'项目类型：{project_type}\n项目说明：{notes}\n'
                    f'已识别页面：{pages_text}\n\n代码：\n{files_text}')
    raw = _call_ai(FLOW_SYSTEM, user_content, max_tokens=1500)
    return _parse_json(raw)


# ── Fallback heuristic selector ───────────────────────────────

def _heuristic_select(all_paths):
    candidates = [p for p in all_paths if os.path.splitext(p)[1] in FRONTEND_EXTS]
    candidates.sort(key=lambda p: (
        0 if any(d in p.split('/') for d in PAGE_DIRS) else
        1 if any(k in p.lower() for k in ('index', 'app', 'router', 'main', 'layout')) else 2
    ))
    return candidates[:MAX_SELECT_FILES]


# ── Main entry ────────────────────────────────────────────────

def generate_wireframe(source_type, source_path):
    """
    Three-phase analysis:
      1. Doctor  — read file tree + config → understand project type
      2. Select  — smart file selection (frontend + backend) based on doctor output
      3. Generate — wireframe from curated files
    """

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

    # Validate: doctor sometimes hallucinates paths — only keep real ones
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

    # ── Phase 5: Generate wireframe ─────────────────────────
    layout_data = analyze_with_context(files_content, project_type, notes)
    pages       = layout_data.get('pages', [])

    all_elements = []
    page_meta    = []
    for i, page in enumerate(pages):
        all_elements.extend(build_page_elements(page, i))
        page_meta.append({'name': page['name'], 'route': page.get('route', '')})

    # ── Phase 6: Flow diagram ────────────────────────────────
    flow_offset = len(pages) * (PAGE_W + 80)
    try:
        flow_data     = analyze_flow(files_content, project_type, notes, page_meta)
        flow_elements = build_flow_diagram(flow_data, offset_x=flow_offset)
        all_elements.extend(flow_elements)
    except Exception:
        pass  # flow diagram is best-effort; don't fail the whole request

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
