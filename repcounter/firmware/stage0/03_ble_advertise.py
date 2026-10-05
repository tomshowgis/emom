# Stage 0, test 3: Bluetooth LE advertising with a Nordic UART service.
# Copy to CIRCUITPY/code.py.
# Expected: a device named "EMOM-REP" visible in nRF Connect (iPhone) and in
# Chrome on the Mac (chrome://bluetooth-internals or the Web Bluetooth chooser).
# Blue LED on while connected. Anything you send over UART is echoed back.
import time
import board
import digitalio
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

blue = digitalio.DigitalInOut(board.LED_BLUE)
blue.direction = digitalio.Direction.OUTPUT
blue.value = True  # off

ble = BLERadio()
ble.name = "EMOM-REP"
uart = UARTService()
adv = ProvideServicesAdvertisement(uart)

while True:
    print("advertising as", ble.name)
    ble.start_advertising(adv)
    while not ble.connected:
        time.sleep(0.1)
    ble.stop_advertising()
    print("connected")
    blue.value = False
    while ble.connected:
        if uart.in_waiting:
            data = uart.read(uart.in_waiting)
            print("rx:", data)
            uart.write(b"echo: " + data)
        time.sleep(0.02)
    blue.value = True
    print("disconnected")
