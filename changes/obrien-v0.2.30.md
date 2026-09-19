O'Brien Must Survive v0.2.30
============================

v0.2.30 adds a deliberately narrow three-person dialogue layer.

Dialogue authority
------------------

Only these three characters may speak in O'Brien Must Survive:

- Miles O'Brien
- Bashir
- Security Hologram / HSO

Everything else remains silent as a character. Ordinary Brogue narration,
combat text, item messages and "Killed by..." remain system narration rather
than character speech. Generic allies, ordinary Golems, monsters and summons
do not receive personality dialogue. The shared speech function also enforces a
runtime whitelist for exactly Miles, Bashir and HSO, so accidental future direct
calls with another speaker name are discarded.

Triggers
--------

- Bashir medical beam-out and return messages are now spoken by Bashir.
- HSO activation/deactivation messages are now spoken by HSO and include
  tactical state where appropriate.
- O'Brien injury dialogue triggers only when crossing 50% and 25% HP, avoiding
  per-hit chatter.
- Low-frequency ambient corridor banter can fire roughly every 240 turns while
  O'Brien is above 50% HP. It uses deterministic turn slots rather than RNG and
  adapts to which of Bashir / HSO are currently present.
- Resource dialogue warns once when the combined Fire / Lightning / Poison reserve
  becomes low, and again if the primary reserve is completely exhausted. Hysteresis
  prevents passive recharge from repeatedly retriggering the same warning.
- HSO reports integrity when crossing 50% and 25%; recovery above 75% rearms the
  warnings for a future damage cycle.
- Visible-hostile transitions can produce a short contact / all-clear exchange,
  with an 80-turn cooldown to prevent line-of-sight flicker from spamming dialogue.
- Deep-level dialogue triggers at depths 10, 15 and every depth from 20 onward.
- On player death, exactly one final line is chosen from living crew:
  Bashir first, then an active HSO, otherwise Miles.
- The final line is emitted before Brogue's native "You die..." sequence.
  No character dialogue is emitted after the death screen begins.

Replay safety
-------------

The dialogue system is cosmetic and deterministic. It does not call substantive
RNG, alter turn order, change AI, or add input events to recordings.
