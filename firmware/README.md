# Firmware

| Path | What it is |
| --- | --- |
| [nucleo_f401re_base/](nucleo_f401re_base) | Base controller for the NUCLEO-F401RE (Arduino IDE with the STM32duino core): TB6612 PWM and direction, quadrature encoders on TIM2/TIM3, two MPU-6050 IMUs on I2C1, ASCII serial link to the Pi over the ST-LINK USB at 230400 baud, PI wheel-speed loop, 0.5 s command timeout that disables the driver |
| [nucleo_f401re_base/PIN_PLAN.md](nucleo_f401re_base/PIN_PLAN.md) | Pin table, power and ground, limits, flashing steps, bench order |
| [drive_link_test.py](drive_link_test.py) | Pi-side test (pyserial): drives the wheels for a few seconds, stops sending, and checks the firmware times out by itself |

**Status, 17 Nov 2026:** v0.2 compiled (STM32 core 3.1.0), flashed through the IDE debugger and run on the board: 100 Hz telemetry, chassis IMU read, commands received, 0.5 s timeout works. Motors not yet connected; speed-loop gains are starting values. Do not use Mass Storage upload on this board (see PIN_PLAN.md). Wiring: [docs/wiring](../docs/wiring).
