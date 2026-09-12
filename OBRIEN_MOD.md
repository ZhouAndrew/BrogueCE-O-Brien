# O'Brien Must Survive v0.2.16

This repository includes a chained updater for **Brogue CE 1.15.1**. Apply the newest updater to a clean source tree; it runs all earlier O'Brien patches in order.

## v0.2.16 design

- **O'Brien Must Survive is a fourth Variant**, alongside Brogue, Rapid Brogue and Bullet Brogue.
- **Normal / Easy / Wizard remain Modes** and are independent of the selected Variant.
- O'Brien keeps normal Brogue fragility: the mod improves equipment, information, mobility and logistics rather than turning him into a tank.
- Full tricorder analysis identifies item type, enchantment, runic state and curse state in the O'Brien variant.
- Bashir is a finite-HP defensive medic, follows O'Brien, has permanent flight/levitation, and carries a finite 20/20 poison staff. He has no innate poison bolt, shield or haste ability.

## Mission-ready starting pack

O'Brien begins with the fixed Starfleet mission kit **already in his backpack**:

- Fire staff: `20/20`
- Lightning staff: `20/20`
- Poison staff: `20/20`
- Blinking staff: `10/10`, capped at 20 spaces in this variant
- Tunneling staff: `3/3`
- Three separate **Starfleet Emergency Power Cells**, each `20/20`
- Ring of Regeneration: `+3`, automatically equipped
- Ring of Wisdom: `+3`, automatically equipped

The two mission rings occupy Brogue's normal two ring slots from turn zero. They are not permanently locked: the player can later replace them using normal Brogue equipment rules.

## Starfleet Emergency Power Cells

The old three `+12 Recharging` charms have been replaced in the O'Brien variant by finite high-discharge emergency batteries.

Each Power Cell stores **20 charge-units**. Applying a Cell lets O'Brien choose one staff and immediately transfer up to 20 units to it. Only the energy actually needed is consumed: a Fire staff at `13/20` uses 7 Cell units, a Blinking staff at `0/10` uses 10, and a Tunneling staff at `1/3` uses 2.

This is intentionally a high-discharge / slow-recovery system. A Cell passively recovers only **1 charge-unit per 100 turns**, so a completely empty Cell requires about 2000 turns to return to `20/20`. This slow recovery is based only on elapsed player time: **Wisdom does not accelerate it, and Reaping does not feed it**. Wisdom continues to improve the normal recharge rate of staffs themselves.

A **Scroll of Recharging** is treated as an external high-power recharge source. In the O'Brien variant it still performs Brogue's normal staff/charm recharge behavior, but it also fills every Starfleet Emergency Power Cell in the pack directly to `20/20`. Thus the player can occasionally find a genuine logistics reset in the dungeon without turning the Cells into self-sustaining reactors.

In other Brogue variants, Recharging charms retain their original native behavior.

## Stairhead logistics

Auxiliary supplies still materialize near designated stairwells. They remain physical floor items, so normal Brogue inventory choices still matter.

- The **initial stairhead cache includes one emergency Scroll of Recharging**. It is intentionally floor-staged instead of preloaded in O'Brien's backpack, serving as a one-shot high-power reserve if the opening mission turns into a severe engagement.
- That emergency scroll does **not** repeat in the five-depth periodic caches; additional Scrolls of Recharging must come from normal dungeon generation.
- The initial stairhead cache keeps optional survival supplies but no longer duplicates Tunneling, the primary mission staffs, Power Cells, or the two mission rings.
- The full 3x3 area centered on the stair anchor is reserved as an item-free exit zone. The player is not forced to step across supplied equipment just to leave the stairhead.
- If a particular supply item cannot be placed outside that clear zone, it is omitted rather than violating the clear-lane rule.
- Fire Immunity, Invisibility and Haste are no longer fixed DS9 cache supplies. They can still appear through normal Brogue random generation.
- Periodic resupply occurs every 5 depths.
- Each periodic cache includes finite battlefield-control gas: 2 poison gas, 2 paralysis gas and 2 confusion gas potions.
- No incineration potion is supplied; the Fire staff remains the ignition source.
- A life potion remains on the rarer medical cadence rather than appearing in every cache.
- Full packs refuse additional pickups normally; carried items are never auto-dropped. Remaining capacity display is clamped at zero rather than becoming negative.
- Deep water does not eject O'Brien's carried items; other variants retain normal Brogue current behavior.

Normal dungeon weapons, armor, staffs, wands, charms, rings and other loot remain usable. O'Brien is an engineer, not a weapon-restricted class.

## Apply

Start from a clean checkout and run:

```bash
cd ~/Desktop/BrogueCE-O-Brien-src
git fetch origin
git reset --hard origin/master
python3 apply_obrien_mod_v0_2_16.py
make -B
./brogue
```

Use the repository's `./brogue` launcher rather than running `./bin/brogue` from the repository root. The launcher changes into `bin/` first so the game can find `bin/assets/tiles.png` correctly.

No special `CPPFLAGS` are required.

Then select:

`Play -> Change Variant -> O'Brien Must Survive`

Normal, Easy or Wizard mode can still be selected independently.

## Command line

For command-line variant selection, run from the repository root through the launcher:

```bash
./brogue --variant obrien_must_survive
```

or:

```bash
./brogue --variant obrien
```
