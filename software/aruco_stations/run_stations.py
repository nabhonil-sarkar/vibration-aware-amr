"""Run station finding on the Raspberry Pi (or on saved images / a webcam on a laptop).

By default this is a DRY RUN: it looks through the camera, decides what the robot should do and
logs the commands, but sends nothing to the motors. Carry the robot or the camera by hand to try it.
Motor output is deliberately not implemented here: fill in send_command() only once the STM32 drive
link, command timeout and the hardwired E-stop have been commissioned.

Examples
  python run_stations.py --picamera --seconds 60 --save-frames
  python run_stations.py --images some_folder
  python run_stations.py --webcam 0 --mission pickup dropoff
"""
import argparse, csv, glob, json, math, time
from pathlib import Path
import cv2
import stations as S


def send_command(v, w):
    """Hook for the drive link. Not implemented on purpose: this program does not move the robot."""
    return None


class PiCamera:
    """Raspberry Pi camera through picamera2 (Raspberry Pi OS). Untested on the real Pi so far."""
    def __init__(self, width, height):
        from picamera2 import Picamera2
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_video_configuration(main={'size': (width, height), 'format': 'RGB888'}))
        self.cam.start(); time.sleep(1.0)

    def read(self):
        return cv2.cvtColor(self.cam.capture_array('main'), cv2.COLOR_BGR2GRAY)

    def close(self):
        self.cam.stop()


class Webcam:
    def __init__(self, index, width, height):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width); self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError(f'could not open webcam {index}')

    def read(self):
        ok, frame = self.cap.read()
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if ok else None

    def close(self):
        self.cap.release()


class Images:
    def __init__(self, folder):
        self.files = sorted(sum((glob.glob(str(Path(folder) / e)) for e in ('*.png', '*.jpg', '*.jpeg')), []))
        if not self.files:
            raise RuntimeError(f'no images in {folder}')
        self.i = 0

    def read(self):
        if self.i >= len(self.files):
            return None
        img = cv2.imread(self.files[self.i], cv2.IMREAD_GRAYSCALE); self.i += 1
        return img

    def close(self):
        pass


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--picamera', action='store_true'); src.add_argument('--webcam', type=int); src.add_argument('--images')
    ap.add_argument('--mission', nargs='+', default=['pickup', 'dropoff', 'recharge'])
    ap.add_argument('--width', type=int, default=1014); ap.add_argument('--height', type=int, default=760)
    ap.add_argument('--hfov', type=float, default=66.0, help='horizontal field of view in degrees if no calibration file')
    ap.add_argument('--calibration', help='camera calibration JSON (width, height, fx, fy, cx, cy, dist)')
    ap.add_argument('--marker-mm', type=float, default=100.0)
    ap.add_argument('--seconds', type=float, default=60.0)
    ap.add_argument('--save-frames', action='store_true', help='save an annotated picture about once a second')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()

    out = Path(a.out or time.strftime('runs/stations_%Y%m%d_%H%M%S')); out.mkdir(parents=True, exist_ok=False)
    source = PiCamera(a.width, a.height) if a.picamera else Webcam(a.webcam, a.width, a.height) if a.webcam is not None else Images(a.images)
    first = source.read()
    if first is None:
        raise RuntimeError('no frame from the camera')
    h, w = first.shape[:2]
    cam = S.Camera.from_json(a.calibration) if a.calibration else S.Camera.approximate(w, h, a.hfov)
    det = S.Detector(cam, a.marker_mm / 1000.0)
    seeker = S.StationSeeker(a.mission)
    print(f'Frame {w} x {h}. Camera calibrated: {cam.calibrated}. DRY RUN: no motor commands are sent. Output: {out}')
    rows, t0, last_save, n, frame = [], time.monotonic(), -1.0, 0, first
    try:
        while frame is not None:
            t = (n * 0.1) if a.images else (time.monotonic() - t0)     # still images are stepped at 0.1 s
            if t > a.seconds and not a.images:
                break
            dets = det.detect(frame)
            cmd = seeker.update(dets, t)
            send_command(cmd.v, cmd.w)
            tgt = [d for d in dets if d.station == cmd.target]
            rows.append([round(t, 3), cmd.state, cmd.target, ' '.join(str(d.marker_id) for d in dets),
                         round(tgt[0].distance_m, 3) if tgt else '', round(math.degrees(tgt[0].bearing_rad), 2) if tgt else '',
                         round(cmd.v, 4), round(cmd.w, 4), cmd.note])
            if n % 10 == 0:
                seen = ', '.join(f'{d.station} {d.distance_m:.2f} m {math.degrees(d.bearing_rad):+.0f} deg' for d in dets) or 'no markers'
                print(f'{t:6.1f} s  {cmd.state:8s} target {cmd.target:9s} v {cmd.v:.2f} w {cmd.w:+.2f}  | {seen}')
            if a.save_frames and (t - last_save >= 1.0 or a.images):
                cv2.imwrite(str(out / f'frame_{n:05d}.jpg'), S.draw_detections(frame, dets, cmd.target)); last_save = t
            if seeker.state in (seeker.DONE, seeker.FAILED):
                break
            n += 1
            frame = source.read()
    except KeyboardInterrupt:
        print('stopped by Ctrl+C')
    finally:
        send_command(0.0, 0.0)
        source.close()
        with (out / 'station_log.csv').open('w', newline='') as fh:
            wr = csv.writer(fh)
            wr.writerow(['t_s', 'state', 'target', 'visible_ids', 'target_distance_m', 'target_bearing_deg', 'v_cmd', 'w_cmd', 'note'])
            wr.writerows(rows)
        (out / 'summary.json').write_text(json.dumps(dict(
            dry_run=True, final_state=seeker.state, frames=len(rows), mission=a.mission, camera_calibrated=cam.calibrated,
            frame_size=[w, h], marker_mm=a.marker_mm,
            arrivals=[dict(station=x.station, time_s=round(x.time, 2), distance_m=round(x.distance_m, 3),
                           bearing_deg=round(math.degrees(x.bearing_rad), 2), marker_yaw_deg=round(math.degrees(x.yaw_rad), 1)) for x in seeker.arrivals]), indent=2))
        print(f'Final state {seeker.state}. Log saved in {out}')


if __name__ == '__main__':
    main()
