# DDM501 - Lab 4: Monitoring & Production Deployment

[![CI](https://github.com/thanhhai12/ddm501-lab4-monitoring/actions/workflows/ci.yml/badge.svg)](https://github.com/thanhhai12/ddm501-lab4-monitoring/actions/workflows/ci.yml)

Instrumented credit-risk API continuing the credit-default problem from Labs 1
and 2. All thirteen starter tasks are complete: PSI, frozen training reference,
fairness window, HTTP/ML metrics, SHAP explanations, seven model alerts, and a
provisioned Model Behaviour dashboard alongside the supplied Service Health dashboard.

## Run from a fresh checkout

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/make_dataset.py
python scripts/train_model.py
python scripts/make_reference.py
pytest --cov-report=xml --cov-report=html
docker compose up -d --build
```

| Service | Address |
|---|---|
| API docs | http://localhost:8000/docs |
| Prometheus exposition | http://localhost:8000/metrics |
| Monitoring JSON | http://localhost:8000/monitoring |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin, lab credentials) |
| Model Behaviour | http://localhost:3000/d/ddm501-model |
| Service Health | http://localhost:3000/d/ddm501-service |

Four containers share the `monitoring` network. Prometheus scrapes `api:8000`
by service DNS. Model and data are mounted read-only; the API runs as appuser.
The healthcheck validates `model_loaded`, not merely HTTP 200.
On Docker Desktop, node-exporter reports the Linux VM/container environment;
it does not expose the native macOS host's exact utilization.

## Tests and validation

The supplied 79 tests pass with **91.52%** application coverage (85% gate).
Promtool rule tests pass with Prometheus 2.51.2. Commands:

```bash
docker run --rm --entrypoint promtool \
  -v "$PWD/monitoring/prometheus:/etc/prometheus:ro" \
  prom/prometheus:v2.51.2 test rules /etc/prometheus/tests/alert_tests.yml
docker compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
docker compose config --quiet
```

CI checks rule syntax/behavior, pytest coverage, the Compose configuration, and
an actual running stack with metrics reaching Prometheus. Evidence, screenshots
and traffic measurements live in [docs/evidence](docs/evidence).
The written analysis is [REPORT.pdf](docs/REPORT.pdf), with [Markdown source](docs/REPORT.md).
[Submission requirements](docs/SUBMISSION_CHECKLIST.md) map each task to evidence.
[Passing CI screenshot](docs/evidence/github-ci-success.jpg) records the actual GitHub run.

## Reproduce the traffic experiment

Reset the API between runs to keep each 400-application window independent.
Wait for `/health` to report model_loaded before sending requests.

```bash
docker compose restart api
# Wait for readiness, then run ONE profile:
python scripts/run_profile.py --profile normal
python scripts/run_profile.py --profile drifted --strength 0.05
python scripts/run_profile.py --profile drifted
python scripts/run_profile.py --profile unfair
```

`run_profile.py` sends real HTTP requests and saves JSON checkpoints every 50
applications plus scores, decision counts, status codes, latency and timestamps.
Use the same seed (501) for all runs to compare matching base populations.
Grafana refreshes every 10s; wait for a scrape after traffic completes.
For exploratory traffic, `make load`, `make drift-mild`, `make drift`, and
`make unfair` use the starter's CLI. Stop with `docker compose down`.

## Metric choices and monitoring semantics

Counters count total requests, decisions and failures; gauges hold window size,
PSI, selection rates and model readiness; histograms hold latency and score
distributions; Info holds model metadata. Counter names end in `_total` and
latency uses seconds. `/metrics` is excluded from request counts. Labels use
route templates and an `unmatched` fallback to bound cardinality.

The PSI reference is frozen from **24,000 training rows**, with unique quantile
edges and open outer buckets. Both proportions are floored at 1e-4 before the
logarithm. All six features are recorded, including utilisation_ratio,
payment_ratio and max_delay derived before the monitoring window receives data.

The window stores at most 2,000 applications, requires 200 before computing
statistics and omits fairness groups smaller than 30. Selection means a score
>= 0.30, i.e. REVIEW or DECLINE. The gap is maximum minus minimum selection
rate and requires two sufficiently represented groups. Expired gauge labels
are cleared. Always read sufficient_data/window size alongside drift_score;
a zero score alone is not proof of stability.

`/explain` transforms the input using the model pipeline, explains the tree
classifier, ranks absolute positive-class SHAP contributions and reports values
in the applicant's units. Its timing/count metrics are separate from predictions.
SHAP log-odds explain this model output; they do not establish causal effects.

## Alert policy

| Alert | Condition | Hold | Severity |
|---|---|---|---|
| ModerateFeatureDrift | max PSI > 0.10 | 15m | warning |
| SignificantFeatureDrift | max PSI > 0.25 | 15m | critical |
| DriftWindowTooSmall | window < 200 | 30m | info |
| DecisionMixShift | decline share > 20% over 30m | 30m | warning |
| FairnessGapWidened | gap > 0.10 | 20m | critical |
| PredictionErrorsRising | inference errors > 0.1/s | 5m | critical |
| ExplanationLatencyHigh | SHAP p95 > 1s | 10m | warning |

Five supplied HTTP alerts cover scrape failure, missing model, 5xx ratio, p95
latency and no traffic. Alerts evaluate in Prometheus; this educational stack
does not configure an external Alertmanager notification channel. Short traffic
runs may make an alert pending; they do not demonstrate the full hold period.
Promtool validates time-dependent firing using synthetic series.

## Dataset and limits

The lab explicitly supplies a deterministic generated dataset because the UCI
archive may be unreachable. This submission uses that generator (30,000 rows,
seed 501), **not the actual UCI dataset**; schema matches the UCI credit-default
23-feature layout. It reproduces offline. No claims about real borrowers follow
from these simulated results. Accuracy cannot be observed immediately without
outcome labels; PSI and selection-rate disparity are signals for investigation.
PSI is univariate and misses changes only in feature relationships. Fairness
here is selection-rate disparity, not a causal discrimination estimate.
The in-memory window assumes a single API worker; multiple replicas need an
explicit aggregation strategy. A fixed-count window represents different time
spans at different traffic rates.
