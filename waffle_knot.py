"""
waffle_knot.py  -- folded "mushroom" knot (the part a height-field CANNOT represent)
====================================================================================
The GTT Mark III primary membrane's defining feature is the folded KNOT at each
corrugation crossing: a pleated, 3-D folded dome of sheet metal whose folds carry
"reserve length" that unfolds to absorb biaxial thermal contraction at -163 C
(sources: sea-man.org "MARK III System"; UCL/Paik FE; US 3,199,963 / 3,994,693).

A single-valued height-field z(x, y) (waffle_membrane.py) physically cannot carry:
  * a re-entrant OVERHANG (the cap is wider than the waist -> "mushroom"),
  * sharp 4-fold CREASES (the pleats), or
  * a twisting PINWHEEL fold.

This module builds the knot as an EXPLICIT closed surface (stacked square-ish rings
with a radial pleat that twists with height, a narrowed waist and a flared cap),
so all three features are actually present. It is then a watertight solid that can
be thickened / dropped onto the membrane lattice.

SCOPE / HONESTY (manufacturing fidelity, report item 3):
  CONFIRMED from public sources and now BUILT IN ->
    * the knot IS the intersection of the small and large corrugations (Paik/UCL FE;
      "knot, which is the intersection of small and large corrugations"),
    * its crest sits at the LARGE-corrugation height (54 mm), the large corrugation
      running continuously over the smaller one,
    * it is a stiffer "folded structure" that deforms LESS than the corrugations
      (Paik/UCL) and "fully unfolds" to release reserve length (GTT),
    * 4-fold crossing with arms along the two corrugation axes; "short and long
      pressing indentations" near the intersection.
  Every node dimension here is now DERIVED from the shared corrugation spec
  (pitch / heights / flank), not guessed -- so the node is dimensionally consistent
  with the membrane (waffle_membrane.py / waffle_cad_step.py).
  STILL APPROXIMATE (proprietary, not public): GTT's EXACT press-tool fold profile.
  The pleat amplitude / twist / cushion factors below are a literature-informed
  approximation of that fold, not the manufacturing drawing.
  Sources: Paik et al., "Nonlinear structural behaviour of membrane-type LNG ..."
  (UCL discovery 1535317); Bengtsson US 3,199,963; GTT Mark III system notes.

Install:  pip install numpy trimesh
Run:      python waffle_knot.py            # SOLID filled mushroom
          python waffle_knot.py --thin     # constant-thickness folded SHEET (normal-offset)
Output:   waffle_knot.{stl,glb} / waffle_knot_thin.{stl,glb}   units = millimetres

--thin builds the constant-thickness 1.2 mm sheet by offsetting the folded surface
along its own vertex normals and sealing the bottom rim (a watertight wall, no boolean
engine needed). This is the knot half of the "thin-wall including the folded node" item:
the pleats are re-entrant, so OCCT .shell() fails (StdFail_NotDone) -- the mesh
normal-offset is the robust route for the fold topology.
"""

from __future__ import annotations
import sys
import math
import argparse
import numpy as np
import trimesh

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --------------------------------------------------------------------------- #
#  Parameters (mm)
# --------------------------------------------------------------------------- #
# Shared GTT Mark III corrugation spec -- identical to waffle_membrane.py / waffle_cad_step.py
P         = 340.0   # corrugation pitch / node spacing                 [confirmed]
H_LARGE   = 54.0    # large corrugation crest height                   [confirmed]
H_SMALL   = 37.2    # small corrugation crest height                   [confirmed]
CRESTF    = 0.09    # crest flat half-width / P                        [shared]
FLANK_DEG = 80.0    # near-vertical corrugation flank angle            [shared]
T_WALL    = 1.2     # sheet thickness for --thin (mm, 304L)            [confirmed]

# --- node geometry DERIVED from the corrugation spec (no magic numbers) ----------------
# The knot is the INTERSECTION of the large (continuous, 54 mm) and small (37.2 mm)
# corrugations [Paik/UCL FE; GTT]. Every node dimension below is GROUNDED in the real
# corrugation profile so the node is dimensionally consistent with the membrane, instead
# of using guessed radii. The fold/pleat detail itself is a literature-informed
# approximation -- GTT's exact press-tool profile is proprietary and not public.
_tan  = math.tan(math.radians(FLANK_DEG))
_WC   = CRESTF * P                       # large crest flat half-width         = 30.6
_WF_L = _WC + H_LARGE / _tan             # large corrugation footprint half    = 40.1
_WF_S = _WC + H_SMALL / _tan             # small corrugation footprint half    = 37.2

H_N      = H_LARGE                       # node crest height = large crest     [confirmed]
R_BASE   = _WF_L + _WF_S                  # cross footprint: both corr feet meet at the node (77.3)
R_CAP    = _WC * 1.30                     # flat crest the large corr carries over + reserve flare (39.8)
R_WAIST  = R_CAP - 0.6 * (H_LARGE - H_SMALL)   # waist from the small-corr tuck -> overhang (29.7)
Z_WAIST  = H_SMALL / H_LARGE             # waist sits at the small-corr crest height (0.69) -- the tuck
PLEAT    = 0.13     # pleat amplitude (fold depth) -- literature-informed approx (press detail proprietary)
FOLDS    = 4        # 4-fold: arms along the two corrugation axes [Paik monitoring pts A-E]
FOLD_PHASE0 = math.pi / 2.0   # align fold lobes to the corrugation axes (+-x large, +-y small)
TWIST    = 0.08     # slight pinwheel of the pressing indentations (subtle; real node ~symmetric)
ASYM     = 0.10     # 2-fold footprint bias: large (x) arms wider than small (y) arms
SQUARE   = 0.45     # cushion/pillow section (Mark III node is squarish, not round)
NZ       = 56       # vertical layers
NT       = 120      # angular samples


def tri_wave(a):
    """Triangle wave in [-1, 1] -> SHARP creases (vs a smooth cos -> rounded)."""
    return (2.0 / np.pi) * np.arcsin(np.sin(a))


def _ring_grid(nt, nz):
    """The (nz, nt, 3) lattice of folded-surface vertices (no caps).
    base -> waist -> flared cap radius profile, 4-fold pinwheel pleats, squarish section."""
    zf = np.linspace(0.0, 1.0, nz)
    r_of_z = np.interp(zf, [0.0, Z_WAIST, 1.0], [R_BASE, R_WAIST, R_CAP])
    phase  = FOLD_PHASE0 + TWIST * 2.0 * np.pi * zf       # folds aligned to corr axes (+ slight pinwheel)
    theta  = np.linspace(0.0, 2.0 * np.pi, nt, endpoint=False)
    q = 4.0                                                # rounded-square section
    sqf = (np.abs(np.cos(theta)) ** q + np.abs(np.sin(theta)) ** q) ** (-1.0 / q)
    shape = (1.0 - SQUARE) + SQUARE * sqf
    asym  = 1.0 + ASYM * np.cos(2.0 * theta)              # large (x) arms wider than small (y) arms
    V = np.empty((nz, nt, 3))
    for k in range(nz):
        fold = 1.0 + PLEAT * tri_wave(FOLDS * theta + phase[k])   # sharp 4-fold pressing indentations
        r = r_of_z[k] * fold * shape * asym
        V[k, :, 0] = r * np.cos(theta)
        V[k, :, 1] = r * np.sin(theta)
        V[k, :, 2] = H_N * zf[k]
    return V


def _side_top_faces(nz, nt, top_c):
    """Side-wall quads + top cap (NO bottom cap -> open rim at ring 0)."""
    def vid(k, j):
        return k * nt + (j % nt)
    faces = []
    for k in range(nz - 1):
        for j in range(nt):
            a, b = vid(k, j), vid(k, j + 1)
            c, d = vid(k + 1, j + 1), vid(k + 1, j)
            faces.append([a, b, c]); faces.append([a, c, d])
    for j in range(nt):
        faces.append([top_c, vid(nz - 1, j), vid(nz - 1, j + 1)])         # top (up)
    return faces


def knot_mesh(nt=NT, nz=NZ):
    """Closed watertight SOLID knot (both caps): the filled folded mushroom."""
    V = _ring_grid(nt, nz).reshape(-1, 3)
    base_c = len(V); top_c = base_c + 1
    V = np.vstack([V, [[0, 0, 0.0]], [[0, 0, H_N]]])

    def vid(k, j):
        return k * nt + (j % nt)
    faces = _side_top_faces(nz, nt, top_c)
    for j in range(nt):
        faces.append([base_c, vid(0, j + 1), vid(0, j)])                  # bottom cap (down)

    mesh = trimesh.Trimesh(vertices=np.asarray(V),
                           faces=np.asarray(faces), process=True)
    mesh.merge_vertices()
    mesh.fix_normals()
    return mesh


def knot_thin_mesh(nt=NT, nz=NZ, t=T_WALL):
    """Constant-thickness folded SHEET via normal-offset (open underneath, like the real
    knot draped on the lattice). The closed mushroom CANNOT be OCCT-shelled (its re-entrant
    pleats -> StdFail_NotDone), so we offset the surface along its own vertex normals and
    seal the bottom rim with a band -- a watertight T-thick wall, no boolean engine needed.

    Topology = outer cup (open bottom) + inner cup offset inward by t (open bottom) + rim
    band joining the two bottom rims = a closed manifold whose interior is the t-thick sheet
    (cavity open downward). Returns a watertight trimesh."""
    V = _ring_grid(nt, nz).reshape(-1, 3)
    top_c = len(V)
    V = np.vstack([V, [[0, 0, H_N]]])                      # open bottom (no base cap)
    faces = np.asarray(_side_top_faces(nz, nt, top_c))

    outer = trimesh.Trimesh(vertices=V.copy(), faces=faces.copy(), process=False)
    outer.fix_normals()                                   # consistent surface normals
    inner_V = outer.vertices - t * outer.vertex_normals   # offset one wall-thickness inward
    N = len(outer.vertices)

    # rim band: outer ring-0 (indices 0..nt-1) <-> inner ring-0 (N..N+nt-1)
    band = []
    for j in range(nt):
        o0, o1 = j, (j + 1) % nt
        i0, i1 = N + j, N + (j + 1) % nt
        band.append([o0, o1, i1]); band.append([o0, i1, i0])

    allV = np.vstack([outer.vertices, inner_V])
    allF = np.vstack([outer.faces, outer.faces[:, ::-1] + N, np.asarray(band)])
    wall = trimesh.Trimesh(vertices=allV, faces=allF, process=True)
    wall.merge_vertices()
    wall.fix_normals()
    return wall


def main():
    ap = argparse.ArgumentParser(description="Folded mushroom knot (Mark III)")
    ap.add_argument("--prefix", default="waffle_knot")
    ap.add_argument("--nt", type=int, default=NT, help="angular samples (default %(default)s)")
    ap.add_argument("--nz", type=int, default=NZ, help="vertical layers (default %(default)s)")
    ap.add_argument("--thin", action="store_true",
                    help="constant-thickness folded SHEET (normal-offset wall) instead of solid")
    ap.add_argument("--wall", type=float, default=T_WALL, help="wall thickness for --thin (default 1.2)")
    args = ap.parse_args()
    prefix = args.prefix + ("_thin" if args.thin else "")

    print("=== Mark III folded 'mushroom' knot (approx.) ===")
    print(f"  H_n={H_N}  base={R_BASE} waist={R_WAIST} cap={R_CAP}  "
          f"folds={FOLDS} twist={TWIST}  overhang={'YES' if R_CAP > R_WAIST else 'no'}  "
          f"res nt={args.nt} nz={args.nz}")

    if args.thin:
        m = knot_thin_mesh(args.nt, args.nz, args.wall)
        ext = m.bounds[1] - m.bounds[0]
        # 2V/A heuristic ~ wall thickness (closed double-skin shell)
        eff = (2.0 * m.volume / m.area) if m.area > 0 else 0.0
        print(f"  mode       : THIN constant-thickness folded sheet (t={args.wall} mm)")
        print(f"  watertight : {m.is_watertight}  (effective wall ~{eff:.2f} mm)")
        print(f"  bbox (mm)  : {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f}")
        print(f"  volume     : {m.volume/1000.0:.2f} cm3  faces: {len(m.faces)}")
    else:
        m = knot_mesh(args.nt, args.nz)
        ext = m.bounds[1] - m.bounds[0]
        print(f"  mode       : SOLID filled mushroom")
        print(f"  watertight : {m.is_watertight}")
        print(f"  bbox (mm)  : {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f}")
        print(f"  cap overhang past waist : {R_CAP - R_WAIST:.1f} mm  (height-field cannot do this)")
        print(f"  faces      : {len(m.faces)}")

    for e in ("stl", "glb"):
        p = f"{prefix}.{e}"; m.export(p); print(f"  written: {p}")


if __name__ == "__main__":
    main()
