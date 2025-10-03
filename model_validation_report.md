Model Validation Report
============================================================
Generated: 2025-10-03 08:38:13

Summary:
  Total Tests: 7
  Passed: 4
  Failed: 3
  Success Rate: 57.1%

Overall Status: ❌ SOME TESTS FAILED
Review failed tests before proceeding to production.

Detailed Results:
  ✅ coefficient_sanity: Model coefficient validation: PASSED
    checks: ['✅ Offensive skill coefficient is positive: 0.150', '✅ Defensive skill coefficient is negative: -0.120', '✅ Archetype coefficients are reasonable: max=0.260']
    warnings: []
  ✅ diminishing_returns: Diminishing returns test: PASSED (3&D value: 0.013, 2nd guard value: -0.015)
    base_lineup_score: 1.4473
    with_second_guard_score: 1.4319
    with_3d_score: 1.4605000000000001
  ❌ synergy_effects: Synergy test: FAILED (Combined: 1.468, Individual sum: 2.890)
    playmaker_score: 1.4473
    finisher_score: 1.4428999999999998
    combined_score: 1.4682000000000002
    synergy_ratio: 0.5079925264687565
  ❌ spacing_effects: Spacing test: FAILED (Improvement: -0.025)
    bad_spacing_score: 1.4495
    good_spacing_score: 1.4242000000000001
    spacing_improvement: -0.025299999999999878
  ✅ historical_validation: Historical validation: PASSED (High skill: 1.472, Low skill: 1.401)
    high_skill_score: 1.4715000000000003
    low_skill_score: 1.4011
    discrimination: 0.07040000000000024
  ❌ archetype_interactions: Archetype interaction test: FAILED (Difference: 0.007)
    lineup1_score: 1.4715000000000003
    lineup2_score: 1.4649
    archetype_difference: 0.006600000000000161
  ✅ skill_impacts: Skill impact test: PASSED (High skill: 1.472, Low skill: -0.686)
    high_skill_score: 1.4715000000000003
    low_skill_score: -0.6856000000000001
    skill_difference: 2.1571000000000002

Next Steps:
1. Review any failed tests and investigate root causes
2. If all tests pass, proceed with building production tools
3. If tests fail, consider model retraining or feature engineering
4. Run this validation after any model updates