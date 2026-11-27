#!/usr/bin/env python3
"""Insert the Nova Fox wiki locations into the fox.phext.io vhost.

Run by nova-fox-wiki-launch/install.sh (as root, via sudo) on
awsbox. Two legs, each idempotent (a second run sees the leg's
marker and changes nothing); the caller gates on `nginx -t` and
restores the backup on any failure.

  leg1  read side — the wiki shell (/wiki/), its public read-only
        catalog (/api/wiki/), the session report, the sign-in
        routes, and the feedback-door redirect (/wiki/feedback).
        No editor route is proxied: the catalog refuses writes.
  leg2  write side — the editor API (/api/) and the feedback
        book's shell (/feedback/). install.sh applies this leg
        only once the wiki's oauth.env carries a sign-in provider,
        so the instance is locked (signed-out writes answer 401).

Both legs proxy to the wiki instance on 127.0.0.1:8082 (a wbic16
user service, nova-fox-wiki.service) and are inserted immediately
before the vhost's static `location /` block.
"""
import shutil
import sys
import time

PATH = "/etc/nginx/sites-available/fox.phext.io"

PROXY = """        proxy_pass http://127.0.0.1:8082;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
"""

LEG1_MARKER = "# nova-fox-wiki-read (installed by nova-fox-wiki-launch/install.sh)"
LEG1 = """
    # nova-fox-wiki-read (installed by nova-fox-wiki-launch/install.sh) —
    # the Nova Fox wiki (Wikibox / phext-edit) on 127.0.0.1:8082, a
    # wbic16 user service. Read side: the wiki shell, its public
    # read-only catalog, the session report, and the sign-in routes.
    # The catalog refuses writes (405); no editor route is proxied
    # on this leg.
    location = /wiki {
        return 302 /wiki/;
    }

    location /wiki/ {
""" + PROXY + """    }

    location /api/wiki/ {
""" + PROXY + """    }

    location = /api/session {
""" + PROXY + """    }

    location /api/auth/ {
""" + PROXY + """    }

    # The game's feedback door lands here: on to the wiki shell,
    # open at the Feedback scroll, the door's query preserved.
    location = /wiki/feedback {
        return 302 "/wiki/?$args#1.1.1/1.1.3/1.1.1";
    }
"""

LEG2_MARKER = "# nova-fox-wiki-write (installed by nova-fox-wiki-launch/install.sh)"
LEG2 = """
    # nova-fox-wiki-write (installed by nova-fox-wiki-launch/install.sh) —
    # the wiki's write side: the editor API and the feedback book's
    # shell. Installed only once oauth.env carries a sign-in
    # provider, so the instance is locked (signed-out writes 401).
    location /api/ {
""" + PROXY + """        client_max_body_size 16M;
    }

    location /feedback/ {
""" + PROXY + """    }
"""

LEGS = {"leg1": (LEG1_MARKER, LEG1), "leg2": (LEG2_MARKER, LEG2)}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in LEGS:
        print("usage: patch-fox-vhost.py leg1|leg2")
        return 2
    marker, block = LEGS[sys.argv[1]]
    with open(PATH, "r", encoding="utf-8") as f:
        src = f.read()
    if marker in src:
        print("fox.phext.io: %s already present — no change" % sys.argv[1])
        return 0
    anchor = "    location / {"
    i = src.find(anchor)
    if i < 0:
        print("fox.phext.io: ANCHOR NOT FOUND (%r) — refusing to guess" % anchor)
        return 1
    backup = PATH + ".bak-nova-fox-wiki-" + time.strftime("%Y%m%d%H%M%S")
    shutil.copy2(PATH, backup)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(src[:i] + block.lstrip("\n") + "\n" + src[i:])
    print("fox.phext.io: %s inserted (backup: %s)" % (sys.argv[1], backup))
    return 0


if __name__ == "__main__":
    sys.exit(main())
