#!/usr/bin/env python3
"""Read-only FX31 browser telemetry monitor. It never sends MAVLink commands."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from typing import Any

ROOT = Path(__file__).resolve().parent

class TelemetryState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.last_packet = 0.0
        self.data: dict[str, Any] = {
            'connected': False, 'mode': 'UNKNOWN', 'armed': False,
            'latitude': None, 'longitude': None, 'relative_altitude_m': None,
            'north_m': None, 'east_m': None, 'battery_v': None,
            'gps_fix_type': None, 'satellites': None, 'groundspeed_mps': None,
            'heading_deg': None, 'source': 'SITL localhost UDP 14561',
        }

    def ingest(self, name: str, fields: dict[str, Any], now: float | None = None) -> None:
        current = time.monotonic() if now is None else now
        with self.lock:
            self.last_packet = current
            if name == 'HEARTBEAT':
                self.data['armed'] = bool(fields.get('base_mode', 0) & 128)
                self.data['mode'] = str(fields.get('mode', 'UNKNOWN'))
            elif name == 'GLOBAL_POSITION_INT':
                self.data['latitude'] = fields.get('lat', 0) / 1e7
                self.data['longitude'] = fields.get('lon', 0) / 1e7
                self.data['relative_altitude_m'] = fields.get('relative_alt', 0) / 1000
                self.data['heading_deg'] = fields.get('hdg', 65535) / 100 if fields.get('hdg') != 65535 else None
            elif name == 'LOCAL_POSITION_NED':
                self.data['north_m'] = round(float(fields.get('x', 0)), 2)
                self.data['east_m'] = round(float(fields.get('y', 0)), 2)
            elif name == 'GPS_RAW_INT':
                self.data['gps_fix_type'] = fields.get('fix_type')
                self.data['satellites'] = fields.get('satellites_visible')
            elif name == 'SYS_STATUS':
                raw = fields.get('voltage_battery')
                self.data['battery_v'] = raw / 1000 if raw is not None and raw != 65535 else None
            elif name == 'VFR_HUD':
                self.data['groundspeed_mps'] = fields.get('groundspeed')

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            data = dict(self.data)
            age = round(time.monotonic() - self.last_packet, 1) if self.last_packet else None
        data['age_seconds'] = age
        data['connected'] = age is not None and age < 5.0
        data['server_time_utc'] = datetime.now(timezone.utc).isoformat()
        return data


def listen(state: TelemetryState) -> None:
    from pymavlink import mavutil
    while True:
        try:
            conn = mavutil.mavlink_connection('udpin:127.0.0.1:14561', autoreconnect=False)
            print('Listening for simulation telemetry on localhost UDP 14561', flush=True)
            while True:
                msg = conn.recv_match(blocking=True, timeout=2)
                if msg is None:
                    continue
                kind = msg.get_type()
                if kind == 'BAD_DATA':
                    continue
                values = msg.to_dict()
                if kind == 'HEARTBEAT':
                    try:
                        values['mode'] = mavutil.mode_string_v10(msg)
                    except Exception:
                        values['mode'] = f"custom_mode={values.get('custom_mode')}"
                state.ingest(kind, values)
        except Exception as exc:
            print('Telemetry listener retry:', exc, flush=True)
            time.sleep(2)
        finally:
            try:
                conn.close()
            except Exception:
                pass


def handler_class(state: TelemetryState):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split('?', 1)[0]
            if path == '/api/telemetry':
                body = json.dumps(state.snapshot(), allow_nan=False).encode('utf-8')
                content_type = 'application/json; charset=utf-8'
            elif path in ('/', '/index.html'):
                body = (ROOT / 'index.html').read_bytes()
                content_type = 'text/html; charset=utf-8'
            elif path == '/healthz':
                body = b'{"server":"ok","flight":"not_asserted"}'
                content_type = 'application/json; charset=utf-8'
            else:
                self.send_error(404, 'Not Found')
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, fmt: str, *args: object) -> None:
            if not self.path.startswith('/api/'):
                super().log_message(fmt, *args)
    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8000)
    ap.add_argument('--no-listener', action='store_true', help='HTTP-only mode for offline testing')
    a = ap.parse_args()
    state = TelemetryState()
    if not a.no_listener:
        threading.Thread(target=listen, args=(state,), daemon=True).start()
    server = ThreadingHTTPServer((a.host, a.port), handler_class(state))
    print(f'FX31 read-only dashboard listening at http://{a.host}:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
