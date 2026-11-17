"""Offline tests. Run: python -m unittest -v test_stations.py"""
import math, random, tempfile, unittest
from pathlib import Path
import numpy as np
import stations as S
import simulate as sim


def det(station='pickup', distance=1.0, bearing=0.0, mid=0, side=60.0):
    return S.Detection(mid, station, np.zeros((4, 2)), side, distance, bearing, 0.0)


class TestDetection(unittest.TestCase):
    def setUp(self):
        self.cam = S.Camera.approximate(1014, 760, 66.0)
        self.det = S.Detector(self.cam)

    def render(self, marker_id, x, y, facing_deg):
        w = sim.World(self.cam, {marker_id: (x, y, math.radians(facing_deg))}, seed=3)
        return w.render(-sim.CAM_FORWARD, 0.0, 0.0)          # camera at the origin looking along +x

    def test_all_station_ids_decode_with_range_and_bearing(self):
        for mid, name in S.STATIONS.items():
            for dist, off in ((0.5, 0.0), (1.5, 0.3), (2.5, -0.5)):
                with self.subTest(marker=mid, distance=dist, offset=off):
                    found = self.det.detect(self.render(mid, dist, off, 180))
                    self.assertEqual([d.marker_id for d in found], [mid])
                    d = found[0]
                    self.assertEqual(d.station, name)
                    true_d, true_b = math.hypot(dist, off), math.atan2(-off, dist)   # +y is left, so bearing is negative
                    self.assertLess(abs(d.distance_m - true_d) / true_d, 0.05)
                    self.assertLess(abs(math.degrees(d.bearing_rad - true_b)), 2.0)

    def test_oblique_marker_still_read_at_45_degrees(self):
        found = self.det.detect(self.render(1, 1.2, 0.0, 180 - 45))
        self.assertEqual([d.marker_id for d in found], [1])
        self.assertAlmostEqual(math.degrees(found[0].yaw_rad), 45, delta=8)

    def test_marker_facing_away_is_not_seen(self):
        self.assertEqual(self.det.detect(self.render(0, 1.0, 0.0, 0)), [])

    def test_non_station_marker_is_ignored(self):
        cam = self.cam
        w = sim.World(cam, {7: (1.0, 0.0, math.pi)}, seed=3)
        self.assertEqual(self.det.detect(w.render(-sim.CAM_FORWARD, 0, 0)), [])


class TestSeeker(unittest.TestCase):
    def test_never_drives_forward_without_the_target_in_view(self):
        s = S.StationSeeker(['pickup', 'dropoff'])
        t = 0.0
        for k in range(300):
            seen = [det('dropoff', 1.0, 0.0, 1)] if k % 2 else []      # only the wrong station is visible
            c = s.update(seen, t); t += 0.1
            self.assertEqual(c.v, 0.0)

    def test_search_then_approach_then_arrive_then_next(self):
        s = S.StationSeeker(['pickup', 'dropoff'])
        c = s.update([], 0.0)
        self.assertEqual((c.state, c.v), ('SEARCH', 0.0)); self.assertGreater(abs(c.w), 0)
        c = s.update([det(distance=1.2)], 0.1)
        self.assertEqual(c.state, 'APPROACH'); self.assertGreater(c.v, 0)
        t = 0.2
        for _ in range(s.cfg.arrive_frames):
            c = s.update([det(distance=s.cfg.stop_distance)], t); t += 0.1
        self.assertEqual(c.state, 'DWELL'); self.assertEqual(len(s.arrivals), 1)
        c = s.update([], t + s.cfg.dwell + 0.05)
        self.assertEqual((c.state, c.target), ('SEARCH', 'dropoff'))

    def test_turns_towards_the_marker(self):
        s = S.StationSeeker(['pickup'])
        self.assertLess(s.update([det(bearing=0.3)], 0.0).w, 0)       # marker on the right -> turn right
        s = S.StationSeeker(['pickup'])
        self.assertGreater(s.update([det(bearing=-0.3)], 0.0).w, 0)

    def test_lost_marker_stops_then_searches_towards_last_side(self):
        s = S.StationSeeker(['pickup'])
        s.update([det(bearing=0.2)], 0.0)
        c = s.update([], 0.1)
        self.assertEqual((c.v, c.w), (0.0, 0.0))                      # holds still first
        c = s.update([], 0.1 + s.cfg.lost_timeout + 0.3)
        self.assertEqual(c.state, 'APPROACH')                         # a long gap between frames stops this cycle
        self.assertEqual((c.v, c.w), (0.0, 0.0))
        t = 0.1 + s.cfg.lost_timeout + 0.4
        c = s.update([], t)
        self.assertEqual(c.state, 'SEARCH'); self.assertLess(c.w, 0)  # last seen on the right

    def test_gives_up_after_search_timeout(self):
        s = S.StationSeeker(['pickup'])
        t, c = 0.0, None
        while t < s.cfg.search_timeout + 2:
            c = s.update([], t); t += 0.1
        self.assertEqual(c.state, 'FAILED'); self.assertEqual((c.v, c.w), (0.0, 0.0))

    def test_stale_frames_and_backwards_time_stop_the_robot(self):
        s = S.StationSeeker(['pickup'])
        s.update([det(distance=2.0)], 0.0)
        self.assertEqual(s.update([det(distance=2.0)], 0.0 + s.cfg.stale_frame + 0.2).v, 0.0)
        self.assertEqual(s.update([det(distance=2.0)], 0.05).v, 0.0)

    def test_commands_always_bounded(self):
        rnd = random.Random(5)
        s = S.StationSeeker(['pickup', 'dropoff', 'recharge'])
        t = 0.0
        for _ in range(3000):
            seen = [det(rnd.choice(['pickup', 'dropoff', 'recharge']), rnd.uniform(0.05, 6), rnd.uniform(-1.2, 1.2))] if rnd.random() < 0.7 else []
            c = s.update(seen, t); t += rnd.uniform(0.02, 0.2)
            self.assertTrue(0.0 <= c.v <= s.cfg.v_max + 1e-9)
            self.assertTrue(abs(c.w) <= s.cfg.w_max + 1e-9)

    def test_unknown_station_is_rejected(self):
        with self.assertRaises(ValueError):
            S.StationSeeker(['pickup', 'kitchen'])


class TestWholeChain(unittest.TestCase):
    def test_mission_completes_and_recovers_when_a_station_is_moved(self):
        with tempfile.TemporaryDirectory() as d:
            for move in (False, True):
                r = sim.run(Path(d) / f'run_{move}', move=move)
                self.assertEqual(r['final_state'], 'DONE')
                self.assertEqual(r['stations_reached'], ['pickup', 'dropoff', 'recharge'])
                self.assertEqual(r['dropoff_marker_moved_at_s'] is not None, move)
                for a in r['arrivals']:
                    self.assertLess(abs(a['stop_error_mm']), 30)       # outline target: within 3 cm
                    self.assertLess(abs(a['true_bearing_deg']), 5)     # outline target: within 5 degrees
                self.assertLessEqual(r['max_v_cmd'], 0.10 + 1e-9)


if __name__ == '__main__':
    unittest.main()
