"""ROS-independent prototype. All time arguments are monotonic seconds."""
from collections import deque
from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class Config:
    adaptive: bool = True
    highpass_hz: float = 1.0
    lowpass_hz: float = 20.0
    window_s: float = 0.5
    warmup_s: float = 1.5
    minimum_samples: int = 30
    imu_timeout_s: float = 0.10
    command_timeout_s: float = 0.30
    loop_timeout_s: float = 0.10
    rms_release: float = 0.20
    rms_enter: float = 0.35
    rms_full: float = 1.00
    minimum_scale: float = 0.25
    scale_fall_per_s: float = 2.0
    scale_rise_per_s: float = 0.20
    max_linear: float = 0.30
    max_angular: float = 0.60
    max_linear_accel: float = 0.25
    max_angular_accel: float = 0.60
    max_linear_jerk: float = 1.0
    max_angular_jerk: float = 2.0
    max_accel_component: float = 60.0

    def __post_init__(self):
        for key, value in asdict(self).items():
            if key != 'adaptive' and (not math.isfinite(value) or value <= 0):
                raise ValueError(f'{key} must be finite and positive')
        if not (self.rms_release < self.rms_enter < self.rms_full):
            raise ValueError('Require rms_release < rms_enter < rms_full')
        if not (self.highpass_hz < self.lowpass_hz):
            raise ValueError('High-pass cutoff must be below low-pass cutoff')
        if self.minimum_scale > 1 or self.warmup_s < self.window_s:
            raise ValueError('Invalid scale or warmup')
        if self.minimum_samples < 2 or int(self.minimum_samples) != self.minimum_samples:
            raise ValueError('minimum_samples must be an integer >= 2')


def clamp(x, low, high):
    return max(low, min(high, x))


class AxisLimiter:
    """Jerk-limited ramp; exact target/stop clamps take precedence over jerk."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.velocity = self.acceleration = 0.0

    def update(self, target, dt, accel_limit, jerk_limit):
        error = target - self.velocity
        # Reduce requested acceleration as the target approaches.
        desired = math.copysign(min(accel_limit, math.sqrt(2 * jerk_limit * abs(error))), error)
        self.acceleration += clamp(desired - self.acceleration, -jerk_limit * dt, jerk_limit * dt)
        candidate = self.velocity + self.acceleration * dt
        if error == 0 or (target - candidate) * error <= 0:
            self.velocity, self.acceleration = target, 0.0
        else:
            self.velocity = candidate
        return self.velocity


class Controller:
    def __init__(self, config=None):
        self.cfg = config or Config()
        self.enabled = False
        self.reason = 'disabled'
        self.command = (0.0, 0.0)
        self.command_time = self.imu_time = self.step_time = None
        self.v = AxisLimiter()
        self.w = AxisLimiter()
        self.reset_filter()

    def reset_filter(self):
        self.samples = deque()
        self.energy = self.rms = 0.0
        self.previous_raw = None
        self.hp = [0.0] * 3
        self.lp = [0.0] * 3
        self.filter_start = None
        self.active = False
        self.scale = 1.0

    def stop(self, reason):
        self.enabled = False
        self.reason = reason
        self.v.reset()
        self.w.reset()

    def invalidate_imu(self, reason='invalid_imu'):
        self.imu_time = None
        self.reset_filter()
        self.stop(reason)

    def feed_imu(self, acceleration, now):
        if len(acceleration) != 3 or not math.isfinite(now) or any(
            not math.isfinite(a) or abs(a) > self.cfg.max_accel_component for a in acceleration
        ):
            self.invalidate_imu()
            return False
        dt = None if self.imu_time is None else now - self.imu_time
        if dt is not None and (dt <= 0 or dt > self.cfg.imu_timeout_s):
            self.invalidate_imu('imu_timing_fault')
            dt = None
        self.imu_time = now
        if self.previous_raw is None:
            self.previous_raw = tuple(acceleration)
            self.filter_start = now
            return True
        # High-pass removes constant gravity/bias, NOT arbitrary tilt effects.
        hp_alpha = 1 / (1 + 2 * math.pi * self.cfg.highpass_hz * dt)
        lp_alpha = 1 - math.exp(-2 * math.pi * self.cfg.lowpass_hz * dt)
        for i, a in enumerate(acceleration):
            self.hp[i] = hp_alpha * (self.hp[i] + a - self.previous_raw[i])
            self.lp[i] += lp_alpha * (self.hp[i] - self.lp[i])
        self.previous_raw = tuple(acceleration)
        power = sum(a * a for a in self.lp)
        self.samples.append((now, power))
        self.energy += power
        while self.samples and self.samples[0][0] < now - self.cfg.window_s:
            self.energy -= self.samples.popleft()[1]
        self.rms = math.sqrt(max(0.0, self.energy / len(self.samples)))
        return True

    def feed_command(self, linear, angular, now):
        if not all(math.isfinite(x) for x in (linear, angular, now)):
            self.command_time = None
            self.stop('invalid_command')
            return False
        if self.command_time is not None and now <= self.command_time:
            self.command_time = None
            self.stop('command_timing_fault')
            return False
        # Common-factor clamp preserves requested curvature at this stage.
        factor = max(1.0, abs(linear) / self.cfg.max_linear, abs(angular) / self.cfg.max_angular)
        self.command = (linear / factor, angular / factor)
        self.command_time = now
        return True

    def input_fault(self, now):
        if not math.isfinite(now):
            return 'invalid_time'
        if self.imu_time is None or not 0 <= now - self.imu_time <= self.cfg.imu_timeout_s:
            return 'imu_stale'
        if self.command_time is None or not 0 <= now - self.command_time <= self.cfg.command_timeout_s:
            return 'command_stale'
        if (now - self.filter_start < self.cfg.warmup_s or
                len(self.samples) < self.cfg.minimum_samples):
            return 'imu_warming_up_or_low_rate'
        return None

    def enable(self, now):
        fault = self.input_fault(now)
        if fault or self.command != (0.0, 0.0):
            self.stop(fault or 'enable_requires_zero_command')
            return False
        self.enabled = True
        self.reason = 'ready'
        self.step_time = now
        return True

    def step(self, now):
        dt = None if self.step_time is None else now - self.step_time
        self.step_time = now
        fault = self.input_fault(now)
        if fault:
            self.stop(fault)
        if dt is not None and (not math.isfinite(dt) or dt <= 0 or dt > self.cfg.loop_timeout_s):
            self.stop('control_loop_timing_fault')
        if not self.enabled or dt is None:
            return 0.0, 0.0
        c = self.cfg
        if self.rms >= c.rms_enter:
            self.active = True
        elif self.rms <= c.rms_release:
            self.active = False
        target_scale = 1.0
        if c.adaptive and self.active:
            fraction = clamp((self.rms - c.rms_release) / (c.rms_full - c.rms_release), 0, 1)
            target_scale = 1 - fraction * (1 - c.minimum_scale)
        self.scale += clamp(target_scale - self.scale, -c.scale_fall_per_s * dt, c.scale_rise_per_s * dt)
        v, w = (x * self.scale for x in self.command)
        # An upstream stop must not be turned into a residual ramp command.
        if v == 0 and w == 0:
            self.v.reset()
            self.w.reset()
            self.reason = 'commanded_stop'
            return 0.0, 0.0
        self.reason = 'adapting' if c.adaptive and self.active else 'normal'
        self.v.update(v, dt, c.max_linear_accel * self.scale, c.max_linear_jerk * self.scale)
        self.w.update(w, dt, c.max_angular_accel * self.scale, c.max_angular_jerk * self.scale)
        for axis, limit in ((self.v, c.max_linear), (self.w, c.max_angular)):
            if abs(axis.velocity) > limit:
                axis.velocity = clamp(axis.velocity, -limit, limit)
                axis.acceleration = 0.0
        return self.v.velocity, self.w.velocity

    def status(self):
        return {'enabled': self.enabled, 'state': self.reason, 'rms_m_s2': self.rms,
                'speed_scale': self.scale, 'adaptive': self.cfg.adaptive,
                'linear_m_s': self.v.velocity, 'angular_rad_s': self.w.velocity}
