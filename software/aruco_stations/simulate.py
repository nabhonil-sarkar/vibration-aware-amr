"""Offline test of the whole chain: synthetic camera frames -> real ArUco detection -> station seeker
-> simulated robot. One station is moved mid-run to show the robot finding it again.

SYNTHETIC. This proves the software logic only. It says nothing about the real camera, lighting,
motors or floor.

Run: python simulate.py --out sim_outputs
"""
import argparse, csv, json, math
from pathlib import Path
import numpy as np
import cv2
import stations as S

CAM_FORWARD = 0.117     # camera is this far ahead of the robot centre (from the v05.1 model)
MARGIN = 0.25           # white border around each printed marker, as a fraction of its size


class World:
    def __init__(self, camera, markers, seed=1):
        self.cam = camera
        self.markers = dict(markers)       # id -> (x, y, facing_rad)
        self.rng = np.random.default_rng(seed)
        self.tiles = {}
        for i in self.markers:
            m = S.marker_image(i, 200)
            pad = int(200 * MARGIN)
            self.tiles[i] = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)

    def render(self, x, y, th):
        """Grey room, markers drawn in perspective at camera height. Returns an 8-bit grey image."""
        W, H = self.cam.width, self.cam.height
        img = np.full((H, W), 118, np.uint8)
        img[H // 2:, :] = 96                                    # darker floor below the horizon
        cxw, cyw = x + CAM_FORWARD * math.cos(th), y + CAM_FORWARD * math.sin(th)
        F = np.array([math.cos(th), math.sin(th)]); Rv = np.array([math.sin(th), -math.cos(th)])
        order = sorted(self.markers.items(), key=lambda kv: -math.hypot(kv[1][0] - cxw, kv[1][1] - cyw))
        for i, (mx, my, phi) in order:
            f = np.array([math.cos(phi), math.sin(phi)])
            to_cam = np.array([cxw - mx, cyw - my])
            dist = float(np.linalg.norm(to_cam))
            if dist < 0.12 or float(f @ to_cam) / dist < math.cos(math.radians(78)):
                continue                                         # facing away or edge-on
            right = np.array([-f[1], f[0]])                      # viewer's right when facing the marker
            h = S.MARKER_SIZE_M * (1 + 2 * MARGIN) / 2
            quad = []
            for sx, sz in ((-1, 1), (1, 1), (1, -1), (-1, -1)):   # TL, TR, BR, BL
                p = np.array([mx, my]) + right * sx * h
                d = p - np.array([cxw, cyw])
                zc, xc, yc = float(d @ F), float(d @ Rv), -sz * h
                if zc < 0.08:
                    quad = None; break
                quad.append((self.cam.fx * xc / zc + self.cam.cx, self.cam.fy * yc / zc + self.cam.cy))
            if quad is None:
                continue
            tile = self.tiles[i]; n = tile.shape[0]
            Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [n, 0], [n, n], [0, n]]), np.float32(quad))
            warped = cv2.warpPerspective(tile, Hm, (W, H), flags=cv2.INTER_AREA, borderValue=0)
            mask = cv2.warpPerspective(np.full_like(tile, 255), Hm, (W, H), flags=cv2.INTER_NEAREST, borderValue=0)
            img[mask > 127] = warped[mask > 127]
        img = cv2.GaussianBlur(img, (3, 3), 0)
        noise = self.rng.normal(0, 3.0, img.shape)
        return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def run(out, move=True, seed=1, dt=0.1, t_max=400.0):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    cam = S.Camera.approximate(1014, 760, 66.0)
    markers = {0: (2.2, 0.3, math.radians(180)), 1: (1.0, 2.2, math.radians(-90)), 2: (-1.8, -0.2, math.radians(40))}
    moved_to = (-0.8, 2.0, math.radians(-45))
    world = World(cam, markers, seed)
    det = S.Detector(cam)
    seeker = S.StationSeeker(['pickup', 'dropoff', 'recharge'])
    rng = np.random.default_rng(seed + 7)
    x = y = th = 0.0
    t, rows, moved_at, frames_saved = 0.0, [], None, 0
    truth = []
    while t < t_max and seeker.state not in (seeker.DONE, seeker.FAILED):
        frame = world.render(x, y, th)
        dets = det.detect(frame)
        n_before = len(seeker.arrivals)
        cmd = seeker.update(dets, t)
        if len(seeker.arrivals) > n_before:                      # ground truth at the moment of arrival
            a = seeker.arrivals[-1]
            mid = [k for k, v in S.STATIONS.items() if v == a.station][0]
            mx, my, _ = world.markers[mid]
            cxw, cyw = x + CAM_FORWARD * math.cos(th), y + CAM_FORWARD * math.sin(th)
            true_d = math.hypot(mx - cxw, my - cyw)
            true_b = math.atan2(math.sin(th - math.atan2(my - cyw, mx - cxw)), math.cos(th - math.atan2(my - cyw, mx - cxw)))
            truth.append(dict(station=a.station, time_s=round(t, 1), true_distance_m=round(true_d, 4),
                              stop_error_mm=round((true_d - seeker.cfg.stop_distance) * 1000, 1),
                              true_bearing_deg=round(math.degrees(true_b), 2),
                              estimated_distance_m=round(a.distance_m, 4), marker_yaw_deg=round(math.degrees(a.yaw_rad), 1)))
        tgt = [d for d in dets if d.station == cmd.target]
        if move and moved_at is None and cmd.target == 'dropoff' and cmd.state == 'APPROACH' and tgt and tgt[0].distance_m < 1.5:
            world.markers[1] = moved_to; moved_at = t
        if cmd.state == 'APPROACH' and tgt and frames_saved < 3 and int(t * 10) % 60 == 0:
            cv2.imwrite(str(out / f'synthetic_frame_{frames_saved + 1}.png'), S.draw_detections(frame, dets, cmd.target)); frames_saved += 1
        rows.append([round(t, 2), round(x, 4), round(y, 4), round(th, 4), cmd.state, cmd.target,
                     ' '.join(str(d.marker_id) for d in dets), round(tgt[0].distance_m, 3) if tgt else '',
                     round(math.degrees(tgt[0].bearing_rad), 2) if tgt else '', round(cmd.v, 4), round(cmd.w, 4), cmd.note])
        v = cmd.v * (1 + rng.normal(0, 0.03)); w = cmd.w * (1 + rng.normal(0, 0.03))   # imperfect drive
        x += v * math.cos(th) * dt; y += v * math.sin(th) * dt; th += w * dt
        t += dt
    with (out / 'sim_log.csv').open('w', newline='') as fh:
        wr = csv.writer(fh)
        wr.writerow(['t_s', 'x_m', 'y_m', 'heading_rad', 'state', 'target', 'visible_ids', 'target_distance_m', 'target_bearing_deg', 'v_cmd', 'w_cmd', 'note'])
        wr.writerows(rows)
    summary = dict(data_type='SYNTHETIC camera frames and simulated robot; no hardware involved',
                   final_state=seeker.state, sim_time_s=round(t, 1), stations_reached=[a.station for a in seeker.arrivals],
                   dropoff_marker_moved_at_s=None if moved_at is None else round(moved_at, 1),
                   arrivals=truth, max_v_cmd=max(r[9] for r in rows), max_abs_w_cmd=max(abs(r[10]) for r in rows),
                   camera=dict(width=cam.width, height=cam.height, hfov_deg=66.0, calibrated=False), marker_size_m=S.MARKER_SIZE_M)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2))
    plot(out, rows, markers, moved_to if moved_at is not None else None, world.markers, moved_at)
    return summary


def plot(out, rows, start_markers, moved_to, final_markers, moved_at):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 8.4)); fig.patch.set_facecolor('white')
    cols = {'SEARCH': '#DD8452', 'APPROACH': '#4C72B0', 'DWELL': '#55A868', 'DONE': '#55A868', 'FAILED': '#C44E52'}
    xs = np.array([r[1] for r in rows]); ys = np.array([r[2] for r in rows]); st = [r[4] for r in rows]
    for s in ('APPROACH', 'SEARCH', 'DWELL'):
        idx = [k for k, v in enumerate(st) if v == s]
        if idx:
            ax.scatter(xs[idx], ys[idx], s=7, color=cols[s], label={'APPROACH': 'driving to marker', 'SEARCH': 'turning to look', 'DWELL': 'stopped at station'}[s], zorder=3)
    ax.plot(xs[0], ys[0], 'k^', ms=11, zorder=5); ax.annotate('start', (xs[0], ys[0]), textcoords='offset points', xytext=(8, -14))

    def mark(m, name, style):
        mx, my, phi = m
        r = np.array([-math.sin(phi), math.cos(phi)]) * 0.12
        ax.plot([mx - r[0], mx + r[0]], [my - r[1], my + r[1]], lw=5, solid_capstyle='butt', zorder=4, **style)
        ax.arrow(mx, my, 0.22 * math.cos(phi), 0.22 * math.sin(phi), head_width=0.06, color=style['color'], alpha=style.get('alpha', 1), zorder=4)
        ax.annotate(name, (mx, my), textcoords='offset points', xytext=(10, 10), fontsize=11, color=style['color'], alpha=style.get('alpha', 1))
    names = {0: 'pick-up (id 0)', 1: 'drop-off (id 1)', 2: 'recharge (id 2)'}
    for i, m in final_markers.items():
        mark(m, names[i] + (' after move' if (i == 1 and moved_to is not None) else ''), dict(color='#1F2A44'))
    if moved_to is not None:
        mark(start_markers[1], 'drop-off before move', dict(color='#999999', alpha=0.9))
        ax.annotate('', xy=final_markers[1][:2], xytext=start_markers[1][:2], arrowprops=dict(arrowstyle='->', ls='--', color='#999999'))
    ax.margins(0.14); ax.set_aspect('equal'); ax.grid(color='#E5E8EC'); ax.set_xlabel('x (m)'); ax.set_ylabel('y (m)')
    ax.legend(loc='lower right', markerscale=2.5)
    title = 'Seek-by-sight station run, SYNTHETIC test'
    if moved_at is not None:
        title += f'\nDrop-off marker moved at t = {moved_at:.0f} s; the robot turned, found it again and carried on'
    ax.set_title(title, fontsize=13)
    fig.text(0.5, 0.012, 'Simulated robot and rendered camera frames. Real ArUco detection code, no real hardware.', ha='center', fontsize=9, color='#9b3b20')
    fig.tight_layout(rect=(0, 0.025, 1, 1)); fig.savefig(out / 'trajectory.png', dpi=130); plt.close(fig)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='sim_outputs'); ap.add_argument('--no-move', action='store_true')
    print(json.dumps(run(ap.parse_args().out, move=not ap.parse_args().no_move), indent=2))
