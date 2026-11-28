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
  public + read-only, editor API 401 signed-out, dark shell).
  Sign-in is phext.tech SSO
  (WIKI-2): the instance binary is phext-lattice@exo e620b64,
  whose consumer mode the hub gates exercised end to end —
  test-provider mint → consumer callback → sealed session →
  a TEST feedback entry under the SSO identity, with replay,
  foreign-audience, and tampered assertions refused.

## Will's remaining steps

1. `bash ~/nova-fox-wiki-launch/install.sh`
   Puts the read side live (wiki shell + public catalog + the
   feedback-door redirect) behind an `nginx -t` gate with
   automatic rollback. Asks for the sudo password once or twice.
2. The provider block — one sudo block. It names this wiki as
   an audience at phext.tech, hands the wiki the shared SSO
   secret (file to file; the value is never printed), and
   deploys the phext-edit build that carries the audience arm:

   ```sh
   # the audience line for the provider
   sudo sh -c 'grep -q "^PHEXT_SSO_NOVAFOXWIKI_URL=" /etc/phext-edit/oauth.env || echo "PHEXT_SSO_NOVAFOXWIKI_URL=https://fox.phext.io" >> /etc/phext-edit/oauth.env'
   # the shared secret into the wiki's env (value never printed)
   sudo sh -c 'grep "^PHEXT_SSO_SECRET=" /etc/phext-edit/oauth.env >> /home/wbic16/nova-fox-wiki/oauth.env'
   # the new phext-edit build (phext-lattice@exo e620b64), by
   # the standing deploy path, then restart the provider
   cd /source/phext-lattice && git pull && cargo build --release --bin phext-edit
   sudo systemctl restart phext-edit.service
   ```

   There is no GitHub OAuth app to create — that was the
   WIKI-1 shape, and it is cancelled. phext.tech is the broker;
   GitHub, Google, and X are the logins behind its own flow.
3. Re-run `bash ~/nova-fox-wiki-launch/install.sh`
   With the SSO configuration in place (audience + secret), it
   restarts the wiki service, opens the write side (editor API
   + the feedback book's shell), and runs the smoke checks.
   Signed-in players can then write feedback; signed-in editors
   can tend the wiki book. A completed sign-in against the
   production phext.tech is the one leg no hub gate can
   exercise — it is verified by the first real sign-in, as
   with every SSO consumer before this one.

## How the pieces fit

- Reading is public: nginx proxies `/wiki/` and `/api/wiki/` to
  the instance; the catalog is built from wiki.phext and refuses
  writes (405). The deployed book's version lives in the deploy
  record, not on its pages (no-tech standard, below).
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
- Sign-in: the game's door sends players to the wiki; the
  wiki's own sign-in surface links straight to phext.tech's
  handoff for the `novafoxwiki` audience, phext.tech signs the
  player in (GitHub, Google, or X), and the sealed assertion
  lands on the wiki's `/api/auth/callback`, which burns it and
  seals the wiki's own session. The wiki holds no provider
  keys of its own — never invent a per-site scheme.
- Fail-closed by construction: the write side is proxied only
  once the SSO configuration (audience + shared secret) is in
  the instance's env. Without it, phext-edit runs unlocked, so
  its editor routes stay loopback-only until then.
- Content standard (Will, 2026-11-27): every page on this wiki is age appropriate for all audiences — no profanity or crude language, no sexual content, no graphic violence beyond the game's own cartoon register, and no gambling framing anywhere (Novakor sponsorship is funding for features, never wagering, bidding, or odds). Money pages are written plainly to the account holder.
- UX standard (Will, 2026-11-27): the UI/UX is super simple — a newcomer lands, reads, and finds feedback and sign-in without learning the editor: few choices, plain words, the feedback door and sign-in unmissable from the front page.
- No-tech standard (Will, 2026-11-27): a game wiki talks about the game, not the tech. Reader-facing pages carry no phext, scroll, coordinate, EE, SSO, dimension, or editor talk: sign-in is just "sign in," feedback is just "sign in, write your note," and the ship log is "What's New" in plain words. Version stamps and machinery live in the deploy record (this repo's history), never on the pages.
