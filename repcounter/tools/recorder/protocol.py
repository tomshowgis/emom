"""Frame parser shared by all host tools. Mirrors firmware/stream/code.py."""
from __future__ import annotations

import struct
from dataclasses import dataclass

MAGIC = b"\xa5\x5a"
TYPE_IMU = 1
TYPE_STATUS = 2
ACC_SCALE = 400.0   # LSB = 2.5 mm/s^2
GYR_SCALE = 1000.0  # LSB = 1 mrad/s

UART_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # host -> device
UART_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # device -> host (notify)
DEVICE_NAME = "EMOM-REP"


@dataclass
class Sample:
    t_ms: int
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float


@dataclass
class Status:
    t_ms: int
    vbat_mv: int
    charging: bool
    streaming: bool
    rate_hz: int


def parse_frame(data: bytes):
    """Return (seq, payload) where payload is list[Sample] or Status; None if malformed."""
    if len(data) < 5 or data[:2] != MAGIC:
        return None
    ftype = data[2]
    (seq,) = struct.unpack_from("<H", data, 3)
    if ftype == TYPE_IMU:
        if len(data) < 11:
            return None
        t0, n, dt = struct.unpack_from("<IBB", data, 5)
        if len(data) < 11 + 12 * n:
            return None
        samples = []
        for i in range(n):
            ax, ay, az, gx, gy, gz = struct.unpack_from("<hhhhhh", data, 11 + 12 * i)
            samples.append(Sample(t0 + i * dt, ax / ACC_SCALE, ay / ACC_SCALE, az / ACC_SCALE,
                                  gx / GYR_SCALE, gy / GYR_SCALE, gz / GYR_SCALE))
        return seq, samples
    if ftype == TYPE_STATUS:
        if len(data) < 15:
            return None
        t, vbat, chg, strm, rate = struct.unpack_from("<IHBBH", data, 5)
        return seq, Status(t, vbat, bool(chg), bool(strm), rate)
    return None
