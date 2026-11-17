"""Render the v05.2 assembly and the print-part overview from the meshes the build scripts pickle.
Orthographic, flat Lambert shading, painter's sort. Usage: python render_v052.py ASM_PKL PRINT_PKL OUTDIR"""
import sys, pickle
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection


def view_matrix(az, el):
    a, e = np.radians(az), np.radians(el)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])   # camera looks along -fwd
    right = np.cross([0, 0, 1], fwd); right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    return right, up, fwd


def draw(ax, meshes, az, el, light=(0.4, -0.5, 0.9), edge=False):
    right, up, fwd = view_matrix(az, el)
    L = np.array(light, float); L /= np.linalg.norm(L)
    polys, cols, depth = [], [], []
    for m in meshes:
        V, T, c = m['V'], m['T'], np.array(m['colour'][:3])
        if len(T) == 0:
            continue
        tri = V[T]                                         # (n,3,3)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn = np.linalg.norm(n, axis=1); ok = nn > 1e-9
        tri, n = tri[ok], n[ok] / nn[ok, None]
        facing = n @ fwd > -0.05                           # back-face cull (keep near-silhouette faces)
        tri, n = tri[facing], n[facing]
        shade = 0.35 + 0.65 * np.clip(np.abs(n @ L), 0, 1)
        p2 = np.stack([tri @ right, tri @ up], axis=-1)
        polys.extend(p2); cols.extend(np.clip(c[None, :] * shade[:, None], 0, 1)); depth.extend((tri @ fwd).mean(axis=1))
    order = np.argsort(depth)
    pc = PolyCollection([polys[i] for i in order], facecolors=[cols[i] for i in order],
                        edgecolors=[cols[i] for i in order] if not edge else 'k', linewidths=0.15)
    ax.add_collection(pc)
    allp = np.concatenate(polys)
    ax.set_xlim(allp[:, 0].min() - 5, allp[:, 0].max() + 5); ax.set_ylim(allp[:, 1].min() - 5, allp[:, 1].max() + 5)
    ax.set_aspect('equal'); ax.axis('off')


def main(asm_pkl, print_pkl, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    asm = pickle.load(open(asm_pkl, 'rb'))
    fig, axs = plt.subplots(1, 2, figsize=(16, 8))
    draw(axs[0], asm, az=-135, el=25); axs[0].set_title('Front-right view', fontsize=13)
    draw(axs[1], asm, az=150, el=20); axs[1].set_title('Rear-left view', fontsize=13)
    fig.suptitle('Vibration-Aware AMR v05.2 concept (drive, wheels and caster from caliper measurements, 17 Nov 2026)', fontsize=14)
    fig.text(0.5, 0.02, '241 x 300 x 206 mm. Purchased parts are envelopes; nothing here is a test result.', ha='center', fontsize=10, color='0.3')
    plt.tight_layout(rect=(0, 0.04, 1, 0.95)); fig.savefig(out / 'AMR_v05_2_Concept.png', dpi=110); plt.close(fig)

    drive = [m for m in asm if m['name'].startswith('D_Left') or m['name'].startswith('C_Base')]
    drive = [m for m in drive if 'Baseplate' not in m['name']]
    fig, ax = plt.subplots(figsize=(9, 6))
    draw(ax, drive, az=-60, el=-20); ax.set_title('Left drive module v05.2 from below: motor, cradle, cap, adapter, wheel', fontsize=12)
    plt.tight_layout(); fig.savefig(out / 'AMR_v05_2_Left_Drive_Module.png', dpi=110); plt.close(fig)

    pp = pickle.load(open(print_pkl, 'rb'))
    names = sorted(pp)
    cols = 4; rows = int(np.ceil(len(names) / cols))
    fig, axs = plt.subplots(rows, cols, figsize=(16, 4 * rows))
    for ax, n in zip(axs.flat, names):
        V, T, g = pp[n]
        colour = (0.30, 0.66, 0.62) if n[:2] in ('10', '11', '12', '13', '14', '15') else (0.55, 0.62, 0.70)
        draw(ax, [dict(name=n, V=V, T=T, colour=colour)], az=-50, el=30)
        ax.set_title(n.replace('_', ' '), fontsize=10)
    for ax in list(axs.flat)[len(names):]:
        ax.axis('off')
    fig.suptitle('AMR v05.2 print parts, in print orientation (green = rebuilt 17 Nov from measurements)', fontsize=14)
    plt.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(out / 'Print_Parts_Overview.png', dpi=90); plt.close(fig)


if __name__ == '__main__':
    main(*sys.argv[1:4])
