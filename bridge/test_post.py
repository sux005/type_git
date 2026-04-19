import requests

payload = {
    "device_id": 2,
    "device_name": "env_node_sam",
    "timestamp_ms": 1234567890,
    "alert_level": "CRITICAL",
    "features": {
        "current_water": 800,
        "delta_water": 50,
    },
}

response = requests.post("http://3.15.176.0:8000/event", json=payload, timeout=5)
print(f"Status: {response.status_code}")
print(f"Body: {response.text}")
