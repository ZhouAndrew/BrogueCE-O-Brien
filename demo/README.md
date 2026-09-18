# Built-in 3727-turn O'Brien historical save demo

This branch contains the exact historical save used by the replay-forensics work:

`OBrien_3727turn_longsave_backup.broguesave`

The fixture is deliberately preserved as evidence. It is **not** a repaired save.

## Identity

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

## Run it

For an O'Brien v0.2.28 source tree:

```bash
python3 apply_obrien_mod_v0_2_28.py
make -B
./demo/run-demo.sh
```

`run-demo.sh` always launches a disposable runtime copy. The checked-in historical save is not modified by gameplay.

You can also reconstruct/verify the fixture without launching Brogue:

```bash
python3 demo/materialize_save.py
```

## Expected behavior

This demo exists to reproduce the historical incompatibility we are investigating. It does **not** claim that clean v0.2.28 can replay the file successfully to turn 3727.

Known forensic facts at the time this demo branch was created:

- clean historical v0.2.23/v0.2.28 agrees through the early recorded checkpoint `90`;
- the next recorded checkpoints are `11` and `24` with no intervening recorded KEY/MOUSE event;
- forcing a normal extra `playerTurnEnded()`, a descent, or a fall does not reproduce checkpoint `11`;
- therefore the save remains a useful exact fixture for reconstructing the dirty historical execution path.

Do not replace this fixture with a re-encoded or RNG-bypassed file. A future repaired save should be added under a different filename and should pass the separate clean-v0.2.28 acceptance test.
