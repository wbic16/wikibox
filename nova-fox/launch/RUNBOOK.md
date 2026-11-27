# Nova Fox wiki — launch package (awsbox)

The Nova Fox wiki: a Wikibox instance (phext-edit, from
wbic16/phext-lattice's wiki line) branded for Nova Fox, served at
**https://fox.phext.io/wiki/**. Source of record: wbic16/wikibox,
`nova-fox/` — this directory on awsbox (`~/nova-fox-wiki-launch/`)
is the operative copy of the launch leg, mirroring the fox game's
own `~/fox-phext-launch/` pattern.

## What is already in place (wbic16, no sudo)

- Instance home: `~/nova-fox-wiki/` — `bin/phext-edit` (the wiki
  build), `data/wiki.phext` (the wiki book: front page, ship log,
  feedback page, agent paved paths, Novakor, raiding),
  `data/feedback.phext` (the feedback book the door writes into),
  `src/` (content builder + the heart image), `oauth.env` (0600).
- Service: `nova-fox-wiki.service`, a wbic16 **user** service on
  127.0.0.1:8082 (linger is on; it starts at boot). Status:
  `systemctl --user status nova-fox-wiki`.
- Verified before staging: the full write path (image upload,
  page edit, book switch, a TEST feedback entry written and read
  back), and the public gates on a locked configuration (catalog
  public + read-only, editor API 401 signed-out, sign-in 302 to
  the provider, dark shell, EE stamp on the front page).

## Will's remaining steps

1. `bash ~/nova-fox-wiki-launch/install.sh`
   Puts the read side live (wiki shell + public catalog + the
   feedback-door redirect) behind an `nginx -t` gate with
   automatic rollback. Asks for the sudo password once or twice.
2. Create a GitHub OAuth app for the wiki — callback URL:
   `https://fox.phext.io/api/auth/github/callback` — and fill
   `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` in
   `~/nova-fox-wiki/oauth.env`. (The instance takes its own OAuth
   registration: GitHub allows one callback per app, and the
   production editor's app points at edit.phext.io. phext.tech
   SSO for the wiki is the fast-follow; it needs the wiki added
   to the SSO provider's audience list.)
3. Re-run `bash ~/nova-fox-wiki-launch/install.sh`
   With sign-in configured, it restarts the service, opens the
   write side (editor API + the feedback book's shell), and runs
   the smoke checks. Signed-in players can then write feedback;
   signed-in editors can tend the wiki book.

## How the pieces fit

- Reading is public: nginx proxies `/wiki/` and `/api/wiki/` to
  the instance; the catalog is built from wiki.phext and refuses
  writes (405). The deployed front page carries the wiki's ship
  EE on its face.
- The game's feedback door points at
  `https://fox.phext.io/wiki/feedback`; the vhost redirects it
  (query preserved) to the wiki shell open at the Feedback
  scroll. The Feedback page sends signed-in players to the
  feedback book (`/feedback/`), one scroll per note.
- Harvest: the dev loop reads `~/nova-fox-wiki/data/feedback.phext`
  on awsbox (ssh, read-only) alongside the game's ideas scroll —
  same register → named build → visibly shipped pipeline. The
  wiki book (wiki.phext) is curated content; the feedback book is
  runtime data and is never committed to git.
- Fail-closed by construction: the write side is proxied only
  once a sign-in provider exists. Without one, phext-edit runs
  unlocked, so its editor routes stay loopback-only until then.
