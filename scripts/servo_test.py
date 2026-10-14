#!/usr/bin/env python3
"""Dry-run-first local SITL test for MAV_CMD_DO_SET_SERVO."""
import argparse,time
from pymavlink import mavutil
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--channel',type=int,required=True);ap.add_argument('--pwm',type=int,required=True);ap.add_argument('--connect',default='udpin:127.0.0.1:14560');ap.add_argument('--execute',action='store_true');ap.add_argument('--confirm',default='');a=ap.parse_args()
 if not 9<=a.channel<=16:ap.error('Safety guard: allowed outputs 9..16 only; channels 1..8 are blocked because they may be motor outputs on larger frames')
 if not 1000<=a.pwm<=2000:ap.error('PWM must be 1000..2000 us')
 if not a.connect.startswith('udpin:127.0.0.1:'):ap.error('Safety guard: local SITL only')
 print(f'Planned DO_SET_SERVO: channel={a.channel}, pwm={a.pwm} us, {a.connect}')
 print('Verify this channel is an auxiliary output in this SITL config (SERVOx_FUNCTION), not a motor output.')
 if not a.execute:print('DRY RUN: nothing sent. Add --execute --confirm SITL_ONLY to send.');return
 if a.confirm!='SITL_ONLY':ap.error('To execute, add --confirm SITL_ONLY')
 m=mavutil.mavlink_connection(a.connect,autoreconnect=False)
 try:
  if m.wait_heartbeat(timeout=15) is None:raise TimeoutError('No SITL heartbeat')
  m.mav.command_long_send(m.target_system,m.target_component,mavutil.mavlink.MAV_CMD_DO_SET_SERVO,0,float(a.channel),float(a.pwm),0,0,0,0,0)
  end=time.monotonic()+5
  while time.monotonic()<end:
   x=m.recv_match(type='COMMAND_ACK',blocking=True,timeout=max(.05,end-time.monotonic()))
   if x is None:break
   if x.command==mavutil.mavlink.MAV_CMD_DO_SET_SERVO:
    if x.result==mavutil.mavlink.MAV_RESULT_ACCEPTED:print('PASS: SITL accepted DO_SET_SERVO. This does not validate a physical servo.');return
    raise RuntimeError(f'SITL rejected command; MAV_RESULT={x.result}')
  raise TimeoutError('No matching COMMAND_ACK received')
 finally:m.close()
if __name__=='__main__':main()
