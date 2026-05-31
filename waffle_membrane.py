"""
waffle_membrane.py  -- v2 (GTT Mark III faithful upgrade)
=========================================================
Constant-thickness 1.2 mm GTT Mark III PRIMARY "waffle" membrane
(Bengtsson, US 3,199,963) as a height-field thin shell.

What changed vs v1 (from the Mark III audit):
  * DUAL-HEIGHT corrugations -- real large = 54 mm, small = 37.2 mm (was a single
    34 mm rib in both directions). The large family rides OVER the small at the
    crossing, so the "knot" now sits at ~large-corrugation height automatically.
  * Realistic CROSS-SECTION -- trapezoidal profile (flat valley + straight flanks
    + flat crest), closer to the real omega/arc-plus-flank section than a cosine.
  * TRUE constant thickness -- the bottom surface is offset along the local
    surface NORMAL (not vertically), so the wall stays 1.2 mm on the steep flanks
    instead of thinning to ~0.79 mm (T*cos(slope)) as a vertical offset does.
  * PANEL mode -- independent NX x NY cells; the standard strake = 3 x 9 cells
    (1020 x 3060 mm), matching GTT's ~1 m x 3 m sheet.

Real spec (sources: GTT/MARIN ISOPE Bogaert 2010; sea-man.org "MARK III System";
UCL/Paik membrane FE paper):
    pitch P = 340 mm   thickness t = 1.2 mm   304L stainless
    large corrugation = 54 mm   small corrugation = 37.2 mm
    standard sheet ~ 3 m x 1 m (3 x 9 corrugation cells)

LIMITATION: a single-valued z(x,y) height-field cannot represent the knot's
folded / overhanging "mushroom" pleats or near-vertical / re-entrant flanks.
The knot is therefore an APPROXIMATION; a faithful folded node needs a B-rep
(see waffle_cad_step.py and the report). This file is the geometrically clean
thin-shell mesh for visualization / 3D-print / FE seeding.

Install:  pip install numpy trimesh
Run:      python waffle_membrane.py            # default 3x3 cells
          python waffle_membrane.py --panel    # full 3x9 strake (1020x3060)
Output:   waffle_membrane.{stl,obj,glb}        # units = millimetres
"""

from __future__ import annotations
import sys
import argparse
import numpy as np
import trimesh

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --------------------------------------------------------------------------- #
#  Parameters (mm) -- GTT Mark III primary membrane
# --------------------------------------------------------------------------- #
P        = 340.0    # corrugation pitch = node spacing (both families)  [confirmed]
T        = 1.2      # sheet thickness, 304L                              [confirmed]
H_LARGE  = 54.0     # large corrugation crest height                     [confirmed]
H_SMALL  = 37.2     # small corrugation crest height                     [confirmed]
# Cross-section shape, as fractions of the half-pitch (0..0.5 from a ridge centre):
CREST    = 0.09     # |t| <= CREST  -> flat crest (value 1) -- narrow ridge top
VALLEY   = 0.27     # |t| >= VALLEY -> flat valley (value 0) -- wide flat field; steep flank between
P_NORM   = 8.0      # soft-max sharpness where the two families cross (knot)
RES      = 24       # grid points per cell per axis (mesh resolution)


def R(frac):
    """Single-corrugation cross-section over fractional position frac in [-0.5, 0.5].
    Trapezoid: flat crest within +/-CREST, straight flank to 0 at +/-VALLEY, flat valley."""
    a = np.abs(frac)
    return np.clip((VALLEY - a) / (VALLEY - CREST), 0.0, 1.0)


def ridge(coord):
    """Periodic corrugation ridge: crest at integer multiples of P, valley between."""
    t = coord / P
    return R(t - np.round(t))


def z_top(x, y):
    """Height field of the membrane top surface.
    large family = ridges running along X (periodic in Y) at H_LARGE,
    small family = ridges running along Y (periodic in X) at H_SMALL,
    combined by a p-norm soft-max so the large rides over the small at the knot."""
    la = H_LARGE * ridge(y)
    sm = H_SMALL * ridge(x)
    return (la ** P_NORM + sm ** P_NORM) ** (1.0 / P_NORM)


def build_membrane(nx_cells, ny_cells):
    """Watertight constant-thickness shell with NORMAL-offset bottom surface."""
    nx = nx_cells * RES + 1
    ny = ny_cells * RES + 1
    xs = np.linspace(0.0, nx_cells * P, nx)
    ys = np.linspace(0.0, ny_cells * P, ny)
    X, Y = np.meshgrid(xs, ys)                      # (ny, nx)
    Z = z_top(X, Y)

    # Surface normal of the height field via numeric gradient (uniform spacing).
    dzdy, dzdx = np.gradient(Z, ys, xs)             # axis0 = y, axis1 = x
    nrm = np.sqrt(dzdx ** 2 + dzdy ** 2 + 1.0)
    nX, nY, nZ = -dzdx / nrm, -dzdy / nrm, 1.0 / nrm
    max_slope = np.degrees(np.arctan(np.sqrt(dzdx ** 2 + dzdy ** 2)).max())

    top = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    bot = np.stack([X - T * nX, Y - T * nY, Z - T * nZ], axis=-1).reshape(-1, 3)
    NT = nx * ny
    verts = np.vstack([top, bot])

    def idx(i, j):                                  # i along x, j along y
        return j * nx + i

    I, J = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1))
    a = (J * nx + I).ravel()
    b = (J * nx + I + 1).ravel()
    c = ((J + 1) * nx + I + 1).ravel()
    d = ((J + 1) * nx + I).ravel()

    faces = []
    # top surface (outward up)
    faces.append(np.stack([a, b, c], axis=1))
    faces.append(np.stack([a, c, d], axis=1))
    # bottom surface (outward down -> reversed winding), shifted by NT
    faces.append(np.stack([a + NT, c + NT, b + NT], axis=1))
    faces.append(np.stack([a + NT, d + NT, c + NT], axis=1))

    # perimeter side walls (top loop <-> bottom loop)
    def wall(seq):
        s = np.asarray(seq)
        t0, t1 = s[:-1], s[1:]
        b0, b1 = t0 + NT, t1 + NT
        return [np.stack([t0, b0, b1], axis=1), np.stack([t0, b1, t1], axis=1)]

    bottom_edge = [idx(i, 0) for i in range(nx)]
    top_edge    = [idx(i, ny - 1) for i in range(nx)]
    left_edge   = [idx(0, j) for j in range(ny)]
    right_edge  = [idx(nx - 1, j) for j in range(ny)]
    for e in (bottom_edge, top_edge, left_edge, right_edge):
        faces.extend(wall(e))

    faces = np.vstack(faces)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    mesh.merge_vertices()
    mesh.fix_normals()
    return mesh, max_slope


def main():
    ap = argparse.ArgumentParser(description="GTT Mark III waffle membrane (height-field shell)")
    ap.add_argument("--panel", action="store_true", help="full 3x9 strake (1020x3060 mm)")
    ap.add_argument("--nx", type=int, default=3, help="cells in X (default 3)")
    ap.add_argument("--ny", type=int, default=3, help="cells in Y (default 3)")
    ap.add_argument("--prefix", default="waffle_membrane", help="output filename prefix")
    args = ap.parse_args()
    nx_cells, ny_cells = (3, 9) if args.panel else (args.nx, args.ny)

    print("=== GTT Mark III waffle membrane (US 3,199,963) -- height-field v2 ===")
    print(f"  P={P}  t={T}  H_large={H_LARGE}  H_small={H_SMALL}")
    print(f"  cells {nx_cells} x {ny_cells}  ->  panel {nx_cells*P:.0f} x {ny_cells*P:.0f} mm")

    mesh, max_slope = build_membrane(nx_cells, ny_cells)
    ext = mesh.bounds[1] - mesh.bounds[0]
    print(f"  watertight   : {mesh.is_watertight}")
    print(f"  bbox (mm)    : {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f}")
    print(f"  faces        : {len(mesh.faces)}")
    print(f"  volume (cm3) : {mesh.volume/1000.0:.1f}")
    print(f"  max flank slope : {max_slope:.1f} deg  "
          f"(a vertical offset would thin the wall to {T*np.cos(np.radians(max_slope)):.3f} mm there; "
          f"normal offset keeps it {T:.1f} mm)")

    for ext_name in ("stl", "obj", "glb"):
        path = f"{args.prefix}.{ext_name}"
        mesh.export(path)
        print(f"  written: {path}")


if __name__ == "__main__":
    main()
