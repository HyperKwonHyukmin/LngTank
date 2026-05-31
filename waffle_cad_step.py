"""
waffle_cad_step.py  -- v2 (GTT Mark III faithful upgrade)
=========================================================
Parametric B-rep (true CAD solid) of the GTT Mark III primary "waffle" membrane
(Bengtsson, US 3,199,963), exported to neutral CAD/CAE formats.

What changed vs v1 (from the Mark III audit):
  * DUAL-HEIGHT corrugations -- large ribs 54 mm, small ribs 37.2 mm, nodes at the
    large-corrugation height (was a single 34 mm rib + 53 mm node).
  * Parameterised entry point -- argparse (--nx/--ny/--panel/--prefix) and a
    build(nx, ny) API that returns the solid; no more hardcoded-only run.
  * Post-build validity check -- asserts a single valid closed solid with volume>0
    and prints the bounding box, so a degenerate boolean is caught before export.
  * Multi-format export -- STEP (AP242 if the OCCT writer supports it, else AP214),
    plus IGES, native BREP and STL, covering modern CAE, legacy toolchains and
    lossless round-trips.
  * Documented rib profile -- named cross-section dims (VALLEY/CREST fractions of
    the half-pitch, shared with waffle_membrane.py) instead of magic numbers.

Real spec (GTT/MARIN ISOPE Bogaert 2010; sea-man.org; UCL/Paik):
    pitch P = 340 mm   t = 1.2 mm 304L   large = 54 mm   small = 37.2 mm
    standard sheet ~ 3 m x 1 m (3 x 9 cells)

NOTE: by default this STEP is a SOLID relief master (a filled positive of the relief).
With --thin it is hollowed into a constant-thickness 1.2 mm wall B-rep (OCCT shell):
this works because the rib cross-section is a STEEP MONOTONIC trapezoid (near-vertical
80 deg flank, no barrel bulge), which OCCT can offset inward. The square top-hat node
is still an APPROXIMATION of the real folded "mushroom" knot (a single-valued/loft
solid cannot carry the fold overhang); the folded node + its own thin wall live in
waffle_knot.py (--thin, trimesh normal-offset). The geometrically clean height-field
thin membrane is waffle_membrane.py (GLB/STL, normal-offset wall).

Install:  pip install cadquery
Run:      python waffle_cad_step.py            # 3x3 cells
          python waffle_cad_step.py --panel    # full 3x9 strake
Output:   waffle_membrane.step / .igs / .brep / _cad.stl   (units = millimetres)
"""

from __future__ import annotations
import sys
import math
import argparse
import cadquery as cq

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --------------------------------------------------------------------------- #
#  Parameters (mm) -- match waffle_membrane.py
# --------------------------------------------------------------------------- #
P        = 340.0    # corrugation pitch = node spacing
T        = 1.2      # base-sheet thickness
H_LARGE  = 54.0     # large corrugation / knot height
H_SMALL  = 37.2     # small corrugation height
# Near-vertical STEEP MONOTONIC trapezoid corrugation cross-section. A straight flank
# at FLANK_DEG from horizontal connects the z=0 valley to the z=h crest flat. The profile
# stays MONOTONIC in x (footprint Wf >= crest Wc, no barrel bulge): that is what lets OCCT
# offset it inward into a constant-thickness 1.2 mm wall for --thin. Arc fillets were tried
# (omega/U section) and dropped -- rounding the flank pushes the mid-flank outward past the
# footprint (non-monotonic), and that bulge defeats the inward shell (StdFail_NotDone).
# Same 80 deg near-vertical flank, but now shellable (verified valid through a 2x2 relief).
CRESTF   = 0.09     # crest flat half-width / P  (-> crest flat = 0.18P = 61.2 mm)
FLANK_DEG = 80.0    # flank angle from horizontal (near-vertical)
WN       = 90.0     # node footprint width
WTOP     = 58.0     # node flat-crest width


def flank_profile(h, flank_deg=FLANK_DEG):
    """Near-vertical STEEP MONOTONIC trapezoid half-section, symmetric about x=0.
    A straight flank at exactly `flank_deg` from horizontal connects the z=0 valley plane
    to the z=h crest flat (half-width Wc = CRESTF*P). The footprint half-width is derived:
        Wf = Wc + h / tan(flank_deg)   (>= Wc, so the section is MONOTONIC in x).
    Monotonicity is what lets OCCT offset the relief inward into a constant-thickness wall
    (--thin). Returns (cadquery wire workplane, realised_flank_deg).
    Verified: 80 deg -> valid solid AND shellable to a 1.2 mm wall through a 2x2 relief."""
    Wc = CRESTF * P
    Wf = Wc + h / math.tan(math.radians(flank_deg))
    pts = [(-Wf, 0.0), (-Wc, h), (Wc, h), (Wf, 0.0)]
    wp = cq.Workplane("XZ").polyline(pts).close()
    realised = math.degrees(math.atan2(h, Wf - Wc))
    return wp, realised


def rib_solid(h, length):
    """Steep trapezoid corrugation of height h, running along +Y, centred on the origin."""
    wp, _ = flank_profile(h)
    return wp.extrude(length / 2.0, both=True)


def node_solid():
    """Square top-hat knot at the large-corrugation height (footprint WN -> flat crest WTOP)."""
    return (
        cq.Workplane("XY")
        .rect(WN, WN)
        .workplane(offset=H_LARGE * 0.5).rect((WN + WTOP) / 2.0, (WN + WTOP) / 2.0)
        .workplane(offset=H_LARGE * 0.5).rect(WTOP, WTOP)
        .loft(combine=True)
    )


def build(nx, ny):
    """Relief master: base sheet + dual-height ribs + knots, centred on the origin."""
    Lx, Ly = nx * P, ny * P
    ox, oy = Lx / 2.0, Ly / 2.0
    cx = [i * P - ox for i in range(nx + 1)]        # node lines in X
    cy = [j * P - oy for j in range(ny + 1)]        # node lines in Y

    result = (
        cq.Workplane("XY")
        .box(Lx, Ly, T, centered=(True, True, False)).translate((0.0, 0.0, -T))
    )

    # knots at every lattice crossing (at large-corrugation height)
    for x in cx:
        for y in cy:
            result = result.union(node_solid().translate((x, y, 0.0)))

    # large corrugations: run along X (at each y line), height H_LARGE
    for y in cy:
        for i in range(nx):
            mid = (cx[i] + cx[i + 1]) / 2.0
            result = result.union(
                rib_solid(H_LARGE, P).rotate((0, 0, 0), (0, 0, 1), 90).translate((mid, y, 0.0)))

    # small corrugations: run along Y (at each x line), height H_SMALL
    for x in cx:
        for j in range(ny):
            mid = (cy[j] + cy[j + 1]) / 2.0
            result = result.union(rib_solid(H_SMALL, P).translate((x, mid, 0.0)))

    # trim the boundary ribs flush with the nominal panel footprint (half-ribs at the
    # edges, clean vertical sheet edges) -> bbox matches the height-field mesh.
    trim = (cq.Workplane("XY")
            .box(Lx, Ly, H_LARGE + T + 2.0, centered=(True, True, False))
            .translate((0.0, 0.0, -T - 1.0)))
    return result.intersect(trim)


def check_solid(result):
    """Assert one valid closed solid with positive volume; return (ok, bbox, vol)."""
    solids = result.solids().vals()
    shp = result.val()
    valid = shp.isValid()
    vol = shp.Volume()
    bb = shp.BoundingBox()
    ok = (len(solids) == 1) and valid and (vol > 0.0)
    return ok, (bb.xlen, bb.ylen, bb.zlen), vol


def export_all(result, prefix):
    """STEP (AP242 if available) + IGES + BREP + STL, each best-effort."""
    written = []

    # STEP -- try to request AP242 from the underlying OCCT writer (binding name
    # varies across OCP versions, so probe both SetCVal_s and SetCVal).
    try:
        from OCP.Interface import Interface_Static
        setc = getattr(Interface_Static, "SetCVal_s", None) or getattr(Interface_Static, "SetCVal", None)
        if setc:
            setc("write.step.schema", "AP242DIS")
    except Exception:
        pass
    step_path = f"{prefix}.step"
    cq.exporters.export(result, step_path)
    # report the schema actually written, read from the STEP FILE_SCHEMA header
    schema = "STEP"
    try:
        head = open(step_path, "r", encoding="utf-8", errors="ignore").read(4000)
        line = head.split("FILE_SCHEMA", 1)[-1][:120] if "FILE_SCHEMA" in head else ""
        schema = "STEP AP242" if "242" in line else ("STEP AP214" if "214" in line else "STEP")
    except Exception:
        pass
    written.append((step_path, schema))

    # IGES (legacy CAE/CFD) via OCCT writer
    try:
        from OCP.IGESControl import IGESControl_Writer
        w = IGESControl_Writer()
        w.AddShape(result.val().wrapped)
        w.ComputeModel()
        if w.Write(f"{prefix}.igs"):
            written.append((f"{prefix}.igs", "IGES"))
    except Exception as e:
        print(f"  (IGES skipped: {type(e).__name__})")

    # native BREP (lossless round-trip)
    try:
        result.val().exportBrep(f"{prefix}.brep")
        written.append((f"{prefix}.brep", "BREP (lossless)"))
    except Exception as e:
        print(f"  (BREP skipped: {type(e).__name__})")

    # STL (quick view / mesh)
    cq.exporters.export(result, f"{prefix}_cad.stl")
    written.append((f"{prefix}_cad.stl", "STL"))
    return written


def main():
    ap = argparse.ArgumentParser(description="GTT Mark III waffle membrane (parametric B-rep)")
    ap.add_argument("--panel", action="store_true", help="full 3x9 strake")
    ap.add_argument("--nx", type=int, default=3, help="cells in X (default 3)")
    ap.add_argument("--ny", type=int, default=3, help="cells in Y (default 3)")
    ap.add_argument("--prefix", default="waffle_membrane", help="output filename prefix")
    ap.add_argument("--thin", action="store_true",
                    help="hollow the relief into a constant-thickness wall (B-rep thin shell)")
    ap.add_argument("--wall", type=float, default=T, help="wall thickness for --thin (default 1.2)")
    args = ap.parse_args()
    nx, ny = (3, 9) if args.panel else (args.nx, args.ny)
    prefix = args.prefix + ("_thin" if args.thin else "")

    _, fa = flank_profile(H_LARGE)
    print("=== GTT Mark III waffle membrane (US 3,199,963) -- CadQuery B-rep v2 ===")
    print(f"  P={P}  t={T}  H_large={H_LARGE}  H_small={H_SMALL}  cells {nx}x{ny} -> {nx*P:.0f}x{ny*P:.0f} mm")
    print(f"  flank angle (trapezoid)   : {fa:.1f} deg from horizontal (near-vertical)")

    result = build(nx, ny)

    if args.thin:
        # Hollow into a constant-thickness wall: remove the single flat bottom face and
        # offset the remaining faces inward by `wall` (CadQuery .shell == OCCT MakeThickSolid).
        try:
            shelled = result.faces("<Z").shell(-args.wall)
            ok0, _, vol0 = check_solid(result)
            ok, bbox, vol = check_solid(shelled)
            if ok and vol > 0:
                result = shelled
                eff = "n/a"
                try:
                    area = result.val().Area()  # closed-wall surface area (both skins + sides)
                    eff = f"{vol / (area * 0.5):.2f}"  # 2V/A heuristic ~ wall thickness (mm)
                except Exception:
                    pass
                print(f"  hollowed to thin wall     : t={args.wall} mm  (effective ~{eff} mm)")
            else:
                print("  !! thin shell invalid; falling back to SOLID relief master.")
        except Exception as e:
            print(f"  !! shell failed ({type(e).__name__}); exporting SOLID relief master instead.")

    ok, bbox, vol = check_solid(result)
    print(f"  single valid closed solid : {ok}")
    print(f"  bbox (mm)                 : {bbox[0]:.1f} x {bbox[1]:.1f} x {bbox[2]:.1f}")
    print(f"  volume (cm3)              : {vol/1000.0:.1f}")
    if not ok:
        print("  !! WARNING: result is not a single valid closed solid -- inspect before trusting export.")
    if args.thin:
        print("  (note: STEP may re-import the wall as a SHELL -- an OCP quirk; BREP round-trips as SOLID.)")

    for path, kind in export_all(result, prefix):
        print(f"  written: {path:28s} {kind}")


if __name__ == "__main__":
    main()
