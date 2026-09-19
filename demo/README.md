# Built-in 3727-turn O'Brien historical save demo

This directory now contains both the exact historical save and the fully recovered save:

- `OBrien_3727turn_longsave_backup.broguesave` — immutable historical source/evidence.
- `OBrien_3727turn_recovered.broguesave` — fully recovered, clean-v0.2.28-compatible save.

The historical source is deliberately preserved and is **not** modified in place.

## Historical source identity

- Size: **20,507 bytes**
- SHA-256: `dadc44db70a6b029e7be9dee422acc96d9a6b9063837c897305c335ee444b76d`
- Recording header: `CE 1.15.1`
- Variant/mode byte: `0xb0` (tagged O'Brien variant, normal mode)
- Seed: **436566627**
- Header turn count: **3727**
- Header level-change count: **14**
- Recorded file length: **20,507**

The repository also keeps seven Base64 source chunks (`save.b64.part00` ... `part06`).
`materialize_save.py` reconstructs the historical binary and refuses to continue if any identity check changes.

## What was wrong with the historical recording

The game state was recoverable. Two O'Brien actions had incomplete recording logic:

- **37 successful Security Hologram `C` actions** consumed real turns and wrote their normal RNG checkpoints, but omitted the initiating `C` input events.
- **Four Emergency Power Cell uses** recorded `a + cell-letter` but omitted the selected target staff. Deterministic replay recovered the target sequence:
  - turn 1922: cell `l` -> staff `e`
  - turn 2785: cell `m` -> staff `f`
  - turn 3326: cell `l` -> staff `g`
  - turn 3385: cell `n` -> staff `e`

No RNG checkpoint is removed, changed, skipped, fabricated, or re-locked.

## Fully recovered save identity

`OBrien_3727turn_recovered.broguesave`

- Size: **20,630 bytes**
- SHA-256: `6ec2dd4a57b9dac8015b09cc84004ffd499d5e50a5ef59be162f3b7dae5138c0`
- Seed: **436566627**
- Header turns: **3727**
- Deepest level: **14**
- Inserted events: **41 KEYSTROKE records** (37 Security `C` + 4 Power Cell targets)

Every event and RNG checkpoint already present in the historical file remains in its original order.

## Reproduce the recovery

The exact reconstruction used for the checked-in recovered save is:

```bash
python3 tools/recover_obrien_3727_save.py \
  demo/OBrien_3727turn_longsave_backup.broguesave \
  demo/OBrien_3727turn_recovered.broguesave
```

The recovery tool is hash-locked to the known historical source and also checks the exact recovered SHA-256.

`repair_legacy_obrien_save.py` remains the production one-time legacy migration helper used with v0.2.29.

## Strict verification

The recovered save was independently reconstructed and loaded by **two separate GitHub Actions runners**, each compiling an untouched O'Brien **v0.2.28** replay engine.

Both clean-engine verification jobs reached `switchToPlaying()` with:

```text
turn=3727
depth=14
hp=40
gameHasEnded=0
playbackOOS=0
```

Both jobs emitted `CLEAN_VERIFY_PASS`.

This is stronger than an RNG-compatible/relock test: the verifier fails immediately on `playbackPanic()`, and the clean v0.2.28 engine contains no forensic replay shim.

## Future recordings

Production `apply_obrien_mod_v0_2_29.py` fixes both recorder defects:

- successful Security Hologram toggles record `C` before the turn RNG checkpoint;
- Emergency Power Cell transfers record the chosen target staff.

Production playback remains strict: no RNG scanning, checkpoint skipping, or synthetic-turn compatibility layer is required.
