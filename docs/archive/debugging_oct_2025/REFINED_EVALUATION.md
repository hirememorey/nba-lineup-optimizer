# Refined Evaluation: Why Matchup-Specific Model Matters

**Date**: October 28, 2025  
**Key Insight**: User correctly identified that simplified model only detects redundancy, not skill-context interactions

## The Critical Distinction

### What the Simplified Model Detected ✅
- "LeBron and Westbrook are both Archetype 4 (Playmaking Guards)"  
- "They have overlapping roles"  
- "This creates redundancy"

### What the Matchup-Specific Model SHOULD Detect 🎯
- "LeBron's skills contribute differently than Westbrook's in different matchup contexts"
- "Against a fast-break defense, LeBron's passing might be more valuable"
- "Against a packed paint, Westbrook's driving might be less effective than LeBron's shooting"
- **Context-dependent skill valuation**, not just "same archetype = redundancy"

## Why This Matters

The simplified model with **global coefficients** says:
```
Archetype 4 always contributes β_off[4] × skill regardless of context
```

But basketball reality is:
```
Archetype 4's skills contribute DIFFERENTLY depending on:
- What type of defense they're facing
- What other archetypes are on the floor  
- The pace and style of the game
```

## The Mathematical Case FOR Matchup-Specific

If we accept that:
1. **Context matters** (same archetype vs different defenses = different contributions)
2. **We detected this** in Phase 3 (both Archetype 4, but should be different impacts)

Then the matchup-specific model is **conceptually correct**, just **overparameterized**.

## The Real Question

**Is there a middle ground between 17 parameters and 612 parameters?**

Let me think from first principles...

### Problem Analysis
- Full model: 612 params ÷ 96K obs = 157 obs/param (actually good!)
- Subsampled: 612 params ÷ 25K obs = 40 obs/param (borderline)
- Sparse matchups: Some matchups have <100 possessions for 16 parameters

### Potential Solution: Reduce Matchup Complexity

Instead of 36 matchups × 16 params = 612 total:

**Option A: Aggregate Archetypes in Matchups**
- Instead of 8 archetypes per matchup, use 2-3 meta-archetypes
- Example: "Ball Handlers" vs "Wings" vs "Bigs"
- Result: 36 matchups × 6 params = 216 params (manageable!)

**Option B: Matchup-Specific Intercepts Only**
- Keep 8 global archetype coefficients
- Add 36 matchup-specific intercepts to capture style interactions
- Result: 1 + 8 + 8 + 36 = 53 params (very manageable!)

**Option C: Hierarchical Approach**
- Main effects: 17 global parameters (already work!)
- Interactively effects: 36 matchup × skill interaction terms (but pooled across archetypes)
- Result: ~100-150 params (borderline but possible)

## Recommendation

Given your insight, I think we should explore **Option B** first:

**Hybrid Model Architecture**:
```stan
parameters {
    // Global archetype effects (already validated)
    real beta_0;  
    vector<lower=0>[8] beta_off;
    vector<lower=0>[8] beta_def;
    
    // Matchup-specific intercepts (new, context effects)
    vector[36] gamma_matchup;  // Matches 36 matchup types
    
    real<lower=0> sigma;
}

model {
    for (i in 1:N) {
        int m = matchup_id[i] + 1;
        real pred = beta_0 +                              // Global intercept
                   gamma_matchup[m] +                     // Matchup-specific adjustment
                   sum(z_off[i] .* beta_off) -           // Global archetype offense
                   sum(z_def[i] .* beta_def);            // Global archetype defense
        
        y[i] ~ normal(pred, sigma);
    }
}
```

This gives us:
- **53 parameters** (36 matchups + 17 global) vs 612
- **Still captures matchup context effects** via γ_matchup[m]
- **Likely to converge** (53 ÷ 25K = 472 obs/param)
- **Interpretable**: Matchups can have different baseline values

## Should We Try This?

Yes, if you want to capture your insight about skill-context interactions.

This hybrid model would tell us:
- "Matchup 12 has higher baseline value than Matchup 5" (style difference)
- Still uses global archetype coefficients (proven to work)
- Adds matchup-specific context without overparameterization

Want to try implementing this hybrid approach?

