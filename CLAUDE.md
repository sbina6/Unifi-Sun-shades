# CLAUDE.md: 3D-printed resin parts

## The user's devices and site (read first)
- Doorbell: **Ubiquiti UniFi Protect Doorbell Lite (UVC-Doorbell-Lite)**, 137 × 40 × 26.4 mm, metal plate 31 × 125 × 1.6, wall screws M3 on the centreline 74 mm c/c, Ø18 cable hole 88 mm below the top. Geometry lives in `cad/sunshade.py` and `v3/v3_geom.json`.
- Site: Doha, wall facing 150°, doorbell on a 20° wedge (v3/v4 replace it), camera looking ~170°.
- The doorbell is mounted over a Qatar / UK BS 4662 switch box (75 mm opening, lugs 60.3 mm c/c). Current designs: `v7/` (the SIMPLE one: a small 48 mm shade, doorbell flat with no angle, its own plate bolts on, ~57 g) and `v6/` (a STRAIGHT 76 mm shade + 86 mm backplate, ~67 g). The doorbell sits ANGLED inside it on the user's OWN angled bracket (the stock 20° wedge), so there is no wedge in the printed part. `v5a/` (integrated wedge) and `adapter/` are earlier designs.
- The user wants one-piece parts, light weight, and everything CENTRED on the box: never move the doorbell off-centre to solve a fixing problem; ask instead.
- Two separate joints, both bolted: (1) shade to wall with the switch box's OWN 2 screws, left and right of the box (the lugs, 60.3 mm apart): never invent new wall holes; (2) the doorbell's plate (v7) or the user's bracket (v6) to the shade with M3 bolts into M3 nut pockets (74 mm apart). Always include nut pockets.
- Design language: Islamic geometric art (stars, rosettes, mashrabiya-style lattices, pointed arches). The arched car-shade / pergola look was rejected: do not use it or its reference image. A bigger shade does not shade better (v2 sweep), so size is a looks-only choice.
- Curved lip cuts (`Face.make_surface_from_array_of_points`) fail silently at some sampling steps and on scalloped edges: always tessellate at ≤0.03 mm and check watertight and length (`cad/sunshade_v6.py: mesh_ok / cut_lip`). Coarser tessellation gives false cracks.

## Toolchain
- CAD Python: `/tmp/cadenv/bin/python` (build123d 0.13.0, cadquery-ocp-novtk 8.0.1.1.0, shapely 2.2.0, trimesh 5.2.0, numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2, pillow, ezdxf). If it's missing, rebuild it:
  ```
  python3 -m venv /tmp/cadenv
  /tmp/cadenv/bin/pip install --quiet build123d==0.13.0 shapely==2.2.0 trimesh==5.2.0 numpy==2.5.4 scipy==1.18.1 matplotlib==3.11.2 pillow ezdxf
  ```
- No rtree or networkx: don't use `trimesh.contains()`, `Path.polygons_full` or `Path.discrete`. Get section areas from `trimesh.intersections.mesh_plane` segments → shapely `linemerge` → rings combined even-odd.
- Chromium and Playwright are preinstalled; don't reinstall them. Use them to screenshot three.js viewers.

## Printer and materials
- MSLA resin printer.
- Rigid: Phrozen TR300 (1.17 g/cm³, Shore D 80, ~60 MPa at break, ~4% elongation). Stiff, not stretchy: no snap fits or clips; join parts with hardware. Keep working stress under ~10 MPa at 3× the real load.
- TR300 post-process: wash, remove supports, clear holes and pockets with a pick, cure 15 min dry, no heat.
- Flexible: Siraya Tech Tenacious Flex Black 70A. Wash 2–3 min in ethanol, cure 10–15 min under water, print upright with no supports, don't over-cure.
- Shrinkage: no published figure for TR300. Every kit gets a `fit_test` coupon with reference faces (62.00 mm in X/Y, 56.60 mm in Z). Slicer scale = drawn / measured × 100%.

## Fits that worked in TR300
- 3x8x3 bearing pocket Ø8.15 × 3, with a 0.4 mm 45° lead-in (fit test: 8.05 / 8.15 / 8.25).
- M3 clearance hole Ø3.4 (test 3.3 / 3.4 / 3.5).
- M3 nut pocket 5.7 across flats × 2.6 deep (test 5.6 / 5.7 / 5.8).
- M3 flat-head countersink: Ø6.3 top, 90°.
- Moving parts: 0.2 mm side gap. Bearings are clamped only by printed 4.2 mm rings on the inner ring; no washers, and no screw head or nut touches a bearing.
- Servo cups: 0.2 mm per side. Printed gears: teeth 0.25 mm thinner and centres 0.3 mm further apart than a tight mesh.

## Design style
- Light, not overbuilt: walls 2–2.5 mm, skins 1.8 mm. Remove material with one window pattern everywhere (S-curved diamonds), even on small parts.
- Fewest parts possible; proven mechanisms over invented ones; simple shapes.

## Print-ready rules
- Every STL watertight, with no sealed internal voids.
- Export STLs pre-oriented: tilted 15–45°, every blind pocket opening upward or vented (no suction cups), lowest point at z = 0.
- No supports on bearing pockets, gear teeth or mating faces.
- Each kit has `PRINT_LIST.md` (purpose, orientation, support notes, fits table, hardware by job with links, assembly steps) and `manifest.json`.

## Hardware (bought in Qatar)
- First choice, online: Voltaat (voltaat.com)
  - 3x8x3 ball bearing VT-1666, QAR 3.
  - M3 stainless flat-head (countersunk) Phillips screws in 5-pc packs: 8, 12, 14, 16, 20, 25, 30, 35, 40 mm, QAR 1 a pack.
  - M3 hex nuts in 5-pc packs, QAR 1.
  - Sells no washers.
- SmartQat (Gulf Market, Gharaffa, Doha): M3 screw-and-nut box and 623ZZ bearings, when it's open.
- Al Annabi Electronics (alannabi.qa): tools only (e.g. a long Phillips #1).
- Design for countersunk M3 screws and nuts in printed pockets.

## Verification before delivering
- Check interference between all parts across the full range of motion, and check that every screw path is clear of plastic.
- Run heavy build123d booleans in a `multiprocessing` pool with the `'spawn'` context: export parts to BREP and load them in each worker. Fork deadlocks OpenCascade; one big process can run out of memory.
- Stop runaway jobs by PID; never `pkill -f` with a pattern that can match your own shell.

## Deliverables for each version
- STEP files.
- Print kits as zips sent to the user.
- An interactive three.js viewer, published as an artifact.
- A README section, committed and pushed to the branch the user gives.
