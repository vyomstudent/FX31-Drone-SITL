#!/usr/bin/env python3
"""Opt-in local SITL-only short GUIDED takeoff then RTL. Dry-run by default."""
import argparse,time
from pymavlink import mavutil
def ack(m,cmd,timeout=4):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  x=m.recv_match(type='COMMAND_ACK',blocking=True,timeout=max(.05,end-time.monotonic()))
  if x is None:break
  if x.command==cmd:
   if x.result not in (mavutil.mavlink.MAV_RESULT_ACCEPTED,mavutil.mavlink.MAV_RESULT_IN_PROGRESS):raise RuntimeError(f'command {cmd} rejected: {x.result}')
   return True
 return False
def mode(m,name,timeout=10):
 modes=m.mode_mapping();mid=modes.get(name)
 if mid is None:raise RuntimeError(f'{name} mode unavailable')
 m.set_mode(mid);end=time.monotonic()+timeout
 while time.monotonic()<end:
  x=m.recv_match(type='HEARTBEAT',blocking=True,timeout=max(.05,end-time.monotonic()))
  if x and int(x.custom_mode)==int(mid):return
 raise TimeoutError(f'Could not confirm {name} mode')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--altitude-m',type=float,default=3);ap.add_argument('--connect',default='udpin:127.0.0.1:14560');ap.add_argument('--execute',action='store_true');ap.add_argument('--confirm',default='');a=ap.parse_args()
 if not 2<=a.altitude_m<=5:ap.error('Altitude limited to 2..5 m')
 if not a.connect.startswith('udpin:127.0.0.1:'):ap.error('Safety guard: local SITL only')
 print(f'Plan: GUIDED -> ARM -> takeoff {a.altitude_m:g} m -> RTL')
 if not a.execute:print('DRY RUN: no connection or flight command. Add --execute --confirm SITL_ONLY only for SITL.');return
 if a.confirm!='SITL_ONLY':ap.error('To execute, add --confirm SITL_ONLY')
 m=mavutil.mavlink_connection(a.connect,autoreconnect=False)
 try:
  if m.wait_heartbeat(timeout=15) is None:raise TimeoutError('No SITL heartbeat')
  gps=m.recv_match(type='GPS_RAW_INT',blocking=True,timeout=10)
  if gps is None or int(gps.fix_type)<3:raise RuntimeError('GPS 3D fix unavailable; refusing to arm')
  pos=m.recv_match(type='GLOBAL_POSITION_INT',blocking=True,timeout=10)
  if pos is None:raise RuntimeError('Position telemetry unavailable; refusing to arm')
  print(f'Preflight telemetry: GPS fix={gps.fix_type}; relative altitude={pos.relative_alt/1000:.2f} m')
  mode(m,'GUIDED')
  m.mav.command_long_send(m.target_system,m.target_component,mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,0,1,0,0,0,0,0,0)
  ack(m,mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,4)
  end=time.monotonic()+8;armed=False
  while time.monotonic()<end:
   x=m.recv_match(type='HEARTBEAT',blocking=True,timeout=.5)
   if x and x.base_mode&mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:armed=True;break
  if not armed:raise RuntimeError('Not armed; no takeoff command sent. Inspect pre-arm errors in MAVProxy.')
  m.mav.command_long_send(m.target_system,m.target_component,mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,0,0,0,0,0,0,0,float(a.altitude_m))
  ack(m,mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,4)
  print('Monitoring altitude for up to 45 s...');end=time.monotonic()+45;reached=False
  while time.monotonic()<end:
   x=m.recv_match(type='GLOBAL_POSITION_INT',blocking=True,timeout=1)
   if x and x.relative_alt/1000>=a.altitude_m*.75:print(f'PASS: altitude={x.relative_alt/1000:.2f} m');reached=True;break
  if not reached:
   try:mode(m,'RTL',timeout=8)
   finally:raise TimeoutError('Altitude target not confirmed; RTL requested. Check MAVProxy immediately.')
  print('Requesting RTL');mode(m,'RTL',timeout=10);print('PASS: RTL mode confirmed. Observe landing/disarm independently in MAVProxy.')
 finally:m.close()
if __name__=='__main__':main()
