"""
3-view render of the folded Mark III knot (report item 3), regrounded so every node
dimension is DERIVED from the real corrugation spec. Shows the axis-aligned 4-fold
arms, the 2-fold large/small asymmetry, and the reserve-length overhang (mushroom
profile) that a single-valued height-field cannot represent.

Output: waffle_render_knot.png
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


def main():
    m = trimesh.load("waffle_knot.stl", force="mesh")
    V, F = m.vertices, m.faces
    fig = plt.figure(figsize=(15, 5))

    # --- (1) isometric 3-D surface ---
    ax = fig.add_subplot(1, 3, 1, projection="3d")
    ax.plot_trisurf(V[:, 0], V[:, 1], F, V[:, 2], color="#9fb8e0",
                    edgecolor="none", linewidth=0, antialiased=True, shade=True)
    ax.set_title("isometric — folded node (solid)", fontsize=10)
    ax.view_init(elev=24, azim=35)
    ax.set_box_aspect((1, 1, 0.45))
    for a in (ax.set_xlabel, ax.set_ylabel): a("mm")
    ax.set_zlabel("z")

    # --- (2) top view (xy): clean ring outlines -> 4-fold arms + 2-fold asymmetry ---
    ax2 = fig.add_subplot(1, 3, 2)
    import waffle_knot as wk
    grid = wk._ring_grid(wk.NT, wk.NZ)                    # (nz, nt, 3)
    for k, lab, col in [(0, "base z=0", "#1f5fbf"),
                        (wk.NZ // 2, "waist", "#bf5f1f"),
                        (wk.NZ - 1, "cap z=54", "#1f9f4f")]:
        ring = np.vstack([grid[k], grid[k, :1]])         # close the loop
        ax2.plot(ring[:, 0], ring[:, 1], "-", lw=1.3, color=col, label=lab)
    ax2.axhline(0, color="k", lw=0.4, ls=":"); ax2.axvline(0, color="k", lw=0.4, ls=":")
    ax2.legend(fontsize=7, loc="upper right")
    ax2.set_title("top view — arms along corr. axes\n(x=large ~192, y=small ~157)", fontsize=10)
    ax2.set_aspect("equal"); ax2.set_xlabel("x (mm)"); ax2.set_ylabel("y (mm)")

    # --- (3) cross-section through y=0 (the overhang / reserve-length fold) ---
    ax3 = fig.add_subplot(1, 3, 3)
    sec = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    if sec is not None:
        for e in sec.discrete:
            p = np.asarray(e)
            ax3.plot(p[:, 0], p[:, 2], "-", color="#1f5fbf", lw=1.2)
    ax3.set_title("section y=0 — waist@37.2 (small crest)\nflare/overhang = reserve fold", fontsize=10)
    ax3.set_aspect("equal"); ax3.set_xlabel("x (mm)"); ax3.set_ylabel("z (mm)")
    ax3.grid(True, ls=":", alpha=0.4)

    fig.suptitle("GTT Mark III folded knot — dimensions DERIVED from the corrugation spec "
                 "(item 3); exact press fold is GTT-proprietary", fontsize=12)
    fig.tight_layout()
    out = "waffle_render_knot.png"
    fig.savefig(out, dpi=130)
    print(f"written: {out}  (bbox {m.extents[0]:.0f} x {m.extents[1]:.0f} x {m.extents[2]:.0f} mm)")


if __name__ == "__main__":
    main()
