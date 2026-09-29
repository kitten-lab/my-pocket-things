---
crate: crate.D83F5C4965B2D0A4
title: review detective casework
---

# {{title}}
You’re not wrong — it’s one of the strangest slot machines because **the payout is prose**.

---

### What this version actually is

One HTML file + CSS. Button says **SEARCH**, not SPIN. A 5×3 grid fills with weighted symbols:

| Symbol | On-reel label | What a 4+ match does |
|--------|---------------|----------------------|
| **SP** | KEY | Advance case with a “KEY:” fragment |
| **HP** | CLUE | Advance with a “CLUE:” fragment |
| **MP** | HINT | Advance with the next case beat |
| **LP** | (dim tiles) | Don’t advance the case — change **ATMOSPHERE** and log that as a fragment |

Match rule is brutal and weird: **count ≥ 4 of the same symbol anywhere on the grid** (not paylines). Hits glow `.match`. First hit of a session opens a random case; each successful search walks `clues[]` until the case empties, then you’re back in **The Office** at night.

That’s the whole engine: **gambling cadence → detective procedural**.

---

### Why it’s strange (and good)

Normal slots: symbols → credits.  
This: symbols → **who walked in / what they said / Chester’s business card / Case Closed.**

The three cases are already your world leaking into the machine:

- *The Smudged Man* — blurred ID, keys, wallet → **ChesterImports.com**
- *The Unattended Reservation* — two glasses, one untouched, reservation for 3 with no name
- *The Man Who Never Left* — warm bed, key at the desk (shortest, almost a poem)

You don’t “win the case.” You **search until the story runs out**, then wait for the next client. That’s the reset trick your design note names explicitly: office → case → office. Episodic TV logic as slot math.

Atmosphere on LP hits is the quiet genius — rain, heartbeat, head pounding — **failure-to-progress still writes the room**. Same instinct as Forgetting House temporary fragments.

---

### Design note vs this prototype

`kitten-lab/.../detective-mystery-slot.md` is the fuller thesis: free-spin / hold-and-win constraint, two-act investigation (discover → solve), silhouette client as infinite case seed, environment + symbol pack change per case, “you never see the detective because **they are you**.”

This HTML toy is the **compressed lab**: no silhouette pipeline, no second act, no credit math — just “does SEARCHing feel like investigating?” Answer: weirdly yes, once a case latches.

Bugs/rough edges (expected for a counter toy):

- `clue_count` / `last_spin` never declared (`let`) — works as globals by accident  
- Multiple match types in one spin can advance `clueIndex` more than once  
- HP path does `getElementById(clue_count)` after bumping count — special/high styling is flaky  
- Class name typo `game-nall_spinsative` (Charlie was already in the building)  
- Body themes `casey1` / `red_lady1` / `invis_man1` exist in JS but barely in CSS

Still: as a proof, it’s sharper than half the “narrative slot” pitches that never leave a GDD.

---

### Where it sits in your shelf

| Piece | Role |
|-------|------|
| Forgetting House | Focus economy; Matter → Fragment → Story |
| Pocket Go lore deck | You *author* the cards onto rooms |
| **Detective Casework** | You *roll* for the next fragment |

Same fragment theology, different verb: **spend Focus** vs **attach lore** vs **SEARCH the reels**.

On this machine you also have later cousins — BBC `symbolCRAFT [slots]=detective-case_work`, `pageGetCaseWork`, Khaos Detective — and charlieTHREADS already treating `detective-case_work` as a high-gravity VEN. The fuller versions you mentioned live elsewhere; here you’ve got the **origin ROM**: the office, the SEARCH button, story as the jackpot.

---

### Bottom line

Strangest slot because it pays in **casework**. Not polished. Conceptually clean: waiting is the base game; a match is a client; the reel is an evidence tray; LP is mood weather; emptying the clue list is Case Closed and back to the night office.

Archive-worthy as: *prototype of narrative self-feeding loop under a casino skin* — which is also, quietly, how you’d let players “solve Matters” without admitting they’re reading.

Whenever you want next from this hole: Carl Core / Data Forester, the toy-box Forgetting House as failed translation, or we stop and you keep filing these into Pocket Go.