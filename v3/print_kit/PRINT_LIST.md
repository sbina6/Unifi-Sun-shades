# Doorbell Lite sunshade v3: print list

**One printed part that replaces the doorbell's black 20° wedge and shades it.** For a Ubiquiti UniFi Protect Doorbell Lite on a wall facing 150° in Doha, turned 20° to the left (as you face the wall) toward the entrance, so the camera looks at about 170°.

- The back of the part sits flush on the wall, and the doorbell's metal plate screws onto its front face, just as it did on the wedge.
- The shell is 2.2 mm thick with R10 top corners. Its lip curves in an S that follows the edge of the camera's picture, with a 3° margin, so the shade never appears in the video.
- In Doha it cuts direct sun on the doorbell by 99% on June 21 and 85% on May 1 / Aug 12. In summer the wall itself shades the doorbell from about 11:45.

## Parts

| File | Qty | Resin | Purpose |
|---|---|---|---|
| `sunshade_hood_v3_TR300.stl` | 1 | Phrozen TR300 | Wedge and sunshade in one. 62.7 g. |
| `fit_test_coupon_v3_TR300.stl` | 1 | Phrozen TR300 | Scale frame (62.00 X / 62.00 Y, 56.60 Z), sliding nut channels 5.6 / 5.7 / 5.8, M3 holes 3.3 / 3.4 / 3.5. 6.2 g. |

STEP files for both are included.

## Orientation and supports

**Hood:** the STL is pre-oriented, so don't rotate it.
- Long axis 45° from vertical, with the wall-side face toward the build plate and the roof up.
- The hollow behind the seat opens toward the wall face and is vented through the seat windows and the cable window, so there is no suction cup.
- Down-facing surfaces: 9,551 mm² at 45° or steeper, plus 51 mm² flatter. Add light supports where your slicer flags them.
- **Supports** go on the wall-side face (it sits against the wall).
- **No supports** on the seat face (the doorbell and plate sit on it), in the nut channels, or on the lip.

**Coupon:** print it axis-aligned and flat, as exported.

## Scale and fits (do this first)

1. Print the coupon and post-process it like the real part.
2. Measure the frame (drawn 62.00 X / 62.00 Y) and the tower (drawn 56.60 Z). Set the slicer scale per axis to drawn ÷ measured × 100 %.
3. Slide an M3 nut through the three channels. The part is drawn at **5.7**. Use the narrowest channel the nut slides through without turning, and tell me if that isn't 5.7.
4. Push an M3 screw through the three holes. The part's screw holes are 3.4.

## Post-processing (TR300)

Wash and remove supports. Clear the nut channels, slots and counterbores with a pick. Cure 15 min dry, no heat.

## Fits

| Feature | Size | Notes |
|---|---|---|
| Wall-screw counterbores | Ø7.5, 3.0 mm floor, Ø3.4 hole; axis square to the wall | Existing wall holes, 74 mm apart |
| Plate-screw slot | 3.4 wide, nominal 46 mm from the middle, travel −1 / +5 mm | Plate holes measured ~92 mm apart; travel covers 90–102 mm |
| Nut channel | 5.7 AF, opens toward the wall, 2.2 mm skin under the plate | Nut slides, can't turn; the wall holds it in |
| Cable window | 24 × 57 mm, through to the wall | Your existing cable hole falls inside |
| Doorbell seat | flat face, 2.4 mm skin with S-diamond windows | Same position as on the wedge |
| Air gap, sides / top | 2.0 / 14.0 mm | The doorbell hooks on at up to 20° tilt with a 4 mm lift |

## Hardware by job

| Job | What | Where |
|---|---|---|
| Part to the wall | The doorbell's own 2 × M3 wall screws and anchors, in the existing holes | Already on the wall |
| Plate to the part | 2 × M3 × 12 mm stainless flat-head (countersunk) Phillips | [Voltaat](https://voltaat.com), 5-pc pack, QAR 1 |
| Nuts for the plate screws | 2 × M3 hex nut | [Voltaat](https://voltaat.com), 5-pc pack, QAR 1 |
| Tools | Phillips screwdriver (the doorbell's own, or a long #1) | Al Annabi ([alannabi.qa](https://alannabi.qa)) |

## Assembly

1. Unplug the doorbell. Undo the lock screw at its bottom, unhook it, and unscrew the metal plate from the black wedge. Unscrew the wedge from the wall and keep its two wall screws.
2. Hold the printed part wall-side up. Drop an M3 nut into each nut channel, flats along the channel.
3. Thread the PoE cable through the cable window. Put the part on the wall with the thick side to the same side as the wedge's thick side (the camera then looks toward the entrance).
4. Drive the two wall screws through the counterbores into the existing anchors. The screwdriver goes straight in along each counterbore.
5. Lay the metal plate on the seat face and line its two end holes up with the slots. Screw in the two M3 × 12 countersunk screws; the nuts slide to meet them.
6. Plug in the doorbell, hook it onto the plate's top tab (tilt the bottom out by 10–20°, lift about 4 mm, slide in under the roof), swing the bottom in and fit the lock screw from below.

## Before printing, check one thing

The plate's end-hole spacing was measured from Ubiquiti's drawing. On your plate, the two small round holes at its ends should be **90–102 mm** apart centre to centre. If they're outside that, tell me before printing.
