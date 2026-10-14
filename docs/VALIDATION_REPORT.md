# FX31 SITL Test Kit — validation report

**Report date:** 2026-10-13  
**Kit version:** 1.0.0  
**Firmware default:** ArduCopter `Copter-4.7.1` (override to match the target Pixhawk release).

## Offline checks completed

- `scripts/self_test.sh`: passed all package, syntax and shell checks, with zero reported failures.
- Rescue world: parsed as XML/SDF; required building, person, fire-proxy and Iris-with-gimbal elements are present.
- Python source: parsed with `ast`; shell scripts passed `bash -n`.
- Release-zone gate: 250 deterministic synthetic trials, seed 42, illustrative 5.0 m separation; **215 ALLOW**, **35 BLOCK**, zero boundary failures and zero invariant failures.
- Scenario randomizer: generated and XML-validated three SDF variants for seeds 42, 43 and 44.
- ZIP archive: integrity check passed; the archive excludes virtual environments, bytecode caches and generated trial outputs.

## Not executed in this build environment

ArduPilot SITL, MAVProxy, `pymavlink`, Gazebo Harmonic and the ArduPilot Gazebo plugin were not installed here. Therefore no live MAVLink heartbeat, telemetry, parameter write, servo-command ACK, GUIDED takeoff/RTL, physics simulation, camera stream or thermal output was runtime-tested. The scripts are syntax-checked, and commands have explicit opt-in guards, but the first runtime checkpoint remains `python scripts/check_sitl.py` after installing and launching SITL.

## Scope limitations

The rescue scene uses static geometry, human-shaped stand-ins and glowing RGB fire proxies. It is not a validated FX31 flight-dynamics model; people do not walk, fire/smoke physics is not simulated, and the glowing geometry is not thermal ground truth. The offline release gate checks only a simple geometric distance rule on synthetic positions; it does not validate any detector, target localization, descent path, wind drift, or payload release safety.

## Upstream compatibility references

- ArduPilot stable Copter releases: https://github.com/ArduPilot/ardupilot/releases
- Official ArduPilot + Gazebo integration: https://ardupilot.org/dev/docs/sitl-with-gazebo.html
- Official Gazebo Harmonic SDF world guide: https://gazebosim.org/docs/harmonic/sdf_worlds/
- Official SITL simulation parameters: https://ardupilot.ardupilot.org/dev/docs/SITL_simulation_parameters.html
