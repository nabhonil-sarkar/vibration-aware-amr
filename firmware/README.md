# Firmware

| Path | What it is |
| --- | --- |
| [nucleo_f401re_base/](nucleo_f401re_base) | Base controller for the NUCLEO-F401RE (Arduino IDE with the STM32duino core): TB6612 PWM and direction, quadrature encoders on TIM2/TIM3, two MPU-6050 IMUs on I2C1, ASCII serial link to the Pi over the ST-LINK USB at 230400 baud, PI wheel-speed loop, 0.5 s command timeout that disables the driver |
| [nucleo_f401re_base/PIN_PLAN.md](nucleo_f401re_base/PIN_PLAN.md) | Pin table, power and ground, limits, flashing steps, bench order |
| [drive_link_test.py](drive_link_test.py) | Pi-side test (pyserial): drives the wheels for a few seconds, stops sending, and checks the firmware times out by itself |

**Status, 17 Nov 2026:** written and syntax-checked against stub headers. Not yet compiled for the board, flashed or run. Speed-loop gains are starting values to be tuned on the bench. Wiring: [docs/wiring](../docs/wiring).
