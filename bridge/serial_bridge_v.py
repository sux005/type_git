import json
import time
from datetime import datetime, timezone

import requests
import serial

# Update these when running on UNO Q
SERIAL_PORT = "/dev/cu.usbmodem15401295172"
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

    # Handle simple format: {"device_id":"water_node","value":0.123,"alert_level":"normal"}
    if "device_id" in event and "value" in event:
        # Convert device_id to string if needed
        if isinstance(event["device_id"], str):
            event["device_id"] = event["device_id"]
        else:
            event["device_id"] = str(event["device_id"])
        # Value is already set
        return event
    
    # Handle complex KNN format
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
    # Accept both formats: complex KNN and simple water sensor
    if "status" in event and event["status"] == "booted":
        return False  # Skip boot messages
    
    # Simple format: {"device_id":"water_node","value":0.123,"alert_level":"normal"}
    if "device_id" in event and "value" in event and "alert_level" in event:
        return True
    
    # Complex KNN format: {"timestamp_ms": 1234567890, "alert_level": "normal", "features": {...}}
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