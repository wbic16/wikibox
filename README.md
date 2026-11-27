# Wikibox

Wikibox is the wiki shape of phext-edit: a phext named `wiki.phext`
in a phext-edit directory is published — readable without sign-in,
read-only — at the instance's `/wiki/` shell and `/api/wiki/*`
catalog, while everything else in the directory stays behind the
editor's sign-in gate. The engine lives in wbic16/phext-lattice
(the wiki line: branch `emise/public-example-wiki`); this repo
holds the instances.

## Instances

### nova-fox/ — the Nova Fox wiki

Live (read side) at https://fox.phext.io/wiki/ once its launch
package runs; the instance runs on awsbox as the wbic16 user
service `nova-fox-wiki.service` (127.0.0.1:8082).

- `build-wiki.py` — builds the wiki book (`wiki.phext`: front
  page with the ship log, the feedback page, one paved-path page
  per agent substrate of record, Novakor, raiding) and the
  feedback book seed (`feedback.phext`) at a given Exocortical
  Epoch.
- `nova-fox-heart.jpg` — the front page's heart image (the
  exo-dreams declaration, downscaled); uploaded into the book
  through the editor's own image path at build time.
- `nova-fox-wiki.service` — the systemd user unit.
- `oauth.env.example` — the instance environment shape (the live
  file stays on awsbox, mode 0600, never in git).
- `verify-hub.py` — the QC driver: exercises the write path in
  the editor's local mode (image upload, page edit, book switch,
  a TEST feedback entry round-trip) and the public gates on a
  locked configuration (catalog public and read-only, editor API
  401 signed-out, sign-in redirect, dark shell, EE stamp).
- `launch/` — the awsbox launch package (RUNBOOK.md, install.sh,
  patch-fox-vhost.py), mirroring the fox game's launch pattern:
  everything pre-staged, the root steps packaged into one gated
  script with automatic rollback.

The feedback loop: the game's feedback door lands on the wiki's
Feedback page; signed-in players write one scroll per note into
the feedback book; the Nova Fox dev loop harvests that book
alongside the game's ideas scroll.
