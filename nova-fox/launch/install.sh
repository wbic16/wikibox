#!/bin/bash
# Nova Fox wiki — the public legs at fox.phext.io/wiki.
#
# Run on awsbox as wbic16; the script sudo's the nginx steps (the
# password is asked once or twice). Everything else — the wiki
# instance itself (a wbic16 user service on 127.0.0.1:8082), its
# content, and this package — is already in place and verified.
#
#   leg 1 (read)  installs always: the wiki shell, its public
#                 read-only catalog, the session report, the
#                 sign-in routes, the feedback-door redirect.
#   leg 2 (write) installs only when ~/nova-fox-wiki/oauth.env
#                 carries the phext.tech SSO configuration (the
#                 audience line and the shared SSO secret): the
#                 wiki signs in as an SSO consumer, and before
#                 that configuration lands the instance is not
#                 locked, so its editor routes must stay
#                 unproxied. The RUNBOOK's step 2 lands both
#                 halves; then re-run this script — it is
#                 idempotent.
#
# `nginx -t` gates every reload; a failed test rolls the vhost
# back from the patch script's backup automatically.
set -u

SITE=fox.phext.io
LAUNCH="$HOME/nova-fox-wiki-launch"
WIKI="$HOME/nova-fox-wiki"
VHOST=/etc/nginx/sites-available/fox.phext.io

say() { echo "[wiki] $*"; }
die() { echo "[wiki] FATAL: $*" >&2; exit 1; }

systemctl --user is-active nova-fox-wiki.service >/dev/null \
  || die "nova-fox-wiki.service is not running — systemctl --user start nova-fox-wiki first"

BACKUPS=$(ls "$VHOST".bak-nova-fox-wiki-* 2>/dev/null | wc -l)
gate() {
  if ! sudo nginx -t; then
    NEWEST=$(ls -t "$VHOST".bak-nova-fox-wiki-* 2>/dev/null | head -1)
    COUNT=$(ls "$VHOST".bak-nova-fox-wiki-* 2>/dev/null | wc -l)
    if [ -n "$NEWEST" ] && [ "$COUNT" -gt "$BACKUPS" ]; then
      sudo cp "$NEWEST" "$VHOST"
      sudo nginx -t && say "vhost rolled back to $NEWEST"
    fi
    die "nginx -t failed — rolled back"
  fi
}

# --- leg 1: the read side.
sudo python3 "$LAUNCH/patch-fox-vhost.py" leg1 || die "leg1 patch failed"
gate
sudo systemctl reload nginx
say "leg 1 (read) live: https://$SITE/wiki/"

# --- leg 2: the write side, once sign-in is configured.
LEG2=held
if grep -q '^PHEXT_SSO_AUDIENCE=.\+' "$WIKI/oauth.env" && grep -q '^PHEXT_SSO_SECRET=.\+' "$WIKI/oauth.env"; then
  systemctl --user restart nova-fox-wiki.service
  sleep 2
  sudo python3 "$LAUNCH/patch-fox-vhost.py" leg2 || die "leg2 patch failed"
  gate
  sudo systemctl reload nginx
  LEG2=live
  say "leg 2 (write) live — sign-in configured, editor routes proxied"
else
  say "leg 2 (write) HELD: phext.tech SSO is not fully configured in $WIKI/oauth.env"
  say "  1. run the RUNBOOK step 2 block (provider audience + secret handoff)"
  say "  2. PHEXT_SSO_AUDIENCE and PHEXT_SSO_SECRET must both be set in $WIKI/oauth.env"
  say "  3. re-run this script"
fi

# --- smoke checks.
say "smoke checks:"
code=$(curl -s -o /tmp/wiki-smoke.html -w '%{http_code}' --max-time 10 "https://$SITE/wiki/")
curl -s --max-time 10 "https://$SITE/api/wiki/nav?c=1.1.1/1.1.1/1.1.1" | grep -qi "Nova Fox" && TITLE=ok || TITLE=MISSING
echo "  https://$SITE/wiki/        -> $code (shell: $TITLE)"
stat=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://$SITE/api/wiki/status")
echo "  /api/wiki/status            -> $stat (want 200)"
post=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST "https://$SITE/api/wiki/nav")
echo "  POST /api/wiki/nav          -> $post (want 405)"
door=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 10 "https://$SITE/wiki/feedback?from=game&ee=0")
echo "  /wiki/feedback              -> $door (want 302 to /wiki/ at the Feedback scroll)"
if [ "$LEG2" = live ]; then
  sess=$(curl -s --max-time 10 "https://$SITE/api/session")
  echo "  /api/session                -> $sess" | head -c 220; echo
  sc=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://$SITE/api/scroll/1.1.1/1.1.1/1.1.1")
  echo "  /api/scroll signed out      -> $sc (want 401)"
fi
[ "$code" = 200 ] && [ "$TITLE" = ok ] && [ "$stat" = 200 ] && [ "$post" = 405 ] \
  && say "SMOKE PASS — the Nova Fox wiki is live at https://$SITE/wiki/" \
  || say "SMOKE: something above is off — read the lines before believing this"
