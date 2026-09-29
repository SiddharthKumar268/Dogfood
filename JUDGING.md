# Judging Methodology

## Assignment Strategy
Round-robin batch assignment ensures each submission receives an equal number of judge reviews (default: 2 per submission in fixtures, configurable up to N).

### Algorithm
For each submission in order, assign the next `perSubmission` judges from a rotating list:
```
judgeIdx = 0
for each submission:
    for i in range(perSubmission):
        assign judges[judgeIdx % len(judges)] to submission
        judgeIdx++
```

This ensures:
- Even distribution of workload across judges
- No judge is assigned their own team's submission (optional enhancement)
- Deterministic, reproducible assignment order

## Scoring

### Rubric Criteria
| Criterion | Weight | Max Score |
|---|---|---|
| Innovation | 0.30 | 10 |
| Technical Complexity | 0.30 | 10 |
| User Experience | 0.20 | 10 |
| Presentation | 0.20 | 10 |
| **Total** | **1.00** | |

Weights MUST sum to 1.0 — validated on rubric creation.

### Raw Score Computation
rawTotal = Σ (criterion_score × criterion_weight)

Example: Innovation=8, TC=7, UX=9, Pres=8
rawTotal = (8×0.3) + (7×0.3) + (9×0.2) + (8×0.2) = 2.4 + 2.1 + 1.8 + 1.6 = 7.9

## Normalization

### Why Normalize?
Different judges have different scoring tendencies. Judge A might use the full 1-10 range while Judge B gives everything a 5. Without normalization, projects reviewed by lenient judges would have an unfair advantage.

### Method: Per-Judge Z-Score Normalization
For each judge j:
1. Collect all rawTotal scores given by judge j: [r₁, r₂, ..., rₙ]
2. Compute mean: μⱼ = (Σrᵢ) / n
3. Compute standard deviation: σⱼ = √(Σ(rᵢ - μⱼ)² / n)
4. For each score: normalizedTotal = (rawTotal - μⱼ) / σⱼ

### Edge Case: Standard Deviation = 0
When a judge scores every submission identically (e.g., Judge Beta in fixtures gives all 5s), the standard deviation is 0, which would cause division by zero.

**Decision:** When σⱼ = 0, substitute σⱼ = 1. This means all normalized scores for that judge become 0 (since rawTotal - mean = 0 for all), effectively making that judge's scores neutral — they don't help or hurt any submission's ranking.

**Justification:** A judge who cannot differentiate between submissions provides no ranking information. Treating their normalized scores as 0 (neutral) is the most fair approach.

### Edge Case: Incomplete Review Batches
Not every judge may have scored every assigned submission. When computing final rankings:
- Only average normalizedTotal over judges who ACTUALLY scored that submission
- Do not include pending/missing scores as zeros
- Report the judge count alongside the average

**Justification:** Including unscored assignments as zeros would unfairly penalize submissions that happen to have unfinished reviews. Averaging only completed scores is standard practice.

## Final Ranking
1. For each submission, collect all normalizedTotal scores from judges who scored it
2. Compute the average normalizedTotal across those judges
3. Rank submissions by average normalizedTotal (descending)
4. Ties broken by higher rawTotal average

## Integrity Safeguards
- Judges can only view their own scores (enforced server-side)
- No judge can see another judge's individual scores
- Participants cannot access any scoring data until results are published
- Only organizers can trigger normalization and publish results
- All score changes are timestamped
