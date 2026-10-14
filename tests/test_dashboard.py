#!/usr/bin/env python3
"""No network, MAVLink, drone, or Gazebo is required for these unit tests."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from urllib.request import urlopen
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fx31_dashboard', ROOT/'dashboard/server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DashboardTests(unittest.TestCase):
    def test_telemetry_units_and_stale(self):
        state = module.TelemetryState()
        state.ingest('HEARTBEAT', {'base_mode':128,'mode':'GUIDED'})
        state.ingest('GLOBAL_POSITION_INT', {'lat':232100000, 'lon':725800000,'relative_alt':3200,'hdg':65535})
        state.ingest('LOCAL_POSITION_NED', {'x':2.5,'y':-3.2})
        state.ingest('SYS_STATUS', {'voltage_battery':12000})
        s=state.snapshot()
        self.assertTrue(s['connected'])
        self.assertEqual(s['mode'],'GUIDED')
        self.assertEqual(s['latitude'],23.21)
        self.assertEqual(s['relative_altitude_m'],3.2)
        self.assertIsNone(s['heading_deg'])
        self.assertEqual(s['battery_v'],12)
        with state.lock:
            state.last_packet -= 7
        self.assertFalse(state.snapshot()['connected'])

    def test_http_routes_are_read_only(self):
        server = ThreadingHTTPServer(('127.0.0.1',0),module.handler_class(module.TelemetryState()))
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            with urlopen(base+'/api/telemetry', timeout=2) as resp:
                self.assertFalse(json.load(resp)['connected'])
            with urlopen(base+'/healthz',timeout=2) as resp:
                self.assertEqual(json.load(resp)['server'],'ok')
            with urlopen(base+'/',timeout=2) as resp:
                self.assertIn('FX31 / Simulation Console',resp.read().decode())
            with self.assertRaises(Exception):
                urlopen(base+'/control',timeout=2)
        finally:
            server.shutdown()
            server.server_close()

if __name__=='__main__': unittest.main()
