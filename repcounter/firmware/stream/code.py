# EMOM rep counter — stage 1 firmware: stream raw IMU samples over BLE (Nordic UART).
#
# Frame format (little endian), one notification per frame:
#   0xA5 0x5A  magic
#   u8   type        1 = IMU batch, 2 = status
#   u16  seq         frame counter (wraps), lets the host detect drops
#   type 1: u32 t_ms (time of first sample), u8 n, u8 dt_ms, then n * 6 * int16
#           acc  in units of 1/400 m/s^2  (LSB = 2.5 mm/s^2, range +-82 m/s^2)
#           gyro in units of 1/1000 rad/s (LSB = 1 mrad/s,  range +-32 rad/s)
#   type 2: u32 t_ms, u16 vbat_mV, u8 charging, u8 streaming, u16 sample_rate_hz
# Commands from host (ASCII): "S" start, "X" stop, "B" status now,
# "M<bytes>" max notification payload the host can receive (MTU-3); device packs frames to fit.
import struct
import time

import analogio
import board
import busio
import digitalio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_lsm6ds import AccelRange, GyroRange, Rate
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3

NAME = "EMOM-REP"
RATE_HZ = 100
DT_MS = 1000 // RATE_HZ
ACC_SCALE = 400.0
GYR_SCALE = 1000.0
VBAT_DIVIDER = 3.07
STATUS_EVERY_MS = 2000


def out(pin, off=True):
    d = digitalio.DigitalInOut(pin)
    d.direction = digitalio.Direction.OUTPUT
    d.value = off
    return d


led_r, led_g, led_b = out(board.LED_RED), out(board.LED_GREEN), out(board.LED_BLUE)

# --- IMU -------------------------------------------------------------------
imu_pwr = out(board.IMU_PWR, off=True)  # True = powered
time.sleep(0.05)
i2c = busio.I2C(board.IMU_SCL, board.IMU_SDA)
imu = LSM6DS3(i2c)
imu.accelerometer_range = AccelRange.RANGE_8G
imu.gyro_range = GyroRange.RANGE_1000_DPS
imu.accelerometer_data_rate = Rate.RATE_208_HZ
imu.gyro_data_rate = Rate.RATE_208_HZ

# --- battery (READ_BATT_ENABLE low = safe, measurement enabled) ------------
batt_en = out(board.READ_BATT_ENABLE, off=False)
vbat_adc = analogio.AnalogIn(board.VBATT)
chg = digitalio.DigitalInOut(board.CHARGE_STATUS)
chg.direction = digitalio.Direction.INPUT
chg.pull = digitalio.Pull.UP


def vbat_mv():
    acc = 0
    for _ in range(8):
        acc += vbat_adc.value
    return int(acc / 8 / 65535 * vbat_adc.reference_voltage * VBAT_DIVIDER * 1000)


# --- BLE -------------------------------------------------------------------
ble = BLERadio()
ble.name = NAME
uart = UARTService()
adv = ProvideServicesAdvertisement(uart)
# UARTService.write() splits into 20-byte notifications; write the bound
# characteristic directly so one frame = one notification of up to MTU-3 bytes.
tx_char = uart._tx.bound_characteristic  # pylint: disable=protected-access

seq = 0


def send(payload):
    global seq
    frame = struct.pack("<BBBH", 0xA5, 0x5A, payload[0], seq & 0xFFFF) + payload[1:]
    seq += 1
    tx_char.value = frame


def send_status(t_ms, streaming):
    send(struct.pack("<BIHBBH", 2, t_ms & 0xFFFFFFFF, vbat_mv(), 0 if chg.value else 1, 1 if streaming else 0, RATE_HZ))


def now_ms():
    return time.monotonic_ns() // 1_000_000


print("stream firmware ready, rate", RATE_HZ, "Hz")
while True:
    led_b.value = True
    led_r.value = False
    ble.start_advertising(adv)
    print("advertising", NAME)
    while not ble.connected:
        time.sleep(0.1)
    ble.stop_advertising()
    led_r.value = True
    led_b.value = False
    conn = ble.connections[0]

    host_mtu = [0]  # set by "M<n>" from the host; CircuitPython's own max_packet_length stays at 20

    def frame_size():
        try:
            mtu = conn.max_packet_length
        except Exception:  # pylint: disable=broad-except
            mtu = 20
        mtu = max(mtu, host_mtu[0], 23)
        return mtu, max(1, min(20, (mtu - 11) // 12))

    mtu, per_frame = frame_size()
    print("connected, packet", mtu, "bytes ->", per_frame, "samples/frame")

    streaming = False
    buf = bytearray(11 + 12 * per_frame)
    n = 0
    t_first = 0
    next_t = now_ms()
    last_status = 0
    while ble.connected:
        # commands
        if uart.in_waiting:
            cmd = uart.read(uart.in_waiting)
            if b"M" in cmd:
                try:
                    digits = "".join(chr(c) for c in cmd[cmd.index(b"M") + 1:] if 48 <= c <= 57)
                    host_mtu[0] = min(int(digits), 244)
                    print("host mtu", host_mtu[0])
                except ValueError:
                    pass
            if b"S" in cmd:
                mtu, per_frame = frame_size()
                buf = bytearray(11 + 12 * per_frame)
                streaming = True
                n = 0
                next_t = now_ms()
                print("stream on, packet", mtu, "bytes ->", per_frame, "samples/frame")
            if b"X" in cmd:
                streaming = False
                n = 0
                print("stream off")
            if b"B" in cmd:
                send_status(now_ms(), streaming)
        t = now_ms()
        if streaming and t >= next_t:
            next_t += DT_MS
            if t - next_t > 200:  # fell far behind (e.g. BLE stall): resync
                next_t = t
            ax, ay, az = imu.acceleration
            gx, gy, gz = imu.gyro
            if n == 0:
                t_first = t
            struct.pack_into(
                "<hhhhhh", buf, 11 + 12 * n,
                int(ax * ACC_SCALE), int(ay * ACC_SCALE), int(az * ACC_SCALE),
                int(gx * GYR_SCALE), int(gy * GYR_SCALE), int(gz * GYR_SCALE),
            )
            n += 1
            if n == per_frame:
                struct.pack_into("<BBBHIBB", buf, 0, 0xA5, 0x5A, 1, seq & 0xFFFF, t_first & 0xFFFFFFFF, n, DT_MS)
                seq += 1
                try:
                    tx_char.value = buf
                except Exception as e:  # pylint: disable=broad-except
                    print("tx error", e)
                n = 0
                led_g.value = not led_g.value
        if t - last_status >= STATUS_EVERY_MS:
            last_status = t
            try:
                send_status(t, streaming)
            except Exception as e:  # pylint: disable=broad-except
                print("status tx error", e)
        if not streaming:
            time.sleep(0.02)
    led_g.value = True
    print("disconnected")
