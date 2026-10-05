"""Stage 1 check: connect, stream for N seconds, report rate and drops.

Usage: .venv/bin/python repcounter/tools/stream_test.py [seconds]
Run from the terminal (macOS Bluetooth permission), not from a sandbox.
"""
import sys
import time

from recorder.ble_stream import BleStreamer, wait_for

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0
s = BleStreamer()
s.connect()
print("connecting...")
if not wait_for(lambda: s.state in ("connected", "error"), 40):
    print("timeout"); sys.exit(1)
if s.state == "error":
    print("error:", s.error); sys.exit(1)
print("connected, RSSI", s.rssi, "MTU", s.mtu)
wait_for(lambda: s.status is not None, 5)
print("status:", s.status)
s.clear()
s.start_stream()
t0 = time.time()
last = 0
while time.time() - t0 < secs:
    time.sleep(1.0)
    n = len(s.samples)
    print(f"  t={time.time()-t0:4.1f}s samples={n:5d} (+{n-last:3d}/s) frames={s.frames} dropped={s.dropped_frames}")
    last = n
s.stop_stream()
time.sleep(0.5)
data = s.snapshot()
if len(data) > 2:
    span = (data[-1].t_ms - data[0].t_ms) / 1000
    print(f"\n{len(data)} samples over {span:.2f} s on device clock -> {len(data)/span:.1f} Hz")
    a = data[len(data)//2]
    print(f"mid sample: acc=({a.ax:.2f},{a.ay:.2f},{a.az:.2f}) m/s2 gyro=({a.gx:.2f},{a.gy:.2f},{a.gz:.2f}) rad/s")
    gaps = [data[i+1].t_ms - data[i].t_ms for i in range(len(data)-1)]
    print(f"dt min/max: {min(gaps)}/{max(gaps)} ms, dropped frames: {s.dropped_frames}")
print("status:", s.status)
s.disconnect()
time.sleep(0.5)
