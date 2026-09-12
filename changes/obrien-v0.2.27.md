O'Brien Must Survive v0.2.27
=============================

- `C` is now a true Security Hologram toggle: deploy while OFF, deactivate while ON.
- Manual deactivation is a shutdown, not destruction. Integrity and Lightning/Poison emitter charge state are retained for the next redeployment, preventing free repair/refill cycling.
- Only one Security Hologram can be active at a time.
- The HSO now participates in Brogue's native long-distance visual-link system by setting `MB_TELEPATHICALLY_REVEALED`; Brogue's normal `updateTelepathy()`/`TELEPATHIC_VISIBLE` path supplies the remote view around the hologram.
- Lightning friendly-fire remains normal Brogue behavior; the toggle is the tactical way to take the HSO offline when its firing lane becomes unsafe.
- Existing HSO combat statistics, flight, rapid integrity repair, finite 20/20 Lightning/Poison emitters and recharge pacing are unchanged.
