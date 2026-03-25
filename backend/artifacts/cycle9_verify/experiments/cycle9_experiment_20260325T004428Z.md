# Cycle 9 Experiment Report: Adaptive Turnaround Buffers

Local fixture-backed toggle that reduces effective arrival delay for the treated cohort to emulate an operational recovery policy.

## Primary Metric
- control rate: 1.0000
- treatment rate: 0.5000
- absolute lift: -0.5000
- relative lift: -0.5000
- p-value: 0.3865
- significant: False

## Guardrails
- `cancellation_rate`: control=0.0000, treatment=0.0000, diff=0.0000, status=pass
- `p90_arr_delay_minutes`: control=4.0000, treatment=62.4000, diff=58.4000, status=watch
- `severe_delay_rate`: control=0.0000, treatment=0.5000, diff=0.5000, status=watch

## Sequential Checks
- 2024-01-05: lift=0.0000, p=1.0000, decision=keep-running
- 2024-01-06: lift=-0.5000, p=0.3865, decision=keep-running

## Segment Breakdown


## Recommendation
- decision: do_not_ship
- rationale: Treatment did not improve the primary metric on the local experiment frame.