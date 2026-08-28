# Week 7 Person 1 and Person 2 Manual Checks

Run commands from the project root.

## Complete automated suite

```bash
python3 -m unittest discover \
  -s "Module 7 - Explainable AI & Performance Evaluation/tests" \
  -v
```

Expected ending:

```text
Ran 21 tests
OK
```

## Real project-data workflow

```bash
python3 "Module 7 - Explainable AI & Performance Evaluation/run_person_1_2.py"
```

Expected checks:

- `forecast_model_count` is `7`;
- `explained_model_count` is `7`;
- an anomaly count is reported;
- `person_3_integration_included` is `false`.

## Validate every JSON output

```bash
for file in \
  "Module 7 - Explainable AI & Performance Evaluation"/outputs/*/*.json
do
  python3 -m json.tool "$file" >/dev/null || exit 1
done
echo "All Module 7 JSON outputs are valid"
```

## Inspect key reports

```bash
python3 -m json.tool \
  "Module 7 - Explainable AI & Performance Evaluation/outputs/reports/person_1_2_summary.json"
```

```bash
python3 -m json.tool \
  "Module 7 - Explainable AI & Performance Evaluation/outputs/performance/model_monitoring.json"
```

```bash
python3 -m json.tool \
  "Module 7 - Explainable AI & Performance Evaluation/outputs/explanations/shap_explanations.json"
```

```bash
python3 -m json.tool \
  "Module 7 - Explainable AI & Performance Evaluation/outputs/anomalies/anomaly_report.json"
```

## Compile check

```bash
python3 -m compileall -q \
  "Module 7 - Explainable AI & Performance Evaluation"
```

Expected result: no compilation errors.
