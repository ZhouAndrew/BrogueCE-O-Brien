# O'Brien Must Survive v0.2.11

This repository includes a chained updater for **Brogue CE 1.15.1**. Apply the newest updater to a clean source tree; it runs all earlier O'Brien patches in order.

## v0.2.11 design

- **O'Brien Must Survive is a fourth Variant**, alongside Brogue, Rapid Brogue and Bullet Brogue.
- **Normal / Easy / Wizard remain Modes** and are independent of the selected Variant.
- The old compile-time `-DOBRIEN_BROGUE` switch is no longer used.
- O'Brien keeps normal Brogue fragility: the mod improves equipment, information, mobility and logistics rather than turning him into a tank.
- Full tricorder analysis identifies item type, enchantment, runic state and curse state in the O'Brien variant.
- Bashir is a finite-HP defensive medic, follows O'Brien, has permanent flight/levitation, and carries a finite 20/20 poison staff. He has no innate poison bolt, shield or haste ability.

## Mission-ready starting pack

O'Brien now begins with the fixed Starfleet mission kit **already in his backpack**:

- Fire staff: `20/20`
- Lightning staff: `20/20`
- Poison staff: `20/20`
- Blinking staff: `10/10`, capped at 20 spaces in this variant
- Three separate `+12 Recharging` charms using Brogue's native charm mechanics

The three Recharging charms are independent items. They are activated through Brogue's normal **Apply (`a`)** command. There is no custom `p`-key refill spell, and natural staff recharge speed remains unchanged.

The standard mission kit is no longer scattered around the first stairwell.

## Stairhead logistics

Auxiliary supplies still materialize near designated stairwells. They remain physical floor items, so normal Brogue inventory choices still matter.

- The initial stairhead cache keeps optional survival/engineering equipment rather than duplicating the fixed mission kit.
- Fire Immunity, Invisibility and Haste are no longer fixed DS9 cache supplies. They can still appear through normal Brogue random generation.
- Periodic resupply occurs every 5 depths.
- Each periodic cache includes finite battlefield-control gas: 2 poison gas, 2 paralysis gas and 2 confusion gas potions.
- No incineration potion is supplied; the Fire staff remains the ignition source.
- A life potion remains on the rarer medical cadence rather than appearing in every cache.
- Full packs refuse additional pickups normally; carried items are never auto-dropped. Remaining capacity display is clamped at zero rather than becoming negative.
- Deep water does not eject O'Brien's carried items; other variants retain normal Brogue current behavior.

Normal dungeon weapons, armor, staffs, wands, charms and other loot remain usable. O'Brien is an engineer, not a weapon-restricted class.

## Apply

Start from a clean checkout and run:

```bash
cd ~/Desktop/BrogueCE-O-Brien-src
git fetch origin
git reset --hard origin/master
python3 apply_obrien_mod_v0_2_11.py
make -B
./bin/brogue
```

No special `CPPFLAGS` are required.

Then select:

`Play -> Change Variant -> O'Brien Must Survive`

Normal, Easy or Wizard mode can still be selected independently.

## Command line

The patched build also accepts:

```bash
./bin/brogue --variant obrien_must_survive
```

or:

```bash
./bin/brogue --variant obrien
```
