"""Background BLE client: connects to EMOM-REP, parses frames, buffers samples.

Runs its own asyncio loop in a thread so a synchronous app (Dash, CLI) can poll it.
"""
from __future__ import annotations

import asyncio
import threading
import time
from collections import deque

from bleak import BleakClient, BleakScanner

from .protocol import DEVICE_NAME, UART_RX, UART_TX, Sample, Status, parse_frame


class BleStreamer:
    def __init__(self, name: str = DEVICE_NAME, buffer_seconds: float = 120.0, rate_hz: int = 100):
        self.name = name
        self.samples: deque[Sample] = deque(maxlen=int(buffer_seconds * rate_hz))
        self.status: Status | None = None
        self.state = "idle"          # idle | scanning | connecting | connected | error
        self.error = ""
        self.rssi = None
        self.mtu = None
        self.frames = 0
        self.dropped_frames = 0
        self.streaming_requested = False
        self._last_seq = None
        self._lock = threading.Lock()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._client: BleakClient | None = None
        self._stop = False
        self._task = None

    # ---- public API (thread-safe) ------------------------------------------------
    def connect(self):
        if self._task is None or self._task.done():
            self._stop = False
            self._task = asyncio.run_coroutine_threadsafe(self._run(), self._loop)

    def disconnect(self):
        self._stop = True

    def start_stream(self):
        self.streaming_requested = True
        self._send(b"S")

    def stop_stream(self):
        self.streaming_requested = False
        self._send(b"X")

    def request_status(self):
        self._send(b"B")

    def clear(self):
        with self._lock:
            self.samples.clear()
            self.frames = 0
            self.dropped_frames = 0
            self._last_seq = None

    def snapshot(self) -> list[Sample]:
        with self._lock:
            return list(self.samples)

    def drain(self) -> list[Sample]:
        """Return and remove all buffered samples (for recording to disk)."""
        with self._lock:
            out = list(self.samples)
            self.samples.clear()
            return out

    # ---- internals -----------------------------------------------------------------
    def _send(self, data: bytes):
        if self._client and self._client.is_connected:
            asyncio.run_coroutine_threadsafe(self._client.write_gatt_char(UART_RX, data, response=False), self._loop)

    def _on_notify(self, _handle, data: bytearray):
        parsed = parse_frame(bytes(data))
        if parsed is None:
            return
        seq, payload = parsed
        with self._lock:
            if self._last_seq is not None:
                gap = (seq - self._last_seq - 1) & 0xFFFF
                if 0 < gap < 1000:
                    self.dropped_frames += gap
            self._last_seq = seq
            self.frames += 1
            if isinstance(payload, Status):
                self.status = payload
            else:
                self.samples.extend(payload)

    async def _run(self):
        try:
            self.state = "scanning"
            dev = None
            for _ in range(3):
                devs = await BleakScanner.discover(timeout=5.0, return_adv=True)
                for d, (device, adv) in devs.items():
                    if adv.local_name == self.name:
                        dev, self.rssi = device, adv.rssi
                if dev or self._stop:
                    break
            if not dev:
                self.state, self.error = "error", f"{self.name} not found"
                return
            self.state = "connecting"
            async with BleakClient(dev, timeout=15.0) as client:
                self._client = client
                await client.start_notify(UART_TX, self._on_notify)
                await asyncio.sleep(0.3)  # let the central finish MTU negotiation
                try:
                    self.mtu = int(client.mtu_size)
                except Exception:  # noqa: BLE001
                    self.mtu = 23
                await client.write_gatt_char(UART_RX, f"M{self.mtu - 3}".encode(), response=False)
                await client.write_gatt_char(UART_RX, b"B", response=False)
                self.state = "connected"
                while client.is_connected and not self._stop:
                    await asyncio.sleep(0.2)
                if client.is_connected:
                    try:
                        await client.write_gatt_char(UART_RX, b"X", response=False)
                        await client.stop_notify(UART_TX)
                    except Exception:  # noqa: BLE001
                        pass
            self.state = "idle"
        except Exception as e:  # noqa: BLE001
            self.state, self.error = "error", repr(e)
        finally:
            self._client = None
            self.streaming_requested = False


def wait_for(cond, timeout: float, step: float = 0.1) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        if cond():
            return True
        time.sleep(step)
    return False
