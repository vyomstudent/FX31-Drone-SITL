#!/usr/bin/env python3
"""Offline Monte Carlo exercise for a simple human-separation release gate.

This tests only the example distance-gate logic with synthetic ground-truth
positions. It is not connected to a camera detector, flight controller, or servo.
"""
from __future__ import annotations
import argparse
import csv
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def permit_release(drop_xy: tuple[float, float], people_xy: list[tuple[float, float]],
                   min_separation_m: float) -> tuple[bool, float | None]:
    """Allow only if every known person's horizontal distance is >= threshold."""
    if not people_xy:
        return True, None
    nearest = min(math.hypot(drop_xy[0] - px, drop_xy[1] - py) for px, py in people_xy)
    return nearest >= min_separation_m, nearest


def check_boundary_cases(threshold: float) -> list[str]:
    failures: list[str] = []
    cases = [
        ((0.0, 0.0), [], True, "no people"),
        ((0.0, 0.0), [(0.0, 0.0)], False, "person at target"),
        ((0.0, 0.0), [(threshold - 0.001, 0.0)], False, "just inside threshold"),
        ((0.0, 0.0), [(threshold, 0.0)], True, "exactly on threshold"),
        ((0.0, 0.0), [(threshold + 0.001, 0.0)], True, "just outside threshold"),
    ]
    for drop, people, expected, label in cases:
        actual, _ = permit_release(drop, people, threshold)
        if actual != expected:
            failures.append(label)
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trials', type=int, default=250, help='number of deterministic synthetic scenes (1..10000)')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--min-separation-m', type=float, required=True,
                    help='engineering input; choose from a reviewed hazard analysis, not this demo')
    ap.add_argument('--output', type=Path, default=ROOT/'outputs'/'release_gate_trials.csv')
    args = ap.parse_args()
    if not 1 <= args.trials <= 10000:
        ap.error('--trials must be between 1 and 10000')
    if not math.isfinite(args.min_separation_m) or args.min_separation_m <= 0 or args.min_separation_m > 100:
        ap.error('--min-separation-m must be >0 and <=100 metres')

    failures = check_boundary_cases(args.min_separation_m)
    rng = random.Random(args.seed)
    rows = []
    allowed = blocked = 0
    invariant_failures = 0
    for trial in range(1, args.trials + 1):
        drop = (rng.uniform(-20, 40), rng.uniform(-20, 20))
        count = rng.randint(0, 8)
        people = [(rng.uniform(-20, 40), rng.uniform(-20, 20)) for _ in range(count)]
        release, nearest = permit_release(drop, people, args.min_separation_m)
        # Independently assert the decision invariant on generated data.
        if nearest is not None and ((release and nearest < args.min_separation_m) or
                                    (not release and nearest >= args.min_separation_m)):
            invariant_failures += 1
        if release:
            allowed += 1
        else:
            blocked += 1
        rows.append({
            'trial': trial, 'seed': args.seed,
            'drop_x_m': f'{drop[0]:.3f}', 'drop_y_m': f'{drop[1]:.3f}',
            'people_count': count,
            'nearest_person_distance_m': '' if nearest is None else f'{nearest:.3f}',
            'required_separation_m': f'{args.min_separation_m:.3f}',
            'decision': 'ALLOW' if release else 'BLOCK',
            'note': 'synthetic ground truth; not a detector or flight test',
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f'Synthetic trials: {args.trials}; seed: {args.seed}; minimum separation: {args.min_separation_m:.3f} m')
    print(f'ALLOW={allowed}; BLOCK={blocked}; boundary failures={len(failures)}; invariant failures={invariant_failures}')
    print(f'CSV: {args.output}')
    if failures:
        print('FAIL: boundary cases: ' + ', '.join(failures))
    if invariant_failures:
        print('FAIL: release decision invariant violated')
    if failures or invariant_failures:
        return 1
    print('PASS: synthetic release-gate properties hold; this does not validate a real detector or drop safety.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
