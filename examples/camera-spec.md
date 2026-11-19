# Nextimus camera spec

**Evidence:** Verified against a local design note titled "Nextimus camera target (Kevin, 2026-11-12, final)," last written 12 Nov 2026, 11:44 AM America/Chicago (CST), and against private PR #287, which I merged on 12 Nov 2026, 9:03 PM America/Chicago (CST).

I wrote these numbers. An agent produced comparison images on a throwaway branch; those images include a third-party game and are **not** in this repository.

## Camera

- Orthographic projection (no perspective). The ground shows evenly on every side of the player.
- Ortho size **7.25 m** (the vertical extent of the view) in both views. Toggling views changes only the pitch, never the zoom or the framing.
- The camera sits due south of the player and looks north. It is set 30 m back along the view direction so nothing clips; in ortho, distance does not change scale.
- The screen centre is the player's feet (the ground point under the body).

| View | Pitch (down from horizontal) | Ground visible from the feet | Character on screen |
|---|---|---|---|
| Angled | 50° | 4.73 m ahead and behind, 6.44 m left and right | about 20% of screen height |
| Top-down | 72° | 3.81 m ahead and behind, 6.44 m left and right | about 10% (seen mostly from above) |

## Characters

- Visual scale is **1.25×**. A bench Knight goes from 1.81 m native to about 2.26 m on screen.
- Models stay authored at real size (about 1.8 m). The game applies 1.25× on the character's visual node.
- Characters face the camera head-on in the reference shots.

Walk speed stayed 7.5 m/s when this landed; pace was tracked separately in issue #286. PR #287 implemented the spec in `scripts/main/World.gd` (`size = 7.25`, angled 50°, top 72°, feet-centered, 30 m back).
