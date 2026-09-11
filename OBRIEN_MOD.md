# O'Brien Must Survive v0.2

This repository now includes `apply_obrien_mod.py`, which converts a **clean Brogue CE 1.15.1 source tree** into the O'Brien Must Survive v0.2 build.

## v0.2 design

- **O'Brien Must Survive is a fourth Variant**, alongside Brogue, Rapid Brogue and Bullet Brogue.
- **Normal / Easy / Wizard remain Modes** and are independent of the selected Variant.
- The old compile-time `-DOBRIEN_BROGUE` switch is no longer used.
- O'Brien and Bashir are explicitly male for pronoun generation, preventing immersion-breaking text such as `her enemies`.
- Mission equipment is **materialized on the floor around the entry stairwell**. The player chooses what to pick up; supplies are never force-inserted into the pack.
- Periodic DS9 resupply is delivered at the stairwell every 5 depths.
- Resupply is biased toward **survival, escape, food and ammunition**. It deliberately does not hand out stockpiles of caustic gas, paralysis, confusion or incineration potions.
- A life potion is only included in every second periodic cache, so resupply does not become an unlimited permanent-HP fountain.
- Inventory UI clamps remaining capacity to zero, and the O'Brien supply system itself respects normal Brogue inventory capacity by leaving excess choices on the floor.

## Apply

Start from a clean checkout. Do not apply v0.2 on top of the old v0.1.x `OBRIEN_BROGUE` source patch.

```bash
cd ~/Desktop/BrogueCE-O-Brien
python3 apply_obrien_mod.py
make -B
./brogue
```

No special `CPPFLAGS` are required.

Then select:

`Play -> Change Variant -> O'Brien Must Survive`

and independently choose Normal, Easy or Wizard from `Change Mode`.

## Command line

The patched build also accepts:

```bash
./bin/brogue --variant obrien_must_survive
```

or the short alias:

```bash
./bin/brogue --variant obrien
```
