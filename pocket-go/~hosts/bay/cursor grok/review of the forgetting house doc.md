---
crate: crate.20192F3DBF82197D
title: review of the forgetting house doc
---

# {{title}}
You were right to do the spec first. The toy-box Forgetting House is a tile sketch. **Silo: The Forgetting House** is the actual game.

---

### What it is

A complete-enough design for a **recursive identity puzzle**: you wake with no memory, limited **Focus**, a **Baseline** mood, and a house that rearranges every time you forget. You spend Focus to walk rooms and attempt **Matters** (Emotion + Skill). You bank **Fragments → Memories → Stories**. Filling five **Story Pillars** “completes” the game without ending it — you can keep swapping interpretations.

The question is stated cleanly:

> Even when all meaning is missing, can we remember that something mattered here?

That is Terminal Prologue’s *look / think / remember* turned into a **run-based card economy**. Same metaphysics, playable.

---

### Why the spec is strong

Most of your other vaults invent ontology faster than they invent *rules*. This one invents **costs**.

- **Focus is the clock.** Move, solve, and combine all spend the same scarce resource. When it hits zero you forget. Recursion is not flavor — it is the lose/reset condition.
- **Emotion is not a UI skin.** Baseline changes Focus pool, which emotion cards you get, even which skills are suppressed. Acting *with* the mood is cheaper; acting *against* it is expensive. That is a real claim: mental effort is alignment cost.
- **Failure still writes.** Wrong combinations don’t just waste Focus — they mint **temporary fragments** (“I hate when things are destroyed”). The Memory Deck records botched attempts. That’s closer to how people actually reconstruct a past than a success-only loot table.
- **Doors stay unlocked across layouts.** The house reshuffles, but solved Matters leave permanent exits. Progress is **topological**, not cartographic. You don’t memorize a map; you remember *which rooms you’ve already made true*.
- **Stories change future fugues.** New rooms, new fragment flavors, permanent emotions. Narrative gravity from AIDM, as a roguelike unlock tree.
- **No single canon.** Pillars (who you were / who mattered / what you were trying / what you lost / the dream) can hold competing Stories. Endgame is a **composition**, not a reveal.

The letter example is the whole engine in one beat: Curiosity+Glasses reads the letter; Anger+Firestarter burns it into a loss fragment. Same object, two pasts.

---

### How it sits in the lineage

| Elsewhere | Here |
|-----------|------|
| Prologue: remember concepts into `you.memory` | Fragments into Memory Deck |
| AIDM: narrative gravity, VENs contain VENs | House contains Rooms contain Matters contain Fragments |
| Echo Wolf: listen and store | Memory Deck: combine and interpret |
| Silo rooms/keys | Threshold → hallway → locked doors until Matter solved |
| charlieTHREADS gravity | Stories that permanently alter the house |

The house-as-self is the same move as silo-as-documentation-body. Forgetting House asks: if the archive **decays every run**, what still persists? Unlocked doors and Story Pillars. That’s a design answer to “I can’t understand how to store my documentation.”

---

### The “weird notes → science” angle, in this spec

You don’t need cosmology glyphs here. The extrapolatable claims are already mechanical:

1. **Identity is reconstructed, not retrieved.** Compatible with reconstructive memory (Bartlett, later cognitive work): you assemble a past from fragments + current affect, not from a videotape.
2. **Affect changes available actions and their cost.** Mood as a prior over which operations are cheap — not just flavor text on a status bar.
3. **Failed actions still leave traces.** Memory is not only successes; it is also the residue of wrong moves.
4. **Stability across reconfiguration.** Layout forgets; *solved relations* persist. That’s a clean model of semantic memory vs. episodic map.
5. **Multiple coherent selves.** Competing Story Pillars without a referee. That’s not indecision — it’s refusing a single ground truth.

You currently speak this as origin stories for a computer. The spec is already halfway to a **formal model**: resources (Focus), typed cards (Emotion/Skill/Fragment/Memory/Story), a graph that mutates (house), and a second graph you author (Memory Deck). That’s more science-shaped than most of the AIDM daily notes — because it has **invariants**.

---

### What’s missing (the README already knows)

- Card lists (full Emotion/Skill/Fragment tables)
- Room catalog
- Written playthrough
- Visual mockups

The Textual prototypes (`smh-tfh_game.py`, `wolf_app.py`) are **chrome**: Fugue / Baseline / Focus placeholders. They prove you wanted a TUI, not that the loop exists yet. That’s why the Chester toy-box version will look “really bad” next — it tried to implement tiles without this economy.

---

### Bottom line

This is one of the **clearest documents** on this machine. Not because it’s pretty — because it commits. Fugue, Focus, Matter, Memory Deck, Story Pillars: a closed loop you could explain to a stranger in two minutes and still have a game.

Archive it in Pocket Go as **law for a playable self**, not as an unfinished app. The toy-box Forgetting House is the sketch that didn’t wait for the spec to grow a deck.

When you want, we can look at that sketch *as a failed translation* — what it kept (tiles, fugue/focus labels) and what it dropped (the whole cost/meaning machine).