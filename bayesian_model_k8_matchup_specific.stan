// Stan model for Bayesian regression of NBA possession outcomes
// Enhanced version with matchup-specific parameters (Equation 2.5 from Brill, Hughes, and Waldbaum)
// This implements the full paper methodology with 36×16 parameter architecture

data {
    int<lower=0> N; // number of observations
    vector[N] y;    // outcome variable (net points)

    // Matchup information
    array[N] int<lower=0, upper=35> matchup_id; // matchup index (0-35 for 6×6 superclusters)

    // Z-scores: aggregated skill ratings by archetype
    // We have 8 archetypes (0-7) for each side (offense/defense)
    matrix[N, 8] z_off;
    matrix[N, 8] z_def;
}

parameters {
    // Matchup-specific intercepts (36 matchups)
    vector[36] beta_0;

    // Matchup-specific coefficients for offensive and defensive Z-scores
    // 36 matchups × 8 archetypes = 288 parameters each
    matrix<lower=0>[36, 8] beta_off;  // Constrained to be positive (offensive skill should increase outcome)
    matrix<lower=0>[36, 8] beta_def;  // Constrained to be positive (defensive skill should decrease outcome)

    // Error term
    real<lower=0> sigma;
}

model {
    // Priors (weakly-informative as described in the paper)
    beta_0 ~ normal(0, 5);           // Intercepts
    for (m in 1:36) {
        beta_off[m] ~ normal(0, 5);  // Offensive coefficients for each matchup
        beta_def[m] ~ normal(0, 5);  // Defensive coefficients for each matchup
    }
    sigma ~ cauchy(0, 2.5);          // Error term

    // Likelihood: matchup-specific model
    // For each possession i, use the coefficients for matchup_id[i]
    for (i in 1:N) {
        int m = matchup_id[i] + 1;  // Convert 0-based to 1-based indexing for Stan

        // Predicted outcome: intercept + offensive contribution - defensive contribution
        real pred = beta_0[m] +
                   sum(z_off[i] .* beta_off[m]) -
                   sum(z_def[i] .* beta_def[m]);

        // Likelihood
        y[i] ~ normal(pred, sigma);
    }
}

// Generated quantities for model diagnostics and posterior predictive checks
generated quantities {
    vector[N] y_pred;      // Posterior predictive samples
    vector[N] log_lik;     // Log likelihood for model comparison

    for (i in 1:N) {
        int m = matchup_id[i] + 1;

        // Posterior predictive
        real pred = beta_0[m] +
                   sum(z_off[i] .* beta_off[m]) -
                   sum(z_def[i] .* beta_def[m]);

        y_pred[i] = normal_rng(pred, sigma);
        log_lik[i] = normal_lpdf(y[i] | pred, sigma);
    }
}