"""
Cross-section render of the constant-thickness THIN-WALL outputs (items 1 & 2).
A planar slice is the clearest proof of a thin wall: it shows two parallel skins
~t apart following the corrugation / fold, plus the near-vertical (80 deg) flanks.

  waffle_membrane_thin_cad.stl  -> slice at y=0  (membrane corrugation wall)
  waffle_knot_thin.stl          -> slice at y=0  (folded-sheet wall)

Output: waffle_render_thin.png
"""
from __future__ import annotations
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def section_xz(path, y=0.0):
    m = trimesh.load(path, force="mesh")
    sec = m.section(plane_origin=[0.0, y, 0.0], plane_normal=[0.0, 1.0, 0.0])
    if sec is None:
        return m, []
    polys = [np.asarray(e)[:, [0, 2]] for e in sec.discrete]   # drop Y -> (x,z)
    return m, polys


def main():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, path, title, xlim, ylim in [
        (axes[0], "waffle_membrane_thin_cad.stl",
         "Membrane thin-wall B-rep  (slice y=0, zoom on one corrugation)\n"
         "steep 80-deg flank, constant 1.2 mm wall",
         (120.0, 220.0), (-5.0, 45.0)),
        (axes[1], "waffle_knot_thin.stl",
         "Folded knot thin-wall  (slice y=0)\nnormal-offset 1.2 mm sheet, open underneath",
         None, None),
    ]:
        try:
            m, polys = section_xz(path)
            for p in polys:
                ax.plot(p[:, 0], p[:, 1], "-", color="#1f5fbf", lw=1.2)
            ax.set_title(title, fontsize=10)
            ax.set_aspect("equal")
            if xlim: ax.set_xlim(*xlim)
            if ylim: ax.set_ylim(*ylim)
            ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
            ax.grid(True, ls=":", alpha=0.4)
            print(f"  {path}: {len(polys)} section loops")
        except Exception as e:
            ax.set_title(f"{title}\n[render failed: {type(e).__name__}]", fontsize=9)
            print(f"  {path}: FAILED {type(e).__name__}: {e}")

    fig.suptitle("GTT Mark III waffle membrane -- constant-thickness thin-wall cross-sections "
                 "(items 1 & 2)", fontsize=12)
    fig.tight_layout()
    out = "waffle_render_thin.png"
    fig.savefig(out, dpi=130)
    print(f"written: {out}")


if __name__ == "__main__":
    main()
