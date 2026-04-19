import requests, json, time
from arduino.app_utils import Bridge

EC2_URL = "http://3.15.176.0:8000/event"


def post_event(payload: str) -> str:
    try:
        data = json.loads(payload)
        r = requests.post(EC2_URL, json=data, timeout=5)
        print(f"EC2: {r.status_code}")
        return str(r.status_code)
    except Exception as e:
        print(f"Error: {e}")
        return f"error:{e}"


Bridge.provide("post_event", post_event)

while True:
    time.sleep(1)
