O'Brien v0.2.28 updater hotfix

- Make `apply_obrien_mod_v0_2_28.py` safe on a source tree where v0.2.27 is already applied.
- Skip replaying the full historical patch chain when the v0.2.27/v0.2.28 source markers are already present.
- Print the correct source-tree launch command: `./brogue`, not `./bin/brogue`, because the root launcher changes into `bin/` so `assets/tiles.png` resolves correctly.
- CI now covers upgrading an already-patched v0.2.27 working tree to v0.2.28.
