# Lab 4 - Submission requirements

Source: DDM501_Lab4_Monitoring.pdf, task list and section 11.

| Task | Implementation | Evidence |
|---|---|---|
| 1 PSI | app/monitoring.py: population_stability_index | tests/test_monitoring.py |
| 2 Drift window | app/monitoring.py: compute_drift | tests/test_monitoring.py |
| 3 Fairness | app/monitoring.py: compute_fairness | tests/test_monitoring.py |
| 4 Publish gauges and JSON | app/monitoring.py: publish | monitoring and API tests |
| 5 Observe derived features | app/main.py: _observe | TestDerivedFeaturesReachTheMonitor |
| 6 Prometheus metrics endpoint | app/main.py: /metrics | tests/test_metrics.py |
| 7 Monitoring endpoint | app/main.py: /monitoring | tests/test_api_monitoring.py |
| 8 Explanation endpoint | app/main.py: /explain | TestExplain |
| 9 HTTP instrumentation | app/middleware.py | metrics/cardinality tests |
| 10 SHAP | app/explain.py | TestExplain |
| 11 Frozen reference | scripts/make_reference.py, models/reference.json | TestReference |
| 12 Seven ML alert rules | monitoring/prometheus/alerts/ml_alerts.yml | promtool.txt, CI config job |
| 13 Model Behaviour dashboard | monitoring/grafana/dashboards/model-behaviour.json | Grafana profile screenshots |

All 79 tests passed; app coverage 91.52% exceeds the 85% configured floor.
Promtool passes all supplied alert cases. Compose stack, health/readiness and
Prometheus scraping were verified locally and in CI.

Required written analysis: [REPORT.pdf](REPORT.pdf), three pages. It answers
which signal moved first, what would trigger an alert, and which signal isolates
the cause, using the actual saved measurements rather than reference answers.

Required dashboard screenshots for three populations:

- Normal: evidence/grafana-normal.jpg; measurements evidence/normal.json.
- Drifted: evidence/grafana-drifted.jpg; measurements evidence/drifted.json.
- Unfair: evidence/grafana-unfair.jpg; measurements evidence/unfair.json.
- Additional mild drift: evidence/grafana-drifted-mild.jpg, evidence/drifted-0.05.json.
- Additional fairness panels: evidence/grafana-drifted-fairness.jpg and evidence/grafana-unfair-fairness.jpg.

Public repository: https://github.com/thanhhai12/ddm501-lab4-monitoring
Verified passing run: https://github.com/thanhhai12/ddm501-lab4-monitoring/actions/runs/37105624178
Screenshot: evidence/github-ci-success.jpg (actual run for commit f700749).
Screenshot/checklist upload is pending GitHub write access; the existing PDF,
traffic screenshots and all thirteen tasks are already on the remote repository.

Local containers were stopped using docker compose down after validation;
volumes and artifacts remain available. Submit the repository link and PDF
through LMS; this work has not sent a submission to LMS.
