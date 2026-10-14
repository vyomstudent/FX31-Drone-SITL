#!/usr/bin/env python3
"""Run dependency-free package checks before installing/running the simulators."""
from __future__ import annotations
import ast, json, shutil, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
errors=[]; checks=0

def check(ok: bool, message: str):
    global checks
    checks += 1
    print(('PASS' if ok else 'FAIL') + ': ' + message)
    if not ok: errors.append(message)

def main() -> int:
    check((ROOT/'README_FIRST.md').is_file(), 'quickstart exists')
    for rel in ('install/01_install_ardupilot_sitl.sh','install/02_install_python_tools.sh','install/03_install_gazebo_harmonic.sh','install/04_build_ardupilot_gazebo_plugin.sh','scripts/run_sitl_only.sh','scripts/run_gazebo_world.sh','scripts/run_gazebo_sitl.sh','scripts/check_sitl.py','scripts/param_audit.py','scripts/sitl_param.py','scripts/servo_test.py','scripts/guided_flight_test.py','scripts/randomize_world.py','scripts/test_release_safety_gate.py','scripts/self_test.sh','docs/TEST_PLAN.md','docs/GAZEBO_STAGE.md','docs/VALIDATION_REPORT.md'):
        check((ROOT/rel).is_file(), f'present: {rel}')
    try:
        cfg=json.loads((ROOT/'config/test_profile.json').read_text(encoding='utf-8'))
        check(cfg['default_endpoint']=='udpin:127.0.0.1:14560', 'profile defaults to localhost SITL')
        check(cfg['servo_test']['channel_range']==[9,16], 'servo tool only allows auxiliary output range 9..16')
        rules={"SIM_RC_FAIL","SIM_GPS_DISABLE","SIM_BATT_VOLTAGE","SIM_WIND_SPD","SIM_WIND_DIR","SIM_ACC_RND"}
        check(set(cfg['fault_allowlist'])==rules, 'profile fault allowlist matches the bounded parameter writer')
    except Exception as e: check(False, f'profile JSON parses ({e})')
    try:
        tree=ET.parse(ROOT/'worlds/fx31_rescue_training_world.sdf')
        models=[x for x in tree.getroot().iter('model')]
        includes=[x.findtext('uri') for x in tree.getroot().iter('include')]
        check(tree.getroot().attrib.get('version')=='1.9', 'rescue world SDF XML parses, version 1.9')
        check(tree.find('./world/physics').attrib.get('type')=='ignored', 'world uses Gazebo-supported ignored physics type')
        check(any('rescue_building_A'==x.attrib.get('name') for x in models), 'world has multi-storey rescue building')
        check('model://iris_with_gimbal' in includes, 'world includes official Iris gimbal model')
        check(any('fire_' in (x.attrib.get('name') or '') for x in tree.getroot().iter('visual')), 'world includes glowing fire proxies')
        check(any((x.attrib.get('name') or '').startswith('person_') for x in models), 'world has person stand-in models')
    except Exception as e: check(False, f'SDF XML parses ({e})')
    pyfiles=list((ROOT/'scripts').glob('*.py'))
    for p in pyfiles:
        try: ast.parse(p.read_text(encoding='utf-8')); check(True, f'Python syntax: {p.name}')
        except SyntaxError as e: check(False, f'Python syntax: {p.name}:{e.lineno}: {e.msg}')
    shellfiles=list((ROOT/'install').glob('*.sh'))+list((ROOT/'scripts').glob('*.sh'))
    if shutil.which('bash'):
        for p in shellfiles:
            r=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True)
            check(r.returncode==0, f'Bash syntax: {p.relative_to(ROOT)}'+(f' ({r.stderr.strip()})' if r.returncode else ''))
    else: check(False, 'bash exists for shell syntax check')
    safety=(ROOT/'scripts/servo_test.py').read_text()+ (ROOT/'scripts/guided_flight_test.py').read_text()+ (ROOT/'scripts/sitl_param.py').read_text()
    check('udpin:127.0.0.1:14560' in safety and "startswith('udpin:127.0.0.1:')" in safety, 'control scripts enforce localhost UDP endpoint')
    check("a.confirm!='SITL_ONLY'" in safety and 'a.execute' in (ROOT/'scripts/servo_test.py').read_text(), 'control actions require explicit execution confirmation')
    check("'SIM_RC_FAIL'" in (ROOT/'scripts/sitl_param.py').read_text() and 'choices=sorted(RULES)' in (ROOT/'scripts/sitl_param.py').read_text(), 'fault injection uses a constrained allowlist')
    gate=(ROOT/'scripts/test_release_safety_gate.py').read_text()
    check('synthetic ground truth' in gate and 'min-separation-m' in gate and 'MAVLink' not in gate, 'release safety gate is offline-only with explicit distance input')
    audit=(ROOT/'scripts/param_audit.py').read_text()
    check('range(9,17)' in audit, 'read-only audit covers auxiliary SERVO9..SERVO16 functions')
    check('SIM_ACC_RND' in audit and 'SIM_BATT_VOLTAGE' in audit, 'read-only audit covers allowlisted sensor-noise and battery fault parameters')
    print(f'\n{checks} checks; {len(errors)} failure(s).')
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())
