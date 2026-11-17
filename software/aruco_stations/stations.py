"""ArUco station finding for the vibration-aware AMR ("seek by sight").

This file holds the logic only: marker detection, distance/bearing estimation and the
station-seeking state machine. It does not open a camera and it does not drive motors.

Conventions
- Bearing is positive when the marker is to the RIGHT of the camera's centre line.
- Angular command w is positive for a LEFT (counter-clockwise) turn, as in ROS.
- Distances are in metres, measured from the camera, along the floor.
"""
from dataclasses import dataclass, field
import json
import math
import numpy as np
import cv2

DICT_NAME = 'DICT_4X4_50'
STATIONS = {0: 'pickup', 1: 'dropoff', 2: 'recharge', 3: 'spare'}
MARKER_SIZE_M = 0.100   # black square, outer edge to outer edge


def get_dictionary():
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DICT_NAME))


def marker_image(marker_id, side_px):
    d = get_dictionary()
    if hasattr(cv2.aruco, 'generateImageMarker'):
        return cv2.aruco.generateImageMarker(d, int(marker_id), int(side_px))
    return cv2.aruco.drawMarker(d, int(marker_id), int(side_px))


@dataclass
class Camera:
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    dist: tuple = (0.0, 0.0, 0.0, 0.0, 0.0)
    calibrated: bool = False

    @classmethod
    def approximate(cls, width, height, hfov_deg=66.0):
        """Uncalibrated guess from the horizontal field of view. Distances are then approximate."""
        fx = (width / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
        return cls(width, height, fx, fx, width / 2.0, height / 2.0)

    @classmethod
    def from_json(cls, path):
        d = json.load(open(path))
        return cls(d['width'], d['height'], d['fx'], d['fy'], d['cx'], d['cy'], tuple(d.get('dist', (0, 0, 0, 0, 0))), True)

    def matrix(self):
        return np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]], dtype=np.float64)


@dataclass
class Detection:
    marker_id: int
    station: str
    corners: np.ndarray        # 4 x 2 pixels: top-left, top-right, bottom-right, bottom-left
    side_px: float
    distance_m: float
    bearing_rad: float
    yaw_rad: float             # 0 when the marker faces the camera squarely


class Detector:
    def __init__(self, camera, marker_size_m=MARKER_SIZE_M, stations=None):
        self.camera = camera
        self.size = float(marker_size_m)
        self.stations = dict(STATIONS if stations is None else stations)
        self._dict = get_dictionary()
        params = cv2.aruco.DetectorParameters() if hasattr(cv2.aruco, 'DetectorParameters') else cv2.aruco.DetectorParameters_create()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self._params = params
        self._detector = cv2.aruco.ArucoDetector(self._dict, params) if hasattr(cv2.aruco, 'ArucoDetector') else None
        s = self.size / 2.0
        self._obj = np.array([[-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0]], dtype=np.float64)

    def detect(self, image):
        gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if self._detector is not None:
            corners, ids, _ = self._detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self._dict, parameters=self._params)
        out = []
        if ids is None:
            return out
        K, dist = self.camera.matrix(), np.array(self.camera.dist, dtype=np.float64)
        for c, i in zip(corners, np.asarray(ids).ravel()):
            i = int(i)
            if i not in self.stations:
                continue                      # ignore markers that are not stations
            pts = np.asarray(c, dtype=np.float64).reshape(4, 2)
            ok, rvec, tvec = cv2.solvePnP(self._obj, pts, K, dist, flags=cv2.SOLVEPNP_IPPE_SQUARE)
            if not ok:
                continue
            t = np.asarray(tvec, dtype=np.float64).ravel()
            R, _ = cv2.Rodrigues(rvec)
            n = R[:, 2]                       # marker normal in the camera frame
            side = float(np.mean([np.linalg.norm(pts[k] - pts[(k + 1) % 4]) for k in range(4)]))
            out.append(Detection(i, self.stations[i], pts, side,
                                 float(math.hypot(t[0], t[2])), float(math.atan2(t[0], t[2])),
                                 float(abs(math.atan2(n[0], -n[2])))))
        return out


def draw_detections(image, detections, target=None):
    vis = image.copy() if image.ndim == 3 else cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    for d in detections:
        col = (0, 200, 0) if (target is None or d.station == target) else (0, 165, 255)
        cv2.polylines(vis, [d.corners.astype(np.int32)], True, col, 2)
        x, y = d.corners.min(axis=0).astype(int)
        label = f'{d.station} id{d.marker_id}  {d.distance_m:.2f} m  {math.degrees(d.bearing_rad):+.0f} deg'
        cv2.putText(vis, label, (int(x), max(int(y) - 8, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2, cv2.LINE_AA)
    return vis


# --------------------------------------------------------------------------------------
# Station-seeking state machine
# --------------------------------------------------------------------------------------
@dataclass
class SeekConfig:
    v_max: float = 0.10                       # m/s; the worm-gearbox motors give about 0.10
    w_max: float = 0.60                       # rad/s
    w_search: float = 0.35                    # rad/s while turning on the spot to look for a marker
    k_v: float = 0.6                          # speed per metre of remaining distance
    k_w: float = 1.2                          # turn rate per radian of bearing error
    stop_distance: float = 0.35               # camera-to-marker distance to stop at
    distance_tol: float = 0.015
    v_creep: float = 0.02                     # slowest useful forward speed for the last few centimetres
    bearing_tol: float = math.radians(4.0)
    slow_bearing: float = math.radians(25.0)  # forward speed fades to zero at this bearing error
    arrive_frames: int = 5                    # consecutive in-tolerance frames before "arrived"
    lost_timeout: float = 1.0                 # seconds without the marker before searching again
    search_timeout: float = 45.0              # about two full turns; then give up
    dwell: float = 3.0                        # seconds to wait at each station
    stale_frame: float = 0.5                  # stop if updates arrive further apart than this


@dataclass
class Command:
    v: float
    w: float
    state: str
    target: str
    note: str = ''


@dataclass
class Arrival:
    station: str
    time: float
    distance_m: float
    bearing_rad: float
    yaw_rad: float


class StationSeeker:
    """Visits the stations in `mission` in order, using only what the camera currently sees.

    Call update(detections, t) once per camera frame. It never commands forward motion unless the
    target marker is detected in that same frame. It is not collision avoidance and not safety-rated.
    """
    SEARCH, APPROACH, DWELL, DONE, FAILED = 'SEARCH', 'APPROACH', 'DWELL', 'DONE', 'FAILED'

    def __init__(self, mission, config=None, stations=None):
        self.cfg = config or SeekConfig()
        names = set((STATIONS if stations is None else stations).values())
        unknown = [m for m in mission if m not in names]
        if unknown or not mission:
            raise ValueError(f'mission must name known stations; unknown: {unknown}')
        self.mission = list(mission)
        self.index = 0
        self.state = self.SEARCH
        self.search_dir = 1.0
        self.search_started = None
        self.last_seen = None
        self.last_bearing = 0.0
        self.arrive_count = 0
        self.dwell_until = None
        self.last_t = None
        self.arrivals = []

    @property
    def target(self):
        return self.mission[self.index] if self.index < len(self.mission) else ''

    def _cmd(self, v, w, note=''):
        c = self.cfg
        v = min(max(float(v), 0.0), c.v_max)          # never reverse, never exceed the cap
        w = min(max(float(w), -c.w_max), c.w_max)
        if not (math.isfinite(v) and math.isfinite(w)):
            v, w, note = 0.0, 0.0, 'non-finite command suppressed'
        return Command(v, w, self.state, self.target, note)

    def update(self, detections, t):
        c = self.cfg
        stale = self.last_t is not None and (t - self.last_t) > c.stale_frame
        went_back = self.last_t is not None and t < self.last_t
        self.last_t = t
        if self.state in (self.DONE, self.FAILED):
            return self._cmd(0, 0)
        if went_back:
            return self._cmd(0, 0, 'time went backwards; stopped')
        if self.search_started is None:
            self.search_started = t

        if self.state == self.DWELL:
            if t >= self.dwell_until:
                self.index += 1
                if self.index >= len(self.mission):
                    self.state = self.DONE
                    return self._cmd(0, 0, 'mission complete')
                self.state, self.search_started, self.arrive_count = self.SEARCH, t, 0
            return self._cmd(0, 0, 'waiting at station')

        seen = [d for d in detections if d.station == self.target]
        det = max(seen, key=lambda d: d.side_px) if seen else None
        if stale:
            self.arrive_count = 0
            return self._cmd(0, 0, 'frame gap too long; stopped this cycle')

        if self.state == self.SEARCH:
            if det is None:
                if t - self.search_started > c.search_timeout:
                    self.state = self.FAILED
                    return self._cmd(0, 0, f'{self.target} not found; gave up')
                return self._cmd(0, self.search_dir * c.w_search, 'turning to look')
            self.state, self.arrive_count = self.APPROACH, 0

        # APPROACH
        if det is None:
            self.arrive_count = 0
            if self.last_seen is None or t - self.last_seen > c.lost_timeout:
                self.state, self.search_started = self.SEARCH, t
                self.search_dir = -1.0 if self.last_bearing > 0 else 1.0   # turn toward where it was last seen
                return self._cmd(0, self.search_dir * c.w_search, 'marker lost; searching')
            return self._cmd(0, 0, 'marker not seen this frame; holding')
        self.last_seen, self.last_bearing = t, det.bearing_rad
        err_d = det.distance_m - c.stop_distance
        w = -c.k_w * det.bearing_rad
        fade = max(0.0, 1.0 - abs(det.bearing_rad) / c.slow_bearing)
        v = max(c.k_v * max(err_d, 0.0), c.v_creep) * fade
        if err_d <= c.distance_tol:
            v = 0.0
            if abs(det.bearing_rad) <= c.bearing_tol:
                self.arrive_count += 1
                if self.arrive_count >= c.arrive_frames:
                    self.arrivals.append(Arrival(self.target, t, det.distance_m, det.bearing_rad, det.yaw_rad))
                    self.state, self.dwell_until = self.DWELL, t + c.dwell
                    return self._cmd(0, 0, 'arrived')
                return self._cmd(0, 0, 'settling')
            self.arrive_count = 0
            return self._cmd(0, w, 'at distance; squaring up')
        self.arrive_count = 0
        return self._cmd(v, w, 'approaching')
