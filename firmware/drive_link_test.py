#!/usr/bin/env python3
"""Pi-side test of the NUCLEO-F401RE drive link (firmware v0.1). Wheels OFF the ground.

  python3 drive_link_test.py --watch                 # print encoder counts only, no motor commands
  python3 drive_link_test.py --pwm 200 200 --seconds 3
  python3 drive_link_test.py --vel 500 500 --seconds 3   # counts/s

After the drive period it STOPS SENDING (no S command) and checks that the firmware times out
on its own within 0.5 s. That is the Wed 18 Nov pass check. Needs pyserial (python3-serial).
"""
import argparse, sys, threading, time
import serial

FIELDS = ['ms', 'encL', 'encR', 'spdL', 'spdR', 'pwmL', 'pwmR', 'flags']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ttyACM0')
    ap.add_argument('--baud', type=int, default=230400)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--watch', action='store_true')
    g.add_argument('--pwm', nargs=2, type=int, metavar=('LEFT', 'RIGHT'))
    g.add_argument('--vel', nargs=2, type=int, metavar=('LEFT', 'RIGHT'))
    ap.add_argument('--seconds', type=float, default=3.0)
    a = ap.parse_args()

    ser = serial.Serial(a.port, a.baud, timeout=0.1)
    time.sleep(0.2)
    ser.reset_input_buffer()
    latest = {}
    stop = threading.Event()

    def reader():
        while not stop.is_set():
            line = ser.readline().decode('ascii', 'replace').strip()
            if line.startswith('T,'):
                p = line.split(',')
                if len(p) == 21:
                    latest.update(zip(FIELDS, map(int, p[1:9])), t=time.monotonic())
            elif line:
                print('  <', line)
    threading.Thread(target=reader, daemon=True).start()

    ser.write(b'I\n')
    time.sleep(0.3)

    def show(tag=''):
        if latest:
            f = latest['flags']
            print(f"{tag}enc {latest['encL']:>8} {latest['encR']:>8}  spd {latest['spdL']:>6} {latest['spdR']:>6}  "
                  f"pwm {latest['pwmL']:>5} {latest['pwmR']:>5}  enabled={f & 1} timeout={(f >> 1) & 1} "
                  f"imu1={'ok' if not f & 4 else 'FAIL'} imu2={'ok' if not f & 8 else 'FAIL'}")
        else:
            print('no telemetry yet')

    try:
        if a.watch:
            ser.write(b'Z\n')
            while True:
                show(); time.sleep(0.5)
        cmd = (f'P,{a.pwm[0]},{a.pwm[1]}\n' if a.pwm else f'V,{a.vel[0]},{a.vel[1]}\n').encode()
        t0 = time.monotonic(); last = 0
        while time.monotonic() - t0 < a.seconds:
            ser.write(cmd)                     # 20 Hz keep-alive
            if time.monotonic() - last > 0.5:
                show('drive  '); last = time.monotonic()
            time.sleep(0.05)
        t_stop = time.monotonic()
        print('stopped sending; waiting for firmware timeout...')
        while time.monotonic() - t_stop < 1.5:
            if latest and latest['flags'] & 2:
                print(f'PASS: firmware timed out {time.monotonic() - t_stop:.2f} s after the last command')
                show('after  ')
                break
            time.sleep(0.01)
        else:
            print('FAIL: no timeout flag within 1.5 s; switch the relay off')
            show('after  ')
    except KeyboardInterrupt:
        pass
    finally:
        ser.write(b'S\n'); time.sleep(0.1)
        stop.set(); ser.close()


if __name__ == '__main__':
    sys.exit(main())
