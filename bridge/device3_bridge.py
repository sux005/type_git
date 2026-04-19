import time

import requests
import serial

# ── Config ────────────────────────────────────────────────────────────────────
# Find your port with: ls /dev/tty.usbmodem*
SERIAL_PORT   = "/dev/tty.usbmodem1503168582"
BAUD_RATE     = 9600
API_URL       = "http://3.15.176.0:8000/events"
POLL_INTERVAL = 5  # seconds between checks

_ALERT_RANK = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2}
_RISK_CMD   = {0: "normal", 1: "warning", 2: "critical"}


def get_combined_risk() -> int:
    """Fetch latest events, return the highest alert level across Device 1 and 2."""
    resp = requests.get(API_URL, timeout=5)
    resp.raise_for_status()

    latest = {}  # device_id → alert rank
    for raw in resp.json().get("events", []):
        dev_id = raw.get("device_id")
        if dev_id not in (1, 2):
            continue
        rank = _ALERT_RANK.get(str(raw.get("alert_level", "NORMAL")).upper(), 0)
        if rank > latest.get(dev_id, -1):
            latest[dev_id] = rank

    return max(latest.values()) if latest else 0


def main() -> None:
    print(f"Opening serial port {SERIAL_PORT} at {BAUD_RATE} baud…")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"Device 3 actuator bridge running. Polling every {POLL_INTERVAL}s.")

    last_risk = -1

    try:
        while True:
            try:
                risk = get_combined_risk()
                cmd  = _RISK_CMD[risk]

                if risk != last_risk:
                    print(f"  {_RISK_CMD.get(last_risk, '—')} → {cmd}  (sending to Device 3)")
                    ser.write((cmd + "\n").encode())
                    last_risk = risk
                else:
                    print(f"  Unchanged: {cmd}")

            except requests.RequestException as e:
                print(f"  API error: {e}")
            except Exception as e:
                print(f"  Error: {e}")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopping actuator bridge.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
