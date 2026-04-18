import serial
import requests
import json
import time
from datetime import datetime, timezone
import os

SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")
BAUD_RATE = 9600
EC2_IP = os.environ.get("EC2_PUBLIC_IP")
if not EC2_IP:
    raise SystemExit("ERROR: EC2_PUBLIC_IP environment variable is not set")
API_URL = f"http://{EC2_IP}:8000/event"


def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    print(f"Listening on {SERIAL_PORT} → {API_URL}")
    while True:
        try:
            line = ser.readline().decode("utf-8").strip()
            if not line:
                continue
            payload = json.loads(line)
            payload["timestamp"] = datetime.now(timezone.utc).isoformat()
            r = requests.post(API_URL, json=payload, timeout=3)
            print(f"Sent: {payload} → {r.status_code}")
        except json.JSONDecodeError:
            print(f"Bad line (skip): {line}")
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
