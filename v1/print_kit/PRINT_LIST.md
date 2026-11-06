# Doorbell Lite sunshade v1: print list

A static hood for the **Ubiquiti UniFi Protect Doorbell Lite** (UVC-Doorbell-Lite, 137 × 40 × 26.4 mm). It shades the doorbell's top and sides, and the front at high sun, to keep heat off a black PoE camera in Qatar sun. Its 2.2 mm back flange sits between the wall (or the 20° wedge) and the doorbell's metal plate, held by the doorbell's own screws. The doorbell hooks on exactly as before, 2.2 mm further from the wall.

## Parts

| File | Qty | Resin | Purpose |
|---|---|---|---|
| `sunshade_hood_v1_TR300.stl` | 1 | Phrozen TR300 | The hood: back flange, two side walls, roof with a 10 mm brim. 41.3 g. |
| `fit_test_coupon_v1_TR300.stl` | 1 | Phrozen TR300 | Shrinkage coupon: 62.00 X / 62.00 Y frame, 56.60 Z tower. 5.0 g. |

STEP files for both are included.

## Orientation and supports

**Hood:** the STL is pre-oriented, so don't rotate it.
- Long axis 45° from vertical, with the wall-side face of the flange toward the build plate and the roof up.
- The cavity opens upward through the front and is vented through the flange windows, so there is no suction cup.
- Down-facing surfaces: 7,760 mm², all at 45° or steeper. Nothing flatter needs support.
- **Supports** go on the back (wall-side) face of the flange, plus light supports under the roof's underside if your slicer flags it.
- **No supports** on the front face of the flange (the doorbell's back edge seats there), on the brim edge, or on the front edges of the side walls.

**Coupon:** print it axis-aligned, as exported. Don't tilt it, or its faces stop matching the printer axes. Light supports or a raft under the frame.

## Scale (do this first)

1. Print the coupon. Wash and cure it the same way as the real part.
2. Measure the frame in X and Y (drawn 62.00 mm) and the tower height in Z (drawn 56.60 mm).
3. Set the slicer scale per axis to drawn ÷ measured × 100 %, then print the hood.

## Post-processing (TR300)

Wash, remove supports, and clear the flange slots and windows with a pick. Cure 15 min dry, no heat.

## Fits

| Feature | Size | Notes |
|---|---|---|
| Wall / plate screw slots | 6.0 wide, 33–51 mm either side of the flange middle | Takes the flat mount's 74 mm and the wedge's ~92 mm hole spacing, ±4 mm; a 6 mm head passes through |
| Cable window | 24 × 57 mm, 42–99 mm below the doorbell top | Covers the flat mount's Ø18 cable hole and the wedge's centre window |
| Doorbell seat | flat flange front, solid 4 mm rim band | The doorbell's back edge sits here |
| Air gap, sides / top | 2.0 / 14.0 mm | 14 mm lets the doorbell hook on at up to 20° tilt with a 4 mm lift |

No press fits; nothing on this part needs a fit test beyond scale.

## Hardware by job

| Job | What | Where |
|---|---|---|
| Flat mount: hood + plate to the wall | The doorbell's own 2 × M3 wall screws and anchors | in the doorbell box |
| Only if those screws now grip the anchor poorly (the flange takes 2.2 mm) | 2 × M3 about 5 mm longer, round/pan head (they sit on the metal plate) | SmartQat M3 screw-and-nut box (Gulf Market, Gharaffa) |
| 20° wedge mount: plate to the wedge through the flange | 2 × M3 about 2.5 mm longer than the doorbell's short plate screws | SmartQat (pan head), or [Voltaat](https://voltaat.com) M3 stainless flat-head 8 mm 5-pc pack, QAR 1 |
| Tools | the doorbell's screwdriver; drill Ø5 for anchors, Ø18 for the cable | the doorbell box / Al Annabi ([alannabi.qa](https://alannabi.qa)) |

## Assembly

**Flat mount**
1. Mark and drill the wall with the doorbell's paper template, as in its quick guide (Ø5 anchors, Ø18 cable hole). Fit the anchors.
2. Pull the PoE cable through the hood's cable window.
3. Hold the hood flat on the wall, roof up, then lay the doorbell's metal plate on the flange so its holes line up with the hood's slots.
4. Drive the 2 × M3 wall screws through the plate and the flange into the anchors. Check the hood is level.
5. Plug in the doorbell. Hook its top onto the plate's top tab: tilt the bottom out by 10–20°, lift about 4 mm, slide in under the roof, then lower and swing the bottom in.
6. Fit the lock screw from below, as before.

**20° wedge mount**
1. Screw the wedge to the wall as in the quick guide.
2. Lay the hood's flange on the wedge, then the plate on the flange. Screw the plate to the wedge with the 2 × longer M3s through the hood's slots.
3. Hook on and lock the doorbell as in steps 5–6 above.

## Before printing, check one dimension

The hole spacing comes from Ubiquiti's to-scale drawing, not a published dimension. On the paper template in the box, the two small holes should be **about 74 mm** apart, centre to centre. The slots tolerate 66–100 mm. If yours is outside that, tell me before printing.
