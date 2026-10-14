#!/usr/bin/env python3
"""Generate repeatable rescue-world variants by randomizing target/fire proxy poses."""
from __future__ import annotations
import argparse, random
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]

def set_pose(el, xyz):
    # Keep roll/pitch/yaw as written in the source SDF; only replace x/y/z.
    parts=(el.text or '').split()
    rpy=parts[3:6] if len(parts)>=6 else ['0','0','0']
    el.text=' '.join(f'{v:.3f}' for v in xyz)+' '+' '.join(rpy)

def make_variant(source: Path, destination: Path, seed: int) -> None:
    rng=random.Random(seed)
    tree=ET.parse(source); root=tree.getroot()
    model_by_name={m.attrib.get('name'):m for m in root.iter('model')}
    # Ground targets stay outside the building footprint; positions are varied for detector trials.
    plans={
      'person_ground_stand': (rng.uniform(7.0,13.0), rng.uniform(-9.0,-4.8), 0.0),
      'person_ground_lying': (rng.uniform(22.0,35.0), rng.uniform(-10.0,-6.0), 0.12),
      'person_balcony_target': (rng.uniform(16.0,20.0), -4.0, rng.choice([3.3,6.3])),
    }
    for name, xyz in plans.items():
        model=model_by_name.get(name)
        if model is None: raise ValueError(f'Missing expected model {name!r} in {source}')
        pose=model.find('pose')
        if pose is None: raise ValueError(f'Model {name!r} has no pose')
        set_pose(pose,xyz)
    building=model_by_name.get('rescue_building_A')
    if building is None: raise ValueError('rescue_building_A model missing')
    fires={
      'fire_ground': (rng.uniform(-2.6,2.6),-3.42,rng.uniform(0.8,2.2)),
      'fire_upper': (rng.uniform(-2.6,2.6),-3.43,rng.uniform(6.5,8.2)),
      'fire_balcony': (rng.uniform(-2.5,2.5),-4.0,rng.choice([3.5,6.5])),
    }
    visual_by_name={v.attrib.get('name'):v for v in building.iter('visual')}
    for name,xyz in fires.items():
        visual=visual_by_name.get(name)
        if visual is None: raise ValueError(f'Missing expected fire visual {name!r}')
        pose=visual.find('pose')
        if pose is None: raise ValueError(f'Visual {name!r} has no pose')
        set_pose(pose,xyz)
    destination.parent.mkdir(parents=True,exist_ok=True)
    tree.write(destination,encoding='utf-8',xml_declaration=True)
    ET.parse(destination)  # Catch corrupt output before the file is handed back.

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',type=int,default=42,help='reproducible seed (default: 42)')
    ap.add_argument('--count',type=int,default=1,help='number of variants to generate (1..500)')
    ap.add_argument('--output-dir',default='outputs/scenarios',help='output directory relative to kit root unless absolute')
    ap.add_argument('--source',default='worlds/fx31_rescue_training_world.sdf',help='source SDF relative to kit root unless absolute')
    a=ap.parse_args()
    if not 1<=a.count<=500: ap.error('--count must be between 1 and 500')
    src=Path(a.source); src=src if src.is_absolute() else ROOT/src
    out=Path(a.output_dir); out=out if out.is_absolute() else ROOT/out
    if not src.is_file(): ap.error(f'Source world not found: {src}')
    for i in range(a.count):
        seed=a.seed+i; dst=out/f'fx31_scenario_seed_{seed:05d}.sdf'
        make_variant(src,dst,seed); print(f'PASS seed={seed}: {dst}')
    print(f'Generated {a.count} XML-validated SDF variant(s). This creates scenario files; it does not run flights.')
if __name__=='__main__': main()
