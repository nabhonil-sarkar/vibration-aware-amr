"""A1 scan input: live serial, recorded JSONL/SDK text, or a synthetic room."""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import argparse
import json
import math
import re
import sys
import time
import numpy as np

DEFAULT_PORT = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'

@dataclass
class Scan:
    timestamp: float
    samples: list  # [(quality, clockwise angle in degrees, distance in millimetres)]

def add_arguments(parser):
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--live', action='store_true', help='Use the physical A1 USB adapter')
    source.add_argument('--replay', type=Path, help='Read our JSONL or official SDK text log')
    source.add_argument('--demo', action='store_true', help='Synthetic room; no hardware access')
    parser.add_argument('--port', default=DEFAULT_PORT)
    parser.add_argument('--seconds', type=float, default=60, help='Live duration; 0 means until Ctrl+C')
    parser.add_argument('--max-scans', type=int, default=0, help='0 means all available scans')
    parser.add_argument('--output', type=Path, help='New empty output directory (never overwrite a run)')
    parser.add_argument('--plot', action='store_true', help='Live plot on Pi desktop; omit over ordinary SSH')

def prepare_output(args, prefix):
    if args.seconds < 0 or args.max_scans < 0:
        raise ValueError('seconds and max-scans must be nonnegative')
    out = args.output or Path('runs') / (prefix + '_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True, exist_ok=False)
    return out

def clean_points(scan, min_m=0.15, max_m=8.0):
    """Reject invalid returns; keep nearest valid return in each 1-degree bin.

    Frame: +X is the scanner's zero-angle ray, +Y is 90 degrees CCW.
    Hardware angles are clockwise, so Y is negated. This is a sensor frame,
    not an established robot base_link orientation.
    """
    bins = {}
    for q, a, d in scan.samples:
        if not all(math.isfinite(float(v)) for v in (q, a, d)):
            continue
        if q <= 0 or not 0 <= a < 360 or not min_m * 1000 <= d <= max_m * 1000:
            continue
        b = int(a)
        if b not in bins or d < bins[b][1]:
            bins[b] = (a, d)
    if not bins:
        return np.empty((0, 2))
    a, d = np.array([bins[b] for b in sorted(bins)]).T
    radians = np.deg2rad(a)
    return np.column_stack((d*np.cos(radians), -d*np.sin(radians))) / 1000

def write_scan(file, scan):
    file.write(json.dumps({'format': 'amr-a1-v1', 'timestamp': scan.timestamp,
                           'samples': scan.samples}, allow_nan=False) + '\n')

def replay(path):
    if path.suffix.lower() == '.jsonl':
        with path.open(encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                obj = json.loads(line)
                if obj.get('format') != 'amr-a1-v1':
                    raise ValueError(f'Unsupported JSONL format at line {line_no}')
                yield Scan(float(obj['timestamp']), obj['samples'])
        return
    # SDK logs have no scan IDs/timestamps. Infer revolutions from a large
    # angle wrap; discard first and last partial revolutions. Never infer Hz.
    pattern = re.compile(r'theta:\s*([\d.]+)\s+Dist:\s*([\d.]+)\s+Q:\s*(\d+)')
    current, previous, started, index = [], None, False, 0
    with path.open(encoding='utf-8', errors='replace') as f:
        for line in f:
            for m in pattern.finditer(line):
                a, d, q = float(m[1]), float(m[2]), int(m[3])
                if previous is not None and previous - a > 180:
                    if started and current:
                        yield Scan(float(index), current)
                        index += 1
                    current, started = [], True
                current.append((q, a, d))
                previous = a

def demo_scans(count=80):
    """Ray-cast an asymmetric static room. Ground truth is test-only."""
    segments = [((-3,-2),(4,-2)), ((4,-2),(4,3)), ((4,3),(-3,3)), ((-3,3),(-3,-2)),
                ((1.5,1),(2.2,1)), ((2.2,1),(2.2,1.7)), ((2.2,1.7),(1.5,1.7)), ((1.5,1.7),(1.5,1))]
    rng = np.random.default_rng(7)
    for i in range(count):
        pose = demo_pose(i, count)
        samples = []
        for a in range(360):
            t = pose[2] - math.radians(a)
            direction = np.array([math.cos(t), math.sin(t)])
            best = 20.0
            for start, end in segments:
                start, edge = np.array(start), np.subtract(end,start)
                matrix = np.column_stack((direction, -edge))
                if abs(np.linalg.det(matrix)) < 1e-9:
                    continue
                distance, u = np.linalg.solve(matrix, start-pose[:2])
                if distance > 0 and 0 <= u <= 1:
                    best = min(best, distance)
            samples.append((47, float(a), float(max(0,best+rng.normal(0,.002))*1000)))
        yield Scan(i*0.2, samples)

def demo_pose(i, count=80):
    u = i / max(1, count-1)
    return np.array([0.6*u, 0.2*math.sin(math.pi*u), math.radians(10)*u])

def shutdown(lidar):
    # Try every cleanup step even if the previous one fails.
    for name in ('stop', 'stop_motor', 'disconnect'):
        try:
            getattr(lidar, name)()
        except Exception as e:
            print(f'Cleanup {name}: {e}', file=sys.stderr)

@contextmanager
def source(args, factory=None):
    if args.demo:
        yield demo_scans()
        return
    if args.replay:
        stream = replay(args.replay)
        try:
            yield stream
        finally:
            stream.close()
        return
    if factory is None:
        from rplidar import RPLidar
        factory = RPLidar
    lidar = factory(args.port, baudrate=115200, timeout=2)
    try:
        print('Device:', lidar.get_info())
        health = lidar.get_health()
        print('Health:', health)
        if health[0] != 'Good':
            raise RuntimeError('LiDAR is not reporting Good health; stop and inspect the device')
        def live():
            # Discard first partial scan, then one tuple list per revolution.
            stream = lidar.iter_scans(max_buf_meas=10000, min_len=5)
            next(stream)
            for samples in stream:
                yield Scan(time.time(), samples)
        yield live()
    finally:
        shutdown(lidar)

def bounded(stream, args):
    start = time.monotonic()
    for i, scan in enumerate(stream):
        if args.max_scans and i >= args.max_scans:
            return
        if args.live and args.seconds and time.monotonic()-start >= args.seconds:
            return
        yield scan
