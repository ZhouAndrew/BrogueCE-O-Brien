O'Brien Must Survive v0.2.29
============================

- Fix Call Security / Security Hologram recording: every successful `C` action is now written to the recording before the turn's normal RNG checkpoint.
- Fix Emergency Power Cell recording: the selected target staff letter is now recorded after `a + cell-letter`, so playback can reproduce the nested inventory choice.
- Keep production playback strict. v0.2.29 does **not** scan RNG, skip checkpoints, synthesize hidden turns, or suppress out-of-sync failures.
- Extend `repair_legacy_obrien_save.py` with a SHA-256-locked migration for the exact historical 3727-turn save:
  - source identity: `dadc44db70a6b029e7be9dee422acc96d9a6b9063837c897305c335ee444b76d`;
  - inserts exactly 37 missing `C` keystroke events;
  - inserts exactly four missing Power Cell target events, uniquely recovered as `e, f, g, e`;
  - preserves every pre-existing event and RNG checkpoint in original order;
  - updates only the recording-length header field after insertion.
- The repaired historical save is 20,630 bytes with SHA-256 `6ec2dd4a57b9dac8015b09cc84004ffd499d5e50a5ef59be162f3b7dae5138c0`.
- Strict replay of the repaired save on a clean v0.2.29 ruleset reaches turn 3727 at depth 14 with O'Brien alive at 40/40 HP and no playback OOS.
