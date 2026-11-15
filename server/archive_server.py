#!/usr/bin/env python3
"""Archive server: like `python -m http.server 8000`, plus a small ratings / readable-image API.

GET  /api/ratings  -> full ratings.json
POST /api/ratings  -> {"id": "...", "r": 0-3, "n": "Notiz", "ts": "ISO"}  (r=0 and empty note = delete entry)

Stores to ratings.json next to this script (atomic write, with ratings.json.bak backup).
"""
import json, os, sys, threading, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
try:
    from PIL import Image  # optional: without Pillow the original image is served
except Exception:
    Image = None

ROOT = os.path.dirname(os.path.abspath(__file__))
RATINGS = os.path.join(ROOT, "ratings.json")
LOCK = threading.Lock()
MAX_BODY = 64 * 1024
HQFILE = os.path.join(ROOT, "hq_settings.json")   # {thread-id: {"5": true/false, ...}} - which screenshots are shown large
HQDIR = os.path.join(ROOT, "_thumbnails_hq")      # cache: 900 px wide versions generated from the originals
HQ_WIDTH = 900
FOLDERS = {"AI", "AI for UXR", "Legal AI", "Public Sector", "Research"}


def load():
    try:
        with open(RATINGS, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save(data):
    tmp = RATINGS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    if os.path.exists(RATINGS):
        try:
            os.replace(RATINGS, RATINGS + ".bak")
        except OSError:
            pass
    os.replace(tmp, RATINGS)


def load_hq():
    try:
        with open(HQFILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_hq(data):
    tmp = HQFILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, HQFILE)


def find_original(folder, stem, i):
    for sep in (" - ", "_"):
        for ext in ("jpg", "jpeg", "png", "JPG", "JPEG", "PNG"):
            p = os.path.join(ROOT, folder, f"{stem}{sep}{i}.{ext}")
            if os.path.isfile(p):
                return p
    return None


def hq_image(folder, stem, i):
    """Path of the 900 px version (created on first request) or None."""
    if folder not in FOLDERS or not str(i).isdigit() or any(c in stem for c in "/\\") or ".." in stem:
        return None
    orig = find_original(folder, stem, i)
    if not orig:
        return None
    if Image is None:
        return orig
    out = os.path.join(HQDIR, folder, f"{stem} - {i}.jpg")
    if not os.path.isfile(out) or os.path.getmtime(out) < os.path.getmtime(orig):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im = Image.open(orig).convert("RGB")
        w, h = im.size
        if w > HQ_WIDTH:
            im = im.resize((HQ_WIDTH, max(1, int(h * HQ_WIDTH / w))), Image.LANCZOS)
        tmp = out + ".tmp"
        im.save(tmp, format="JPEG", quality=85, optimize=True)
        os.replace(tmp, out)
    return out


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/ratings":
            with LOCK:
                return self._json(200, load())
        if path == "/api/hq":
            with LOCK:
                return self._json(200, load_hq())
        if path == "/api/hqimg":
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            try:
                f = hq_image(q["folder"][0], q["stem"][0], q["i"][0])
            except Exception as e:
                print("hqimg error:", e)
                f = None
            if not f:
                return self._json(404, {"error": "not found"})
            with open(f, "rb") as fh:
                body = fh.read()
            ctype = "image/png" if f.lower().endswith(".png") else "image/jpeg"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] == "/api/hq":
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if n <= 0 or n > MAX_BODY:
                    return self._json(413, {"error": "bad size"})
                p = json.loads(self.rfile.read(n).decode("utf-8"))
                tid, i, on = str(p["id"]), str(int(p["i"])), bool(p["on"])
            except Exception as e:
                return self._json(400, {"error": str(e)})
            with LOCK:
                data = load_hq()
                data.setdefault(tid, {})[i] = on
                save_hq(data)
            return self._json(200, {"ok": True})
        if self.path.split("?")[0] != "/api/ratings":
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n <= 0 or n > MAX_BODY:
                return self._json(413, {"error": "bad size"})
            p = json.loads(self.rfile.read(n).decode("utf-8"))
            tid = str(p["id"])
            r = int(p.get("r", 0))
            note = str(p.get("n", ""))[:500]
            ts = str(p.get("ts", ""))[:40]
            if r not in (0, 1, 2, 3):
                return self._json(400, {"error": "r must be 0-3"})
        except Exception as e:
            return self._json(400, {"error": str(e)})
        with LOCK:
            data = load()
            if r == 0 and not note.strip():
                data.pop(tid, None)
            else:
                data[tid] = {"r": r, "n": note, "ts": ts}
            save(data)
        return self._json(200, {"ok": True, "count": len(data)})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Archive server with ratings API: http://localhost:{port}/archive_browser.html")
    print(f"Ratings file: {RATINGS}")
    print("Readable toggle: Pillow " + ("available" if Image else "MISSING (pip install pillow) - originals are served"))
    ThreadingHTTPServer(("", port), Handler).serve_forever()
