"""Record one real HTTP profile plus 50-request checkpoints (restart API first)."""
import argparse
import json
import random
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.load_test import apply_drift, apply_group_bias, post, row_to_payload
from pipeline.data_ingestion import load_raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['normal', 'drifted', 'unfair'], required=True)
    parser.add_argument('--strength', type=float, default=1.0)
    parser.add_argument('--requests', type=int, default=400)
    parser.add_argument('--seed', type=int, default=501)
    args = parser.parse_args()
    name = args.profile if args.strength == 1 else f'{args.profile}-{args.strength}'
    rng = random.Random(args.seed)
    sample = load_raw().sample(n=args.requests, replace=True, random_state=args.seed)
    report = {'profile': args.profile, 'strength': args.strength, 'seed': args.seed,
              'started_at': datetime.now(timezone.utc).isoformat(), 'checkpoints': []}
    scores, latencies, decisions, statuses = [], [], Counter(), Counter()
    for i, (_, row) in enumerate(sample.iterrows(), 1):
        payload = row_to_payload(row)
        if args.profile == 'drifted':
            payload = apply_drift(payload, rng, args.strength)
        elif args.profile == 'unfair':
            payload = apply_group_bias(payload, rng)
        status, body, duration = post('http://localhost:8000/predict', payload)
        statuses[status] += 1
        latencies.append(duration)
        if status != 200:
            raise RuntimeError(f'Request {i} failed: HTTP {status}')
        scores.append(body['default_probability'])
        decisions[body['decision']] += 1
        if i % 50 == 0:
            with urllib.request.urlopen('http://localhost:8000/monitoring') as response:
                state = json.load(response)
            report['checkpoints'].append({'requests': i, 'elapsed_seconds': time.time(),
                'mean_score': sum(scores)/len(scores), 'decisions': dict(decisions), **state})
            print(i, state['drift_score'], state['fairness_gap'], flush=True)
        time.sleep(0.15)
    report.update({'statuses': dict(statuses), 'mean_score': sum(scores)/len(scores),
                   'decisions': dict(decisions), 'p95_ms': sorted(latencies)[int(.95*len(latencies))]*1000,
                   'finished_at': datetime.now(timezone.utc).isoformat()})
    out = Path('docs/evidence') / f'{name}.json'
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(out)


if __name__ == '__main__':
    main()
