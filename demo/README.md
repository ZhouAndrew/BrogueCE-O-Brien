# Built-in 3727-turn O'Brien historical save demo

This branch contains the exact historical save used by the replay-forensics work:

`OBrien_3727turn_longsave_backup.broguesave`

The checked-in fixture is deliberately preserved as evidence. It is **not** modified in place.

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
`materialize_save.py` reconstructs the binary and refuses to continue if any identity check changes.

## What was wrong with the historical recording

The game state itself was recoverable. Two O'Brien actions had incomplete recording logic:

- 37 successful Security Hologram `C` actions consumed turns and wrote their normal RNG checkpoints, but omitted the `C` input events.
- Four Emergency Power Cell uses recorded `a + cell-letter` but omitted the selected target staff. Exhaustive replay uniquely recovered the target sequence as `e, f, g, e`.

No RNG checkpoint needs to be skipped or rewritten.

## Deterministic repair

`repair_legacy_obrien_save.py` recognizes the historical source **only by its exact SHA-256**. For that file it inserts exactly the missing 41 keystroke events and updates the header file-length field.

Verified repaired identity:

- Size: **20,630 bytes**
- SHA-256: `6ec2dd4a57b9dac8015b09cc84004ffd499d5e50a5ef59be162f3b7dae5138c0`
- Header turns: **3727**
- Deepest level: **14**

Every pre-existing event and RNG checkpoint remains in original order.

## Run it

Build the production v0.2.29 ruleset:

```bash
python3 apply_obrien_mod_v0_2_29.py
make -B
./demo/run-demo.sh
```

`run-demo.sh` first verifies/materializes the historical fixture, then creates a repaired disposable copy under `/tmp` and launches that copy. The historical source file remains untouched.

You can also create the repaired save manually:

```bash
python3 demo/materialize_save.py
python3 repair_legacy_obrien_save.py \
  demo/OBrien_3727turn_longsave_backup.broguesave \
  --output /tmp/OBrien_3727turn_repaired.broguesave
```

## Verified result

A strict replay using the clean v0.2.29 production ruleset reaches:

```text
turn=3727
depth=14
deepest=14
hp=40/40
ended=0
oos=0
```

The production engine contains no RNG relock, checkpoint skipping, or synthetic-turn playback shim. The repair is entirely in the one-time, hash-locked migration.
