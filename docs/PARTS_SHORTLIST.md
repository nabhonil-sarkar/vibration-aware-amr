# Parts shortlist

Supplier pages checked **2 October 2026**. This is the recorded engineering shortlist, not a current quotation, purchase record or final BOM. Recheck specifications, stock, prices and checkout charges before ordering. Preserve the approved outline; reconcile these candidates with its categories and lab stock.

## Cytron Singapore drivetrain

| Candidate | Quantity | Listed SGD/unit | Recorded specification |
| --- | ---: | ---: | --- |
| [SPG30E-GR131 encoder motor](https://sg.cytron.io/p-12v-37mm-dc-geared-motor-with-encoder-spg30e-gr131) | 2 | 27.14 | 12V; 60 RPM at rated load; listed torque 5 kg·cm |
| [SPG30E-GR56 encoder motor](https://sg.cytron.io/p-12v-37mm-dc-geared-motor-with-encoder-spg30e-gr56) | 2 instead | 27.14 | 12V; 112 RPM at rated load; listed torque 2.1 kg·cm |
| [Rubber wheel](https://sg.cytron.io/p-small-robot-rubber-wheel-65x26.5mm) | 2 | 3.57 | Current page description: 68 × 27 mm despite historical URL |
| [6 mm hex coupling](https://sg.cytron.io/p-hex-brass-mini-wheel-coupling-6mm) | 2 | 1.96 | Matches the motors' 6 mm shafts and the rubber wheels |
| [SPG30/SPG50 metal bracket](https://sg.cytron.io/p-dc-geared-motor-bracket-spg30-spg50) | 2 | 5.00 | Supplier-supported SPG30E mounting; drawing available |
| [MDD3A dual driver](https://sg.cytron.io/p-3amp-4v-16v-dc-motor-driver-2-channels) | 1 | 13.29 | 4–16V, 3A continuous/channel, 3.3V-compatible control |

Recorded subtotal with either motor pair: **S$88.63**, excluding final delivery/checkout charges. Both motors list 1.2A stall current, making MDD3A a compatible candidate on paper. Its 5V/200mA auxiliary output cannot power Pi 5.

Calculated speeds with 68 mm wheels at the listed rated-load RPM: approximately 0.21 m/s for GR131 and 0.40 m/s for GR56. These are kinematic estimates, not observed robot speeds. Final selection needs total mass, acceleration, rolling resistance and slope requirements. V04's 120 mm wheels and motor envelopes are provisional and differ from this shortlist; adopting these parts requires coordinated mounting/ground-clearance changes.

[Waveshare UPS HAT E](https://sg.cytron.io/p-v-hat-ups-21700) was listed at S$58.93 without four required 21700 cells, with Pi 5 compatibility and 5V/6A output. It is a separate power-layout candidate, not a selected shared drivetrain battery system. The checked [W420 ball castor](https://sg.cytron.io/p-w420-steel-ball-universal-wheel-castor) was S$1.07 with no stated load rating and differs from the planned swivel castor. Checked Cytron [RPLIDAR A1](https://sg.cytron.io/ampp-rplidar-a1m8-360-degree-laser-scanner-kit-12m-range) and [Adafruit MPU6050](https://sg.cytron.io/p-adafruit-mpu-6050-6dof-accel-and-gyro-sensor-stemma-qt-qwiic) listings were discontinued.

## Kuriosity comparison

The [Kuriosity catalogue](https://kuriosity.sg/) check recorded RPLIDAR A1M8-R6 kit S$146, original-chip soldered MPU6050 S$9 each (two needed) and Pi 5 active cooler S$15. Camera Module 3 S$58 is CSI and needs the Pi 5 cable; it differs from the proposed USB camera.

The 12V encoder worm motor was S$17.20 each, with 40 RPM no-load and 30 RPM loaded; the 65 mm wheel/coupling pair was S$10.60. Calculated loaded-speed estimate is about 0.10 m/s, and the motor torque units were ambiguous. The 12V/4800mAh battery/charger at S$46 had unresolved discharge-current/protection details. The generic driver's ratings and a buck converter's 3A continuous/5A peak distinction need checking before selection.

Still unresolved: rated rear swivel castor, payload isolators, MCU, latching motor E-stop, final battery/charger/protection, Pi 5 regulated power and exact vendor mounting dimensions. No hardware purchase or installation is implied by this list.
