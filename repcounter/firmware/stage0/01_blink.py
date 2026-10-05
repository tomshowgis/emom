# Stage 0, test 1: RGB LED. Copy to CIRCUITPY/code.py.
# Expected: red, green, blue, each for 1 s, in a loop. LEDs are active LOW.
import time
import board
import digitalio

def led(pin):
    d = digitalio.DigitalInOut(pin)
    d.direction = digitalio.Direction.OUTPUT
    d.value = True  # off
    return d

leds = [("red", led(board.LED_RED)), ("green", led(board.LED_GREEN)), ("blue", led(board.LED_BLUE))]
print("blink test: red -> green -> blue")
while True:
    for name, d in leds:
        d.value = False  # on
        print(name)
        time.sleep(1.0)
        d.value = True   # off
