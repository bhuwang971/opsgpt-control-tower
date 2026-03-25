# Cycle 9 Experiment Report: Adaptive Turnaround Buffers

Local fixture-backed toggle that reduces effective arrival delay for the treated cohort to emulate an operational recovery policy.

## Primary Metric
- control rate: 0.0484
- treatment rate: 0.1587
- absolute lift: 0.1103
- relative lift: 2.2804
- p-value: 0.0433
- significant: True

## Guardrails
- `cancellation_rate`: control=0.0484, treatment=0.0794, diff=0.0310, status=watch
- `p90_arr_delay_minutes`: control=51.0000, treatment=47.0000, diff=-4.0000, status=pass
- `severe_delay_rate`: control=0.0323, treatment=0.0000, diff=-0.0323, status=pass

## Sequential Checks
- 2024-01-05: lift=0.3333, p=0.3613, decision=keep-running
- 2024-01-06: lift=0.0000, p=1.0000, decision=keep-running
- 2024-01-07: lift=0.2321, p=0.3104, decision=keep-running
- 2024-01-08: lift=0.2000, p=0.2636, decision=keep-running
- 2024-01-09: lift=0.1474, p=0.3151, decision=keep-running
- 2024-01-10: lift=0.0667, p=0.6242, decision=keep-running
- 2024-01-11: lift=0.1046, p=0.4120, decision=keep-running
- 2024-01-12: lift=0.1000, p=0.3758, decision=keep-running
- 2024-01-13: lift=0.1265, p=0.2419, decision=keep-running
- 2024-01-14: lift=0.1200, p=0.2214, decision=keep-running
- 2024-01-15: lift=0.1759, p=0.0779, decision=keep-running
- 2024-01-16: lift=0.1667, p=0.0706, decision=keep-running
- 2024-01-17: lift=0.1799, p=0.0444, decision=promising
- 2024-01-18: lift=0.1714, p=0.0404, decision=promising
- 2024-01-19: lift=0.1565, p=0.0463, decision=promising
- 2024-01-20: lift=0.1250, p=0.1045, decision=keep-running
- 2024-01-21: lift=0.1379, p=0.0680, decision=keep-running
- 2024-01-22: lift=0.1333, p=0.0628, decision=keep-running
- 2024-01-23: lift=0.1237, p=0.0697, decision=keep-running
- 2024-01-24: lift=0.1200, p=0.0648, decision=keep-running
- 2024-01-25: lift=0.1310, p=0.0416, decision=promising
- 2024-01-26: lift=0.1273, p=0.0387, decision=promising
- 2024-01-27: lift=0.1198, p=0.0425, decision=promising
- 2024-01-28: lift=0.1167, p=0.0398, decision=promising
- 2024-01-29: lift=0.1103, p=0.0433, decision=promising

## Segment Breakdown
- AA: lift=0.2000, sample=50
- UA: lift=0.1538, sample=25
- SW: lift=0.0000, sample=25
- DL: lift=-0.0064, sample=25

## Recommendation
- decision: hold_for_guardrail_review
- rationale: Primary metric improved, but at least one guardrail needs a closer read.