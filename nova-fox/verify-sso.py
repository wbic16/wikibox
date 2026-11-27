#!/usr/bin/env python3
"""WIKI-2 hub driver: the wiki as a phext.tech SSO consumer.

Two instances of the same build, hub-only test scaffolding:
  consumer  127.0.0.1:18082 — the wiki instance shape (audience
            novafoxwiki, provider pointed at the test provider,
            the shared test SSO secret).
  provider  127.0.0.1:18083 — a test phext.tech (throwaway
            provider keys, the novafoxwiki arm aimed back at the
            consumer, the agent mint armed with a test secret so
            assertions can be minted without a browser session).

The round trip is the real one: mint -> consumer callback ->
sealed session -> a TEST feedback entry written through the
editor's own write path under the SSO identity, read back, and
verified on disk. Replay, foreign-audience, and tampered
assertions are refused. A third, unconfigured instance shows
the fail-closed fact the launch package is built on: with no
sign-in configured the editor is unlocked, which is why the
write leg stays unproxied until the SSO lines land.
"""
import base64, hashlib, hmac, http.client, json, os, re, shutil, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.environ.get("WIKI2_ROOT", "/home/wbic16/nova-fox-wiki")
BIN = os.environ.get("WIKI2_BIN", f"{ROOT}/bin/phext-edit")
DATA = f"{ROOT}/data"
EE = sys.argv[1] if len(sys.argv) > 1 else "1155"
CPORT, PPORT = 18082, 18083
CBASE, PBASE = f"http://127.0.0.1:{CPORT}", f"http://127.0.0.1:{PPORT}"

SSO_SECRET = "wiki2-hub-test-sso-secret-0123456789"
AGENT_SECRET = "wiki2-hub-agent-emise-secret-0123456"

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""))

def okj(body):
    return '"ok":true' in body.replace(" ", "")

# redirect-following opener for the public-surface checks
opener = urllib.request.build_opener()
def req(method, path, body=None, headers=None, base=CBASE):
    h = dict(headers or {})
    data = body
    if isinstance(body, (dict, list)):
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    elif isinstance(body, str):
        data = body.encode()
    r = urllib.request.Request(base + path, data=data, method=method, headers=h)
    try:
        with opener.open(r, timeout=15) as resp:
            return resp.status, resp.read().decode("utf-8", "replace"), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e.headers

# raw no-follow client for 302 probes and header-carrying posts
def raw(method, port, path, body=None, headers=None):
    h = dict(headers or {})
    data = body
    if isinstance(body, (dict, list)):
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    conn.request(method, path, body=data, headers=h)
    resp = conn.getresponse()
    out = resp.status, resp.read().decode("utf-8", "replace"), dict(resp.getheaders())
    conn.close()
    return out

def wait_up(port):
    for _ in range(60):
        try:
            req("GET", "/api/wiki/status", base=f"http://127.0.0.1:{port}")
            return True
        except Exception:
            time.sleep(0.5)
    return False

def start(port, data, env, log):
    e = dict(os.environ)
    e.update(env)
    lf = open(f"{ROOT}/{log}", "wb")
    p = subprocess.Popen([BIN, "--dir", data, "--home", "wiki.phext",
                          "--home-coord", "1.1.1/1.1.1/1.1.1",
                          "--host", "127.0.0.1", "--port", str(port)],
                         stdout=lf, stderr=lf, env=e, cwd=ROOT)
    ok = wait_up(port)
    print(f"server on {port} up:", ok, "pid", p.pid)
    return p

def stop(p):
    p.terminate()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()

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

# ---------- Phase A: the consumer, signed out ----------
consumer_env = {
    "PHEXT_PUBLIC_URL": "https://fox.phext.io",
    "PHEXT_SESSION_SECRET": "wiki2-hub-consumer-session-secret-01",
    "PHEXT_SSO_SECRET": SSO_SECRET,
    "PHEXT_SSO_AUDIENCE": "novafoxwiki",
    "PHEXT_SSO_PROVIDER_URL": PBASE,
}
srv = start(CPORT, DATA, consumer_env, "sso-consumer.log")
s, body, _ = req("GET", "/wiki/")
check("A: /wiki/ shell 200 signed-out", s == 200, f"status {s}")
check("A: shell is dark-themed", ("--text: #dedede" in body) or ("#101010" in body), "")
s, body, _ = req("GET", "/api/wiki/status")
wst = json.loads(body) if s == 200 else {}
wk = explode(open(f"{DATA}/wiki.phext", "rb").read())
check("A: /api/wiki/status", s == 200 and wst.get("scrolls", 0) == len(wk), str(wst))
s, body, _ = req("GET", "/api/wiki/nav?at=1.1.1/1.1.1/1.1.1")
check("A: front page via catalog", "Nova Fox Wiki" in body, "")
s, body, _ = req("GET", "/api/wiki/nav?at=1.1.1/1.1.3/1.1.1")
check("A: feedback page via catalog", "Feedback" in body and "feedback door" in body, "")
s, body, _ = req("POST", "/api/wiki/nav", {"x": 1})
check("A: catalog write refused (405)", s == 405, f"status {s}")
s, body, _ = req("GET", "/api/scroll/1.1.1/1.1.1/1.1.1")
check("A: editor reads are open signed-out (login-to-edit doctrine)", s == 200, f"status {s}")
s, body, _ = req("POST", "/api/update", {"coordinate": "1.1.1/1.1.1/1.1.1", "content": "vandal"})
check("A: editor write 401 signed-out", s == 401, f"status {s}")
s, body, _ = req("POST", "/api/open", f"{DATA}/feedback.phext")
check("A: viewport open is read-class by doctrine (200 signed-out)", s == 200, f"status {s}")
s, body, _ = req("GET", "/api/session")
sj = json.loads(body)
check("A: session signed-out, locked, SSO endpoint advertised",
      sj.get("signed_in") is False and sj.get("locked") is True
      and sj.get("sso") == f"{PBASE}/api/auth/sso/novafoxwiki"
      and sj.get("providers") == [], body[:160])
s, body, _ = req("GET", "/api/wiki/nav?at=1.1.1/1.1.1/1.1.1")
check("A: front page intact after write attempts", "Nova Fox Wiki" in body and "vandal" not in body, "")

# ---------- Phase B: the test provider ----------
pdata = "/tmp/wiki2-provider-data"
shutil.rmtree(pdata, ignore_errors=True)
shutil.copytree(DATA, pdata)
provider_env = {
    "PHEXT_PUBLIC_URL": PBASE,
    "PHEXT_SESSION_SECRET": "wiki2-hub-provider-session-secret-01",
    "GITHUB_CLIENT_ID": "wiki2-hub-test-scaffolding",
    "GITHUB_CLIENT_SECRET": "wiki2-hub-test-scaffolding-not-a-real-secret",
    "PHEXT_SSO_SECRET": SSO_SECRET,
    "PHEXT_SSO_NOVAFOXWIKI_URL": CBASE,
    "PHEXT_SSO_AGENT_EMISE_SECRET": AGENT_SECRET,
}
psrv = start(PPORT, pdata, provider_env, "sso-provider.log")
s, body, hdrs = raw("GET", PPORT, "/api/auth/sso/novafoxwiki?return=/feedback/")
loc = hdrs.get("Location", "")
check("B: SSO start for novafoxwiki bounces to sign-in (302)",
      s == 302 and loc.startswith(f"{PBASE}/?next="), f"status {s} loc {loc[:90]}")
s, body, hdrs = raw("GET", PPORT, "/api/auth/sso/notreal?return=/")
check("B: unknown audience 404", s == 404, f"status {s}")
s, body, hdrs = raw("POST", PPORT, "/api/auth/sso/agent/assertion",
                    {"aud": "novafoxwiki"},
                    {"x-phext-agent": "emise", "x-phext-agent-secret": AGENT_SECRET})
mint = json.loads(body) if s == 200 else {}
assertion = mint.get("assertion", "")
check("B: agent mint issues a novafoxwiki assertion", s == 200 and "." in assertion, f"status {s} {body[:80]}")
s, body, hdrs = raw("POST", PPORT, "/api/auth/sso/agent/assertion",
                    {"aud": "novafoxwiki"},
                    {"x-phext-agent": "emise", "x-phext-agent-secret": "wrong-secret-wrong-secret-wrong"})
check("B: agent mint refuses a bad secret (401)", s == 401, f"status {s}")
s, body, hdrs = raw("POST", PPORT, "/api/auth/sso/agent/assertion",
                    {"aud": "mutable"},
                    {"x-phext-agent": "emise", "x-phext-agent-secret": AGENT_SECRET})
foreign = (json.loads(body) if s == 200 else {}).get("assertion", "")
check("B: agent mint issues a foreign (mutable) assertion", s == 200 and "." in foreign, f"status {s}")

def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def seal_assertion(payload):
    body = b64u(json.dumps(payload).encode())
    sig = b64u(hmac.new(SSO_SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"

now = int(time.time())
assertion = seal_assertion({
    "aud": "novafoxwiki", "who": "google:sub-1", "handle": "ada",
    "name": "Ada Lovelace", "email": "", "editor": False,
    "ret": "/feedback/", "iat": now, "exp": now + 120,
    "jti": "wiki2-hub-round-trip-0001",
})

# ---------- Phase C: the round trip at the consumer ----------
s, body, hdrs = raw("GET", CPORT, f"/api/auth/callback?assertion={assertion}")
set_cookie = hdrs.get("Set-Cookie", "")
cookie = set_cookie.split(";")[0] if set_cookie.startswith("phext_session=") else ""
check("C: callback 302 to the return path, session cookie sealed",
      s == 302 and hdrs.get("Location", "") == "/feedback/" and cookie.startswith("phext_session="),
      f"status {s} loc {hdrs.get('Location', '')[:40]}")
H = {"Cookie": cookie}
s, body, _ = req("GET", "/api/session", headers=H)
sj = json.loads(body)
csrf = sj.get("csrf", "")
check("C: session is the SSO identity (google:sub-1)",
      sj.get("signed_in") is True and sj.get("who") == "google:sub-1", body[:140])
H["x-csrf-token"] = csrf
s, body, _ = req("POST", "/api/open", f"{DATA}/feedback.phext",
                 headers={**H, "Content-Type": "text/plain"})
s2, status_body, _ = req("GET", "/api/status", headers=H)
check("C: feedback book opened under the SSO session",
      "feedback.phext" in str(json.loads(status_body).get("file", "")), status_body[:90])
fb = explode(open(f"{DATA}/feedback.phext", "rb").read())
nums = [int(m.group(1)) for c in fb for m in [re.match(r"1\.1\.1/1\.1\.(\d+)/1\.1\.1", c)] if m]
coord = f"1.1.1/1.1.{max(nums + [1]) + 1}/1.1.1"
entry = (f"TEST · fox wiki-ee{EE} · WIKI-2 verification entry\n\n"
         "TEST entry — written through the editor's own write path on the hub "
         "instance, under a session sealed by the phext.tech SSO consumer "
         "callback (test provider, agent-minted assertion), to prove the "
         "feedback intake round-trips on SSO sign-in. This is a test entry, "
         "not player feedback.\n")
s, body, _ = req("POST", "/api/update", {"coordinate": coord, "content": entry}, headers=H)
check("C: TEST feedback entry written under the SSO session", okj(body), body[:100])
s, body, _ = req("POST", "/api/save", "", headers=H)
check("C: feedback saved", okj(body), body[:100])
s, body, _ = req("GET", f"/api/scroll/{coord}", headers=H)
check("C: TEST entry reads back via API", json.loads(body).get("content", "") == entry, "")
s, body, hdrs = raw("GET", CPORT, f"/api/auth/callback?assertion={assertion}")
check("C: replayed assertion refused (400)", s == 400 and "Sign-in did not complete." in body, f"status {s}")
s, body, hdrs = raw("GET", CPORT, f"/api/auth/callback?assertion={foreign}")
check("C: foreign-audience assertion refused (400)", s == 400 and "Sign-in did not complete." in body, f"status {s}")
tampered = ("A" if assertion[0] != "A" else "B") + assertion[1:]
s, body, hdrs = raw("GET", CPORT, f"/api/auth/callback?assertion={tampered}")
check("C: tampered assertion refused (400)", s == 400, f"status {s}")
stop(psrv)
stop(srv)
fb = explode(open(f"{DATA}/feedback.phext", "rb").read())
check("C: TEST entry verified on disk", fb.get(coord, "").startswith("TEST ·"), str(list(fb)))

# ---------- Phase D: unconfigured — the fail-closed fact ----------
srv = start(CPORT, DATA, {}, "sso-open.log")
s, body, _ = req("GET", "/api/session")
sj = json.loads(body)
check("D: unconfigured instance reports unlocked, no SSO endpoint",
      sj.get("locked") is False and sj.get("sso") is None, body[:140])
s, body, _ = req("GET", "/api/scroll/1.1.1/1.1.1/1.1.1")
check("D: editor reads admitted signed-out while unlocked (why leg 2 waits)",
      s == 200, f"status {s}")
stop(srv)

fails = [r for r in results if not r[1]]
print(f"\n==== {len(results) - len(fails)}/{len(results)} checks passed ====")
if fails:
    for n, _ in fails: print("FAILED:", n)
    sys.exit(1)
