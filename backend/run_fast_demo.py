
import urllib.request
import json
import time

BASE_URL = 'http://localhost:5000/api'

def post(endpoint, data):
    try:
        req = urllib.request.Request(
            f'{BASE_URL}/{endpoint}',
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except Exception as e:
        print(f"Error calling {endpoint}: {e}")
        return None

print('='*60)
print('STARTING M-003 FAST FAILURE DEMO (30 Seconds)')
print('='*60)

# 1. Set Rate to 0.033 (1/30)
print('\n1. Setting degradation rate to 0.033 (30s duration)...')
res = post('machines/M-003/degradation-rate', {'rate': 0.033})
print("Result:", res)

# 2. Reset Machine
print('\n2. Resetting M-003 to start from beginning...')
res = post('machines/M-003/reset-degradation', {})
print("Result:", res)

print('\n' + '='*60)
print('✅ DEMO STARTED!')
print('Go to http://localhost:5173 and watch M-003')
print('It will fail in exactly 30 seconds.')
print('='*60)
