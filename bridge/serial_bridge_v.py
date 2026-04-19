import json
import time
from datetime import datetime, timezone

import requests
import serial

# Update these when running on UNO Q
SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
API_URL = "http://3.15.176.0:8000/event"
DEVICE_NAME = "unoq_vivek"
DEFAULT_DEVICE_ID = "1"


def enrich_event(event: dict) -> dict:
    """
    Add fields needed by the backend and normalize the payload.
    """
    event["device_name"] = DEVICE_NAME
    event["host_timestamp"] = datetime.now(timezone.utc).isoformat()

    if "device_id" not in event or event["device_id"] is None:
        event["device_id"] = DEFAULT_DEVICE_ID
    else:
        event["device_id"] = str(event["device_id"])

    if "value" not in event or event["value"] is None:
        features = event.get("features", {})
        event["value"] = features.get("current_water")

    return event


def is_valid_event(event: dict) -> bool:
    """
    Only forward actual sensor events, not boot/status messages.
    """
    required_keys = {"timestamp_ms", "alert_level", "features"}
    return isinstance(event, dict) and required_keys.issubset(event.keys())


def post_event(event: dict) -> None:
    """
    Send one JSON event to the remote API.
    """
    print("Posting event:")
    print(json.dumps(event, indent=2))

    response = requests.post(API_URL, json=event, timeout=5)

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")

    response.raise_for_status()
    print(f"Sent event: {event.get('alert_level', 'UNKNOWN')} | status={response.status_code}")


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

                event = enrich_event(event)
                post_event(event)

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