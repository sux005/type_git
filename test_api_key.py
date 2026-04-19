import os
import urllib.request
import json

api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if not api_key:
    raise SystemExit("GEMINI_API_KEY not set")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
body = json.dumps({"contents": [{"parts": [{"text": "Say: API key works"}]}]}).encode()

req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    print(data["candidates"][0]["content"]["parts"][0]["text"].strip())
    print("SUCCESS")
except urllib.error.HTTPError as e:
    raise SystemExit(f"FAILED: {e.code} {e.read().decode()}")
