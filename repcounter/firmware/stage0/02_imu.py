# Stage 0, test 2: LSM6DS3TR-C accelerometer + gyro over the dedicated IMU I2C bus.
# Copy to CIRCUITPY/code.py. Open the serial console.
# Expected: in rest, accel ~ (0, 0, +-9.8) depending on orientation; gyro ~ 0.
# Prints a measured sample rate every 2 s (how fast CircuitPython can poll the sensor).
import time
import board
import busio
import digitalio
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
from adafruit_lsm6ds import Rate, AccelRange, GyroRange

# 1. Power the IMU (P1_08 high), wait for it to boot.
imu_pwr = digitalio.DigitalInOut(board.IMU_PWR)
imu_pwr.direction = digitalio.Direction.OUTPUT
imu_pwr.value = True
time.sleep(0.05)

# 2. Dedicated bus, not the header SCL/SDA.
i2c = busio.I2C(board.IMU_SCL, board.IMU_SDA)
imu = LSM6DS3(i2c)
imu.accelerometer_range = AccelRange.RANGE_8G       # swings may exceed 4 g
imu.gyro_range = GyroRange.RANGE_1000_DPS
imu.accelerometer_data_rate = Rate.RATE_208_HZ
imu.gyro_data_rate = Rate.RATE_208_HZ
print("IMU ok, address 0x6A, 208 Hz configured")

n = 0
t0 = time.monotonic()
last_print = t0
while True:
    ax, ay, az = imu.acceleration   # m/s^2
    gx, gy, gz = imu.gyro           # rad/s
    n += 1
    now = time.monotonic()
    if now - last_print >= 2.0:
        hz = n / (now - t0)
        print("acc %6.2f %6.2f %6.2f  gyro %6.2f %6.2f %6.2f  poll %.0f Hz" % (ax, ay, az, gx, gy, gz, hz))
        last_print = now
