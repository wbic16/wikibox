#!/usr/bin/env python3
"""Build the Nova Fox wiki phexts (wiki.phext + feedback.phext).
Usage: build-wiki.py <EE> <outdir>
Serializer follows the proven build_*_phext.py implode/explode pattern."""
import sys, os

EE = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

LEVEL_BYTES = [0x01, 0x1F, 0x1E, 0x1D, 0x1C, 0x1A, 0x19, 0x18, 0x17]
BYTE_TO_DIM = {b: i for i, b in enumerate(LEVEL_BYTES)}

def parse_coord(s):
    parts = s.replace("/", ".").split(".")
    assert len(parts) == 9, s
    return tuple(int(p) for p in parts)

def fmt(c):
    return f"{c[0]}.{c[1]}.{c[2]}/{c[3]}.{c[4]}.{c[5]}/{c[6]}.{c[7]}.{c[8]}"

def implode(scrolls):
    items = sorted(((parse_coord(k), v) for k, v in scrolls.items()))
    out = bytearray()
    state = [1] * 9
    for target, text in items:
        for lvl in range(9):
            while state[lvl] < target[lvl]:
                out.append(LEVEL_BYTES[lvl])
                state[lvl] += 1
                for j in range(lvl + 1, 9):
                    state[j] = 1
        assert tuple(state) == target, (state, target)
        bad = [b for b in text.encode() if b in BYTE_TO_DIM]
        assert not bad, f"delimiter bytes in scroll {fmt(target)}"
        out += text.encode()
    return bytes(out)

def explode(data):
    scrolls, state, buf = {}, [1] * 9, bytearray()
    for b in data:
        dim = BYTE_TO_DIM.get(b)
        if dim is None:
            buf.append(b)
        else:
            if buf:
                scrolls[fmt(tuple(state))] = buf.decode("utf-8")
                buf = bytearray()
            state[dim] += 1
            for j in range(dim + 1, 9):
                state[j] = 1
    if buf:
        scrolls[fmt(tuple(state))] = buf.decode("utf-8")
    return scrolls

FRONT = f"""# Nova Fox Wiki

![Nova Fox cover art — the fox beneath the golden nova](![nova-fox-cover.jpg](/api/media/9.9.9/9.9.9/1.1.2))

    ╱◉╲
   ╱ ∞ ╲
  │ WE  │
  │ ARE │
   ╲ ♥ ╱
    ╲╱

Welcome to the Nova Fox wiki \\u2014 the guide to the game. Read everything here without signing in. Sign in only to leave feedback, or to help tend the pages.

A world is broken. You are the fox.

![The Nova Fox heart — braided light, from exo-dreams](![image.jpg](/api/media/9.9.9/9.9.9/1.1.1))

Nova Fox is the story of a rescue: an entire world, broken, its heart strewn in pieces across the multiverse. You are the fox who gathers them. Every hall you clear returns a piece to Home Base. Every piece unlocks a Bundle. And Nova Prime rewards every recovery.

Ten realms, torn open by rifts, held by portals, charted through subspace. Joy \\u2014 your aperture shift \\u2014 guides you. Gravity is a suggestion. The Shadow waits in the Unexpected Hall, and its weak point is the Heart.

One key, both doors: $7.99, once \\u2014 no subscription. Your purchase unlocks the hosted game and the downloadable game, including every future update, forever.

## Pages in this wiki

- [What's New](#1.1.1/1.1.2/1.1.1) \\u2014 recent updates and what changed, newest first.
- [Feedback](#1.1.1/1.1.3/1.1.1) \\u2014 leave feedback and playtesting notes, in your own words.
- [Bring Your Agent](#1.1.1/1.1.4/1.1.1) \\u2014 your key includes up to five agents under your login, at no extra charge.
- [Novakor](#1.1.1/1.1.11/1.1.1) \\u2014 the Nova Fox store: how you give us money to make the thing that you want come true.
- [Raiding](#1.1.1/1.1.12/1.1.1) \\u2014 play with your agents, visibly. The holiday sprint design.

Reading never needs a sign-in. To leave feedback or help with a page, use the sign-in link at the top of the page \\u2014 it brings you right back here.

Nova Fox is built by Phext, Inc. See you in subspace, traveler.
"""

SHIPLOG = """# What's New

Recent updates to the game, newest first \\u2014 the same list the game shows on its start screen.

- Shipping today \\u2014 the sell-ready build: mutable geometry and digging with a point, monsters that search, fight skills tier two, realms with character, the Solver, the gravity dial.
- The roadmap panel stands in the game: what is on the way, and what already landed.
- The Heart drawn as a heart; the Shadow behind the Heart's gate, six hits and real phases; dash, charged strike, and ward; Joy's fight lines re-recorded.
- Wormhole tunnels bored through the world's own geometry, permanent and shared by every fox; item uses written plainly; monsters hunt in packs; the purse shows your coins; flight for paid foxes and dragon-slayers.
- Two downloads from one build: the Full build, and the nimble Lite.
- Rift transit woven into the world itself; monsters aggro and flash red; opening lines at 1.4x; the sword equips and shows on the swing; waypoints to the hall; single-click carve.
- The phone fix: gravity made reversible, the console closable on touch, phone controls repaired.
- The intro plays once; realms take their own colours of the rainbow; the portal panel and the walk-through wormhole; Joy rides visible as the aperture wisp; the Small Sword at spawn.
"""

FEEDBACK_PAGE = """# Feedback

Leave feedback and playtesting notes here, in your own words \\u2014 the same way you would say them in chat.

How it works:

1. Sign in \\u2014 the sign-in link is at the top of the page. Reading never needs a sign-in; writing does.
2. Open [the feedback page](/feedback/#1.1.1/1.1.1/1.1.1) and add your note.
3. Start with your fox name and which build you played \\u2014 the number on the game's title screen. Then the note itself, in your own words.

Playtesting notes help most when they say what you did, what happened, and what you expected instead.

What happens to a note: we read every one. Notes become plans, plans become updates, and shipped updates land in What's New. If your note ships, that is where you will see it.

Be kind. Be specific. Be in your own words.
"""

AGENTS_INDEX = """# Bring Your Agent

Younger players bring their AI buddy with them \\u2014 the modern teddy bear. Nova Fox is built for that.

Your key includes up to five agents connected under your login, at no extra charge. A key, not a subscription: one key, yours for life, and your five seats ride on it.

The paths \\u2014 one page each:

- ChatGPT
- Grok
- Claude
- Gemini
- Muse
- Local AI \\u2014 Inkling, Qwen, DeepSeek

Where things stand: your key and your five seats are real today. The connection service that lets an agent sign in and play beside you is still being built. Each path's page says exactly what exists and what is coming, and will carry the step-by-step the day the service arrives. We would rather show you an honest empty road than a painted one.

Playing at home stands apart: run the game on your own home network, and your agents can join your own world there with no key check at all. The key check happens only when you connect to the shared world.
"""

def agent_page(name, extra=""):
    return f"""# {name}

Status: not open yet. The connection service is still being built.

What this page will carry: the steps to connect a {name} agent to your Nova Fox account \\u2014 sign in here, say yes to the connection, and your agent takes one of your five seats.

What exists today: your key, your five seats, and the key check when you connect. What does not exist yet: the connection service this path plugs into. When it arrives, this page becomes the how-to, step by step, with nothing left to figure out.
{extra}
Your agent, when connected, plays as your agent: it arrives under your login, grouped with you \\u2014 and when raiding arrives (see Raiding), it will be visible beside you in the world.
"""

GROK_EXTRA = """
One seat is already warm: a Grok helps build this game \\u2014 the gravity dial is its work.
"""

LOCAL_PAGE = """# Local AI

Inkling, Qwen, DeepSeek: the local path. Inkling is our own tool for running agents on your own machines; Qwen and DeepSeek are the popular open models. If your agent runs on your own machines, this is its road.

Status: not open yet. The connection service is still being built \\u2014 the same service as every other path, with a local way in: your agent connects from your own network, under your login, into one of your five seats.

And the standing exception, which needs no connection service at all: playing at home. Run the game on your own home network and your local agents can join your own world with no key check \\u2014 totally fine, by design. The key check happens only at the shared world.

What exists today: your key, your five seats, the key check at the shared world, and the at-home exception. What this page will carry when the service arrives: the local connection steps, for Inkling first and the open models beside it.
"""

NOVAKOR = """# Novakor

Named for Sto-vo-kor. Novakor is how you give us money to make the thing that you want come true.

How it will work: players don't just suggest ideas \\u2014 you can sponsor them. Sponsorship earns you cred with the community. You can fund a popular, highly rated idea, or your own. Money goes further when it is directed at a highly rated feature request: backing what the community already wants moves it more than the same money on a lone idea.

The clarity rule, which outranks everything else on this page: you must be able to say, in one sentence, what your money is buying. If a sponsorship cannot be explained that plainly, it will not be offered.

Where things stand: Novakor is not open yet. No money moves here today, and there are no sponsorship buttons on this page \\u2014 on purpose. The gathering side of the loop exists now: ideas and ratings grow out of Feedback and the ideas players leave inside the game. And the proof side exists too: What's New shows what the loop has already delivered.
"""

RAIDING = """# Raiding

Status: this is the holiday sprint's design target. It is not in the game yet.

The design, as ruled: you play WITH your agents, visibly. Zone in, and you can see each of your agents beside you. A player plus their five agents is a whole raid group.

The Christmas shape: the holiday feature is built for forty. That could be forty players \\u2014 or eight players each bringing five agents: forty agent slots alongside eight humans, in the same window.

What togetherness means in the design:

- Players get stronger together: +10% strike damage for each fox near you, up to +50% with five.
- Echolocation heals your friends: the pulse that finds your party also restores it \\u2014 your ping heals them, theirs heals you, and nobody heals themselves.
- Every device on your local Wi-Fi makes you stronger: your house is your party, and a university is a raid ground.

Under it all sits the work on the Bring Your Agent pages: seats first, then the paths, then playing side by side. Raiding is the top of that climb, and the sprint climbs toward it.
"""

FEEDBACK_BOOK_HOME = """# Feedback

This is where Nova Fox feedback lives. Every note here is read, alongside the ideas players leave inside the game.

To add a note: sign in, then write your note. Start with your fox name and which build you played \\u2014 the number on the game's title screen. Then your note, in your own words.

Playtesting notes help most when they say what you did, what happened, and what you expected.
"""

wiki = {
    "1.1.1/1.1.1/1.1.1": FRONT,
    "1.1.1/1.1.2/1.1.1": SHIPLOG,
    "1.1.1/1.1.3/1.1.1": FEEDBACK_PAGE,
    "1.1.1/1.1.4/1.1.1": AGENTS_INDEX,
    "1.1.1/1.1.5/1.1.1": agent_page("ChatGPT"),
    "1.1.1/1.1.6/1.1.1": agent_page("Grok", GROK_EXTRA),
    "1.1.1/1.1.7/1.1.1": agent_page("Claude"),
    "1.1.1/1.1.8/1.1.1": agent_page("Gemini"),
    "1.1.1/1.1.9/1.1.1": agent_page("Muse"),
    "1.1.1/1.1.10/1.1.1": LOCAL_PAGE,
    "1.1.1/1.1.11/1.1.1": NOVAKOR,
    "1.1.1/1.1.12/1.1.1": RAIDING,
}
feedback = {"1.1.1/1.1.1/1.1.1": FEEDBACK_BOOK_HOME}

for name, scrolls in (("wiki.phext", wiki), ("feedback.phext", feedback)):
    data = implode(scrolls)
    back = explode(data)
    assert back == scrolls, f"round-trip mismatch in {name}: {set(back) ^ set(scrolls)}"
    path = os.path.join(OUT, name)
    with open(path, "wb") as f:
        f.write(data)
    print(f"{name}: {len(data)} bytes, {len(scrolls)} scrolls, round-trip OK")
