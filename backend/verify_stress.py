
import urllib.request
import json
import time
import sys

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
        print(f"POST {endpoint} failed: {e}")
        return None

def get(endpoint):
    try:
        with urllib.request.urlopen(f'{BASE_URL}/{endpoint}') as r:
            return json.load(r)
    except Exception as e:
        print(f"GET {endpoint} failed: {e}")
        return None

print('='*60)
print('STRESS SCENARIO ENPOINT VERIFICATION')
print('='*60)

print('\n1. Initial Status M-002:')
status = get('scenarios/status/M-002')
print(json.dumps(status, indent=2))

print('\n2. Starting LOAD_SPIKE on M-002 (Severity=0.8)...')
res = post('scenarios/stress/start', {
    'machine_id': 'M-002', 
    'type': 'LOAD_SPIKE', 
    'severity': 0.8,
    'duration_sec': 30
})
print("Result:", json.dumps(res, indent=2))

print('\n3. Active Scenarios:')
active = get('scenarios/stress/active')
print(json.dumps(active, indent=2))

print('\n4. Checking Sensor Data (expecting high vibration)...')
machines_data = get('machines')
if machines_data:
    m002 = next((m for m in machines_data['machines'] if m['id'] == 'M-002'), None)
    if m002:
        vib_x = m002['sensors']['vibration_x']
        print(f"M-002 Vib X: {vib_x} (Normal base ~0.5)")
        if vib_x > 0.6:
            print("✓ SUCCESS: Vibration increased significantly")
        else:
            print("✗ FAIL: Vibration did not increase expected amount")
    else:
        print("✗ FAIL: M-002 found")

print('\n5. Stopping Scenario...')
stop_res = post('scenarios/stress/stop', {'machine_id': 'M-002'})
print("Result:", json.dumps(stop_res, indent=2))

print('\n' + '='*60)
print('VERIFICATION COMPLETE')
