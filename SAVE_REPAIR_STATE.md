# Brogue save-repair state

Persistent notes for future repair work.

## Validation rule

A `.broguesave` is not considered repaired merely because the 36-byte header parses, the event stream reaches EOF cleanly, file length matches, and RNG_CHECK count equals the turn header. Those checks establish structural validity only.

A repaired save must also be replayed by the matching Brogue/O'Brien engine. Accept it only when playback reaches the target checkpoint without OUT OF SYNC / RNG mismatch, switches back to live play, and executes at least one live turn.

## 2026-10-05 findings

- `LastGame.broguesave`: 4077 turns, 22613 bytes, 4077 RNG_CHECK events, 2 SAVED_GAME_LOADED events.
- `LastGame (3).broguesave`: 6852 turns, 38463 bytes, 6852 RNG_CHECK events, 2 SAVED_GAME_LOADED events.
- The two originals share 8002 decoded events and 3716 RNG checks.
- Last common SAVED_GAME_LOADED: event 7992, byte offset 20541, after turn 3714.
- A naive turn-6200 truncation is structurally valid but engine-invalid; playback diverges around turn 3715.

## Verified checkpoint

- turn: 3714
- deepest-level header: 13
- cut length: 20541 bytes
- recording-body SHA-256: `164d1de82fdf70afbb0fb29d8be4b029e6221ec59e282f0207aa17c5863dd928`
- repaired-output SHA-256: `1942b1142e8edacd5c70e80dfdf4b429ff836e90b8326326ae14c3e5809a3c63`

Engine verification must require successful resume at turn 3714, successful continuation to 3715, `playback=0 recording=1 oos=0`, exit code 0, and no `USER_SAVE_OOS`, `Expected RNG output`, or `Playback panic`.

## Future workflow

Preserve originals; compare event streams; identify reload/divergence boundaries; generate a minimal candidate; structurally validate it; then run the exact matching engine. Do not call a repair successful until engine replay passes.


## Additional progression evidence

User-reported progression for seed 438245716:

- the run had already reached level/depth 25;
- a Dragon had been encountered.

This means the verified 3714/depth-13 checkpoint is only a safe recovery anchor, not the best-known historical progress of the run.

Also note that the longer supplied `LastGame (3).broguesave` has `deepestLevel=23` in its recording header, so the available save artifacts themselves prove progress beyond depth 13 even before considering the user's level-25/Dragon report.

Future salvage work should therefore aim to recover a later synchronized state and should not treat depth 13 or turn 3714 as the intended final endpoint.
