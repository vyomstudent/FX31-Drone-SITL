#!/usr/bin/env python3
"""Bounded local-SITL fault injection. Dry-run by default; writes only allowlisted SIM_ parameters."""
import argparse,time
from pymavlink import mavutil
RULES={
 'SIM_RC_FAIL':(0,2,{0,1,2},'0=normal, 1=RC loss, 2=neutral controls + low throttle'),
 'SIM_GPS_DISABLE':(0,1,{0,1},'1=disable simulated GPS'),
 'SIM_BATT_VOLTAGE':(8,25.2,None,'simulated battery voltage in volts; choose using the active BATT_LOW_VOLT/BATT_CRT_VOLT thresholds'),
 'SIM_WIND_SPD':(0,25,None,'simulated wind speed m/s'),
 'SIM_WIND_DIR':(0,360,None,'wind direction degrees'),
 'SIM_ACC_RND':(0,10,None,'accelerometer noise m/s^2'),
}
def get(m,n,timeout=3):
 m.mav.param_request_read_send(m.target_system,m.target_component,n.encode(),-1);end=time.monotonic()+timeout
 while time.monotonic()<end:
  x=m.recv_match(type='PARAM_VALUE',blocking=True,timeout=max(.05,end-time.monotonic()))
  if x is None:break
  ident=x.param_id.decode(errors='ignore').rstrip('\0') if isinstance(x.param_id,bytes) else str(x.param_id).rstrip('\0')
  if ident==n:return float(x.param_value),int(x.param_type)
 return None
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--connect',default='udpin:127.0.0.1:14560');ap.add_argument('--parameter',choices=sorted(RULES),required=True);ap.add_argument('--value',type=float,required=True);ap.add_argument('--apply',action='store_true');ap.add_argument('--confirm',default='');a=ap.parse_args()
 if not a.connect.startswith('udpin:127.0.0.1:'):ap.error('Safety guard: local UDP SITL only.')
 lo,hi,discrete,desc=RULES[a.parameter]
 if not lo<=a.value<=hi:ap.error(f'value must be between {lo} and {hi}')
 if discrete is not None and a.value not in discrete:ap.error(f'allowed values are {sorted(discrete)}')
 print(f'Plan: {a.parameter}={a.value:g} ({desc})')
 if not a.apply:print('DRY RUN: no change. Add --apply --confirm SITL_ONLY to apply.');return
 if a.confirm!='SITL_ONLY':ap.error('To apply, add --confirm SITL_ONLY')
 m=mavutil.mavlink_connection(a.connect,autoreconnect=False)
 try:
  if m.wait_heartbeat(timeout=15) is None:raise TimeoutError('No SITL heartbeat')
  old=get(m,a.parameter)
  if old is None:raise RuntimeError(f'{a.parameter} absent/no response in this firmware; no write sent')
  m.mav.param_set_send(m.target_system,m.target_component,a.parameter.encode().ljust(16,b'\0'),float(a.value),old[1])
  end=time.monotonic()+4
  while time.monotonic()<end:
   x=m.recv_match(type='PARAM_VALUE',blocking=True,timeout=max(.05,end-time.monotonic()))
   if x is None:break
   ident=x.param_id.decode(errors='ignore').rstrip('\0') if isinstance(x.param_id,bytes) else str(x.param_id).rstrip('\0')
   if ident==a.parameter:
    actual=float(x.param_value)
    if abs(actual-a.value)>.01:raise RuntimeError(f'parameter echo mismatch: {actual}')
    print(f'PASS: verified {a.parameter}={actual:g}. Restore it after the trial.');return
  raise TimeoutError('No matching PARAM_VALUE echo; inspect MAVProxy before retrying')
 finally:m.close()
if __name__=='__main__':main()
