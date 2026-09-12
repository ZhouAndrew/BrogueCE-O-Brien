# O'Brien Must Survive v0.2.21

This repository includes a chained updater for **Brogue CE 1.15.1**. Apply the newest updater to a clean source tree; it runs all earlier O'Brien patches in order.

## v0.2.21 design

- **O'Brien Must Survive is a fourth Variant**, alongside Brogue, Rapid Brogue and Bullet Brogue.
- **Normal / Easy / Wizard remain Modes** and are independent of the selected Variant.
- O'Brien keeps normal Brogue fragility: the mod improves equipment, information, mobility and logistics rather than turning him into a tank.
- Full tricorder analysis identifies item type, enchantment, runic state and curse state in the O'Brien variant.
- Bashir is a finite-HP defensive medic, follows O'Brien, has permanent flight/levitation, and carries a finite 20-shot poison staff. He has no innate poison bolt, shield or haste ability.

## Mission-ready starting pack

O'Brien begins with the fixed Starfleet mission kit **already in his backpack**:

- Fire staff: `20/20` storage, native Brogue `+3` effect/recharge level
- Lightning staff: `20/20` storage, native Brogue `+3` effect/recharge level
- Poison staff: `20/20` storage, native Brogue `+3` effect/recharge level
- Blinking staff: `10/10`, capped at 20 spaces in this variant
- Tunneling staff: `3/3`
- Three separate **Starfleet Emergency Power Cells**, each `20/20`
- One native **Recharging charm +3**, initially ready
- Ring of Regeneration: `+3`, automatically equipped
- Ring of Wisdom: `+3`, automatically equipped

The two mission rings occupy Brogue's normal two ring slots from turn zero. They are not permanently locked: the player can later replace them using normal Brogue equipment rules.

### 20-shot capacity is not +20 enchantment

v0.2.21 separates the Starfleet battery capacity of the three primary combat staffs from Brogue's native staff enchantment value. Fire, Lightning and Poison can still store **20 shots**, but they behave as ordinary **+3 staffs** for damage/effect magnitude and natural recharge timing.

This fixes the old coupling where `20/20` was implemented as `enchant1 = 20`. That accidentally made Poison last hundreds of turns and made natural staff recharge extremely fast. Capacity is now queried independently, while Brogue's normal +3 formulas remain responsible for Fire/Lightning/Poison power and recharge.

The Ring of Wisdom still accelerates natural staff recharge exactly through Brogue's normal ring mechanic; it no longer accelerates a mistakenly +20 staff. Enchanting one of these marked mission staffs can still improve its native effect/recharge enchantment without reducing the separate 20-shot battery capacity.

Bashir's carried poison staff uses the same model: 20-shot storage with native +3 poison strength/recharge behavior.

## Native Recharging charm

O'Brien carries a real Brogue **Recharging charm +3**.

It uses Brogue's native Recharging-charm mechanics: applying it instantly recharges staffs, then the charm itself enters its normal cooldown. At `+3`, the native curve is about **1664 turns** from use to ready again (`10000 × 0.55^3`, subject to the game's integer timing). This is deliberately a strategic emergency reserve rather than a rapidly cycling power source.

In the O'Brien variant only, casting the native Recharging charm also refills the three marked Starfleet Emergency Power Cells to `20/20`. Naturally found Recharging charms work the same way. Naturally found **Scrolls of Recharging** remain ordinary one-use scrolls and also refill the marked Power Cells.

For the three marked primary combat staffs, a Recharging charm or Scroll fills the independent battery all the way to `20/20`; it does not reinterpret the capacity as enchantment.

## Starfleet Emergency Power Cells

The three Power Cells remain finite high-discharge emergency batteries. Only the three mission batteries carry a dedicated internal Power Cell marker; ordinary/random Recharging charms retain their native Brogue behavior.

Each Power Cell stores **20 charge-units**. Applying a Cell lets O'Brien choose one staff and immediately transfer up to 20 units to it. Only the energy actually needed is consumed: a Fire staff at `13/20` uses 7 Cell units, a Blinking staff at `0/10` uses 10, and a Tunneling staff at `1/3` uses 2.

This is intentionally a high-discharge / slow-recovery system. A Cell passively recovers only **1 charge-unit per 100 turns**, so a completely empty Cell requires about 2000 turns to return to `20/20`. This slow recovery is based only on elapsed player time: **Wisdom does not accelerate it, and Reaping does not feed it**. Wisdom continues to improve the normal recharge rate of staffs themselves.

The energy model is therefore layered:

- Fire / Lightning / Poison are +3 Brogue staffs with separate 20-shot Starfleet batteries.
- Other staffs keep their ordinary Brogue capacity/enchantment relationship unless specifically defined otherwise.
- Power Cells are immediate 20-unit emergency reserves with very slow trickle recovery.
- The native Recharging charm is a very slow-cycling full-system emergency reset.
- Scrolls of Recharging are rare one-use external high-power resets found through normal dungeon generation.

## Stairhead logistics

Auxiliary supplies still materialize near designated stairwells. They remain physical floor items, so normal Brogue inventory choices still matter.

- The initial stairhead cache contains no fixed Recharging spell or scroll; the native +3 Recharging charm is already in O'Brien's backpack.
- The old every-ten-depth fixed Recharging-scroll resupply remains removed. Additional Scrolls of Recharging come from normal dungeon generation.
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
python3 apply_obrien_mod_v0_2_21.py
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
