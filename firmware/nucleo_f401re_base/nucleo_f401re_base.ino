// Vibration-Aware AMR - base controller firmware v0.1 for NUCLEO-F401RE
// Arduino IDE + "STM32 MCU based boards" core (STMicroelectronics / STM32duino).
// Board: Nucleo-64, Board part number: Nucleo F401RE, Upload method: STM32CubeProgrammer (SWD).
//
// Does: TB6612 PWM + direction for two motors, quadrature encoder counts on TIM2/TIM3,
// two MPU6050-class IMUs on I2C1, line-based serial link to the Pi over the ST-LINK USB
// (virtual COM port), PI wheel-speed loop, and a 0.5 s command timeout that disables
// the motor driver.
//
// STATUS 17 Nov 2026: v0.2. Compiles for the F401RE. Not yet run: binaries over ~32 KB do not run after a
// Mass Storage (drag-and-drop) upload on this board's ST-LINK, so flash with STM32CubeProgrammer (SWD) or the IDE debugger.
// v0.2 adds flushed start-up messages and skips the IMUs when D14/D15 have no pull-ups.
// Pin plan: see PIN_PLAN.md in this folder.
//
// ---------------- Serial protocol (230400 baud, ASCII, one command per line '\n') -------
// Pi -> STM32
//   V,<left>,<right>     wheel speed targets in encoder counts/s (PI loop)
//   P,<left>,<right>     open-loop PWM, -1000..1000 (for first tests and calibration)
//   S                    stop now (driver to standby)
//   Z                    zero both encoder counts
//   K,<kp>,<ki>,<kf>     speed-loop gains (floats)
//   L,<limit>            PWM limit 0..1000 (default 600)
//   I                    print info line
// V and P must be re-sent at least every 0.5 s (send at 10-20 Hz), or the motors stop.
//
// STM32 -> Pi, every 10 ms (100 Hz):
//   T,<ms>,<encL>,<encR>,<spdL>,<spdR>,<pwmL>,<pwmR>,<flags>,
//     <ax1>,<ay1>,<az1>,<gx1>,<gy1>,<gz1>,<ax2>,<ay2>,<az2>,<gx2>,<gy2>,<gz2>
//   enc = counts since zero, spd = counts/s, pwm = applied -1000..1000.
//   IMU 1 = chassis (0x68), IMU 2 = deck (0x69); raw int16, +-4 g (8192 LSB/g),
//   +-500 deg/s (65.5 LSB/(deg/s)).
//   flags: bit0 driver enabled, bit1 timed out, bit2 IMU1 read failed, bit3 IMU2 read failed,
//          bit4 user button stop, bit5 velocity mode
// Also: "I,..." info lines and "E,<text>" error lines.

#include <Wire.h>

// ---------------- pins ----------------
const uint32_t PIN_PWMA = PA8;   // D7  TIM1_CH1 -> TB6612 PWMA (left motor)
const uint32_t PIN_PWMB = PA9;   // D8  TIM1_CH2 -> TB6612 PWMB (right motor)
const uint32_t PIN_AIN1 = PA10;  // D2
const uint32_t PIN_AIN2 = PB5;   // D4
const uint32_t PIN_BIN1 = PB4;   // D5
const uint32_t PIN_BIN2 = PB10;  // D6
const uint32_t PIN_STBY = PC7;   // D9  TB6612 STBY (high = enabled)
const uint32_t PIN_LED  = PA5;   // LD2 green LED (also D13; leave D13 unconnected)
const uint32_t PIN_BTN  = PC13;  // B1 blue user button, low when pressed
// Encoders (set up by registers in encoderInit):
//   left  A = PA0 (A0), B = PA1 (A1)  -> TIM2 CH1/CH2, AF1
//   right A = PA6 (D12), B = PA7 (D11) -> TIM3 CH1/CH2, AF2
// IMUs: I2C1 SCL = PB8 (D15), SDA = PB9 (D14)  (Wire defaults on this board)

// ---------------- settings ----------------
const uint32_t BAUD = 230400;
const uint32_t LOOP_US = 10000;          // 100 Hz control + telemetry
const uint32_t CMD_TIMEOUT_MS = 500;
const uint8_t IMU_ADDR[2] = {0x68, 0x69};

// Flip these on the bench so that a positive command drives the robot FORWARD and
// the encoder counts UP for that wheel. The two motors are mirror images, so expect
// one side to need flipping.
const bool LEFT_MOTOR_INVERT = false;
const bool RIGHT_MOTOR_INVERT = false;
const bool LEFT_ENC_INVERT = false;
const bool RIGHT_ENC_INVERT = false;

// Speed loop: STARTING VALUES ONLY, tune on the bench (K command).
float kp = 0.05f, ki = 0.5f, kf = 0.0f;
int pwmLimit = 600;                      // of 1000; raise only after first drives
const int PWM_SLEW = 20;                 // max PWM change per 10 ms tick (0 -> 1000 in 0.5 s)

// ---------------- state ----------------
enum Mode { MODE_OFF, MODE_PWM, MODE_VEL };
Mode mode = MODE_OFF;
float target[2] = {0, 0};                // PWM (MODE_PWM) or counts/s (MODE_VEL)
float integ[2] = {0, 0};
int pwmOut[2] = {0, 0};
int32_t encPos[2] = {0, 0};
uint16_t encLast[2] = {0, 0};
float speed[2] = {0, 0};
uint32_t lastCmdMs = 0;
bool timedOut = false, buttonStop = false;
bool imuOk[2] = {false, false};
bool i2cPresent = false;                 // false if D14/D15 have no pull-ups (no IMU wired): IMUs skipped
uint8_t imuWho[2] = {0, 0};
int16_t imu[2][6];
char rxBuf[64];
uint8_t rxLen = 0;

// ---------------- encoders ----------------
static void encoderInit() {
  RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
  RCC->APB1ENR |= RCC_APB1ENR_TIM2EN | RCC_APB1ENR_TIM3EN;
  (void)RCC->APB1ENR;
  const uint8_t pins[4] = {0, 1, 6, 7};
  for (uint8_t i = 0; i < 4; i++) {
    uint8_t p = pins[i];
    GPIOA->MODER = (GPIOA->MODER & ~(3UL << (2 * p))) | (2UL << (2 * p));  // alternate function
    GPIOA->PUPDR = (GPIOA->PUPDR & ~(3UL << (2 * p))) | (1UL << (2 * p));  // pull-up
  }
  GPIOA->AFR[0] = (GPIOA->AFR[0] & ~((0xFUL << 0) | (0xFUL << 4) | (0xFUL << 24) | (0xFUL << 28)))
                | (1UL << 0) | (1UL << 4)      // PA0, PA1 -> AF1 TIM2
                | (2UL << 24) | (2UL << 28);   // PA6, PA7 -> AF2 TIM3
  TIM_TypeDef *tims[2] = {TIM2, TIM3};
  for (uint8_t i = 0; i < 2; i++) {
    TIM_TypeDef *t = tims[i];
    t->CR1 = 0;
    t->SMCR = 3;                                            // SMS = 011: encoder mode 3 (x4)
    t->CCMR1 = (1UL << 0) | (1UL << 8)                      // CC1S = CC2S = 01 (TI1, TI2 inputs)
             | (3UL << 4) | (3UL << 12);                    // IC1F = IC2F = 0011 input filter
    t->CCER = 0;
    t->ARR = 0xFFFF;                                        // 16-bit wrap on both; deltas handle it
    t->CNT = 0;
    t->CR1 = TIM_CR1_CEN;
  }
}

static void encoderUpdate(float dt) {
  uint16_t now[2] = {(uint16_t)TIM2->CNT, (uint16_t)TIM3->CNT};
  for (uint8_t i = 0; i < 2; i++) {
    int16_t d = (int16_t)(now[i] - encLast[i]);
    encLast[i] = now[i];
    bool inv = (i == 0) ? LEFT_ENC_INVERT : RIGHT_ENC_INVERT;
    if (inv) d = -d;
    encPos[i] += d;
    float s = d / dt;
    speed[i] = 0.7f * speed[i] + 0.3f * s;                  // light low-pass on measured speed
  }
}

// ---------------- motors ----------------
static void driverEnable(bool on) { digitalWrite(PIN_STBY, on ? HIGH : LOW); }

static void motorWrite(uint8_t side, int pwm) {
  bool inv = (side == 0) ? LEFT_MOTOR_INVERT : RIGHT_MOTOR_INVERT;
  int p = inv ? -pwm : pwm;
  uint32_t in1 = side == 0 ? PIN_AIN1 : PIN_BIN1;
  uint32_t in2 = side == 0 ? PIN_AIN2 : PIN_BIN2;
  uint32_t pw = side == 0 ? PIN_PWMA : PIN_PWMB;
  if (p > 0)      { digitalWrite(in1, HIGH); digitalWrite(in2, LOW); }
  else if (p < 0) { digitalWrite(in1, LOW);  digitalWrite(in2, HIGH); }
  else            { digitalWrite(in1, LOW);  digitalWrite(in2, LOW); }   // coast
  int mag = p < 0 ? -p : p;
  if (mag > 1000) mag = 1000;
  analogWrite(pw, (mag * 1023) / 1000);
}

static void stopAll() {
  mode = MODE_OFF;
  for (uint8_t i = 0; i < 2; i++) { target[i] = 0; integ[i] = 0; pwmOut[i] = 0; motorWrite(i, 0); }
  driverEnable(false);
}

static int clampi(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }

static void controlUpdate(float dt) {
  for (uint8_t i = 0; i < 2; i++) {
    float want = 0;
    if (mode == MODE_PWM) {
      want = target[i];
    } else if (mode == MODE_VEL) {
      float err = target[i] - speed[i];
      integ[i] += err * dt;
      float iMax = (ki > 0) ? pwmLimit / ki : 0;            // anti-windup
      if (integ[i] > iMax) integ[i] = iMax;
      if (integ[i] < -iMax) integ[i] = -iMax;
      want = kf * target[i] + kp * err + ki * integ[i];
      if (target[i] == 0 && speed[i] > -1 && speed[i] < 1) { want = 0; integ[i] = 0; }
    }
    int w = clampi((int)want, -pwmLimit, pwmLimit);
    int step = clampi(w - pwmOut[i], -PWM_SLEW, PWM_SLEW);
    pwmOut[i] += step;
    motorWrite(i, pwmOut[i]);
  }
}

// ---------------- IMUs ----------------
static bool imuWrite(uint8_t addr, uint8_t reg, uint8_t val) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

static bool imuInit(uint8_t i) {
  uint8_t a = IMU_ADDR[i];
  Wire.beginTransmission(a);
  Wire.write(0x75);                                         // WHO_AM_I
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(a, (uint8_t)1) != 1) return false;
  imuWho[i] = Wire.read();
  bool ok = imuWrite(a, 0x6B, 0x01)                         // wake, clock from gyro X PLL
         && imuWrite(a, 0x19, 0x04)                         // sample rate 1 kHz / (1 + 4) = 200 Hz
         && imuWrite(a, 0x1A, 0x03)                         // DLPF ~44 Hz accel, 42 Hz gyro
         && imuWrite(a, 0x1B, 0x08)                         // gyro +-500 deg/s
         && imuWrite(a, 0x1C, 0x08);                        // accel +-4 g
  return ok;
}

static bool imuRead(uint8_t i) {
  uint8_t a = IMU_ADDR[i];
  Wire.beginTransmission(a);
  Wire.write(0x3B);                                         // ACCEL_XOUT_H
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(a, (uint8_t)14) != 14) return false;
  uint8_t b[14];
  for (uint8_t k = 0; k < 14; k++) b[k] = Wire.read();
  imu[i][0] = (int16_t)((b[0] << 8) | b[1]);
  imu[i][1] = (int16_t)((b[2] << 8) | b[3]);
  imu[i][2] = (int16_t)((b[4] << 8) | b[5]);
  imu[i][3] = (int16_t)((b[8] << 8) | b[9]);                // b[6..7] is temperature
  imu[i][4] = (int16_t)((b[10] << 8) | b[11]);
  imu[i][5] = (int16_t)((b[12] << 8) | b[13]);
  return true;
}

// With nothing wired to D14/D15 the I2C lines float and the I2C peripheral can hang.
// IMU breakouts have pull-ups, so both lines read high even against the internal pull-downs.
static bool i2cLinesPulledUp() {
  pinMode(PB8, INPUT_PULLDOWN);
  pinMode(PB9, INPUT_PULLDOWN);
  delay(2);
  bool ok = digitalRead(PB8) == HIGH && digitalRead(PB9) == HIGH;
  pinMode(PB8, INPUT);
  pinMode(PB9, INPUT);
  return ok;
}

// ---------------- serial ----------------
static void printInfo() {
  char s[128];
  snprintf(s, sizeof(s), "I,fw=0.2,board=NUCLEO-F401RE,i2c=%s,imu1_who=0x%02X,imu2_who=0x%02X,limit=%d,timeout_ms=%lu\n",
           i2cPresent ? "ok" : "no_pullups", imuWho[0], imuWho[1], pwmLimit, (unsigned long)CMD_TIMEOUT_MS);
  Serial.write(s);
}

static void handleLine(char *line) {
  char *tok = strtok(line, ",");
  if (!tok) return;
  char c = tok[0];
  char *a = strtok(NULL, ",");
  char *b = strtok(NULL, ",");
  char *d = strtok(NULL, ",");
  if ((c == 'V' || c == 'P') && a && b) {
    float l = strtof(a, NULL), r = strtof(b, NULL);
    Mode m = (c == 'V') ? MODE_VEL : MODE_PWM;
    if (m != mode) { integ[0] = integ[1] = 0; }
    mode = m;
    target[0] = l; target[1] = r;
    lastCmdMs = millis();
    timedOut = false;
    buttonStop = false;
    driverEnable(true);
  } else if (c == 'S') {
    stopAll();
  } else if (c == 'Z') {
    encPos[0] = encPos[1] = 0;
  } else if (c == 'K' && a && b && d) {
    kp = strtof(a, NULL); ki = strtof(b, NULL); kf = strtof(d, NULL);
    integ[0] = integ[1] = 0;
  } else if (c == 'L' && a) {
    pwmLimit = clampi((int)strtol(a, NULL, 10), 0, 1000);
  } else if (c == 'I') {
    printInfo();
  } else {
    Serial.write("E,bad command\n");
  }
}

static void serialPoll() {
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch == '\r') continue;
    if (ch == '\n') {
      rxBuf[rxLen] = 0;
      if (rxLen) handleLine(rxBuf);
      rxLen = 0;
    } else if (rxLen < sizeof(rxBuf) - 1) {
      rxBuf[rxLen++] = ch;
    } else {
      rxLen = 0;                                            // overlong line: drop it
      Serial.write("E,line too long\n");
    }
  }
}

static void sendTelemetry() {
  uint8_t flags = (digitalRead(PIN_STBY) == HIGH ? 1 : 0) | (timedOut ? 2 : 0) | (imuOk[0] ? 0 : 4)
                | (imuOk[1] ? 0 : 8) | (buttonStop ? 16 : 0) | (mode == MODE_VEL ? 32 : 0);
  char s[256];
  snprintf(s, sizeof(s), "T,%lu,%ld,%ld,%d,%d,%d,%d,%u,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
           (unsigned long)millis(), (long)encPos[0], (long)encPos[1], (int)speed[0], (int)speed[1],
           pwmOut[0], pwmOut[1], flags,
           imu[0][0], imu[0][1], imu[0][2], imu[0][3], imu[0][4], imu[0][5],
           imu[1][0], imu[1][1], imu[1][2], imu[1][3], imu[1][4], imu[1][5]);
  Serial.write(s);
}

// ---------------- main ----------------
static void stage(const char *msg) {                       // start-up trace: flushed so it survives a crash
  Serial.write(msg);
  Serial.flush();
}

void setup() {
  pinMode(PIN_LED, OUTPUT); digitalWrite(PIN_LED, HIGH);   // LED stays ON only while setup runs
  Serial.begin(BAUD);
  delay(200);
  stage("I,boot\n");
  pinMode(PIN_STBY, OUTPUT); digitalWrite(PIN_STBY, LOW);   // driver off first
  pinMode(PIN_AIN1, OUTPUT); pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_BIN1, OUTPUT); pinMode(PIN_BIN2, OUTPUT);
  pinMode(PIN_BTN, INPUT);                                  // board has its own pull-up
  stage("I,pins_ok\n");
  analogWriteResolution(10);
  analogWriteFrequency(20000);                              // 20 kHz, above hearing
  stage("I,pwm_config_ok\n");
  stopAll();
  stage("I,driver_off\n");

  encoderInit();
  encLast[0] = (uint16_t)TIM2->CNT;
  encLast[1] = (uint16_t)TIM3->CNT;
  stage("I,encoders_ok\n");

  memset(imu, 0, sizeof(imu));
  i2cPresent = i2cLinesPulledUp();
  stage(i2cPresent ? "I,i2c_pullups_found\n" : "I,i2c_no_pullups\n");
  if (i2cPresent) {
    Wire.begin();
    Wire.setClock(400000);                                  // drop to 100000 if the deck cable gives errors
    stage("I,wire_begin_ok\n");
    for (uint8_t i = 0; i < 2; i++) imuOk[i] = imuInit(i);
    stage("I,imu_init_done\n");
  } else {
    stage("E,no pull-ups on D14/D15: IMUs skipped (wire an IMU and reset)\n");
  }
  printInfo();
  digitalWrite(PIN_LED, LOW);
}

void loop() {
  static uint32_t nextUs = micros();
  serialPoll();

  if (digitalRead(PIN_BTN) == LOW && mode != MODE_OFF) { stopAll(); buttonStop = true; }
  if (mode != MODE_OFF && millis() - lastCmdMs > CMD_TIMEOUT_MS) { stopAll(); timedOut = true; }

  if ((int32_t)(micros() - nextUs) >= 0) {
    nextUs += LOOP_US;
    const float dt = LOOP_US * 1e-6f;
    encoderUpdate(dt);
    if (mode != MODE_OFF) controlUpdate(dt);
    for (uint8_t i = 0; i < 2 && i2cPresent; i++) {
      bool ok = imuRead(i);
      if (!ok && imuOk[i]) memset(imu[i], 0, sizeof(imu[i]));
      imuOk[i] = ok;
    }
    sendTelemetry();
    // LED: solid while driving, slow blink when idle, fast blink after a timeout
    uint32_t ms = millis();
    bool led = (mode != MODE_OFF) ? true : (timedOut ? (ms / 100) % 2 : (ms / 500) % 2);
    digitalWrite(PIN_LED, led ? HIGH : LOW);
  }
}
