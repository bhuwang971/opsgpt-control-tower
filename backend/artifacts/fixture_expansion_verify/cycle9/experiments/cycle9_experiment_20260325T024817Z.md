# Cycle 9 Experiment Report: Adaptive Turnaround Buffers

Local fixture-backed toggle that reduces effective arrival delay for the treated cohort to emulate an operational recovery policy.

## Primary Metric
- control rate: 0.4444
- treatment rate: 0.4444
- absolute lift: 0.0000
- relative lift: 0.0000
- p-value: 1.0000
- significant: False

## Guardrails
- `cancellation_rate`: control=0.0000, treatment=0.1111, diff=0.1111, status=watch
- `p90_arr_delay_minutes`: control=75.8000, treatment=60.8000, diff=-15.0000, status=pass
- `severe_delay_rate`: control=0.2222, treatment=0.1111, diff=-0.1111, status=pass

## Sequential Checks
- 2024-01-05: lift=-0.5000, p=0.3865, decision=keep-running
- 2024-01-06: lift=-0.3333, p=0.4142, decision=keep-running
- 2024-01-07: lift=-0.3500, p=0.2937, decision=keep-running
- 2024-01-08: lift=0.0000, p=1.0000, decision=keep-running
- 2024-01-09: lift=0.0714, p=0.7821, decision=keep-running
- 2024-01-10: lift=0.0000, p=1.0000, decision=keep-running

## Segment Breakdown
- AA: lift=0.0000, sample=5
- UA: lift=0.0000, sample=5
- DL: lift=-0.3333, sample=5
- SW: lift=-0.5000, sample=3

## Recommendation
- decision: do_not_ship
- rationale: Treatment did not improve the primary metric on the local experiment frame.