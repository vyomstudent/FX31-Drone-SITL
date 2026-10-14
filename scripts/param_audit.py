#!/usr/bin/env python3
"""Read-only ArduCopter parameter audit; no parameters are changed."""
import argparse,csv,time
from datetime import datetime,timezone
from pathlib import Path
from pymavlink import mavutil
KIT=Path(__file__).resolve().parents[1]
PARAMS=['SYSID_THISMAV','ARMING_CHECK','FS_THR_ENABLE','FS_THR_VALUE','FS_GCS_ENABLE','BATT_LOW_VOLT','BATT_CRT_VOLT','BATT_LOW_MAH','BATT_CRT_MAH','BATT_FS_LOW_ACT','BATT_FS_CRT_ACT','SIM_BATT_VOLTAGE','FENCE_ENABLE','FENCE_ACTION','FENCE_ALT_MAX',*[f'SERVO{i}_FUNCTION' for i in range(9,17)],'SIM_RC_FAIL','SIM_GPS_DISABLE','SIM_WIND_SPD','SIM_WIND_DIR','SIM_ACC_RND']
def get(m,name,timeout=2):
    m.mav.param_request_read_send(m.target_system,m.target_component,name.encode(),-1); end=time.monotonic()+timeout
    while time.monotonic()<end:
        x=m.recv_match(type='PARAM_VALUE',blocking=True,timeout=max(.05,end-time.monotonic()))
        if x is None: break
        ident=x.param_id.decode(errors='ignore').rstrip('\0') if isinstance(x.param_id,bytes) else str(x.param_id).rstrip('\0')
        if ident==name:return float(x.param_value),int(x.param_type)
    return None
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--connect',default='udpin:127.0.0.1:14560'); a=ap.parse_args()
    if not a.connect.startswith('udpin:127.0.0.1:'): ap.error('Only localhost SITL endpoints are allowed.')
    m=mavutil.mavlink_connection(a.connect,autoreconnect=False)
    try:
        if m.wait_heartbeat(timeout=15) is None: raise TimeoutError('No SITL heartbeat')
        rows=[]
        for name in PARAMS:
            val=get(m,name)
            row=(name,'NOT_PRESENT_OR_NO_REPLY','') if val is None else (name,val[0],val[1]); rows.append(row); print(f'{name:20} {row[1]}')
        out=KIT/'outputs';out.mkdir(exist_ok=True);path=out/f"parameter_audit_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
        with path.open('w',newline='',encoding='utf-8') as f: w=csv.writer(f);w.writerow(['parameter','value','mav_param_type']);w.writerows(rows)
        print(f'\nRead-only audit saved: {path}')
    finally:m.close()
if __name__=='__main__':main()
