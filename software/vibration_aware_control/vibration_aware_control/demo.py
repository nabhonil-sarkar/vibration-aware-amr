"""Synthetic open-loop demonstration, NOT a robot dynamics/performance model."""
import argparse
import csv
import json
import math
from pathlib import Path

from .core import Config, Controller


def run_demo():
    controllers = [Controller(Config(adaptive=flag)) for flag in (False, True)]
    rows = []
    for i in range(2001):
        t = i / 100
        amplitude = 1.8 if 6 <= t < 12 else 0.05
        az = 9.80665 + amplitude * math.sin(2 * math.pi * 8 * t)
        requested = 0.25 if 2.2 <= t < 18 else 0.0
        outputs = []
        for controller in controllers:
            # Demonstrate sensor loss at 16 s, then recovery without auto-rearm.
            if not 16 <= t < 16.5:
                controller.feed_imu((0.0, 0.0, az), t)
            if i % 2 == 0:
                controller.feed_command(requested, 0.0, t)
                if i == 200:
                    assert controller.enable(t)
                else:
                    outputs.append(controller.step(t)[0])
        if len(outputs) == 2:
            rows.append({'time_s': t, 'raw_az_m_s2': az,
                         'filtered_rms_m_s2': controllers[1].rms,
                         'requested_m_s': requested, 'baseline_m_s': outputs[0],
                         'adaptive_m_s': outputs[1], 'speed_scale': controllers[1].scale,
                         'state': controllers[1].reason})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('demo_outputs'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = run_demo()
    with (args.output / 'synthetic_controller_demo.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    report = {'data_type': 'SYNTHETIC open-loop input; no physical vibration reduction measured',
              'maximum_filtered_rms_m_s2': max(r['filtered_rms_m_s2'] for r in rows),
              'minimum_speed_scale': min(r['speed_scale'] for r in rows),
              'dropout_stop_seen': any(r['state'] == 'imu_stale' for r in rows),
              'remains_stopped_after_dropout': all(r['adaptive_m_s'] == 0 for r in rows if r['time_s'] >= 16.12)}
    (args.output / 'demo_summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('CSV saved. Optional plot needs matplotlib: python -m pip install matplotlib')
        return
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    t = [r['time_s'] for r in rows]
    axes[0].plot(t, [r['filtered_rms_m_s2'] for r in rows], color='#8e44ad')
    axes[0].axhline(Config().rms_enter, color='gray', ls='--', label='Illustrative entry threshold')
    axes[0].set_ylabel('Filtered RMS (m/s²)')
    axes[0].legend(loc='upper right')
    for key, label, style in [('requested_m_s', 'Requested', ':'),
                              ('baseline_m_s', 'Baseline (same safety limits)', '--'),
                              ('adaptive_m_s', 'Vibration-aware', '-')]:
        axes[1].plot(t, [r[key] for r in rows], style, label=label)
    axes[1].set_ylabel('Speed command (m/s)')
    axes[1].legend(loc='lower left')
    axes[2].plot(t, [r['speed_scale'] for r in rows], color='#008080')
    axes[2].set_ylabel('Speed scale')
    axes[2].set_xlabel('Time (s)')
    for ax in axes:
        ax.axvspan(6, 12, color='orange', alpha=0.12)
        ax.axvspan(16, 16.5, color='red', alpha=0.15)
        ax.grid(alpha=0.2)
    axes[2].text(6.1, 0.90, 'High synthetic vibration')
    axes[2].text(16.1, 0.45, 'IMU dropout\nRe-enable required')
    fig.suptitle('Vibration-aware controller: SYNTHETIC software demonstration\nSame imposed IMU signal in both modes; not evidence of physical vibration reduction')
    fig.tight_layout()
    fig.savefig(args.output / 'synthetic_controller_demo.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
