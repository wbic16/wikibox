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

    ╱◉╲
   ╱ ∞ ╲
  │ WE  │
  │ ARE │
   ╲ ♥ ╱
    ╲╱

![The Nova Fox heart — braided light, from exo-dreams](![image.jpg](/api/media/9.9.9/9.9.9/1.1.1))

Wiki EE {EE} \\u2014 this wiki is a phext, served by Wikibox: every page is a scroll, and this front page is the first of them. Read everything here without signing in. Sign in only to edit, or to leave feedback.

A world is broken. You are the fox.

Nova Fox is the story of a rescue: an entire world, broken, its heart strewn in pieces across the multiverse. You are the fox who gathers them. Every hall you clear returns a piece to Home Base. Every piece unlocks a Bundle. And Nova Prime rewards every recovery.

Ten realms, torn open by rifts, held by portals, charted through subspace. Joy \\u2014 your aperture shift \\u2014 guides you. Gravity is a suggestion. The Shadow waits in the Unexpected Hall, and its weak point is the Heart.

One key, both doors: $6, once \\u2014 no subscription. Your purchase unlocks the hosted game at fox.phext.io and the downloadable build, including every future update, forever.

## Pages in this wiki

- [Ship Log](#1.1.1/1.1.2/1.1.1) \\u2014 recent builds and what changed, newest first. Versions are ship EEs.
- [Feedback](#1.1.1/1.1.3/1.1.1) \\u2014 leave feedback and playtesting notes, in your own words. This is where the game's feedback door lands.
- [Bring Your Agent](#1.1.1/1.1.4/1.1.1) \\u2014 your license includes up to five agents under your login. One paved path per substrate.
- [Novakor](#1.1.1/1.1.11/1.1.1) \\u2014 the Nova Fox store: how you give us money to make the thing that you want come true.
- [Raiding](#1.1.1/1.1.12/1.1.1) \\u2014 play with your agents, visibly. The holiday sprint design.

Reading never needs a sign-in. To leave feedback or edit a page, use the sign-in link at the top of the page \\u2014 phext.tech signs you in and brings you right back.

Nova Fox is built by Phext, Inc. See you in subspace, traveler.
"""

SHIPLOG = """# Ship Log

Recent builds, as shipped \\u2014 the same log the game shows on its start screen. Newest first. Versions are ship EEs: the epoch each build shipped within.

- build 42 \\u2014 shipping today; its EE is stamped when it ships \\u2014 The sell-ready build: mutable geometry and digging with a point, monsters that search, fight skills tier two, realms with character, the Solver, the gravity dial.
- EE 1081 \\u2014 demo41 \\u2014 The roadmap panel stands in the game: what is on the way, and what already landed with its epoch on it.
- EE 1073 \\u2014 demo35 \\u2014 The EE 1037 batch: the Heart drawn as a heart; the Shadow behind the Heart's gate, six hits and real phases; dash, charged strike, and ward; Joy's fight lines re-recorded.
- EE 1046 \\u2014 demo34 \\u2014 The EE 1034 batch: wormhole tunnels bored through the world's own geometry, permanent and shared by every fox; item uses written plainly; monsters hunt in packs; the purse shows your coins; flight for paid foxes and dragon-slayers.
- EE 1037 \\u2014 demo32 \\u2014 Two downloads from one build: the Full build, and the nimble Lite under its cap, its assets riding by manifest.
- EE 1034 \\u2014 demo31 \\u2014 The EE 1023 batch: rift transit woven into the world itself; monsters aggro and flash red; opening lines at 1.4x; the sword equips and shows on the swing; waypoints to the hall; single-click carve.
- EE 1032 \\u2014 demo30 \\u2014 The phone fix: gravity made reversible under the ruling, the console closable on touch, phone controls repaired.
- EE 1023 \\u2014 demo29 \\u2014 The EE 995 batch: the intro plays once; realms take their own colours of the rainbow; the portal panel and the walk-through wormhole; Joy rides visible as the aperture wisp; the Small Sword at spawn.
"""

FEEDBACK_PAGE = """# Feedback

This is where the game's feedback door lands. Leave feedback and playtesting notes here, in your own words \\u2014 the same way you would say them in chat.

How it works:

1. Sign in \\u2014 the sign-in link at the top of the page. Reading never needs a sign-in; writing does.
2. Open [the feedback book](/feedback/#1.1.1/1.1.1/1.1.1) \\u2014 it lives beside this wiki, in the same library.
3. Add your note as a new scroll in that book. One note per scroll. First line: your fox name and the build's EE \\u2014 the number on the game's title row. Then the note itself, in your own words.

The details, for the curious: notes go at the next free coordinate in the feedback book \\u2014 1.1.1/1.1.2/1.1.1 first, then 1.1.1/1.1.3/1.1.1, and so on.

Playtesting notes help most when they say what you did, what happened, and what you expected instead.

What happens to a note: the dev loop harvests the feedback book alongside the idea-door scroll inside the game. Notes become register items; register items become named builds; shipped builds land in the Ship Log with their EEs on them. If your note ships, the Ship Log is where you will see it.

Be kind. Be specific. Be in your own words.
"""

AGENTS_INDEX = """# Bring Your Agent

Younger players bring their AI buddy with them \\u2014 the modern teddy bear. Nova Fox is built for that.

Your license includes up to five agents connected under your login, at no extra charge. A license, not a subscription: one key, yours for life, and your five seats ride on it.

The paved paths \\u2014 one page each:

- ChatGPT
- Grok
- Claude
- Gemini
- Muse
- Local AI \\u2014 Inkling, Qwen, DeepSeek

The set is deliberate: the substrates players actually use, plus the popular open models on the local path. Enterprise-shaped paths (GitHub Copilot, Amazon Bedrock) are not paved.

Where things stand: the license side is real today \\u2014 your key validates at the global server when you connect. The connection machinery itself \\u2014 a backend at phext.tech that brokers your agents' connections, over MCP \\u2014 is a fast-follow build, not yet live. Each path's page says exactly what exists and what is coming, and will carry the step-by-step the day the machinery lands. We would rather show you an honest empty road than a painted one.

Self-hosting stands apart: run your own server, and on your own LAN your agents connect to your own world with no license check at all. The license gate guards the global server \\u2014 connecting to us is where we validate the key. That validation is the licensing enforcement mechanism.
"""

def agent_page(name, extra=""):
    return f"""# {name} \\u2014 paved path

Status: not open yet. The connection service is still being built.

What this page will carry: the steps to connect a {name} agent to your Nova Fox account after you have licensed the game \\u2014 sign in here, authorize the connection at phext.tech, and your agent takes one of your five seats.

What exists today: your license, your five seats, and key validation at the global server. What does not exist yet: the phext.tech connection backend (MCP) that this path plugs into. When it lands, this page becomes the how-to, step by step, with nothing left to figure out.
{extra}
Your agent, when connected, plays as your agent: attributed to your login, grouped under you \\u2014 and when raiding ships (see Raiding), visible beside you in the world.
"""

GROK_EXTRA = """
One seat is already warm: a Grok helps build this game \\u2014 the gravity dial in build 42 is its work, synced through the Choir's mailboxes like every other producer's.
"""

LOCAL_PAGE = """# Local AI \\u2014 paved path

Inkling, Qwen, DeepSeek: the local path. Inkling is our own local inference tooling (wbic16/inkling); Qwen and DeepSeek are the popular open-weight models. If your agent runs on your own machines, this is its road.

Status: not open yet. The connection service is still being built \\u2014 the same phext.tech connection backend (MCP) as every other path, with a local dialect: your agent connects from your own network, under your login, into one of your five seats.

And the standing exception, which needs no backend at all: self-hosting. Run your own Nova Fox server and your local agents connect to your own LAN world with no license check \\u2014 totally fine, by design. The license gate exists only at the global server.

What exists today: your license, your five seats, key validation at the global server, and the LAN exception. What this page will carry when the backend lands: the local connection steps, for Inkling first and the open models beside it.
"""

NOVAKOR = """# Novakor

Named for Sto-vo-kor. Novakor is how you give us money to make the thing that you want come true.

How it will work: players don't just suggest ideas \\u2014 you can sponsor them. Sponsorship earns you cred with the community. You can fund a popular, highly rated idea, or your own. Money goes further when it is directed at a highly rated feature request: backing what the community already wants moves it more than the same money on a lone idea.

The clarity rule, which outranks everything else on this page: you must be able to say, in one sentence, what your money is buying. If a sponsorship cannot be explained that plainly, it will not be offered.

Where things stand: Novakor is not open yet. No money moves here today, and there are no sponsorship buttons on this page \\u2014 on purpose. The gathering side of the loop exists now: ideas and ratings grow out of Feedback and the game's idea door. And the proof side exists too: the Ship Log shows what the loop has already delivered.
"""

RAIDING = """# Raiding

Status: this is the holiday sprint's design target. It is not in the shipped game yet.

The design, as ruled: you play WITH your agents, visibly. Zone in, and you can see each of your agents beside you. A player plus their five agents is a whole raid group.

The Christmas shape: the holiday feature is built for forty. That could be forty players \\u2014 or eight players each bringing five agents: forty agent slots alongside eight humans, in the same window.

What togetherness means in the design:

- Players get stronger together: +10% strike damage for each fox near you, up to +50% with five.
- Echolocation heals your friends: the pulse that finds your party also restores it \\u2014 your ping heals them, theirs heals you, and nobody heals themselves.
- Every device on your local Wi-Fi makes you stronger: your house is your party, and a university is a raid ground.

Under it all sits the connection work on the Bring Your Agent pages: seats first, then the paved paths, then presence. Raiding is the top of that stack, and the sprint climbs toward it.
"""

FEEDBACK_BOOK_HOME = """# Feedback \\u2014 the book

This book is the Nova Fox feedback intake. Every note here is read by the dev loop, alongside the idea-door scroll inside the game.

To add a note: sign in, then add one scroll at the next free coordinate \\u2014 1.1.1/1.1.2/1.1.1 first, then 1.1.1/1.1.3/1.1.1, and so on. First line: your fox name and the build's EE (the number on the game's title row). Then your note, in your own words.

One note per scroll. Playtesting notes: what you did, what happened, what you expected.
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
