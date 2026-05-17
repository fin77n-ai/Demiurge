import os
import json
import urllib.request
import urllib.error
import ssl


CARD_TYPE_LABELS = {
    'feature': '功能点',
    'ui': '界面/交互',
    'data': '数据结构',
    'constraint': '约束条件',
    'flow': '用户路径',
}


def generate_spec(cards: list, project_name: str = 'Untitled') -> str:
    """Convert a list of requirement cards into a structured Markdown spec."""
    if not cards:
        return "# 暂无需求卡片\n\n请在左侧画板添加卡片后点击生成。"

    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _local_spec(cards, project_name)

    # Try AI generation
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _claude_spec(cards, project_name, os.environ["ANTHROPIC_API_KEY"])
    return _deepseek_spec(cards, project_name, os.environ["DEEPSEEK_API_KEY"])


def _local_spec(cards: list, project_name: str) -> str:
    """Fallback: generate spec from cards without AI."""
    groups: dict = {}
    for card in cards:
        t = card.get('type', 'feature')
        groups.setdefault(t, []).append(card)

    lines = [f"# {project_name} — Spec", ""]

    order = ['flow', 'feature', 'ui', 'data', 'constraint']
    for t in order:
        if t not in groups:
            continue
        lines.append(f"## {CARD_TYPE_LABELS.get(t, t)}")
        for card in groups[t]:
            title = card.get('title', '(无标题)')
            desc = card.get('desc', '').strip()
            lines.append(f"- **{title}**" + (f"：{desc}" if desc else ""))
        lines.append("")

    lines += [
        "---",
        "_由 Demiurge 生成（本地模式，未调用 AI）_",
        "_设置 ANTHROPIC_API_KEY 或 DEEPSEEK_API_KEY 可启用 AI 结构化_",
    ]
    return "\n".join(lines)


def _claude_spec(cards: list, project_name: str, api_key: str) -> str:
    card_text = "\n".join(
        f"[{c.get('type','feature')}] {c.get('title','')}：{c.get('desc','')}"
        for c in cards
    )
    prompt = f"""你是一个产品经理助手。根据以下需求卡片，生成一份简洁、结构清晰的 Markdown spec，供 AI 执行模型（Claude/Gemini）直接阅读并开始实现。

项目名称：{project_name}

需求卡片：
{card_text}

输出格式要求：
- 使用中文
- 包含：## 项目目标、## 用户路径、## 功能列表、## 数据结构、## 约束与边界
- 每节简洁，不超过 10 行
- 不要写废话，直接写关键点
"""
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            result = json.loads(resp.read())
            return result['content'][0]['text']
    except Exception as e:
        return _local_spec(cards, project_name) + f"\n\n_AI 调用失败：{e}_"


def import_cards(text: str) -> list:
    """Parse free-form document text into requirement cards using AI, or fall back to local parsing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if api_key and os.environ.get("ANTHROPIC_API_KEY"):
        return _claude_import(text, os.environ["ANTHROPIC_API_KEY"])
    if api_key and os.environ.get("DEEPSEEK_API_KEY"):
        return _deepseek_import(text, os.environ["DEEPSEEK_API_KEY"])
    return _local_import(text)


def _local_import(text: str) -> list:
    cards = []
    for line in text.splitlines():
        line = line.strip().lstrip('-*#').strip()
        if len(line) > 4:
            cards.append({'type': 'feature', 'title': line[:60], 'desc': ''})
    return cards[:20]


def _claude_import(text: str, api_key: str) -> list:
    prompt = f"""将以下文档内容拆解为需求卡片列表，以 JSON 数组返回，每个卡片包含：
- type: "feature" | "ui" | "data" | "flow" | "constraint"
- title: 简短标题（20字以内）
- desc: 一句话描述（50字以内，可为空字符串）

只输出 JSON 数组，不要其他内容。最多 15 张卡片。

文档内容：
{text[:3000]}
"""
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            result = json.loads(resp.read())
            raw = result['content'][0]['text'].strip()
            # Strip markdown code fences if present
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            return json.loads(raw)
    except Exception:
        return _local_import(text)


def _deepseek_import(text: str, api_key: str) -> list:
    prompt = f"""将以下文档拆解为需求卡片 JSON 数组，每项有 type/title/desc 字段，type 取值为 feature/ui/data/flow/constraint。只输出 JSON 数组，最多 15 条。

{text[:3000]}"""

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            result = json.loads(resp.read())
            raw = result['choices'][0]['message']['content'].strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            return json.loads(raw)
    except Exception:
        return _local_import(text)


def _deepseek_spec(cards: list, project_name: str, api_key: str) -> str:
    card_text = "\n".join(
        f"[{c.get('type','feature')}] {c.get('title','')}：{c.get('desc','')}"
        for c in cards
    )
    prompt = f"""根据以下需求卡片，生成一份简洁的 Markdown spec，供 AI 执行模型直接阅读实现。

项目名称：{project_name}
需求卡片：
{card_text}

包含：## 项目目标、## 用户路径、## 功能列表、## 数据结构、## 约束与边界。简洁，每节不超过 10 行。"""

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    )
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            result = json.loads(resp.read())
            return result['choices'][0]['message']['content']
    except Exception as e:
        return _local_spec(cards, project_name) + f"\n\n_AI 调用失败：{e}_"
