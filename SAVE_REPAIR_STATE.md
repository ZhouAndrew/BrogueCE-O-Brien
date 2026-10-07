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


## Withdrawn depth-23 candidate (2026-10-05)

The former claim that `RECOVER_D23_T5811_VERIFIED.broguesave` was a verified depth-23 recovery is **withdrawn**.

The user's actual Desktop GUI executable (`CE 1.15.1-dev.67a1970.master`, O'Brien v0.2.37) replayed that file and displayed `OUT OF SYNC` at turn 3715/5811 while still on depth 13. Therefore the earlier probe/headless acceptance was not an authoritative engine verification.

Authoritative validation rule from now on:

- use the actual executable from `Desktop.zip` (or demonstrably bit-identical game logic);
- replay the candidate from the beginning;
- require no RNG/playback OOS;
- require the target depth/state to be reached;
- reload the produced candidate and execute at least one live turn.

The turn-5811/depth-23 candidate must not be used as a recovery checkpoint.



## 2026-10-07 continuation: 3715 root cause narrowed and replay pushed to turn 4746

Using the source tree that builds the same `CE 1.15.1-dev.67a1970.master / O'Brien v0.2.37` gameplay logic as the Desktop binary, the turn-3715 failure was reproduced exactly:

`Expected RNG output of 93; got 209.`

A compatibility experiment showed that the v0.2.37 legacy Strength-clock phase must **not** be reapplied at the second historical save boundary near turn 3714. The first historical `SAVED_GAME_LOADED` boundary still needs legacy phase 40 to preserve the known-good prefix, but the later boundary must rebase the process-local Bashir Strength clock to the current absolute turn.

With this boundary-specific behavior, strict replay no longer fails at 3715. It proceeds through depths 13-16 and reaches:

`turn 4746 / depth 16`

before the next deterministic divergence:

`Expected RNG output of 123; got 33.`

At that point the forensic state was:

- playerTurn=4746
- absoluteTurn=4725
- Bashir last Strength-potion clock=3696
- Bashir return timer=0
- Security Hologram Lightning charges=3
- Security Hologram Poison charges=2
- Security recharge clock=4712
- Security suspended=false
- stored Security integrity=180

This proves that the 3715 defect is not the only compatibility defect, but it also proves the repair path is working: the first blocker was pushed forward by more than 1000 turns without rewriting the user's input history.

A naïve strategy that ignores historical RNG checks and simply replays the post-3714 user inputs as fresh live input is **not** acceptable: it diverges behaviorally, reaches only depth 15, and dies at turn 4114. Therefore future work should keep strict replay and reconstruct missing historical process state rather than regenerate a new trajectory.

Current next blocker: explain and reproduce the state transition that first becomes observable at turn 4746 / depth 16, likely around O'Brien process-local ally/runtime state rather than the already-fixed Bashir Strength clock.


## 2026-10-07 continuation: turn-4746 blocker localized

Further strict-replay work narrowed the next blocker substantially.

### Control result

With the boundary-specific Strength-clock fix, the shorter `LastGame.broguesave` branch replays cleanly all the way to its end:

- turn 4077
- depth 14
- deepest 14
- HP 50/50
- no RNG OOS

This is important: the second historical load boundary repair is not globally corrupting replay. The longer branch has an additional later compatibility defect.

### Exact v0.2.35 is not the answer

A clean Brogue source tree rebuilt by applying the O'Brien updater chain only through v0.2.35 does **not** replay the long save. It diverges at approximately:

- turn 2012
- depth 7
- expected RNG 28, got 60

Therefore the long recording is not simply "a v0.2.35 recording that should be opened with a v0.2.35 binary". Later compatibility behavior is genuinely required.

### Removing the second SAVED_GAME_LOADED is insufficient

Deleting only the second historical `SAVED_GAME_LOADED` byte makes unmodified v0.2.37 pass the old 3715 failure, but it then diverges around turn 4060. This is consistent with the Bashir Strength clock no longer being rebased at the second load: the old fabrication phase eventually becomes observable again. So the load event cannot simply be deleted.

### Turn 4746 details

The longer branch remains strictly synchronized through turn 4745. The first later mismatch occurs at the RNG checkpoint written after the recorded `h` movement at turn 4746:

- player action: `h`
- depth: 16
- absolute turn: 4725
- expected RNG checkpoint: 123
- current replay: 33

Instrumentation showed 558 substantive RNG calls in this turn. The tail is dominated by `paintLight()`, especially luminescent-fungus terrain lights and a few wall torches.

A diagnostic that suppresses the final group of terrain-light RNG calls can make the **4746 checkpoint itself** equal the historical 123, but the very next checkpoint (4747) still diverges. Therefore "skip some lighting RNG" is only an audit alignment trick, not a valid repair.

The extra glowing terrain was already present before the turn-4746 input, so it was not newly spawned on that turn. The current working hypothesis is that some latent game-state difference becomes behaviorally observable on turn 4746 and changes the lighting/environment/monster update path. The root cause has not yet been proven.

### Current repair rule

Do not patch the RNG byte at 4746 and do not suppress lighting merely to make one checkpoint green. Any accepted fix must carry synchronization into following turns and eventually into a loadable depth-23 save.
