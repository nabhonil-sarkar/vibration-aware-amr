"""AMR wiring diagram v1 (17 Nov 2026): NUCLEO-F401RE + TB6612FNG + 2 x JGY-370-CE encoder motors,
2 x MPU-6050 IMUs, Raspberry Pi 5, RPLIDAR A1, AI Camera, 12 V Li-Po power chain.
Planned connections from firmware/nucleo_f401re_base/PIN_PLAN.md. NOT yet wired or tested.
Usage: python make_wiring_diagram.py OUTDIR   -> AMR_Wiring_Diagram_v1.png / .svg / .pdf"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

C12, C5, C33, SIG, GND, USB = '#c0392b', '#e67e22', '#2471a3', '#1e8449', '#222222', '#6c3483'
fig = plt.figure(figsize=(18, 11.5))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 180); ax.set_ylim(0, 115); ax.axis('off')


S = 2.4   # line spacing


def block(x, y, w, h, title, lines, edge='#34495e', face='#f4f6f7', tsize=11, lsize=8.2, dashed=False):
    need = 5.4 + len(lines) * S + 0.4
    assert h >= need - 0.01, (title, h, need)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4,rounding_size=1.2', fc=face, ec=edge,
                                lw=1.8, ls='--' if dashed else '-'))
    ax.text(x + 1.2, y + h - 1.4, title, fontsize=tsize, fontweight='bold', color=edge, va='top')
    for i, l in enumerate(lines):
        ax.text(x + 1.2, y + h - 5.2 - i * S, l, fontsize=lsize, va='top', family='DejaVu Sans Mono' if l.startswith(' ') else None)


def wire(pts, colour, label=None, at=0, dx=0.0, dy=0.6, dashed=False, lw=2.2, ha='center', va='bottom'):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=colour, lw=lw, ls=(0, (5, 3)) if dashed else '-', solid_capstyle='round', zorder=1)
    if label:
        (x0, y0), (x1, y1) = pts[at], pts[at + 1]
        ax.text((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, label, fontsize=8, color=colour, ha=ha, va=va,
                bbox=dict(fc='white', ec='none', pad=0.5), zorder=3)


ax.text(2, 113.5, 'Vibration-Aware AMR: wiring diagram v1', fontsize=18, fontweight='bold', color='#17202a', va='top')
ax.text(2, 109.6, 'Planned connections, 17 Nov 2026. Matches firmware/nucleo_f401re_base/PIN_PLAN.md. Not yet wired, powered or tested. '
        'Dashed = not yet fitted or still to confirm.', fontsize=10, color='#566573', va='top')

# ---------------- power chain (top) ----------------
block(2, 86, 21, 16, '12 V Li-Po pack', ['4800 mAh, built-in', 'protection; max discharge', 'current unconfirmed', '+ / - to DC jack'], edge=C12)
block(28, 89, 16, 13, 'DC jack', ['adapter: battery plug', 'to screw terminals', ''], edge=C12)
block(49, 89, 15, 13, '5 A fuse', ['inline, close to', 'battery +', 'NOT YET SOURCED'], edge=C12, dashed=True)
block(69, 89, 16, 13, 'Main switch', ['rocker; switches', 'Pi and motor branch', ''], edge=C12)
block(93, 93.5, 22, 11, 'XL4016 buck', ['set 5.1 V unloaded', 'out -> cut USB-C cable'], edge=C5)
block(93, 79, 22, 11, 'Motor switch', ['rocker; drives the', 'relay coil only'], edge=C12)
block(121, 79, 25, 11, '12 V relay module', ['10 A / 30 V DC contacts', 'COM-NO in motor 12 V'], edge=C12)
wire([(23.4, 95.5), (27.6, 95.5)], C12)
wire([(44.4, 95.5), (48.6, 95.5)], C12, dashed=True)
wire([(64.4, 95.5), (68.6, 95.5)], C12, dashed=True)
wire([(85.4, 95.5), (89, 95.5), (89, 99), (92.6, 99)], C12, '12 V', at=1, dx=-2.2, dy=0, ha='center', va='center')
wire([(89, 95.5), (89, 84.5), (92.6, 84.5)], C12)
wire([(115.4, 84.5), (120.6, 84.5)], C12, 'coil')
ax.text(150.5, 104, "Relay = motor cut-off in place of a\nmushroom E-stop. Lab engineer's\nacceptance still to be confirmed.\n"
        "Motor current never goes through the\nPi, Nucleo or breadboard: power\nwiring on screw terminals only.",
        fontsize=8, color=C12, va='top')

# ---------------- Pi and its peripherals (left) ----------------
block(2, 38, 34, 34, 'Raspberry Pi 5', ['USB-C power  <- 5.1 V buck', '  (usb_max_current_enable=1)', 'CSI CAM/DISP <- AI Camera',
                                        'USB-A        -> RPLIDAR A1', 'USB-A        -> Nucleo ST-LINK', 'Ethernet     -> laptop (SSH)',
                                        '', 'Runs logging, station finding,', 'speed-adaptation decisions'], edge='#7d3c98')
block(2, 20, 16, 14, 'AI Camera', ['IMX500, CSI ribbon', 'fit with Pi', 'powered off'], edge='#7d3c98', lsize=7.8)
block(20, 20, 16, 14, 'RPLIDAR A1', ['CP2102 USB adapter', '115200 baud', 'USB data + power'], edge='#7d3c98', lsize=7.8)
wire([(104, 104.9), (104, 106.4), (0.9, 106.4), (0.9, 62), (1.6, 62)], C5, '5.1 V to Pi USB-C (cut cable: check voltage and polarity first)', at=1, dy=0.3)
wire([(10, 37.6), (10, 34.4)], USB, 'CSI', dx=1.2, dy=-1.2, ha='left')
wire([(28, 37.6), (28, 34.4)], USB, 'USB', dx=1.2, dy=-1.2, ha='left')
ax.text(2, 17, 'All grounds common: battery -, buck -,\nTB6612 GND, Nucleo GND, encoder and\nIMU GND.\n\n'
        'Nucleo: keep D0/D1 free (USB serial),\nnothing on D13 (LED). Blue button B1\nstops the motors. Firmware holds the\n'
        'driver off at boot and drops STBY\n0.5 s after the last command.', fontsize=7.8, color='#566573', va='top')

# ---------------- Nucleo (centre) ----------------
block(50, 20, 40, 52.4, 'NUCLEO-F401RE', [
    ' USB (ST-LINK): power, flashing,', ' serial 230400 baud (/dev/ttyACM0)', '',
    ' D7  PA8  TIM1_CH1  -> PWMA', ' D2  PA10           -> AIN1', ' D4  PB5            -> AIN2',
    ' D8  PA9  TIM1_CH2  -> PWMB', ' D5  PB4            -> BIN1', ' D6  PB10           -> BIN2',
    ' D9  PC7            -> STBY', '', ' A0  PA0  TIM2_CH1  <- Left enc A', ' A1  PA1  TIM2_CH2  <- Left enc B',
    ' D12 PA6  TIM3_CH1  <- Right enc A', ' D11 PA7  TIM3_CH2  <- Right enc B', '',
    ' D15 PB8  I2C1 SCL  -- both IMUs', ' D14 PB9  I2C1 SDA  -- both IMUs'], edge='#1a5276', lsize=7.9)
wire([(36.4, 52), (49.6, 52)], USB, 'USB cable')

# ---------------- TB6612 ----------------
block(104, 44, 27, 28, 'TB6612FNG driver', ['VM   <- 12 V via relay', 'VCC  <- Nucleo 3V3', 'GND  -- common ground',
                                             'PWMA AIN1 AIN2 <- Nucleo', 'PWMB BIN1 BIN2 <- Nucleo', 'STBY <- Nucleo D9',
                                             'AO1/AO2 -> left motor', 'BO1/BO2 -> right motor', '~1.2 A cont. per channel'],
      edge='#117864', lsize=7.9)
wire([(90.4, 63), (103.6, 63)], SIG, '7 control', dy=0.5)
wire([(90.4, 57), (103.6, 57)], C33, '3V3 + GND', dy=0.5)
wire([(146.4, 84.5), (149, 84.5), (149, 68), (131.4, 68)], C12, 'switched 12 V -> VM', at=2, dy=0.5)

# ---------------- motors ----------------
for side, my in (('Left', 47), ('Right', 17)):
    a, b = ('AO1', 'AO2') if side == 'Left' else ('BO1', 'BO2')
    e1, e2 = ('A0', 'A1') if side == 'Left' else ('D12', 'D11')
    block(152, my, 27, 26, f'{side} motor JGY-370-CE', ['12 V 40 RPM worm gear,', 'Hall encoder, 6-pin plug:',
                                                         f' 1 M1  -> TB6612 {a}', ' 2 GND -- Nucleo GND', f' 3 A   -> Nucleo {e1}',
                                                         f' 4 B   -> Nucleo {e2}', ' 5 VCC <- Nucleo 3V3', f' 6 M2  -> TB6612 {b}'],
          edge='#117864', lsize=7.7)
wire([(131.4, 62), (151.6, 62)], C12, 'AO1 / AO2')
wire([(131.4, 50), (138, 50), (138, 32), (151.6, 32)], C12, 'BO1 / BO2', at=2)
wire([(151.6, 55), (145, 55), (145, 40), (90.4, 40)], SIG, 'left encoder A/B + 3V3/GND', at=2)
wire([(151.6, 23), (98, 23), (98, 34), (90.4, 34)], SIG, 'right encoder A/B + 3V3/GND', at=0)
ax.text(152, 15.6, 'Connector order confirmed with a meter on\nboth motors, 17 Nov 2026 (only pin 1 is\nlabelled on the board). A/B may be swapped.', fontsize=7.6, color='#117864', va='top')

# ---------------- IMUs ----------------
block(48, 2, 21, 14, 'IMU 1, chassis', ['MPU-6050 (GY-521), 3V3', 'SCL D15, SDA D14', 'AD0 -> GND: 0x68'], edge=C33, lsize=7.8)
block(72, 2, 21, 14, 'IMU 2, isolated deck', ['same bus; slack cable', 'across the isolators', 'AD0 -> 3V3: 0x69'], edge=C33, lsize=7.8)
wire([(58, 19.6), (58, 16.4)], C33)
wire([(82, 19.6), (82, 16.4)], C33)
ax.text(70, 18, 'I2C + 3V3 + GND', fontsize=8, color=C33, ha='center', va='center', bbox=dict(fc='white', ec='none', pad=0.4))

# ---------------- legend ----------------
lx, ly = 104, 15
for i, (c, t) in enumerate(((C12, '12 V battery / motor power'), (C5, '5.1 V Pi supply'), (C33, '3.3 V logic + I2C'),
                            (SIG, 'signals'), (USB, 'USB / CSI'))):
    ax.plot([lx, lx + 5], [ly - i * 2.6] * 2, color=c, lw=3)
    ax.text(lx + 6.5, ly - i * 2.6, t, fontsize=8.5, va='center')

out = Path(sys.argv[1] if len(sys.argv) > 1 else '.'); out.mkdir(parents=True, exist_ok=True)
for ext in ('png', 'svg', 'pdf'):
    fig.savefig(out / f'AMR_Wiring_Diagram_v1.{ext}', dpi=130 if ext == 'png' else None)
print('written', out)
