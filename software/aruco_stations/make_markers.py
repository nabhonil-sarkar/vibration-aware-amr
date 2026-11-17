"""Make the printable station markers: one A4 page per station in a single PDF, plus PNGs.

Print at 100 % ("actual size", NOT "fit to page") on matte paper. Check the 100 mm bar with a ruler.
Run: python make_markers.py --out markers
"""
import argparse
from pathlib import Path
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import stations as S

A4_W, A4_H = 210.0, 297.0          # mm
TITLES = {'pickup': 'PICK-UP', 'dropoff': 'DROP-OFF', 'recharge': 'RECHARGE', 'spare': 'SPARE'}


def page(pdf, marker_id, name, size_mm):
    fig = plt.figure(figsize=(A4_W / 25.4, A4_H / 25.4)); fig.patch.set_facecolor('white')
    left, bottom = (A4_W - size_mm) / 2, 128.0
    ax = fig.add_axes([left / A4_W, bottom / A4_H, size_mm / A4_W, size_mm / A4_H])
    ax.imshow(S.marker_image(marker_id, 600), cmap='gray', vmin=0, vmax=255, interpolation='nearest'); ax.set_axis_off()
    # light cut guide leaving a 25 mm white border, which the detector needs
    b = 25.0
    g = fig.add_axes([(left - b) / A4_W, (bottom - b) / A4_H, (size_mm + 2 * b) / A4_W, (size_mm + 2 * b) / A4_H])
    g.set_xticks([]); g.set_yticks([]); g.patch.set_alpha(0)
    for sp in g.spines.values():
        sp.set_linestyle((0, (4, 4))); sp.set_color('#AAAAAA'); sp.set_linewidth(0.6)
    fig.text(0.5, 274 / A4_H, f'STATION {marker_id}:  {TITLES.get(name, name.upper())}', ha='center', fontsize=30, fontweight='bold')
    fig.text(0.5, 262 / A4_H, f'ArUco {S.DICT_NAME}, id {marker_id}', ha='center', fontsize=13, color='#444444')
    fig.text(0.5, 92 / A4_H, 'Cut along the dashed line. Keep the white border.', ha='center', fontsize=11, color='#444444')
    # 100 mm check bar
    bar = fig.add_axes([(A4_W - 100) / 2 / A4_W, 62 / A4_H, 100 / A4_W, 3 / A4_H])
    bar.set_xticks([]); bar.set_yticks([]); bar.set_facecolor('black')
    fig.text(0.5, 54 / A4_H, 'This bar must measure exactly 100 mm. If it does not, reprint at 100 % scale.', ha='center', fontsize=10)
    fig.text(0.5, 40 / A4_H, f'Black square: {size_mm:g} mm. Mount upright and flat, centre about 135 mm above the floor (camera height).',
             ha='center', fontsize=10, color='#444444')
    fig.text(0.5, 32 / A4_H, 'Matte paper on stiff card. Avoid glossy lamination and direct glare.', ha='center', fontsize=10, color='#444444')
    pdf.savefig(fig); plt.close(fig)


def run(out, size_mm=100.0):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    with PdfPages(out / 'AMR_Station_Markers_A4.pdf') as pdf:
        for i, name in S.STATIONS.items():
            page(pdf, i, name, size_mm)
            cv2.imwrite(str(out / f'station_{i}_{name}.png'), cv2.copyMakeBorder(S.marker_image(i, 800), 200, 200, 200, 200, cv2.BORDER_CONSTANT, value=255))
    return out / 'AMR_Station_Markers_A4.pdf'


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='markers'); ap.add_argument('--size-mm', type=float, default=100.0)
    a = ap.parse_args(); print(run(a.out, a.size_mm))
