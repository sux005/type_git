import json
import time
from datetime import datetime, timezone

import requests
import serial

# Update SERIAL_PORT when running — find with: ls /dev/tty.usb* or ls /dev/tty.usbmodem*
SERIAL_PORT = "/dev/tty.usbmodem26911793012"
BAUD_RATE = 9600
API_URL = "http://3.15.176.0:8000/event"
DEVICE_NAME = "env_node_sam"
DEVICE_ID = 2

ALERT_MAP = {
    "idle": "NORMAL",
    "normal": "NORMAL",
    "warning": "WARNING",
    "critical": "CRITICAL",
}

_prev_water: int = 0
_last_alert: str = ""


def build_payload(event: dict) -> dict:
    global _prev_water

    # value is 0.0–1.0 joystick deflection — scale to 0–1023 for current_water
    value_float = float(event.get("value", 0.0))
    current_water = int(round(value_float * 1023))
    delta_water = current_water - _prev_water
    _prev_water = current_water

    alert_raw = str(event.get("alert_level", "idle")).lower()
    alert_level = ALERT_MAP.get(alert_raw, "NORMAL")

    return {
        "device_id": DEVICE_ID,
        "device_name": DEVICE_NAME,
        "timestamp_ms": int(time.time() * 1000),
        "host_timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_level": alert_level,
        "features": {
            "current_water": current_water,
            "delta_water": delta_water,
        },
    }


def is_valid_event(event: dict) -> bool:
    if not (isinstance(event, dict) and "alert_level" in event and "value" in event):
        return False
    # ignore noise: value below 0.1 with no button press is analog drift
    value = float(event.get("value", 0.0))
    alert = str(event.get("alert_level", "")).lower()
    if value < 0.1 and alert == "normal":
        return False
    # only post when alert level changes
    global _last_alert
    mapped = ALERT_MAP.get(alert, "NORMAL")
    if mapped == _last_alert:
        return False
    _last_alert = mapped
    return True


def post_event(payload: dict) -> None:
    print("Posting event:")
    print(json.dumps(payload, indent=2))

    response = requests.post(API_URL, json=payload, timeout=5)

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    response.raise_for_status()
    print(f"Sent: {payload['alert_level']} | current_water={payload['features']['current_water']}")


def main() -> None:
    print(f"Opening serial port {SERIAL_PORT} at {BAUD_RATE} baud...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    print(f"Forwarding events to {API_URL}")

    try:
        while True:
            try:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                print(f"Raw serial: {line}")

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    print("Skipping non-JSON line")
                    continue

                if not is_valid_event(event):
                    print("Skipping non-event JSON")
                    continue

                payload = build_payload(event)
                post_event(payload)

            except requests.RequestException as e:
                print(f"API error: {e}")

            except Exception as e:
                print(f"Unexpected error: {e}")

    except KeyboardInterrupt:
        print("\nStopping bridge.")

    finally:
        ser.close()


if __name__ == "__main__":
    main()
