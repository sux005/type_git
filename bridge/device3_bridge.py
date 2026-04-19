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
    resp = requests.get(API_URL, timeout=5)
    resp.raise_for_status()

    latest = {}
    for raw in resp.json().get("events", []):
        dev_id = raw.get("device_id")
        try:
            dev_id = int(dev_id)
        except (TypeError, ValueError):
            continue
        if dev_id not in (1, 2):
            continue
        rank = _ALERT_RANK.get(str(raw.get("alert_level", "NORMAL")).upper(), 0)
        if rank > latest.get(dev_id, -1):
            latest[dev_id] = rank

    return max(latest.values()) if latest else 0


def main() -> None:
    print(f"Opening serial port {SERIAL_PORT} at {BAUD_RATE} baud…")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("Waiting for Arduino to boot…")
    time.sleep(3)
    print(f"Running. Polling {API_URL} every {POLL_INTERVAL}s.")

    try:
        while True:
            try:
                risk = get_combined_risk()
                cmd  = _RISK_CMD[risk]
                print(f"  Sending: {cmd}")
                ser.write((cmd + "\n").encode())
                ser.flush()

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
