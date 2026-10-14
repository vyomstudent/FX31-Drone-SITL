#!/usr/bin/env python3
"""Read-only local SITL telemetry smoke test; emits timestamped JSON and CSV evidence."""
from __future__ import annotations
import argparse, csv, json, sys
from datetime import datetime, timezone
from pathlib import Path
from pymavlink import mavutil
KIT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--connect', default='udpin:127.0.0.1:14560')
    ap.add_argument('--timeout', type=float, default=20)
    a=ap.parse_args()
    if not a.connect.startswith('udpin:127.0.0.1:'): ap.error('Safety guard: only localhost UDP SITL is allowed.')
    out=KIT/'outputs'; out.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc); tag=stamp.strftime('%Y%m%dT%H%M%SZ')
    result={'timestamp_utc':stamp.isoformat(),'endpoint':a.connect,'checks':{},'telemetry':{}}
    m=mavutil.mavlink_connection(a.connect, autoreconnect=False)
    try:
        hb=m.wait_heartbeat(timeout=a.timeout)
        if hb is None: raise TimeoutError('No heartbeat. Ensure run_sitl_only.sh is running with --out=127.0.0.1:14560.')
        result['checks']['HEARTBEAT']='PASS'
        result['telemetry'].update(system_id=m.target_system,component_id=m.target_component,autopilot=int(hb.autopilot),vehicle_type=int(hb.type),custom_mode=int(hb.custom_mode))
        print(f"PASS HEARTBEAT: sys={m.target_system}, comp={m.target_component}, mode={hb.custom_mode}")
        for name in ('GPS_RAW_INT','GLOBAL_POSITION_INT','SYS_STATUS'):
            msg=m.recv_match(type=name,blocking=True,timeout=a.timeout)
            if msg is None:
                result['checks'][name]='FAIL'; print(f'FAIL {name}: no message within {a.timeout}s'); continue
            result['checks'][name]='PASS'; print(f'PASS {name}')
            if name=='GPS_RAW_INT':
                result['telemetry'].update(gps_fix_type=int(msg.fix_type),satellites_visible=int(msg.satellites_visible),latitude_deg=msg.lat/1e7,longitude_deg=msg.lon/1e7)
                result['checks']['GPS_3D_FIX']='PASS' if msg.fix_type>=3 else 'WARN'
                if msg.fix_type<3: print('WARN GPS fix is not 3D yet; wait before flight tests.')
            elif name=='GLOBAL_POSITION_INT': result['telemetry'].update(relative_alt_m=msg.relative_alt/1000,altitude_msl_m=msg.alt/1000)
            else: result['telemetry'].update(battery_voltage_v=(msg.voltage_battery/1000 if msg.voltage_battery!=65535 else None),battery_remaining_pct=int(msg.battery_remaining))
        result['status']='PASS' if all(v=='PASS' for v in result['checks'].values()) else 'CHECK'
    except Exception as e:
        result['status']='FAIL'; result['error']=f'{type(e).__name__}: {e}'; print(f'FAIL: {e}',file=sys.stderr)
    finally: m.close()
    jp=out/f'sitl_smoke_{tag}.json'; cp=out/f'sitl_smoke_{tag}.csv'
    jp.write_text(json.dumps(result,indent=2),encoding='utf-8')
    with cp.open('w',newline='',encoding='utf-8') as f:
        wr=csv.writer(f); wr.writerow(['timestamp_utc','check','result']); wr.writerows([[result['timestamp_utc'],k,v] for k,v in result['checks'].items()])
    print(f"Status: {result['status']}\nEvidence: {jp}\n          {cp}")
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
