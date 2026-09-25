import math
import random
import unittest
from vibration_aware_control.core import Config, Controller, AxisLimiter
from vibration_aware_control.demo import run_demo


class ControllerTests(unittest.TestCase):
    def ready(self, **kwargs):
        c = Controller(Config(**kwargs))
        for i in range(201):
            t = i / 100
            c.feed_imu((0, 0, 9.80665), t)
            c.feed_command(0, 0, t)
            c.step(t)
        self.assertTrue(c.enable(2.0))
        return c

    def advance(self, c, start, end, amplitude=0.0, v=0.25, w=0.0):
        output = (0, 0)
        for i in range(round(start * 100) + 1, round(end * 100) + 1):
            t = i / 100
            c.feed_imu((0, 0, 9.80665 + amplitude * math.sin(2 * math.pi * 8 * t)), t)
            c.feed_command(v, w, t)
            output = c.step(t)
        return output

    def test_defaults_disabled(self):
        c = Controller()
        self.assertEqual(c.step(0), (0, 0))
        self.assertFalse(c.enable(0))

    def test_gravity_removed(self):
        c = self.ready()
        self.assertAlmostEqual(c.rms, 0)

    def test_normal_speed(self):
        c = self.ready()
        self.assertAlmostEqual(self.advance(c, 2, 5)[0], 0.25)

    def test_vibration_slows_and_recovers(self):
        c = self.ready()
        self.advance(c, 2, 5)
        v, _ = self.advance(c, 5, 10, amplitude=1.8)
        self.assertLess(v, 0.1)
        self.assertAlmostEqual(c.scale, 0.25)
        self.advance(c, 10, 17)
        self.assertAlmostEqual(c.scale, 1)

    def test_baseline_no_adaptation(self):
        c = self.ready(adaptive=False)
        v, _ = self.advance(c, 2, 7, amplitude=1.8)
        self.assertAlmostEqual(v, 0.25)
        self.assertEqual(c.scale, 1)

    def test_stale_imu_disarms(self):
        c = self.ready()
        self.advance(c, 2, 4)
        c.feed_command(0.2, 0, 4.2)
        self.assertEqual(c.step(4.2), (0, 0))
        self.assertFalse(c.enabled)
        self.advance(c, 4.2, 7)
        self.assertFalse(c.enabled)
        self.assertEqual(c.v.velocity, 0)

    def test_stale_command_disarms(self):
        c = self.ready()
        for i in range(201, 240):
            t = i / 100
            c.feed_imu((0, 0, 9.8), t)
            c.step(t)
        self.assertFalse(c.enabled)
        self.assertEqual(c.reason, 'command_stale')

    def test_nan_imu(self):
        c = self.ready()
        self.assertFalse(c.feed_imu((0, float('nan'), 0), 2.01))
        self.assertFalse(c.enabled)

    def test_nan_command(self):
        c = self.ready()
        self.assertFalse(c.feed_command(float('inf'), 0, 2.01))
        self.assertFalse(c.enabled)

    def test_stop_immediate(self):
        c = self.ready()
        self.advance(c, 2, 4)
        self.assertEqual(self.advance(c, 4, 4.01, v=0), (0, 0))

    def test_enable_needs_zero_command(self):
        c = self.ready()
        c.stop('manual')
        c.feed_command(0.1, 0, 2.01)
        self.assertFalse(c.enable(2.01))

    def test_reverse(self):
        c = self.ready()
        v, w = self.advance(c, 2, 7, v=-0.2, w=-0.4)
        self.assertAlmostEqual(v, -0.2)
        self.assertAlmostEqual(w, -0.4)

    def test_common_factor_clamp(self):
        c = Controller()
        c.feed_command(3, 3, 0)
        self.assertEqual(c.command, (0.3, 0.3))

    def test_low_sample_rate_cannot_arm(self):
        c = Controller()
        for i in range(50):
            c.feed_imu((0, 0, 9.8), i * 0.09)
            c.feed_command(0, 0, i * 0.09)
        self.assertFalse(c.enable(49 * 0.09))

    def test_backwards_imu_time(self):
        c = self.ready()
        c.feed_imu((0, 0, 9.8), 1.9)
        self.assertFalse(c.enabled)

    def test_loop_delay(self):
        c = self.ready()
        for i in range(201, 222):
            c.feed_imu((0, 0, 9.8), i / 100)
            c.feed_command(0.2, 0, i / 100)
        self.assertEqual(c.step(2.21), (0, 0))
        self.assertEqual(c.reason, 'control_loop_timing_fault')

    def test_limiter_initial_ramp(self):
        axis = AxisLimiter()
        last_v = last_a = 0
        for _ in range(30):
            v = axis.update(1, 0.01, 0.25, 1)
            a = (v - last_v) / 0.01
            self.assertLessEqual(abs(a), 0.2500001)
            self.assertLessEqual(abs(a - last_a) / 0.01, 1.000001)
            last_v, last_a = v, a

    def test_finite_bounded_random_inputs(self):
        c = self.ready()
        rng = random.Random(42)
        for i in range(201, 2201):
            t = i / 100
            c.feed_imu((rng.uniform(-2, 2), 0, 9.8), t)
            if i % 20 == 1:
                command = (rng.uniform(-1, 1), rng.uniform(-2, 2))
            c.feed_command(*command, t)
            v, w = c.step(t)
            self.assertTrue(math.isfinite(v) and math.isfinite(w))
            self.assertLessEqual(abs(v), c.cfg.max_linear)
            self.assertLessEqual(abs(w), c.cfg.max_angular)

    def test_config_validation(self):
        for kwargs in ({'rms_enter': 2}, {'minimum_scale': 2}, {'window_s': -1},
                       {'lowpass_hz': 0.5}, {'minimum_samples': 1.5}, {'max_linear': float('nan')}):
            with self.assertRaises(ValueError):
                Config(**kwargs)

    def test_demo_dropout(self):
        rows = run_demo()
        self.assertTrue(any(r['adaptive_m_s'] < r['baseline_m_s'] for r in rows if 8 < r['time_s'] < 12))
        self.assertTrue(all(r['adaptive_m_s'] == 0 for r in rows if r['time_s'] >= 16.12))


if __name__ == '__main__':
    unittest.main()
