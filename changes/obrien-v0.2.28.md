O'Brien Must Survive v0.2.28
============================

- Fix recording/save playback desync caused by the selected game variant not being stored in Brogue CE's recording header.
- Preserve the 36-byte header layout: byte 15 is now a tagged packed mode/variant field, so seed, turn, depth, length and event offsets do not move.
- O'Brien recordings made by v0.2.28 are self-describing and restore `VARIANT_OBRIEN_MUST_SURVIVE` before O'Brien-specific level initialization consumes substantive RNG.
- Legacy untagged recordings remain readable with the caller-selected variant.
- Add `repair_legacy_obrien_save.py` to tag old O'Brien `.broguesave` / `.broguerec` files without changing their event stream. The migration changes exactly header byte 15.
- No gameplay balance changes in this release.
