import sys
import os
import re
import json
import shutil
import threading
import webbrowser
import http.server
import socketserver
import urllib.parse
import socket
import time

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
SAVES_DIR = os.path.join(BASE_DIR, 'saves')

sys.path.insert(0, BASE_DIR)
from ai.spec_generator import generate_spec


# ─── helpers ────────────────────────────────────────────
def ensure_saves_dir():
    os.makedirs(SAVES_DIR, exist_ok=True)
    # migrate old board_state.json → saves/default.json
    old = os.path.join(BASE_DIR, 'board_state.json')
    new = os.path.join(SAVES_DIR, 'default.json')
    if os.path.exists(old) and not os.path.exists(new):
        shutil.move(old, new)


def slugify(name: str) -> str:
    s = re.sub(r'[^\w\s-]', '', name.strip().lower())
    s = re.sub(r'[\s_-]+', '-', s)
    return s.strip('-') or 'project'


def unique_slug(name: str) -> str:
    base = slugify(name)
    slug, i = base, 2
    while os.path.exists(os.path.join(SAVES_DIR, slug + '.json')):
        slug = f'{base}-{i}'; i += 1
    return slug


def safe_slug(raw: str) -> str:
    return re.sub(r'[^a-z0-9\-_]', '', str(raw))[:64] or 'default'


def list_projects() -> list:
    ensure_saves_dir()
    projects = []
    for fn in os.listdir(SAVES_DIR):
        if not fn.endswith('.json'):
            continue
        slug  = fn[:-5]
        fpath = os.path.join(SAVES_DIR, fn)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                name = json.load(f).get('projectName', slug)
        except Exception:
            name = slug
        projects.append({'slug': slug, 'name': name, 'mtime': os.path.getmtime(fpath)})
    projects.sort(key=lambda x: -x['mtime'])
    return projects


# ─── HTTP handler ───────────────────────────────────────
class DemiurgeHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        p = self.path

        if p in ('/', '/index.html'):
            self._serve_file(os.path.join(BASE_DIR, 'ui', 'index.html'), 'text/html')
            return

        if p.startswith('/ui/'):
            self._serve_file(os.path.join(BASE_DIR, p[1:]), self._mime(p))
            return

        if p == '/api/projects':
            self._json_response(json.dumps(list_projects()))
            return

        if p.startswith('/api/projects/load'):
            qs   = urllib.parse.parse_qs(urllib.parse.urlparse(p).query)
            slug = safe_slug(qs.get('slug', ['default'])[0])
            fpath = os.path.join(SAVES_DIR, slug + '.json')
            if os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = f.read()
            else:
                data = json.dumps({'cards': [], 'wfElements': [], 'wfNextId': 1,
                                   'projectName': slug})
            self._json_response(data)
            return

        # legacy load
        if p == '/api/load':
            ensure_saves_dir()
            fpath = os.path.join(SAVES_DIR, 'default.json')
            data = open(fpath, 'r', encoding='utf-8').read() if os.path.exists(fpath) \
                   else json.dumps({'cards': []})
            self._json_response(data)
            return

        self.send_response(404); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)
        p      = self.path

        if p == '/api/projects/save':
            ensure_saves_dir()
            payload = json.loads(body)
            slug    = safe_slug(payload.get('slug', 'default'))
            fpath   = os.path.join(SAVES_DIR, slug + '.json')
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            self._json_response('{"ok":true}')
            return

        if p == '/api/projects/create':
            ensure_saves_dir()
            payload = json.loads(body)
            name    = str(payload.get('name', 'New Project'))[:80]
            slug    = unique_slug(name)
            fpath   = os.path.join(SAVES_DIR, slug + '.json')
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump({'projectName': name, 'cards': [], 'wfElements': [],
                           'wfNextId': 1}, f, ensure_ascii=False, indent=2)
            self._json_response(json.dumps({'slug': slug, 'name': name}))
            return

        if p == '/api/projects/delete':
            ensure_saves_dir()
            slug  = safe_slug(json.loads(body).get('slug', ''))
            fpath = os.path.join(SAVES_DIR, slug + '.json')
            if slug and os.path.exists(fpath):
                os.remove(fpath)
            self._json_response('{"ok":true}')
            return

        if p == '/api/projects/rename':
            ensure_saves_dir()
            payload = json.loads(body)
            slug    = safe_slug(payload.get('slug', ''))
            name    = str(payload.get('name', ''))[:80]
            fpath   = os.path.join(SAVES_DIR, slug + '.json')
            if slug and name and os.path.exists(fpath):
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['projectName'] = name
                with open(fpath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            self._json_response('{"ok":true}')
            return

        # legacy save → default project
        if p == '/api/save':
            ensure_saves_dir()
            fpath = os.path.join(SAVES_DIR, 'default.json')
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(body.decode('utf-8'))
            self._json_response('{"ok":true}')
            return

        if p == '/api/generate_spec':
            payload      = json.loads(body)
            spec_md      = generate_spec(payload.get('cards', []),
                                         payload.get('projectName', 'Untitled'))
            self._json_response(json.dumps({'spec': spec_md}))
            return

        self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _serve_file(self, path, mime):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404); self.end_headers()

    def _json_response(self, data):
        encoded = data.encode('utf-8') if isinstance(data, str) else data
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(encoded)

    def _mime(self, path):
        if path.endswith('.js'):  return 'application/javascript'
        if path.endswith('.css'): return 'text/css'
        if path.endswith('.html'): return 'text/html'
        return 'text/plain'

    def log_message(self, format, *args):
        pass


def find_free_port(start=7070):
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port)); return port
            except OSError:
                continue
    return start


def main():
    ensure_saves_dir()
    # seed a default project if saves/ is empty
    if not os.listdir(SAVES_DIR):
        fpath = os.path.join(SAVES_DIR, 'default.json')
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump({'projectName': 'My Project', 'cards': [],
                       'wfElements': [], 'wfNextId': 1}, f, indent=2)

    port   = find_free_port()
    server = socketserver.TCPServer(('', port), DemiurgeHandler)
    server.allow_reuse_address = True

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    print(f'⚗️  Demiurge — http://localhost:{port}')
    webbrowser.open(f'http://localhost:{port}')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n👋 Demiurge 退出。')
        sys.exit(0)


if __name__ == '__main__':
    main()
