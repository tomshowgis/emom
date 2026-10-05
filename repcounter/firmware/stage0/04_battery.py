# Stage 0, test 4: battery voltage, charge status, and "alive on battery" heartbeat.
# Copy to CIRCUITPY/code.py.
# SAFETY (Seeed wiki): the divider on P0_31 is only safe while READ_BATT_ENABLE is LOW.
# LOW is the safe state, so we hold it LOW for the whole test and read continuously.
# Green LED blinks once per second: unplug USB and it must keep blinking if the
# battery is really connected.
import time
import board
import analogio
import digitalio

DIVIDER = 3.07  # calibrated 2026-10-05: multimeter 4.11 V vs 4.15 V at 3.1

en = digitalio.DigitalInOut(board.READ_BATT_ENABLE)
en.direction = digitalio.Direction.OUTPUT
en.value = False            # enable the reading path and keep it enabled
time.sleep(0.05)
adc = analogio.AnalogIn(board.VBATT)

chg = digitalio.DigitalInOut(board.CHARGE_STATUS)
chg.direction = digitalio.Direction.INPUT
chg.pull = digitalio.Pull.UP

green = digitalio.DigitalInOut(board.LED_GREEN)
green.direction = digitalio.Direction.OUTPUT
green.value = True  # off

def vbat():
    acc = 0
    for _ in range(16):
        acc += adc.value
    raw = acc // 16
    return raw, raw / 65535 * adc.reference_voltage * DIVIDER

while True:
    raw, v = vbat()
    status = "charging" if not chg.value else "not charging / full"
    print("raw %5d  vbat %.3f V  chg_pin=%d  %s" % (raw, v, chg.value, status))
    green.value = False
    time.sleep(0.1)
    green.value = True
    time.sleep(0.9)
