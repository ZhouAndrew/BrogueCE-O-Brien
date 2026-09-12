# O'Brien Must Survive v0.2.14

This repository includes a chained updater for **Brogue CE 1.15.1**. Apply the newest updater to a clean source tree; it runs all earlier O'Brien patches in order.

## v0.2.14 design

- **O'Brien Must Survive is a fourth Variant**, alongside Brogue, Rapid Brogue and Bullet Brogue.
- **Normal / Easy / Wizard remain Modes** and are independent of the selected Variant.
- The old compile-time `-DOBRIEN_BROGUE` switch is no longer used.
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
- Three separate `+12 Recharging` charms using Brogue's native charm mechanics
- Ring of Regeneration: `+3`, automatically equipped
- Ring of Wisdom: `+3`, automatically equipped

The two mission rings occupy Brogue's normal two ring slots from turn zero. They are not permanently locked: the player can later replace them using normal Brogue equipment rules. Regeneration improves between-fight recovery without adding armor or extra maximum HP, while Wisdom supports the staff-heavy engineering loadout through Brogue's native ring mechanics.

Tunneling is treated as a core engineering tool and no longer has to be collected from the first stairhead cache. The three Recharging charms are independent items and can recharge Tunneling under Brogue's normal native Recharging behavior. They are activated through Brogue's normal **Apply (`a`)** command. There is no custom `p`-key refill spell, and natural staff recharge speed remains unchanged.

The standard mission kit is no longer scattered around the first stairwell.

## Stairhead logistics

Auxiliary supplies still materialize near designated stairwells. They remain physical floor items, so normal Brogue inventory choices still matter.

- The initial stairhead cache keeps optional survival supplies but no longer duplicates Tunneling, the primary mission staffs, Recharging charms, or the two mission rings.
- The full 3x3 area centered on the stair anchor is reserved as an item-free exit zone for O'Brien's DS9 cache. The player is not forced to step across supplied equipment just to leave the stairhead.
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
python3 apply_obrien_mod_v0_2_14.py
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
