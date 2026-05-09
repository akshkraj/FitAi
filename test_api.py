import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://127.0.0.1:5000/api/chat', 
    data=json.dumps({"message": "hello"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode())
