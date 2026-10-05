"""Stage 0, test 3 helper: find EMOM-REP from the Mac and test the UART echo.

Usage:  .venv/bin/python repcounter/tools/ble_scan.py
macOS asks for Bluetooth permission for the terminal app on first run.
"""
import asyncio
import traceback

from bleak import BleakClient, BleakScanner

UART_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # write to device
UART_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # notifications from device
NAME = "EMOM-REP"


async def main():
    print("scanning 8 s...")
    devs = await BleakScanner.discover(timeout=8.0, return_adv=True)
    print("devices seen:", len(devs))
    found = None
    for _, (dev, adv) in devs.items():
        if adv.local_name:
            print("  ", adv.local_name, "RSSI", adv.rssi)
        if adv.local_name == NAME:
            found = dev
    if not found:
        print(NAME, "not found")
        return
    got = []
    async with BleakClient(found, timeout=15) as c:
        print("connected:", c.is_connected)
        await c.start_notify(UART_TX, lambda h, d: got.append(bytes(d)))
        await c.write_gatt_char(UART_RX, b"ping 123\n", response=False)
        await asyncio.sleep(1.5)
        print("echo:", b"".join(got))
    print("disconnected")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except BaseException:
        traceback.print_exc()
