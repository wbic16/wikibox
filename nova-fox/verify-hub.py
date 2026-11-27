#!/usr/bin/env python3
"""WIKI-1 hub driver v2: correct file switching via /api/open; locked-gate
verification with a throwaway provider pair (hub-only test scaffolding)."""
import json, os, re, subprocess, sys, time, urllib.request, urllib.error, http.cookiejar

BASE = "http://127.0.0.1:18082"
ROOT = "/home/wbic16/nova-fox-wiki"
BIN = f"{ROOT}/bin/phext-edit"
DATA = f"{ROOT}/data"
EE = sys.argv[1] if len(sys.argv) > 1 else "1139"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def req(method, path, body=None, headers=None, raw=False):
    h = dict(headers or {})
    data = body
    if isinstance(body, (dict, list)):
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    elif isinstance(body, str):
        data = body.encode()
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with opener.open(r, timeout=15) as resp:
            b = resp.read()
            return resp.status, (b if raw else b.decode("utf-8", "replace")), resp.headers
    except urllib.error.HTTPError as e:
        b = e.read()
        return e.code, (b if raw else b.decode("utf-8", "replace")), e.headers

def wait_up():
    for _ in range(60):
        try:
            req("GET", "/api/wiki/status")
            return True
        except Exception:
            time.sleep(0.5)
    return False

def start(args, env=None, log="server.log"):
    e = dict(os.environ)
    if env:
        e.update(env)
    lf = open(f"{ROOT}/{log}", "wb")
    p = subprocess.Popen([BIN] + args, stdout=lf, stderr=lf, env=e, cwd=ROOT)
    ok = wait_up()
    print("server up:", ok, "pid", p.pid)
    return p

def stop(p):
    p.terminate()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""))

def okj(body):
    return '"ok":true' in body.replace(" ", "")

# ---------- Phase 1: --local write path, correct file switching ----------
srv = start(["--local", "--dir", DATA, "--home", "wiki.phext",
             "--home-coord", "1.1.1/1.1.1/1.1.1", "--port", "18082"], log="local2.log")
s, body, _ = req("GET", "/api/session")
csrf = json.loads(body).get("csrf", "")
H = {"x-csrf-token": csrf} if csrf else {}
s, body, _ = req("GET", "/api/status")
check("local: open file is wiki.phext", "wiki.phext" in str(json.loads(body).get("file", "")), body[:90])

img = open(f"{ROOT}/nova-fox-heart.jpg", "rb").read()
s, body, _ = req("POST", "/api/images", body=img, headers={**H, "Content-Type": "image/jpeg"})
up = json.loads(body)
ref = up.get("reference", "")
check("local: image stored at 9.9.9/9.9.9/1.1.1", s == 200 and up.get("coordinate") == "9.9.9/9.9.9/1.1.1", body[:140])

s, body, _ = req("GET", "/api/scroll/1.1.1/1.1.1/1.1.1")
front = json.loads(body).get("content", "")
if ref and ref not in front:
    marker = "    ╲╱\n"
    newfront = front.replace(marker, marker + f"\n![The Nova Fox heart — braided light, from exo-dreams]({ref})\n", 1)
    s, body, _ = req("POST", "/api/update", {"coordinate": "1.1.1/1.1.1/1.1.1", "content": newfront}, headers=H)
    check("local: front scroll updated with heart", okj(body), body[:100])
    s, body, _ = req("POST", "/api/save", "", headers=H)
    check("local: wiki saved", okj(body), body[:100])

# switch to the feedback book through the editor's own open route
s, body, _ = req("POST", "/api/open", f"{DATA}/feedback.phext", headers={**H, "Content-Type": "text/plain"})
print("open feedback:", s, body[:140])
s, body, _ = req("GET", "/api/status")
check("local: open file is feedback.phext", "feedback.phext" in str(json.loads(body).get("file", "")), body[:90])
test_entry = (f"TEST · fox wiki-ee{EE} · WIKI-1 verification entry\n\n"
              "TEST entry — written through the editor's own write path on the hub "
              "instance (local mode, the signed-in equivalent) to prove the feedback "
              "intake round-trips before launch. This is a test entry, not player "
              "feedback. If you are reading this in the book, the door works.\n")
s, body, _ = req("POST", "/api/update", {"coordinate": "1.1.1/1.1.2/1.1.1", "content": test_entry}, headers=H)
check("local: TEST feedback entry written", okj(body), body[:100])
s, body, _ = req("POST", "/api/save", "", headers=H)
check("local: feedback saved", okj(body), body[:100])
s, body, _ = req("GET", "/api/scroll/1.1.1/1.1.2/1.1.1")
check("local: TEST entry reads back via API", json.loads(body).get("content", "") == test_entry, "")
stop(srv)

# disk verification
LEVEL_BYTES = [0x01, 0x1F, 0x1E, 0x1D, 0x1C, 0x1A, 0x19, 0x18, 0x17]
B2D = {b: i for i, b in enumerate(LEVEL_BYTES)}
def fmt(c): return f"{c[0]}.{c[1]}.{c[2]}/{c[3]}.{c[4]}.{c[5]}/{c[6]}.{c[7]}.{c[8]}"
def explode(data):
    scrolls, state, buf = {}, [1]*9, bytearray()
    for b in data:
        d = B2D.get(b)
        if d is None: buf.append(b)
        else:
            if buf: scrolls[fmt(tuple(state))] = buf.decode("utf-8", "replace"); buf = bytearray()
            state[d] += 1
            for j in range(d+1, 9): state[j] = 1
    if buf: scrolls[fmt(tuple(state))] = buf.decode("utf-8", "replace")
    return scrolls
fb = explode(open(f"{DATA}/feedback.phext", "rb").read())
wk = explode(open(f"{DATA}/wiki.phext", "rb").read())
check("disk: TEST entry in feedback.phext", fb.get("1.1.1/1.1.2/1.1.1", "").startswith("TEST ·"), str(list(fb)))
check("disk: ship log intact in wiki.phext", wk.get("1.1.1/1.1.2/1.1.1", "").startswith("# Ship Log"), wk.get("1.1.1/1.1.2/1.1.1", "")[:40])
check("disk: no TEST text in wiki.phext", all("WIKI-1 verification" not in v for v in wk.values()), "")
check("disk: media scrolls present", "9.9.9/9.9.9/1.1.1" in wk and "9.9.9/9.9.9/1.2.1" in wk, f"{len(wk)} scrolls")

# ---------- Phase 2: locked production-shaped gates ----------
secret = subprocess.run(["head", "-c", "32", "/dev/urandom"], capture_output=True).stdout.hex()
env = {"PHEXT_SESSION_SECRET": secret,
       "PHEXT_PUBLIC_URL": "https://fox.phext.io",
       "GITHUB_CLIENT_ID": "wiki1-hub-test-scaffolding",
       "GITHUB_CLIENT_SECRET": "wiki1-hub-test-scaffolding-not-a-real-secret"}
srv = start(["--dir", DATA, "--home", "wiki.phext", "--home-coord", "1.1.1/1.1.1/1.1.1",
             "--host", "127.0.0.1", "--port", "18082"], env=env, log="prod2.log")
cj.clear()
s, body, _ = req("GET", "/wiki/")
check("pub: /wiki/ shell 200 signed-out", s == 200, f"status {s}")
check("pub: shell is dark-themed", ("--text: #dedede" in body) or ("#101010" in body), "")
s, body, _ = req("GET", "/api/wiki/status")
wst = json.loads(body) if s == 200 else {}
check("pub: /api/wiki/status", s == 200 and wst.get("scrolls", 0) == len(wk), str(wst))
s, body, _ = req("GET", "/api/wiki/nav?at=1.1.1/1.1.1/1.1.1")
check("pub: front page via catalog (EE stamp)", "Nova Fox Wiki" in body and f"EE {EE}" in body, "")
s, body, _ = req("GET", "/api/wiki/nav?at=1.1.1/1.1.2/1.1.1")
check("pub: ship log page via catalog", "Ship Log" in body and "EE 1081" in body, "")
s, body, _ = req("GET", "/api/wiki/nav?at=1.1.1/1.1.3/1.1.1")
check("pub: feedback page via catalog", "Feedback" in body and "feedback door" in body, "")
s, body, _ = req("GET", "/api/wiki/search?q=Novakor")
check("pub: search finds Novakor", "Novakor" in body, "")
s, body, hdrs = req("GET", "/api/wiki/media/9.9.9/9.9.9/1.1.1", raw=True)
check("pub: heart media serves (jpeg bytes)", s == 200 and isinstance(body, bytes) and body[:2] == b"\xff\xd8" and len(body) == len(img), f"status {s}")
s, body, _ = req("POST", "/api/wiki/nav", {"x": 1})
check("pub: catalog write refused (405)", s == 405, f"status {s}")
s, body, _ = req("GET", "/api/scroll/1.1.1/1.1.1/1.1.1")
check("pub: editor scroll API 401 signed-out", s == 401, f"status {s} {body[:80]}")
s, body, _ = req("POST", "/api/update", {"coordinate": "1.1.1/1.1.1/1.1.1", "content": "vandal"})
check("pub: editor write 401 signed-out", s == 401, f"status {s} {body[:80]}")
s, body, _ = req("POST", "/api/open", f"{DATA}/feedback.phext")
check("pub: editor open 401 signed-out", s == 401, f"status {s}")
s, body, _ = req("GET", "/api/wiki/nav?at=1.1.1/1.1.1/1.1.1")
check("pub: front page intact after write attempts", "Nova Fox Wiki" in body and "vandal" not in body, "")
s, body, hdrs = req("GET", "/api/auth/github")
loc = hdrs.get("Location", "") if hdrs else ""
check("pub: sign-in starts OAuth (302 to github)", s == 302 and "github.com" in loc, f"status {s} loc {loc[:80]}")
s, body, _ = req("GET", "/api/session")
sj = json.loads(body)
check("pub: session signed-out, providers listed", sj.get("signed_in") is False and "github" in str(sj.get("providers")), body[:140])
stop(srv)

fails = [r for r in results if not r[1]]
print(f"\n==== {len(results) - len(fails)}/{len(results)} checks passed ====")
if fails:
    for n, _ in fails: print("FAILED:", n)
    sys.exit(1)
